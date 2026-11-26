"""Mechanical check: legal references in an answer that the retrieved sources do not support.

No LLM judge. A document number or `Điều N` the answer states must appear in a source (its
metadata or its text) or in the user's own question. This measures "not supported by what was
retrieved", NOT fabrication: a real law outside the retrieved passages is flagged too.

Known limits: only numbers with a year (`NN/YYYY/XXX`) or `NN/VBHN-...` count, so that form
numbers such as `01/GTGT` do not; official letters without a year are therefore missed. An
article tied to a law by name only ("Điều 5 Bộ luật Hình sự") cannot be matched reliably and is
listed in `needs_review` for a person.
"""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field

_DOC = r"\d{1,4}/(?:\d{4}/[A-ZĐ][A-ZĐ0-9\-]*(?:/[A-ZĐ0-9\-]+)?|VBHN-[A-ZĐ][A-ZĐ0-9\-]*)"
_DOC_NUMBER_RE = re.compile(rf"\b{_DOC}")
_KIND = r"(?:Bộ luật|Luật|Nghị định|Thông tư|Nghị quyết|Văn bản hợp nhất)"
# A number followed by one of these is a quantity, a date or an amount, not another article.
_NOT_ARTICLE = r"(?!\s*(?:%|/|ngày|tháng|năm|triệu|tỷ|đồng|khoản|giờ|lần|người|tuổi)|[.,]\d)"
_ARTICLES_RE = re.compile(
    r"\b(?i:Điều)\s+\d+[a-zđ]?\b"
    r"(?:\s*(?:,|;|và|hoặc|đến|-|–)\s*(?:(?i:Điều)\s+)?\d+[a-zđ]?\b" + _NOT_ARTICLE + r")*"
)
# What may directly follow an article list to say which document it belongs to.
_TIED_NUMBER_RE = re.compile(
    rf"\s*(?:(?:của\s+)?(?i:{_KIND})[^.;:\n\[\]()0-9]{{0,80}}?)?\s*(?:\(\s*)?(?:số\s+)?(?P<doc>{_DOC})"
)
_TIED_NAME_RE = re.compile(rf"\s*(?:của\s+)?{_KIND}\s+(?!này\b)[^.,;:\n\[\]()]{{1,60}}")


def normalize_doc_number(number: str) -> str:
    text = unicodedata.normalize("NFC", number).upper().replace("Đ", "D")
    return re.sub(r"\s+", "", text)


@dataclass(frozen=True)
class Source:
    """One retrieved passage, as the check needs it."""

    doc_number: str
    articles: tuple[int, ...]
    content: str = ""


@dataclass
class ReferenceReport:
    doc_numbers: list[str] = field(default_factory=list)
    articles: list[int] = field(default_factory=list)
    unsupported_doc_numbers: list[str] = field(default_factory=list)
    unsupported_articles: list[int] = field(default_factory=list)
    needs_review: list[str] = field(default_factory=list)

    @property
    def unsupported(self) -> bool:
        return bool(self.unsupported_doc_numbers or self.unsupported_articles)


def find_doc_numbers(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text)
    return list(dict.fromkeys(m.group(0) for m in _DOC_NUMBER_RE.finditer(text)))


def _article_lists(text: str):
    """(match, article numbers) for every `Điều ...` mention, lists included."""
    for match in _ARTICLES_RE.finditer(text):
        yield match, [int(n) for n in re.findall(r"\d+", match.group(0))]


def _articles_in(text: str) -> set[int]:
    text = unicodedata.normalize("NFC", text)
    return {n for _, numbers in _article_lists(text) for n in numbers}


def check_references(answer: str, sources: Sequence[Source], question: str = "") -> ReferenceReport:
    """Flag the document numbers and articles of `answer` that neither source nor question has."""
    answer = unicodedata.normalize("NFC", answer)
    texts = [question, *(source.content for source in sources)]
    allowed_docs = {normalize_doc_number(s.doc_number) for s in sources}
    allowed_docs |= {normalize_doc_number(n) for text in texts for n in find_doc_numbers(text)}
    allowed_articles = {n for s in sources for n in s.articles}
    allowed_articles |= {n for text in texts for n in _articles_in(text)}
    by_doc: dict[str, set[int]] = {}
    for source in sources:
        known = by_doc.setdefault(normalize_doc_number(source.doc_number), set())
        known |= {*source.articles, *_articles_in(source.content)}
    asked = _articles_in(question)

    articles, unsupported, needs_review = [], [], []
    for match, numbers in _article_lists(answer):
        allowed = allowed_articles
        if tied := _TIED_NUMBER_RE.match(answer, match.end()):
            doc = normalize_doc_number(tied.group("doc"))
            if doc in by_doc:  # the answer says which document: only its articles count
                allowed = by_doc[doc] | asked
        elif named := _TIED_NAME_RE.match(answer, match.end()):
            needs_review.append(" ".join((match.group(0) + named.group(0)).split()))
        articles += numbers
        unsupported += [n for n in numbers if n not in allowed]

    doc_numbers = find_doc_numbers(answer)
    return ReferenceReport(
        doc_numbers=doc_numbers,
        articles=list(dict.fromkeys(articles)),
        unsupported_doc_numbers=[
            n for n in doc_numbers if normalize_doc_number(n) not in allowed_docs
        ],
        unsupported_articles=list(dict.fromkeys(unsupported)),
        needs_review=list(dict.fromkeys(needs_review)),
    )
