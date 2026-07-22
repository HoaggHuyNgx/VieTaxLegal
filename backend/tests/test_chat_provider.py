import asyncio
from collections.abc import AsyncIterator
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.core.config import get_settings
from app.services import chat_provider
from app.services.chat_provider import (
    OpenAIProvider,
    ProviderConfigurationError,
    ProviderMessage,
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
