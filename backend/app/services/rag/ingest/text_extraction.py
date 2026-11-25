"""Turn a downloaded law file (.docx / .pdf) into clean NFC plain text.

Offline tooling for the corpus pipeline; the web app never calls this. Text is only normalised
(Unicode NFC, whitespace, page headers/footers dropped), never rewritten.
"""

import re
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Page furniture of official sources: Cong bao banner, "Trang 3", "- 3 -", lone page numbers.
_PAGE_FURNITURE = re.compile(
    r"^(CÔNG BÁO\b.*"
    r"|Trang\s+\d+(\s*/\s*\d+)?"
    r"|-\s*\d+\s*-"
    r"|\d{1,3})$",
    re.IGNORECASE,
)


class UnsupportedFormatError(ValueError):
    pass


def clean_text(raw: str) -> str:
    """NFC, trim, collapse inner spaces, drop page furniture, squeeze blank lines."""
    lines: list[str] = []
    for line in unicodedata.normalize("NFC", raw).replace("\r", "").replace(" ", " ").split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line and _PAGE_FURNITURE.match(line):
            continue
        if not line and (not lines or not lines[-1]):
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def _val(node: ElementTree.Element | None) -> str:
    return node.get(f"{_W}val", "") if node is not None else ""


def _numbering_levels(archive: zipfile.ZipFile) -> dict[tuple[str, str], tuple[str, str]]:
    """Map (numId, ilvl) -> (numFmt, lvlText) from word/numbering.xml, if the file has one."""
    if "word/numbering.xml" not in archive.namelist():
        return {}
    root = ElementTree.fromstring(archive.read("word/numbering.xml"))
    abstract = {
        a.get(f"{_W}abstractNumId"): {
            _val(lvl.find(f"{_W}ilvl")) or lvl.get(f"{_W}ilvl", ""): (
                _val(lvl.find(f"{_W}numFmt")),
                _val(lvl.find(f"{_W}lvlText")),
            )
            for lvl in a.findall(f"{_W}lvl")
        }
        for a in root.findall(f"{_W}abstractNum")
    }
    levels = {}
    for num in root.findall(f"{_W}num"):
        for ilvl, fmt in abstract.get(_val(num.find(f"{_W}abstractNumId")), {}).items():
            levels[(num.get(f"{_W}numId", ""), ilvl)] = fmt
    return levels


def _auto_number_label(levels, counters, num_id: str, ilvl: str) -> str:
    """Literal label ("1.", "a)") Word would draw for an auto-numbered paragraph, or ""."""
    fmt, pattern = levels.get((num_id, ilvl), ("", ""))
    counters[(num_id, ilvl)] = counters.get((num_id, ilvl), 0) + 1
    for other_id, other_lvl in list(counters):  # a new item restarts the deeper levels
        if other_id == num_id and other_lvl > ilvl:
            counters[(other_id, other_lvl)] = 0
    count = counters[(num_id, ilvl)]
    symbol = {"decimal": str(count), "lowerLetter": chr(96 + count) if count <= 26 else ""}.get(fmt)
    placeholder = f"%{int(ilvl) + 1}"
    if not symbol or placeholder not in pattern:
        return ""
    label = pattern.replace(placeholder, symbol)
    return "" if "%" in label else label


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
        levels = _numbering_levels(archive)
    counters: dict[tuple[str, str], int] = {}
    paragraphs = []
    for paragraph in root.iter(f"{_W}p"):
        parts = []
        for node in paragraph.iter():
            if node.tag == f"{_W}t":
                parts.append(node.text or "")
            elif node.tag in (f"{_W}tab", f"{_W}br"):
                parts.append(" ")
        text = "".join(parts)
        numbering = paragraph.find(f"{_W}pPr/{_W}numPr")
        if numbering is not None and text.strip():
            num_id = _val(numbering.find(f"{_W}numId"))
            ilvl = _val(numbering.find(f"{_W}ilvl")) or "0"
            label = _auto_number_label(levels, counters, num_id, ilvl)
            if label and not text.lstrip().startswith(label):
                text = f"{label} {text.lstrip()}"
        paragraphs.append(text)
    return "\n".join(paragraphs)


def extract_pdf(path: Path) -> str:
    import pymupdf  # offline tooling dependency; keep out of the app import path

    # pymupdf keeps Vietnamese glyph clusters intact; pypdf split words ("điề u") on several
    # official PDFs and shredded others entirely.
    with pymupdf.open(path) as document:
        return "\n".join(page.get_text() for page in document)


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return clean_text(extract_docx(path))
    if suffix == ".pdf":
        return clean_text(extract_pdf(path))
    raise UnsupportedFormatError(f"Unsupported corpus file type: {path.name}")


_PART_FOOTER_RE = re.compile(r"^(\(Xem tiếp|VĂN PHÒNG CHÍNH PHỦ XUẤT BẢN)")
_PART_HEADER_RE = re.compile(r"^\(Tiếp theo Công báo")


def join_parts(texts: list[str]) -> str:
    """Join the parts of a document published over several Cong bao issues.

    Drops the print footer ("Xem tiep ...") that ends each part and the banner
    ("... Tiep theo Cong bao ...") that opens the next one.
    """
    pieces = []
    for number, text in enumerate(texts):
        lines = text.split("\n")
        if number > 0:
            marker = next((i for i, line in enumerate(lines) if _PART_HEADER_RE.match(line)), -1)
            lines = lines[marker + 1 :]
        if number < len(texts) - 1:
            cut = next((i for i, line in enumerate(lines) if _PART_FOOTER_RE.match(line)), None)
            lines = lines[:cut] if cut is not None else lines
        pieces.append("\n".join(lines).strip())
    return "\n".join(pieces) + "\n"
