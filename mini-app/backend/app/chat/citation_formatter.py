"""Build API-safe citation objects from retrieved chunks."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import SourceType
from app.retrieval.types import RetrievedChunk


@dataclass(frozen=True, slots=True)
class CitationPayload:
    chunk_id: int
    source_id: int
    title: str | None
    url: str | None
    source_type: SourceType
    page_number: int | None
    score: float


def citations_for_display(
    *,
    chunks_by_index: dict[int, RetrievedChunk],
    cited_indices: list[int],
    fallback_chunks: tuple[RetrievedChunk, ...],
) -> list[CitationPayload]:
    """
    Prefer model-cited indices; if empty but chunks exist, fall back to top retrieved chunks.

    Deduplicates by chunk_id preserving first occurrence order.
    """
    ordered_ids: list[int] = []
    seen: set[int] = set()

    for idx in cited_indices:
        ch = chunks_by_index.get(idx)
        if ch is None:
            continue
        if ch.chunk_id in seen:
            continue
        seen.add(ch.chunk_id)
        ordered_ids.append(ch.chunk_id)

    if not ordered_ids and fallback_chunks:
        for ch in fallback_chunks:
            if ch.chunk_id not in seen:
                seen.add(ch.chunk_id)
                ordered_ids.append(ch.chunk_id)

    id_to_chunk: dict[int, RetrievedChunk] = {c.chunk_id: c for c in fallback_chunks}
    for ch in chunks_by_index.values():
        id_to_chunk[ch.chunk_id] = ch
    out: list[CitationPayload] = []
    for cid in ordered_ids:
        ch = id_to_chunk.get(cid)
        if ch is None:
            continue
        out.append(
            CitationPayload(
                chunk_id=ch.chunk_id,
                source_id=ch.source_id,
                title=ch.title,
                url=ch.source_url,
                source_type=ch.source_type,
                page_number=ch.page_number,
                score=ch.score,
            ),
        )
    return out
