"""HTML extraction API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractHtmlRequest(BaseModel):
    force: bool = Field(
        default=False,
        description="Re-run extractor even when raw bytes match the latest snapshot.",
    )


class ExtractHtmlResponse(BaseModel):
    extracted_document_id: int
    source_snapshot_id: int
    title: str | None
    language: str | None
    extraction_hash: str | None

    model_config = {"from_attributes": True}
