"""Run an evaluation config and write rag_eval/results/<date>-<name>.json.

From backend/:
  .venv/Scripts/python.exe scripts/run_eval.py rag_eval/configs/dense-article.json [--provisional]
Retrieval tier needs only the query embedding (cheap). Generation tier calls the chat model.
--provisional also scores unreviewed (pending) questions: for tuning only, flagged in the result.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.chat_provider import OpenAIProvider  # noqa: E402
from rag_eval.dataset import load_questions  # noqa: E402
from rag_eval.generation_tier import run_generation_tier  # noqa: E402
from rag_eval.runner import (  # noqa: E402
    RESULTS_DIR,
    EvalConfig,
    build_retriever,
    run_metadata,
    run_retrieval_tier,
    select_questions,
)


async def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--provisional", action="store_true")
    parser.add_argument("--tier", choices=("retrieval", "generation"))
    args = parser.parse_args()

    config = EvalConfig.load(args.config)
    config.include_pending = config.include_pending or args.provisional
    config.tier = args.tier or config.tier
    settings = get_settings()
    questions = load_questions()
    chosen = select_questions(questions, config)
    if not chosen:
        print("No scoreable questions. Approve some (scripts/eval_review.py) or use --provisional.")
        return 1

    retriever, _ = build_retriever(config, settings)
    if config.tier == "retrieval":
        summary, rows = await run_retrieval_tier(config, retriever, chosen)
    else:
        provider = OpenAIProvider(settings.openai_api_key, settings.chat_model)
        summary, rows = await run_generation_tier(
            config,
            retriever,
            provider,
            chosen,
            config.max_output_tokens or settings.chat_max_output_tokens,
        )
    result = {
        "meta": run_metadata(config, settings, questions, len(chosen)),
        "summary": summary,
        "questions": rows,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    suffix = "-provisional" if result["meta"]["dataset"]["provisional"] else ""
    path = RESULTS_DIR / f"{result['meta']['date']}-{config.name}-{config.tier}{suffix}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
