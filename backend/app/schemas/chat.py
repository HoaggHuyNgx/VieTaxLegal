from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, StringConstraints

from app.models.chat import Conversation, Message

ChatContent = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
]


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("conversationId", "conversation_id"),
        serialization_alias="conversationId",
    )
    content: ChatContent


class TokenUsage(BaseModel):
    input_tokens: int | None = Field(serialization_alias="inputTokens")
    output_tokens: int | None = Field(serialization_alias="outputTokens")


class CitationResponse(BaseModel):
    id: str
    title: str
    url: str | None = None
    excerpt: str | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    conversation_id: UUID = Field(serialization_alias="conversationId")
    role: Literal["user", "assistant"]
    status: Literal["pending", "completed", "failed", "cancelled"]
    content: str
    provider: str | None
    model: str | None
    token_usage: TokenUsage = Field(serialization_alias="tokenUsage")
    citations: list[CitationResponse] = Field(default_factory=list)
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @classmethod
    def from_message(cls, message: Message) -> "MessageResponse":
        return cls(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,  # type: ignore[arg-type]
            status=message.status,  # type: ignore[arg-type]
            content=message.content,
            provider=message.provider,
            model=message.model,
            token_usage=TokenUsage(
                input_tokens=message.input_tokens,
                output_tokens=message.output_tokens,
            ),
            citations=[],
            created_at=message.created_at,
            updated_at=message.updated_at,
        )


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    title: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]

    @classmethod
    def from_conversation(cls, conversation: Conversation) -> "ConversationDetailResponse":
        return cls(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[MessageResponse.from_message(message) for message in conversation.messages],
        )
