"""Index job lifecycle: running, success/failure, stats (retry-safe)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.indexing.embeddings import EmbeddingGenerator
from app.indexing.indexing_service import IndexOutcome, index_extracted_document
from app.models.enums import IndexJobType, JobStatus, SourceStatus
from app.models.job import IndexJob
from app.models.source import Source


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_index_job(
    session: Session,
    index_job_id: int,
    *,
    force: bool = False,
    embedding_generator: EmbeddingGenerator | None = None,
) -> IndexOutcome:
    """
    Run indexing for `IndexJob.extracted_document_id` with a savepoint so failures
    roll back chunk writes while still recording job + source status.
    """
    job = session.get(IndexJob, index_job_id)
    if job is None:
        msg = "Index job not found"
        raise ValueError(msg)
    if job.extracted_document_id is None:
        msg = "Index job has no extracted_document_id"
        raise ValueError(msg)

    job.status = JobStatus.running
    job.started_at = _utcnow()
    job.error_message = None
    session.flush()

    try:
        with session.begin_nested():
            outcome = index_extracted_document(
                session,
                job.extracted_document_id,
                force=force,
                embedding_generator=embedding_generator,
                index_job=job,
            )
        job.status = JobStatus.succeeded
        job.completed_at = _utcnow()
        job.error_message = None
        return outcome
    except Exception as exc:
        job.status = JobStatus.failed
        job.completed_at = _utcnow()
        job.error_message = str(exc)[:8000]
        if job.source_id is not None:
            src = session.get(Source, job.source_id)
            if src is not None:
                src.status = SourceStatus.failed
        raise exc


def create_index_job_for_document(
    session: Session,
    *,
    tenant_id: int,
    source_id: int,
    extracted_document_id: int,
    job_type: IndexJobType = IndexJobType.incremental_document,
) -> IndexJob:
    """Create a queued index job row (caller commits)."""
    job = IndexJob(
        tenant_id=tenant_id,
        source_id=source_id,
        extracted_document_id=extracted_document_id,
        job_type=job_type,
        status=JobStatus.queued,
    )
    session.add(job)
    session.flush()
    return job
