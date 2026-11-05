import hashlib
import json

import pytest

from app.services.rag.chunking import article_chunks
from app.services.rag.corpus_manifest import ManifestError, load_manifest, verify_raw_file
from app.services.rag.legal_parser import parse


def _entry(**overrides) -> dict:
    entry = {
        "slug": "doc-a",
        "number": "1/2026",
        "title": "A",
        "doc_type": "luat",
        "field": "tax",
        "file": "raw/a.docx",
        "sha256": "ab",
        "source_url": "https://example.test",
    }
    return {**entry, **overrides}


def _write(tmp_path, *entries):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"documents": list(entries)}), encoding="utf-8")
    return path


def test_unverified_fields_default_to_none(tmp_path):
    doc = load_manifest(_write(tmp_path, _entry()))[0]

    assert doc.status is None and doc.effective_from is None
    assert doc.excluded_articles == () and doc.known_gaps == ()


def test_status_must_be_a_known_value(tmp_path):
    with pytest.raises(ManifestError, match="invalid status"):
        load_manifest(_write(tmp_path, _entry(status="maybe")))


def test_missing_field_and_duplicate_slug_fail_loudly(tmp_path):
    broken = _entry()
    del broken["sha256"]
    with pytest.raises(ManifestError, match="missing field"):
        load_manifest(_write(tmp_path, broken))
    with pytest.raises(ManifestError, match="Duplicate"):
        load_manifest(_write(tmp_path, _entry(), _entry()))


def test_verify_raw_file_detects_changed_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.rag.corpus_manifest.CORPUS_DIR", tmp_path)
    (tmp_path / "raw").mkdir()
    raw = tmp_path / "raw" / "a.docx"
    raw.write_bytes(b"hello")
    doc = load_manifest(_write(tmp_path, _entry(sha256=hashlib.sha256(b"hello").hexdigest())))[0]

    assert verify_raw_file(doc) is True
    raw.write_bytes(b"tampered")
    assert verify_raw_file(doc) is False


def test_committed_corpus_parses_without_unexplained_gaps():
    """Phase 3 success criterion: no unexplained gaps across the committed corpus texts."""
    docs = load_manifest()
    assert docs, "corpus/manifest.json lists no documents"
    for doc in docs:
        parsed = parse(doc.text_path.read_text(encoding="utf-8"))
        assert parsed.diagnostics.article_count > 0, doc.slug
        assert parsed.diagnostics.unexplained_gaps(doc.known_gaps) == [], doc.slug
        assert article_chunks(doc, parsed), doc.slug


def test_ingest_defaults_to_true_and_can_be_switched_off(tmp_path):
    path = _write(tmp_path, _entry(slug="a"), _entry(slug="b", ingest=False))

    docs = {doc.slug: doc for doc in load_manifest(path)}

    assert docs["a"].ingest is True
    assert docs["b"].ingest is False


def test_committed_manifest_indexes_the_consolidated_labour_code_not_the_base_text():
    docs = {doc.slug: doc for doc in load_manifest()}

    base = docs["bo-luat-lao-dong-45-2019-qh14"]
    assert base.ingest is False
    assert base.superseded_by == "bo-luat-lao-dong-vbhn-18-2026-vbhn-vpqh"
    assert docs[base.superseded_by].ingest is True
    assert [doc.slug for doc in docs.values() if not doc.ingest] == [base.slug]


def test_committed_manifest_has_verified_status_fields_and_no_open_truncation():
    docs = load_manifest()

    assert all(doc.status == "in_force" and doc.effective_from for doc in docs)
    assert not any(doc.truncated for doc in docs)
