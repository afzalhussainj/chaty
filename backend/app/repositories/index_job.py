"""Index job persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import IndexJob


class IndexJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_tenant(
        self,
        tenant_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IndexJob]:
        stmt = (
            select(IndexJob)
            .where(IndexJob.tenant_id == tenant_id)
            .order_by(IndexJob.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt).all())
