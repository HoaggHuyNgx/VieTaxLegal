import asyncio
import json

import pytest

from app.services.chat.provider import ProviderError
from rag_eval.faithfulness import check_rows, source_texts
from tests.eval.test_answer_judge import ScriptedProvider
from tests.eval.test_runner import CHUNKS, COLLECTION, _retriever


def _row(qid: str, answer: str) -> dict:
    return {"id": qid, "answer": answer}


def _check(provider, rows, sources):
    return asyncio.run(check_rows(provider, rows, sources, concurrency=1))


def _reply(*claims: tuple[str, str]) -> str:
    return json.dumps(
        {"claims": [{"quote": quote, "label": label} for quote, label in claims]},
        ensure_ascii=False,
    )


def test_claims_are_counted_and_answers_with_an_unbacked_one_flagged():
    answer = "Mức a [1]. **Mức b**.\n- Mức c;\n- Mức d."
    rows = [_row("q1", answer), _row("q2", "Chưa đủ căn cứ."), {"id": "q3", "error": "x"}]
    provider = ScriptedProvider(
        _reply(
            ("Mức a", "supported"),
            ("Mức b", "unsupported"),
            ("mức c", "contradicted"),
            ("Mức d.", "supported"),
        ),  # fmt: skip
        '{"claims": []}',  # a refusal states nothing to check
    )

    summary = _check(provider, rows, {"q1": ["Điều 1"], "q2": ["Điều 2"]})

    assert summary["faithfulness_checked"] == 2 and summary["faithfulness_errors"] == 0
    assert summary["claims"] == 4 and summary["claims_supported_rate"] == 0.5
    assert summary["claims_unsupported"] == 1 and summary["claims_contradicted"] == 1
    assert summary["answers_with_unbacked_claim"] == 1
    assert rows[0]["claims"][1] == {"quote": "Mức b", "label": "unsupported"}
    assert "Điều 1" in provider.prompts[0] and "Mức a" in provider.prompts[0]
    assert "claims" not in rows[2]


def test_a_claim_that_is_not_in_the_answer_is_rejected():
    """The checker once rewrote a wrong "507 triệu" as the source's "500 triệu" and passed it."""
    rows = [_row("q1", "Doanh thu từ 507 triệu đồng trở xuống.")]
    corrected = _reply(("Doanh thu từ 500 triệu đồng trở xuống", "supported"))
    honest = _reply(("Doanh thu từ 507 triệu đồng trở xuống", "contradicted"))

    summary = _check(ScriptedProvider(corrected, honest), rows, {"q1": ["500 triệu"]})

    assert summary["claims_contradicted"] == 1 and summary["claims"] == 1


def test_unreadable_reply_is_retried_then_counted_not_guessed():
    rows = [_row("q1", "Trả lời")]
    provider = ScriptedProvider(_reply(("Trả lời", "maybe")), "không phải JSON", ProviderError("x"))

    summary = _check(provider, rows, {"q1": ["Điều 1"]})

    assert rows[0]["claims"] is None
    assert summary["faithfulness_errors"] == 1 and summary["faithfulness_checked"] == 0
    assert summary["claims_supported_rate"] is None


def test_source_texts_rebuild_what_the_model_read_in_the_stored_order():
    retrieved = [
        {"id": CHUNKS[2].id, "article_nos": [3]},
        {"id": CHUNKS[0].id, "article_nos": [1]},
    ]

    async def run(items):
        retriever = await _retriever()
        return await source_texts(retriever._client, COLLECTION, retriever, items, expand=True)

    texts = asyncio.run(run(retrieved))

    assert [text.splitlines()[-1] for text in texts] == ["Nội dung điều 3", "Nội dung điều 1"]
    assert texts[0].startswith("Bộ luật Lao động > Điều 3\n")  # same format as the prompt
    gone = [{"id": "00000000-0000-0000-0000-000000000000", "article_nos": [1]}]
    with pytest.raises(ValueError, match="no longer"):
        asyncio.run(run(gone))
    changed = [{"id": CHUNKS[0].id, "article_nos": [9]}]
    with pytest.raises(ValueError, match="no longer"):
        asyncio.run(run(changed))
