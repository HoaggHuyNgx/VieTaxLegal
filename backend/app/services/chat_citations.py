"""Select the sources an answer actually used (`[n]` markers) and serialise them for storage."""

import re
from dataclasses import dataclass

from app.schemas.chat import CitationResponse
from app.services.chat_retriever import Citation, RetrievalResult

_MARKER_RE = re.compile(r"\[(\d{1,3})\]")


@dataclass(frozen=True)
class CitationSelection:
    cited: list[Citation]
    unknown_markers: list[str]  # `[n]` the model wrote for a source that was never provided


def strip_markers(text: str) -> str:
    """Remove `[n]` from replayed assistant turns: each turn renumbers its sources from 1."""
    return re.sub(r"\s*\[\d{1,3}\]", "", text)


def marker_ids(answer: str) -> list[str]:
    """`[n]` ids in order of first appearance, without repeats."""
    return list(dict.fromkeys(match.group(1) for match in _MARKER_RE.finditer(answer)))


def select_cited(result: RetrievalResult, answer: str) -> CitationSelection:
    """Keep only retrieved sources the answer cites; invented ids are reported, never shown."""
    by_id = {citation.id: citation for citation in result.citations}
    ids = marker_ids(answer)
    return CitationSelection(
        cited=[by_id[i] for i in ids if i in by_id],
        unknown_markers=[i for i in ids if i not in by_id],
    )


def citation_snapshot(citations: list[Citation]) -> list[dict[str, object]]:
    """JSON stored on `messages.citations` and sent to the client (camelCase, no nulls)."""
    return [
        CitationResponse(
            id=item.id,
            title=item.title,
            url=item.url,
            excerpt=item.excerpt,
            document_number=item.doc_number,
            locator=item.locator,
            issued_on=item.issued_on,
        ).model_dump(mode="json", by_alias=True, exclude_none=True)
        for item in citations
    ]
