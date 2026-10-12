"""Parse Vietnamese legal text into Chuong / Muc / Dieu / Khoan / Diem.

Pure functions, no I/O. Offsets (``start``/``end``) index into the exact text passed to ``parse``.
Headings count only at line start, and only in sequence: a line such as "Dieu 35 cua Luat nay..."
(a wrapped cross-reference) or a stray out-of-order heading is recorded in the diagnostics and
treated as body text, so a wrong citation never silently enters the corpus.
"""

import re
from dataclasses import dataclass, field

from app.services.rag.legal_clauses import CLAUSE_RE, POINT_RE, Clause, split_body

ARTICLE_RE = re.compile(r"^Điều\s+(\d+)\s?([a-zđ]?)\s?\.\s+(\S.*)$")
CHAPTER_RE = re.compile(r"^Chương\s+([IVXLC]+|\d+)\b\.?\s*(.*)$")
SECTION_RE = re.compile(r"^Mục\s+(\d+)\b\.?\s*(.*)$")
# Signature block, receivers, annexes, law adoption note and the Cong bao print footer end the
# last article's body.
TRAILER_RE = re.compile(
    r"^(Nơi nhận\b|TM\.\s|KT\.\s|CHỦ TỊCH QUỐC HỘI|XÁC THỰC VĂN BẢN HỢP NHẤT|PHỤ LỤC\b"
    r"|Luật này (đã )?được Quốc hội|\(Xem tiếp|VĂN PHÒNG CHÍNH PHỦ XUẤT BẢN)"
)
# "(Xem tiep Cong bao so ...)" means the downloaded text is only the first part of the document.
CONTINUATION_RE = re.compile(r"^\(Xem tiếp")
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


@dataclass
class Article:
    no: int
    suffix: str
    title: str
    chapter: str | None
    section: str | None
    start: int
    end: int
    intro: str = ""  # body text before the first khoan
    clauses: list[Clause] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.no}{self.suffix}"


@dataclass
class Diagnostics:
    article_count: int = 0
    missing_numbers: list[int] = field(default_factory=list)
    skipped_headings: list[str] = field(default_factory=list)
    empty_articles: list[str] = field(default_factory=list)
    rejected_clauses: list[str] = field(default_factory=list)  # "<article label>: <line>"
    trailer_start: int | None = None
    continuation_marker: bool = False

    def unexplained_gaps(self, known_gaps: tuple[int, ...] = ()) -> list[int]:
        return [n for n in self.missing_numbers if n not in known_gaps]

    def stale_known_gaps(self, known_gaps: tuple[int, ...] = ()) -> list[int]:
        """``known_gaps`` entries that are not real gaps (would hide a future real one)."""
        return [n for n in known_gaps if n not in self.missing_numbers]


@dataclass
class ParsedDocument:
    text: str
    articles: list[Article]
    diagnostics: Diagnostics


def _lines_with_offsets(text: str) -> list[tuple[int, str]]:
    result, pos = [], 0
    for line in text.split("\n"):
        result.append((pos, line))
        pos += len(line) + 1
    return result


def _is_next_article(prev: Article | None, no: int, suffix: str) -> bool:
    if prev is None:
        return no == 1 and not suffix
    if no == prev.no + 1 and not suffix:
        return True
    # 5a after 5, 5b after 5a
    return no == prev.no and bool(suffix) and suffix > prev.suffix


def _roman_or_int(token: str) -> int:
    if token.isdigit():
        return int(token)
    total = 0
    for char, nxt in zip(token, token[1:] + " "):
        value = _ROMAN[char]
        total += -value if _ROMAN.get(nxt, 0) > value else value
    return total


def _is_heading_remainder(rest: str) -> bool:
    """A real Chuong/Muc heading has nothing after the number, or an all-caps title.

    "Muc 2 Chuong III Nghi dinh nay..." is a wrapped cross-reference, not a heading.
    """
    rest = rest.strip()
    return not rest or rest.isupper()


def _heading_title(lines: list[tuple[int, str]], index: int, inline: str) -> tuple[str, int]:
    """Title of a Chuong/Muc heading plus the index of the first line after it.

    The title is the inline text and/or the following all-caps lines (titles wrap).
    """
    parts, nxt = ([inline] if inline else []), index + 1
    while nxt < len(lines) and lines[nxt][1].isupper() and len(lines[nxt][1]) <= 200:
        if ARTICLE_RE.match(lines[nxt][1]) or CHAPTER_RE.match(lines[nxt][1]):
            break
        parts.append(lines[nxt][1])
        nxt += 1
    return " ".join(parts), nxt


def parse(text: str) -> ParsedDocument:
    lines = _lines_with_offsets(text)
    diagnostics = Diagnostics()
    articles: list[Article] = []
    bodies: list[list[tuple[int, str]]] = []
    chapter = section = None
    chapter_no = section_no = 0
    skip_until = 0  # lines before this index were consumed as a chapter/section title

    for index, (offset, line) in enumerate(lines):
        if index < skip_until:
            continue
        article_match = ARTICLE_RE.match(line)
        if article_match:
            no, suffix = int(article_match.group(1)), article_match.group(2)
            prev = articles[-1] if articles else None
            if _is_next_article(prev, no, suffix) or (prev and no > prev.no):
                if prev and no > prev.no + 1:
                    diagnostics.missing_numbers.extend(range(prev.no + 1, no))
                title = article_match.group(3).strip()
                articles.append(
                    Article(no, suffix, title, chapter, section, offset, offset + len(line))
                )
                bodies.append([])
            else:
                diagnostics.skipped_headings.append(line[:80])
                if articles:
                    bodies[-1].append((offset, line))
            continue

        if articles and TRAILER_RE.match(line):
            diagnostics.trailer_start = offset
            diagnostics.continuation_marker = bool(CONTINUATION_RE.match(line))
            break

        chapter_match = CHAPTER_RE.match(line)
        if chapter_match and _is_heading_remainder(chapter_match.group(2)):
            number = _roman_or_int(chapter_match.group(1))
            if chapter_no == 0 or number == chapter_no + 1:
                title, skip_until = _heading_title(lines, index, chapter_match.group(2).strip())
                chapter = f"Chương {chapter_match.group(1)}" + (f" - {title}" if title else "")
                chapter_no, section, section_no = number, None, 0
                continue
            if number == chapter_no:  # banner repeated where a multi-part source resumes
                _, skip_until = _heading_title(lines, index, chapter_match.group(2).strip())
                continue
            diagnostics.skipped_headings.append(line[:80])
        section_match = SECTION_RE.match(line)
        if section_match and _is_heading_remainder(section_match.group(2)):
            number = int(section_match.group(1))
            if section_no == 0 or number == section_no + 1:
                title, skip_until = _heading_title(lines, index, section_match.group(2).strip())
                section = f"Mục {section_match.group(1)}" + (f" - {title}" if title else "")
                section_no = number
                continue
            if number == section_no:
                _, skip_until = _heading_title(lines, index, section_match.group(2).strip())
                continue
            diagnostics.skipped_headings.append(line[:80])

        if articles and line:
            last = articles[-1]
            wrapped_title = (
                not bodies[-1]
                and line[0].islower()
                and not last.title.endswith((".", ":", ";"))
                and not POINT_RE.match(line)
                and not CLAUSE_RE.match(line)
            )
            if wrapped_title:
                last.title += " " + line  # heading wrapped onto the next line (PDF line breaks)
            else:
                bodies[-1].append((offset, line))
            last.end = offset + len(line)

    for article, body in zip(articles, bodies):
        article.intro, article.clauses, rejected = split_body(body)
        diagnostics.rejected_clauses.extend(f"{article.label}: {line}" for line in rejected)
        if not body:
            diagnostics.empty_articles.append(article.label)
    diagnostics.article_count = len(articles)
    return ParsedDocument(text=text, articles=articles, diagnostics=diagnostics)
