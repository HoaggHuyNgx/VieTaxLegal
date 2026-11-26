from rag_eval.export import (
    GENERATION_HEADER,
    RETRIEVAL_HEADER,
    csv_text,
    error_analysis,
    generation_rows,
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
            "in_corpus_questions": 4, "hit@1": 0.5, "hit@3": 0.75, "hit@5": 1.0,
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
    assert row[9:] == ["200/300", "7/9", "-", "-"]  # no total latency or date in this file
    assert len(row) == len(RETRIEVAL_HEADER)


def _generation(refused: list[bool | None]) -> dict:
    return {
        "meta": {
            "date": "2026-11-26",
            "config": {"name": "rag", "tier": "generation"},
            "dataset": {"provisional": False},
        },
        "summary": {
            "answered": 3, "provider_errors": 2, "truncated_answers": 1,
            "citation_precision": 0.5, "citation_recall": 0.5,
            "unsupported_reference_rate": None, "unknown_doc_rate": 0.25,
            "answers_needing_review": 4, "ooc_no_citation_rate": 1.0,
            "ttft_ms": {"p50": 1.0, "p95": 2.0}, "end_to_end_ms": {"p50": 3.0, "p95": 4.0},
            "input_tokens": 10, "output_tokens": 5,
        },
        "questions": [{"id": f"o{i}", "type": "out_of_corpus", "refused": value}
                      for i, value in enumerate(refused)],
    }  # fmt: skip


def _column(result: dict, name: str) -> str:
    return generation_rows([result])[0][GENERATION_HEADER.index(name)]


def test_generation_row_shows_errors_truncation_and_date():
    result = _generation([])

    assert len(generation_rows([result])[0]) == len(GENERATION_HEADER)
    assert _column(result, "errors") == "2" and _column(result, "truncated") == "1"
    assert _column(result, "unsupported ref") == "-"
    assert _column(result, "date") == "2026-11-26"


def test_refusal_rate_appears_only_once_every_question_is_labelled():
    assert _column(_generation([True, None]), "OOC refused (hand)") == "-"
    assert _column(_generation([True, False, True]), "OOC refused (hand)") == "0.667"


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


def test_older_result_files_that_still_say_recall_render_the_same_hit_columns():
    old = _result()
    old["summary"] = {
        **{k: v for k, v in old["summary"].items() if not k.startswith("hit@")},
        "recall@1": 0.5, "recall@3": 0.75, "recall@5": 1.0,
    }  # fmt: skip

    assert retrieval_rows([old])[0][5:9] == retrieval_rows([_result()])[0][5:9]


def test_retrieval_header_names_the_metric_hit_at_k():
    assert RETRIEVAL_HEADER[5:8] == ["Hit@1", "Hit@3", "Hit@5"]
