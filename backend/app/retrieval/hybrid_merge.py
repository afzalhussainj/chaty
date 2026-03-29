"""Merge vector and FTS legs with simple weighted fusion + freshness tie-break."""

from __future__ import annotations

from datetime import datetime

from app.models.enums import SourceType
from app.retrieval.types import ChunkHit, RetrievedChunk


def _min_max_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return [1.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def cosine_distance_to_similarity(dist: float) -> float:
    """pgvector `<=>` is cosine distance; map to a similarity-ish [0, 1]."""
    # Cosine distance in [0, 2] for unit vectors; similarity = 1 - d/2
    s = 1.0 - min(max(dist, 0.0), 2.0) / 2.0
    return max(0.0, min(1.0, s))


def merge_hybrid(
    *,
    vector_hits: list[ChunkHit],
    fts_hits: list[ChunkHit],
    chunk_rows: dict[int, dict[str, object]],
    weight_vector: float,
    weight_fts: float,
    top_k: int,
) -> tuple[RetrievedChunk, ...]:
    """
    Reciprocal-style fusion on normalized scores, then sort by:
    combined score desc, `indexed_at` desc (freshness), `chunk_id` desc (stable).

    `chunk_rows` maps chunk_id -> keys: content, source_id, source_type, extracted_document_id,
    title, heading, page_number, source_url, content_hash, indexed_at (datetime|None).
    """
    by_id: dict[int, dict[str, float]] = {}
    for h in vector_hits:
        cur = by_id.setdefault(h.chunk_id, {"v": 0.0, "f": 0.0})
        cur["v"] = max(cur["v"], float(h.score_raw))
    for h in fts_hits:
        cur = by_id.setdefault(h.chunk_id, {"v": 0.0, "f": 0.0})
        cur["f"] = max(cur["f"], float(h.score_raw))

    ids = list(by_id.keys())
    v_raw = [by_id[i]["v"] for i in ids]
    f_raw = [by_id[i]["f"] for i in ids]
    if max(v_raw, default=0.0) < 1e-12:
        v_norm = [0.0 for _ in v_raw]
    else:
        v_norm = _min_max_norm(v_raw)
    if max(f_raw, default=0.0) < 1e-12:
        f_norm = [0.0 for _ in f_raw]
    else:
        f_norm = _min_max_norm(f_raw)

    combined: list[tuple[int, float, float, float]] = []
    for idx, cid in enumerate(ids):
        nv = v_norm[idx]
        nf = f_norm[idx]
        comb = weight_vector * nv + weight_fts * nf
        combined.append((cid, comb, nv, nf))

    def sort_key(t: tuple[int, float, float, float]) -> tuple[float, float, int]:
        cid, comb, _, _ = t
        row = chunk_rows.get(cid) or {}
        idx_at = row.get("indexed_at")
        ts = idx_at.timestamp() if isinstance(idx_at, datetime) else 0.0
        return (comb, ts, cid)

    combined.sort(key=sort_key, reverse=True)

    out: list[RetrievedChunk] = []
    seen_hash: set[str] = set()
    for cid, comb, nv, nf in combined:
        row = chunk_rows.get(cid)
        if row is None:
            continue
        ch = str(row.get("content_hash") or "")
        if ch and ch in seen_hash:
            continue
        if ch:
            seen_hash.add(ch)
        st = row.get("source_type")
        if not isinstance(st, SourceType):
            st = SourceType.html_page
        title = row.get("title")
        heading = row.get("heading")
        surl = row.get("source_url")
        idx_at = row.get("indexed_at")
        out.append(
            RetrievedChunk(
                chunk_id=cid,
                content=str(row.get("content") or ""),
                score=comb,
                vector_score_norm=nv,
                fts_score_norm=nf,
                source_id=int(row["source_id"]),
                source_type=st,
                extracted_document_id=int(row["extracted_document_id"]),
                title=title if isinstance(title, str) else None,
                heading=heading if isinstance(heading, str) else None,
                page_number=int(row["page_number"]) if row.get("page_number") is not None else None,
                source_url=surl if isinstance(surl, str) else None,
                content_hash=ch,
                indexed_at=idx_at if isinstance(idx_at, datetime) else None,
            ),
        )
        if len(out) >= top_k:
            break

    return tuple(out)
