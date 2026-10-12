import zipfile
from pathlib import Path

import pytest

from app.services.rag.text_extraction import UnsupportedFormatError, clean_text, extract_text

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

NUMBERING = (
    '<w:abstractNum w:abstractNumId="0">'
    '<w:lvl w:ilvl="0"><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/></w:lvl>'
    '<w:lvl w:ilvl="1"><w:numFmt w:val="lowerLetter"/><w:lvlText w:val="%2)"/></w:lvl>'
    "</w:abstractNum>"
    '<w:num w:numId="5"><w:abstractNumId w:val="0"/></w:num>'
)


def _docx(path: Path, body_xml: str, numbering_xml: str = "") -> Path:
    document = f"<w:document {W}><w:body>{body_xml}</w:body></w:document>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        if numbering_xml:
            archive.writestr(
                "word/numbering.xml", f"<w:numbering {W}>{numbering_xml}</w:numbering>"
            )
    return path


def _numbered(text: str, ilvl: int) -> str:
    return (
        f'<w:p><w:pPr><w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="5"/></w:numPr></w:pPr>'
        f"<w:r><w:t>{text}</w:t></w:r></w:p>"
    )


def test_clean_text_normalises_nfc_spaces_and_blank_lines():
    decomposed_e = "é"
    raw = decomposed_e + "\n\n\n  Điều 1.  Phạm   vi điều chỉnh  \r\n"

    assert clean_text(raw) == "é\n\nĐiều 1. Phạm vi điều chỉnh\n"


def test_clean_text_drops_page_furniture_but_keeps_real_numbers():
    raw = (
        "CÔNG BÁO/Số 851 + 852/Ngày 01-7-2025 5\nĐiều 1. A\nTrang 3\n- 4 -\n12\n"
        "2. Khoản hai\nMức 12 triệu\n"
    )

    assert clean_text(raw) == "Điều 1. A\n2. Khoản hai\nMức 12 triệu\n"


def test_extract_docx_joins_runs_into_paragraphs_in_document_order(tmp_path):
    path = _docx(
        tmp_path / "law.docx",
        "<w:p><w:r><w:t>Điều 1. </w:t></w:r><w:r><w:t>Phạm vi</w:t></w:r></w:p>"
        "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>ô A</w:t></w:r><w:r><w:tab/></w:r>"
        "<w:r><w:t>ô B</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
        "<w:p><w:r><w:t>1. Khoản</w:t></w:r></w:p>",
    )

    assert extract_text(path) == "Điều 1. Phạm vi\nô A ô B\n1. Khoản\n"


def test_extract_docx_restores_word_auto_numbering_labels(tmp_path):
    body = (
        "<w:p><w:r><w:t>Điều 2. Đối tượng</w:t></w:r></w:p>"
        + _numbered("Khoản một", 0)
        + _numbered("Điểm a", 1)
        + _numbered("Điểm b", 1)
        + _numbered("Khoản hai", 0)
        + _numbered("Điểm a lại", 1)
        + _numbered("3. Đã có số sẵn", 0)
    )

    text = extract_text(_docx(tmp_path / "law.docx", body, NUMBERING))

    assert text == (
        "Điều 2. Đối tượng\n1. Khoản một\na) Điểm a\nb) Điểm b\n2. Khoản hai\n"
        "a) Điểm a lại\n3. Đã có số sẵn\n"
    )


def test_unsupported_extension_is_rejected(tmp_path):
    with pytest.raises(UnsupportedFormatError):
        extract_text(tmp_path / "law.html")
