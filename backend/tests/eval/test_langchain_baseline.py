import asyncio
from pathlib import Path

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.vectorstores import InMemoryVectorStore

from app.core.config import get_settings
from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.legal_parser import parse
from rag_eval.dataset import GoldRef, Question
from rag_eval.langchain_baseline import (
    LangChainBaselineRetriever,
    articles_touched,
    chunk_document,
)
from rag_eval.runner import EvalConfig, build_retriever, run_retrieval_tier

FIXTURE = Path(__file__).parents[1] / "rag" / "fixtures" / "luat-quan-ly-thue-excerpt.txt"


def _doc(**overrides) -> CorpusDoc:
    values = {
        "slug": "luat-qlt-excerpt",
        "number": "108/2025/QH15",
        "title": "Luật Quản lý thuế",
        "doc_type": "luat",
        "field": "tax",
        "file": "raw/x.docx",
        "sha256": "0" * 64,
        "source_url": "https://example.test/doc",
        "status": "in_force",
    }
    return CorpusDoc(**{**values, **overrides})


@pytest.fixture
def parsed():
    return parse(FIXTURE.read_text(encoding="utf-8"))


def test_articles_touched_lists_overlapping_articles_in_order(parsed):
    first, second = parsed.articles[0], parsed.articles[1]

    assert articles_touched(parsed.articles, first.start, first.end) == [first.no]
    assert articles_touched(parsed.articles, first.start, second.end) == [first.no, second.no]
    assert articles_touched(parsed.articles, 0, 1) == []  # the preamble belongs to no article


def test_chunk_document_tags_pieces_and_skips_excluded_articles(parsed):
    splitters = pytest.importorskip("langchain_text_splitters")
    splitter = splitters.RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=50, add_start_index=True
    )
    excluded_label = parsed.articles[1].label

    pieces = chunk_document(_doc(excluded_articles=(excluded_label,)), parsed, splitter)

    assert pieces
    for piece in pieces:
        start = piece.metadata["start_index"]
        assert piece.page_content == parsed.text[start : start + len(piece.page_content)]
        assert parsed.articles[1].no not in piece.metadata["article_nos"]
    assert {n for p in pieces for n in p.metadata["article_nos"]} >= {parsed.articles[0].no}


def _retriever(parsed_articles) -> LangChainBaselineRetriever:
    documents = [
        Document(
            page_content=f"Nội dung điều {article.no}",
            metadata={"doc_slug": "luat-qlt-excerpt", "start_index": article.start,
                      "article_nos": [article.no]},
        )
        for article in parsed_articles
    ]  # fmt: skip
    embeddings = DeterministicFakeEmbedding(size=16)
    retriever = LangChainBaselineRetriever(embeddings, [_doc()], top_k=3)
    retriever._store = asyncio.run(InMemoryVectorStore.afrom_documents(documents, embeddings))
    return retriever


def test_search_returns_hits_with_the_payload_the_scorer_reads(parsed):
    retriever = _retriever(parsed.articles)

    outcome = asyncio.run(retriever.search("Nội dung điều 2"))

    assert len(outcome.hits) == 3
    top = outcome.hits[0]
    assert top.payload == {"doc_slug": "luat-qlt-excerpt", "article_nos": [2]}
    assert outcome.embed_ms >= 0 and outcome.search_ms >= 0


def test_runner_scores_the_baseline_like_any_other_retriever(parsed):
    retriever = _retriever(parsed.articles)

    async def already_built() -> None:  # the real index build needs the manifest and the network
        retriever.index_info = {"pipeline": "langchain_baseline", "chunks": 4}

    retriever.prepare = already_built
    question = Question(
        id="q1", question="Nội dung điều 2", field="tax", type="lookup", gold_answer="x",
        gold_refs=[GoldRef("luat-qlt-excerpt", 2)],
    )  # fmt: skip
    config = EvalConfig(name="t", pipeline="langchain_baseline", top_k=3)

    summary, rows = asyncio.run(run_retrieval_tier(config, retriever, [question]))

    assert summary["recall@1"] == 1.0 and summary["mrr"] == 1.0
    assert summary["chunks"] == 4
    assert rows[0]["rank"] == 1


def test_baseline_is_retrieval_only():
    config = EvalConfig(name="t", tier="generation", pipeline="langchain_baseline")

    with pytest.raises(ValueError, match="retrieval tier only"):
        build_retriever(config, get_settings())
