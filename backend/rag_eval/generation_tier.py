"""Generation tier: retrieve, answer with the real prompt, score citations and references.

Refusals on out-of-corpus questions are not scored here: a person fills `refused` in the result
file (true/false), and the export computes the rate once every row has an answer.
"""

import asyncio
import time

from app.services.chat.citations import select_cited
from app.services.chat.prompt import prompt_with_context
from app.services.chat.provider import ModelProvider, ProviderError, ProviderMessage
from app.services.chat.retriever import RetrievalResult
from app.services.rag.retrieve.qdrant_retriever import Hit, QdrantRetriever, hits_to_result
from rag_eval import metrics
from rag_eval.dataset import Question
from rag_eval.provenance import corpus_documents
from rag_eval.reference_check import (
    Source,
    check_references,
    find_doc_numbers,
    normalize_doc_number,
)
from rag_eval.runner import EvalConfig, gold_articles, hit_articles


def _error_name(error: ProviderError) -> str:
    """Class of the underlying failure (never its message, which may quote the prompt)."""
    return type(error.__cause__ or error).__name__


async def _answer(provider: ModelProvider, question: str, result: RetrievalResult, max_tokens: int):
    started, first, text, usage = time.perf_counter(), None, "", (None, None)
    truncated, stream_error = False, None
    try:
        async for event in provider.stream(
            [ProviderMessage("user", question)], prompt_with_context(result), max_tokens
        ):
            if event.kind == "delta":
                first = first or time.perf_counter()
                text += event.text
            else:
                usage = (event.input_tokens, event.output_tokens)
                truncated = event.truncated
    except ProviderError as error:
        if not text:  # nothing to score
            raise
        truncated, stream_error = True, _error_name(error)  # score what arrived
    end = time.perf_counter()
    timing = ((first or end) - started) * 1000, (end - started) * 1000
    return text, *timing, usage, truncated, stream_error


def _source(hit: Hit) -> Source:
    payload = hit.payload
    return Source(
        payload.get("doc_number", ""),
        tuple(payload.get("article_nos", [])),
        f"{payload.get('heading_path', '')}\n{payload.get('content', '')}",
    )


def _reference_fields(
    config: EvalConfig, question: str, text: str, hits: list[Hit], corpus_numbers: set[str]
) -> dict:
    refs = check_references(text, [_source(hit) for hit in hits], question)
    known = corpus_numbers | {normalize_doc_number(n) for n in find_doc_numbers(question)}
    # Without retrieval there is no source to be supported by, so "unsupported" is undefined.
    return {
        "references": {"docs": refs.doc_numbers, "articles": refs.articles},
        "unsupported_reference": refs.unsupported if config.rag else None,
        "unsupported": {
            "docs": refs.unsupported_doc_numbers if config.rag else [],
            "articles": refs.unsupported_articles if config.rag else [],
        },
        "needs_review": refs.needs_review,
        # Comparable with and without RAG; a real document outside the corpus counts too.
        "unknown_docs": [n for n in refs.doc_numbers if normalize_doc_number(n) not in known],
    }


async def _one(
    config, retriever, provider, q: Question, max_tokens: int, corpus_numbers: set[str]
) -> dict:
    hits, retrieval_ms, plan_ms, result = [], 0.0, 0.0, RetrievalResult()
    if config.rag:
        started = time.perf_counter()
        outcome = await retriever.search(q.question)
        retrieval_ms = (time.perf_counter() - started) * 1000  # planner and rerank included
        plan_ms = outcome.plan_info.get("plan_ms", 0.0)
        hits = outcome.hits
        result = hits_to_result(hits)
    try:
        text, ttft_ms, total_ms, (tokens_in, tokens_out), truncated, stream_error = await _answer(
            provider, q.question, result, max_tokens
        )
    except ProviderError as error:
        return {"id": q.id, "type": q.type, "error": _error_name(error)}

    selection = select_cited(result, text)
    by_id = {c.id: hit_articles(h.payload) for c, h in zip(result.citations, hits)}
    cited = set().union(*(by_id[c.id] for c in selection.cited)) if selection.cited else set()
    row = {
        "id": q.id, "type": q.type, "field": q.field, "n_cited": len(selection.cited),
        "unknown_markers": len(selection.unknown_markers),
        **_reference_fields(config, q.question, text, hits, corpus_numbers),
        "retrieved": [
            {"id": h.id, "doc_number": h.payload.get("doc_number"),
             "article_nos": h.payload.get("article_nos", [])}
            for h in hits
        ],
        "retrieval_ms": retrieval_ms, "plan_ms": plan_ms, "ttft_ms": ttft_ms,
        "total_ms": total_ms, "end_to_end_ms": retrieval_ms + total_ms,
        "truncated": truncated,
        "input_tokens": tokens_in, "output_tokens": tokens_out, "answer": text,
    }  # fmt: skip
    if stream_error:
        row["stream_error"] = stream_error
    if q.type == "out_of_corpus":
        row["refused"] = None  # filled in by a person
    else:
        row["citation_precision"], row["citation_recall"] = metrics.citation_precision_recall(
            cited, gold_articles(q)
        )
    return row


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if "error" not in r]
    in_rows = [r for r in ok if r["type"] != "out_of_corpus"]
    ooc = [r for r in ok if r["type"] == "out_of_corpus"]
    supported = [r["unsupported_reference"] for r in ok if r["unsupported_reference"] is not None]
    return {
        "answered": len(ok),
        "provider_errors": len(rows) - len(ok),
        "truncated_answers": sum(r["truncated"] for r in ok),
        "citation_precision": metrics.mean(r["citation_precision"] for r in in_rows),
        "citation_recall": metrics.mean(r["citation_recall"] for r in in_rows),
        "answers_without_citation": sum(r["n_cited"] == 0 for r in in_rows),
        "unsupported_reference_rate": sum(supported) / len(supported) if supported else None,
        "unknown_doc_rate": sum(bool(r["unknown_docs"]) for r in ok) / len(ok) if ok else None,
        "answers_needing_review": sum(bool(r["needs_review"]) for r in ok),
        "ooc_no_citation_rate": sum(r["n_cited"] == 0 for r in ooc) / len(ooc) if ooc else None,
        **{
            name: metrics.latency_summary([r[name] for r in ok])
            for name in ("retrieval_ms", "plan_ms", "ttft_ms", "total_ms", "end_to_end_ms")
        },
        "input_tokens": sum(r["input_tokens"] or 0 for r in ok),
        "output_tokens": sum(r["output_tokens"] or 0 for r in ok),
    }


async def run_generation_tier(
    config: EvalConfig, retriever: QdrantRetriever, provider, questions, max_tokens: int,
    concurrency: int = 3,
):  # fmt: skip
    gate = asyncio.Semaphore(concurrency)
    numbers = {normalize_doc_number(d.number) for d in corpus_documents(config.chunk_set)}

    async def guarded(q):
        async with gate:
            return await _one(config, retriever, provider, q, max_tokens, numbers)

    rows = await asyncio.gather(*(guarded(q) for q in questions))
    return summarize(rows), rows
