"""Tenant chat (RAG); not under /admin — separate from retrieval debug."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep
from app.auth.deps import TenantReaderDep
from app.auth.rbac import can_read_tenant
from app.schemas.chat_query import ChatQueryRequest, ChatQueryResponse
from app.services.chat_query_service import execute_chat_query

router = APIRouter(prefix="/tenants/{tenant_id}/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryResponse)
def post_chat_query(
    tenant_id: int,
    body: ChatQueryRequest,
    session: SessionDep,
    actor: TenantReaderDep,
) -> ChatQueryResponse:
    if not can_read_tenant(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return execute_chat_query(session, tenant_id, body)
