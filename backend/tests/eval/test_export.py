from rag_eval.export import (
    csv_text,
    error_analysis,
    markdown_table,
    miss_reason,
    retrieval_rows,
)


def _result(**overrides) -> dict:
    result = {
        "meta": {
            "config": {"name": "dense-article", "tier": "retrieval", "chunk_set": "article"},
            "dataset": {"provisional": True},
        },
        "summary": {
            "in_corpus_questions": 4, "recall@1": 0.5, "recall@3": 0.75, "recall@5": 1.0,
            "mrr": 0.7, "embed_ms": {"p50": 200.0, "p95": 300.0},
            "search_ms": {"p50": 7.0, "p95": 9.0},
        },
        "questions": [],
    }  # fmt: skip
    return {**result, **overrides}


def test_retrieval_row_formats_metrics_and_flags_provisional_runs():
    row = retrieval_rows([_result()])[0]

    assert row[0] == "dense-article (provisional)"
    assert row[1:5] == ["article", "dense", "-", "4"]
    assert row[5:9] == ["0.500", "0.750", "1.000", "0.700"]
    assert row[9:] == ["200/300", "7/9"]


def test_generation_results_are_not_mixed_into_the_retrieval_table():
    generation = _result()
    generation["meta"]["config"]["tier"] = "generation"

    assert retrieval_rows([generation]) == []


def test_markdown_and_csv_have_matching_shape():
    header, rows = ["a", "b"], [["1", "2"]]

    assert markdown_table(header, rows).splitlines() == ["| a | b |", "|---|---|", "| 1 | 2 |"]
    assert csv_text(header, rows) == "a,b\n1,2\n"


def test_miss_reason_separates_wrong_document_from_wrong_article():
    gold = [["luat-a", 5]]

    assert miss_reason({"gold": gold, "rank": 2, "top": []}) == "hit"
    assert (
        miss_reason({"gold": gold, "rank": None, "top": [["luat-a", [9]]]})
        == "right_doc_wrong_article"
    )
    assert miss_reason({"gold": gold, "rank": None, "top": [["luat-b", [5]]]}) == "wrong_document"


def _row(row_id: str, rank: int | None = None, score: float = 0.5) -> dict:
    return {
        "id": row_id, "type": "lookup", "rank": rank, "gold": [["a", 1]], "top": [],
        "top1_score": score, "question": "?",
    }  # fmt: skip


def test_error_analysis_lists_only_in_corpus_misses_sorted_by_top_score():
    rows = [
        _row("hit", rank=1, score=0.9),
        _row("m1", score=0.5),
        _row("m2", score=0.8),
        {"id": "ooc", "type": "out_of_corpus", "gold": [], "top": [], "top1_score": 0.99},
    ]  # fmt: skip

    misses = error_analysis(_result(questions=rows))

    assert [m["id"] for m in misses] == ["m2", "m1"]
    assert misses[0]["reason"] == "wrong_document"
