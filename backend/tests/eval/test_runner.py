import asyncio
from collections.abc import AsyncIterator, Sequence

import pytest
from qdrant_client import AsyncQdrantClient, models

from app.services.chat_provider import ProviderError, ProviderEvent, ProviderMessage
from app.services.rag.chunking import ChunkDraft
from app.services.rag.embeddings import FakeEmbedder, embedding_text
from app.services.rag.qdrant_retriever import QdrantRetriever
from app.services.rag.qdrant_store import DENSE_VECTOR
from rag_eval.dataset import GoldRef, Question
from rag_eval.generation_tier import run_generation_tier
from rag_eval.runner import EvalConfig, run_retrieval_tier, threshold_sweep

COLLECTION = "legal_eval_test"


def _chunk(article: int, content: str, slug: str = "luat-a") -> ChunkDraft:
    return ChunkDraft(
        doc_slug=slug, doc_number="45/2019/QH14", doc_title="Bộ luật Lao động", doc_type="luat",
        field="labor", status="in_force", issued_on=None, effective_from=None, effective_to=None,
        source_url="https://example.test", chunk_set="article", ordinal=article,
        article_no=article, article_nos=(article,), clause_no=None, point=None,
        locator=f"Điều {article}", heading_path=f"Bộ luật Lao động > Điều {article}",
        content=content, content_sha256="x", char_start=0, char_end=len(content),
    )  # fmt: skip


CHUNKS = [_chunk(n, f"Nội dung điều {n}") for n in (1, 2, 3)]


async def _retriever(top_k: int = 3) -> QdrantRetriever:
    embedder = FakeEmbedder()
    client = AsyncQdrantClient(":memory:")
    config = models.VectorParams(size=16, distance=models.Distance.COSINE)
    await client.create_collection(COLLECTION, vectors_config={DENSE_VECTOR: config})
    vectors = embedder.embed_documents([embedding_text(c) for c in CHUNKS]).vectors
    await client.upsert(
        COLLECTION,
        [
            models.PointStruct(id=c.id, vector={DENSE_VECTOR: v}, payload=c.to_payload())
            for c, v in zip(CHUNKS, vectors)
        ],
    )
    return QdrantRetriever(client, embedder, COLLECTION, top_k, require_in_force=True)


def _question(qid: str, text: str, article: int | None = 2, kind: str = "lookup") -> Question:
    refs = [GoldRef("luat-a", article)] if article else []
    return Question(qid, text, "labor", kind, "đáp án", refs, status="approved")


class FakeProvider:
    name, model = "fake", "fake-model"

    def __init__(self, answers: dict[str, str]) -> None:
        self.answers = answers

    async def stream(
        self, messages: Sequence[ProviderMessage], system_prompt: str, max_output_tokens: int
    ) -> AsyncIterator[ProviderEvent]:
        answer = self.answers[messages[-1].content]
        if answer == "FAIL":
            raise ProviderError("boom")
        yield ProviderEvent(kind="delta", text=answer)
        yield ProviderEvent(kind="done", input_tokens=10, output_tokens=5)


def test_retrieval_tier_scores_rank_recall_and_mrr():
    questions = [
        _question("hit", embedding_text(CHUNKS[1]), article=2),  # exact text -> rank 1
        _question("miss", embedding_text(CHUNKS[0]), article=3),  # gold is a different article
        _question("ooc", "ngoài phạm vi", article=None, kind="out_of_corpus"),
    ]

    async def run():
        return await run_retrieval_tier(EvalConfig("t", depth=3), await _retriever(), questions)

    summary, rows = asyncio.run(run())

    assert summary["in_corpus_questions"] == 2 and summary["out_of_corpus_questions"] == 1
    assert rows[0]["rank"] == 1
    assert rows[1]["rank"] in (2, 3)
    assert summary["recall@1"] == 0.5 and summary["recall@5"] == 1.0
    assert 0.5 < summary["mrr"] <= 1.0
    assert summary["embed_ms"]["p50"] is not None
    assert len(summary["threshold_sweep"]) > 5


def test_threshold_sweep_trades_answerable_kept_against_out_of_corpus_rejected():
    rows = {r["threshold"]: r for r in threshold_sweep([0.7, 0.6, 0.4], [0.5, 0.3])}

    assert rows[0.0] == {"threshold": 0.0, "answerable_kept": 1.0, "out_of_corpus_rejected": 0.0}
    assert rows[0.55]["answerable_kept"] == pytest.approx(2 / 3)
    assert rows[0.55]["out_of_corpus_rejected"] == 1.0
    assert threshold_sweep([], [])[0]["answerable_kept"] is None


def test_generation_tier_scores_citations_hallucination_and_abstention():
    exact = embedding_text(CHUNKS[1])
    questions = [
        _question("good", exact, article=2),
        _question("invented", embedding_text(CHUNKS[2]), article=3),
        _question("ooc", "ngoài phạm vi", article=None, kind="out_of_corpus"),
        _question("down", embedding_text(CHUNKS[0]), article=1),
    ]
    provider = FakeProvider(
        {
            exact: "Căn cứ Điều 2 Bộ luật Lao động 45/2019/QH14 [1].",
            embedding_text(CHUNKS[2]): "Theo Điều 99 và nghị định 7/2030/NĐ-CP [1].",
            "ngoài phạm vi": "Tôi chưa thể xác minh nội dung này.",
            embedding_text(CHUNKS[0]): "FAIL",
        }
    )

    async def run():
        retriever = await _retriever()
        config = EvalConfig("t", tier="generation")
        return await run_generation_tier(config, retriever, provider, questions, 100)

    summary, rows = asyncio.run(run())
    by_id = {r["id"]: r for r in rows}

    assert by_id["good"]["citation_precision"] == 1.0 and by_id["good"]["citation_recall"] == 1.0
    assert by_id["good"]["hallucinated_reference"] is False
    assert by_id["invented"]["hallucinated_reference"] is True
    assert by_id["invented"]["unsupported"]["articles"] == [99]
    assert by_id["ooc"]["abstained"] is True and by_id["ooc"]["n_cited"] == 0
    assert by_id["down"] == {"id": "down", "type": "lookup", "error": "provider"}
    assert summary["provider_errors"] == 1 and summary["answered"] == 3
    assert summary["ooc_abstain_phrase_rate"] == 1.0
    assert summary["hallucinated_reference_rate"] == pytest.approx(1 / 3)
    assert summary["input_tokens"] == 30


def test_no_rag_baseline_has_no_sources_so_any_reference_is_unsupported():
    question = _question("q", "câu hỏi", article=2)
    provider = FakeProvider({"câu hỏi": "Theo Điều 25 Bộ luật Lao động 45/2019/QH14."})

    async def run():
        config = EvalConfig("norag", tier="generation", rag=False)
        return await run_generation_tier(config, await _retriever(), provider, [question], 100)

    summary, rows = asyncio.run(run())

    assert rows[0]["n_cited"] == 0 and rows[0]["hallucinated_reference"] is True
    assert summary["citation_recall"] == 0.0
    assert summary["hallucinated_reference_rate"] == 1.0
