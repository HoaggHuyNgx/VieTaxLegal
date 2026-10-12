from rag_eval.reference_check import check_references, normalize_doc_number


def test_supported_references_are_not_flagged():
    answer = "Theo Điều 25 Bộ luật Lao động 45/2019/QH14, thời gian thử việc tối đa là 180 ngày."

    report = check_references(answer, {"45/2019/QH14"}, {25, 27})

    assert report.doc_numbers == ["45/2019/QH14"]
    assert report.articles == [25]
    assert not report.hallucinated


def test_invented_document_number_and_article_are_flagged():
    answer = "Nghị định 99/2030/NĐ-CP tại Điều 77 quy định khác; xem thêm Điều 25."

    report = check_references(answer, {"45/2019/QH14"}, {25})

    assert report.unsupported_doc_numbers == ["99/2030/NĐ-CP"]
    assert report.unsupported_articles == [77]
    assert report.hallucinated


def test_document_number_matching_ignores_case_spacing_and_d_variants():
    assert normalize_doc_number("181/2025/nđ-cp") == normalize_doc_number("181/2025/ND-CP")
    report = check_references("Nghị định 181/2025/NĐ-CP", {"181/2025/ND-CP"}, set())
    assert not report.hallucinated


def test_answer_without_references_is_clean():
    assert not check_references("Tôi chưa thể xác minh.", set(), set()).hallucinated


def test_lettered_article_is_read_as_its_number():
    report = check_references("theo Điều 7a của Luật", set(), {7})

    assert report.articles == [7]
    assert not report.hallucinated
