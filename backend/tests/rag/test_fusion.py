import pytest

from app.services.rag.fusion import rrf_fuse


def test_item_in_both_rankings_beats_items_in_one():
    fused = rrf_fuse([["a", "b", "c"], ["c", "d"]])

    assert [i for i, _ in fused][:2] == ["c", "a"]
    assert dict(fused)["c"] == pytest.approx(1 / 63 + 1 / 61)


def test_ties_break_by_first_ranking_position_then_id():
    # a and b swap ranks between the lists -> equal scores; the first ranking decides.
    fused = rrf_fuse([["a", "b"], ["b", "a"]])

    assert [i for i, _ in fused] == ["a", "b"]
    assert fused[0][1] == pytest.approx(fused[1][1])


def test_result_is_identical_across_runs_and_input_dict_order():
    rankings = [["x", "y", "z"], ["z", "y", "x"]]

    assert rrf_fuse(rankings) == rrf_fuse([list(r) for r in rankings])


def test_duplicates_in_one_ranking_count_once_and_empty_input_is_empty():
    assert dict(rrf_fuse([["a", "a"]]))["a"] == pytest.approx(1 / 61)
    assert rrf_fuse([[], []]) == []
