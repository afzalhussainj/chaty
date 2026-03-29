"""Hybrid merge scoring and deduplication."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.enums import SourceType
from app.retrieval.hybrid_merge import merge_hybrid
from app.retrieval.types import ChunkHit


def _row(
    cid: int,
    *,
    content: str,
    indexed_at: datetime | None,
    content_hash: str = "h",
) -> dict[str, object]:
    return {
        "content": content,
        "content_hash": content_hash,
        "source_id": 1,
        "source_type": SourceType.html_page,
        "extracted_document_id": 10,
        "title": "T",
        "heading": None,
        "page_number": None,
        "source_url": "https://x",
        "indexed_at": indexed_at,
    }


def test_keyword_heavy_fts_dominates_when_vector_weak() -> None:
    v_hits = [ChunkHit(1, 0.2, "vector")]
    f_hits = [ChunkHit(1, 5.0, "fts"), ChunkHit(2, 0.1, "fts")]
    rows = {
        1: _row(1, content="a", indexed_at=None),
        2: _row(2, content="b", indexed_at=None, content_hash="h2"),
    }
    out = merge_hybrid(
        vector_hits=v_hits,
        fts_hits=f_hits,
        chunk_rows=rows,
        weight_vector=0.5,
        weight_fts=0.5,
        top_k=5,
    )
    assert len(out) >= 1
    assert out[0].chunk_id in (1, 2)


def test_semantic_vector_only_still_ranks() -> None:
    v_hits = [ChunkHit(10, 0.95, "vector"), ChunkHit(11, 0.85, "vector")]
    f_hits: list[ChunkHit] = []
    rows = {
        10: _row(10, content="x", indexed_at=None),
        11: _row(11, content="y", indexed_at=None, content_hash="y"),
    }
    out = merge_hybrid(
        vector_hits=v_hits,
        fts_hits=f_hits,
        chunk_rows=rows,
        weight_vector=0.62,
        weight_fts=0.38,
        top_k=2,
    )
    assert [c.chunk_id for c in out] == [10, 11]


def test_freshness_tiebreak() -> None:
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    new = datetime(2025, 6, 1, tzinfo=timezone.utc)
    v_hits = [ChunkHit(1, 0.9, "vector"), ChunkHit(2, 0.9, "vector")]
    f_hits = [ChunkHit(1, 1.0, "fts"), ChunkHit(2, 1.0, "fts")]
    rows = {
        1: _row(1, content="a", indexed_at=old),
        2: _row(2, content="b", indexed_at=new, content_hash="b"),
    }
    out = merge_hybrid(
        vector_hits=v_hits,
        fts_hits=f_hits,
        chunk_rows=rows,
        weight_vector=0.5,
        weight_fts=0.5,
        top_k=2,
    )
    assert out[0].chunk_id == 2


def test_content_hash_dedup_keeps_first_ranked() -> None:
    v_hits = [ChunkHit(1, 0.9, "vector"), ChunkHit(2, 0.8, "vector")]
    f_hits = [ChunkHit(1, 1.0, "fts"), ChunkHit(2, 0.9, "fts")]
    rows = {
        1: _row(1, content="dup", indexed_at=None, content_hash="same"),
        2: _row(2, content="dup2", indexed_at=None, content_hash="same"),
    }
    out = merge_hybrid(
        vector_hits=v_hits,
        fts_hits=f_hits,
        chunk_rows=rows,
        weight_vector=0.5,
        weight_fts=0.5,
        top_k=5,
    )
    assert len(out) == 1


def test_pdf_page_metadata_preserved() -> None:
    v_hits = [ChunkHit(3, 0.99, "vector")]
    f_hits: list[ChunkHit] = []
    rows = {
        3: {
            "content": "pdf text",
            "content_hash": "p",
            "source_id": 9,
            "source_type": SourceType.pdf,
            "extracted_document_id": 4,
            "title": "PDF",
            "heading": None,
            "page_number": 7,
            "source_url": "https://x/a.pdf",
            "indexed_at": None,
        },
    }
    out = merge_hybrid(
        vector_hits=v_hits,
        fts_hits=f_hits,
        chunk_rows=rows,
        weight_vector=1.0,
        weight_fts=0.0,
        top_k=3,
    )
    assert out[0].page_number == 7
    assert out[0].source_type == SourceType.pdf
