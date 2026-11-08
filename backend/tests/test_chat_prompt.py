from app.services.chat_prompt import NO_SOURCE_RULES, SYSTEM_PROMPT, prompt_with_context
from app.services.chat_retriever import RetrievalResult, RetrievedContext


def test_searching_and_finding_nothing_forbids_answering_from_memory():
    assert prompt_with_context(RetrievalResult(searched=True)).endswith(NO_SOURCE_RULES)


def test_rag_off_keeps_the_plain_prompt():
    assert prompt_with_context(RetrievalResult()) == SYSTEM_PROMPT


def test_sources_never_get_the_no_source_rules():
    context = RetrievedContext(content="Nội dung", citation_id="1")

    prompt = prompt_with_context(RetrievalResult(contexts=[context], searched=True))

    assert NO_SOURCE_RULES not in prompt and '<reference id="1">' in prompt
