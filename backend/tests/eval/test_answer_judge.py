import asyncio

from app.services.chat.provider import ProviderError, ProviderEvent
from rag_eval.answer_judge import gold_numbers_present, judge_rows


class ScriptedProvider:
    """Replies with each scripted text in turn; an exception in the script is raised."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    async def stream(self, messages, system, max_tokens):
        self.prompts.append(messages[0].content)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        yield ProviderEvent(kind="delta", text=reply)
        yield ProviderEvent(kind="done")


def row(answer="Thuế suất 10% trong 15 năm.", **extra):
    return {"id": "q1", "type": "numeric", "answer": answer, **extra}


GOLD = {"q1": ("Câu hỏi?", "Thuế suất 10% trong 15 năm.")}


def judge(provider, rows, gold=GOLD):
    return asyncio.run(judge_rows(provider, rows, gold))


def test_gold_numbers_need_every_number_as_a_whole_token():
    assert gold_numbers_present("10% trong 15 năm", "mức 10%, thời hạn 15 năm") is True
    assert gold_numbers_present("10% trong 15 năm", "mức 10%, thời hạn 150 năm") is False
    assert gold_numbers_present("1.000.000 đồng", "phạt 1.000.000 đồng") is True


def test_gold_without_numbers_has_no_number_check():
    assert gold_numbers_present("Bộ trưởng Bộ Tài chính", "Bộ Tài chính") is None


def test_verdicts_are_stored_and_summarized():
    rows = [row(), row()]
    provider = ScriptedProvider(
        '{"verdict": "correct", "reason": "khớp"}', '{"verdict": "incorrect", "reason": "sai"}'
    )

    summary = judge(provider, rows)

    assert [r["answer_verdict"] for r in rows] == ["correct", "incorrect"]
    assert summary["answer_correct_rate"] == 0.5
    assert summary["answer_incorrect"] == 1
    assert summary["gold_numbers_present_rate"] == 1.0
    assert "Thuế suất 10%" in provider.prompts[0]


def test_failed_or_invalid_judge_output_is_retried_then_counted_not_guessed():
    rows = [row()]
    provider = ScriptedProvider(ProviderError("x"), '{"verdict": "maybe"}', "không phải JSON")

    summary = judge(provider, rows)

    assert rows[0]["answer_verdict"] is None
    assert summary["judge_errors"] == 1
    assert summary["answer_correct_rate"] is None


def test_rows_without_gold_or_answer_are_not_judged():
    rows = [
        {"id": "q2", "type": "out_of_corpus", "answer": "Chưa đủ căn cứ."},
        {"id": "q1", "type": "numeric", "error": "provider"},
    ]

    summary = judge(ScriptedProvider(), rows, {"q2": ("Câu hỏi?", "")} | GOLD)

    assert all("answer_verdict" not in r for r in rows)
    assert summary["answer_judged"] == 0
