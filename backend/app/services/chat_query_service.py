"""Shared chat query execution (admin JWT and public slug routes)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.chat.answer_service import generate_chat_answer
from app.retrieval.types import RetrievalFilters
from app.schemas.chat_query import ChatQueryRequest, ChatQueryResponse, CitationResponse


def execute_chat_query(
    session: Session,
    tenant_id: int,
    body: ChatQueryRequest,
) -> ChatQueryResponse:
    if body.stream:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Streaming is not implemented yet.",
        )

    flt: RetrievalFilters | None = None
    if body.filters is not None:
        f = body.filters
        st = tuple(f.source_types) if f.source_types else None
        sids = tuple(f.source_ids) if f.source_ids else None
        flt = RetrievalFilters(source_ids=sids, source_types=st, page_number=f.page_number)

    try:
        result = generate_chat_answer(
            session,
            tenant_id=tenant_id,
            user_message=body.message,
            session_id=body.session_id,
            answer_mode=body.answer_mode,
            retrieval_filters=flt,
            top_k=body.top_k,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    citations = [
        CitationResponse(
            chunk_id=c.chunk_id,
            source_id=c.source_id,
            title=c.title,
            url=c.url,
            source_type=c.source_type,
            page_number=c.page_number,
            score=c.score,
        )
        for c in result.citations
    ]
    support = result.support if result.support in ("high", "partial", "none") else "none"
    return ChatQueryResponse(
        answer=result.answer,
        citations=citations,
        support=support,
        session_id=result.session_id,
        retrieval=result.retrieval,
    )
