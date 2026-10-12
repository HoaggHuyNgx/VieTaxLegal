"""Generation tier: retrieve, answer with the real prompt, score citations and references."""

import asyncio
import re
import time
import unicodedata

from app.services.chat_citations import select_cited
from app.services.chat_prompt import prompt_with_context
from app.services.chat_provider import ModelProvider, ProviderError, ProviderMessage
from app.services.chat_retriever import RetrievalResult
from app.services.rag.qdrant_retriever import QdrantRetriever, hits_to_result
from rag_eval import metrics
from rag_eval.dataset import Question
from rag_eval.reference_check import check_references
from rag_eval.runner import EvalConfig, gold_articles, hit_articles

ABSTAIN_RE = re.compile(
    r"chưa thể (xác minh|xác nhận|khẳng định|kết luận)|chưa đủ căn cứ|không đủ căn cứ|"
    r"không (tìm thấy|có) (nguồn|căn cứ|quy định)|chưa có nguồn",
    re.IGNORECASE,
)


async def _answer(provider: ModelProvider, question: str, result: RetrievalResult, max_tokens: int):
    started, first, text, usage, truncated = time.perf_counter(), None, "", (None, None), False
    try:
        async for event in provider.stream(
            [ProviderMessage("user", question)], prompt_with_context(result), max_tokens
        ):
            if event.kind == "delta":
                first = first or time.perf_counter()
                text += event.text
            else:
                usage = (event.input_tokens, event.output_tokens)
    except ProviderError:
        if not text:  # nothing to score
            raise
        truncated = True  # stream cut off (usually the output-token cap): score what arrived
    end = time.perf_counter()
    return text, ((first or end) - started) * 1000, (end - started) * 1000, usage, truncated


async def _one(config, retriever, provider, q: Question, max_tokens: int) -> dict:
    hits, retrieval_ms, result = [], 0.0, RetrievalResult()
    if config.rag:
        outcome = await retriever.search(q.question)
        hits, retrieval_ms = outcome.hits, outcome.embed_ms + outcome.search_ms
        result = hits_to_result(hits)
    try:
        text, ttft_ms, total_ms, (tokens_in, tokens_out), truncated = await _answer(
            provider, q.question, result, max_tokens
        )
    except ProviderError:
        return {"id": q.id, "type": q.type, "error": "provider"}

    selection = select_cited(result, text)
    by_id = {c.id: hit_articles(h.payload) for c, h in zip(result.citations, hits)}
    cited = set().union(*(by_id[c.id] for c in selection.cited)) if selection.cited else set()
    refs = check_references(
        text,
        {h.payload.get("doc_number", "") for h in hits},
        {n for h in hits for n in h.payload.get("article_nos", [])},
    )
    row = {
        "id": q.id, "type": q.type, "field": q.field, "n_cited": len(selection.cited),
        "unknown_markers": len(selection.unknown_markers),
        "hallucinated_reference": refs.hallucinated,
        "unsupported": {
            "docs": refs.unsupported_doc_numbers,
            "articles": refs.unsupported_articles,
        },
        "retrieval_ms": retrieval_ms, "ttft_ms": ttft_ms, "total_ms": total_ms,
        "truncated": truncated,
        "input_tokens": tokens_in, "output_tokens": tokens_out, "answer": text,
    }  # fmt: skip
    if q.type == "out_of_corpus":
        row["abstained"] = bool(ABSTAIN_RE.search(unicodedata.normalize("NFC", text)))
    else:
        row["citation_precision"], row["citation_recall"] = metrics.citation_precision_recall(
            cited, gold_articles(q)
        )
    return row


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if "error" not in r]
    in_rows = [r for r in ok if r["type"] != "out_of_corpus"]
    ooc = [r for r in ok if r["type"] == "out_of_corpus"]
    return {
        "answered": len(ok),
        "provider_errors": len(rows) - len(ok),
        "truncated_answers": sum(r["truncated"] for r in ok),
        "citation_precision": metrics.mean(r["citation_precision"] for r in in_rows),
        "citation_recall": metrics.mean(r["citation_recall"] for r in in_rows),
        "answers_without_citation": sum(r["n_cited"] == 0 for r in in_rows),
        "hallucinated_reference_rate": (
            sum(r["hallucinated_reference"] for r in ok) / len(ok) if ok else None
        ),
        "ooc_no_citation_rate": sum(r["n_cited"] == 0 for r in ooc) / len(ooc) if ooc else None,
        "ooc_abstain_phrase_rate": sum(r["abstained"] for r in ooc) / len(ooc) if ooc else None,
        "retrieval_ms": metrics.latency_summary([r["retrieval_ms"] for r in ok]),
        "ttft_ms": metrics.latency_summary([r["ttft_ms"] for r in ok]),
        "total_ms": metrics.latency_summary([r["total_ms"] for r in ok]),
        "input_tokens": sum(r["input_tokens"] or 0 for r in ok),
        "output_tokens": sum(r["output_tokens"] or 0 for r in ok),
    }


async def run_generation_tier(
    config: EvalConfig, retriever: QdrantRetriever, provider, questions, max_tokens: int,
    concurrency: int = 3,
):  # fmt: skip
    gate = asyncio.Semaphore(concurrency)

    async def guarded(q):
        async with gate:
            return await _one(config, retriever, provider, q, max_tokens)

    rows = await asyncio.gather(*(guarded(q) for q in questions))
    return summarize(rows), rows
