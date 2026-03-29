"""Public (non-admin-debug) chat query API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SourceType


class ChatRetrievalFiltersBody(BaseModel):
    source_ids: list[int] | None = None
    source_types: list[SourceType] | None = None
    page_number: int | None = Field(default=None, ge=1)


class ChatQueryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=8000)
    session_id: int | None = Field(
        default=None,
        description="Continue an existing thread; omit to start new.",
    )
    answer_mode: Literal["concise", "detailed"] = "concise"
    stream: bool = False
    """Reserved; streaming is not implemented yet."""
    top_k: int | None = Field(default=None, ge=1, le=32)
    filters: ChatRetrievalFiltersBody | None = None


class CitationResponse(BaseModel):
    chunk_id: int
    source_id: int
    title: str | None
    url: str | None
    source_type: SourceType
    page_number: int | None
    score: float


class ChatQueryResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    support: str
    """Model-reported grounding strength: high | partial | none."""
    session_id: int
    retrieval: dict[str, Any]
    """Counts and normalized query only (no prompts or raw context)."""
