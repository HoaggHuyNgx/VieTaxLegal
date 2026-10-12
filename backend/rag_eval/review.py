"""Human review of generated questions: show the gold law text, record approve/reject/edit."""

from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.legal_parser import parse
from rag_eval.dataset import Question


def gold_text(question: Question, docs: dict[str, CorpusDoc], limit: int = 1500) -> str:
    """Law text of the gold references, so the reviewer checks the answer against the source."""
    blocks = []
    for ref in question.gold_refs:
        doc = docs.get(ref.doc_slug)
        if doc is None:
            blocks.append(f"[{ref.doc_slug}: document not in manifest]")
            continue
        text = doc.text_path.read_text(encoding="utf-8")
        article = next((a for a in parse(text).articles if a.no == ref.article), None)
        body = text[article.start : article.end] if article else "[article not found]"
        blocks.append(f"{doc.number} Điều {ref.article}:\n{body[:limit]}")
    return "\n\n".join(blocks)


def apply_key(question: Question, key: str, note: str = "", new_text: str = "") -> bool:
    """Apply a review key. Returns False for keys that do not change the question (skip/unknown)."""
    if key == "a":
        question.status = "approved"
    elif key == "r":
        question.status = "rejected"
        question.reviewer_note = note
    elif key == "e" and new_text.strip():
        question.question = new_text.strip()
        question.status = "approved"
        question.reviewer_note = note or "edited"
    else:
        return False
    return True
