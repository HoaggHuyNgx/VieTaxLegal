"""Thin wrapper over Qdrant: collection naming, schema, point ids and client factories.

The index is a rebuildable derivative of ``backend/corpus/``; nothing here is a source of truth.
Collection names come only from config and the embedding model id, never from user input.
"""

import hashlib
import re
import warnings
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import AsyncQdrantClient, QdrantClient, models

from app.core.config import Settings, get_settings

DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"

KEYWORD_INDEXES = ("status", "field", "doc_slug")
INTEGER_INDEXES = ("article_no",)

_POINT_NAMESPACE = uuid5(NAMESPACE_URL, "vietaxlegal/rag/chunk")


class CollectionMismatchError(ValueError):
    """An existing collection does not match the requested embedding dimensions."""


def collection_name(chunk_set: str, model: str) -> str:
    """``legal_<chunk_set>_<model_slug>``, e.g. ``legal_article_text_embedding_3_small``."""
    model_slug = re.sub(r"[^a-z0-9]+", "_", model.rsplit("/", 1)[-1].lower()).strip("_")
    chunk_slug = re.sub(r"[^a-z0-9_]+", "_", chunk_set.lower()).strip("_")
    if not model_slug or not chunk_slug:
        raise ValueError("chunk_set and model must contain at least one alphanumeric character.")
    return f"legal_{chunk_slug}_{model_slug}"


def point_id(doc_slug: str, chunk_set: str, ordinal: int, content: str) -> str:
    """Deterministic id: re-ingesting identical text is an idempotent upsert, edited text is new."""
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return str(uuid5(_POINT_NAMESPACE, f"{doc_slug}|{chunk_set}|{ordinal}|{digest}"))


def _client_kwargs(settings: Settings) -> dict:
    api_key = settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None
    return {"url": settings.qdrant_url, "api_key": api_key, "check_compatibility": False}


def get_sync_client(settings: Settings | None = None) -> QdrantClient:
    return QdrantClient(**_client_kwargs(settings or get_settings()))


def get_async_client(settings: Settings | None = None) -> AsyncQdrantClient:
    return AsyncQdrantClient(**_client_kwargs(settings or get_settings()))


def ensure_collection(client: QdrantClient, name: str, dimensions: int) -> bool:
    """Create the collection with dense + sparse vectors if absent. Returns True if created.

    Calling it again is a no-op; calling it with different dimensions raises
    ``CollectionMismatchError`` instead of silently mixing embedding spaces.
    """
    if dimensions < 1:
        raise ValueError("dimensions must be positive.")

    if client.collection_exists(name):
        _check_schema(client, name, dimensions)
        # Idempotent; repairs a collection whose first creation died before the indexes.
        _create_payload_indexes(client, name)
        return False

    client.create_collection(
        collection_name=name,
        vectors_config={
            DENSE_VECTOR: models.VectorParams(size=dimensions, distance=models.Distance.COSINE)
        },
        # Created now so enabling hybrid search later does not require rebuilding the collection.
        sparse_vectors_config={
            SPARSE_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )
    _create_payload_indexes(client, name)
    return True


def _check_schema(client: QdrantClient, name: str, dimensions: int) -> None:
    params = client.get_collection(name).config.params
    dense = params.vectors.get(DENSE_VECTOR) if isinstance(params.vectors, dict) else None
    if dense is None or dense.size != dimensions:
        found = f"{dense.size} dims" if dense is not None else "no dense vector"
        raise CollectionMismatchError(
            f"Collection '{name}' has {found}, expected {dimensions} dims. "
            "Delete it or use a different embedding model."
        )
    if dense.distance != models.Distance.COSINE or SPARSE_VECTOR not in (
        params.sparse_vectors or {}
    ):
        raise CollectionMismatchError(
            f"Collection '{name}' must use cosine distance and a '{SPARSE_VECTOR}' vector. "
            "Delete it and re-ingest."
        )


def _create_payload_indexes(client: QdrantClient, name: str) -> None:
    with warnings.catch_warnings():
        # Local (in-memory) mode ignores payload indexes and warns; the server honours them.
        warnings.simplefilter("ignore", UserWarning)
        for field in KEYWORD_INDEXES:
            client.create_payload_index(name, field, models.PayloadSchemaType.KEYWORD)
        for field in INTEGER_INDEXES:
            client.create_payload_index(name, field, models.PayloadSchemaType.INTEGER)
