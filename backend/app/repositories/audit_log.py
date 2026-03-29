"""Audit log persistence."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.admin import AuditLog


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: AuditLog) -> AuditLog:
        self._session.add(entry)
        self._session.flush()
        return entry
