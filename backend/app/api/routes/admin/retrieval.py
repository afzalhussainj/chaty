"""Admin debug retrieval (hybrid search)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep
from app.auth.deps import TenantReaderDep
from app.auth.rbac import can_read_crawl_config
from app.retrieval.retrieval_service import retrieve_hybrid
from app.retrieval.types import RetrievalFilters
from app.schemas.retrieval import (
    RetrievalDebugRequest,
    RetrievalDebugResponse,
    RetrievedChunkResponse,
)

router = APIRouter(prefix="/tenants/{tenant_id}/retrieval", tags=["admin-retrieval"])


@router.post("/debug", response_model=RetrievalDebugResponse, status_code=status.HTTP_200_OK)
def post_retrieval_debug(
    tenant_id: int,
    body: RetrievalDebugRequest,
    session: SessionDep,
    actor: TenantReaderDep,
) -> RetrievalDebugResponse:
    """
    Run hybrid retrieval for debugging (tenant-isolated).

    Requires PostgreSQL with pgvector + FTS; returns fused scores per chunk.
    """
    if not can_read_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    flt: RetrievalFilters | None = None
    if body.filters is not None:
        f = body.filters
        st = tuple(f.source_types) if f.source_types else None
        sids = tuple(f.source_ids) if f.source_ids else None
        flt = RetrievalFilters(
            source_ids=sids,
            source_types=st,
            page_number=f.page_number,
        )
    result = retrieve_hybrid(
        session,
        tenant_id=tenant_id,
        query=body.query,
        filters=flt,
        top_k=body.top_k,
        vector_pool=body.vector_pool,
        fts_pool=body.fts_pool,
    )
    chunks = [
        RetrievedChunkResponse(
            chunk_id=c.chunk_id,
            score=c.score,
            vector_score_norm=c.vector_score_norm,
            fts_score_norm=c.fts_score_norm,
            content=c.content,
            source_id=c.source_id,
            source_type=c.source_type,
            extracted_document_id=c.extracted_document_id,
            title=c.title,
            heading=c.heading,
            page_number=c.page_number,
            source_url=c.source_url,
            content_hash=c.content_hash,
            indexed_at=c.indexed_at,
        )
        for c in result.chunks
    ]
    return RetrievalDebugResponse(
        query_normalized=result.query_normalized,
        vector_candidates=result.vector_candidates,
        fts_candidates=result.fts_candidates,
        weight_vector=result.weights[0],
        weight_fts=result.weights[1],
        chunks=chunks,
    )
