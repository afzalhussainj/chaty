"""Orchestrate chunking, embeddings, and persistence for one extracted document."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.indexing.chunker import chunk_extracted_document
from app.indexing.embeddings import EmbeddingGenerator, OpenAIEmbeddingGenerator
from app.indexing.persistence import delete_chunks_for_document, replace_chunks
from app.models.enums import SourceStatus
from app.models.extracted import DocumentChunk, ExtractedDocument
from app.models.job import IndexJob
from app.models.source import Source
from app.repositories.extracted_document import ExtractedDocumentRepository


@dataclass(frozen=True, slots=True)
class IndexOutcome:
    skipped: bool
    chunk_count: int
    extraction_hash: str | None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _merge_job_stats(job: IndexJob | None, **kwargs: object) -> None:
    if job is None:
        return
    base: dict[str, object] = dict(job.stats or {})
    base.update(kwargs)
    job.stats = base


def index_extracted_document(
    session: Session,
    extracted_document_id: int,
    *,
    force: bool = False,
    embedding_generator: EmbeddingGenerator | None = None,
    index_job: IndexJob | None = None,
) -> IndexOutcome:
    """
    Chunk, embed, and persist rows for `extracted_document_id`.

    If ``force`` is False and ``indexed_extraction_hash`` equals ``extraction_hash``,
    skips work (idempotent no-op). Deletes and replaces chunks when re-indexing.
    """
    doc = session.get(ExtractedDocument, extracted_document_id)
    if doc is None:
        msg = "Extracted document not found"
        raise ValueError(msg)
    source = session.get(Source, doc.source_id)
    if source is None:
        msg = "Source not found"
        raise ValueError(msg)

    exh = doc.extraction_hash
    if exh is None:
        msg = "Extracted document has no extraction_hash; run extraction first"
        raise ValueError(msg)

    if not force and doc.indexed_extraction_hash == exh:
        existing = session.scalar(
            select(func.count()).select_from(DocumentChunk).where(
                DocumentChunk.extracted_document_id == doc.id,
            ),
        )
        _merge_job_stats(
            index_job,
            skipped=True,
            reason="extraction_hash_unchanged",
            chunk_count=int(existing or 0),
            extraction_hash=exh,
        )
        return IndexOutcome(skipped=True, chunk_count=int(existing or 0), extraction_hash=exh)

    gen = embedding_generator or OpenAIEmbeddingGenerator()

    source.status = SourceStatus.indexing
    session.flush()

    drafts = chunk_extracted_document(doc)
    texts = [d.content for d in drafts]
    headings = [d.heading for d in drafts]
    pages = [d.page_number for d in drafts]

    if not texts:
        delete_chunks_for_document(session, doc.id)
        doc.indexed_extraction_hash = exh
        doc.indexed_at = _utcnow()
        source.last_indexed_at = _utcnow()
        source.status = SourceStatus.indexed
        _merge_job_stats(
            index_job,
            skipped=False,
            chunk_count=0,
            extraction_hash=exh,
            note="no_chunks_after_chunking",
        )
        session.flush()
        return IndexOutcome(skipped=False, chunk_count=0, extraction_hash=exh)

    embeddings: list[list[float]] = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        embeddings.extend(gen.embed_batch(texts[i : i + batch_size]))

    replace_chunks(
        session,
        doc=doc,
        source=source,
        chunk_texts=texts,
        headings=headings,
        page_numbers=pages,
        embeddings=embeddings,
    )

    doc.indexed_extraction_hash = exh
    doc.indexed_at = _utcnow()
    source.last_indexed_at = _utcnow()
    source.status = SourceStatus.indexed

    _merge_job_stats(
        index_job,
        skipped=False,
        chunk_count=len(texts),
        extraction_hash=exh,
    )
    session.flush()
    return IndexOutcome(skipped=False, chunk_count=len(texts), extraction_hash=exh)


def index_source_latest(
    session: Session,
    source_id: int,
    *,
    force: bool = False,
    embedding_generator: EmbeddingGenerator | None = None,
    index_job: IndexJob | None = None,
) -> IndexOutcome:
    """Index the latest `ExtractedDocument` for `source_id` (by snapshot version)."""
    repo = ExtractedDocumentRepository(session)
    doc = repo.latest_for_source(source_id)
    if doc is None:
        msg = "No extracted document for this source"
        raise ValueError(msg)
    return index_extracted_document(
        session,
        doc.id,
        force=force,
        embedding_generator=embedding_generator,
        index_job=index_job,
    )


def index_sources(
    session: Session,
    source_ids: list[int],
    *,
    force: bool = False,
    embedding_generator: EmbeddingGenerator | None = None,
) -> dict[int, IndexOutcome | str]:
    """
    Index latest extracted document for each source id. Uses a savepoint per source so
    one failure does not roll back prior successful indexes in the same transaction.
    """
    out: dict[int, IndexOutcome | str] = {}
    for sid in source_ids:
        try:
            with session.begin_nested():
                out[sid] = index_source_latest(
                    session,
                    sid,
                    force=force,
                    embedding_generator=embedding_generator,
                    index_job=None,
                )
        except Exception as exc:  # noqa: BLE001 — aggregate errors
            out[sid] = str(exc)
    return out
