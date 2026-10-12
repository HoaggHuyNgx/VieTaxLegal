"""Write the two human checklists for the corpus to plans/reports/ (Markdown).

1. Status checklist: per document, the "hieu luc thi hanh" article text, so a person can fill
   status / effective_from / effective_to in manifest.json without opening every source.
2. Chunk spot-check: 12 stratified chunks with source links, to compare against the official text.

Usage (from backend/): .venv/Scripts/python.exe scripts/corpus_review_sheets.py
"""

import random
import re
import sys
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services.rag.chunking import article_chunks  # noqa: E402
from app.services.rag.corpus_manifest import load_manifest  # noqa: E402
from app.services.rag.legal_parser import parse  # noqa: E402

REPORTS = BACKEND.parent / "plans" / "reports"
EFFECT_TITLE = re.compile(r"hiệu lực|điều khoản thi hành|tổ chức thực hiện", re.IGNORECASE)
SAMPLE_SIZE = 12


def status_sheet(docs) -> str:
    lines = [
        f"# Corpus status checklist ({date.today()})",
        "",
        "Fill `status` (in_force | expired | superseded), `effective_from`, `effective_to` in",
        "`backend/corpus/manifest.json` after checking the source page. Text below is only a hint.",
        "",
    ]
    for doc in docs:
        parsed = parse(doc.text_path.read_text(encoding="utf-8"))
        lines += [
            f"## {doc.number} - {doc.title}",
            f"- slug: `{doc.slug}`  | ingest: {doc.ingest} | truncated: {doc.truncated}",
            f"- source: {doc.source_url}",
            "- verified: [ ] status=____  effective_from=____  effective_to=____",
        ]
        for article in parsed.articles:
            if EFFECT_TITLE.search(article.title):
                body = doc.text_path.read_text(encoding="utf-8")[article.start : article.end]
                lines.append(f"- Điều {article.label} (hint): " + " ".join(body.split())[:420])
        lines.append("")
    return "\n".join(lines)


def chunk_sheet(docs) -> str:
    rng = random.Random(2026)
    pool = [d for d in docs if d.ingest]
    by_format = {"docx": [d for d in pool if d.file.endswith(".docx")],
                 "pdf": [d for d in pool if d.file.endswith(".pdf")]}  # fmt: skip
    picks = rng.sample(by_format["docx"], 4) + rng.sample(by_format["pdf"], SAMPLE_SIZE - 4)
    lines = [
        f"# Chunk spot-check ({date.today()})",
        "",
        "For each chunk: open the source, find the locator, tick if the text matches (no missing,",
        "merged or garbled words, correct Điều/khoản).",
        "",
    ]
    for doc in picks:
        chunks = article_chunks(doc, parse(doc.text_path.read_text(encoding="utf-8")))
        chunk = rng.choice(chunks)
        lines += [
            f"## [ ] {doc.number} - {chunk.locator}",
            f"- source: {doc.source_url}  (file: {doc.file})",
            f"- heading_path: {chunk.heading_path}",
            "",
            "```text",
            chunk.content[:700],
            "```",
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    docs = load_manifest()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "corpus-status-checklist.md").write_text(status_sheet(docs), encoding="utf-8")
    (REPORTS / "corpus-chunk-spot-check.md").write_text(chunk_sheet(docs), encoding="utf-8")
    print(f"wrote 2 sheets to {REPORTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
