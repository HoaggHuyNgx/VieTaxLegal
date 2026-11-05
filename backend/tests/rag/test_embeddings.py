import asyncio
import math

import pytest

from app.core.config import Settings
from app.services.rag import embeddings
from app.services.rag.bkai_embedder import BkaiEmbedder
from app.services.rag.embeddings import (
    EmbeddingConfigError,
    FakeEmbedder,
    LangChainEmbedder,
    get_embedder,
    openai_embedder,
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


def test_openai_embedder_needs_dimensions_for_unknown_models():
    with pytest.raises(EmbeddingConfigError, match="EMBEDDING_DIMENSIONS"):
        openai_embedder("sk-test", "custom-model")
    assert openai_embedder("sk-test", "text-embedding-3-small").dims == 1536
    assert openai_embedder("sk-test", "custom-model", dimensions=256).dims == 256


def _no_tiktoken(*_args):
    raise AssertionError("tiktoken encoding loaded eagerly")


class _StubEmbeddings:
    def __init__(self):
        self.documents, self.queries = [], []

    def embed_documents(self, texts):
        self.documents.append(texts)
        return [[0.1, 0.2] for _ in texts]

    async def aembed_query(self, text):
        self.queries.append(text)
        return [0.3, 0.4]


def test_langchain_embedder_returns_vectors_and_counted_tokens():
    documents, queries = _StubEmbeddings(), _StubEmbeddings()
    embedder = LangChainEmbedder(
        "openai", "m", 2, documents, queries, count_tokens=lambda texts: 7 * len(texts)
    )

    batch = embedder.embed_documents(["a", "b"])

    assert documents.documents == [["a", "b"]]
    assert (len(batch.vectors), batch.tokens) == (2, 14)
    assert asyncio.run(embedder.aembed_query("q")) == [0.3, 0.4]
    assert (queries.queries, documents.queries) == (["q"], [])


def test_openai_embedder_configures_document_and_query_clients(monkeypatch):
    # Building the embedder (query path) must not load a tiktoken encoding (network download).
    monkeypatch.setattr(embeddings.tiktoken, "encoding_for_model", _no_tiktoken)
    embedder = openai_embedder("sk-test", "text-embedding-3-small", dimensions=256)

    assert embedder._documents.dimensions == 256
    assert embedder._documents.max_retries == 5
    assert embedder._queries.max_retries == 1


def test_get_embedder_requires_openai_key_and_supports_fake():
    with pytest.raises(EmbeddingConfigError, match="OPENAI_API_KEY"):
        get_embedder(_settings(embedding_provider="openai", openai_api_key=None))
    assert isinstance(get_embedder(_settings(embedding_provider="fake")), FakeEmbedder)
    assert get_embedder(_settings(openai_api_key="sk-test")).model == "text-embedding-3-small"


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
