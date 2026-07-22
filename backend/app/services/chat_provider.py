from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import SecretStr

from app.core.config import get_settings


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


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: SecretStr | None, model: str) -> None:
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
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is not configured")

        client = AsyncAnthropic(api_key=api_key)
        try:
            async with client.messages.stream(
                model=self.model,
                max_tokens=max_output_tokens,
                system=system_prompt,
                messages=[{"role": item.role, "content": item.content} for item in messages],
            ) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield ProviderEvent(kind="delta", text=text)
                final_message = await stream.get_final_message()
                yield ProviderEvent(
                    kind="done",
                    input_tokens=final_message.usage.input_tokens,
                    output_tokens=final_message.usage.output_tokens,
                )
        except ProviderConfigurationError:
            raise
        except Exception as error:
            raise ProviderError("Anthropic request failed") from error
        finally:
            await client.close()


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: SecretStr | None, model: str) -> None:
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
            raise ProviderConfigurationError("OPENAI_API_KEY is not configured")

        client = AsyncOpenAI(api_key=api_key)
        completed = False
        try:
            stream = await client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=[{"role": item.role, "content": item.content} for item in messages],
                max_output_tokens=max_output_tokens,
                stream=True,
            )
            async for event in stream:
                event_type = getattr(event, "type", "")
                if event_type == "response.output_text.delta":
                    text = getattr(event, "delta", "")
                    if text:
                        yield ProviderEvent(kind="delta", text=text)
                elif event_type == "response.completed":
                    usage = getattr(getattr(event, "response", None), "usage", None)
                    yield ProviderEvent(
                        kind="done",
                        input_tokens=getattr(usage, "input_tokens", None),
                        output_tokens=getattr(usage, "output_tokens", None),
                    )
                    completed = True
                elif event_type in {"error", "response.failed", "response.incomplete"}:
                    raise ProviderError("OpenAI response stream failed")

            if not completed:
                raise ProviderError("OpenAI response stream ended before completion")
        except ProviderConfigurationError:
            raise
        except ProviderError:
            raise
        except Exception as error:
            raise ProviderError("OpenAI request failed") from error
        finally:
            await client.close()


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
        return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.chat_model)
    if provider_name == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.chat_model)
    return UnavailableProvider(name=settings.chat_provider, model=settings.chat_model)
