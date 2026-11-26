"""Conversation history sent to the model, and the query used to retrieve sources."""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chat import Message
from app.services.chat.citations import strip_markers
from app.services.chat.provider import ProviderMessage

MAX_HISTORY_CHARACTERS = 40_000
# A question this short is usually a follow-up ("còn điều kiện thì sao?") that is meaningless
# to the retriever on its own. Heuristic: tune against real conversations, not the eval set.
FOLLOW_UP_MAX_WORDS = 8
PREVIOUS_QUESTION_MAX_CHARACTERS = 500


def provider_history(database: Session, conversation_id: UUID) -> list[ProviderMessage]:
    settings = get_settings()
    eligible = or_(
        and_(Message.role == "user", Message.status == "completed"),
        and_(Message.role == "assistant", Message.status == "completed"),
    )
    newest = list(
        database.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id, eligible)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(settings.chat_history_messages)
        )
    )

    selected: list[Message] = []
    character_count = 0
    for message in newest:
        if character_count + len(message.content) > MAX_HISTORY_CHARACTERS:
            break
        selected.append(message)
        character_count += len(message.content)
    selected.reverse()

    normalized: list[ProviderMessage] = []
    for message in selected:
        role = message.role
        content = strip_markers(message.content) if role == "assistant" else message.content
        if role == "assistant" and not normalized:
            continue
        if normalized and normalized[-1].role == role:
            previous = normalized[-1]
            normalized[-1] = ProviderMessage(
                role=previous.role, content=f"{previous.content}\n\n{content}"
            )
        else:
            normalized.append(ProviderMessage(role=role, content=content))  # type: ignore[arg-type]
    return normalized


def previous_question(
    database: Session, conversation_id: UUID, current_message_id: UUID
) -> str | None:
    """The user's message before this one, read directly: in `provider_history` a failed reply
    leaves two user turns that are merged, which would hide it."""
    return database.scalar(
        select(Message.content)
        .where(
            Message.conversation_id == conversation_id,
            Message.role == "user",
            Message.id != current_message_id,
        )
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
    )


def retrieval_query(previous: str | None, question: str) -> str:
    """Prefix a short follow-up with the user's previous question so retrieval has a topic."""
    if not previous or len(question.split()) > FOLLOW_UP_MAX_WORDS:
        return question
    return "\n".join((previous[-PREVIOUS_QUESTION_MAX_CHARACTERS:], question))
