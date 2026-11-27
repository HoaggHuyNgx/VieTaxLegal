"""Rerank seam. `NoopReranker` keeps the order; `CohereReranker` calls the Cohere Rerank API.

A reranker reorders (and may truncate) the fused candidates. Whether to keep one is decided from
the experiment numbers (P9), not assumed.
"""

from typing import TYPE_CHECKING, Protocol

import httpx
from pydantic import SecretStr

if TYPE_CHECKING:
    from app.services.rag.retrieve.qdrant_retriever import Hit

COHERE_RERANK_URL = "https://api.cohere.com/v2/rerank"
COHERE_TIMEOUT_SECONDS = 8.0


class Reranker(Protocol):
    async def rerank(self, query: str, hits: "list[Hit]", limit: int) -> "list[Hit]": ...


class NoopReranker:
    async def rerank(self, query: str, hits: "list[Hit]", limit: int) -> "list[Hit]":
        del query  # unused: order is kept
        return hits[:limit]


class CohereReranker:
    """Cross-encoder rerank via Cohere: one API call per query, billed per search."""

    def __init__(
        self,
        api_key: SecretStr | None,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,  # tests pass a MockTransport
    ) -> None:
        if not api_key or not api_key.get_secret_value().strip():
            raise ValueError("COHERE_API_KEY is required when RAG_RERANK_MODEL is set.")
        self._api_key, self._model, self._transport = api_key, model, transport
        self.fallbacks = 0  # calls that kept the original order; eval reports it

    async def _order(self, query: str, hits: "list[Hit]", limit: int) -> list[int]:
        documents = [
            f"{hit.payload.get('heading_path', '')}\n{hit.payload.get('content', '')}"
            for hit in hits
        ]
        body = {"model": self._model, "query": query, "documents": documents, "top_n": limit}
        headers = {"Authorization": f"Bearer {self._api_key.get_secret_value()}"}
        async with httpx.AsyncClient(
            transport=self._transport, timeout=COHERE_TIMEOUT_SECONDS
        ) as client:
            response = await client.post(COHERE_RERANK_URL, json=body, headers=headers)
            response.raise_for_status()
            # Cohere returns results sorted by relevance; `index` points into `documents`.
            return [int(item["index"]) for item in response.json()["results"]]

    async def rerank(self, query: str, hits: "list[Hit]", limit: int) -> "list[Hit]":
        if not hits:
            return []
        try:
            order = await self._order(query, hits, limit)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            order = []  # outage, rate limit or unexpected reply: fall back to the original order
        self.fallbacks += not order
        ranked = [hits[n] for n in dict.fromkeys(order) if 0 <= n < len(hits)]
        rest = [hit for hit in hits if hit not in ranked]  # unranked candidates keep their order
        return (ranked + rest)[:limit]
