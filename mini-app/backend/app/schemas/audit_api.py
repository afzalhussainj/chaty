"""Audit log listing for admin UI."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import AuditAction


class AuditLogEntryResponse(BaseModel):
    id: int
    tenant_id: int | None
    admin_user_id: int | None
    action: AuditAction
    resource_type: str
    resource_id: str
    details: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
