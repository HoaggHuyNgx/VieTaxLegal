import unicodedata

import pytest

from app.services.rag.ingest.corpus_manifest import load_manifest
from rag_eval.reference_check import Source, check_references, normalize_doc_number

LABOUR = "45/2019/QH14"
DECREE = "181/2025/NĐ-CP"


def _source(number: str = LABOUR, articles: tuple[int, ...] = (25,), content: str = "") -> Source:
    return Source(number, articles, content)


def test_supported_references_are_not_flagged():
    answer = "Theo Điều 25 Bộ luật Lao động 45/2019/QH14, thời gian thử việc tối đa là 180 ngày."

    report = check_references(answer, [_source()])

    assert report.doc_numbers == [LABOUR]
    assert report.articles == [25]
    assert not report.unsupported


def test_invented_document_number_and_article_are_flagged():
    answer = "Nghị định 99/2030/NĐ-CP tại Điều 77 quy định khác; xem thêm Điều 25."

    report = check_references(answer, [_source()])

    assert report.unsupported_doc_numbers == ["99/2030/NĐ-CP"]
    assert report.unsupported_articles == [77]
    assert report.unsupported


def test_references_written_in_a_source_or_in_the_question_are_supported():
    source = _source(content="Thực hiện theo Điều 90 và Nghị định 7/2021/NĐ-CP.")
    answer = "Theo Điều 90, Nghị định 7/2021/NĐ-CP; còn Điều 12 của 8/2022/TT-BTC bạn hỏi."

    report = check_references(answer, [source], question="Điều 12 của 8/2022/TT-BTC là gì?")

    assert not report.unsupported


@pytest.mark.parametrize("form", ["01/GTGT", "05/KK-TNCN", "ngày 01/07/2025"])
def test_form_numbers_and_dates_are_not_document_numbers(form):
    assert check_references(f"Nộp tờ khai {form}.", []).doc_numbers == []


def test_consolidated_document_numbers_are_read():
    report = check_references("Theo 12/VBHN-VPQH.", [_source("12/VBHN-VPQH", ())])

    assert report.doc_numbers == ["12/VBHN-VPQH"] and not report.unsupported


def test_every_corpus_document_number_is_recognised():
    for doc in load_manifest():
        assert check_references(f"Văn bản {doc.number}.", []).doc_numbers == [doc.number]


def test_every_article_of_a_list_is_checked():
    report = check_references("Theo Điều 3, 99 và 100.", [_source(articles=(3,))])

    assert report.articles == [3, 99, 100]
    assert report.unsupported_articles == [99, 100]


@pytest.mark.parametrize(
    "tail", ["10 ngày", "20%", "5 triệu đồng", "3 khoản", "1.000.000 đồng", "01/07/2025"]
)
def test_quantities_after_an_article_are_not_more_articles(tail):
    report = check_references(f"Theo Điều 3, {tail} được tính.", [_source(articles=(3,))])

    assert report.articles == [3]


def test_an_article_tied_to_a_document_number_is_checked_against_that_document():
    sources = [_source(LABOUR, (25,)), _source(DECREE, (5,))]

    wrong = check_references(f"Theo Điều 5 Bộ luật Lao động số {LABOUR}.", sources)
    right = check_references(f"Theo Điều 5 Nghị định {DECREE}.", sources)
    lower = check_references(f"theo Điều 5 bộ luật lao động số {LABOUR}.", sources)

    assert wrong.unsupported_articles == [5]
    assert lower.unsupported_articles == [5]
    assert not right.unsupported


def test_an_article_tied_only_to_a_law_name_is_left_for_a_person():
    """Article 5 is in a source, but not necessarily in the law the answer names."""
    report = check_references("Theo Điều 5 Bộ luật Hình sự.", [_source(articles=(5,))])

    assert not report.unsupported
    assert report.needs_review == ["Điều 5 Bộ luật Hình sự"]
    assert not check_references("Theo Điều 5 Luật này.", [_source(articles=(5,))]).needs_review


def test_document_number_matching_ignores_case_spacing_and_d_variants():
    assert normalize_doc_number("181/2025/nđ-cp") == normalize_doc_number("181/2025/ND-CP")
    report = check_references(f"Nghị định {DECREE}", [_source("181/2025/ND-CP", ())])
    assert not report.unsupported


def test_answer_without_references_is_clean():
    assert not check_references("Tôi chưa thể xác minh.", []).unsupported


def test_lettered_article_is_read_as_its_number():
    report = check_references("theo Điều 7a của Luật", [_source(articles=(7,))])

    assert report.articles == [7]
    assert not report.unsupported


def test_reference_check_is_case_insensitive_and_unicode_form_independent():
    answer = unicodedata.normalize("NFD", "theo điều 77 của luật")

    assert check_references(answer, [_source(articles=(5,))]).unsupported_articles == [77]
