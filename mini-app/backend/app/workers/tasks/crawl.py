"""Celery tasks for crawl pipeline."""

from __future__ import annotations

from app.db.session import SessionLocal, get_engine
from app.services.crawl_execution_service import run_job_to_completion
from app.services.post_crawl_extraction import queue_extractions_after_crawl_job
from app.workers.celery_app import celery_app


@celery_app.task(name="crawl.run_job")
def run_crawl_job_task(job_id: int) -> None:
    """
    Run a crawl job to completion. Not auto-retried at the Celery layer: full crawls are
    long-running and should be re-queued explicitly after fixing upstream issues.
    """
    session = SessionLocal(bind=get_engine())
    try:
        ok = run_job_to_completion(session, job_id)
        session.commit()
        if ok:
            queue_extractions_after_crawl_job(job_id)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
