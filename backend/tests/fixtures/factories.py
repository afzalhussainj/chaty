"""Minimal ORM-like objects for unit tests (avoid full DB when only attributes matter)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.enums import SourceStatus, SourceType
from app.models.extracted import ExtractedDocument
from app.models.source import Source


def make_source(
    *,
    id: int = 1,
    tenant_id: int = 1,
    url: str = "https://example.com/",
    canonical_url: str | None = None,
    source_type: SourceType = SourceType.html_page,
    status: SourceStatus = SourceStatus.discovered,
) -> Source:
    return Source(
        id=id,
        tenant_id=tenant_id,
        url=url,
        canonical_url=canonical_url or url,
        source_type=source_type,
        status=status,
    )


def make_extracted_document(
    *,
    id: int = 1,
    tenant_id: int = 1,
    source_id: int = 1,
    source_snapshot_id: int = 1,
    extraction_hash: str = "hash_a",
    indexed_extraction_hash: str | None = None,
    full_text: str = "## Section\nbody",
) -> ExtractedDocument:
    return ExtractedDocument(
        id=id,
        tenant_id=tenant_id,
        source_id=source_id,
        source_snapshot_id=source_snapshot_id,
        extraction_hash=extraction_hash,
        indexed_extraction_hash=indexed_extraction_hash,
        full_text=full_text,
        created_at=datetime.now(timezone.utc),
    )
