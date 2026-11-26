"""Evaluation question set: JSONL rows with a review status. Only `approved` rows are scored.

Approved rows carry a fixed `split`: tune settings (thresholds, RRF) on `dev`, and quote only `test`
numbers in the thesis, so a reported score is never measured on the questions used to pick it.
`holdout` is set by hand on questions written after the settings were chosen; nothing assigns it,
and runs skip it unless asked for it by name.
"""

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
QUESTIONS_PATH = DATA_DIR / "questions.jsonl"
TYPES = ("lookup", "numeric", "multi", "out_of_corpus")
STATUSES = ("pending", "approved", "rejected")
SPLITS = ("", "dev", "test", "holdout")  # "" = not assigned yet


@dataclass
class GoldRef:
    doc_slug: str
    article: int
    clause: int | None = None


@dataclass
class Question:
    id: str
    question: str
    field: str
    type: str
    gold_answer: str
    gold_refs: list[GoldRef] = field(default_factory=list)
    source: str = "llm"  # llm | human
    status: str = "pending"
    reviewer_note: str = ""
    split: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        refs = [GoldRef(**ref) for ref in data.get("gold_refs", [])]
        known = {
            k: v for k, v in data.items() if k in cls.__dataclass_fields__ and k != "gold_refs"
        }
        question = cls(**known, gold_refs=refs)
        if question.type not in TYPES or question.status not in STATUSES:
            raise ValueError(f"{question.id}: invalid type/status")
        if question.split not in SPLITS:
            raise ValueError(f"{question.id}: invalid split")
        if question.type != "out_of_corpus" and not question.gold_refs:
            raise ValueError(f"{question.id}: in-corpus question needs gold_refs")
        return question


def load_questions(path: Path = QUESTIONS_PATH) -> list[Question]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Question.from_dict(json.loads(line)) for line in lines if line.strip()]


def save_questions(questions: list[Question], path: Path = QUESTIONS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(q.to_json() for q in questions) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def scoreable(questions: list[Question], include_pending: bool = False) -> list[Question]:
    """Approved questions; `include_pending` is for provisional tuning runs only."""
    allowed = {"approved", "pending"} if include_pending else {"approved"}
    return [q for q in questions if q.status in allowed]


def assign_splits(questions: list[Question]) -> None:
    """Give every approved question without a split one, balanced per (field, type).

    Splits already assigned never move, so adding questions later cannot reshuffle the test set.
    Within a stratum, new questions go (in id-hash order, so the result is reproducible) to
    whichever side currently has fewer, dev on a tie.
    """
    counts: Counter[tuple[str, str, str]] = Counter(
        (q.field, q.type, q.split) for q in questions if q.split
    )
    todo = [q for q in questions if q.status == "approved" and not q.split]
    for q in sorted(todo, key=lambda q: hashlib.sha256(q.id.encode()).hexdigest()):
        dev, test = counts[(q.field, q.type, "dev")], counts[(q.field, q.type, "test")]
        q.split = "dev" if dev <= test else "test"
        counts[(q.field, q.type, q.split)] += 1
