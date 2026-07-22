import asyncio
import json
from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.main import app
from app.models.chat import ChatUsageEvent, Conversation, Message
from app.models.user import User
from app.schemas.chat import SendMessageRequest
from app.services.chat import _provider_history, prepare_chat_stream, stream_chat_events
from app.services.chat_provider import (
    ModelProvider,
    ProviderError,
    ProviderEvent,
    ProviderMessage,
    get_model_provider,
)


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, chunks: Sequence[str] = ("Xin ", "chào"), *, fail: bool = False) -> None:
        self.chunks = chunks
        self.fail = fail
        self.received_messages: list[ProviderMessage] = []

    async def stream(
        self,
        messages: Sequence[ProviderMessage],
        system_prompt: str,
        max_output_tokens: int,
    ) -> AsyncIterator[ProviderEvent]:
        self.received_messages = list(messages)
        assert "tiếng Việt" in system_prompt
        assert max_output_tokens > 0
        for chunk in self.chunks:
            yield ProviderEvent(kind="delta", text=chunk)
        if self.fail:
            raise ProviderError("sensitive upstream details")
        yield ProviderEvent(kind="done", input_tokens=12, output_tokens=7)


def register(client: TestClient, suffix: str = "one") -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"chat-{suffix}@example.com",
            "username": f"chat_{suffix}",
            "fullName": "Chat Tester",
            "password": "mat-khau-an-toan",
            "acceptTerms": True,
        },
    )
    assert response.status_code == 201
    return response.json()


def parse_sse(payload: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in payload.strip().split("\n\n"):
        lines = block.splitlines()
        event = next(line[6:].strip() for line in lines if line.startswith("event:"))
        data = "\n".join(line[5:].lstrip() for line in lines if line.startswith("data:"))
        events.append((event, json.loads(data)))
    return events


def install_provider(provider: ModelProvider) -> None:
    app.dependency_overrides[get_model_provider] = lambda: provider


def test_chat_end_to_end_stream_history_and_delete(
    client: TestClient, database_session: Session
) -> None:
    register(client)
    provider = FakeProvider()
    install_provider(provider)

    response = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": None, "content": "  Điều kiện khấu trừ thuế GTGT?  "},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache, no-transform"
    assert response.headers["x-accel-buffering"] == "no"
    events = parse_sse(response.text)
    assert [event for event, _ in events] == ["meta", "delta", "delta", "done"]

    meta = events[0][1]
    conversation_id = meta["conversation"]["id"]
    assistant_id = meta["assistantMessage"]["id"]
    assert meta["conversation"]["title"] == "Điều kiện khấu trừ thuế GTGT?"
    assert meta["userMessage"]["status"] == "completed"
    assert meta["assistantMessage"]["status"] == "pending"
    assert events[1][1] == {"messageId": assistant_id, "text": "Xin "}

    done = events[-1][1]
    assert done["message"]["content"] == "Xin chào"
    assert done["message"]["status"] == "completed"
    assert done["message"]["citations"] == []
    assert done["usage"] == {"inputTokens": 12, "outputTokens": 7}
    assert [(item.role, item.content) for item in provider.received_messages] == [
        ("user", "Điều kiện khấu trừ thuế GTGT?")
    ]

    list_response = client.get("/api/chat/conversations")
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == conversation_id

    detail = client.get(f"/api/chat/conversations/{conversation_id}")
    assert detail.status_code == 200
    assert [message["role"] for message in detail.json()["messages"]] == [
        "user",
        "assistant",
    ]

    delete_response = client.delete(f"/api/chat/conversations/{conversation_id}")
    assert delete_response.status_code == 204
    assert database_session.scalar(select(func.count(Conversation.id))) == 0
    assert database_session.scalar(select(func.count(Message.id))) == 0
    assert database_session.scalar(select(func.count(ChatUsageEvent.id))) == 1


def test_chat_endpoints_require_authentication(client: TestClient) -> None:
    conversation_id = uuid4()

    assert client.get("/api/chat/conversations").status_code == 401
    assert client.get(f"/api/chat/conversations/{conversation_id}").status_code == 401
    assert client.delete(f"/api/chat/conversations/{conversation_id}").status_code == 401
    assert (
        client.post(
            "/api/chat/messages/stream",
            json={"conversationId": None, "content": "Câu hỏi"},
        ).status_code
        == 401
    )


def test_conversation_ownership_is_not_disclosed(client: TestClient) -> None:
    register(client, "owner")
    install_provider(FakeProvider())
    created = parse_sse(
        client.post(
            "/api/chat/messages/stream",
            json={"conversationId": None, "content": "Câu hỏi của chủ sở hữu"},
        ).text
    )
    conversation_id = created[0][1]["conversation"]["id"]

    client.cookies.clear()
    register(client, "other")

    assert client.get(f"/api/chat/conversations/{conversation_id}").status_code == 404
    assert client.delete(f"/api/chat/conversations/{conversation_id}").status_code == 404
    response = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": conversation_id, "content": "Không thuộc sở hữu"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_provider_failure_is_safe_and_persisted(
    client: TestClient, database_session: Session
) -> None:
    register(client)
    install_provider(FakeProvider(chunks=("Nội dung dở",), fail=True))

    response = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": None, "content": "Câu hỏi gây lỗi"},
    )

    events = parse_sse(response.text)
    assert [event for event, _ in events] == ["meta", "delta", "error"]
    error = events[-1][1]
    assert error["messageId"] == events[0][1]["assistantMessage"]["id"]
    assert error["error"]["code"] == "CHAT_PROVIDER_UNAVAILABLE"
    assert error["error"]["retryable"] is True
    assert "sensitive" not in response.text

    assistant = database_session.scalar(select(Message).where(Message.role == "assistant"))
    assert assistant is not None
    database_session.refresh(assistant)
    assert assistant.status == "failed"
    assert assistant.content == "Nội dung dở"


def test_validation_and_rate_limits_happen_before_stream(client: TestClient, monkeypatch) -> None:
    register(client)
    install_provider(FakeProvider())

    invalid = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": None, "content": "x" * 4001},
    )
    assert invalid.status_code == 422
    assert invalid.headers["content-type"].startswith("application/json")

    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "chat_rate_limit_per_minute", 1)
    first = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": None, "content": "Câu đầu"},
    )
    assert first.status_code == 200
    conversation_id = parse_sse(first.text)[0][1]["conversation"]["id"]
    assert client.delete(f"/api/chat/conversations/{conversation_id}").status_code == 204
    limited = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": None, "content": "Câu thứ hai"},
    )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "CHAT_RATE_LIMITED"


def test_daily_limit(client: TestClient, monkeypatch) -> None:
    register(client)
    install_provider(FakeProvider())

    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "chat_rate_limit_per_minute", 100)
    monkeypatch.setattr(get_settings(), "chat_daily_message_limit", 1)
    first = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": None, "content": "Câu đầu"},
    )
    assert first.status_code == 200
    conversation_id = parse_sse(first.text)[0][1]["conversation"]["id"]
    assert client.delete(f"/api/chat/conversations/{conversation_id}").status_code == 204
    limited = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": None, "content": "Câu thứ hai"},
    )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "CHAT_DAILY_LIMIT_REACHED"


def test_pending_conversation_rejects_send_and_delete(
    client: TestClient, database_session: Session
) -> None:
    user_data = register(client)
    conversation = Conversation(user_id=UUID(user_data["id"]), title="Pending")
    database_session.add(conversation)
    database_session.flush()
    database_session.add(
        Message(
            conversation_id=conversation.id,
            role="assistant",
            status="pending",
            content="",
        )
    )
    database_session.commit()
    install_provider(FakeProvider())

    send = client.post(
        "/api/chat/messages/stream",
        json={"conversationId": str(conversation.id), "content": "Câu mới"},
    )
    assert send.status_code == 409
    assert send.json()["error"]["code"] == "CHAT_IN_PROGRESS"
    delete = client.delete(f"/api/chat/conversations/{conversation.id}")
    assert delete.status_code == 409
    assert delete.json()["error"]["code"] == "CHAT_IN_PROGRESS"


def test_abort_persists_partial_content_and_closing_done_stays_completed(
    client: TestClient, database_session: Session
) -> None:
    user_data = register(client)
    user = database_session.get(User, UUID(user_data["id"]))
    assert user is not None

    async def exercise_abort() -> UUID:
        provider = FakeProvider(chunks=("Một phần",))
        prepared = prepare_chat_stream(
            database_session,
            user,
            SendMessageRequest(content="Câu bị dừng"),
            provider,
        )
        assert database_session.in_transaction() is False
        stream = stream_chat_events(database_session, prepared, provider, NullRetrieverForTest())
        assert "event: meta" in await anext(stream)
        assert "Một phần" in await anext(stream)
        assert database_session.in_transaction() is False
        await stream.aclose()
        return prepared.assistant_message_id

    aborted_id = asyncio.run(exercise_abort())
    database_session.expire_all()
    aborted = database_session.get(Message, aborted_id)
    assert aborted is not None
    assert aborted.status == "cancelled"
    assert aborted.content == "Một phần"

    async def exercise_done() -> UUID:
        provider = FakeProvider(chunks=("Hoàn tất",))
        prepared = prepare_chat_stream(
            database_session,
            user,
            SendMessageRequest(content="Câu hoàn tất"),
            provider,
        )
        assert database_session.in_transaction() is False
        stream = stream_chat_events(database_session, prepared, provider, NullRetrieverForTest())
        while True:
            event = await anext(stream)
            if "event: done" in event:
                assert database_session.in_transaction() is False
                break
        await stream.aclose()
        return prepared.assistant_message_id

    completed_id = asyncio.run(exercise_done())
    database_session.expire_all()
    completed = database_session.get(Message, completed_id)
    assert completed is not None
    assert completed.status == "completed"


class NullRetrieverForTest:
    async def retrieve(self, query: str):
        from app.services.chat_retriever import RetrievalResult

        assert query
        return RetrievalResult()


def test_history_respects_message_and_character_caps(
    client: TestClient, database_session: Session, monkeypatch
) -> None:
    user_data = register(client)
    conversation = Conversation(user_id=UUID(user_data["id"]), title="Long history")
    database_session.add(conversation)
    database_session.flush()
    start = datetime.now(timezone.utc)
    for index in range(20):
        database_session.add(
            Message(
                conversation_id=conversation.id,
                role="user" if index % 2 == 0 else "assistant",
                status="completed",
                content=str(index) * 3000,
                created_at=start + timedelta(microseconds=index),
                updated_at=start + timedelta(microseconds=index),
            )
        )
    database_session.commit()

    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "chat_history_messages", 20)
    history = _provider_history(database_session, conversation.id)
    assert len(history) <= 20
    assert sum(len(item.content) for item in history) <= 40_000
