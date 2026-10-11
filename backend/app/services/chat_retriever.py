from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Citation:
    id: str
    title: str
    url: str | None = None
    excerpt: str | None = None


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
    return NullRetriever()
