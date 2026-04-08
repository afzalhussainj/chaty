"""Audit log read API (tenant-scoped and super-admin global)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.auth.deps import SuperAdminDep, TenantReaderDep
from app.schemas.audit_api import AuditLogEntryResponse
from app.services import audit_list_service

router = APIRouter(tags=["admin-audit"])


@router.get("/tenants/{tenant_id}/audit-logs", response_model=list[AuditLogEntryResponse])
def list_tenant_audit_logs(
    tenant_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogEntryResponse]:
    return audit_list_service.list_tenant_audit_logs(
        session,
        tenant_id,
        actor,
        limit=limit,
        offset=offset,
    )


@router.get("/audit-logs", response_model=list[AuditLogEntryResponse])
def list_audit_logs_global(
    session: SessionDep,
    actor: SuperAdminDep,
    tenant_id: Annotated[int | None, Query(description="Filter by tenant id")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogEntryResponse]:
    return audit_list_service.list_audit_logs_super(
        session,
        actor,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
