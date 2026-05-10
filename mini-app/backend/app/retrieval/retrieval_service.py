"""Hybrid retrieval: pgvector + PostgreSQL FTS with tenant isolation."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session

from app.indexing.embeddings import EmbeddingGenerator, OpenAIEmbeddingGenerator
from app.models.extracted import DocumentChunk, ExtractedDocument
from app.models.source import Source
from app.retrieval.config import load_retrieval_config
from app.retrieval.hybrid_merge import cosine_distance_to_similarity, merge_hybrid
from app.retrieval.query_preprocess import fts_query_text, normalize_query
from app.retrieval.types import ChunkHit, HybridRetrievalResult, Reranker, RetrievalFilters


def _narrow_source_filters_for_tenant(
    session: Session,
    tenant_id: int,
    flt: RetrievalFilters,
) -> RetrievalFilters | None:
    """
    Restrict ``source_ids`` to rows owned by ``tenant_id``.

    Returns ``None`` when the caller asked for specific sources but none belong to
    this tenant (retrieve nothing — avoids widening scope to the full tenant).
    """
    if not flt.source_ids:
        return flt
    requested = tuple(dict.fromkeys(flt.source_ids))
    stmt = select(Source.id).where(
        Source.tenant_id == tenant_id,
        Source.id.in_(requested),
    )
    valid = {int(x) for x in session.scalars(stmt).all()}
    ordered = tuple(sid for sid in requested if sid in valid)
    if not ordered:
        return None
    if ordered != requested:
        return replace(flt, source_ids=ordered)
    return flt


def _apply_filters(
    stmt: Any,
    *,
    filters: RetrievalFilters,
) -> Any:
    if filters.source_ids:
        stmt = stmt.where(DocumentChunk.source_id.in_(filters.source_ids))
    if filters.source_types:
        stmt = stmt.where(Source.source_type.in_(tuple(filters.source_types)))
    if filters.page_number is not None:
        stmt = stmt.where(DocumentChunk.page_number == filters.page_number)
    return stmt


def _vector_search(
    session: Session,
    *,
    tenant_id: int,
    query_embedding: list[float],
    filters: RetrievalFilters,
    limit: int,
) -> list[ChunkHit]:
    dist_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(DocumentChunk.id, dist_expr.label("dist"))
        .join(Source, Source.id == DocumentChunk.source_id)
        .join(ExtractedDocument, ExtractedDocument.id == DocumentChunk.extracted_document_id)
        .where(DocumentChunk.tenant_id == tenant_id)
        .where(Source.tenant_id == tenant_id)
        .where(Source.is_active.is_(True))
    )
    if filters.require_embedding:
        stmt = stmt.where(DocumentChunk.embedding.isnot(None))
    stmt = _apply_filters(stmt, filters=filters)
    stmt = stmt.order_by(dist_expr.asc()).limit(limit)
    rows = session.execute(stmt).all()
    out: list[ChunkHit] = []
    for cid, dist in rows:
        sim = cosine_distance_to_similarity(float(dist))
        out.append(ChunkHit(chunk_id=int(cid), score_raw=sim, leg="vector"))
    return out


def _fts_search(
    session: Session,
    *,
    tenant_id: int,
    fts_text: str,
    filters: RetrievalFilters,
    limit: int,
) -> list[ChunkHit]:
    tsv = literal_column("document_chunks.content_tsv")
    # Must be a string literal in SQL — unquoted `simple` is parsed as a column name.
    tsq = func.plainto_tsquery(literal_column("'simple'::regconfig"), fts_text)
    rank = func.ts_rank_cd(tsv, tsq)
    stmt = (
        select(DocumentChunk.id, rank.label("rk"))
        .join(Source, Source.id == DocumentChunk.source_id)
        .join(ExtractedDocument, ExtractedDocument.id == DocumentChunk.extracted_document_id)
        .where(DocumentChunk.tenant_id == tenant_id)
        .where(Source.tenant_id == tenant_id)
        .where(Source.is_active.is_(True))
        .where(tsv.op("@@")(tsq))
    )
    stmt = _apply_filters(stmt, filters=filters)
    stmt = stmt.order_by(rank.desc()).limit(limit)
    rows = session.execute(stmt).all()
    return [
        ChunkHit(chunk_id=int(cid), score_raw=float(rk), leg="fts")
        for cid, rk in rows
    ]


def _load_chunk_rows(
    session: Session,
    *,
    tenant_id: int,
    chunk_ids: set[int],
) -> dict[int, dict[str, object]]:
    if not chunk_ids:
        return {}
    stmt = (
        select(DocumentChunk, Source, ExtractedDocument)
        .join(Source, Source.id == DocumentChunk.source_id)
        .join(ExtractedDocument, ExtractedDocument.id == DocumentChunk.extracted_document_id)
        .where(DocumentChunk.tenant_id == tenant_id)
        .where(Source.tenant_id == tenant_id)
        .where(ExtractedDocument.tenant_id == tenant_id)
        .where(DocumentChunk.id.in_(chunk_ids))
    )
    rows = session.execute(stmt).all()
    out: dict[int, dict[str, object]] = {}
    for dc, src, ex in rows:
        out[int(dc.id)] = {
            "content": dc.content,
            "content_hash": dc.content_hash,
            "source_id": int(src.id),
            "source_type": src.source_type,
            "extracted_document_id": int(ex.id),
            "title": dc.title or ex.title,
            "heading": dc.heading,
            "page_number": dc.page_number,
            "source_url": dc.source_url,
            "indexed_at": ex.indexed_at,
        }
    return out


def retrieve_hybrid(
    session: Session,
    *,
    tenant_id: int,
    query: str,
    filters: RetrievalFilters | None = None,
    embedding_generator: EmbeddingGenerator | None = None,
    reranker: Reranker | None = None,
    top_k: int | None = None,
    vector_pool: int | None = None,
    fts_pool: int | None = None,
) -> HybridRetrievalResult:
    """
    Tenant-scoped hybrid retrieval. Requires PostgreSQL (pgvector + FTS).

    Optional ``reranker`` receives merged candidates and may shrink/reorder (future).
    """
    cfg = load_retrieval_config(top_k=top_k, vector_pool=vector_pool, fts_pool=fts_pool)
    flt = filters or RetrievalFilters()
    qn = normalize_query(query, max_chars=cfg.max_query_chars)
    if not qn.strip():
        return HybridRetrievalResult(
            chunks=(),
            query_normalized="",
            vector_candidates=0,
            fts_candidates=0,
            weights=(cfg.weight_vector, cfg.weight_fts),
        )

    narrowed = _narrow_source_filters_for_tenant(session, tenant_id, flt)
    if narrowed is None:
        return HybridRetrievalResult(
            chunks=(),
            query_normalized=qn,
            vector_candidates=0,
            fts_candidates=0,
            weights=(cfg.weight_vector, cfg.weight_fts),
        )
    flt = narrowed

    gen = embedding_generator or OpenAIEmbeddingGenerator()
    qvec = gen.embed_batch([qn])[0]

    v_hits = _vector_search(
        session,
        tenant_id=tenant_id,
        query_embedding=qvec,
        filters=flt,
        limit=cfg.vector_pool,
    )
    fts_q = fts_query_text(qn)
    f_hits = _fts_search(
        session,
        tenant_id=tenant_id,
        fts_text=fts_q,
        filters=flt,
        limit=cfg.fts_pool,
    )

    ids = {h.chunk_id for h in v_hits} | {h.chunk_id for h in f_hits}
    chunk_rows = _load_chunk_rows(session, tenant_id=tenant_id, chunk_ids=ids)

    merged = merge_hybrid(
        vector_hits=v_hits,
        fts_hits=f_hits,
        chunk_rows=chunk_rows,
        weight_vector=cfg.weight_vector,
        weight_fts=cfg.weight_fts,
        top_k=cfg.top_k,
    )
    if reranker is not None:
        merged = reranker.rerank(qn, merged, top_k=cfg.top_k)

    return HybridRetrievalResult(
        chunks=merged,
        query_normalized=qn,
        vector_candidates=len(v_hits),
        fts_candidates=len(f_hits),
        weights=(cfg.weight_vector, cfg.weight_fts),
    )
