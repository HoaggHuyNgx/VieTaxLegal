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
    suffix = " (provisional)" if meta["dataset"]["provisional"] else ""
    return f"{meta['config']['name']}{suffix}"


def retrieval_rows(results: list[dict]) -> list[list[str]]:
    rows = []
    for result in (r for r in results if r["meta"]["config"]["tier"] == "retrieval"):
        cfg, s = result["meta"]["config"], result["summary"]
        rows.append([
            _label(result), cfg["chunk_set"], cfg.get("mode", "dense"), cfg.get("rerank") or "-",
            str(s["in_corpus_questions"]), _fmt(s["recall@1"]), _fmt(s["recall@3"]),
            _fmt(s["recall@5"]), _fmt(s["mrr"]), _ms(s["embed_ms"]), _ms(s["search_ms"]),
        ])  # fmt: skip
    return rows


def generation_rows(results: list[dict]) -> list[list[str]]:
    rows = []
    for result in (r for r in results if r["meta"]["config"]["tier"] == "generation"):
        s = result["summary"]
        rows.append([
            _label(result), str(s["answered"]), _fmt(s["citation_precision"]),
            _fmt(s["citation_recall"]), _fmt(s["hallucinated_reference_rate"]),
            _fmt(s["ooc_no_citation_rate"]), _fmt(s["ooc_abstain_phrase_rate"]),
            _ms(s["ttft_ms"]), _ms(s["total_ms"]), f"{s['input_tokens']}/{s['output_tokens']}",
        ])  # fmt: skip
    return rows


RETRIEVAL_HEADER = ["config", "chunks", "mode", "rerank", "n", "R@1", "R@3", "R@5", "MRR",
                    "embed ms p50/p95", "search ms p50/p95"]  # fmt: skip
GENERATION_HEADER = ["config", "answered", "cit. precision", "cit. recall", "hallucinated ref",
                     "OOC no-cite", "OOC abstain", "TTFT ms p50/p95", "total ms p50/p95",
                     "tokens in/out"]  # fmt: skip


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
