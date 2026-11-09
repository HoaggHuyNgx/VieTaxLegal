"""Score the stored answers of a generation result against gold_answer, in place.

From backend/:
  .venv/Scripts/python.exe scripts/judge_answers.py rag_eval/results/<file>.json --model <id>
Calls only the judge model, so existing runs can be compared without generating answers again.
Use a judge model other than the one that wrote the answers.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.rag.query_planner import llm_provider  # noqa: E402
from rag_eval.answer_judge import add_verdicts_to_result, judge_rows  # noqa: E402
from rag_eval.dataset import load_questions  # noqa: E402


async def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    result = json.loads(args.result.read_text(encoding="utf-8"))
    gold = {q.id: (q.question, q.gold_answer) for q in load_questions()}
    provider = llm_provider(get_settings(), "openai", args.model)
    summary = await judge_rows(provider, result["questions"], gold)
    text = add_verdicts_to_result(result, summary, args.model)
    args.result.write_text(text, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
