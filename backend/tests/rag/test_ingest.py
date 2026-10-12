from dataclasses import replace
from pathlib import Path

import pytest
from qdrant_client import QdrantClient

from app.services.rag.chunking import article_chunks
from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.embeddings import FakeEmbedder, embedding_text
from app.services.rag.ingest import IngestStats, ingest_corpus, ingest_document
from app.services.rag.legal_parser import parse
from app.services.rag.qdrant_store import ensure_collection

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
