import asyncio

from app.services.chat_provider import ProviderError, ProviderEvent
from app.services.rag.qdrant_retriever import Hit
from app.services.rag.reranker import LlmReranker, NoopReranker

HITS = [
    Hit(str(n), 1.0, {"heading_path": f"Điều {n}", "content": f"nội dung {n}"}) for n in (1, 2, 3)
]


class _Provider:
    name, model = "fake", "fake"

    def __init__(self, reply: str = "", fail: bool = False) -> None:
        self.reply, self.fail, self.prompt = reply, fail, ""

    async def stream(self, messages, system_prompt, max_output_tokens):
        self.prompt = messages[-1].content
        if self.fail:
            raise ProviderError("down")
        yield ProviderEvent(kind="delta", text=self.reply)


def _ids(hits):
    return [h.id for h in hits]


def test_noop_reranker_keeps_order_and_limits():
    assert _ids(asyncio.run(NoopReranker().rerank("q", HITS, 2))) == ["1", "2"]


def test_llm_reranker_applies_the_model_order_and_lists_candidates_in_the_prompt():
    provider = _Provider("Thứ tự: [3, 1, 2]")

    ranked = asyncio.run(LlmReranker(provider).rerank("câu hỏi", HITS, 2))

    assert _ids(ranked) == ["3", "1"]
    assert "Câu hỏi: câu hỏi" in provider.prompt and "[3] Điều 3" in provider.prompt


def test_llm_reranker_keeps_unranked_candidates_and_ignores_bad_ids():
    ranked = asyncio.run(LlmReranker(_Provider("[2, 9, 2]")).rerank("q", HITS, 3))

    assert _ids(ranked) == ["2", "1", "3"]


def test_llm_reranker_falls_back_to_original_order_on_garbage_or_outage():
    assert _ids(asyncio.run(LlmReranker(_Provider("không rõ")).rerank("q", HITS, 3))) == [
        "1",
        "2",
        "3",
    ]
    assert _ids(asyncio.run(LlmReranker(_Provider(fail=True)).rerank("q", HITS, 2))) == ["1", "2"]
