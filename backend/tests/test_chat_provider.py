import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import get_settings
from app.services import chat_provider
from app.services.chat_provider import (
    LangChainProvider,
    ProviderConfigurationError,
    ProviderError,
    ProviderMessage,
    UnavailableProvider,
    build_chat_model,
    get_model_provider,
)


class FakeChatModel(BaseChatModel):
    """Streams scripted chunks; `fail` raises like an upstream outage."""

    chunks: list[AIMessageChunk]
    fail: bool = False
    seen: list[list[BaseMessage]] = []

    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=""))])

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        self.seen.append(messages)
        for chunk in self.chunks:
            yield ChatGenerationChunk(message=chunk)
        if self.fail:
            raise RuntimeError("upstream 529 overloaded")

    def _stream(self, *args: Any, **kwargs: Any) -> Iterator[ChatGenerationChunk]:
        raise NotImplementedError


def _usage(input_tokens: int, output_tokens: int) -> UsageMetadata:
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def _provider(monkeypatch, model: FakeChatModel, name: str = "anthropic") -> LangChainProvider:
    built: list[tuple[str, str, str, int]] = []

    def fake_build(provider: str, api_key: str, model_id: str, max_tokens: int) -> FakeChatModel:
        built.append((provider, api_key, model_id, max_tokens))
        return model

    monkeypatch.setattr(chat_provider, "build_chat_model", fake_build)
    provider = LangChainProvider(name, SecretStr("sk-test"), "model-test")
    provider.built = built  # type: ignore[attr-defined]
    return provider


async def _collect(provider: LangChainProvider, messages=(), max_tokens: int = 100):
    return [event async for event in provider.stream(messages, "System prompt", max_tokens)]


def test_provider_translates_stream_sums_usage_and_skips_empty_chunks(monkeypatch) -> None:
    # Anthropic reports input tokens at message start and output tokens in the final delta.
    model = FakeChatModel(
        chunks=[
            AIMessageChunk(content="Chào ", usage_metadata=_usage(34, 1)),
            AIMessageChunk(content=""),
            AIMessageChunk(content="bạn"),
            AIMessageChunk(content="", usage_metadata=_usage(0, 11)),
        ],
        seen=[],
    )
    provider = _provider(monkeypatch, model)

    events = asyncio.run(
        _collect(provider, [ProviderMessage(role="user", content="Câu hỏi")], max_tokens=1500)
    )

    assert [(event.kind, event.text) for event in events] == [
        ("delta", "Chào "),
        ("delta", "bạn"),
        ("done", ""),
    ]
    assert (events[-1].input_tokens, events[-1].output_tokens) == (34, 12)
    assert provider.built == [("anthropic", "sk-test", "model-test", 1500)]  # type: ignore[attr-defined]


def test_provider_sends_system_prompt_then_history_in_order(monkeypatch) -> None:
    model = FakeChatModel(chunks=[AIMessageChunk(content="ok")], seen=[])
    provider = _provider(monkeypatch, model)

    asyncio.run(
        _collect(
            provider,
            [
                ProviderMessage(role="user", content="Câu 1"),
                ProviderMessage(role="assistant", content="Trả lời 1"),
                ProviderMessage(role="user", content="Câu 2"),
            ],
        )
    )

    sent = model.seen[0]
    assert [type(message) for message in sent] == [
        SystemMessage,
        HumanMessage,
        AIMessage,
        HumanMessage,
    ]
    assert [message.content for message in sent] == [
        "System prompt",
        "Câu 1",
        "Trả lời 1",
        "Câu 2",
    ]


def test_provider_reports_no_usage_when_upstream_sends_none(monkeypatch) -> None:
    provider = _provider(monkeypatch, FakeChatModel(chunks=[AIMessageChunk(content="x")], seen=[]))

    events = asyncio.run(_collect(provider))

    assert (events[-1].input_tokens, events[-1].output_tokens) == (None, None)


@pytest.mark.parametrize("key", [None, SecretStr(""), SecretStr("replace-with-your-api-key")])
def test_provider_rejects_missing_or_placeholder_key(key) -> None:
    provider = LangChainProvider("openai", key, "gpt-test")

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(_collect(provider))


def test_provider_wraps_upstream_failure(monkeypatch) -> None:
    """Upstream detail stays internal: callers only ever see ProviderError."""
    model = FakeChatModel(chunks=[AIMessageChunk(content="partial")], fail=True, seen=[])
    provider = _provider(monkeypatch, model)

    with pytest.raises(ProviderError) as raised:
        asyncio.run(_collect(provider))

    assert "529" not in str(raised.value)


def test_build_chat_model_openai_uses_responses_api_and_token_cap() -> None:
    model = build_chat_model("openai", "sk-test", "gpt-test", 1500)

    assert isinstance(model, ChatOpenAI)
    assert model.use_responses_api is True
    assert model.stream_usage is True
    payload = model._get_request_payload([HumanMessage(content="hi")])
    assert payload["model"] == "gpt-test"
    assert payload["max_output_tokens"] == 1500
    assert model.request_timeout == chat_provider.PROVIDER_TIMEOUT_SECONDS


def test_build_chat_model_anthropic_sets_token_cap_and_timeout() -> None:
    model = build_chat_model("anthropic", "sk-ant-test", "claude-test", 900)

    assert isinstance(model, ChatAnthropic)
    assert model.model == "claude-test"
    assert model.max_tokens == 900
    assert model.default_request_timeout == chat_provider.PROVIDER_TIMEOUT_SECONDS


def test_build_chat_model_rejects_unknown_provider() -> None:
    with pytest.raises(ProviderConfigurationError):
        build_chat_model("mistral", "key", "model", 100)


@pytest.mark.parametrize(
    ("configured", "expected_name", "key_setting"),
    [("openai", "openai", "openai_api_key"), ("Anthropic", "anthropic", "anthropic_api_key")],
)
def test_provider_factory_selects_langchain_provider(
    monkeypatch, configured, expected_name, key_setting
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "chat_provider", configured)
    monkeypatch.setattr(settings, "chat_model", "model-test")
    monkeypatch.setattr(settings, key_setting, SecretStr("sk-test"))

    provider = get_model_provider()

    assert isinstance(provider, LangChainProvider)
    assert provider.name == expected_name
    assert provider.model == "model-test"


def test_provider_factory_falls_back_to_unavailable(monkeypatch) -> None:
    """An unsupported CHAT_PROVIDER must fail as a configuration error, not a crash."""
    settings = get_settings()
    monkeypatch.setattr(settings, "chat_provider", "mistral")
    monkeypatch.setattr(settings, "chat_model", "whatever")

    provider = get_model_provider()
    assert isinstance(provider, UnavailableProvider)

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(_collect(provider))  # type: ignore[arg-type]
