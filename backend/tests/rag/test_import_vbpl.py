import json

import pytest

from app.services.rag.ingest.chunking import article_chunks
from app.services.rag.ingest.corpus_manifest import CORPUS_DIR, load_manifest
from app.services.rag.ingest.legal_parser import parse
from scripts.corpus_import_vbpl import (
    has_oversized_chunk,
    html_to_text,
    is_candidate,
    iso_date,
    load_inventory,
    manifest_entry,
    primary_field,
    select_rows,
    structure_issue,
)

INVENTORY = {"1": "tax", "2": "tax", "3": "tax"}


def _row(**overrides) -> dict:
    values = {
        "id": "1",
        "title": "Thông tư hướng dẫn quản lý thuế",
        "so_ky_hieu": "1/2024/TT-BTC",
        "ngay_ban_hanh": "02/01/2024",
        "ngay_co_hieu_luc": "01/03/2024",
        "ngay_het_hieu_luc": None,
        "loai_van_ban": "Thông tư",
        "nganh": "Tài chính",
        "linh_vuc": "Quản lý thuế",
        "pham_vi": "Trung ương",
        "tinh_trang_hieu_luc": "Còn hiệu lực",
    }
    return {**values, **overrides}


def test_candidate_is_an_inventory_id_of_a_supported_type():
    assert is_candidate(_row(), INVENTORY)
    assert is_candidate(_row(title="Thông tư sửa đổi, bổ sung Thông tư 10"), INVENTORY)
    assert not is_candidate(_row(id="99"), INVENTORY)
    assert not is_candidate(_row(loai_van_ban="Quyết định"), INVENTORY)


@pytest.mark.parametrize(
    ("tags", "field"),
    [("thue;doanh_nghiep", "tax"), ("dau_tu;lao_dong", "enterprise"), ("bhxh", "labor"),
     ("ho_kinh_doanh", "tax"), ("tien_luong", "labor")],
)  # fmt: skip
def test_primary_field_maps_inventory_tags_to_project_fields(tags, field):
    assert primary_field(tags) == field


def test_load_inventory_keeps_core_rows_with_an_id(tmp_path):
    path = tmp_path / "inventory.csv"
    path.write_text(
        "tier,fields,id\nA_core,bhxh,7\nB_review_relation_signal,thue,8\nA_core,thue,\n",
        encoding="utf-8-sig",
    )

    assert load_inventory(path) == {"7": "labor"}


def test_select_prefers_the_in_force_record_and_skips_known_numbers():
    rows = [
        _row(id="1", tinh_trang_hieu_luc="Hết hiệu lực một phần"),
        _row(id="2"),
        _row(id="3", so_ky_hieu="9/2024/TT-BTC"),
    ]

    assert list(select_rows(rows, {"9/2024/tt-btc"}, INVENTORY)) == ["2"]


def test_iso_date_handles_blank_and_bad_values():
    assert iso_date("02/01/2024") == "2024-01-02"
    assert iso_date(None) is None and iso_date("không rõ") is None


def test_manifest_entry_loads_and_flags_partial_expiry(tmp_path):
    row = _row(tinh_trang_hieu_luc="Hết hiệu lực một phần")
    entry = manifest_entry(row, "vbpl-1", "nội dung", "labor")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"documents": [entry]}), encoding="utf-8")

    doc = load_manifest(path)[0]

    assert doc.partially_expired is True and doc.status == "in_force"
    assert doc.field == "labor"
    assert doc.text_path == CORPUS_DIR / "vbpl" / "texts" / "vbpl-1.txt"
    assert "not verified by a person" in doc.notes and "amending" not in doc.notes


def test_manifest_entry_notes_an_amending_document():
    row = _row(title="Thông tư sửa đổi, bổ sung Thông tư 10")

    assert "amending document" in manifest_entry(row, "vbpl-1", "x", "tax")["notes"]


def test_the_partial_expiry_flag_reaches_the_chunk_payload():
    row = _row(tinh_trang_hieu_luc="Hết hiệu lực một phần")
    entry = manifest_entry(row, "vbpl-1", "x", "tax")
    from app.services.rag.ingest.corpus_manifest import _build

    text = "Điều 1. Phạm vi\nThông tư này quy định về thuế.\n"

    chunks = article_chunks(_build(entry), parse(text))

    assert chunks[0].to_payload()["partially_expired"] is True


def test_structure_issue_reports_documents_without_articles():
    assert structure_issue("ngắn", parse("ngắn")) == "empty_or_tiny"
    long_text = "Văn bản không chia điều. " * 30

    assert structure_issue(long_text, parse(long_text)) == "no_articles"


def test_oversized_chunk_is_detected_with_the_given_counter():
    entry = manifest_entry(_row(), "vbpl-1", "x", "tax")
    from app.services.rag.ingest.corpus_manifest import _build

    chunks = article_chunks(_build(entry), parse("Điều 1. Phạm vi\nNội dung của điều này.\n"))

    assert has_oversized_chunk(chunks, lambda texts: 9000) is True
    assert has_oversized_chunk(chunks, lambda texts: 10) is False


def test_html_to_text_keeps_article_headings_on_their_own_lines():
    pytest.importorskip("bs4")
    html = "<html><head><title>x</title></head><body><p><b>Điều 1.</b> Phạm vi</p></body></html>"

    text = html_to_text(html)

    assert "Điều 1. Phạm vi\n" in text and "x" not in text.split("\n")
