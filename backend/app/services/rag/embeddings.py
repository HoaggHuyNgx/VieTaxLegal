"""Embedding providers: OpenAI (primary), a deterministic fake for tests, BKAI (see bkai_embedder).

Callers pass raw NFC text; any provider-specific preprocessing (e.g. word segmentation) stays
inside the provider so ingest and query can never diverge.
"""

import hashlib
import math
import unicodedata
from dataclasses import dataclass
from typing import Protocol

from openai import AsyncOpenAI, OpenAI

from app.core.config import Settings, get_settings
from app.services.rag.chunking import ChunkDraft

# USD per 1M input tokens. Verify against the provider's pricing page before quoting in the thesis.
PRICE_PER_MILLION_TOKENS = {"text-embedding-3-small": 0.02, "text-embedding-3-large": 0.13}
KNOWN_DIMENSIONS = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}


class EmbeddingConfigError(ValueError):
    pass


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: list[list[float]]
    tokens: int


class EmbeddingProvider(Protocol):
    name: str
    model: str
    dims: int
    short_prefix: bool  # True: embed "Dieu N. Title" instead of the full heading path

    def embed_documents(self, texts: list[str]) -> EmbeddingBatch: ...

    async def aembed_query(self, text: str) -> list[float]: ...


def embedding_text(chunk: ChunkDraft, short_prefix: bool = False) -> str:
    """Text actually embedded: a heading prefix plus the clean chunk content."""
    prefix = chunk.heading_path.rsplit(" > ", 1)[-1][:120] if short_prefix else chunk.heading_path
    return unicodedata.normalize("NFC", f"{prefix}\n{chunk.content}")


def estimate_cost_usd(model: str, tokens: int) -> float | None:
    price = PRICE_PER_MILLION_TOKENS.get(model)
    return None if price is None else tokens / 1_000_000 * price


class FakeEmbedder:
    """Deterministic unit vectors from a hash of the text. Tests only; no semantic meaning."""

    name = "fake"
    short_prefix = False

    def __init__(self, dims: int = 16, model: str = "fake-embedding") -> None:
        self.dims, self.model = dims, model

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [digest[i % len(digest)] - 127.5 for i in range(self.dims)]
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    def embed_documents(self, texts: list[str]) -> EmbeddingBatch:
        return EmbeddingBatch([self._vector(t) for t in texts], sum(len(t.split()) for t in texts))

    async def aembed_query(self, text: str) -> list[float]:
        return self._vector(text)


class OpenAIEmbedder:
    name = "openai"
    short_prefix = False

    def __init__(self, api_key: str, model: str, dimensions: int | None = None) -> None:
        dims = dimensions or KNOWN_DIMENSIONS.get(model)
        if dims is None:
            raise EmbeddingConfigError(f"Set EMBEDDING_DIMENSIONS for unknown model '{model}'.")
        self.model, self.dims = model, dims
        self._custom_dimensions = dimensions
        self._sync = OpenAI(api_key=api_key, max_retries=5)  # SDK backs off on 429/5xx
        self._async = AsyncOpenAI(api_key=api_key, max_retries=5)

    def _kwargs(self) -> dict:
        extra = {"dimensions": self._custom_dimensions} if self._custom_dimensions else {}
        return {"model": self.model, **extra}

    def embed_documents(self, texts: list[str]) -> EmbeddingBatch:
        response = self._sync.embeddings.create(input=texts, **self._kwargs())
        return EmbeddingBatch(
            [item.embedding for item in response.data], response.usage.total_tokens
        )

    async def aembed_query(self, text: str) -> list[float]:
        response = await self._async.embeddings.create(input=[text], **self._kwargs())
        return response.data[0].embedding


def get_embedder(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    if settings.embedding_provider == "fake":
        return FakeEmbedder(settings.embedding_dimensions or 16)
    if settings.embedding_provider == "bkai":
        from app.services.rag.bkai_embedder import BkaiEmbedder  # heavy optional dependencies

        return BkaiEmbedder(settings.embedding_model, settings.embedding_batch_size)
    if settings.openai_api_key is None:
        raise EmbeddingConfigError("OPENAI_API_KEY is required for EMBEDDING_PROVIDER=openai.")
    return OpenAIEmbedder(
        settings.openai_api_key.get_secret_value(),
        settings.embedding_model,
        settings.embedding_dimensions,
    )
