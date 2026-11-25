"""Dependency-free sparse (lexical) encoder for Vietnamese legal text.

NFC -> lowercase -> accent folding -> unigrams + bigrams (Vietnamese words are mostly two
syllables, so bigrams approximate them) -> crc32 term hash as the sparse index.

Documents get BM25 term weights (saturating term frequency with length normalisation); queries are
binary. IDF is applied by the collection's sparse `modifier=idf`. Raw term frequency was tried
first and ranked purely by chunk length (sparse recall@5 under 10%), hence BM25. Hash collisions
are negligible at this vocabulary size (tens of thousands of terms in a 32-bit space).
"""

import re
import unicodedata
import zlib
from collections import Counter

from qdrant_client import models

_WORD_RE = re.compile(r"\w+")
K1 = 1.2
B = 0.75
# Typical number of terms (unigrams + bigrams) in a chunk; a constant keeps ingest incremental.
AVG_TERMS = 200.0


def fold(text: str) -> str:
    """Lowercase and strip diacritics so 'khấu trừ' and 'khau tru' match; NFC/NFD input is equal."""
    lowered = unicodedata.normalize("NFC", text).lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def terms(text: str) -> list[str]:
    words = _WORD_RE.findall(fold(text))
    return words + [f"{a} {b}" for a, b in zip(words, words[1:])]


def _hash(term: str) -> int:
    return zlib.crc32(term.encode("utf-8"))


def encode_document(text: str) -> models.SparseVector:
    all_terms = terms(text)
    counts: Counter[int] = Counter(_hash(t) for t in all_terms)
    norm = K1 * (1 - B + B * len(all_terms) / AVG_TERMS)
    indices = sorted(counts)
    return models.SparseVector(
        indices=indices,
        values=[counts[i] * (K1 + 1) / (counts[i] + norm) for i in indices],
    )


def encode_query(text: str) -> models.SparseVector:
    indices = sorted({_hash(t) for t in terms(text)})
    return models.SparseVector(indices=indices, values=[1.0] * len(indices))
