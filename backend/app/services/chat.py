import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.chat import ChatUsageEvent, Conversation, Message
from app.models.user import User
from app.schemas.chat import (
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
)
from app.services.chat_citations import (
    citation_snapshot,
    select_cited,
)
from app.services.chat_history import provider_history, retrieval_query
from app.services.chat_limits import enforce_rate_limits, expire_stale_pending
from app.services.chat_prompt import prompt_with_context
from app.services.chat_provider import (
    ModelProvider,
    ProviderConfigurationError,
)
from app.services.chat_retriever import Retriever

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PreparedChatStream:
    conversation_id: UUID
    user_message_id: UUID
    assistant_message_id: UUID
    query: str
    meta: dict[str, object]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def owned_conversation(
    database: Session, user_id: UUID, conversation_id: UUID, *, lock: bool = False
) -> Conversation:
    statement = select(Conversation).where(
        Conversation.id == conversation_id, Conversation.user_id == user_id
    )
    if lock:
        statement = statement.with_for_update()
    conversation = database.scalar(statement)
    if not conversation:
        raise AppError(404, "CONVERSATION_NOT_FOUND", "Không tìm thấy cuộc hội thoại.")
    return conversation


def _title_from_content(content: str) -> str:
    return " ".join(content.split())[:80]


def prepare_chat_stream(
    database: Session,
    user: User,
    payload: SendMessageRequest,
    provider: ModelProvider,
) -> PreparedChatStream:
    now = _utcnow()
    # Serializing on the user row makes the database-backed rate check atomic per account.
    database.scalar(select(User.id).where(User.id == user.id).with_for_update())
    enforce_rate_limits(database, user.id, now)

    if payload.conversation_id:
        conversation = owned_conversation(database, user.id, payload.conversation_id, lock=True)
        expire_stale_pending(database, conversation.id, now)
        pending = database.scalar(
            select(Message.id).where(
                Message.conversation_id == conversation.id,
                Message.role == "assistant",
                Message.status == "pending",
            )
        )
        if pending:
            raise AppError(
                409,
                "CHAT_IN_PROGRESS",
                "Cuộc hội thoại này đang có một câu trả lời được xử lý.",
            )
        conversation.updated_at = now
    else:
        conversation = Conversation(
            user_id=user.id,
            title=_title_from_content(payload.content),
            created_at=now,
            updated_at=now,
        )
        database.add(conversation)
        database.flush()

    database.add(ChatUsageEvent(user_id=user.id, created_at=now))

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        status="completed",
        content=payload.content,
        created_at=now,
        updated_at=now,
    )
    assistant_time = _utcnow()
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        status="pending",
        content="",
        provider=provider.name,
        model=provider.model,
        created_at=assistant_time,
        updated_at=assistant_time,
    )
    database.add_all([user_message, assistant_message])
    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise AppError(
            409,
            "CHAT_IN_PROGRESS",
            "Cuộc hội thoại này đang có một câu trả lời được xử lý.",
        ) from None

    database.refresh(conversation)
    database.refresh(user_message)
    database.refresh(assistant_message)
    meta: dict[str, object] = {
        "conversation": ConversationResponse.model_validate(conversation).model_dump(
            mode="json", by_alias=True
        ),
        "userMessage": MessageResponse.from_message(user_message).model_dump(
            mode="json", by_alias=True
        ),
        "assistantMessage": MessageResponse.from_message(assistant_message).model_dump(
            mode="json", by_alias=True
        ),
    }
    prepared = PreparedChatStream(
        conversation_id=conversation.id,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        query=payload.content,
        meta=meta,
    )
    # refresh() opens a read transaction; release it before the long-lived SSE response.
    database.rollback()
    return prepared


def _sse(event: str, data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


def _finalize_message(
    database: Session,
    prepared: PreparedChatStream,
    status: str,
    content: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    citations: list[dict[str, object]] | None = None,
) -> Message:
    message = database.get(Message, prepared.assistant_message_id)
    if not message:
        raise RuntimeError("Pending assistant message no longer exists")
    message.status = status
    message.content = content
    message.input_tokens = input_tokens
    message.output_tokens = output_tokens
    message.citations = citations or None
    message.updated_at = _utcnow()
    conversation = database.get(Conversation, prepared.conversation_id)
    if conversation:
        conversation.updated_at = message.updated_at
    original_expire_on_commit = database.expire_on_commit
    database.expire_on_commit = False
    try:
        database.commit()
    finally:
        database.expire_on_commit = original_expire_on_commit
    return message


def _finalize_quietly(
    database: Session, prepared: PreparedChatStream, status: str, content: str
) -> None:
    """Best-effort terminal write for error paths.

    If the database is also failing, raising here would replace the original error and the
    client would never get an `error` event. The stale-pending sweep recovers the row later.
    """
    try:
        database.rollback()
        _finalize_message(database, prepared, status, content)
    except Exception:
        database.rollback()
        logger.warning(
            "Could not mark assistant message %s as %s", prepared.assistant_message_id, status
        )


def _error_event(prepared: PreparedChatStream, code: str, message: str, retryable: bool) -> str:
    error = {"code": code, "message": message, "retryable": retryable}
    return _sse("error", {"messageId": str(prepared.assistant_message_id), "error": error})


async def stream_chat_events(
    database: Session,
    prepared: PreparedChatStream,
    provider: ModelProvider,
    retriever: Retriever,
) -> AsyncIterator[str]:
    partial_content = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    terminal_persisted = False
    try:
        yield _sse("meta", prepared.meta)
        history = provider_history(database, prepared.conversation_id)
        # Release the read-only transaction/connection before waiting on retrieval or the model.
        database.rollback()
        retrieval = await retriever.retrieve(retrieval_query(history, prepared.query))
        settings = get_settings()
        async for event in provider.stream(
            history,
            prompt_with_context(retrieval),
            settings.chat_max_output_tokens,
        ):
            if event.kind == "delta":
                partial_content += event.text
                yield _sse(
                    "delta",
                    {"messageId": str(prepared.assistant_message_id), "text": event.text},
                )
            else:
                input_tokens = event.input_tokens
                output_tokens = event.output_tokens

        selection = select_cited(retrieval, partial_content)
        if selection.unknown_markers:
            logger.info("Answer cited %d unknown source ids", len(selection.unknown_markers))
        message = _finalize_message(
            database,
            prepared,
            "completed",
            partial_content,
            input_tokens,
            output_tokens,
            citation_snapshot(selection.cited),
        )
        terminal_persisted = True
        message_payload = MessageResponse.from_message(message).model_dump(
            mode="json", by_alias=True
        )
        yield _sse(
            "done",
            {"message": message_payload, "usage": message_payload["tokenUsage"]},
        )
    except (asyncio.CancelledError, GeneratorExit):
        if not terminal_persisted:
            _finalize_quietly(database, prepared, "cancelled", partial_content)
        raise
    except Exception as error:
        if terminal_persisted:
            # The answer is already saved as completed; do not overwrite it with "failed".
            # The client sees a truncated stream and reloads the finished message.
            logger.warning("Chat stream failed after completion: %s", type(error).__name__)
            return
        logger.warning("Chat stream failed for assistant message %s", prepared.assistant_message_id)
        _finalize_quietly(database, prepared, "failed", partial_content)
        if isinstance(error, ProviderConfigurationError):
            yield _error_event(
                prepared,
                "CHAT_NOT_CONFIGURED",
                "Dịch vụ chat chưa được cấu hình. Vui lòng liên hệ quản trị viên.",
                retryable=False,
            )
        else:
            yield _error_event(
                prepared,
                "CHAT_PROVIDER_UNAVAILABLE",
                "Dịch vụ trả lời đang tạm thời gián đoạn. Vui lòng thử lại sau.",
                retryable=True,
            )
