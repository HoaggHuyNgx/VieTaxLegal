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
    content: str
    citation_id: str


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    contexts: Sequence[RetrievedContext] = ()
    citations: Sequence[Citation] = ()


class Retriever(Protocol):
    async def retrieve(self, query: str) -> RetrievalResult: ...


class NullRetriever:
    async def retrieve(self, query: str) -> RetrievalResult:
        del query
        return RetrievalResult()


def get_retriever() -> Retriever:
    return NullRetriever()
