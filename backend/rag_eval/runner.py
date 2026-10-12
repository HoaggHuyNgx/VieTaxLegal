"""Eval runner: config, shared setup, result metadata and the retrieval tier (no chat calls)."""

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from app.core.config import Settings
from app.services.chat_provider import OpenAIProvider
from app.services.rag.corpus_manifest import CORPUS_DIR
from app.services.rag.embeddings import get_embedder
from app.services.rag.qdrant_retriever import QdrantRetriever
from app.services.rag.qdrant_store import collection_name, get_async_client
from app.services.rag.reranker import LlmReranker
from rag_eval import metrics
from rag_eval.dataset import Question, scoreable

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RECALL_KS = (1, 3, 5)
SWEEP = (0.0, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7)


@dataclass
class EvalConfig:
    name: str
    tier: str = "retrieval"  # retrieval | generation
    chunk_set: str = "article"
    top_k: int = 5
    min_similarity: float = 0.0
    require_in_force: bool = True
    rag: bool = True  # False = no-RAG baseline (generation tier only)
    mode: str = "dense"  # dense | hybrid
    rerank: str | None = None  # None | "llm" (experiment 2 trial)
    include_pending: bool = False  # provisional run on unreviewed questions
    depth: int = 10  # retrieved chunks scored by the retrieval tier
    embedding_provider: str | None = None
    embedding_model: str | None = None
    limit: int | None = None
    # Reasoning models spend output tokens before visible text; None = CHAT_MAX_OUTPUT_TOKENS.
    max_output_tokens: int | None = None

    @classmethod
    def load(cls, path: Path) -> "EvalConfig":
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:12]


def build_retriever(config: EvalConfig, settings: Settings) -> tuple[QdrantRetriever, object]:
    updates = {}
    if config.embedding_provider:
        updates["embedding_provider"] = config.embedding_provider
    if config.embedding_model:
        updates["embedding_model"] = config.embedding_model
    embedder = get_embedder(settings.model_copy(update=updates))
    retriever = QdrantRetriever(
        get_async_client(settings),
        embedder,
        collection_name(config.chunk_set, embedder.model),
        config.top_k,
        config.min_similarity,
        config.require_in_force,
        config.mode,
        reranker=LlmReranker(OpenAIProvider(settings.openai_api_key, settings.chat_model))
        if config.rerank == "llm"
        else None,
    )
    return retriever, embedder


def select_questions(questions: list[Question], config: EvalConfig) -> list[Question]:
    chosen = scoreable(questions, config.include_pending)
    return chosen[: config.limit] if config.limit else chosen


def gold_articles(question: Question) -> set[tuple[str, int]]:
    return {(ref.doc_slug, ref.article) for ref in question.gold_refs}


def hit_articles(payload: dict) -> set[tuple[str, int]]:
    return {(payload.get("doc_slug", ""), n) for n in payload.get("article_nos", [])}


def run_metadata(config: EvalConfig, settings: Settings, questions: list[Question], used: int):
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        sha = ""
    manifest = (CORPUS_DIR / "manifest.json").read_bytes()
    return {
        "date": date.today().isoformat(),
        "config": asdict(config),
        "config_hash": config.digest(),
        "git_sha": sha or None,
        "corpus_manifest_sha": hashlib.sha256(manifest).hexdigest()[:12],
        "models": {
            "chat": f"{settings.chat_provider}:{settings.chat_model}",
            "embedding": f"{config.embedding_provider or settings.embedding_provider}:"
            f"{config.embedding_model or settings.embedding_model}",
            "eval_generator": settings.eval_generator_model or "(same as chat)",
            "temperature": "provider default (not settable through the chat provider)",
        },
        "dataset": {
            "total": len(questions),
            "approved": sum(q.status == "approved" for q in questions),
            "used": used,
            # Unreviewed gold answers: fine for tuning, NOT for numbers quoted in the thesis.
            "provisional": config.include_pending and any(q.status == "pending" for q in questions),
        },
    }


def threshold_sweep(in_corpus_top1: list[float], ooc_top1: list[float]) -> list[dict]:
    """For each cosine threshold: share of answerable questions kept vs out-of-corpus rejected."""
    return [
        {
            "threshold": t,
            "answerable_kept": sum(s >= t for s in in_corpus_top1) / len(in_corpus_top1)
            if in_corpus_top1 else None,
            "out_of_corpus_rejected": sum(s < t for s in ooc_top1) / len(ooc_top1)
            if ooc_top1 else None,
        }
        for t in SWEEP
    ]  # fmt: skip


async def run_retrieval_tier(config: EvalConfig, retriever: QdrantRetriever, questions):
    rows, ranks, embed_ms, search_ms = [], [], [], []
    in_top1, ooc_top1 = [], []
    for q in questions:
        outcome = await retriever.search(q.question, limit=config.depth)
        embed_ms.append(outcome.embed_ms)
        search_ms.append(outcome.search_ms)
        top1 = outcome.hits[0].score if outcome.hits else 0.0
        top5 = outcome.hits[:5]
        row = {
            "id": q.id, "type": q.type, "field": q.field, "question": q.question,
            "top1_score": top1, "gold": sorted(gold_articles(q)),
            "top": [[h.payload.get("doc_slug"), h.payload.get("article_nos")] for h in top5],
        }  # fmt: skip
        if q.type == "out_of_corpus":
            ooc_top1.append(top1)
        else:
            rank = metrics.first_hit_rank(
                [hit_articles(h.payload) for h in outcome.hits], gold_articles(q)
            )
            ranks.append(rank)
            in_top1.append(top1)
            row["rank"] = rank
        rows.append(row)
    summary = {
        "in_corpus_questions": len(ranks),
        "out_of_corpus_questions": len(ooc_top1),
        **{f"recall@{k}": metrics.recall_at_k(ranks, k) for k in RECALL_KS},
        "mrr": metrics.mrr(ranks),
        "embed_ms": metrics.latency_summary(embed_ms),
        "search_ms": metrics.latency_summary(search_ms),
        # Cosine thresholds only make sense for dense scores (RRF/BM25 scores are on other scales).
        "threshold_sweep": threshold_sweep(in_top1, ooc_top1) if config.mode == "dense" else None,
    }
    return summary, rows
