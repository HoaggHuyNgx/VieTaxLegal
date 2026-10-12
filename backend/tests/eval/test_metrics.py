import pytest

from rag_eval.metrics import (
    citation_precision_recall,
    first_hit_rank,
    latency_summary,
    mean,
    mrr,
    percentile,
    recall_at_k,
)

GOLD = {("luat-a", 5)}


def test_first_hit_rank_is_one_based_and_matches_any_covered_article():
    retrieved = [{("luat-a", 1)}, {("luat-b", 5)}, {("luat-a", 4), ("luat-a", 5)}]

    assert first_hit_rank(retrieved, GOLD) == 3
    assert first_hit_rank(retrieved[:2], GOLD) is None
    assert first_hit_rank([], GOLD) is None


def test_document_must_match_not_only_the_article_number():
    assert first_hit_rank([{("luat-b", 5)}], GOLD) is None


def test_recall_at_k_and_mrr_hand_computed():
    ranks = [1, 3, None, 5]

    assert recall_at_k(ranks, 1) == 0.25
    assert recall_at_k(ranks, 3) == 0.5
    assert recall_at_k(ranks, 5) == 0.75
    assert mrr(ranks) == pytest.approx((1 + 1 / 3 + 0 + 1 / 5) / 4)


def test_empty_inputs_give_zero_not_errors():
    assert recall_at_k([], 5) == 0.0
    assert mrr([]) == 0.0


def test_citation_precision_recall():
    cited = {("a", 1), ("a", 2), ("b", 3)}
    gold = {("a", 1), ("c", 9)}

    assert citation_precision_recall(cited, gold) == (pytest.approx(1 / 3), 0.5)
    assert citation_precision_recall(set(), gold) == (None, 0.0)
    assert citation_precision_recall(cited, set()) == (0.0, None)


def test_mean_skips_undefined_values():
    assert mean([1.0, None, 0.0]) == 0.5
    assert mean([None]) is None


def test_percentile_nearest_rank():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    assert percentile(values, 50) == 30.0
    assert percentile(values, 95) == 50.0
    assert percentile([], 50) is None
    assert latency_summary([7.0]) == {"p50": 7.0, "p95": 7.0}
