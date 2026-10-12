import json

from app.services.rag.corpus_manifest import load_manifest


def _entry(slug: str, **extra) -> dict:
    return {
        "slug": slug,
        "number": "1/2026",
        "title": "A",
        "doc_type": "luat",
        "field": "tax",
        "file": "raw/a.docx",
        "sha256": "ab",
        "source_url": "https://example.test",
        **extra,
    }


def test_ingest_defaults_to_true_and_can_be_switched_off(tmp_path):
    path = tmp_path / "manifest.json"
    entries = [_entry("a"), _entry("b", ingest=False)]
    path.write_text(json.dumps({"documents": entries}), encoding="utf-8")

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
