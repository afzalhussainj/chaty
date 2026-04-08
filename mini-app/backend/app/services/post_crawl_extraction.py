"""Queue HTML + PDF extraction tasks after a successful crawl job."""

from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal, get_engine
from app.models.enums import CrawlJobType, JobStatus, SourceType
from app.models.job import CrawlJob
from app.models.source import Source
from app.workers.tasks.extract import extract_html_source_task
from app.workers.tasks.extract_pdf import extract_pdf_source_task


def queue_extractions_after_crawl_job(job_id: int) -> dict[str, int]:
    """
    Enqueue extraction Celery tasks for HTML and PDF sources touched by the crawl.

    Returns counts per kind. No-op if job missing, not succeeded, or dry-run.
    """
    session = SessionLocal(bind=get_engine())
    html_ids: list[int] = []
    pdf_ids: list[int] = []
    try:
        job = session.get(CrawlJob, job_id)
        if job is None or job.status != JobStatus.succeeded:
            return {"html": 0, "pdf": 0}
        stats = job.stats or {}
        if stats.get("dry_run"):
            return {"html": 0, "pdf": 0}
        if job.job_type == CrawlJobType.sync_changed:
            return {"html": 0, "pdf": 0, "note": "sync_changed uses inline extract/index"}
        if job.crawl_config_id is None:
            return {"html": 0, "pdf": 0}

        touched = stats.get("touched_source_ids")
        if isinstance(touched, list) and len(touched) > 0:
            ids = []
            for x in touched:
                try:
                    ids.append(int(x))
                except (TypeError, ValueError):
                    continue
            if not ids:
                html_ids = []
                pdf_ids = []
            else:
                rows = session.execute(
                    select(Source.id, Source.source_type).where(
                        Source.id.in_(ids),
                        Source.tenant_id == job.tenant_id,
                    ),
                ).all()
                html_ids = [int(r[0]) for r in rows if r[1] == SourceType.html_page]
                pdf_ids = [int(r[0]) for r in rows if r[1] == SourceType.pdf]
        else:
            base_filters = (
                Source.tenant_id == job.tenant_id,
                Source.crawl_config_id == job.crawl_config_id,
                Source.last_crawled_at.isnot(None),
            )
            time_filter = ()
            if job.started_at is not None:
                time_filter = (Source.last_crawled_at >= job.started_at,)

            stmt_html = select(Source.id).where(
                *base_filters,
                Source.source_type == SourceType.html_page,
                *time_filter,
            )
            stmt_pdf = select(Source.id).where(
                *base_filters,
                Source.source_type == SourceType.pdf,
                *time_filter,
            )

            html_ids = [int(x) for x in session.scalars(stmt_html)]
            pdf_ids = [int(x) for x in session.scalars(stmt_pdf)]
    finally:
        session.close()

    for sid in html_ids:
        extract_html_source_task.delay(sid)
    for sid in pdf_ids:
        extract_pdf_source_task.delay(sid)

    return {"html": len(html_ids), "pdf": len(pdf_ids)}
