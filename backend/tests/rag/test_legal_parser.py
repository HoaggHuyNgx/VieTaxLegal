from pathlib import Path

from app.services.rag.legal_parser import parse

FIXTURE = Path(__file__).parent / "fixtures" / "luat-quan-ly-thue-excerpt.txt"


def _real() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_real_excerpt_articles_chapters_and_sections():
    parsed = parse(_real())

    assert [a.no for a in parsed.articles] == [1, 2, 3, 10]
    assert parsed.articles[0].chapter == "Chương I - QUY ĐỊNH CHUNG"
    assert parsed.articles[3].chapter == "Chương II - CÁC CHỨC NĂNG QUẢN LÝ THUẾ"
    assert parsed.articles[3].section == "Mục 1 - ĐĂNG KÝ THUẾ"
    assert parsed.articles[3].title == "Đăng ký thuế"


def test_real_excerpt_clauses_and_points_in_sequence():
    article3 = parse(_real()).articles[2]

    assert [c.no for c in article3.clauses] == [1, 2, 3]
    assert [p.label for p in article3.clauses[1].points] == ["a", "b", "c", "d", "đ"]
    assert article3.clauses[1].points[4].text.startswith("đ) Các tiêu chí khác")


def test_real_excerpt_gap_between_articles_is_reported_not_hidden():
    diagnostics = parse(_real()).diagnostics

    assert diagnostics.missing_numbers == [4, 5, 6, 7, 8, 9]
    assert diagnostics.unexplained_gaps(known_gaps=(4, 5, 6, 7, 8, 9)) == []
    assert diagnostics.unexplained_gaps() == [4, 5, 6, 7, 8, 9]


def test_article_offsets_slice_the_original_text():
    text = _real()
    for article in parse(text).articles:
        assert text[article.start : article.end].startswith(f"Điều {article.label}.")


def test_cross_reference_at_line_start_is_body_text_not_a_heading():
    text = "Điều 1. Phạm vi\n1. Áp dụng theo\nĐiều 35 của Luật này.\nĐiều 2. Đối tượng\nNội dung\n"

    parsed = parse(text)

    assert [a.no for a in parsed.articles] == [1, 2]
    assert "Điều 35 của Luật này." in text[parsed.articles[0].start : parsed.articles[0].end]


def test_out_of_order_heading_is_skipped_and_recorded():
    text = "Điều 1. A\nnội dung\nĐiều 2. B\nnội dung\nĐiều 1. Quoted again\nnội dung\n"

    parsed = parse(text)

    assert [a.no for a in parsed.articles] == [1, 2]
    assert parsed.diagnostics.skipped_headings == ["Điều 1. Quoted again"]


def test_lettered_article_follows_its_number():
    parsed = parse("Điều 1. A\nx\nĐiều 1a. B\ny\nĐiều 2. C\nz\n")

    assert [a.label for a in parsed.articles] == ["1", "1a", "2"]
    assert parsed.diagnostics.missing_numbers == []


def test_pdf_style_space_before_period_is_accepted():
    parsed = parse("Điều 1 . Phạm vi\nx\nĐiều 2 . Đối tượng\ny\n")

    assert [a.no for a in parsed.articles] == [1, 2]


def test_wrapped_number_and_wrong_point_letter_stay_body_text():
    text = "Điều 1. A\n1. Khoản một\n3. không phải khoản\nb) không phải điểm\n"

    article = parse(text).articles[0]

    assert [c.no for c in article.clauses] == [1]
    assert article.clauses[0].points == []
    assert "3. không phải khoản" in article.clauses[0].text


def test_trailer_ends_the_last_article_and_is_not_indexed():
    text = "Điều 1. A\nnội dung\nNơi nhận:\n- Lưu: VT\nPHỤ LỤC I\nbảng\n"

    parsed = parse(text)

    assert parsed.diagnostics.trailer_start == text.index("Nơi nhận")
    assert text[parsed.articles[0].start : parsed.articles[0].end] == "Điều 1. A\nnội dung"


def test_empty_article_is_reported():
    parsed = parse("Điều 1. A\nĐiều 2. B\nNội dung\n")

    assert parsed.diagnostics.empty_articles == ["1"]


def test_heading_wrapped_onto_next_line_joins_the_title_not_the_body():
    text = "Điều 1. Cơ cấu tổ chức của công ty\nthành viên do tổ chức làm chủ\n1. Khoản một\n"

    article = parse(text).articles[0]

    assert article.title == "Cơ cấu tổ chức của công ty thành viên do tổ chức làm chủ"
    assert article.intro == ""
    assert [c.no for c in article.clauses] == [1]


def test_chapter_cross_reference_is_not_a_chapter_heading():
    text = "Chương I\nQUY ĐỊNH CHUNG\nĐiều 1. A\nChương II của Luật này quy định\nnội dung\n"

    parsed = parse(text)

    assert parsed.articles[0].chapter == "Chương I - QUY ĐỊNH CHUNG"
    assert "Chương II của Luật này" in text[parsed.articles[0].start : parsed.articles[0].end]
