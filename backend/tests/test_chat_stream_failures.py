import asyncio
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.chat import Message
from app.models.user import User
from app.schemas.chat import MessageResponse, SendMessageRequest
from app.services import chat as chat_service
from app.services.chat import prepare_chat_stream, stream_chat_events
from app.services.chat_history import FOLLOW_UP_MAX_WORDS, retrieval_query
from app.services.chat_provider import ProviderMessage
from app.services.chat_retriever import RetrievalResult
from tests.test_chat import FakeProvider, parse_sse, register


class RecordingRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def retrieve(self, query: str) -> RetrievalResult:
        self.queries.append(query)
        return RetrievalResult()


def user_for(client: TestClient, database_session: Session) -> User:
    user = database_session.get(User, UUID(register(client)["id"]))
    assert user is not None
    return user


async def collect(stream) -> list[str]:
    return [event async for event in stream]


def prepare(database_session: Session, user: User, provider: FakeProvider, text: str):
    return prepare_chat_stream(database_session, user, SendMessageRequest(content=text), provider)


def test_failing_finalize_does_not_hide_the_provider_error(
    client: TestClient, database_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DB trouble while recording a failure must not replace the error event with a crash."""
    user = user_for(client, database_session)
    provider = FakeProvider(fail=True)
    prepared = prepare(database_session, user, provider, "Câu hỏi")

    def broken_finalize(*args: object, **kwargs: object) -> None:
        raise RuntimeError("database is down")

    monkeypatch.setattr(chat_service, "_finalize_message", broken_finalize)

    events = asyncio.run(
        collect(stream_chat_events(database_session, prepared, provider, RecordingRetriever()))
    )

    parsed = parse_sse("".join(events))
    assert parsed[-1][0] == "error"
    assert parsed[-1][1]["error"]["code"] == "CHAT_PROVIDER_UNAVAILABLE"


def test_completed_answer_is_not_overwritten_by_a_late_error(
    client: TestClient, database_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = user_for(client, database_session)
    provider = FakeProvider(chunks=("Trả lời đầy đủ",))
    prepared = prepare(database_session, user, provider, "Câu hỏi")

    def broken_serializer(*args: object, **kwargs: object) -> None:
        raise ValueError("cannot serialize")

    monkeypatch.setattr(MessageResponse, "from_message", broken_serializer)

    events = asyncio.run(
        collect(stream_chat_events(database_session, prepared, provider, RecordingRetriever()))
    )

    assert "event: done" not in "".join(events)
    database_session.expire_all()
    saved = database_session.get(Message, prepared.assistant_message_id)
    assert saved.status == "completed"
    assert saved.content == "Trả lời đầy đủ"
    assert saved.output_tokens == 7


def test_follow_up_retrieval_uses_the_previous_question(
    client: TestClient, database_session: Session
) -> None:
    user = user_for(client, database_session)
    retriever = RecordingRetriever()
    provider = FakeProvider(chunks=("Câu trả lời",))
    first = prepare(database_session, user, provider, "Thuế GTGT hàng xuất khẩu là bao nhiêu?")
    asyncio.run(collect(stream_chat_events(database_session, first, provider, retriever)))

    second = prepare_chat_stream(
        database_session,
        user,
        SendMessageRequest(content="còn điều kiện thì sao?", conversationId=first.conversation_id),
        provider,
    )
    asyncio.run(collect(stream_chat_events(database_session, second, provider, retriever)))

    assert retriever.queries[0] == "Thuế GTGT hàng xuất khẩu là bao nhiêu?"
    assert retriever.queries[1] == (
        "Thuế GTGT hàng xuất khẩu là bao nhiêu?\ncòn điều kiện thì sao?"
    )


def history_of(*turns: tuple[str, str]) -> list[ProviderMessage]:
    return [ProviderMessage(role=role, content=content) for role, content in turns]


def test_retrieval_query_leaves_standalone_questions_alone() -> None:
    long_question = " ".join(["từ"] * (FOLLOW_UP_MAX_WORDS + 1))
    history = history_of(("user", "câu trước"), ("assistant", "đáp"), ("user", long_question))

    assert retrieval_query(history, long_question) == long_question


def test_retrieval_query_without_earlier_question_is_unchanged() -> None:
    assert retrieval_query(history_of(("user", "còn gì nữa?")), "còn gì nữa?") == "còn gì nữa?"


def test_retrieval_query_caps_the_previous_question_length() -> None:
    history = history_of(("user", "x" * 2000), ("assistant", "đáp"), ("user", "tiếp?"))

    query = retrieval_query(history, "tiếp?")

    assert query == "x" * 500 + "\ntiếp?"
