"""Read-only audit log listing."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.rbac import can_manage_tenants, can_read_tenant
from app.models.admin import AdminUser, AuditLog
from app.repositories.audit_log import AuditLogRepository
from app.schemas.audit_api import AuditLogEntryResponse


def _entry_to_response(entry: AuditLog) -> AuditLogEntryResponse:
    ip = entry.ip_address
    ip_str = str(ip) if ip is not None else None
    return AuditLogEntryResponse(
        id=entry.id,
        tenant_id=entry.tenant_id,
        admin_user_id=entry.admin_user_id,
        action=entry.action,
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        details=entry.details,
        ip_address=ip_str,
        user_agent=entry.user_agent,
        created_at=entry.created_at,
    )


def list_tenant_audit_logs(
    session: Session,
    tenant_id: int,
    actor: AdminUser,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLogEntryResponse]:
    if not can_read_tenant(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = AuditLogRepository(session)
    entries = repo.list_for_tenant(tenant_id, limit=limit, offset=offset)
    return [_entry_to_response(e) for e in entries]


def list_audit_logs_super(
    session: Session,
    actor: AdminUser,
    *,
    tenant_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLogEntryResponse]:
    if not can_manage_tenants(actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = AuditLogRepository(session)
    entries = repo.list_all(tenant_id=tenant_id, limit=limit, offset=offset)
    return [_entry_to_response(e) for e in entries]
