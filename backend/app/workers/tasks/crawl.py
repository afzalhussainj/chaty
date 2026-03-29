"""Celery tasks for crawl pipeline."""

from __future__ import annotations

from app.db.session import SessionLocal, get_engine
from app.services.crawl_execution_service import run_job_to_completion
from app.workers.celery_app import celery_app


@celery_app.task(name="crawl.run_job")
def run_crawl_job_task(job_id: int) -> None:
    session = SessionLocal(bind=get_engine())
    try:
        run_job_to_completion(session, job_id)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
