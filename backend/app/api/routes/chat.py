from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.chat import Conversation, Message
from app.models.user import User
from app.schemas.chat import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    SendMessageRequest,
)
from app.services.chat import _owned_conversation, prepare_chat_stream, stream_chat_events
from app.services.chat_provider import ModelProvider, get_model_provider
from app.services.chat_retriever import Retriever, get_retriever

router = APIRouter(prefix="/chat", tags=["Chat"])


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
    conversation = database.scalar(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    if not conversation:
        # Use the shared ownership-safe error shape without revealing whether the UUID exists.
        _owned_conversation(database, current_user.id, conversation_id)
        raise AssertionError("unreachable")
    return ConversationDetailResponse.from_conversation(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[Session, Depends(get_db)],
) -> Response:
    conversation = _owned_conversation(database, current_user.id, conversation_id, lock=True)
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
