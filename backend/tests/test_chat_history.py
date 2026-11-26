import pytest

from app.services.chat.history import FOLLOW_UP_MAX_WORDS, retrieval_query

LONG_QUESTION = " ".join(["từ"] * (FOLLOW_UP_MAX_WORDS + 1))


@pytest.mark.parametrize(
    ("previous", "question"),
    [
        pytest.param("câu trước", LONG_QUESTION, id="standalone-question"),
        pytest.param(None, "còn gì nữa?", id="no-earlier-question"),
    ],
)
def test_retrieval_query_leaves_the_question_unchanged(previous, question) -> None:
    assert retrieval_query(previous, question) == question


def test_retrieval_query_caps_the_previous_question_length() -> None:
    query = retrieval_query("x" * 2000, "tiếp?")

    assert query == "x" * 500 + "\ntiếp?"
