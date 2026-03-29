"""Celery tasks for HTML extraction."""

from __future__ import annotations

from app.db.session import SessionLocal, get_engine
from app.models.enums import SourceStatus
from app.models.source import Source
from app.services.html_extraction_service import extract_html_source
from app.workers.celery_app import celery_app


@celery_app.task(name="extract.html_source")
def extract_html_source_task(source_id: int) -> dict[str, int | None]:
    session = SessionLocal(bind=get_engine())
    doc_id: int | None = None
    try:
        doc = extract_html_source(session, source_id)
        session.commit()
        doc_id = doc.id
    except Exception:
        session.rollback()
        _mark_failed(source_id)
        raise
    finally:
        session.close()
    if doc_id is not None:
        from app.workers.tasks.index import index_extracted_document_task

        index_extracted_document_task.delay(doc_id)
    return {"extracted_document_id": doc_id}


def _mark_failed(source_id: int) -> None:
    s = SessionLocal(bind=get_engine())
    try:
        src = s.get(Source, source_id)
        if src is not None:
            src.status = SourceStatus.extraction_failed
            s.commit()
    finally:
        s.close()
