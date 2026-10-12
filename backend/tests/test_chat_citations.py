import asyncio
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_chat import FakeProvider, register

from app.models.chat import Message
from app.models.user import User
from app.schemas.chat import SendMessageRequest
from app.services.chat import prepare_chat_stream, stream_chat_events
from app.services.chat_citations import citation_snapshot, marker_ids, select_cited
from app.services.chat_prompt import CITATION_RULES, SYSTEM_PROMPT, prompt_with_context
from app.services.chat_retriever import Citation, RetrievalResult, RetrievedContext

CITATIONS = [
    Citation(
        id="1",
        title="Luật Quản lý thuế",
        url="https://example.test/108",
        excerpt="Điều 16...",
        doc_number="108/2025/QH15",
        locator="Điều 16 khoản 2",
        issued_on="2025-12-10",
    ),
    Citation(id="2", title="Luật Thuế GTGT", url=None, doc_number="48/2024/QH15"),
    Citation(id="3", title="Không dùng", locator="Điều 99"),
]
RESULT = RetrievalResult(
    contexts=[RetrievedContext(content=f"nội dung {c.id}", citation_id=c.id) for c in CITATIONS],
    citations=CITATIONS,
)


class FakeRetriever:
    async def retrieve(self, query: str) -> RetrievalResult:
        assert query
        return RESULT


def test_marker_ids_keep_first_appearance_order_and_drop_repeats():
    assert marker_ids("Theo [2] và [1], lại [2]. Không phải [x] hay [] hay [1234].") == ["2", "1"]
    assert marker_ids("không có nguồn") == []


def test_select_cited_returns_only_used_sources_and_reports_invented_ones():
    selection = select_cited(RESULT, "Căn cứ [2] và [1]; ngoài ra [7].")

    assert [c.id for c in selection.cited] == ["2", "1"]
    assert selection.unknown_markers == ["7"]
    assert select_cited(RESULT, "Trả lời không trích nguồn.").cited == []


def test_snapshot_is_camel_case_without_nulls():
    snapshot = citation_snapshot(CITATIONS[:2])

    assert snapshot[0] == {
        "id": "1",
        "title": "Luật Quản lý thuế",
        "url": "https://example.test/108",
        "excerpt": "Điều 16...",
        "documentNumber": "108/2025/QH15",
        "locator": "Điều 16 khoản 2",
        "issuedOn": "2025-12-10",
    }
    assert snapshot[1] == {"id": "2", "title": "Luật Thuế GTGT", "documentNumber": "48/2024/QH15"}


def test_prompt_keeps_no_fabrication_rules_and_adds_citation_rules_only_with_sources():
    plain = prompt_with_context(RetrievalResult())
    grounded = prompt_with_context(RESULT)

    assert plain == SYSTEM_PROMPT
    assert grounded.startswith(SYSTEM_PROMPT)
    assert "Không được bịa số hiệu văn bản" in grounded
    assert "chưa thể xác minh hiệu lực" in grounded
    assert CITATION_RULES in grounded
    assert '<reference id="2">\nnội dung 2\n</reference>' in grounded
    assert CITATION_RULES not in plain


def _run_stream(database: Session, user: User, answer: str, retriever) -> UUID:
    async def exercise() -> UUID:
        provider = FakeProvider(chunks=(answer,))
        prepared = prepare_chat_stream(
            database, user, SendMessageRequest(content="Mức phạt chậm nộp?"), provider
        )
        stream = stream_chat_events(database, prepared, provider, retriever)
        async for event in stream:
            if "event: done" in event:
                break
        await stream.aclose()
        return prepared.assistant_message_id

    return asyncio.run(exercise())


def test_cited_sources_are_persisted_and_survive_reload(
    client: TestClient, database_session: Session
) -> None:
    user_data = register(client)
    user = database_session.get(User, UUID(user_data["id"]))
    assert user is not None

    message_id = _run_stream(
        database_session, user, "Phạt theo [2], căn cứ [1], bịa [9].", FakeRetriever()
    )

    database_session.expire_all()
    stored = database_session.get(Message, message_id)
    assert stored is not None
    assert [c["id"] for c in stored.citations] == ["2", "1"]
    conversation_id = stored.conversation_id
    reloaded = client.get(f"/api/chat/conversations/{conversation_id}").json()
    assistant = [m for m in reloaded["messages"] if m["role"] == "assistant"][0]
    assert [c["id"] for c in assistant["citations"]] == ["2", "1"]
    assert assistant["citations"][1]["locator"] == "Điều 16 khoản 2"
    assert assistant["citations"][1]["documentNumber"] == "108/2025/QH15"


def test_answer_without_markers_stores_no_citations(
    client: TestClient, database_session: Session
) -> None:
    user_data = register(client, "nomarker")
    user = database_session.get(User, UUID(user_data["id"]))
    assert user is not None

    message_id = _run_stream(database_session, user, "Không viện dẫn nguồn nào.", FakeRetriever())

    database_session.expire_all()
    stored = database_session.get(Message, message_id)
    assert stored is not None and stored.citations is None
