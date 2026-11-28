import asyncio
import json

import pytest
from pydantic import SecretStr

from app.core.config import get_settings
from app.services.chat.provider import ProviderError, ProviderEvent
from app.services.rag.retrieve import query_planner
from app.services.rag.retrieve.qdrant_retriever import Hit, SearchOutcome
from app.services.rag.retrieve.query_planner import (
    QueryPlan,
    QueryPlanner,
    RetrievalPipeline,
    build_pipeline,
)

QUESTION = "Thuế GTGT và thuế TNCN của hộ kinh doanh tính thế nào?"


class _Provider:
    name, model = "fake", "fake"

    def __init__(self, reply: str = "", fail: bool = False, delay: float = 0.0) -> None:
        self.reply, self.fail, self.delay = reply, fail, delay

    async def stream(self, messages, system_prompt, max_output_tokens):
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail:
            raise ProviderError("down")
        yield ProviderEvent(kind="delta", text=self.reply)


def _plan(reply: str, question: str = QUESTION) -> QueryPlan:
    return asyncio.run(QueryPlanner(_Provider(reply)).plan(question))


def _reply(route: str = "law", queries: list[str] | None = None) -> str:
    return json.dumps({"route": route, "queries": queries or []}, ensure_ascii=False)


def test_plan_keeps_the_original_first_and_caps_the_rewrites():
    plan = _plan(_reply(queries=["thuế GTGT hộ kinh doanh", "thuế TNCN hộ kinh doanh", "thừa"]))

    assert plan == QueryPlan(
        "law", (QUESTION, "thuế GTGT hộ kinh doanh", "thuế TNCN hộ kinh doanh")
    )


def test_plan_reads_json_wrapped_in_prose():
    assert _plan("Đây: " + _reply(queries=["thuế GTGT"]) + " xong").queries[1] == "thuế GTGT"


def test_plan_drops_rewrites_with_numbers_the_user_did_not_write():
    plan = _plan(_reply(queries=["Điều 5 Luật Thuế GTGT", "thuế GTGT hộ kinh doanh"]))

    assert plan.queries == (QUESTION, "thuế GTGT hộ kinh doanh")


def test_plan_keeps_numbers_the_user_wrote():
    question = "Điều 5 Luật Thuế quy định gì?"

    assert _plan(_reply(queries=["nội dung Điều 5 Luật Thuế"]), question).queries == (
        question,
        "nội dung Điều 5 Luật Thuế",
    )


def test_plan_drops_a_rewrite_identical_to_the_question():
    assert _plan(_reply(queries=[QUESTION.upper()])).queries == (QUESTION,)


@pytest.mark.parametrize(("route", "expected"), [("invalid", "invalid"), ("other", "law")])
def test_only_an_explicit_invalid_route_counts(route, expected):
    assert _plan(_reply(route=route)).route == expected


@pytest.mark.parametrize(
    "provider",
    [_Provider("không phải JSON"), _Provider('["danh sách"]'), _Provider(fail=True)],
)
def test_planner_failure_falls_back_to_the_original_question(provider):
    plan = asyncio.run(QueryPlanner(provider).plan(QUESTION))

    assert plan == QueryPlan("law", (QUESTION,), fallback=True)


def test_planner_timeout_falls_back(monkeypatch):
    monkeypatch.setattr(query_planner, "PLANNER_TIMEOUT_SECONDS", 0.01)

    plan = asyncio.run(QueryPlanner(_Provider(_reply(), delay=1.0)).plan(QUESTION))

    assert plan.fallback is True


class _Inner:
    def __init__(self, ranking: dict[str, list[str]], fail: bool = False) -> None:
        self.ranking, self.fail, self.calls = ranking, fail, []
        self.top_dense: dict[str, float] = {}

    async def search(self, query, limit=None):
        self.calls.append((query, limit))
        if self.fail:
            raise RuntimeError("qdrant down")
        hits = [Hit(i, 1.0, {"doc_slug": "luat", "id": i}) for i in self.ranking[query]]
        return SearchOutcome(hits[:limit], 3.0, 4.0, top_dense=self.top_dense.get(query))


class _Planner:
    def __init__(self, plan: QueryPlan) -> None:
        self.result = plan

    async def plan(self, question):
        return self.result


def test_search_fuses_rankings_and_reports_the_plan():
    inner = _Inner({"a": ["1", "2"], "b": ["2", "3"]})
    retriever = RetrievalPipeline(inner, 5, _Planner(QueryPlan("law", ("a", "b"))))

    outcome = asyncio.run(retriever.search("a", limit=3))

    assert [hit.id for hit in outcome.hits] == ["2", "1", "3"]  # "2" is in both rankings
    assert outcome.hits[0].payload == {"doc_slug": "luat", "id": "2"}
    assert inner.calls == [("a", 3), ("b", 3)]
    assert outcome.plan_info["route"] == "law" and outcome.plan_info["queries"] == ["a", "b"]
    assert (outcome.embed_ms, outcome.search_ms) == (3.0, 4.0)


def test_search_cuts_the_fused_list_to_the_limit():
    inner = _Inner({"a": ["1", "2"], "b": ["3", "4"]})
    retriever = RetrievalPipeline(inner, 2, _Planner(QueryPlan("law", ("a", "b"))))

    assert len(asyncio.run(retriever.search("a")).hits) == 2


def test_single_query_keeps_the_plain_ranking():
    inner = _Inner({"a": ["2", "1"]})
    retriever = RetrievalPipeline(inner, 5, _Planner(QueryPlan("law", ("a",))))

    outcome = asyncio.run(retriever.search("a"))

    assert [(hit.id, hit.score) for hit in outcome.hits] == [("2", 1.0), ("1", 1.0)]


def test_retrieve_degrades_to_no_sources():
    inner = _Inner({}, fail=True)
    retriever = RetrievalPipeline(inner, 5, _Planner(QueryPlan("law", ("a",))))

    result = asyncio.run(retriever.retrieve("a"))

    assert not result.contexts and not result.citations
    assert result.searched  # RAG is on, so the model must be told there are no sources


def test_planner_is_off_without_a_model():
    inner = object()

    assert build_pipeline(inner, get_settings()) is inner


def test_planner_wraps_when_a_model_is_set():
    settings = get_settings().model_copy(update={"rag_query_planner_model": "small-model"})

    assert isinstance(build_pipeline(object(), settings), RetrievalPipeline)


class _Reranker:
    def __init__(self, order: list[str] | None = None, delay: float = 0.0) -> None:
        self.order, self.delay, self.fallbacks, self.queries = order, delay, 0, []

    async def rerank(self, query, hits, limit):
        self.queries.append(query)
        await asyncio.sleep(self.delay)
        by_id = {hit.id: hit for hit in hits}
        return [by_id[i] for i in self.order][:limit]


def test_rerank_runs_once_on_the_original_question_with_spare_candidates():
    inner = _Inner({"a": ["1", "2", "3"], "b": ["3", "4"]})
    reranker = _Reranker(order=["4", "1", "3"])
    retriever = RetrievalPipeline(inner, 2, _Planner(QueryPlan("law", ("a", "b"))), reranker)

    outcome = asyncio.run(retriever.search("a"))

    assert [hit.id for hit in outcome.hits] == ["4", "1"]
    assert reranker.queries == ["a"]
    assert inner.calls == [("a", 10), ("b", 10)]


def test_rerank_timeout_keeps_the_fused_order_and_is_counted(monkeypatch):
    monkeypatch.setattr(query_planner, "RERANK_TIMEOUT_SECONDS", 0.01)
    inner = _Inner({"a": ["1", "2", "3"]})
    retriever = RetrievalPipeline(inner, 2, reranker=_Reranker(order=["3"], delay=1.0))

    outcome = asyncio.run(retriever.search("a"))

    assert [hit.id for hit in outcome.hits] == ["1", "2"]
    assert retriever.index_info == {"rerank_fallbacks": 1}


def test_gate_returns_no_sources_and_skips_the_reranker():
    inner = _Inner({"a": ["1"]})
    inner.top_dense = {"a": 0.4}
    reranker = _Reranker(order=["1"])
    retriever = RetrievalPipeline(inner, 5, reranker=reranker, min_top_score=0.5)

    assert asyncio.run(retriever.search("a")).hits == []
    assert reranker.queries == []


def test_gate_uses_the_original_question_not_a_rewrite():
    inner = _Inner({"a": ["1"], "b": ["2"]})
    inner.top_dense = {"a": 0.4, "b": 0.9}
    planner = _Planner(QueryPlan("law", ("a", "b")))
    retriever = RetrievalPipeline(inner, 5, planner, min_top_score=0.5)

    assert asyncio.run(retriever.search("a")).hits == []


def test_gate_passes_at_the_threshold_and_when_no_dense_score_exists():
    inner = _Inner({"a": ["1"], "b": ["2"]})
    inner.top_dense = {"a": 0.5}
    retriever = RetrievalPipeline(inner, 5, min_top_score=0.5)

    assert len(asyncio.run(retriever.search("a")).hits) == 1
    assert len(asyncio.run(retriever.search("b")).hits) == 1  # sparse-only mode


def test_invalid_route_searches_nothing():
    inner = _Inner({})
    planner = _Planner(QueryPlan("invalid", ("nấu phở",)))
    retriever = RetrievalPipeline(inner, 5, planner)

    outcome = asyncio.run(retriever.search("nấu phở"))

    assert outcome.hits == [] and inner.calls == []
    assert outcome.plan_info["route"] == "invalid"


class _ExpandingInner(_Inner):
    def __init__(self, ranking):
        super().__init__(ranking)
        self.expanded = []

    async def expand_articles(self, hits, limit):
        self.expanded.append(([hit.id for hit in hits], limit))
        return hits[1:][:limit]  # pretend the first hit shared its Dieu with a later one


def test_expand_runs_after_rerank_on_spare_candidates():
    inner = _ExpandingInner({"a": ["1", "2", "3", "4"]})
    reranker = _Reranker(order=["4", "3", "2", "1"])
    retriever = RetrievalPipeline(inner, 2, reranker=reranker, expand=True)

    outcome = asyncio.run(retriever.search("a"))

    assert inner.calls == [("a", 10)]
    assert inner.expanded == [(["4", "3", "2", "1"], 2)]  # reranker kept every candidate
    assert [hit.id for hit in outcome.hits] == ["3", "2"]


def test_pipeline_is_built_for_rerank_or_gate_alone():
    base = get_settings()

    rerank = {"rag_rerank_model": "rerank-test", "cohere_api_key": SecretStr("test-key")}
    for update in (rerank, {"rag_min_top_score": 0.5}, {"rag_expand_articles": True}):
        built = build_pipeline(object(), base.model_copy(update=update))
        assert isinstance(built, RetrievalPipeline)


def test_rerank_without_cohere_key_refuses_to_build():
    settings = get_settings().model_copy(
        update={"rag_rerank_model": "rerank-test", "cohere_api_key": None}
    )

    with pytest.raises(ValueError, match="COHERE_API_KEY"):
        build_pipeline(object(), settings)
