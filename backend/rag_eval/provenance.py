"""What a result was measured on (code, corpus, questions, models), so it can be traced later."""

import hashlib
import subprocess
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app.core.config import Settings
from app.services.rag.ingest.corpus_manifest import CORPUS_DIR, CorpusDoc, load_manifest
from rag_eval.dataset import Question
from rag_eval.runner import EvalConfig

BACKEND_DIR = Path(__file__).resolve().parents[1]


def corpus_documents(chunk_set: str) -> list[CorpusDoc]:
    """Documents behind a chunk set: the manifest, plus the vbpl import for the `vbpl` set."""
    docs = load_manifest()
    extra = CORPUS_DIR / "vbpl" / "manifest.json"
    if chunk_set == "vbpl" and extra.exists():
        docs += load_manifest(extra)
    return docs


def _short_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def corpus_texts_sha(docs: list[CorpusDoc]) -> str:
    """Hash of the indexed texts: they can change while the manifest stays the same."""
    digest = hashlib.sha256()
    for doc in sorted(docs, key=lambda d: d.slug):
        if doc.ingest and doc.text_path.exists():
            digest.update(doc.slug.encode())
            digest.update(doc.text_path.read_bytes())
    return digest.hexdigest()[:12]


def _git(*args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *args], cwd=BACKEND_DIR, capture_output=True, text=True, timeout=10, check=True
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip()


def run_metadata(
    config: EvalConfig,
    settings: Settings,
    questions: list[Question],
    used: int,
    collection: str | None = None,
) -> dict:
    # Result files are the output of a run, so they do not make the code "dirty".
    status = _git(
        "status", "--porcelain", "--",
        ":(top)backend", ":(top,exclude)backend/rag_eval/results",
    )  # fmt: skip
    return {
        "date": date.today().isoformat(),
        "config": asdict(config),
        "config_hash": config.digest(),
        "git_sha": _git("rev-parse", "--short", "HEAD") or None,
        "git_dirty": None if status is None else bool(status),
        "corpus_manifest_sha": _short_sha((CORPUS_DIR / "manifest.json").read_bytes()),
        "corpus_texts_sha": corpus_texts_sha(corpus_documents(config.chunk_set)),
        "questions_sha": _short_sha("\n".join(q.to_json() for q in questions).encode()),
        "collection": collection,
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
