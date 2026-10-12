"""``article_s256`` chunk set: article chunks that fit a 256-token embedding model (BKAI).

Same units as ``article_chunks`` (Dieu, or Khoan for long Dieu) but any unit over ``max_tokens`` is
cut again at line (usually Diem) boundaries, then sentence boundaries, then word windows. The
default leaves room for the ``heading_path`` prefix that is embedded together with the content.
Every piece keeps exact offsets into the parsed text.
"""

import re

from app.services.rag.chunking import (
    ChunkDraft,
    _draft,
    _heading_path,
    _kept_articles,
    estimate_tokens,
)
from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.legal_parser import ParsedDocument

SMALL_MAX_TOKENS = 200
CHUNK_SET = "article_s256"
_SENTENCE_RE = re.compile(r"\S.*?(?:[.;:](?=\s)|$)")


def _split_long(text: str, start: int, end: int, max_tokens: int) -> list[tuple[int, int]]:
    """Cut one over-long line into sentence pieces, then word windows."""
    pieces = []
    for sentence in _SENTENCE_RE.finditer(text[start:end]):
        s, e = start + sentence.start(), start + sentence.end()
        if estimate_tokens(text[s:e]) <= max_tokens:
            pieces.append((s, e))
            continue
        words = [(s + w.start(), s + w.end()) for w in re.finditer(r"\S+", text[s:e])]
        step = max(1, int(max_tokens / 1.4))
        pieces += [
            (words[i][0], words[min(i + step, len(words)) - 1][1])
            for i in range(0, len(words), step)
        ]
    return pieces


def split_span(text: str, start: int, end: int, max_tokens: int) -> list[tuple[int, int]]:
    """Greedy-pack the lines of text[start:end] into spans of at most ``max_tokens`` (estimated)."""
    atoms = []
    for line in re.finditer(r"[^\n]+", text[start:end]):
        s, e = start + line.start(), start + line.end()
        atoms += (
            [(s, e)]
            if estimate_tokens(text[s:e]) <= max_tokens
            else _split_long(text, s, e, max_tokens)
        )
    spans: list[tuple[int, int]] = []
    for s, e in atoms:
        if spans and estimate_tokens(text[spans[-1][0] : e]) <= max_tokens:
            spans[-1] = (spans[-1][0], e)
        else:
            spans.append((s, e))
    return spans


def small_article_chunks(
    doc: CorpusDoc, parsed: ParsedDocument, max_tokens: int = SMALL_MAX_TOKENS
) -> list[ChunkDraft]:
    text, chunks = parsed.text, []
    for article in _kept_articles(doc, parsed):
        label = f"Điều {article.label}"
        units = [(article.start, article.end, label, None)]
        whole_fits = estimate_tokens(text[article.start : article.end]) <= max_tokens
        if article.clauses and not whole_fits:
            units = [(clause.start, clause.end, f"{label} khoản {clause.no}", clause.no)
                     for clause in article.clauses]  # fmt: skip
            if article.intro:
                units.insert(0, (article.start, article.clauses[0].start, label, None))
        for unit_start, unit_end, locator, clause_no in units:
            for start, end in split_span(text, unit_start, unit_end, max_tokens):
                chunks.append(
                    _draft(doc, CHUNK_SET, len(chunks), text, start, end,
                           article_no=article.no, article_nos=(article.no,), clause_no=clause_no,
                           locator=locator, heading_path=_heading_path(doc, article))
                )  # fmt: skip
    return [c for c in chunks if c.content.strip()]
