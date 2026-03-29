"""Retrieval DTOs (filters, hits, pipeline hooks)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.models.enums import SourceType


@dataclass(frozen=True, slots=True)
class RetrievalFilters:
    """Optional metadata filters; all conditions are ANDed."""

    source_ids: tuple[int, ...] | None = None
    source_types: tuple[SourceType, ...] | None = None
    page_number: int | None = None
    """Exact page for PDF chunks; ignored if None."""

    require_embedding: bool = True
    """If True, vector leg requires non-null embedding (default)."""


@dataclass(slots=True)
class ChunkHit:
    """One scored chunk from a single retrieval leg (vector or FTS)."""

    chunk_id: int
    score_raw: float
    leg: str  # vector | fts


@dataclass(slots=True)
class RetrievedChunk:
    """Final ranked chunk for RAG / citations."""

    chunk_id: int
    content: str
    score: float
    vector_score_norm: float
    fts_score_norm: float
    source_id: int
    source_type: SourceType
    extracted_document_id: int
    title: str | None
    heading: str | None
    page_number: int | None
    source_url: str | None
    content_hash: str
    indexed_at: datetime | None
    extras: dict[str, Any] = field(default_factory=dict)
    """Room for future reranker scores or explainability."""


@dataclass(frozen=True, slots=True)
class HybridRetrievalResult:
    chunks: tuple[RetrievedChunk, ...]
    query_normalized: str
    vector_candidates: int
    fts_candidates: int
    weights: tuple[float, float]
    """(vector, fts) after normalization."""


class Reranker(Protocol):
    """Optional second-stage ranker (cross-encoder, LLM, etc.)."""

    def rerank(
        self,
        query: str,
        chunks: tuple[RetrievedChunk, ...],
        *,
        top_k: int,
    ) -> tuple[RetrievedChunk, ...]:
        ...
