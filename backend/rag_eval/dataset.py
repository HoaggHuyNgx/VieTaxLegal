"""Evaluation question set: JSONL rows with a review status. Only `approved` rows are scored."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
QUESTIONS_PATH = DATA_DIR / "questions.jsonl"
TYPES = ("lookup", "numeric", "multi", "out_of_corpus")
STATUSES = ("pending", "approved", "rejected")


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
