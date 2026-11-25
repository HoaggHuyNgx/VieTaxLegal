"""Compare two retrieval result files question by question; print a Markdown report.

From backend/:
  .venv/Scripts/python.exe scripts/eval_compare.py rag_eval/results/A.json rag_eval/results/B.json
Gives Hit@1, Hit@5 and MRR for both runs, the paired bootstrap 95% CI of B - A, McNemar's exact
p for Hit@k, and the questions whose rank changed (material for the error analysis).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag_eval.compare import compare_runs, to_markdown  # noqa: E402


def _load(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result["meta"]["config"].get("tier") != "retrieval":
        raise SystemExit(f"{path.name}: only retrieval-tier results carry per-question ranks.")
    return result


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("a", type=Path, help="baseline result file")
    parser.add_argument("b", type=Path, help="candidate result file")
    args = parser.parse_args()
    result = compare_runs(_load(args.a), _load(args.b))
    print(to_markdown(result, args.a.stem, args.b.stem), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
