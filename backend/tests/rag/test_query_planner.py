import asyncio
import json

import pytest

from app.core.config import get_settings
from app.services import rag
from app.services.chat_provider import ProviderError, ProviderEvent
from app.services.rag.qdrant_retriever import Hit, SearchOutcome
from app.services.rag.query_planner import (
    MultiQueryRetriever,
    QueryPlan,
    QueryPlanner,
    with_query_planner,
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
    monkeypatch.setattr(rag.query_planner, "PLANNER_TIMEOUT_SECONDS", 0.01)

    plan = asyncio.run(QueryPlanner(_Provider(_reply(), delay=1.0)).plan(QUESTION))

    assert plan.fallback is True


class _Inner:
    def __init__(self, ranking: dict[str, list[str]], fail: bool = False) -> None:
        self.ranking, self.fail, self.calls = ranking, fail, []

    async def search(self, query, limit=None):
        self.calls.append((query, limit))
        if self.fail:
            raise RuntimeError("qdrant down")
        hits = [Hit(i, 1.0, {"doc_slug": "luat", "id": i}) for i in self.ranking[query]]
        return SearchOutcome(hits[:limit], 3.0, 4.0)


class _Planner:
    def __init__(self, plan: QueryPlan) -> None:
        self.result = plan

    async def plan(self, question):
        return self.result


def test_search_fuses_rankings_and_reports_the_plan():
    inner = _Inner({"a": ["1", "2"], "b": ["2", "3"]})
    retriever = MultiQueryRetriever(inner, _Planner(QueryPlan("law", ("a", "b"))), top_k=5)

    outcome = asyncio.run(retriever.search("a", limit=3))

    assert [hit.id for hit in outcome.hits] == ["2", "1", "3"]  # "2" is in both rankings
    assert outcome.hits[0].payload == {"doc_slug": "luat", "id": "2"}
    assert inner.calls == [("a", 3), ("b", 3)]
    assert outcome.plan_info["route"] == "law" and outcome.plan_info["queries"] == ["a", "b"]
    assert (outcome.embed_ms, outcome.search_ms) == (3.0, 4.0)


def test_search_cuts_the_fused_list_to_the_limit():
    inner = _Inner({"a": ["1", "2"], "b": ["3", "4"]})
    retriever = MultiQueryRetriever(inner, _Planner(QueryPlan("law", ("a", "b"))), top_k=2)

    assert len(asyncio.run(retriever.search("a")).hits) == 2


def test_single_query_keeps_the_plain_ranking():
    inner = _Inner({"a": ["2", "1"]})
    retriever = MultiQueryRetriever(inner, _Planner(QueryPlan("law", ("a",))), top_k=5)

    outcome = asyncio.run(retriever.search("a"))

    assert [(hit.id, hit.score) for hit in outcome.hits] == [("2", 1.0), ("1", 1.0)]


def test_retrieve_degrades_to_no_sources():
    inner = _Inner({}, fail=True)
    retriever = MultiQueryRetriever(inner, _Planner(QueryPlan("law", ("a",))), top_k=5)

    result = asyncio.run(retriever.retrieve("a"))

    assert not result.contexts and not result.citations


def test_planner_is_off_without_a_model():
    inner = object()

    assert with_query_planner(inner, get_settings()) is inner


def test_planner_wraps_when_a_model_is_set():
    settings = get_settings().model_copy(update={"rag_query_planner_model": "small-model"})

    assert isinstance(with_query_planner(object(), settings), MultiQueryRetriever)
