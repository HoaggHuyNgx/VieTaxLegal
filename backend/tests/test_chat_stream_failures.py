import asyncio
import threading
from dataclasses import replace
from datetime import timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.chat import Message
from app.models.user import User
from app.schemas.chat import MessageResponse, SendMessageRequest
from app.services.chat import service as chat_service
from app.services.chat.retriever import RetrievalResult
from app.services.chat.service import (
    TRUNCATED_NOTE,
    prepare_chat_stream,
    stream_chat_events,
)
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


class TruncatingProvider(FakeProvider):
    """Ends the way a real provider does when the output-token cap is reached."""

    def __init__(self, chunks: tuple[str, ...]) -> None:
        super().__init__(chunks)

    async def stream(self, messages, system_prompt, max_output_tokens):
        async for event in super().stream(messages, system_prompt, max_output_tokens):
            yield replace(event, truncated=True) if event.kind == "done" else event


@pytest.mark.parametrize("chunks", [("Theo quy ", "định"), ()])
def test_truncated_answer_says_so_on_screen_and_after_reload(
    client: TestClient, database_session: Session, chunks: tuple[str, ...]
) -> None:
    user = user_for(client, database_session)
    provider = TruncatingProvider(chunks)
    prepared = prepare(database_session, user, provider, "Câu hỏi")

    events = asyncio.run(
        collect(stream_chat_events(database_session, prepared, provider, RecordingRetriever()))
    )

    parsed = parse_sse("".join(events))
    shown = "".join(data["text"] for name, data in parsed if name == "delta")
    database_session.expire_all()
    stored = database_session.get(Message, prepared.assistant_message_id)
    assert stored is not None and stored.status == "completed"
    assert stored.content == shown  # the stream and the saved row agree
    separator = "\n\n" if chunks else ""
    assert stored.content == "".join(chunks) + separator + TRUNCATED_NOTE


def test_database_work_in_the_stream_stays_off_the_event_loop(
    client: TestClient, database_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A synchronous query on the loop (say, waiting for a pooled connection) stalls everyone."""
    user = user_for(client, database_session)
    provider = FakeProvider()
    prepared = prepare(database_session, user, provider, "Câu hỏi")
    threads: dict[str, int] = {}

    def recording(name: str):
        original = getattr(chat_service, name)

        def wrapper(*args, **kwargs):
            threads[name] = threading.get_ident()
            return original(*args, **kwargs)

        monkeypatch.setattr(chat_service, name, wrapper)

    recording("provider_history")
    recording("_finalize_message")

    asyncio.run(
        collect(stream_chat_events(database_session, prepared, provider, RecordingRetriever()))
    )

    assert set(threads) == {"provider_history", "_finalize_message"}
    assert threading.get_ident() not in threads.values()


def test_a_cancel_arriving_after_the_save_does_not_undo_it(
    client: TestClient, database_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = user_for(client, database_session)
    provider = FakeProvider()
    prepared = prepare(database_session, user, provider, "Câu hỏi")
    original = chat_service._finalize_message
    calls: list[str] = []

    def saved_then_cancelled(database, prepared_stream, status, *args, **kwargs):
        calls.append(status)
        message = original(database, prepared_stream, status, *args, **kwargs)
        if len(calls) == 1:
            raise asyncio.CancelledError
        return message

    monkeypatch.setattr(chat_service, "_finalize_message", saved_then_cancelled)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            collect(stream_chat_events(database_session, prepared, provider, RecordingRetriever()))
        )

    database_session.expire_all()
    assert database_session.get(Message, prepared.assistant_message_id).status == "completed"


def test_follow_up_after_a_failed_reply_still_carries_the_previous_question(
    client: TestClient, database_session: Session
) -> None:
    user = user_for(client, database_session)
    first_question = "Điều kiện khấu trừ thuế giá trị gia tăng đầu vào gồm những gì?"
    retriever = RecordingRetriever()
    failing = FakeProvider(fail=True)
    first = prepare(database_session, user, failing, first_question)
    asyncio.run(collect(stream_chat_events(database_session, first, failing, retriever)))

    provider = FakeProvider()
    follow_up = prepare_chat_stream(
        database_session,
        user,
        SendMessageRequest(conversationId=first.conversation_id, content="còn hồ sơ?"),
        provider,
    )
    asyncio.run(collect(stream_chat_events(database_session, follow_up, provider, retriever)))

    assert retriever.queries[-1] == "\n".join((first_question, "còn hồ sơ?"))


def test_opening_a_conversation_expires_a_reply_that_never_finished(
    client: TestClient, database_session: Session
) -> None:
    user = user_for(client, database_session)
    prepared = prepare(database_session, user, FakeProvider(), "Câu hỏi")
    stuck = database_session.get(Message, prepared.assistant_message_id)
    stuck.created_at = stuck.created_at - timedelta(minutes=10)
    database_session.commit()

    response = client.get(f"/api/chat/conversations/{prepared.conversation_id}")

    statuses = {m["role"]: m["status"] for m in response.json()["messages"]}
    assert statuses == {"user": "completed", "assistant": "failed"}
