"""Split one article body into intro / Khoan / Diem. Pure functions, no I/O.

Only in-sequence numbers count: Khoan 1, 2, 3... and Diem a, b, c, d, dd... Anything else stays
body text, and rejected Khoan-looking lines are returned so the caller can report them instead of
silently losing structure.
"""

import re
from dataclasses import dataclass, field

# Optional 1-2 digit footnote marker glued to the number by the source ("1.2 San pham...").
CLAUSE_RE = re.compile(r"^(\d+)\.(\d{1,2})?\s+\S")
POINT_RE = re.compile(r"^([a-zđ])\)\s+\S")
# Letters used to enumerate diem, in order (Vietnamese skips f, j, w, z).
POINT_LETTERS = "abcdđeghiklmnopqrstuvxy"


@dataclass
class Point:
    label: str
    text: str


@dataclass
class Clause:
    no: int
    text: str  # clause line(s) before the first diem
    start: int
    end: int
    points: list[Point] = field(default_factory=list)


def _is_next_point(clause: Clause, label: str) -> bool:
    expected = POINT_LETTERS[len(clause.points)] if len(clause.points) < len(POINT_LETTERS) else ""
    return label == expected


def split_body(body_lines: list[tuple[int, str]]) -> tuple[str, list[Clause], list[str]]:
    """Return ``(intro, clauses, rejected_clause_lines)`` for the (offset, line) body lines."""
    intro: list[str] = []
    clauses: list[Clause] = []
    rejected: list[str] = []
    clause: Clause | None = None
    for offset, line in body_lines:
        clause_match = CLAUSE_RE.match(line)
        if clause_match:
            if int(clause_match.group(1)) == (clause.no + 1 if clause else 1):
                clause = Clause(int(clause_match.group(1)), line, offset, offset + len(line))
                clauses.append(clause)
                continue
            rejected.append(line[:60])
        if clause is None:
            intro.append(line)
            continue
        clause.end = offset + len(line)
        point_match = POINT_RE.match(line)
        if point_match and _is_next_point(clause, point_match.group(1)):
            clause.points.append(Point(label=point_match.group(1), text=line))
        elif clause.points:
            clause.points[-1].text += "\n" + line
        else:
            clause.text += "\n" + line
    return "\n".join(intro).strip(), clauses, rejected
