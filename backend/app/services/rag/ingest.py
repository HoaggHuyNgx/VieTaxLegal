"""Idempotent corpus -> Qdrant ingest.

Point ids are deterministic (doc, chunk set, ordinal, content hash), so a re-run only embeds chunks
whose id is missing, refreshes document-level payload (status, dates) on the rest, and deletes
points of the same document that no longer exist in the corpus. No chunk text is ever logged.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient, models

from app.services.rag import sparse
from app.services.rag.chunking import ChunkDraft, article_chunks, fixed_chunks
from app.services.rag.chunking_small import small_article_chunks
from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.embeddings import EmbeddingProvider, embedding_text
from app.services.rag.legal_parser import ParsedDocument, parse
from app.services.rag.qdrant_store import DENSE_VECTOR, SPARSE_VECTOR, ensure_collection

CHUNKERS: dict[str, Callable[[CorpusDoc, ParsedDocument], list[ChunkDraft]]] = {
    "article": article_chunks,
    "article_s256": small_article_chunks,
    "fixed": fixed_chunks,
}
# Fields copied from the manifest that may change without the chunk text changing.
DOC_LEVEL_FIELDS = (
    "heading_path",
    "locator",
    "doc_title",
    "doc_number",
    "doc_type",
    "field",
    "status",
    "issued_on",
    "effective_from",
    "effective_to",
    "source_url",
)


@dataclass
class IngestStats:
    docs: int = 0
    chunks: int = 0
    embedded: int = 0
    reused: int = 0
    deleted_stale: int = 0
    tokens: int = 0


def _sparse_input(heading_path: str, content: str) -> str:
    return f"{heading_path}\n{content}"


def sparse_text(chunk: ChunkDraft) -> str:
    return _sparse_input(chunk.heading_path, chunk.content)


def backfill_sparse(client: QdrantClient, collection: str, batch_size: int = 256) -> int:
    """Write sparse vectors for every point from its stored payload (no re-embedding, no cost).

    Idempotent: re-running overwrites the same sparse vectors.
    """
    written, offset = 0, None
    while True:
        points, offset = client.scroll(
            collection, limit=batch_size, offset=offset, with_payload=True, with_vectors=False
        )
        if points:
            client.update_vectors(
                collection,
                points=[
                    models.PointVectors(
                        id=p.id,
                        vector={
                            SPARSE_VECTOR: sparse.encode_document(
                                _sparse_input(
                                    p.payload.get("heading_path", ""), p.payload.get("content", "")
                                )
                            )
                        },
                    )
                    for p in points
                ],
            )
            written += len(points)
        if offset is None:
            return written


def build_chunks(doc: CorpusDoc, chunk_set: str) -> list[ChunkDraft]:
    parsed = parse(doc.text_path.read_text(encoding="utf-8"))
    return CHUNKERS[chunk_set](doc, parsed)


def _doc_filter(doc_slug: str) -> models.FilterSelector:
    condition = models.FieldCondition(key="doc_slug", match=models.MatchValue(value=doc_slug))
    return models.FilterSelector(filter=models.Filter(must=[condition]))


def _existing_ids(client: QdrantClient, collection: str, ids: list[str]) -> set[str]:
    found = client.retrieve(collection, ids=ids, with_payload=False, with_vectors=False)
    return {str(point.id) for point in found}


def ingest_document(
    client: QdrantClient,
    collection: str,
    provider: EmbeddingProvider,
    chunks: list[ChunkDraft],
    doc_slug: str,
    batch_size: int,
    stats: IngestStats,
) -> None:
    ids = [chunk.id for chunk in chunks]
    existing = _existing_ids(client, collection, ids) if ids else set()
    missing = [chunk for chunk in chunks if chunk.id not in existing]

    for start in range(0, len(missing), batch_size):
        batch = missing[start : start + batch_size]
        result = provider.embed_documents(
            [embedding_text(chunk, provider.short_prefix) for chunk in batch]
        )
        stats.tokens += result.tokens
        client.upsert(
            collection,
            points=[
                models.PointStruct(
                    id=chunk.id,
                    vector={
                        DENSE_VECTOR: vector,
                        SPARSE_VECTOR: sparse.encode_document(sparse_text(chunk)),
                    },
                    payload=chunk.to_payload(),
                )
                for chunk, vector in zip(batch, result.vectors)
            ],
        )

    for chunk in chunks:
        if chunk.id in existing:
            client.set_payload(
                collection,
                payload={name: getattr(chunk, name) for name in DOC_LEVEL_FIELDS},
                points=[chunk.id],
            )

    stale = models.Filter(
        must=[models.FieldCondition(key="doc_slug", match=models.MatchValue(value=doc_slug))],
        must_not=[models.HasIdCondition(has_id=ids)],
    )
    before = client.count(collection, count_filter=stale, exact=True).count
    if before:
        client.delete(collection, points_selector=models.FilterSelector(filter=stale))
    stats.deleted_stale += before
    stats.chunks += len(chunks)
    stats.embedded += len(missing)
    stats.reused += len(existing)
    stats.docs += 1


def ingest_corpus(
    client: QdrantClient,
    collection: str,
    provider: EmbeddingProvider,
    docs: list[CorpusDoc],
    chunk_set: str,
    batch_size: int,
    chunks_for: Callable[[CorpusDoc, str], list[ChunkDraft]] = build_chunks,
    on_progress: Callable[[str, IngestStats], Any] | None = None,
    purge_unknown: bool = False,
) -> IngestStats:
    """Ingest `docs` (the whole manifest). `ingest=false` docs are purged from the index.

    With `purge_unknown`, points of documents that are no longer in the manifest are deleted too.
    """
    ensure_collection(client, collection, provider.dims)
    stats = IngestStats()
    if purge_unknown:
        known = models.FieldCondition(
            key="doc_slug", match=models.MatchAny(any=[doc.slug for doc in docs])
        )
        client.delete(
            collection,
            points_selector=models.FilterSelector(filter=models.Filter(must_not=[known])),
        )
    for doc in docs:
        if not doc.ingest:  # switched off in the manifest: make sure nothing of it stays indexed
            client.delete(collection, points_selector=_doc_filter(doc.slug))
            continue
        ingest_document(
            client, collection, provider, chunks_for(doc, chunk_set), doc.slug, batch_size, stats
        )
        if on_progress:
            on_progress(doc.slug, stats)
    return stats
