"""Extracted document persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.extracted import ExtractedDocument
from app.models.source import SourceSnapshot


class ExtractedDocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_snapshot_id(self, source_snapshot_id: int) -> ExtractedDocument | None:
        stmt = select(ExtractedDocument).where(
            ExtractedDocument.source_snapshot_id == source_snapshot_id,
        )
        return self._session.scalars(stmt).first()

    def add(self, row: ExtractedDocument) -> ExtractedDocument:
        self._session.add(row)
        self._session.flush()
        return row

    def latest_for_source(self, source_id: int) -> ExtractedDocument | None:
        """Latest extracted document for a source (highest snapshot version)."""
        stmt = (
            select(ExtractedDocument)
            .join(SourceSnapshot, ExtractedDocument.source_snapshot_id == SourceSnapshot.id)
            .where(ExtractedDocument.source_id == source_id)
            .order_by(SourceSnapshot.version.desc())
            .limit(1)
        )
        return self._session.scalars(stmt).first()
