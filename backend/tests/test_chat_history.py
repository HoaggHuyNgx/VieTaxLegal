import pytest

from app.services.chat_history import FOLLOW_UP_MAX_WORDS, retrieval_query
from app.services.chat_provider import ProviderMessage

LONG_QUESTION = " ".join(["từ"] * (FOLLOW_UP_MAX_WORDS + 1))


def history_of(*turns: tuple[str, str]) -> list[ProviderMessage]:
    return [ProviderMessage(role=role, content=content) for role, content in turns]


@pytest.mark.parametrize(
    ("history", "question"),
    [
        pytest.param(
            history_of(("user", "câu trước"), ("assistant", "đáp"), ("user", LONG_QUESTION)),
            LONG_QUESTION,
            id="standalone-question",
        ),
        pytest.param(history_of(("user", "còn gì nữa?")), "còn gì nữa?", id="no-earlier-question"),
    ],
)
def test_retrieval_query_leaves_the_question_unchanged(history, question) -> None:
    assert retrieval_query(history, question) == question


def test_retrieval_query_caps_the_previous_question_length() -> None:
    history = history_of(("user", "x" * 2000), ("assistant", "đáp"), ("user", "tiếp?"))

    query = retrieval_query(history, "tiếp?")

    assert query == "x" * 500 + "\ntiếp?"
