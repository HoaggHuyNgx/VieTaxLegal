import asyncio
import math
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services.rag.bkai_embedder import BkaiEmbedder
from app.services.rag.embeddings import (
    EmbeddingConfigError,
    FakeEmbedder,
    OpenAIEmbedder,
    estimate_cost_usd,
    get_embedder,
)

SECRET = "a-secure-test-secret-with-at-least-32-characters"


def _settings(**overrides) -> Settings:
    return Settings(database_url="sqlite+pysqlite://", jwt_secret=SECRET, **overrides)


def test_fake_embedder_is_deterministic_unit_length_and_text_sensitive():
    embedder = FakeEmbedder(dims=8)

    first = embedder.embed_documents(["Điều 1", "Điều 2"]).vectors
    again = embedder.embed_documents(["Điều 1"]).vectors[0]

    assert first[0] == again
    assert first[0] != first[1]
    assert math.isclose(sum(x * x for x in first[0]), 1.0)
    assert asyncio.run(embedder.aembed_query("Điều 1")) == again


def test_estimate_cost_known_and_unknown_model():
    assert estimate_cost_usd("text-embedding-3-small", 1_000_000) == pytest.approx(0.02)
    assert estimate_cost_usd("some-local-model", 1_000_000) is None


def test_openai_embedder_needs_dimensions_for_unknown_models():
    with pytest.raises(EmbeddingConfigError, match="EMBEDDING_DIMENSIONS"):
        OpenAIEmbedder("sk-test", "custom-model")
    assert OpenAIEmbedder("sk-test", "text-embedding-3-small").dims == 1536
    assert OpenAIEmbedder("sk-test", "custom-model", dimensions=256).dims == 256


def test_openai_embedder_sends_model_and_reads_vectors_and_usage():
    embedder = OpenAIEmbedder("sk-test", "text-embedding-3-small", dimensions=256)
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        data = [SimpleNamespace(embedding=[0.1, 0.2]) for _ in kwargs["input"]]
        return SimpleNamespace(data=data, usage=SimpleNamespace(total_tokens=7))

    embedder._sync = SimpleNamespace(embeddings=SimpleNamespace(create=create))

    batch = embedder.embed_documents(["a", "b"])

    assert calls == [{"input": ["a", "b"], "model": "text-embedding-3-small", "dimensions": 256}]
    assert (len(batch.vectors), batch.tokens) == (2, 7)


def test_get_embedder_requires_openai_key_and_supports_fake():
    with pytest.raises(EmbeddingConfigError, match="OPENAI_API_KEY"):
        get_embedder(_settings(embedding_provider="openai", openai_api_key=None))
    assert isinstance(get_embedder(_settings(embedding_provider="fake")), FakeEmbedder)
    assert get_embedder(_settings(openai_api_key="sk-test")).model == "text-embedding-3-small"


def test_settings_reject_unknown_embedding_provider():
    with pytest.raises(ValueError, match="EMBEDDING_PROVIDER"):
        _settings(embedding_provider="word2vec")


class _StubEncoder:
    def __init__(self):
        self.seen = []

    def get_sentence_embedding_dimension(self):
        return 3

    def encode(self, texts, batch_size, normalize_embeddings):
        self.seen.append((list(texts), batch_size, normalize_embeddings))
        return [[1.0, 0.0, 0.0] for _ in texts]


def test_bkai_embedder_segments_identically_for_documents_and_queries():
    encoder = _StubEncoder()
    embedder = BkaiEmbedder(
        "bkai/model", 4, encoder=encoder, segmenter=lambda text: text.replace(" ", "_")
    )

    batch = embedder.embed_documents(["thuế suất"])
    query = asyncio.run(embedder.aembed_query("thuế suất"))

    assert encoder.seen[0] == (["thuế_suất"], 4, True)
    assert encoder.seen[1][0] == ["thuế_suất"]
    assert batch.vectors[0] == query
    assert (embedder.dims, embedder.short_prefix) == (3, True)


def test_bkai_embedder_normalises_unicode_before_segmenting():
    encoder = _StubEncoder()
    embedder = BkaiEmbedder("m", encoder=encoder, segmenter=lambda text: text)

    embedder.embed_documents(["é"])

    assert encoder.seen[0][0] == ["é"]
