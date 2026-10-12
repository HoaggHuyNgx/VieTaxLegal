"""Dry-run over the corpus: parse every document and print counts, problems and chunk stats.

Run before any embedding job. From backend/: .venv/Scripts/python.exe scripts/corpus_report.py
Exit code 1 when any document has a blocking problem (tagged BLOCK below).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.rag.chunking import article_chunks, estimate_tokens, fixed_chunks  # noqa: E402
from app.services.rag.chunking_small import small_article_chunks  # noqa: E402
from app.services.rag.corpus_manifest import CorpusDoc, load_manifest, verify_raw_file  # noqa: E402
from app.services.rag.legal_parser import ParsedDocument, parse  # noqa: E402

BKAI_TOKEN_LIMIT = 256
OCR_GARBAGE_PER_MILLE = 0.3  # share of ~ \ { } | characters that signals a bad text layer


def problems(doc: CorpusDoc, parsed: ParsedDocument, text: str) -> tuple[list[str], list[str]]:
    """Return (blocking, warnings) for one document."""
    diag, blocking, warnings = parsed.diagnostics, [], []
    if gaps := diag.unexplained_gaps(doc.known_gaps):
        blocking.append(f"GAPS {gaps[:8]}")
    if stale := diag.stale_known_gaps(doc.known_gaps):
        blocking.append(f"STALE known_gaps {stale}")
    labels = {a.label for a in parsed.articles}
    if unknown := [label for label in doc.excluded_articles if label not in labels]:
        blocking.append(f"excluded_articles not in text {unknown}")
    if diag.skipped_headings:
        blocking.append(f"skipped headings {diag.skipped_headings[:3]}")
    if diag.empty_articles:
        blocking.append(f"empty articles {diag.empty_articles[:5]}")
    if diag.continuation_marker and doc.truncated is None:
        blocking.append("text ends with 'Xem tiep Cong bao' - set truncated true/false in manifest")
    if not verify_raw_file(doc):
        blocking.append("RAW SHA256 MISMATCH")
    if doc.truncated:
        warnings.append("TRUNCATED source (partial document)")
    if diag.rejected_clauses:
        warnings.append(f"rejected khoan lines={len(diag.rejected_clauses)}")
    garbage = len(re.findall(r"[~\\{}|]", text)) / max(len(text), 1) * 1000
    if garbage > OCR_GARBAGE_PER_MILLE:
        warnings.append(f"OCR-garbage {garbage:.2f}/1000 chars")
    return blocking, warnings


def main() -> int:
    sys.stdout.reconfigure(
        encoding="utf-8"
    )  # headings contain Vietnamese; Windows pipes use cp1252
    blocked = 0
    totals = {"article": 0, "fixed": 0, "over_bkai": 0}
    for doc in load_manifest():
        text = doc.text_path.read_text(encoding="utf-8")
        parsed = parse(text)
        articles, fixed = article_chunks(doc, parsed), fixed_chunks(doc, parsed)
        small = small_article_chunks(doc, parsed)
        small_over = sum(
            estimate_tokens(c.heading_path + c.content) > BKAI_TOKEN_LIMIT for c in small
        )
        sizes = [estimate_tokens(c.content) for c in articles]
        over = sum(size > BKAI_TOKEN_LIMIT for size in sizes)
        totals["article"] += len(articles)
        totals["fixed"] += len(fixed)
        totals["over_bkai"] += over
        blocking, warnings = problems(doc, parsed, text)
        blocked += bool(blocking)
        print(
            f"{doc.slug[:42]:42} art={parsed.diagnostics.article_count:3} "
            f"chunks={len(articles):4} fixed={len(fixed):4} max_tok={max(sizes, default=0):5} "
            f">256={over:3} s256={len(small):4} s256>256={small_over}"
            + ("" if doc.ingest else "  [ingest=false]")
        )
        for message in blocking:
            print(f"    BLOCK {message}")
        for message in warnings:
            print(f"    warn  {message}")
    print(
        f"\nTOTAL article_chunks={totals['article']} fixed_chunks={totals['fixed']} "
        f"article_chunks_over_{BKAI_TOKEN_LIMIT}_tokens={totals['over_bkai']} "
        f"docs_blocked={blocked}"
    )
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
