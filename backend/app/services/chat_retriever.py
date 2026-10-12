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


class Retriever(Protocol):
    async def retrieve(self, query: str) -> RetrievalResult:
        """Return passages and citations relevant to `query`.

        Return an empty result when nothing relevant is found; never fabricate
        sources. Citations must come from real documents.
        """
        ...


class NullRetriever:
    """Placeholder until RAG exists: no sources, so the model must say it cannot verify."""

    async def retrieve(self, query: str) -> RetrievalResult:
        del query  # Unused; required by the Retriever protocol.
        return RetrievalResult()


def get_retriever() -> Retriever:
    # The single seam for plugging in RAG; the stream code should not change.
    if not get_settings().rag_enabled:
        return NullRetriever()
    from app.services.rag.qdrant_retriever import get_qdrant_retriever

    try:
        return get_qdrant_retriever()
    except Exception as error:  # e.g. missing OPENAI_API_KEY: chat must still work, without sources
        logger.warning("RAG disabled for this request: %s", type(error).__name__)
        return NullRetriever()
