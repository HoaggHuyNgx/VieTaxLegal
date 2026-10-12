"""Dense retriever over Qdrant (stage 1): embed the query, filtered vector search, map to sources.

Failure policy: an embedding or Qdrant outage returns an empty result (the system prompt then makes
the model say it cannot verify) and logs only the error type, never the query text.
"""

import asyncio
import logging
import time
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from qdrant_client import AsyncQdrantClient, models

from app.core.config import Settings, get_settings
from app.services.chat_retriever import Citation, RetrievalResult, RetrievedContext
from app.services.rag import sparse
from app.services.rag.embeddings import EmbeddingProvider, get_embedder
from app.services.rag.fusion import rrf_fuse
from app.services.rag.qdrant_store import (
    DENSE_VECTOR,
    SPARSE_VECTOR,
    collection_name,
    get_async_client,
)
from app.services.rag.reranker import Reranker

logger = logging.getLogger(__name__)
EXCERPT_CHARS = 300


@dataclass(frozen=True)
class Hit:
    id: str
    score: float
    payload: dict[str, Any]


@dataclass
class SearchOutcome:
    hits: list[Hit] = field(default_factory=list)
    embed_ms: float = 0.0
    search_ms: float = 0.0


class QdrantRetriever:
    def __init__(
        self,
        client: AsyncQdrantClient,
        embedder: EmbeddingProvider,
        collection: str,
        top_k: int,
        min_similarity: float = 0.0,
        require_in_force: bool = True,
        mode: str = "dense",
        reranker: Reranker | None = None,
    ) -> None:
        self._client, self._embedder, self._collection = client, embedder, collection
        self._mode, self._reranker = mode, reranker
        self._top_k, self._min_similarity = top_k, min_similarity
        self._require_in_force = require_in_force

    def _filter(self) -> models.Filter | None:
        if not self._require_in_force:
            return None
        condition = models.FieldCondition(key="status", match=models.MatchValue(value="in_force"))
        return models.Filter(must=[condition])

    async def search(self, query: str, limit: int | None = None) -> SearchOutcome:
        """Dense search with per-stage timings (also used by the eval harness)."""
        started = time.perf_counter()
        vector = await self._embedder.aembed_query(unicodedata.normalize("NFC", query))
        embedded = time.perf_counter()
        wanted = limit or self._top_k
        fetch = max(wanted * 2, 10) if self._reranker else wanted  # rerank needs spare candidates
        if self._mode == "hybrid":
            hits = await self._hybrid(query, vector, fetch)
        elif self._mode == "sparse":  # lexical-only ablation
            points = await self._sparse_points(query, fetch)
            hits = [Hit(str(p.id), p.score, p.payload or {}) for p in points]
        else:
            points = await self._dense_points(vector, fetch)
            hits = [Hit(str(p.id), p.score, p.payload or {}) for p in points]
        if self._reranker:
            hits = await self._reranker.rerank(query, hits, wanted)
        finished = time.perf_counter()
        return SearchOutcome(hits, (embedded - started) * 1000, (finished - embedded) * 1000)

    async def _dense_points(self, vector: list[float], limit: int):
        response = await self._client.query_points(
            self._collection,
            query=vector,
            using=DENSE_VECTOR,
            query_filter=self._filter(),
            limit=limit,
            score_threshold=self._min_similarity or None,
            with_payload=True,
        )
        return response.points

    async def _sparse_points(self, query: str, limit: int):
        response = await self._client.query_points(
            self._collection,
            query=sparse.encode_query(query),
            using=SPARSE_VECTOR,
            query_filter=self._filter(),
            limit=limit,
            with_payload=True,
        )
        return response.points

    async def _hybrid(self, query: str, vector: list[float], limit: int) -> list[Hit]:
        """Dense and sparse candidates fused with RRF here (deterministic tie-break, see fusion).

        `min_similarity` is a cosine threshold, so it only applies to the dense candidate list;
        the returned score is the rank-based RRF score.
        """
        depth = max(limit * 4, 20)
        dense, lexical = await asyncio.gather(
            self._dense_points(vector, depth), self._sparse_points(query, depth)
        )
        by_id = {str(p.id): p for p in [*lexical, *dense]}
        fused = rrf_fuse([[str(p.id) for p in dense], [str(p.id) for p in lexical]])
        return [Hit(i, score, by_id[i].payload or {}) for i, score in fused[:limit]]

    async def retrieve(self, query: str) -> RetrievalResult:
        try:
            outcome = await self.search(query)
        except Exception as error:  # degrade to "no sources"; never raise into the chat stream
            logger.warning("RAG retrieval failed: %s", type(error).__name__)
            return RetrievalResult()
        return hits_to_result(outcome.hits)


def hits_to_result(hits: list[Hit]) -> RetrievalResult:
    contexts, citations = [], []
    for number, hit in enumerate(hits, start=1):
        payload = hit.payload
        citation_id = str(number)
        contexts.append(
            RetrievedContext(
                content=f"{payload.get('heading_path', '')}\n{payload.get('content', '')}",
                citation_id=citation_id,
            )
        )
        citations.append(
            Citation(
                id=citation_id,
                title=payload.get("doc_title", ""),
                url=payload.get("source_url"),
                excerpt=str(payload.get("content", ""))[:EXCERPT_CHARS],
                doc_number=payload.get("doc_number"),
                locator=payload.get("locator"),
                issued_on=payload.get("issued_on"),
            )
        )
    return RetrievalResult(contexts, citations)


def build_retriever(settings: Settings, client: AsyncQdrantClient, embedder) -> QdrantRetriever:
    return QdrantRetriever(
        client,
        embedder,
        collection_name(settings.rag_chunk_set, embedder.model),
        settings.rag_top_k,
        settings.rag_min_similarity,
        settings.rag_require_in_force,
        settings.rag_retrieval_mode,
    )


@lru_cache
def get_qdrant_retriever() -> QdrantRetriever:
    settings = get_settings()
    return build_retriever(settings, get_async_client(settings), get_embedder(settings))


async def close_qdrant_retriever() -> None:
    """Close the shared client on app shutdown (no-op if RAG was never used)."""
    if get_qdrant_retriever.cache_info().currsize:
        await get_qdrant_retriever()._client.close()
        get_qdrant_retriever.cache_clear()
