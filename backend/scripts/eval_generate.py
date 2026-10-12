"""Generate pending eval questions (LLM) into rag_eval/data/questions.jsonl.

From backend/: .venv/Scripts/python.exe scripts/eval_generate.py [--seed 7] [--force]
Uses EVAL_GENERATOR_MODEL (falls back to CHAT_MODEL with a warning). Costs a few API calls.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.chat_provider import OpenAIProvider  # noqa: E402
from app.services.rag.corpus_manifest import load_manifest  # noqa: E402
from rag_eval.dataset import QUESTIONS_PATH, load_questions, save_questions  # noqa: E402
from rag_eval.dataset_gen import generate_questions  # noqa: E402


async def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--force", action="store_true", help="overwrite an existing question file")
    args = parser.parse_args()
    if load_questions() and not args.force:
        print(f"{QUESTIONS_PATH} exists (reviewed rows would be lost). Use --force.")
        return 1

    settings = get_settings()
    model = settings.eval_generator_model or settings.chat_model
    if model == settings.chat_model:
        print("WARNING: generator model == chat model (self-preference bias not mitigated).")
    provider = OpenAIProvider(settings.openai_api_key, model)
    questions = await generate_questions(provider, load_manifest(), seed=args.seed)
    save_questions(questions)
    by_type: dict[str, int] = {}
    for q in questions:
        by_type[q.type] = by_type.get(q.type, 0) + 1
    print(f"wrote {len(questions)} pending questions with {model}: {by_type}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
