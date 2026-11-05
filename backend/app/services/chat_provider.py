from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import get_settings

# Per-read timeout (also applies between streamed chunks), so a stalled provider cannot hold
# a chat request, and its row lock on the conversation, for the SDK default of 10 minutes.
PROVIDER_TIMEOUT_SECONDS = 60.0


class ProviderError(Exception):
    """A provider failure that is safe to translate to a generic client error."""


class ProviderConfigurationError(ProviderError):
    """Raised when the selected provider cannot be initialized."""


@dataclass(frozen=True, slots=True)
class ProviderMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class ProviderEvent:
    kind: Literal["delta", "done"]
    text: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None


class ModelProvider(Protocol):
    name: str
    model: str

    def stream(
        self,
        messages: Sequence[ProviderMessage],
        system_prompt: str,
        max_output_tokens: int,
    ) -> AsyncIterator[ProviderEvent]: ...


def build_chat_model(name: str, api_key: str, model: str, max_output_tokens: int) -> BaseChatModel:
    """LangChain chat model for a supported provider (OpenAI Responses API / Anthropic Messages)."""
    if name == "anthropic":
        return ChatAnthropic(
            model=model,
            api_key=SecretStr(api_key),
            max_tokens=max_output_tokens,
            timeout=PROVIDER_TIMEOUT_SECONDS,
        )
    if name == "openai":
        return ChatOpenAI(
            model=model,
            api_key=SecretStr(api_key),
            use_responses_api=True,
            stream_usage=True,
            max_tokens=max_output_tokens,
            timeout=PROVIDER_TIMEOUT_SECONDS,
        )
    raise ProviderConfigurationError("Unsupported chat provider")


def _to_langchain(messages: Sequence[ProviderMessage], system_prompt: str) -> list[BaseMessage]:
    converted: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    for item in messages:
        message_type = HumanMessage if item.role == "user" else AIMessage
        converted.append(message_type(content=item.content))
    return converted


class LangChainProvider:
    """Streams a LangChain chat model as `ProviderEvent`s; the model is built per request."""

    def __init__(self, name: str, api_key: SecretStr | None, model: str) -> None:
        self.name = name
        self.api_key = api_key
        self.model = model

    async def stream(
        self,
        messages: Sequence[ProviderMessage],
        system_prompt: str,
        max_output_tokens: int,
    ) -> AsyncIterator[ProviderEvent]:
        api_key = self.api_key.get_secret_value() if self.api_key else ""
        if not api_key or api_key.startswith("replace-with-"):
            raise ProviderConfigurationError(f"{self.name.upper()}_API_KEY is not configured")

        chat_model = build_chat_model(self.name, api_key, self.model, max_output_tokens)
        input_tokens: int | None = None
        output_tokens: int | None = None
        try:
            async for chunk in chat_model.astream(_to_langchain(messages, system_prompt)):
                text = str(chunk.text)
                if text:
                    yield ProviderEvent(kind="delta", text=text)
                # Providers report usage across several chunks (Anthropic: start + delta).
                if usage := chunk.usage_metadata:
                    input_tokens = (input_tokens or 0) + usage.get("input_tokens", 0)
                    output_tokens = (output_tokens or 0) + usage.get("output_tokens", 0)
        except ProviderError:
            raise
        except Exception as error:
            raise ProviderError(f"{self.name} request failed") from error
        yield ProviderEvent(kind="done", input_tokens=input_tokens, output_tokens=output_tokens)


class UnavailableProvider:
    def __init__(self, name: str, model: str) -> None:
        self.name = name
        self.model = model

    async def stream(
        self,
        messages: Sequence[ProviderMessage],
        system_prompt: str,
        max_output_tokens: int,
    ) -> AsyncIterator[ProviderEvent]:
        del messages, system_prompt, max_output_tokens
        raise ProviderConfigurationError("Unsupported chat provider")
        yield  # pragma: no cover


def get_model_provider() -> ModelProvider:
    settings = get_settings()
    provider_name = settings.chat_provider.lower()
    if provider_name == "anthropic":
        return LangChainProvider(provider_name, settings.anthropic_api_key, settings.chat_model)
    if provider_name == "openai":
        return LangChainProvider(provider_name, settings.openai_api_key, settings.chat_model)
    return UnavailableProvider(name=settings.chat_provider, model=settings.chat_model)
