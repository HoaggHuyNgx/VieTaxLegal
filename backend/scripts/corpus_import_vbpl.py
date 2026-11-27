"""Import the documents of a coverage inventory from th1nhng0/vietnamese-legal-documents into
corpus/vbpl/ (not in git).

Needs the `corpus` extra, the dataset's `metadata` and `content` parquet files and the inventory CSV
(columns `tier`, `fields`, `id`; only `A_core` rows are imported). From backend/:
  .venv/Scripts/python.exe scripts/corpus_import_vbpl.py --metadata m.parquet --content c.parquet \
      --inventory inventory.csv

Status comes from the portal snapshot, which can lag reality, so it is recorded in `notes` as not
verified by a person. Documents that fail the structure checks are skipped, never cut by length.
Amending documents are kept (the base texts are not consolidated, so they carry the current rule)
and marked in `notes`.
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.rag.index.embeddings import _openai_token_counter, embedding_text  # noqa: E402
from app.services.rag.ingest.chunking import ChunkDraft, article_chunks  # noqa: E402
from app.services.rag.ingest.corpus_manifest import CORPUS_DIR, _build, load_manifest  # noqa: E402
from app.services.rag.ingest.legal_parser import ParsedDocument, parse  # noqa: E402
from app.services.rag.ingest.text_extraction import clean_text  # noqa: E402

DATASET_REVISION = "8977887f17be2defae4c5171d55562e1cde7d695"
OUTPUT_DIR = CORPUS_DIR / "vbpl"
DOC_TYPES = {"Luật": "luat", "Bộ luật": "bo_luat", "Nghị định": "nghi_dinh", "Thông tư": "thong_tu",
             "Thông tư liên tịch": "thong_tu_lien_tich", "Văn bản hợp nhất": "vbhn"}  # fmt: skip
PARTLY_EXPIRED = "Hết hiệu lực một phần"
CORE_TIER = "A_core"
# Inventory tags -> the project's three fields, first match wins (a tax + enterprise text is tax).
FIELD_PRIORITY = (("thue", "tax"), ("ho_kinh_doanh", "tax"), ("doanh_nghiep", "enterprise"),
                  ("dau_tu", "enterprise"), ("lao_dong", "labor"), ("bhxh", "labor"),
                  ("tien_luong", "labor"))  # fmt: skip
MIN_CHARS = 300
MAX_EMBED_TOKENS = 8000  # the embedding API rejects a single input above 8192
AMENDING = re.compile(r"sửa đổi|bổ sung|bãi bỏ|sừa đổi", re.IGNORECASE)
BLOCK_TAGS = ["p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table"]


def low(value: str | None) -> str:
    return (value or "").strip().lower()


def iso_date(value: str | None) -> str | None:
    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", (value or "").strip())
    return f"{match[3]}-{match[2]}-{match[1]}" if match else None


def primary_field(tags: str) -> str:
    present = set(tags.split(";"))
    return next(field for tag, field in FIELD_PRIORITY if tag in present)


def load_inventory(path: Path) -> dict[str, str]:
    """Dataset id -> project field for the inventory's core rows."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["tier"] == CORE_TIER and r["id"]]
    return {row["id"]: primary_field(row["fields"]) for row in rows}


def is_candidate(row: dict, inventory: dict[str, str]) -> bool:
    return row["id"] in inventory and row["loai_van_ban"] in DOC_TYPES


def select_rows(
    rows: list[dict], known_numbers: set[str], inventory: dict[str, str]
) -> dict[str, dict]:
    """Candidates by id, one per document number, preferring the fully in-force record."""
    seen, chosen = set(known_numbers), {}
    ordered = sorted(rows, key=lambda r: (r["tinh_trang_hieu_luc"] == PARTLY_EXPIRED, r["id"]))
    for row in (r for r in ordered if is_candidate(r, inventory)):
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


def manifest_entry(row: dict, slug: str, text: str, field: str) -> dict:
    amending = "; amending document" if AMENDING.search(row["title"] or "") else ""
    return {
        "slug": slug,
        "number": row["so_ky_hieu"],
        "title": row["title"],
        "doc_type": DOC_TYPES[row["loai_van_ban"]],
        "field": field,
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
        f"{row['tinh_trang_hieu_luc']}{amending}",
    }


def main() -> int:
    import pyarrow.parquet as pq

    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--content", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()

    known = {low(doc.number) for doc in load_manifest()}
    inventory = load_inventory(args.inventory)
    wanted = select_rows(pq.read_table(args.metadata).to_pylist(), known, inventory)
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
            entry = manifest_entry(wanted[doc_id], slug, text, inventory[doc_id])
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
