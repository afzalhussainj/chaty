"""Source persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import SourceStatus, SourceType
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

    def get_for_tenant(self, source_id: int, tenant_id: int) -> Source | None:
        stmt = select(Source).where(Source.id == source_id, Source.tenant_id == tenant_id)
        return self._session.scalars(stmt).first()

    def add(self, entity: Source) -> Source:
        self._session.add(entity)
        self._session.flush()
        return entity

    def list_for_tenant(
        self,
        tenant_id: int,
        *,
        source_type: SourceType | None = None,
        status: SourceStatus | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Source]:
        stmt = select(Source).where(Source.tenant_id == tenant_id)
        if source_type is not None:
            stmt = stmt.where(Source.source_type == source_type)
        if status is not None:
            stmt = stmt.where(Source.status == status)
        if is_active is not None:
            stmt = stmt.where(Source.is_active == is_active)
        stmt = stmt.order_by(Source.id.desc()).limit(limit).offset(offset)
        return list(self._session.scalars(stmt).all())
