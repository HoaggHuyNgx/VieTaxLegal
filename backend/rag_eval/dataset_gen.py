"""Generate pending evaluation questions from corpus chunks with an LLM (human review follows).

Questions are paraphrased user-voice questions that do not name the document or article, so
retrieval is tested on meaning rather than on copied wording. Rows stay `pending` until a person
approves them with the review CLI.
"""

import asyncio
import json
import random
import re
from collections import defaultdict

from app.services.chat_provider import ModelProvider, ProviderError, ProviderMessage
from app.services.rag.chunking import ChunkDraft, article_chunks, estimate_tokens
from app.services.rag.corpus_manifest import CorpusDoc
from app.services.rag.legal_parser import parse
from rag_eval.dataset import GoldRef, Question

FIELD_QUOTAS = {"tax": 34, "labor": 20, "enterprise": 16}
MIN_TOKENS, MAX_TOKENS = 60, 450
SKIP_TITLES = re.compile(
    r"hiệu lực|điều khoản thi hành|chuyển tiếp|tổ chức thực hiện|giải thích", re.I
)
SYSTEM = """Bạn tạo câu hỏi kiểm thử cho hệ thống hỏi đáp pháp luật Việt Nam.
Chỉ trả về một đối tượng JSON: {"question": "...", "gold_answer": "...", "type": "lookup|numeric"}.
Quy tắc cho "question": văn phong người dùng thực tế (chủ doanh nghiệp, kế toán, người lao động);
diễn đạt lại bằng từ ngữ khác, không chép nguyên cụm từ trong đoạn luật; KHÔNG nêu số hiệu văn
bản, số điều, khoản; tự đủ nghĩa, không dùng "điều này", "đoạn trên".
Quy tắc cho "gold_answer": 1-3 câu, chỉ dựa vào đoạn luật được cho, không thêm kiến thức ngoài.
"type" là "numeric" nếu đáp án chủ yếu là con số/tỷ lệ/thời hạn, ngược lại là "lookup"."""
# Questions that no document in the corpus answers; success is "no citation + cannot verify".
OUT_OF_CORPUS = [
    ("Công ty tôi có nên mua bitcoin để đầu tư không?", "other"),
    ("Thủ tục ly hôn thuận tình cần những giấy tờ gì?", "other"),
    ("Mức phạt khi vượt đèn đỏ đối với xe máy là bao nhiêu?", "other"),
    ("Điều kiện để được cấp sổ đỏ cho đất nông nghiệp là gì?", "other"),
    ("Tội trốn thuế bị phạt tù tối đa bao nhiêu năm?", "tax"),
    ("Thuế nhập khẩu ô tô điện từ Trung Quốc hiện nay là bao nhiêu?", "tax"),
    ("Quy trình xin giấy phép lao động cho người nước ngoài thế nào?", "labor"),
    ("Doanh nghiệp phải làm gì khi phá sản theo Luật Phá sản?", "enterprise"),
    ("Thời hạn bảo hộ nhãn hiệu là bao lâu?", "enterprise"),
    ("Cách tính thuế thu nhập từ chuyển nhượng bất động sản ở nước ngoài?", "tax"),
]


def eligible_chunks(docs: list[CorpusDoc]) -> dict[str, list[tuple[CorpusDoc, ChunkDraft]]]:
    """Article chunks of ingestable documents, grouped by field, filtered for question quality."""
    by_field: dict[str, list[tuple[CorpusDoc, ChunkDraft]]] = defaultdict(list)
    for doc in docs:
        if not doc.ingest or doc.is_amending:
            continue
        parsed = parse(doc.text_path.read_text(encoding="utf-8"))
        titles = {a.no: a.title for a in parsed.articles}
        for chunk in article_chunks(doc, parsed):
            size = estimate_tokens(chunk.content)
            repealed = "được bãi bỏ" in chunk.content.lower()
            if MIN_TOKENS <= size <= MAX_TOKENS and not repealed:
                if not SKIP_TITLES.search(titles.get(chunk.article_no or 0, "")):
                    by_field[doc.field].append((doc, chunk))
    return by_field


def sample_chunks(by_field, quotas: dict[str, int], seed: int):
    """Stratified: per field, cycle through documents so no single document dominates."""
    rng, picked = random.Random(seed), []
    for field_name, quota in quotas.items():
        per_doc: dict[str, list] = defaultdict(list)
        for doc, chunk in by_field.get(field_name, []):
            per_doc[doc.slug].append((doc, chunk))
        for items in per_doc.values():
            rng.shuffle(items)
        order = sorted(per_doc)
        while quota > 0 and any(per_doc.values()):
            for slug in order:
                if per_doc[slug] and quota > 0:
                    picked.append(per_doc[slug].pop())
                    quota -= 1
    return picked


def copied_ngram(question: str, source: str, n: int = 5) -> bool:
    """True if the question repeats n consecutive words of the source (inflates recall)."""
    words = re.findall(r"\w+", question.lower())
    haystack = " ".join(re.findall(r"\w+", source.lower()))
    return any(" ".join(words[i : i + n]) in haystack for i in range(len(words) - n + 1))


def _parse_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        return None


async def _generate(provider: ModelProvider, doc: CorpusDoc, chunk: ChunkDraft) -> dict | None:
    prompt = f"Đoạn luật ({doc.title}):\n{chunk.content}"
    text = ""
    for _ in range(3):  # retry if the call fails or the question copies the passage wording
        text = ""
        try:
            # Generous cap: reasoning models spend output tokens before the visible answer.
            async for event in provider.stream([ProviderMessage("user", prompt)], SYSTEM, 3000):
                if event.kind == "delta":
                    text += event.text
        except ProviderError:
            continue
        data = _parse_json(text)
        if data and data.get("question") and data.get("gold_answer"):
            if not copied_ngram(data["question"], chunk.content):
                return data
    return None


async def generate_questions(
    provider: ModelProvider, docs: list[CorpusDoc], seed: int = 7, concurrency: int = 4
) -> list[Question]:
    oversampled = {name: quota * 2 for name, quota in FIELD_QUOTAS.items()}
    picks = sample_chunks(eligible_chunks(docs), oversampled, seed)
    gate = asyncio.Semaphore(concurrency)

    async def one(doc: CorpusDoc, chunk: ChunkDraft):
        async with gate:
            return doc, chunk, await _generate(provider, doc, chunk)

    questions: list[Question] = []
    kept_per_field: dict[str, int] = defaultdict(int)
    for doc, chunk, data in await asyncio.gather(*(one(d, c) for d, c in picks)):
        if not data or kept_per_field[doc.field] >= FIELD_QUOTAS[doc.field]:
            continue
        kept_per_field[doc.field] += 1
        kind = data.get("type") if data.get("type") in ("lookup", "numeric") else "lookup"
        ref = GoldRef(doc.slug, chunk.article_no or 0, chunk.clause_no)
        questions.append(
            Question(f"q{len(questions) + 1:03d}", data["question"].strip(), doc.field, kind,
                     data["gold_answer"].strip(), [ref])
        )  # fmt: skip
    for text, field_name in OUT_OF_CORPUS:
        questions.append(
            Question(f"q{len(questions) + 1:03d}", text, field_name, "out_of_corpus", "")
        )
    return questions
