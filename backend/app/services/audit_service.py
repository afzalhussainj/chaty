"""Write audit log entries for admin actions."""

from __future__ import annotations

import ipaddress
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.admin import AuditLog
from app.models.enums import AuditAction
from app.repositories.audit_log import AuditLogRepository


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    raw = forwarded.split(",")[0].strip() if forwarded else None
    if raw is None and request.client:
        raw = request.client.host
    if raw is None:
        return None
    try:
        return str(ipaddress.ip_address(raw.split("%")[0]))
    except ValueError:
        return None


def write_audit(
    session: Session,
    *,
    admin_user_id: int | None,
    tenant_id: int | None,
    action: AuditAction,
    resource_type: str,
    resource_id: str,
    details: dict[str, Any] | None,
    request: Request,
) -> None:
    merged: dict[str, Any] = dict(details) if details else {}
    rid = getattr(request.state, "request_id", None)
    if rid and "request_id" not in merged:
        merged["request_id"] = rid

    repo = AuditLogRepository(session)
    entry = AuditLog(
        tenant_id=tenant_id,
        admin_user_id=admin_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=merged if merged else None,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    repo.add(entry)
