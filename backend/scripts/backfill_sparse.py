"""Add sparse (lexical) vectors to an already ingested collection; no embedding cost.

From backend/: .venv/Scripts/python.exe scripts/backfill_sparse.py --chunk-set article
Run once per collection before using RAG_RETRIEVAL_MODE=hybrid. Safe to re-run.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.rag.ingest import CHUNKERS, backfill_sparse  # noqa: E402
from app.services.rag.qdrant_store import collection_name, get_sync_client  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-set", choices=sorted(CHUNKERS), default=None)
    parser.add_argument("--model", default=None, help="embedding model of the collection")
    args = parser.parse_args()
    settings = get_settings()
    name = collection_name(
        args.chunk_set or settings.rag_chunk_set, args.model or settings.embedding_model
    )
    written = backfill_sparse(get_sync_client(settings), name)
    print(f"collection={name} sparse_vectors_written={written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
