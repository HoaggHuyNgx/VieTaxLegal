import asyncio
from collections.abc import AsyncIterator, Sequence
from dataclasses import asdict
from pathlib import Path

import pytest
from qdrant_client import AsyncQdrantClient, models

from app.core.config import get_settings
from app.services.chat.provider import ProviderError, ProviderEvent, ProviderMessage
from app.services.rag.index.embeddings import FakeEmbedder, embedding_text
from app.services.rag.index.qdrant_store import DENSE_VECTOR
from app.services.rag.ingest.chunking import ChunkDraft
from app.services.rag.retrieve.qdrant_retriever import QdrantRetriever, SearchOutcome
from rag_eval.dataset import GoldRef, Question
from rag_eval.generation_tier import run_generation_tier
from rag_eval.provenance import run_metadata
from rag_eval.runner import (
    EvalConfig,
    build_retriever,
    result_filename,
    run_retrieval_tier,
    select_questions,
    threshold_sweep,
)

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
        return await run_retrieval_tier(EvalConfig("t"), await _retriever(), questions)

    summary, rows = asyncio.run(run())

    assert summary["in_corpus_questions"] == 2 and summary["out_of_corpus_questions"] == 1
    assert rows[0]["rank"] == 1
    assert rows[1]["rank"] in (2, 3)
    assert summary["hit@1"] == 0.5 and summary["hit@5"] == 1.0
    assert 0.5 < summary["mrr"] <= 1.0
    assert summary["embed_ms"]["p50"] is not None
    assert len(summary["threshold_sweep"]) > 5


def test_retrieval_tier_searches_exactly_as_the_app_does():
    """A deeper `limit` would also widen the hybrid and rerank candidate pools."""
    limits = []

    class Recording:
        async def search(self, query: str, limit: int | None = None) -> SearchOutcome:
            limits.append(limit)
            return SearchOutcome()

    summary, _ = asyncio.run(
        run_retrieval_tier(EvalConfig("t"), Recording(), [_question("q", "câu hỏi")])
    )

    assert limits == [None]
    assert summary["retrieval_ms"]["p50"] is not None  # whole call, planner included


def test_threshold_sweep_trades_answerable_kept_against_out_of_corpus_rejected():
    rows = {r["threshold"]: r for r in threshold_sweep([0.7, 0.6, 0.4], [0.5, 0.3])}

    assert rows[0.0] == {"threshold": 0.0, "answerable_kept": 1.0, "out_of_corpus_rejected": 0.0}
    assert rows[0.55]["answerable_kept"] == pytest.approx(2 / 3)
    assert rows[0.55]["out_of_corpus_rejected"] == 1.0
    assert threshold_sweep([], [])[0]["answerable_kept"] is None


def test_generation_tier_scores_citations_and_unsupported_references():
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
    assert by_id["good"]["unsupported_reference"] is False
    assert by_id["invented"]["unsupported_reference"] is True
    assert by_id["invented"]["unsupported"]["articles"] == [99]
    assert by_id["invented"]["unknown_docs"] == ["7/2030/NĐ-CP"]
    assert by_id["good"]["unknown_docs"] == []
    # Left blank for a person: no phrase match can tell a refusal from a full answer.
    assert by_id["ooc"]["refused"] is None and by_id["ooc"]["n_cited"] == 0
    assert by_id["down"] == {"id": "down", "type": "lookup", "error": "ProviderError"}
    assert summary["provider_errors"] == 1 and summary["answered"] == 3
    assert summary["unsupported_reference_rate"] == pytest.approx(1 / 3)
    assert summary["unknown_doc_rate"] == pytest.approx(1 / 3)
    assert summary["input_tokens"] == 30
    # Enough to check the references again without calling the model.
    assert by_id["good"]["retrieved"][0]["doc_number"] == "45/2019/QH14"
    assert by_id["good"]["retrieved"][0]["id"] and by_id["good"]["retrieved"][0]["article_nos"]
    assert by_id["good"]["end_to_end_ms"] == pytest.approx(
        by_id["good"]["retrieval_ms"] + by_id["good"]["total_ms"]
    )


def test_no_rag_run_has_no_support_rate_only_the_unknown_document_rate():
    """With no sources every reference would count as unsupported, which measures nothing."""
    question = _question("q", "câu hỏi", article=2)
    answer = "Theo Điều 25 Bộ luật Lao động 45/2019/QH14 và Nghị định 7/2030/NĐ-CP."

    async def run():
        config = EvalConfig("norag", tier="generation", rag=False)
        provider = FakeProvider({"câu hỏi": answer})
        return await run_generation_tier(config, await _retriever(), provider, [question], 100)

    summary, rows = asyncio.run(run())

    assert rows[0]["n_cited"] == 0 and rows[0]["unsupported_reference"] is None
    assert rows[0]["references"]["articles"] == [25]
    assert rows[0]["unknown_docs"] == ["7/2030/NĐ-CP"]
    assert summary["citation_recall"] == 0.0
    assert summary["unsupported_reference_rate"] is None
    assert summary["unknown_doc_rate"] == 1.0


def test_generation_tier_counts_cut_off_answers_and_times_the_whole_retrieval():
    class SlowPlanned:
        async def search(self, query: str, limit: int | None = None) -> SearchOutcome:
            await asyncio.sleep(0.05)  # planner time is in neither embed_ms nor search_ms
            return SearchOutcome(embed_ms=1.0, search_ms=1.0, plan_info={"plan_ms": 40.0})

    class Capped(FakeProvider):
        async def stream(self, messages, system_prompt, max_output_tokens):
            yield ProviderEvent(kind="delta", text="Một phần")
            yield ProviderEvent(kind="done", truncated=True)

    async def run():
        config = EvalConfig("t", tier="generation")
        questions = [_question("q", "câu hỏi")]
        return await run_generation_tier(config, SlowPlanned(), Capped({}), questions, 100)

    summary, rows = asyncio.run(run())

    assert rows[0]["truncated"] is True and summary["truncated_answers"] == 1
    assert rows[0]["retrieval_ms"] >= 40 and rows[0]["plan_ms"] == 40.0
    assert summary["end_to_end_ms"]["p50"] >= rows[0]["retrieval_ms"]


def test_result_metadata_pins_code_questions_and_corpus_text():
    questions = [_question("q", "câu hỏi")]
    changed = [_question("q", "câu hỏi", article=3)]
    config, settings = EvalConfig("t"), get_settings()

    meta = run_metadata(config, settings, questions, 1, "legal_x")

    assert meta["collection"] == "legal_x"
    assert meta["git_dirty"] in (True, False, None)
    assert len(meta["corpus_texts_sha"]) == 12
    assert meta["questions_sha"] != run_metadata(config, settings, changed, 1)["questions_sha"]


def test_holdout_questions_are_scored_only_when_asked_for():
    def question(qid: str, split: str) -> Question:
        return Question(
            qid, "q?", "tax", "lookup", "a", [GoldRef("x", 1)], status="approved", split=split
        )

    questions = [question("d", "dev"), question("h", "holdout")]

    # A run over "everything" while tuning must not see them either.
    assert [q.id for q in select_questions(questions, EvalConfig("t"))] == ["d"]
    assert [q.id for q in select_questions(questions, EvalConfig("t", split="holdout"))] == ["h"]


def test_a_split_config_scores_only_that_split_and_names_its_result_file():
    questions = [
        Question(
            "d", "q?", "tax", "lookup", "a", [GoldRef("x", 1)], status="approved", split="dev"
        ),
        Question(
            "t", "q?", "tax", "lookup", "a", [GoldRef("x", 1)], status="approved", split="test"
        ),
    ]
    config = EvalConfig("hybrid", split="test")

    assert [q.id for q in select_questions(questions, config)] == ["t"]
    assert result_filename(config, "2026-11-26", provisional=False) == (
        "2026-11-26-hybrid-retrieval-test.json"
    )
    assert result_filename(EvalConfig("hybrid"), "2026-11-26", provisional=True) == (
        "2026-11-26-hybrid-retrieval-provisional.json"
    )


def test_rrf_sensitivity_configs_differ_from_hybrid_article_only_in_rrf_k():
    configs = Path(__file__).resolve().parents[2] / "rag_eval" / "configs" / "retrieval"
    base = asdict(EvalConfig.load(configs / "hybrid-article.json"))
    assert base["rrf_k"] == 60

    for k in (20, 40, 100):
        variant = asdict(EvalConfig.load(configs / f"hybrid-article-rrfk{k}.json"))
        assert variant["rrf_k"] == k
        assert {**variant, "name": base["name"], "rrf_k": 60} == base


@pytest.mark.parametrize(
    ("update", "message"),
    [({"rerank": "llm"}, "only 'cohere'"), ({"rerank": "cohere"}, "needs rerank_model")],
)
def test_build_retriever_rejects_an_unusable_rerank_config(update, message):
    config = EvalConfig("t", embedding_provider="fake", **update)

    with pytest.raises(ValueError, match=message):
        build_retriever(config, get_settings())
