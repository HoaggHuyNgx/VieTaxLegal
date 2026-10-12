"""Regressions from the phase 4-10 code review."""

from dataclasses import replace
from pathlib import Path

from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.services import chat_retriever
from app.services.chat_citations import strip_markers
from app.services.rag.chunking import article_chunks
from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.embeddings import FakeEmbedder
from app.services.rag.ingest import ingest_corpus
from app.services.rag.legal_parser import parse
from app.services.rag.qdrant_store import ensure_collection
from rag_eval.reference_check import check_references

EXCERPT = Path(__file__).parent / "fixtures" / "luat-quan-ly-thue-excerpt.txt"
COLLECTION = "legal_review_test"


def _doc(slug: str) -> CorpusDoc:
    return CorpusDoc(
        slug=slug, number="1/2026", title="Luật thử", doc_type="luat", field="tax",
        file="raw/x.docx", sha256="0" * 64, source_url="https://example.test",
    )  # fmt: skip


def _chunks(doc: CorpusDoc, _chunk_set: str):
    return article_chunks(doc, parse(EXCERPT.read_text(encoding="utf-8")))


def test_replayed_assistant_text_loses_its_numbered_markers():
    assert strip_markers("Theo luật [1], mức phạt là 8% [2][3]. Kết thúc [12].") == (
        "Theo luật, mức phạt là 8%. Kết thúc."
    )
    assert strip_markers("Không có nguồn") == "Không có nguồn"


def test_full_ingest_purges_documents_removed_from_the_manifest(qdrant_memory: QdrantClient):
    ensure_collection(qdrant_memory, COLLECTION, 16)
    both = [_doc("kept"), _doc("removed")]
    ingest_corpus(qdrant_memory, COLLECTION, FakeEmbedder(), both, "article", 8, chunks_for=_chunks)
    assert qdrant_memory.count(COLLECTION, exact=True).count == 8

    ingest_corpus(
        qdrant_memory, COLLECTION, FakeEmbedder(), both[:1], "article", 8,
        chunks_for=_chunks, purge_unknown=True,
    )  # fmt: skip

    slugs = {p.payload["doc_slug"] for p in qdrant_memory.scroll(COLLECTION, limit=20)[0]}
    assert slugs == {"kept"}


def test_partial_ingest_without_purge_keeps_other_documents(qdrant_memory: QdrantClient):
    ensure_collection(qdrant_memory, COLLECTION, 16)
    ingest_corpus(
        qdrant_memory, COLLECTION, FakeEmbedder(), [_doc("a"), _doc("b")], "article", 8,
        chunks_for=_chunks,
    )  # fmt: skip

    ingest_corpus(
        qdrant_memory, COLLECTION, FakeEmbedder(), [_doc("a")], "article", 8, chunks_for=_chunks
    )

    assert qdrant_memory.count(COLLECTION, exact=True).count == 8


def test_switched_off_document_is_purged_even_in_a_full_run(qdrant_memory: QdrantClient):
    ensure_collection(qdrant_memory, COLLECTION, 16)
    live = _doc("a")
    ingest_corpus(
        qdrant_memory, COLLECTION, FakeEmbedder(), [live], "article", 8, chunks_for=_chunks
    )

    ingest_corpus(
        qdrant_memory, COLLECTION, FakeEmbedder(), [replace(live, ingest=False)], "article", 8,
        chunks_for=_chunks, purge_unknown=True,
    )  # fmt: skip

    assert qdrant_memory.count(COLLECTION, exact=True).count == 0


def test_misconfigured_rag_degrades_to_no_sources_instead_of_failing_chat(monkeypatch):
    monkeypatch.setattr(get_settings(), "rag_enabled", True)

    def broken():
        raise RuntimeError("OPENAI_API_KEY is required")

    monkeypatch.setattr("app.services.rag.qdrant_retriever.get_qdrant_retriever", broken)

    assert isinstance(chat_retriever.get_retriever(), chat_retriever.NullRetriever)


def test_reference_check_is_case_insensitive_and_unicode_form_independent():
    nfd_answer = "theo điều 77 của luật".encode().decode()
    import unicodedata

    report = check_references(unicodedata.normalize("NFD", nfd_answer), set(), {5})

    assert report.unsupported_articles == [77]
