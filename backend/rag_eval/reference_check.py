"""Mechanical hallucination check: legal references in an answer that no source supports.

No LLM judge: a document number or `Dieu N` the answer states must appear in the retrieved
sources (or, for document numbers, at least exist in the corpus). Anything else is flagged.
"""

import re
import unicodedata
from dataclasses import dataclass, field

_DOC_NUMBER_RE = re.compile(r"\b\d{1,4}/(?:\d{4}/)?[A-ZĐ][A-ZĐ0-9\-]*(?:/[A-ZĐ0-9\-]+)?")
_ARTICLE_RE = re.compile(r"\bĐiều\s+(\d+)([a-zđ]?)\b", re.IGNORECASE)


def normalize_doc_number(number: str) -> str:
    text = unicodedata.normalize("NFC", number).upper().replace("Đ", "D")
    return re.sub(r"\s+", "", text)


@dataclass
class ReferenceReport:
    doc_numbers: list[str] = field(default_factory=list)
    articles: list[int] = field(default_factory=list)
    unsupported_doc_numbers: list[str] = field(default_factory=list)
    unsupported_articles: list[int] = field(default_factory=list)

    @property
    def hallucinated(self) -> bool:
        return bool(self.unsupported_doc_numbers or self.unsupported_articles)


def check_references(
    answer: str, retrieved_doc_numbers: set[str], retrieved_articles: set[int]
) -> ReferenceReport:
    """Flag doc numbers not among the retrieved sources and article numbers no source covers."""
    allowed_docs = {normalize_doc_number(n) for n in retrieved_doc_numbers}
    answer = unicodedata.normalize("NFC", answer)
    doc_numbers = list(dict.fromkeys(m.group(0) for m in _DOC_NUMBER_RE.finditer(answer)))
    articles = list(dict.fromkeys(int(m.group(1)) for m in _ARTICLE_RE.finditer(answer)))
    return ReferenceReport(
        doc_numbers=doc_numbers,
        articles=articles,
        unsupported_doc_numbers=[
            n for n in doc_numbers if normalize_doc_number(n) not in allowed_docs
        ],
        unsupported_articles=[a for a in articles if a not in retrieved_articles],
    )
