"""Import a filtered slice of th1nhng0/vietnamese-legal-documents into corpus/vbpl/ (not in git).

Needs the `corpus` extra and two parquet files from the dataset's `metadata` and `content` configs.
From backend/:
  .venv/Scripts/python.exe scripts/import_vbpl.py --metadata meta.parquet --content content.parquet

Status comes from the portal snapshot, which can lag reality, so it is recorded in `notes` as not
verified by a person. Documents that fail the structure checks are skipped, never cut by length.
Amending documents only make sense next to the text they amend, so they are skipped too.
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.rag.chunking import ChunkDraft, article_chunks  # noqa: E402
from app.services.rag.corpus_manifest import CORPUS_DIR, _build, load_manifest  # noqa: E402
from app.services.rag.embeddings import _openai_token_counter, embedding_text  # noqa: E402
from app.services.rag.legal_parser import ParsedDocument, parse  # noqa: E402
from app.services.rag.text_extraction import clean_text  # noqa: E402

DATASET_REVISION = "8977887f17be2defae4c5171d55562e1cde7d695"
OUTPUT_DIR = CORPUS_DIR / "vbpl"
DOC_TYPES = {"Luật": "luat", "Bộ luật": "bo_luat", "Nghị định": "nghi_dinh", "Thông tư": "thong_tu",
             "Thông tư liên tịch": "thong_tu_lien_tich"}  # fmt: skip
PARTLY_EXPIRED = "Hết hiệu lực một phần"
STATUSES = {"Còn hiệu lực", PARTLY_EXPIRED}
KEYWORDS = ("thuế", "tài chính", "kế toán", "doanh nghiệp", "đầu tư", "thương mại")
MIN_YEAR = 2020
MIN_CHARS = 300
MAX_EMBED_TOKENS = 8000  # the embedding API rejects a single input above 8192
AMENDING = re.compile(r"sửa đổi|bổ sung|bãi bỏ|sừa đổi", re.IGNORECASE)
BLOCK_TAGS = ["p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table"]


def low(value: str | None) -> str:
    return (value or "").strip().lower()


def issue_year(row: dict) -> int:
    tail = (row["ngay_ban_hanh"] or "")[-4:]
    return int(tail) if tail.isdigit() else 0


def iso_date(value: str | None) -> str | None:
    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", (value or "").strip())
    return f"{match[3]}-{match[2]}-{match[1]}" if match else None


def is_candidate(row: dict) -> bool:
    labels = f"{low(row['linh_vuc'])} | {low(row['nganh'])}"
    return (
        row["pham_vi"] == "Trung ương"
        and row["loai_van_ban"] in DOC_TYPES
        and row["tinh_trang_hieu_luc"] in STATUSES
        and issue_year(row) >= MIN_YEAR
        and not AMENDING.search(row["title"] or "")
        and any(keyword in labels for keyword in KEYWORDS)
    )


def select_rows(rows: list[dict], known_numbers: set[str]) -> dict[str, dict]:
    """Candidates by id, one per document number, preferring the fully in-force record."""
    seen, chosen = set(known_numbers), {}
    ordered = sorted(rows, key=lambda r: (r["tinh_trang_hieu_luc"] == PARTLY_EXPIRED, r["id"]))
    for row in filter(is_candidate, ordered):
        number = low(row["so_ky_hieu"])
        if number and number not in seen:
            seen.add(number)
            chosen[row["id"]] = row
    return chosen


def html_to_text(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "head", "title"]):
        tag.decompose()
    for line_break in soup.find_all("br"):
        line_break.replace_with("\n")
    for tag in soup.find_all(BLOCK_TAGS):
        tag.append("\n")
    for cell in soup.find_all(["td", "th"]):
        cell.append(" ")
    return clean_text(soup.get_text(""))


def structure_issue(text: str, parsed: ParsedDocument) -> str | None:
    diagnostics = parsed.diagnostics
    if len(text) < MIN_CHARS:
        return "empty_or_tiny"
    if not parsed.articles:
        return "no_articles"
    if diagnostics.unexplained_gaps(()):
        return "gaps"
    if diagnostics.skipped_headings:
        return "skipped_headings"
    if diagnostics.empty_articles:
        return "empty_articles"
    if diagnostics.continuation_marker:
        return "continuation_marker"
    return None


def has_oversized_chunk(chunks: list[ChunkDraft], count_tokens) -> bool:
    """True when a chunk cannot be embedded; such a document is skipped rather than truncated."""
    return any(count_tokens([embedding_text(chunk)]) > MAX_EMBED_TOKENS for chunk in chunks)


def manifest_entry(row: dict, slug: str, text: str) -> dict:
    return {
        "slug": slug,
        "number": row["so_ky_hieu"],
        "title": row["title"],
        "doc_type": DOC_TYPES[row["loai_van_ban"]],
        "field": "vbpl",
        "file": f"vbpl/texts/{slug}.txt",
        "text_file": f"vbpl/texts/{slug}.txt",
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_url": "https://vbpl.vn",
        "status": "in_force",
        "partially_expired": row["tinh_trang_hieu_luc"] == PARTLY_EXPIRED,
        "issued_on": iso_date(row["ngay_ban_hanh"]),
        "effective_from": iso_date(row["ngay_co_hieu_luc"]),
        "effective_to": iso_date(row["ngay_het_hieu_luc"]),
        "notes": f"vbpl dataset {DATASET_REVISION[:7]}, status not verified by a person: "
        f"{row['tinh_trang_hieu_luc']}",
    }


def main() -> int:
    import pyarrow.parquet as pq

    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--content", type=Path, required=True)
    args = parser.parse_args()

    known = {low(doc.number) for doc in load_manifest()}
    wanted = select_rows(pq.read_table(args.metadata).to_pylist(), known)
    (OUTPUT_DIR / "texts").mkdir(parents=True, exist_ok=True)
    entries, outcome = [], Counter()
    count = _openai_token_counter(get_settings().embedding_model)
    content = pq.ParquetFile(args.content)
    for batch in content.iter_batches(batch_size=500, columns=["id", "content_html"]):
        ids, bodies = batch.column("id").to_pylist(), batch.column("content_html").to_pylist()
        for doc_id, html in zip(ids, bodies):
            if doc_id not in wanted:
                continue
            text = html_to_text(html or "")
            parsed = parse(text)
            slug = "vbpl-" + re.sub(r"[^A-Za-z0-9_-]", "-", doc_id)
            entry = manifest_entry(wanted[doc_id], slug, text)
            issue = structure_issue(text, parsed)
            if not issue and has_oversized_chunk(article_chunks(_build(entry), parsed), count):
                issue = "chunk_too_long"
            outcome[issue or "imported"] += 1
            if issue:
                continue
            (OUTPUT_DIR / "texts" / f"{slug}.txt").write_text(text, encoding="utf-8", newline="\n")
            entries.append(entry)
    manifest = json.dumps({"documents": entries}, ensure_ascii=False, indent=1)
    (OUTPUT_DIR / "manifest.json").write_text(manifest, encoding="utf-8", newline="\n")
    print(
        f"candidates={len(wanted)} {dict(outcome)} no_content={len(wanted) - sum(outcome.values())}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
