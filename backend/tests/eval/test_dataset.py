import pytest

from rag_eval.dataset import GoldRef, Question, load_questions, save_questions, scoreable


def _question(**overrides) -> Question:
    values = {
        "id": "q1",
        "question": "Thời gian thử việc tối đa?",
        "field": "labor",
        "type": "lookup",
        "gold_answer": "180 ngày",
        "gold_refs": [GoldRef("bo-luat-lao-dong-45-2019-qh14", 25)],
    }
    return Question(**{**values, **overrides})


def test_roundtrip_through_jsonl(tmp_path):
    path = tmp_path / "q.jsonl"
    questions = [_question(), _question(id="q2", gold_refs=[GoldRef("x", 1, clause=2)])]

    save_questions(questions, path)

    assert load_questions(path) == questions


def test_missing_file_is_an_empty_set(tmp_path):
    assert load_questions(tmp_path / "none.jsonl") == []


def test_only_approved_rows_score_unless_provisional():
    rows = [
        _question(id="a", status="approved"),
        _question(id="p"),
        _question(id="r", status="rejected"),
    ]

    assert [q.id for q in scoreable(rows)] == ["a"]
    assert [q.id for q in scoreable(rows, include_pending=True)] == ["a", "p"]


def test_in_corpus_question_needs_gold_refs_but_out_of_corpus_does_not():
    with pytest.raises(ValueError, match="gold_refs"):
        Question.from_dict({**_question().__dict__, "gold_refs": []})
    ooc = Question.from_dict(
        {"id": "o", "question": "Mua bitcoin?", "field": "other", "type": "out_of_corpus",
         "gold_answer": "", "gold_refs": []}
    )  # fmt: skip
    assert ooc.gold_refs == []


def test_invalid_type_is_rejected():
    with pytest.raises(ValueError, match="invalid"):
        Question.from_dict({**_question().__dict__, "gold_refs": [], "type": "essay"})
