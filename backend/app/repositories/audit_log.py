"""Audit log persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import AuditLog


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: AuditLog) -> AuditLog:
        self._session.add(entry)
        self._session.flush()
        return entry

    def list_for_tenant(
        self,
        tenant_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt).all())

    def list_all(
        self,
        *,
        tenant_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        stmt = select(AuditLog)
        if tenant_id is not None:
            stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        stmt = stmt.order_by(AuditLog.id.desc()).limit(limit).offset(offset)
        return list(self._session.scalars(stmt).all())
