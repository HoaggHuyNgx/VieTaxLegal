import importlib.util
from dataclasses import replace
from pathlib import Path

import pytest
from qdrant_client import QdrantClient

from app.services.rag.index.embeddings import FakeEmbedder, embedding_text
from app.services.rag.index.qdrant_store import ensure_collection
from app.services.rag.ingest.chunking import article_chunks
from app.services.rag.ingest.corpus_manifest import CorpusDoc
from app.services.rag.ingest.ingest import IngestStats, ingest_corpus, ingest_document
from app.services.rag.ingest.legal_parser import parse

EXCERPT = Path(__file__).parent / "fixtures" / "luat-quan-ly-thue-excerpt.txt"
COLLECTION = "legal_test"


def _doc(**overrides) -> CorpusDoc:
    values = {
        "slug": "excerpt",
        "number": "108/2025/QH15",
        "title": "Luật Quản lý thuế",
        "doc_type": "luat",
        "field": "tax",
        "file": "raw/x.docx",
        "sha256": "0" * 64,
        "source_url": "https://example.test/doc",
        "status": "in_force",
    }
    return CorpusDoc(**{**values, **overrides})


def _chunks(doc: CorpusDoc, text: str | None = None):
    return article_chunks(doc, parse(text or EXCERPT.read_text(encoding="utf-8")))


def _by_doc(doc: CorpusDoc, _chunk_set: str):
    return _chunks(doc)


def _run(client, doc, text=None) -> IngestStats:
    stats = IngestStats()
    ingest_document(
        client, COLLECTION, FakeEmbedder(), _chunks(doc, text), doc.slug, batch_size=2, stats=stats
    )
    return stats


@pytest.fixture
def client(qdrant_memory: QdrantClient) -> QdrantClient:
    ensure_collection(qdrant_memory, COLLECTION, 16)
    return qdrant_memory


def test_first_run_embeds_every_chunk_second_run_embeds_none(client):
    first = _run(client, _doc())
    second = _run(client, _doc())

    assert first.embedded == first.chunks == 4
    assert (second.embedded, second.reused) == (0, 4)
    assert client.count(COLLECTION, exact=True).count == 4


def test_edited_text_replaces_old_point_and_removes_stale_one(client):
    original = EXCERPT.read_text(encoding="utf-8")
    _run(client, _doc(), original)

    edited = _run(client, _doc(), original.replace("Phạm vi điều chỉnh", "Phạm vi mới"))

    assert (edited.embedded, edited.deleted_stale) == (1, 1)
    assert client.count(COLLECTION, exact=True).count == 4


def test_status_change_updates_payload_without_re_embedding(client):
    _run(client, _doc(status=None))

    stats = _run(client, _doc(status="in_force", effective_from="2026-07-01"))

    assert stats.embedded == 0
    payloads = [p.payload for p in client.scroll(COLLECTION, limit=10, with_payload=True)[0]]
    assert {p["status"] for p in payloads} == {"in_force"}
    assert {p["effective_from"] for p in payloads} == {"2026-07-01"}


def test_removed_chunks_of_a_document_are_pruned(client):
    text = EXCERPT.read_text(encoding="utf-8")
    _run(client, _doc(), text)

    stats = _run(client, _doc(excluded_articles=("2",)), text)

    # Ordinals are part of the id, so chunks after the removed one get new ids (cheap to re-embed)
    # and every old point of the document is pruned: nothing stale stays retrievable.
    assert stats.deleted_stale >= 1
    assert client.count(COLLECTION, exact=True).count == 3
    locators = {p.payload["locator"] for p in client.scroll(COLLECTION, limit=10)[0]}
    assert locators == {"Điều 1", "Điều 3", "Điều 10"}


def test_ingest_corpus_skips_and_purges_documents_switched_off(client):
    live = _doc()
    _run(client, live)
    off = replace(live, ingest=False)

    stats = ingest_corpus(
        client, COLLECTION, FakeEmbedder(), [off], "article", 4, chunks_for=lambda d, s: []
    )

    assert stats.docs == 0
    assert client.count(COLLECTION, exact=True).count == 0


def test_points_are_self_contained_with_vector_and_payload(client):
    _run(client, _doc())

    point = client.scroll(COLLECTION, limit=1, with_payload=True, with_vectors=True)[0][0]

    assert len(point.vector["dense"]) == 16
    assert point.payload["doc_slug"] == "excerpt"
    assert point.payload["content"].startswith("Điều")
    assert point.payload["locator"].startswith("Điều")


def test_embedding_text_uses_full_or_short_heading_prefix():
    chunk = _chunks(_doc())[3]

    full = embedding_text(chunk)
    short = embedding_text(chunk, short_prefix=True)

    assert full.startswith("Luật Quản lý thuế 108/2025/QH15 > Chương II")
    assert short.startswith("Điều 10. Đăng ký thuế\n")
    assert len(short) < len(full)


def test_full_ingest_purges_documents_removed_from_the_manifest(client):
    both = [_doc(slug="kept"), _doc(slug="removed")]
    ingest_corpus(client, COLLECTION, FakeEmbedder(), both, "article", 8, chunks_for=_by_doc)
    assert client.count(COLLECTION, exact=True).count == 8

    ingest_corpus(
        client, COLLECTION, FakeEmbedder(), both[:1], "article", 8,
        chunks_for=_by_doc, purge_unknown=True,
    )  # fmt: skip

    slugs = {p.payload["doc_slug"] for p in client.scroll(COLLECTION, limit=20)[0]}
    assert slugs == {"kept"}


def test_partial_ingest_without_purge_keeps_other_documents(client):
    docs = [_doc(slug="a"), _doc(slug="b")]
    ingest_corpus(client, COLLECTION, FakeEmbedder(), docs, "article", 8, chunks_for=_by_doc)

    ingest_corpus(client, COLLECTION, FakeEmbedder(), docs[:1], "article", 8, chunks_for=_by_doc)

    assert client.count(COLLECTION, exact=True).count == 8


def test_a_renamed_heading_is_embedded_again(client):
    """The point id covers the content only, but both vectors also cover the heading."""
    doc = _doc()
    _run(client, doc)
    chunks = _chunks(doc)
    renamed = [replace(chunks[0], heading_path=f"{chunks[0].heading_path} (sửa đổi)"), *chunks[1:]]
    stats = IngestStats()

    ingest_document(client, COLLECTION, FakeEmbedder(), renamed, doc.slug, 2, stats)

    assert (stats.embedded, stats.reused) == (1, 3)
    [point] = client.retrieve(COLLECTION, ids=[chunks[0].id], with_payload=True, with_vectors=True)
    assert point.payload["heading_path"] == renamed[0].heading_path
    expected = FakeEmbedder().embed_documents([embedding_text(renamed[0])]).vectors[0]
    assert point.vector["dense"] == pytest.approx(expected, abs=1e-6)
    assert client.count(COLLECTION, exact=True).count == 4


def test_full_vbpl_ingest_without_its_manifest_is_refused(monkeypatch):
    """A full run purges documents it does not know, which would be every imported one."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "corpus_ingest.py"
    spec = importlib.util.spec_from_file_location("corpus_ingest_script", path)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    reached = []
    monkeypatch.setattr(script, "get_embedder", lambda *_: reached.append("embedder"))
    monkeypatch.setattr("sys.argv", ["corpus_ingest.py", "--chunk-set", "vbpl"])

    with pytest.raises(SystemExit) as refused:
        script.main()

    assert refused.value.code == 2 and reached == []
