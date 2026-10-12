"""Regressions for failure modes found on the real corpus (footnotes, wrapped titles, trailers)."""

from app.services.rag.legal_parser import parse


def test_footnote_marker_glued_to_clause_number_keeps_the_clause_sequence():
    text = "Điều 1. Đối tượng\n1.2 Sản phẩm trồng trọt\n2. Khoản hai\n3. Khoản ba\n"

    article = parse(text).articles[0]

    assert [c.no for c in article.clauses] == [1, 2, 3]
    assert article.intro == ""


def test_out_of_sequence_clause_line_is_reported_not_silently_lost():
    parsed = parse("Điều 1. A\n1. Một\n5. Không đúng thứ tự\n2. Hai\n")

    assert [c.no for c in parsed.articles[0].clauses] == [1, 2]
    assert parsed.diagnostics.rejected_clauses == ["1: 5. Không đúng thứ tự"]
    assert "5. Không đúng thứ tự" in parsed.articles[0].clauses[0].text


def test_multi_line_chapter_title_does_not_leak_into_previous_article():
    text = (
        "Điều 1. A\nNội dung một\n"
        "Chương II\nQUY ĐỊNH VỀ TIỀN LƯƠNG VÀ\nCÁC KHOẢN THU NHẬP\n"
        "Điều 2. B\nNội dung hai\n"
    )

    parsed = parse(text)

    assert text[parsed.articles[0].start : parsed.articles[0].end] == "Điều 1. A\nNội dung một"
    assert parsed.articles[1].chapter == "Chương II - QUY ĐỊNH VỀ TIỀN LƯƠNG VÀ CÁC KHOẢN THU NHẬP"


def test_point_as_first_body_line_is_not_glued_onto_the_title():
    article = parse("Điều 1. Giải thích\na) Một\nb) Hai\n").articles[0]

    assert article.title == "Giải thích"
    assert article.intro.startswith("a) Một")


def test_wrapped_cross_reference_starting_with_muc_is_not_a_section_heading():
    text = (
        "Chương III\nTỔ CHỨC\nMục 1\nCHUNG\nĐiều 1. A\nNội dung\n"
        "Mục 2 Chương III Nghị định này và các hóa đơn\nĐiều 2. B\nNội dung\n"
    )

    parsed = parse(text)

    assert parsed.articles[1].section == "Mục 1 - CHUNG"
    assert (
        "Mục 2 Chương III Nghị định này" in text[parsed.articles[0].start : parsed.articles[0].end]
    )


def test_chapter_number_out_of_sequence_is_skipped_and_reported():
    text = "Chương I\nMỘT\nĐiều 1. A\nNội dung\nChương 25\nXYZ\nĐiều 2. B\nNội dung\n"

    parsed = parse(text)

    assert parsed.articles[1].chapter == "Chương I - MỘT"
    assert parsed.diagnostics.skipped_headings == ["Chương 25"]


def test_xem_tiep_footer_ends_the_text_and_marks_it_partial():
    text = "Điều 1. A\nNội dung\n(Xem tiếp Công báo số 875)\nVĂN PHÒNG CHÍNH PHỦ XUẤT BẢN\n"

    parsed = parse(text)

    assert text[parsed.articles[0].start : parsed.articles[0].end] == "Điều 1. A\nNội dung"
    assert parsed.diagnostics.continuation_marker is True


def test_normal_trailer_is_not_a_continuation_marker():
    parsed = parse("Điều 1. A\nNội dung\nNơi nhận:\n- Lưu: VT\n")

    assert parsed.diagnostics.trailer_start is not None
    assert parsed.diagnostics.continuation_marker is False


def test_stale_known_gaps_are_detected():
    diagnostics = parse("Điều 1. A\nNội dung\nĐiều 3. C\nNội dung\n").diagnostics

    assert diagnostics.missing_numbers == [2]
    assert diagnostics.stale_known_gaps((2, 7)) == [7]
    assert diagnostics.unexplained_gaps((2,)) == []
