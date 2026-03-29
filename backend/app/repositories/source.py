"""Source persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source


class SourceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_canonical(self, tenant_id: int, canonical_url: str) -> Source | None:
        stmt = select(Source).where(
            Source.tenant_id == tenant_id,
            Source.canonical_url == canonical_url,
        )
        return self._session.scalars(stmt).first()

    def add(self, entity: Source) -> Source:
        self._session.add(entity)
        self._session.flush()
        return entity
