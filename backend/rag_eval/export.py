"""Merge result files into Markdown/CSV tables and an error analysis for the thesis."""

import csv
import io
import json
from pathlib import Path


def load_results(results_dir: Path) -> list[dict]:
    results = []
    for path in sorted(results_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["file"] = path.name
        results.append(data)
    return results


def _fmt(value, digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


def _ms(summary: dict | None) -> str:
    return (
        "-"
        if not summary or summary.get("p50") is None
        else f"{summary['p50']:.0f}/{summary['p95']:.0f}"
    )


def _label(result: dict) -> str:
    meta = result["meta"]
    split = meta["config"].get("split")  # older result files predate splits
    suffix = " (provisional)" if meta["dataset"]["provisional"] else ""
    return f"{meta['config']['name']}{f' [{split}]' if split else ''}{suffix}"


def _hit(summary: dict, k: int) -> float | None:
    # Result files written before the rename call the same number recall@k.
    return summary.get(f"hit@{k}", summary.get(f"recall@{k}"))


def retrieval_rows(results: list[dict]) -> list[list[str]]:
    rows = []
    for result in (r for r in results if r["meta"]["config"]["tier"] == "retrieval"):
        cfg, s = result["meta"]["config"], result["summary"]
        rows.append([
            _label(result), cfg["chunk_set"], cfg.get("mode", "dense"), cfg.get("rerank") or "-",
            str(s["in_corpus_questions"]), _fmt(_hit(s, 1)), _fmt(_hit(s, 3)),
            _fmt(_hit(s, 5)), _fmt(s["mrr"]), _ms(s["embed_ms"]), _ms(s["search_ms"]),
            _ms(s.get("retrieval_ms")), result["meta"].get("date", "-"),
        ])  # fmt: skip
    return rows


def refusal_rate(rows: list[dict]) -> float | None:
    """Share of out-of-corpus answers a person marked `refused`; None until all are marked."""
    labels = [
        r.get("refused") for r in rows if r.get("type") == "out_of_corpus" and "error" not in r
    ]
    if not labels or not all(isinstance(label, bool) for label in labels):
        return None
    return sum(labels) / len(labels)


def generation_rows(results: list[dict]) -> list[list[str]]:
    rows = []
    for result in (r for r in results if r["meta"]["config"]["tier"] == "generation"):
        s = result["summary"]
        # `.get`: older result files measured references differently and have no such keys.
        rows.append([
            _label(result), str(s["answered"]), _fmt(s.get("provider_errors")),
            _fmt(s.get("truncated_answers")), _fmt(s["citation_precision"]),
            _fmt(s["citation_recall"]), _fmt(s.get("unsupported_reference_rate")),
            _fmt(s.get("unknown_doc_rate")), _fmt(s.get("answers_needing_review")),
            _fmt(s["ooc_no_citation_rate"]), _fmt(refusal_rate(result.get("questions", []))),
            _ms(s["ttft_ms"]), _ms(s.get("end_to_end_ms")),
            f"{s['input_tokens']}/{s['output_tokens']}", result["meta"].get("date", "-"),
        ])  # fmt: skip
    return rows


RETRIEVAL_HEADER = ["config", "chunks", "mode", "rerank", "n", "Hit@1", "Hit@3", "Hit@5", "MRR@5",
                    "embed ms p50/p95", "search ms p50/p95", "total ms p50/p95",
                    "date"]  # fmt: skip
GENERATION_HEADER = ["config", "answered", "errors", "truncated", "cit. precision", "cit. recall",
                     "unsupported ref", "unknown doc", "needs review", "OOC no-cite",
                     "OOC refused (hand)", "TTFT ms p50/p95", "end-to-end ms p50/p95",
                     "tokens in/out", "date"]  # fmt: skip


def markdown_table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def csv_text(header: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def miss_reason(row: dict) -> str:
    """Why a retrieval missed: wrong document, or right document but wrong article."""
    gold_slugs = {slug for slug, _ in row["gold"]}
    if row.get("rank") is not None:
        return "hit"
    top_slugs = {slug for slug, _ in row["top"]}
    return "right_doc_wrong_article" if gold_slugs & top_slugs else "wrong_document"


def error_analysis(result: dict, limit: int = 10) -> list[dict]:
    """Questions whose gold article was not retrieved, worst first (by top-1 score)."""
    misses = [
        {**row, "reason": miss_reason(row)}
        for row in result["questions"]
        if row.get("type") != "out_of_corpus" and row.get("rank") is None
    ]
    return sorted(misses, key=lambda r: -r["top1_score"])[:limit]


def error_markdown(result: dict) -> str:
    lines = [f"### {_label(result)}", ""]
    misses = error_analysis(result)
    if not misses:
        return "\n".join(lines + ["No misses within the retrieved depth.", ""])
    for row in misses:
        lines.append(f"- `{row['id']}` [{row['reason']}] {row['question']} -> gold {row['gold']}")
    return "\n".join(lines + [""])
