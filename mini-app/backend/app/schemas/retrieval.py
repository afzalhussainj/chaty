"""Retrieval API schemas (admin debug)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import SourceType


class RetrievalFilterParams(BaseModel):
    source_ids: list[int] | None = None
    source_types: list[SourceType] | None = None
    page_number: int | None = Field(default=None, ge=1)


class RetrievalDebugRequest(BaseModel):
    query: str = Field(min_length=1, max_length=16000)
    top_k: int | None = Field(default=None, ge=1, le=100)
    vector_pool: int | None = Field(default=None, ge=1, le=500)
    fts_pool: int | None = Field(default=None, ge=1, le=500)
    filters: RetrievalFilterParams | None = None


class RetrievedChunkResponse(BaseModel):
    chunk_id: int
    score: float
    vector_score_norm: float
    fts_score_norm: float
    content: str
    source_id: int
    source_type: SourceType
    extracted_document_id: int
    title: str | None
    heading: str | None
    page_number: int | None
    source_url: str | None
    content_hash: str
    indexed_at: datetime | None


class RetrievalDebugResponse(BaseModel):
    query_normalized: str
    vector_candidates: int
    fts_candidates: int
    weight_vector: float
    weight_fts: float
    chunks: list[RetrievedChunkResponse]
    extras: dict[str, Any] = Field(default_factory=dict)
