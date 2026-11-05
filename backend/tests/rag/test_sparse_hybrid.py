import asyncio
import unicodedata

from qdrant_client import AsyncQdrantClient, QdrantClient, models

from app.services.rag import sparse
from app.services.rag.chunking import ChunkDraft
from app.services.rag.embeddings import FakeEmbedder, embedding_text
from app.services.rag.ingest import backfill_sparse, sparse_text
from app.services.rag.qdrant_retriever import QdrantRetriever
from app.services.rag.qdrant_store import DENSE_VECTOR, SPARSE_VECTOR, ensure_collection

COLLECTION = "legal_hybrid_test"


def _chunk(n: int, content: str) -> ChunkDraft:
    return ChunkDraft(
        doc_slug="doc", doc_number="1/2026", doc_title="Luật thử", doc_type="luat", field="tax",
        status="in_force", issued_on=None, effective_from=None, effective_to=None,
        source_url="https://example.test", chunk_set="article", ordinal=n, article_no=n,
        article_nos=(n,), clause_no=None, point=None, locator=f"Điều {n}",
        heading_path=f"Luật thử > Điều {n}", content=content, content_sha256="x",
        char_start=0, char_end=len(content),
    )  # fmt: skip


CHUNKS = [
    _chunk(1, "Điều kiện khấu trừ thuế giá trị gia tăng đầu vào"),
    _chunk(2, "Thời gian thử việc tối đa đối với người lao động"),
    _chunk(3, "Mức giảm trừ gia cảnh của người nộp thuế"),
]


def test_encoder_folds_accents_and_is_unicode_form_independent():
    nfc = sparse.encode_document("Khấu trừ thuế")
    nfd = sparse.encode_document(unicodedata.normalize("NFD", "Khấu trừ thuế"))
    folded = sparse.encode_document("khau tru thue")

    assert nfc == nfd == folded
    assert sparse.fold("Đầu vào") == "dau vao"


def test_encoder_emits_unigrams_and_bigrams_deterministically():
    assert sparse.terms("Thuế suất 8%") == ["thue", "suat", "8", "thue suat", "suat 8"]
    vector = sparse.encode_document("thuế thuế suất")
    assert vector.indices == sorted(vector.indices)
    assert len(vector.indices) == len(set(vector.indices))
    assert sparse.encode_document("thuế thuế suất") == vector


def test_document_weights_saturate_and_shrink_with_length():
    short = sparse.encode_document("thuế suất")
    long_text = "thuế suất " + " ".join(f"từ{i}" for i in range(300))
    long = sparse.encode_document(long_text)
    index = sparse.encode_query("thuế").indices[0]

    short_weight = short.values[short.indices.index(index)]
    long_weight = long.values[long.indices.index(index)]
    assert 0 < long_weight < short_weight  # same term, longer chunk -> weaker evidence
    twice = sparse.encode_document("thuế thuế suất")
    assert short_weight < twice.values[twice.indices.index(index)] < 2 * short_weight


def test_query_vector_is_binary_over_unique_terms():
    query = sparse.encode_query("thuế thuế suất")

    assert set(query.values) == {1.0}
    assert len(query.indices) == len(set(sparse.terms("thuế thuế suất")))


def test_encoder_handles_empty_text():
    for vector in (sparse.encode_document(""), sparse.encode_query("")):
        assert vector.indices == [] and vector.values == []


def _seeded_sync() -> QdrantClient:
    client = QdrantClient(":memory:")
    ensure_collection(client, COLLECTION, 16)
    embedder = FakeEmbedder()
    vectors = embedder.embed_documents([embedding_text(c) for c in CHUNKS]).vectors
    client.upsert(
        COLLECTION,
        [
            models.PointStruct(id=c.id, vector={DENSE_VECTOR: v}, payload=c.to_payload())
            for c, v in zip(CHUNKS, vectors)
        ],
    )
    return client


def test_backfill_adds_sparse_vectors_from_payload_and_is_idempotent():
    client = _seeded_sync()

    assert backfill_sparse(client, COLLECTION, batch_size=2) == 3
    assert backfill_sparse(client, COLLECTION, batch_size=2) == 3

    found = client.query_points(
        COLLECTION, query=sparse.encode_query("khấu trừ thuế"), using=SPARSE_VECTOR, limit=1
    )
    assert found.points[0].payload["locator"] == "Điều 1"


def test_sparse_text_matches_what_backfill_indexes():
    assert (
        sparse_text(CHUNKS[0])
        == "Luật thử > Điều 1\nĐiều kiện khấu trừ thuế giá trị gia tăng đầu vào"
    )


async def _hybrid_retriever(**kwargs) -> QdrantRetriever:
    sync = _seeded_sync()
    backfill_sparse(sync, COLLECTION)
    # The async client needs its own in-memory store; rebuild it from the sync one's points.
    client = AsyncQdrantClient(":memory:")
    await client.create_collection(
        COLLECTION,
        vectors_config={
            DENSE_VECTOR: models.VectorParams(size=16, distance=models.Distance.COSINE)
        },
        sparse_vectors_config={
            SPARSE_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )
    points, _ = sync.scroll(COLLECTION, limit=10, with_payload=True, with_vectors=True)
    await client.upsert(
        COLLECTION,
        [models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points],
    )
    return QdrantRetriever(client, FakeEmbedder(), COLLECTION, top_k=3, mode="hybrid", **kwargs)


def test_hybrid_lets_the_lexical_match_win_when_dense_is_uninformative():
    async def run():
        retriever = await _hybrid_retriever()
        return await retriever.search("khấu đầu vào")

    outcome = asyncio.run(run())

    assert outcome.hits[0].payload["locator"] == "Điều 1"
    assert len(outcome.hits) == 3


def test_hybrid_respects_the_in_force_filter():
    async def run():
        retriever = await _hybrid_retriever()
        # Flip the stored status of the lexical match, then search again.
        await retriever._client.set_payload(
            COLLECTION, payload={"status": "expired"}, points=[CHUNKS[0].id]
        )
        return await retriever.search("điều kiện khấu trừ thuế đầu vào")

    outcome = asyncio.run(run())

    assert "Điều 1" not in [h.payload["locator"] for h in outcome.hits]
