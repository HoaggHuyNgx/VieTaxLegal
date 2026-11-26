"""Embed the corpus and write it to Qdrant (idempotent; safe to re-run).

From backend/:
  .venv/Scripts/python.exe scripts/corpus_ingest.py --chunk-set article --dry-run
  .venv/Scripts/python.exe scripts/corpus_ingest.py --chunk-set article [--only <slug>]

Provider and model come from .env (EMBEDDING_PROVIDER / EMBEDDING_MODEL). --dry-run embeds
nothing and calls no API: it prints chunk counts and the estimated tokens and cost.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.rag.index.embeddings import (  # noqa: E402
    embedding_text,
    estimate_cost_usd,
    get_embedder,
)
from app.services.rag.index.qdrant_store import collection_name, get_sync_client  # noqa: E402
from app.services.rag.ingest.chunking import estimate_tokens  # noqa: E402
from app.services.rag.ingest.corpus_manifest import load_manifest  # noqa: E402
from app.services.rag.ingest.ingest import CHUNKERS, build_chunks, ingest_corpus  # noqa: E402

BKAI_LIMIT = 256


def dry_run(docs, chunk_set: str, model: str, short_prefix: bool) -> None:
    total_chunks = total_tokens = over = 0
    for doc in docs:
        chunks = build_chunks(doc, chunk_set)
        sizes = [estimate_tokens(embedding_text(c, short_prefix)) for c in chunks]
        total_chunks += len(chunks)
        total_tokens += sum(sizes)
        over += sum(size > BKAI_LIMIT for size in sizes)
        print(f"{doc.slug[:44]:44} chunks={len(chunks):4} est_tokens={sum(sizes):7}")
    cost = estimate_cost_usd(model, total_tokens)
    cost_text = "n/a" if cost is None else f"US${cost:.4f}"
    print(f"\nDRY RUN chunk_set={chunk_set} chunks={total_chunks} est_tokens={total_tokens} "
          f"est_cost={cost_text} chunks_over_{BKAI_LIMIT}_tokens={over}")  # fmt: skip


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-set", choices=sorted(CHUNKERS), default=None)
    parser.add_argument("--only", help="ingest a single document slug")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--extra-manifest", type=Path, help="add documents from another manifest")
    args = parser.parse_args()

    settings = get_settings()
    chunk_set = args.chunk_set or settings.rag_chunk_set
    if chunk_set not in CHUNKERS:
        parser.error(f"unknown chunk set '{chunk_set}'")
    manifest = load_manifest()
    if args.extra_manifest:
        manifest += load_manifest(args.extra_manifest)
    docs = [d for d in manifest if not args.only or d.slug == args.only]
    if not any(d.ingest for d in docs):
        parser.error("no documents selected")

    if args.dry_run:
        short_prefix = settings.embedding_provider == "bkai"
        dry_run([d for d in docs if d.ingest], chunk_set, settings.embedding_model, short_prefix)
        return 0

    if chunk_set == "vbpl" and not args.only and not args.extra_manifest:
        # A full run purges unknown documents: without that manifest, every imported one.
        parser.error("a full vbpl ingest needs --extra-manifest corpus/vbpl/manifest.json")

    provider = get_embedder(settings)
    collection = collection_name(chunk_set, provider.model)
    client = get_sync_client(settings)
    started = time.perf_counter()
    stats = ingest_corpus(
        client, collection, provider, docs, chunk_set, settings.embedding_batch_size,
        on_progress=lambda slug, s: print(f"ok {slug}: embedded={s.embedded} reused={s.reused}"),
        purge_unknown=not args.only,  # a full run also drops documents removed from the manifest
    )  # fmt: skip
    cost = estimate_cost_usd(provider.model, stats.tokens)
    print(
        f"\ncollection={collection} docs={stats.docs} chunks={stats.chunks} "
        f"embedded={stats.embedded} reused={stats.reused} deleted_stale={stats.deleted_stale} "
        f"tokens={stats.tokens} est_cost={'n/a' if cost is None else f'US${cost:.4f}'} "
        f"elapsed={time.perf_counter() - started:.1f}s"
    )
    if stats.embedded and stats.tokens:  # measured by the API, unlike the dry-run estimate
        print(f"real_tokens_per_embedded_chunk={stats.tokens / stats.embedded:.0f}")
    print(f"points_in_collection={client.count(collection, exact=True).count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
