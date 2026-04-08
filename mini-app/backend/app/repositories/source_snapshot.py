"""Source snapshot persistence."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.source import SourceSnapshot


class SourceSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def latest_for_source(self, source_id: int) -> SourceSnapshot | None:
        stmt = (
            select(SourceSnapshot)
            .where(SourceSnapshot.source_id == source_id)
            .order_by(SourceSnapshot.version.desc())
            .limit(1)
        )
        return self._session.scalars(stmt).first()

    def next_version(self, source_id: int) -> int:
        stmt = select(func.coalesce(func.max(SourceSnapshot.version), 0)).where(
            SourceSnapshot.source_id == source_id,
        )
        v = self._session.scalar(stmt)
        return int(v or 0) + 1

    def add(self, snap: SourceSnapshot) -> SourceSnapshot:
        self._session.add(snap)
        self._session.flush()
        return snap
