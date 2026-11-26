"""Select the sources an answer actually used (`[n]` markers) and serialise them for storage."""

import re
from dataclasses import dataclass

from app.schemas.chat import CitationResponse
from app.services.chat.retriever import Citation, RetrievalResult

# `[1]`, and the grouped forms models also write: `[1, 2]`, `[1; 2]`, `[1-3]`.
_MARKER_BODY = r"\[(\d{1,3}(?:\s*[,;\-–]\s*\d{1,3})*)\]"
_MARKER_RE = re.compile(_MARKER_BODY)
_STRIP_RE = re.compile(r"\s*" + _MARKER_BODY)
MAX_RANGE_SPAN = 20  # a wider "range" is not a list of sources; keep only its two ends


@dataclass(frozen=True)
class CitationSelection:
    cited: list[Citation]
    unknown_markers: list[str]  # `[n]` the model wrote for a source that was never provided


def strip_markers(text: str) -> str:
    """Remove `[n]` from replayed assistant turns: each turn renumbers its sources from 1."""
    return _STRIP_RE.sub("", text)


def _expand(group: str) -> list[str]:
    """Ids inside one marker: "1, 3-5" -> ["1", "3", "4", "5"]."""
    ids: list[str] = []
    for part in re.split(r"[,;]", group):
        ends = [int(number) for number in re.findall(r"\d+", part)]
        if len(ends) == 2 and 0 < ends[1] - ends[0] <= MAX_RANGE_SPAN:
            ends = list(range(ends[0], ends[1] + 1))
        ids += [str(number) for number in ends]
    return ids


def marker_ids(answer: str) -> list[str]:
    """`[n]` ids in order of first appearance, without repeats."""
    matches = _MARKER_RE.finditer(answer)
    return list(dict.fromkeys(i for match in matches for i in _expand(match.group(1))))


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
