"""Extracted document persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.extracted import ExtractedDocument


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
