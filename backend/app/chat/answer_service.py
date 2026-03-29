"""RAG answer orchestration: retrieve → OpenAI Responses → citations + persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.chat.citation_formatter import CitationPayload, citations_for_display
from app.chat.context_formatter import build_user_message, format_context_blocks
from app.chat.openai_responses import create_response_with_schema_fallback, parse_model_json
from app.chat.prompt_builder import RAG_RESPONSE_JSON_SCHEMA, build_grounded_instructions
from app.core.settings import get_settings
from app.indexing.embeddings import OpenAIEmbeddingGenerator
from app.models.enums import ChatRole
from app.repositories.chat import ChatMessageRepository, ChatSessionRepository
from app.retrieval.retrieval_service import retrieve_hybrid
from app.retrieval.types import RetrievalFilters

AnswerMode = Literal["concise", "detailed"]


@dataclass(frozen=True, slots=True)
class ChatAnswerResult:
    answer: str
    citations: tuple[CitationPayload, ...]
    support: str
    session_id: int
    retrieval: dict[str, Any]


def _coerce_support(raw: object) -> str:
    s = str(raw or "").lower()
    if s in ("high", "partial", "none"):
        return s
    return "none"


def generate_chat_answer(
    db: Session,
    *,
    tenant_id: int,
    user_message: str,
    session_id: int | None,
    answer_mode: AnswerMode,
    retrieval_filters: RetrievalFilters | None = None,
    top_k: int | None = None,
) -> ChatAnswerResult:
    settings = get_settings()
    if not settings.openai_api_key:
        msg = "Chat is not configured (missing OPENAI_API_KEY)"
        raise RuntimeError(msg)

    sess_repo = ChatSessionRepository(db)
    msg_repo = ChatMessageRepository(db)

    if session_id is not None:
        chat_sess = sess_repo.get(session_id, tenant_id)
        if chat_sess is None:
            msg = "Chat session not found"
            raise ValueError(msg)
    else:
        chat_sess = sess_repo.create(tenant_id, title=None)

    seq = sess_repo.next_sequence(chat_sess.id)
    msg_repo.add(
        tenant_id=tenant_id,
        session_id=chat_sess.id,
        role=ChatRole.user,
        content=user_message.strip(),
        sequence=seq,
    )

    k = top_k if top_k is not None else settings.chat_retrieval_top_k
    retrieval = retrieve_hybrid(
        db,
        tenant_id=tenant_id,
        query=user_message,
        filters=retrieval_filters,
        embedding_generator=OpenAIEmbeddingGenerator(),
        top_k=k,
    )

    ctx_block, idx_map = format_context_blocks(retrieval.chunks)
    user_payload = build_user_message(
        user_question=user_message,
        context_block=ctx_block,
        answer_mode=answer_mode,
    )
    instructions = build_grounded_instructions(answer_mode)

    _raw, out_text = create_response_with_schema_fallback(
        api_key=settings.openai_api_key,
        model=settings.openai_chat_model,
        instructions=instructions,
        user_text=user_payload,
        timeout_s=settings.chat_openai_timeout_s,
        json_schema=RAG_RESPONSE_JSON_SCHEMA,
    )

    try:
        parsed = parse_model_json(out_text)
    except json.JSONDecodeError as exc:
        msg = "Model returned invalid JSON"
        raise RuntimeError(msg) from exc

    answer = str(parsed.get("answer") or "").strip()
    cited = parsed.get("cited_chunk_indices")
    if not isinstance(cited, list):
        cited = []
    cited_ints: list[int] = []
    for x in cited:
        if isinstance(x, int):
            cited_ints.append(x)
        elif isinstance(x, str) and x.strip().isdigit():
            cited_ints.append(int(x))
    support = _coerce_support(parsed.get("support"))

    if not retrieval.chunks and support != "none":
        support = "none"
        if not answer:
            answer = (
                "I could not find relevant information in the indexed content for your question. "
                "Try rephrasing or check back after more site content has been indexed."
            )

    max_ctx = len(retrieval.chunks)
    if max_ctx > 0:
        cited_ints = [i for i in cited_ints if 1 <= i <= max_ctx]

    cite_objs = citations_for_display(
        chunks_by_index=idx_map,
        cited_indices=cited_ints,
        fallback_chunks=retrieval.chunks,
    )

    trace = {
        "chunk_ids": [c.chunk_id for c in retrieval.chunks],
        "vector_candidates": retrieval.vector_candidates,
        "fts_candidates": retrieval.fts_candidates,
        "support": support,
        "cited_chunk_indices": cited_ints,
        "weights": {"vector": retrieval.weights[0], "fts": retrieval.weights[1]},
    }

    aseq = sess_repo.next_sequence(chat_sess.id)
    msg_repo.add(
        tenant_id=tenant_id,
        session_id=chat_sess.id,
        role=ChatRole.assistant,
        content=answer,
        sequence=aseq,
        retrieval_trace=trace,
    )

    if chat_sess.title is None and user_message.strip():
        chat_sess.title = user_message.strip()[:120]

    return ChatAnswerResult(
        answer=answer,
        citations=tuple(cite_objs),
        support=support,
        session_id=int(chat_sess.id),
        retrieval={
            "chunks_returned": len(retrieval.chunks),
            "vector_candidates": retrieval.vector_candidates,
            "fts_candidates": retrieval.fts_candidates,
            "query_normalized": retrieval.query_normalized,
        },
    )
