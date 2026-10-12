"""Chunkers over a ParsedDocument: ``article`` (Dieu, split by Khoan when long) and ``fixed``.

Pure functions, no I/O. Both chunkers keep exact offsets into the parsed text, so every chunk can
be traced to its source and fixed chunks can be scored at article level (experiment 1).
"""

import hashlib
import math
import re
from dataclasses import asdict, dataclass

from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.legal_parser import Article, ParsedDocument
from app.services.rag.qdrant_store import point_id

# Vietnamese syllables are whitespace-separated words, ~1.4 BPE tokens each (estimate, not exact).
TOKENS_PER_WORD = 1.4
ARTICLE_MAX_TOKENS = 800
FIXED_TOKENS = 512
FIXED_OVERLAP_TOKENS = 64


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text.split()) * TOKENS_PER_WORD)


@dataclass(frozen=True)
class ChunkDraft:
    """One future Qdrant point; field names match the payload schema from Phase 2."""

    doc_slug: str
    doc_number: str
    doc_title: str
    doc_type: str
    field: str
    status: str | None
    issued_on: str | None
    effective_from: str | None
    effective_to: str | None
    source_url: str
    chunk_set: str
    ordinal: int
    article_no: int | None
    article_nos: tuple[int, ...]
    clause_no: int | None
    point: str | None
    locator: str
    heading_path: str
    content: str
    content_sha256: str
    char_start: int
    char_end: int

    @property
    def id(self) -> str:
        return point_id(self.doc_slug, self.chunk_set, self.ordinal, self.content)

    def to_payload(self) -> dict:
        payload = asdict(self)
        payload["article_nos"] = list(self.article_nos)
        return payload


def _heading_path(doc: CorpusDoc, article: Article) -> str:
    parts = [f"{doc.title} {doc.number}", article.chapter, article.section]
    parts.append(f"Điều {article.label}. {article.title}")
    return " > ".join(part for part in parts if part)


def _draft(doc: CorpusDoc, chunk_set: str, ordinal: int, text: str, start: int, end: int, **kw):
    end = start + len(text[start:end].rstrip())  # slices may end on the newline before a Khoan
    content = text[start:end]
    return ChunkDraft(
        doc_slug=doc.slug, doc_number=doc.number, doc_title=doc.title, doc_type=doc.doc_type,
        field=doc.field, status=doc.status, issued_on=doc.issued_on,
        effective_from=doc.effective_from, effective_to=doc.effective_to,
        source_url=doc.source_url, chunk_set=chunk_set, ordinal=ordinal, point=None,
        content=content, content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        char_start=start, char_end=end, **kw,
    )  # fmt: skip


def _kept_articles(doc: CorpusDoc, parsed: ParsedDocument) -> list[Article]:
    return [a for a in parsed.articles if a.label not in doc.excluded_articles]


def article_chunks(
    doc: CorpusDoc, parsed: ParsedDocument, max_tokens: int = ARTICLE_MAX_TOKENS
) -> list[ChunkDraft]:
    """One chunk per Dieu; a Dieu over ``max_tokens`` becomes an intro chunk + one per Khoan."""
    text, chunks = parsed.text, []

    def add(article: Article, start: int, end: int, locator: str, clause_no: int | None):
        chunks.append(
            _draft(doc, "article", len(chunks), text, start, end,
                   article_no=article.no, article_nos=(article.no,), clause_no=clause_no,
                   locator=locator, heading_path=_heading_path(doc, article))
        )  # fmt: skip

    for article in _kept_articles(doc, parsed):
        label = f"Điều {article.label}"
        if estimate_tokens(text[article.start : article.end]) <= max_tokens or not article.clauses:
            add(article, article.start, article.end, label, None)
            continue
        if article.intro:  # a heading-only chunk is noise; the title lives in heading_path
            add(article, article.start, article.clauses[0].start, label, None)
        for clause in article.clauses:
            add(article, clause.start, clause.end, f"{label} khoản {clause.no}", clause.no)
    return [c for c in chunks if c.content.strip()]


def _segments(doc: CorpusDoc, parsed: ParsedDocument) -> list[tuple[int, int]]:
    """Text spans to window: first to last article, minus excluded (repealed) articles."""
    if not parsed.articles:
        return []
    spans, cursor = [], parsed.articles[0].start
    for article in parsed.articles:
        if article.label in doc.excluded_articles:
            if article.start > cursor:
                spans.append((cursor, article.start))
            cursor = article.end
    last_end = parsed.articles[-1].end
    if last_end > cursor:
        spans.append((cursor, last_end))
    return spans


def fixed_chunks(
    doc: CorpusDoc,
    parsed: ParsedDocument,
    size_tokens: int = FIXED_TOKENS,
    overlap_tokens: int = FIXED_OVERLAP_TOKENS,
) -> list[ChunkDraft]:
    """Sliding word windows over the same text; ``article_nos`` lists each Dieu a window touches."""
    window = max(1, int(size_tokens / TOKENS_PER_WORD))
    step = max(1, window - int(overlap_tokens / TOKENS_PER_WORD))
    kept, chunks = _kept_articles(doc, parsed), []
    for seg_start, seg_end in _segments(doc, parsed):
        words = [m.span() for m in re.finditer(r"\S+", parsed.text[seg_start:seg_end])]
        for first in range(0, len(words), step):
            last = min(first + window, len(words)) - 1
            start, end = seg_start + words[first][0], seg_start + words[last][1]
            touched = [a for a in kept if a.start < end and a.end > start]
            if not touched:
                continue
            numbers = tuple(dict.fromkeys(a.no for a in touched))
            locator = f"Điều {touched[0].label}" + (
                f"–{touched[-1].label}" if len(touched) > 1 else ""
            )
            chunks.append(
                _draft(doc, "fixed", len(chunks), parsed.text, start, end,
                       article_no=numbers[0], article_nos=numbers, clause_no=None,
                       locator=locator, heading_path=_heading_path(doc, touched[0]))
            )  # fmt: skip
            if last == len(words) - 1:
                break
    return chunks
