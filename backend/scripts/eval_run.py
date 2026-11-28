"""Run an evaluation config and write rag_eval/results/<date>-<name>.json.

From backend/:
  .venv/Scripts/python.exe scripts/eval_run.py rag_eval/configs/retrieval/dense-article.json
Retrieval tier needs only the query embedding (cheap). Generation tier calls the chat model.
--provisional also scores unreviewed (pending) questions: for tuning only, flagged in the result.
--pause N waits N seconds between questions, one at a time, for rate-limited API keys.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.chat.provider import LangChainProvider  # noqa: E402
from app.services.rag.index.qdrant_store import collection_name  # noqa: E402
from rag_eval.dataset import load_questions  # noqa: E402
from rag_eval.generation_tier import run_generation_tier  # noqa: E402
from rag_eval.provenance import run_metadata  # noqa: E402
from rag_eval.runner import (  # noqa: E402
    RESULTS_DIR,
    EvalConfig,
    build_retriever,
    result_filename,
    run_retrieval_tier,
    select_questions,
)


async def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--provisional", action="store_true")
    parser.add_argument("--tier", choices=("retrieval", "generation"))
    parser.add_argument(
        "--split", choices=("dev", "test", "holdout"), help="tune on dev, report test and holdout"
    )
    parser.add_argument("--pause", type=float, default=0.0, help="seconds between questions")
    args = parser.parse_args()

    config = EvalConfig.load(args.config)
    config.include_pending = config.include_pending or args.provisional
    config.tier = args.tier or config.tier
    config.split = args.split or config.split
    settings = get_settings()
    questions = load_questions()
    chosen = select_questions(questions, config)
    if not chosen:
        print("No scoreable questions. Approve some (scripts/eval_review.py) or use --provisional.")
        return 1

    retriever, embedder = build_retriever(config, settings)
    if config.tier == "retrieval":
        summary, rows = await run_retrieval_tier(config, retriever, chosen, args.pause)
    else:
        provider = LangChainProvider("openai", settings.openai_api_key, settings.chat_model)
        summary, rows = await run_generation_tier(
            config,
            retriever,
            provider,
            chosen,
            config.max_output_tokens or settings.chat_max_output_tokens,
            pause_seconds=args.pause,
        )
    searched = embedder is not None and (config.rag or config.tier == "retrieval")
    collection = collection_name(config.chunk_set, embedder.model) if searched else None
    result = {
        "meta": run_metadata(config, settings, questions, len(chosen), collection),
        "summary": summary,
        "questions": rows,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    provisional = result["meta"]["dataset"]["provisional"]
    path = RESULTS_DIR / result_filename(config, result["meta"]["date"], provisional)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
