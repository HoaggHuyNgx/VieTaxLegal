"""Merge rag_eval/results/*.json into SUMMARY.md and CSV tables for the thesis.

From backend/: .venv/Scripts/python.exe scripts/export_results.py
Provisional rows (unreviewed gold) are labelled; do not quote them in the thesis.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag_eval import export  # noqa: E402
from rag_eval.runner import RESULTS_DIR  # noqa: E402


def main() -> int:
    results = export.load_results(RESULTS_DIR)
    retrieval = export.retrieval_rows(results)
    generation = export.generation_rows(results)
    (RESULTS_DIR / "summary-retrieval.csv").write_text(
        export.csv_text(export.RETRIEVAL_HEADER, retrieval), encoding="utf-8", newline="\n"
    )
    (RESULTS_DIR / "summary-generation.csv").write_text(
        export.csv_text(export.GENERATION_HEADER, generation), encoding="utf-8", newline="\n"
    )
    sections = [
        f"# RAG evaluation summary ({date.today()})",
        "",
        "Counts are small (tens of questions): differences of a few points are within noise.",
        "",
        "## Retrieval tier",
        export.markdown_table(export.RETRIEVAL_HEADER, retrieval),
        "",
        "## Generation tier",
        export.markdown_table(export.GENERATION_HEADER, generation),
        "",
        "## Error analysis (retrieval misses)",
        "",
        *(export.error_markdown(r) for r in results if r["meta"]["config"]["tier"] == "retrieval"),
    ]
    (RESULTS_DIR / "SUMMARY.md").write_text("\n".join(sections), encoding="utf-8", newline="\n")
    print(f"wrote SUMMARY.md + 2 CSVs for {len(results)} result files in {RESULTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
