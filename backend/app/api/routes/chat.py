"""HTTP endpoints for chat (thin layer; the logic lives in `services/chat/`).

GET /usage, GET /conversations, GET and DELETE /conversations/{id}, and POST /messages/stream,
which returns a Server-Sent Events stream. Every query filters by the current user.
"""

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.chat import Conversation, Message
from app.models.user import User
from app.schemas.chat import (
    ChatUsageResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    SendMessageRequest,
)
from app.services.chat.limits import count_daily_messages
from app.services.chat.provider import ModelProvider, get_model_provider
from app.services.chat.retriever import Retriever, get_retriever
from app.services.chat.service import (
    expire_stale_pending,
    owned_conversation,
    prepare_chat_stream,
    stream_chat_events,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/usage", response_model=ChatUsageResponse)
def get_usage(
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[Session, Depends(get_db)],
) -> ChatUsageResponse:
    limit = get_settings().chat_daily_message_limit
    used = count_daily_messages(database, current_user.id, datetime.now(timezone.utc))
    return ChatUsageResponse(
        daily_limit=limit, daily_used=used, daily_remaining=max(limit - used, 0)
    )


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 50,
) -> ConversationListResponse:
    conversations = list(
        database.scalars(
            select(Conversation)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .limit(limit)
        )
    )
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(item) for item in conversations]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[Session, Depends(get_db)],
) -> ConversationDetailResponse:
    # A UUID owned by someone else is indistinguishable from one that does not exist: same
    # 404, same message. Never 403, which would confirm existence.
    conversation = owned_conversation(database, current_user.id, conversation_id)
    # A reply whose stream died would otherwise show as "answering" until the next send.
    expire_stale_pending(database, conversation.id, datetime.now(timezone.utc))
    database.commit()
    database.refresh(conversation, ["messages"])
    return ConversationDetailResponse.from_conversation(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[Session, Depends(get_db)],
) -> Response:
    conversation = owned_conversation(database, current_user.id, conversation_id, lock=True)
    expire_stale_pending(database, conversation.id, datetime.now(timezone.utc))
    has_pending = database.scalar(
        select(Message.id).where(
            Message.conversation_id == conversation.id,
            Message.role == "assistant",
            Message.status == "pending",
        )
    )
    if has_pending:
        raise AppError(
            409,
            "CHAT_IN_PROGRESS",
            "Hãy dừng câu trả lời trước khi xóa cuộc hội thoại này.",
        )
    database.delete(conversation)
    database.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/messages/stream")
def stream_message(
    payload: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[Session, Depends(get_db)],
    provider: Annotated[ModelProvider, Depends(get_model_provider)],
    retriever: Annotated[Retriever, Depends(get_retriever)],
) -> StreamingResponse:
    # Validation, ownership, limits, and pending-message creation happen before response headers.
    prepared = prepare_chat_stream(database, current_user, payload, provider)
    bind = database.get_bind()

    async def event_source() -> AsyncIterator[str]:
        stream_database = Session(bind=bind, autoflush=False, expire_on_commit=False)
        stream = stream_chat_events(stream_database, prepared, provider, retriever)
        try:
            async for event in stream:
                yield event
        finally:
            try:
                await stream.aclose()
            finally:
                stream_database.close()

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
