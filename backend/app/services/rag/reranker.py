"""Rerank seam. `NoopReranker` keeps the order; `LlmReranker` is the single trial for experiment 2.

A reranker reorders (and may truncate) the fused candidates. Whether to keep one is decided from
the experiment numbers (P9), not assumed.
"""

import json
import re
from typing import TYPE_CHECKING, Protocol

from app.services.chat_provider import ModelProvider, ProviderError, ProviderMessage

if TYPE_CHECKING:
    from app.services.rag.qdrant_retriever import Hit

_RERANK_SYSTEM = """Bạn xếp hạng độ liên quan của các đoạn luật đối với câu hỏi.
Chỉ trả về một mảng JSON các số thứ tự đoạn, từ liên quan nhất đến ít liên quan nhất,
ví dụ [3,1,2]. Không giải thích."""
_ARRAY_RE = re.compile(r"\[[\d,\s]*\]")


class Reranker(Protocol):
    async def rerank(self, query: str, hits: "list[Hit]", limit: int) -> "list[Hit]": ...


class NoopReranker:
    async def rerank(self, query: str, hits: "list[Hit]", limit: int) -> "list[Hit]":
        del query  # unused: order is kept
        return hits[:limit]


class LlmReranker:
    """Listwise rerank with the chat model: one extra model call per query (slow, costs tokens)."""

    def __init__(
        self, provider: ModelProvider, max_chars: int = 600, max_output_tokens: int = 3000
    ) -> None:
        self._provider, self._max_chars, self._max_tokens = provider, max_chars, max_output_tokens

    async def rerank(self, query: str, hits: "list[Hit]", limit: int) -> "list[Hit]":
        listing = "\n\n".join(
            f"[{number}] {hit.payload.get('heading_path', '')}\n"
            f"{str(hit.payload.get('content', ''))[: self._max_chars]}"
            for number, hit in enumerate(hits, start=1)
        )
        prompt = f"Câu hỏi: {query}\n\nCác đoạn:\n{listing}"
        order: list[int] = []
        try:
            text = ""
            async for event in self._provider.stream(
                [ProviderMessage("user", prompt)], _RERANK_SYSTEM, self._max_tokens
            ):
                if event.kind == "delta":
                    text += event.text
            match = _ARRAY_RE.search(text)
            order = [int(n) for n in json.loads(match.group(0))] if match else []
        except (ProviderError, ValueError):
            order = []  # fall back to the original order
        ranked = [hits[n - 1] for n in dict.fromkeys(order) if 1 <= n <= len(hits)]
        rest = [hit for hit in hits if hit not in ranked]  # unranked candidates keep their order
        return (ranked + rest)[:limit]
