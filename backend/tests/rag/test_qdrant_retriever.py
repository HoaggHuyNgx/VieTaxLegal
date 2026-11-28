import asyncio
import logging
from dataclasses import replace

from qdrant_client import AsyncQdrantClient, models

from app.core.config import get_settings
from app.services.chat.prompt import NO_SOURCE_RULES, SYSTEM_PROMPT, prompt_with_context
from app.services.chat.retriever import NullRetriever, get_retriever
from app.services.rag.index.embeddings import FakeEmbedder, embedding_text
from app.services.rag.index.qdrant_store import DENSE_VECTOR
from app.services.rag.ingest.chunking import ChunkDraft
from app.services.rag.retrieve.qdrant_retriever import Hit, QdrantRetriever, hits_to_result

COLLECTION = "legal_test"


def _chunk(ordinal: int, content: str, status: str | None = "in_force") -> ChunkDraft:
    return ChunkDraft(
        doc_slug="doc", doc_number="108/2025/QH15", doc_title="Luật Quản lý thuế",
        doc_type="luat", field="tax", status=status, issued_on="2025-12-10",
        effective_from=None, effective_to=None, source_url="https://example.test/108",
        chunk_set="article", ordinal=ordinal, article_no=ordinal, article_nos=(ordinal,),
        clause_no=None, point=None, locator=f"Điều {ordinal}",
        heading_path=f"Luật Quản lý thuế > Điều {ordinal}", content=content,
        content_sha256="x", char_start=0, char_end=len(content),
    )  # fmt: skip


async def _retriever(chunks, **kwargs) -> QdrantRetriever:
    embedder = FakeEmbedder()
    client = AsyncQdrantClient(":memory:")
    await client.create_collection(
        COLLECTION,
        vectors_config={
            DENSE_VECTOR: models.VectorParams(size=16, distance=models.Distance.COSINE)
        },
    )
    vectors = embedder.embed_documents([embedding_text(c) for c in chunks]).vectors
    await client.upsert(
        COLLECTION,
        [
            models.PointStruct(id=c.id, vector={DENSE_VECTOR: v}, payload=c.to_payload())
            for c, v in zip(chunks, vectors)
        ],
    )
    return QdrantRetriever(client, embedder, COLLECTION, top_k=3, **kwargs)


def _query_for(chunk: ChunkDraft) -> str:
    return embedding_text(chunk)  # identical text -> identical fake vector -> top hit


def test_best_match_ranks_first_and_maps_to_numbered_sources():
    chunks = [_chunk(i, f"Nội dung điều {i}") for i in range(1, 5)]

    async def run():
        retriever = await _retriever(chunks)
        return await retriever.retrieve(_query_for(chunks[2]))

    result = asyncio.run(run())

    assert len(result.citations) == 3
    first = result.citations[0]
    assert (first.id, first.locator, first.doc_number) == ("1", "Điều 3", "108/2025/QH15")
    assert first.title == "Luật Quản lý thuế" and first.url == "https://example.test/108"
    assert first.issued_on == "2025-12-10"
    assert result.contexts[0].citation_id == "1"
    assert result.contexts[0].content.startswith("Luật Quản lý thuế > Điều 3\nNội dung điều 3")


def test_documents_not_in_force_are_never_returned():
    chunks = [_chunk(1, "hết hiệu lực", status="expired"), _chunk(2, "chưa kiểm", status=None)]

    async def run():
        retriever = await _retriever(chunks)
        return await retriever.retrieve(_query_for(chunks[0]))

    assert not asyncio.run(run()).citations


def test_in_force_filter_can_be_switched_off_for_development():
    chunks = [_chunk(1, "chưa kiểm", status=None)]

    async def run():
        retriever = await _retriever(chunks, require_in_force=False)
        return await retriever.retrieve(_query_for(chunks[0]))

    assert len(asyncio.run(run()).citations) == 1


def test_similarity_threshold_drops_weak_hits():
    chunks = [_chunk(1, "một"), _chunk(2, "hai")]

    async def run():
        retriever = await _retriever(chunks, min_similarity=0.999)
        return await retriever.retrieve(_query_for(chunks[0]))

    assert [c.locator for c in asyncio.run(run()).citations] == ["Điều 1"]


def test_search_reports_stage_timings():
    chunks = [_chunk(1, "một")]

    async def run():
        retriever = await _retriever(chunks)
        return await retriever.search(_query_for(chunks[0]))

    outcome = asyncio.run(run())

    assert outcome.hits[0].payload["locator"] == "Điều 1"
    assert outcome.embed_ms >= 0 and outcome.search_ms >= 0


def test_outage_returns_empty_result_and_logs_no_query_text(caplog):
    secret_query = "truy vấn bí mật về thuế"

    async def run():
        client = AsyncQdrantClient(":memory:")  # collection never created -> error
        retriever = QdrantRetriever(client, FakeEmbedder(), COLLECTION, top_k=3)
        return await retriever.retrieve(secret_query)

    with caplog.at_level(logging.WARNING):
        result = asyncio.run(run())

    assert not result.contexts and not result.citations
    assert NO_SOURCE_RULES in prompt_with_context(result)  # not answered from memory
    assert "RAG retrieval failed" in caplog.text
    assert secret_query not in caplog.text


def test_hits_to_result_handles_empty_and_sparse_payloads():
    assert not hits_to_result([]).citations
    result = hits_to_result([Hit("1", 0.5, {})])
    assert result.citations[0].title == "" and result.citations[0].locator is None


def test_factory_returns_null_retriever_when_rag_disabled():
    retriever = get_retriever()

    assert isinstance(retriever, NullRetriever)
    # RAG off was never meant to search, so the plain prompt stays.
    assert prompt_with_context(asyncio.run(retriever.retrieve("q"))) == SYSTEM_PROMPT


def test_misconfigured_rag_degrades_to_no_sources_instead_of_failing_chat(monkeypatch):
    monkeypatch.setattr(get_settings(), "rag_enabled", True)

    def broken():
        raise RuntimeError("OPENAI_API_KEY is required")

    monkeypatch.setattr("app.services.rag.retrieve.qdrant_retriever.get_qdrant_retriever", broken)

    retriever = get_retriever()

    assert isinstance(retriever, NullRetriever)
    assert NO_SOURCE_RULES in prompt_with_context(asyncio.run(retriever.retrieve("q")))


def _part(ordinal: int, article: int, clause: int | None, start: int, label: str = ""):
    locator = f"Điều {label or article}" + (f" khoản {clause}" if clause else "")
    return replace(
        _chunk(ordinal, f"phần {ordinal}"), article_no=article, article_nos=(article,),
        clause_no=clause, locator=locator, char_start=start, char_end=start + 10,
    )  # fmt: skip


def test_expand_articles_returns_whole_articles_once_each():
    """Small-to-big: a Khoan chunk becomes its whole Dieu; a second chunk of it is dropped."""
    intro, k1, k2 = _part(1, 5, None, 0), _part(2, 5, 1, 20), _part(3, 5, 2, 40)
    whole, other = _part(4, 6, None, 60), _part(5, 5, None, 80, label="5a")  # 5a: own Dieu
    chunks = [intro, k1, k2, whole, other]
    hits = [Hit(c.id, 1.0, c.to_payload()) for c in (k2, whole, k1, other)]

    async def run():
        retriever = await _retriever(chunks)
        return await retriever.expand_articles(hits, limit=5)

    expanded = asyncio.run(run())

    assert [h.payload["locator"] for h in expanded] == ["Điều 5", "Điều 6", "Điều 5a"]
    assert expanded[0].payload["content"] == "phần 1\nphần 2\nphần 3"
    assert expanded[0].payload["clause_no"] is None and expanded[0].id == k2.id
    assert expanded[1].payload == whole.to_payload()


def test_expand_keeps_the_khoan_when_the_whole_article_is_too_long(monkeypatch):
    chunks = [_part(1, 5, 1, 0), _part(2, 5, 2, 20)]
    monkeypatch.setattr("app.services.rag.retrieve.qdrant_retriever.EXPAND_MAX_TOKENS", 1)

    async def run():
        retriever = await _retriever(chunks)
        return await retriever.expand_articles([Hit(chunks[1].id, 1.0, chunks[1].to_payload())], 5)

    assert asyncio.run(run())[0].payload == chunks[1].to_payload()


def test_expand_stops_at_the_limit():
    chunks = [_part(i, i, None, i * 10) for i in range(1, 5)]

    async def run():
        retriever = await _retriever(chunks)
        return await retriever.expand_articles([Hit(c.id, 1.0, c.to_payload()) for c in chunks], 2)

    assert len(asyncio.run(run())) == 2
