from pathlib import Path

import pytest

from app.services.rag.chunking import article_chunks, estimate_tokens, fixed_chunks
from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.legal_parser import parse

FIXTURE = Path(__file__).parent / "fixtures" / "luat-quan-ly-thue-excerpt.txt"


def _doc(**overrides) -> CorpusDoc:
    values = {
        "slug": "luat-qlt-excerpt",
        "number": "108/2025/QH15",
        "title": "Luật Quản lý thuế",
        "doc_type": "luat",
        "field": "tax",
        "file": "raw/x.docx",
        "sha256": "0" * 64,
        "source_url": "https://example.test/doc",
        "status": "in_force",
    }
    return CorpusDoc(**{**values, **overrides})


@pytest.fixture
def parsed():
    return parse(FIXTURE.read_text(encoding="utf-8"))


def test_article_chunks_are_exact_slices_with_locator_and_heading_path(parsed):
    chunks = article_chunks(_doc(), parsed)

    assert [c.locator for c in chunks] == ["Điều 1", "Điều 2", "Điều 3", "Điều 10"]
    for chunk, article in zip(chunks, parsed.articles):
        assert chunk.content == parsed.text[article.start : article.end]
        assert (chunk.char_start, chunk.char_end) == (article.start, article.end)
    assert chunks[3].heading_path == (
        "Luật Quản lý thuế 108/2025/QH15 > Chương II - CÁC CHỨC NĂNG QUẢN LÝ THUẾ"
        " > Mục 1 - ĐĂNG KÝ THUẾ > Điều 10. Đăng ký thuế"
    )


def test_chunk_ids_are_deterministic_and_payload_matches_schema(parsed):
    first = article_chunks(_doc(), parsed)
    second = article_chunks(_doc(), parse(parsed.text))

    assert [c.id for c in first] == [c.id for c in second]
    assert len({c.id for c in first}) == len(first)
    payload = first[0].to_payload()
    assert payload["doc_slug"] == "luat-qlt-excerpt"
    assert payload["status"] == "in_force"
    assert payload["article_nos"] == [1]
    assert {"locator", "heading_path", "content", "content_sha256", "char_start"} <= set(payload)


def test_long_article_splits_into_one_chunk_per_clause(parsed):
    chunks = article_chunks(_doc(), parsed, max_tokens=20)

    article10 = [c for c in chunks if c.article_no == 10]
    clause_nos = [c.no for c in parsed.articles[3].clauses]
    assert len(clause_nos) >= 4
    assert [c.locator for c in article10] == [f"Điều 10 khoản {n}" for n in clause_nos]
    assert article10[0].content.startswith("1. ")
    assert [c.clause_no for c in article10] == clause_nos


def test_split_chunks_lose_no_text(parsed):
    chunks = article_chunks(_doc(), parsed, max_tokens=20)

    for article in parsed.articles:
        original = parsed.text[article.start : article.end]
        rebuilt = "\n".join(c.content for c in chunks if c.article_no == article.no)
        if not rebuilt.startswith("Điều"):  # split by Khoan: the heading lives in heading_path
            original = original.split("\n", 1)[1]
        assert rebuilt.split() == original.split()


def test_excluded_articles_are_dropped_from_both_chunkers(parsed):
    doc = _doc(excluded_articles=("2",))

    assert [c.article_no for c in article_chunks(doc, parsed)] == [1, 3, 10]
    assert all(2 not in c.article_nos for c in fixed_chunks(doc, parsed, size_tokens=30))


def test_fixed_chunks_overlap_cover_all_words_and_map_to_articles(parsed):
    chunks = fixed_chunks(_doc(), parsed, size_tokens=70, overlap_tokens=14)

    assert len(chunks) > len(parsed.articles)
    covered: set[int] = set()
    for chunk in chunks:
        assert chunk.content == parsed.text[chunk.char_start : chunk.char_end]
        assert estimate_tokens(chunk.content) <= 72
        covered.update(range(chunk.char_start, chunk.char_end))
    first_start, last_end = parsed.articles[0].start, parsed.articles[-1].end
    for position in range(first_start, last_end):
        if not parsed.text[position].isspace():
            assert position in covered
    assert any(b.char_start < a.char_end for a, b in zip(chunks, chunks[1:]))


def test_fixed_chunk_lists_every_article_it_touches(parsed):
    chunks = fixed_chunks(_doc(), parsed, size_tokens=2000, overlap_tokens=0)

    assert len(chunks) == 1
    assert chunks[0].article_nos == (1, 2, 3, 10)
    assert chunks[0].locator == "Điều 1–10"
    assert chunks[0].chunk_set == "fixed"


def test_split_article_keeps_a_chunk_for_intro_text_before_the_first_clause():
    parsed = parse("Điều 1. Tiêu đề\nLời dẫn của điều luật này như sau:\n1. Một\n2. Hai\n")

    chunks = article_chunks(_doc(), parsed, max_tokens=3)

    assert [c.locator for c in chunks] == ["Điều 1", "Điều 1 khoản 1", "Điều 1 khoản 2"]
    assert chunks[0].content == "Điều 1. Tiêu đề\nLời dẫn của điều luật này như sau:"
