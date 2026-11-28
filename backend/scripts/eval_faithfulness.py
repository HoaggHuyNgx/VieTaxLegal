"""Check the stored answers of a generation result against the sources they were given, in place.

From backend/:
  .venv/Scripts/python.exe scripts/eval_faithfulness.py rag_eval/results/<file>.json --model <id>
Rebuilds each answer's sources from the Qdrant index the run used, so the corpus and the retrieval
code must be the ones of that run. Calls only the checking model; no answer is generated again.
Use a model other than the one that wrote the answers.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.rag.index.embeddings import get_embedder  # noqa: E402
from app.services.rag.index.qdrant_store import get_async_client  # noqa: E402
from app.services.rag.retrieve.qdrant_retriever import QdrantRetriever  # noqa: E402
from app.services.rag.retrieve.query_planner import llm_provider  # noqa: E402
from rag_eval.faithfulness import check_rows, source_texts  # noqa: E402
from rag_eval.provenance import corpus_documents, corpus_texts_sha  # noqa: E402


async def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    result = json.loads(args.result.read_text(encoding="utf-8"))
    meta, config = result["meta"], result["meta"]["config"]
    if corpus_texts_sha(corpus_documents(config["chunk_set"])) != meta["corpus_texts_sha"]:
        print("The corpus texts changed since this run; its sources cannot be rebuilt.")
        return 1

    settings = get_settings()
    client = get_async_client(settings)
    retriever = QdrantRetriever(client, get_embedder(settings), meta["collection"], config["top_k"])
    expand = config.get("expand_articles", False)
    sources = {
        r["id"]: await source_texts(client, meta["collection"], retriever, r["retrieved"], expand)
        for r in result["questions"]
        if "error" not in r
    }
    provider = llm_provider(settings, "openai", args.model)
    summary = await check_rows(provider, result["questions"], sources)
    result["summary"].update(summary)
    meta["faithfulness_model"] = args.model
    args.result.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
