"""Admin browse schemas for sources and extraction inspection."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import SourceStatus, SourceType


class SourceSummaryResponse(BaseModel):
    id: int
    tenant_id: int
    crawl_config_id: int | None
    url: str
    canonical_url: str
    title: str | None
    source_type: SourceType
    status: SourceStatus
    is_active: bool
    content_hash: str | None
    last_crawled_at: datetime | None
    last_indexed_at: datetime | None

    model_config = {"from_attributes": True}


class ChunkInspectItem(BaseModel):
    id: int
    chunk_index: int
    heading: str | None
    page_number: int | None
    content: str = Field(description="Truncated chunk text for admin inspection.")


class ExtractedDocumentInspectResponse(BaseModel):
    id: int
    source_id: int
    source_snapshot_id: int
    title: str | None
    language: str | None
    page_count: int | None
    extraction_hash: str | None
    indexed_extraction_hash: str | None
    indexed_at: datetime | None
    full_text_preview: str | None = Field(
        default=None,
        description="Start of extracted full text (truncated).",
    )
    extraction_metadata: dict[str, Any] | None = None


class SourceExtractionInspectResponse(BaseModel):
    source: SourceSummaryResponse
    document: ExtractedDocumentInspectResponse | None
    chunks: list[ChunkInspectItem]
    chunk_total: int
    chunk_limit: int
    chunk_offset: int


class RetryExtractionResponse(BaseModel):
    ok: bool = True
    source_type: SourceType
    extracted_document_id: int
