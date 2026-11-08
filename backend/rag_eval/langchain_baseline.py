"""Stock-LangChain RAG baseline (the textbook pipeline) for the thesis comparison.

Retrieval tier only.

Same corpus, same embedding model and the same article-level scoring as the custom pipeline, so a
gap in the numbers comes from what differs on purpose:
  - character chunks (RecursiveCharacterTextSplitter 1200/200) instead of Dieu/Khoan chunks;
  - raw chunk text is embedded (no heading path) and search is dense only (no sparse, no RRF);
  - repealed articles stay in the text, as a generic loader ignoring `excluded_articles` would.
Documents are still filtered by `status` when `require_in_force` is set, so the question set stays
comparable. Nothing here is imported by the app; it only runs through `scripts/run_eval.py`.
"""

import time
import unicodedata

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore

from app.core.config import Settings
from app.services.rag.corpus_manifest import CorpusDoc, load_manifest
from app.services.rag.legal_parser import Article, ParsedDocument, parse
from app.services.rag.qdrant_retriever import Hit, SearchOutcome

CHUNK_SIZE = 1200  # characters; the values used in the reference tutorial
CHUNK_OVERLAP = 200


def articles_touched(articles: list[Article], start: int, end: int) -> list[int]:
    """Article numbers whose text overlaps [start, end), in order and without repeats."""
    return list(dict.fromkeys(a.no for a in articles if a.start < end and a.end > start))


def chunk_document(doc: CorpusDoc, parsed: ParsedDocument, splitter) -> list[Document]:
    """Split the whole parsed text; tag each piece with the articles it overlaps (scoring only)."""
    kept = [a for a in parsed.articles if a.label not in doc.excluded_articles]
    # The splitter must be built with add_start_index=True so each piece knows its text offset.
    pieces = splitter.create_documents([parsed.text], metadatas=[{"doc_slug": doc.slug}])
    for piece in pieces:
        start = piece.metadata["start_index"]
        end = start + len(piece.page_content)
        piece.metadata["article_nos"] = articles_touched(kept, start, end)
    return pieces


def build_baseline(settings: Settings, top_k: int, require_in_force: bool):
    from langchain_openai import OpenAIEmbeddings

    if settings.openai_api_key is None:
        raise ValueError("OPENAI_API_KEY is required for the langchain_baseline pipeline.")
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
        dimensions=settings.embedding_dimensions,
        chunk_size=settings.embedding_batch_size,  # keeps each request under the token cap
    )
    return LangChainBaselineRetriever(embeddings, eligible_docs(require_in_force), top_k)


def eligible_docs(require_in_force: bool) -> list[CorpusDoc]:
    return [
        d for d in load_manifest() if d.ingest and (not require_in_force or d.status == "in_force")
    ]


class LangChainBaselineRetriever:
    """Duck-types `QdrantRetriever.search`, so the eval runner treats both the same way."""

    def __init__(self, embeddings: Embeddings, docs: list[CorpusDoc], top_k: int = 5) -> None:
        self._embeddings, self._docs, self._top_k = embeddings, docs, top_k
        self._store: InMemoryVectorStore | None = None
        self.index_info: dict[str, object] = {}

    async def prepare(self) -> None:
        """Chunk and embed the corpus once, outside the per-question timings."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter  # `eval-baseline` extra

        started = time.perf_counter()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True
        )
        chunks: list[Document] = []
        for doc in self._docs:
            parsed = parse(doc.text_path.read_text(encoding="utf-8"))
            chunks.extend(chunk_document(doc, parsed, splitter))
        self._store = await InMemoryVectorStore.afrom_documents(chunks, self._embeddings)
        self.index_info = {
            "pipeline": "langchain_baseline",
            "chunks": len(chunks),
            "index_build_s": round(time.perf_counter() - started, 1),
        }

    async def search(self, query: str, limit: int | None = None) -> SearchOutcome:
        if self._store is None:
            await self.prepare()
        assert self._store is not None
        started = time.perf_counter()
        vector = await self._embeddings.aembed_query(unicodedata.normalize("NFC", query))
        embedded = time.perf_counter()
        found = self._store.similarity_search_with_score_by_vector(vector, k=limit or self._top_k)
        finished = time.perf_counter()
        hits = [
            Hit(
                f"{piece.metadata['doc_slug']}:{piece.metadata['start_index']}",
                score,
                {
                    "doc_slug": piece.metadata["doc_slug"],
                    "article_nos": piece.metadata["article_nos"],
                },
            )
            for piece, score in found
        ]
        return SearchOutcome(hits, (embedded - started) * 1000, (finished - embedded) * 1000)
