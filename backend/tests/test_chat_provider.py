import asyncio
from collections.abc import AsyncIterator
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.core.config import get_settings
from app.services import chat_provider
from app.services.chat_provider import (
    AnthropicProvider,
    OpenAIProvider,
    ProviderConfigurationError,
    ProviderError,
    ProviderMessage,
    UnavailableProvider,
    get_model_provider,
)


class FakeOpenAIStream:
    def __init__(self, events: list[SimpleNamespace]) -> None:
        self.events = events

    async def __aiter__(self) -> AsyncIterator[SimpleNamespace]:
        for event in self.events:
            yield event


class FakeOpenAIResponses:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    async def create(self, **kwargs: object) -> FakeOpenAIStream:
        self.request = kwargs
        usage = SimpleNamespace(input_tokens=21, output_tokens=8)
        response = SimpleNamespace(usage=usage)
        return FakeOpenAIStream(
            [
                SimpleNamespace(type="response.created"),
                SimpleNamespace(type="response.output_text.delta", delta="Xin "),
                SimpleNamespace(type="response.output_text.delta", delta="chào"),
                SimpleNamespace(type="response.completed", response=response),
            ]
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeOpenAIResponses()
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class FakeAnthropicTextStream:
    def __init__(self, chunks: list[str]) -> None:
        self.chunks = chunks

    async def __aiter__(self) -> AsyncIterator[str]:
        for chunk in self.chunks:
            yield chunk


class FakeAnthropicStream:
    def __init__(self, chunks: list[str], usage: SimpleNamespace) -> None:
        self.text_stream = FakeAnthropicTextStream(chunks)
        self.usage = usage

    async def __aenter__(self) -> "FakeAnthropicStream":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get_final_message(self) -> SimpleNamespace:
        return SimpleNamespace(usage=self.usage)


class FakeAnthropicMessages:
    def __init__(self, chunks: list[str], usage: SimpleNamespace) -> None:
        self.chunks = chunks
        self.usage = usage
        self.request: dict[str, object] | None = None

    def stream(self, **kwargs: object) -> FakeAnthropicStream:
        # Not awaited: the SDK returns an async context manager directly.
        self.request = kwargs
        return FakeAnthropicStream(self.chunks, self.usage)


class FakeAnthropicClient:
    def __init__(self, chunks: list[str], usage: SimpleNamespace | None = None) -> None:
        self.messages = FakeAnthropicMessages(chunks, usage or SimpleNamespace())
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def test_anthropic_provider_translates_message_stream(monkeypatch) -> None:
    usage = SimpleNamespace(input_tokens=34, output_tokens=12)
    # The empty chunk must not become a delta event.
    client = FakeAnthropicClient(["Chào ", "", "bạn"], usage)
    monkeypatch.setattr(chat_provider, "AsyncAnthropic", lambda **_: client)
    provider = AnthropicProvider(SecretStr("sk-ant-test"), "claude-test")

    async def collect_events():
        return [
            event
            async for event in provider.stream(
                [ProviderMessage(role="user", content="Câu hỏi")],
                "System prompt",
                1500,
            )
        ]

    events = asyncio.run(collect_events())

    assert [(event.kind, event.text) for event in events] == [
        ("delta", "Chào "),
        ("delta", "bạn"),
        ("done", ""),
    ]
    assert events[-1].input_tokens == 34
    assert events[-1].output_tokens == 12
    assert client.messages.request == {
        "model": "claude-test",
        "max_tokens": 1500,
        "system": "System prompt",
        "messages": [{"role": "user", "content": "Câu hỏi"}],
    }
    assert client.closed is True


def test_anthropic_provider_rejects_missing_key() -> None:
    provider = AnthropicProvider(None, "claude-test")

    async def consume_stream() -> None:
        async for _ in provider.stream([], "System prompt", 100):
            pass

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(consume_stream())


def test_anthropic_provider_rejects_placeholder_key() -> None:
    """The .env.example placeholder must never reach the provider as a real key."""
    provider = AnthropicProvider(SecretStr("replace-with-your-anthropic-api-key"), "claude-test")

    async def consume_stream() -> None:
        async for _ in provider.stream([], "System prompt", 100):
            pass

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(consume_stream())


def test_anthropic_provider_wraps_upstream_failure(monkeypatch) -> None:
    """Upstream detail stays internal: callers only ever see ProviderError."""

    class ExplodingClient(FakeAnthropicClient):
        def __init__(self) -> None:
            super().__init__([])

        def _explode(self, **_: object) -> None:
            raise RuntimeError("upstream 529 overloaded")

    client = ExplodingClient()
    client.messages.stream = client._explode  # type: ignore[method-assign]
    monkeypatch.setattr(chat_provider, "AsyncAnthropic", lambda **_: client)
    provider = AnthropicProvider(SecretStr("sk-ant-test"), "claude-test")

    async def consume_stream() -> None:
        async for _ in provider.stream([], "System prompt", 100):
            pass

    with pytest.raises(ProviderError):
        asyncio.run(consume_stream())
    assert client.closed is True


def test_openai_provider_translates_responses_stream(monkeypatch) -> None:
    client = FakeOpenAIClient()
    monkeypatch.setattr(chat_provider, "AsyncOpenAI", lambda **_: client)
    provider = OpenAIProvider(SecretStr("sk-test"), "gpt-test")

    async def collect_events():
        return [
            event
            async for event in provider.stream(
                [ProviderMessage(role="user", content="Câu hỏi")],
                "System prompt",
                1500,
            )
        ]

    events = asyncio.run(collect_events())

    assert [(event.kind, event.text) for event in events] == [
        ("delta", "Xin "),
        ("delta", "chào"),
        ("done", ""),
    ]
    assert events[-1].input_tokens == 21
    assert events[-1].output_tokens == 8
    assert client.responses.request == {
        "model": "gpt-test",
        "instructions": "System prompt",
        "input": [{"role": "user", "content": "Câu hỏi"}],
        "max_output_tokens": 1500,
        "stream": True,
    }
    assert client.closed is True


def test_openai_provider_rejects_missing_key() -> None:
    provider = OpenAIProvider(None, "gpt-test")

    async def consume_stream() -> None:
        async for _ in provider.stream([], "System prompt", 100):
            pass

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(consume_stream())


def test_provider_factory_selects_openai(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "chat_provider", "openai")
    monkeypatch.setattr(settings, "chat_model", "gpt-test")
    monkeypatch.setattr(settings, "openai_api_key", SecretStr("sk-test"))

    provider = get_model_provider()

    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "openai"
    assert provider.model == "gpt-test"


def test_provider_factory_selects_anthropic(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "chat_provider", "Anthropic")
    monkeypatch.setattr(settings, "chat_model", "claude-test")
    monkeypatch.setattr(settings, "anthropic_api_key", SecretStr("sk-ant-test"))

    provider = get_model_provider()

    assert isinstance(provider, AnthropicProvider)
    assert provider.name == "anthropic"
    assert provider.model == "claude-test"


def test_provider_factory_falls_back_to_unavailable(monkeypatch) -> None:
    """An unsupported CHAT_PROVIDER must fail as a configuration error, not a crash."""
    settings = get_settings()
    monkeypatch.setattr(settings, "chat_provider", "mistral")
    monkeypatch.setattr(settings, "chat_model", "whatever")

    provider = get_model_provider()
    assert isinstance(provider, UnavailableProvider)

    async def consume_stream() -> None:
        async for _ in provider.stream([], "System prompt", 100):
            pass

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(consume_stream())
