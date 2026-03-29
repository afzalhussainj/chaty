"""Celery tasks for chunking + embedding index pipeline."""

from __future__ import annotations

from app.db.session import SessionLocal, get_engine
from app.indexing.embeddings import OpenAIEmbeddingGenerator
from app.indexing.index_job_service import create_index_job_for_document, run_index_job
from app.indexing.indexing_service import index_source_latest, index_sources
from app.models.extracted import ExtractedDocument
from app.workers.celery_app import celery_app


@celery_app.task(
    name="index.extracted_document",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 30},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def index_extracted_document_task(
    extracted_document_id: int,
    index_job_id: int | None = None,
    *,
    force: bool = False,
) -> dict[str, object]:
    """
    Index one extracted document. Creates an `IndexJob` when `index_job_id` is omitted.
    Persists failed job state on error, then re-raises for Celery retry/monitoring.
    """
    session = SessionLocal(bind=get_engine())
    gen = OpenAIEmbeddingGenerator()
    try:
        jid = index_job_id
        if jid is None:
            doc = session.get(ExtractedDocument, extracted_document_id)
            if doc is None:
                return {"ok": False, "error": "extracted_document_not_found"}
            job = create_index_job_for_document(
                session,
                tenant_id=doc.tenant_id,
                source_id=doc.source_id,
                extracted_document_id=extracted_document_id,
            )
            session.flush()
            jid = job.id

        try:
            outcome = run_index_job(session, jid, force=force, embedding_generator=gen)
        except Exception:
            session.commit()
            raise
        session.commit()
        return {
            "ok": True,
            "index_job_id": jid,
            "skipped": outcome.skipped,
            "chunk_count": outcome.chunk_count,
        }
    finally:
        session.close()


@celery_app.task(name="index.source")
def index_source_task(source_id: int, *, force: bool = False) -> dict[str, object]:
    """Index the latest extracted document for a single source (no IndexJob row)."""
    session = SessionLocal(bind=get_engine())
    gen = OpenAIEmbeddingGenerator()
    try:
        outcome = index_source_latest(session, source_id, force=force, embedding_generator=gen)
        session.commit()
        return {"ok": True, "source_id": source_id, **outcome.__dict__}
    except Exception as exc:
        session.rollback()
        return {"ok": False, "source_id": source_id, "error": str(exc)}
    finally:
        session.close()


@celery_app.task(name="index.sources")
def index_sources_task(source_ids: list[int], *, force: bool = False) -> dict[str, object]:
    """Index many sources; per-source outcomes (continues on errors)."""
    session = SessionLocal(bind=get_engine())
    gen = OpenAIEmbeddingGenerator()
    try:
        raw = index_sources(session, source_ids, force=force, embedding_generator=gen)
        session.commit()
        return {"ok": True, "results": {str(k): v for k, v in raw.items()}}
    except Exception as exc:
        session.rollback()
        return {"ok": False, "error": str(exc)}
    finally:
        session.close()
