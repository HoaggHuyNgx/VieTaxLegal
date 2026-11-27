import asyncio
import json

import httpx
import pytest
from pydantic import SecretStr

from app.services.rag.retrieve.qdrant_retriever import Hit
from app.services.rag.retrieve.reranker import COHERE_RERANK_URL, CohereReranker, NoopReranker

HITS = [
    Hit(str(n), 1.0, {"heading_path": f"Điều {n}", "content": f"nội dung {n}"}) for n in (1, 2, 3)
]
KEY = SecretStr("test-key")


def _transport(indexes=None, status=200, body=None):
    """A fake Cohere API: records each request and answers with the given result order."""
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = body if body is not None else {"results": [{"index": n} for n in indexes]}
        return httpx.Response(status, json=payload)

    return httpx.MockTransport(handler), requests


def _ids(hits):
    return [h.id for h in hits]


def test_noop_reranker_keeps_order_and_limits():
    assert _ids(asyncio.run(NoopReranker().rerank("q", HITS, 2))) == ["1", "2"]


def test_cohere_reranker_applies_the_api_order_and_sends_the_candidates():
    transport, requests = _transport([2, 0, 1])
    reranker = CohereReranker(KEY, "rerank-test", transport)

    ranked = asyncio.run(reranker.rerank("câu hỏi", HITS, 2))

    assert _ids(ranked) == ["3", "1"]
    sent = json.loads(requests[0].content)
    assert str(requests[0].url) == COHERE_RERANK_URL
    assert requests[0].headers["Authorization"] == "Bearer test-key"
    assert sent["model"] == "rerank-test" and sent["query"] == "câu hỏi" and sent["top_n"] == 2
    assert sent["documents"][2] == "Điều 3\nnội dung 3"
    assert reranker.fallbacks == 0


def test_cohere_reranker_keeps_unranked_candidates_and_ignores_bad_indexes():
    transport, _ = _transport([1, 9, 1])

    ranked = asyncio.run(CohereReranker(KEY, "m", transport).rerank("q", HITS, 3))

    assert _ids(ranked) == ["2", "1", "3"]


@pytest.mark.parametrize(
    ("status", "body"),
    [(429, {"message": "rate limited"}), (500, {}), (200, {"unexpected": True})],
)
def test_cohere_reranker_falls_back_to_original_order_on_errors(status, body):
    transport, _ = _transport(status=status, body=body)
    reranker = CohereReranker(KEY, "m", transport)

    assert _ids(asyncio.run(reranker.rerank("q", HITS, 2))) == ["1", "2"]
    assert reranker.fallbacks == 1


def test_cohere_reranker_skips_the_call_without_candidates():
    transport, requests = _transport([])

    assert asyncio.run(CohereReranker(KEY, "m", transport).rerank("q", [], 5)) == []
    assert requests == []


@pytest.mark.parametrize("key", [None, SecretStr("  ")])
def test_cohere_reranker_needs_an_api_key(key):
    with pytest.raises(ValueError, match="COHERE_API_KEY"):
        CohereReranker(key, "m")
