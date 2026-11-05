import pytest
from qdrant_client import QdrantClient, models

from app.core.config import Settings
from app.services.rag.qdrant_store import (
    DENSE_VECTOR,
    SPARSE_VECTOR,
    CollectionMismatchError,
    collection_name,
    ensure_collection,
    get_async_client,
    get_sync_client,
    point_id,
)


def test_collection_name_slugs_model_and_chunk_set():
    assert collection_name("article", "text-embedding-3-small") == (
        "legal_article_text_embedding_3_small"
    )
    assert collection_name("Clause", "bkai-foundation-models/vietnamese-bi-encoder") == (
        "legal_clause_vietnamese_bi_encoder"
    )


def test_collection_name_rejects_empty_parts():
    with pytest.raises(ValueError):
        collection_name("article", "///")


def test_point_id_is_deterministic_and_content_sensitive():
    first = point_id("luat-qlt-2019", "article", 3, "Điều 1")
    assert first == point_id("luat-qlt-2019", "article", 3, "Điều 1")
    assert first != point_id("luat-qlt-2019", "article", 3, "Điều 1 (sửa)")
    assert first != point_id("luat-qlt-2019", "clause", 3, "Điều 1")


def test_ensure_collection_creates_dense_and_sparse_vectors(qdrant_memory: QdrantClient):
    assert ensure_collection(qdrant_memory, "legal_test", 4) is True

    params = qdrant_memory.get_collection("legal_test").config.params
    assert params.vectors[DENSE_VECTOR].size == 4
    assert params.vectors[DENSE_VECTOR].distance == models.Distance.COSINE
    assert SPARSE_VECTOR in params.sparse_vectors


def test_ensure_collection_twice_is_noop(qdrant_memory: QdrantClient):
    ensure_collection(qdrant_memory, "legal_test", 4)
    assert ensure_collection(qdrant_memory, "legal_test", 4) is False


def test_collection_supports_filtered_dense_search(qdrant_memory: QdrantClient):
    ensure_collection(qdrant_memory, "legal_test", 2)
    qdrant_memory.upsert(
        "legal_test",
        [
            models.PointStruct(
                id=point_id("d", "article", 0, "in force"),
                vector={DENSE_VECTOR: [1.0, 0.0]},
                payload={"status": "in_force"},
            ),
            models.PointStruct(
                id=point_id("d", "article", 1, "repealed"),
                vector={DENSE_VECTOR: [1.0, 0.0]},
                payload={"status": "repealed"},
            ),
        ],
    )
    only_in_force = models.Filter(
        must=[models.FieldCondition(key="status", match=models.MatchValue(value="in_force"))]
    )

    result = qdrant_memory.query_points(
        "legal_test", query=[1.0, 0.0], using=DENSE_VECTOR, query_filter=only_in_force
    )

    assert [p.payload["status"] for p in result.points] == ["in_force"]


def _settings(**overrides) -> Settings:
    return Settings(
        database_url="sqlite+pysqlite://",
        jwt_secret="test-secret-not-for-production-0123456789",
        **overrides,
    )


def test_client_factories_use_settings_without_leaking_key():
    settings = _settings(qdrant_url="https://qdrant.example.com:6333", qdrant_api_key="s3cret")

    assert "s3cret" not in repr(settings)
    sync_client = get_sync_client(settings)
    assert isinstance(sync_client, QdrantClient)
    sync_client.close()
    assert get_async_client(settings) is not None


def _existing_collection(client: QdrantClient, kind: str) -> None:
    if kind == "4-dims":
        ensure_collection(client, "legal_test", 4)
    elif kind == "dot-distance":
        client.create_collection(
            "legal_test",
            vectors_config={
                DENSE_VECTOR: models.VectorParams(size=4, distance=models.Distance.DOT)
            },
            sparse_vectors_config={SPARSE_VECTOR: models.SparseVectorParams()},
        )
    elif kind == "no-sparse":
        client.create_collection(
            "legal_test",
            vectors_config={
                DENSE_VECTOR: models.VectorParams(size=4, distance=models.Distance.COSINE)
            },
        )


@pytest.mark.parametrize(
    ("existing", "dims", "error", "match"),
    [
        pytest.param(
            "4-dims", 8, CollectionMismatchError, "has 4 dims, expected 8 dims", id="dims"
        ),
        pytest.param(None, 0, ValueError, None, id="non-positive-dims"),
        pytest.param("dot-distance", 4, CollectionMismatchError, "cosine", id="distance"),
        pytest.param("no-sparse", 4, CollectionMismatchError, "sparse", id="missing-sparse"),
    ],
)
def test_ensure_collection_rejects_mismatched_or_invalid_config(
    qdrant_memory: QdrantClient, existing, dims, error, match
):
    if existing:
        _existing_collection(qdrant_memory, existing)

    with pytest.raises(error, match=match):
        ensure_collection(qdrant_memory, "legal_test", dims)
