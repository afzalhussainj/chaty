"""Sync all sources under a crawl config (extract + queue index; index skips unchanged)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crawler.engine import CrawlRunResult
from app.crawler.types import CrawlStats
from app.models.enums import SourceType
from app.models.job import CrawlJob
from app.models.source import Source
from app.services.html_extraction_service import extract_html_source
from app.services.pdf_extraction_service import extract_pdf_source


def execute_sync_changed_job(session: Session, job: CrawlJob) -> CrawlRunResult:
    """
    Re-fetch and extract each **active** HTML/PDF source for the job's crawl config.

    Does not run the BFS crawler. Queues `index.extracted_document` per extraction; the
    indexer skips when `extraction_hash` is unchanged (no chunk/embedding churn).
    """
    if job.crawl_config_id is None:
        msg = "sync_changed job requires crawl_config_id"
        raise ValueError(msg)

    stats = CrawlStats()
    errors: list[dict[str, object]] = []

    stmt = (
        select(Source)
        .where(
            Source.tenant_id == job.tenant_id,
            Source.crawl_config_id == job.crawl_config_id,
            Source.is_active.is_(True),
            Source.source_type.in_((SourceType.html_page, SourceType.pdf)),
        )
        .order_by(Source.id)
    )
    sources = list(session.scalars(stmt).all())
    stats.extras["sync_sources_total"] = len(sources)

    from app.workers.tasks.index import index_extracted_document_task

    index_enqueued = 0
    for src in sources:
        try:
            if src.source_type == SourceType.html_page:
                doc = extract_html_source(session, src.id)
            else:
                doc = extract_pdf_source(session, src.id)
            session.flush()
            index_extracted_document_task.delay(doc.id)
            index_enqueued += 1
        except Exception as exc:  # noqa: BLE001 — aggregate per-source failures
            errors.append({"source_id": src.id, "error": str(exc)[:2000]})

    stats.extras["sync_index_tasks_enqueued"] = index_enqueued
    stats.extras["sync_errors"] = errors
    return CrawlRunResult(stats=stats, dry_run_records=[])
