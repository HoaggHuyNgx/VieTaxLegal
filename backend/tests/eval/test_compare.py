import pytest

from rag_eval.compare import compare_runs, mcnemar_exact, paired_bootstrap, to_markdown


def _run(ranks: dict[str, int | None], split: str | None = "test") -> dict:
    rows = [{"id": qid, "question": f"câu {qid}", "rank": rank} for qid, rank in ranks.items()]
    rows.append({"id": "ooc", "question": "ngoài phạm vi", "type": "out_of_corpus"})
    return {"meta": {"config": {"name": "x", "split": split}}, "questions": rows}


def test_mcnemar_exact_hand_computed():
    assert mcnemar_exact(0, 5) == pytest.approx(0.0625)  # 2 * (1/2)^5
    assert mcnemar_exact(3, 3) == 1.0
    assert mcnemar_exact(0, 0) == 1.0


def test_bootstrap_of_identical_runs_is_exactly_zero_and_reproducible():
    values = [1.0, 0.0, 1.0, 1.0]

    assert paired_bootstrap(values, values) == (0.0, 0.0, 0.0)
    assert paired_bootstrap([0, 1, 0, 1], [1, 1, 1, 0]) == paired_bootstrap(
        [0, 1, 0, 1], [1, 1, 1, 0]
    )


def test_runs_are_aligned_on_shared_in_corpus_questions_only():
    a = _run({"q1": 1, "q2": None, "q3": 2})
    b = _run({"q1": 1, "q2": 1, "q4": 1})

    result = compare_runs(a, b)

    assert result["n"] == 2  # q1, q2; q3/q4 are missing on one side, ooc has no rank
    assert result["only_a"] == 1 and result["only_b"] == 1
    assert result["metrics"]["hit@1"]["a"] == 0.5 and result["metrics"]["hit@1"]["b"] == 1.0


def test_changes_list_only_moved_questions_with_improvements_first():
    a = _run({"q1": 1, "q2": None, "q3": 4, "q4": 2})
    b = _run({"q1": 1, "q2": 3, "q3": 1, "q4": 5})

    changes = compare_runs(a, b)["changes"]

    assert [c["id"] for c in changes] == ["q2", "q3", "q4"]
    assert [c["better"] for c in changes] == ["b", "b", "a"]


def test_a_split_mismatch_is_reported_not_hidden():
    result = compare_runs(_run({"q1": 1}, "dev"), _run({"q1": 1}, "test"))

    assert result["warnings"]
    assert "split" in to_markdown(result, "a", "b").lower()
