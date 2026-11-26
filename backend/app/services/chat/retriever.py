"""The single seam between chat and RAG.

Chat only knows the `Retriever` protocol and its result types (`Citation`, `RetrievedContext`,
`RetrievalResult`). `get_retriever()` returns `NullRetriever` (no sources) when RAG is off or
fails to start, otherwise the Qdrant retriever wrapped by the optional planner/rerank/gate steps.
With RAG on, any failure is reported as "searched, nothing found" so the model never answers a
legal question from memory just because retrieval broke.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Citation:
    id: str
    title: str
    url: str | None = None
    excerpt: str | None = None
    doc_number: str | None = None
    locator: str | None = None  # e.g. "Điều 5 khoản 2"
    issued_on: str | None = None


@dataclass(frozen=True, slots=True)
class RetrievedContext:
    # `citation_id` must match the `id` of a Citation in the same RetrievalResult,
    # so every passage given to the model can be traced to a real source.
    content: str
    citation_id: str


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    contexts: Sequence[RetrievedContext] = ()
    citations: Sequence[Citation] = ()
    # True when RAG is on (it searched, or failed to): empty then means "say there are no
    # sources". False only when RAG is off.
    searched: bool = False


class Retriever(Protocol):
    async def retrieve(self, query: str) -> RetrievalResult:
        """Return passages and citations relevant to `query`.

        Return an empty result when nothing relevant is found; never fabricate
        sources. Citations must come from real documents.
        """
        ...


class NullRetriever:
    """No sources: RAG is off, or it failed to start (`searched=True`)."""

    def __init__(self, searched: bool = False) -> None:
        self._searched = searched

    async def retrieve(self, query: str) -> RetrievalResult:
        del query  # Unused; required by the Retriever protocol.
        return RetrievalResult(searched=self._searched)


def get_retriever() -> Retriever:
    # The single seam for plugging in RAG; the stream code should not change.
    if not get_settings().rag_enabled:
        return NullRetriever()
    from app.services.rag.retrieve.qdrant_retriever import get_qdrant_retriever
    from app.services.rag.retrieve.query_planner import build_pipeline

    try:
        return build_pipeline(get_qdrant_retriever(), get_settings())
    except Exception as error:  # e.g. missing OPENAI_API_KEY: chat must still work, without sources
        logger.warning("RAG disabled for this request: %s", type(error).__name__)
        return NullRetriever(searched=True)
