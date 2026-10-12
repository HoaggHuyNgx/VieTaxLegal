from app.services.rag.chunking import estimate_tokens
from app.services.rag.chunking_small import CHUNK_SET, small_article_chunks, split_span
from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.legal_parser import parse


def _doc() -> CorpusDoc:
    return CorpusDoc(
        slug="doc",
        number="1/2026",
        title="Luật thử",
        doc_type="luat",
        field="tax",
        file="raw/x.docx",
        sha256="0" * 64,
        source_url="https://example.test",
    )


def _words(n: int) -> str:
    return " ".join(f"từ{i}" for i in range(n))


def test_short_article_stays_one_chunk_even_with_clauses():
    parsed = parse("Điều 1. A\n1. Một\n2. Hai\n")

    chunks = small_article_chunks(_doc(), parsed)

    assert [c.locator for c in chunks] == ["Điều 1"]
    assert chunks[0].chunk_set == CHUNK_SET


def test_long_article_splits_by_clause_then_lines_within_max_tokens():
    lines = "\n".join(f"{chr(97 + i)}) {_words(40)};" for i in range(4))
    text = f"Điều 1. A\n1. Mở đầu:\n{lines}\n2. Khoản hai\n"
    parsed = parse(text)

    chunks = small_article_chunks(_doc(), parsed, max_tokens=80)

    assert all(estimate_tokens(c.content) <= 80 for c in chunks)
    assert {c.locator for c in chunks} == {"Điều 1 khoản 1", "Điều 1 khoản 2"}
    assert len([c for c in chunks if c.clause_no == 1]) > 1
    for chunk in chunks:
        assert chunk.content == text[chunk.char_start : chunk.char_end]


def test_overlong_single_line_is_cut_at_sentences_then_words():
    sentence_line = " ".join(f"{_words(30)}." for _ in range(3))
    word_line = _words(200)
    text = f"{sentence_line}\n{word_line}"

    spans = split_span(text, 0, len(text), max_tokens=60)

    assert all(estimate_tokens(text[s:e]) <= 60 for s, e in spans)
    covered = " ".join(text[s:e] for s, e in spans).split()
    assert covered == text.split()


def test_split_loses_no_words_of_the_clause_body():
    body = "\n".join(f"{_words(25)}." for _ in range(10))
    text = f"Điều 1. A\n1. Khoản\n{body}\n2. Hai\n"
    parsed = parse(text)

    chunks = [c for c in small_article_chunks(_doc(), parsed, max_tokens=60) if c.clause_no == 1]

    assert " ".join(c.content for c in chunks).split() == ("1. Khoản\n" + body).split()
