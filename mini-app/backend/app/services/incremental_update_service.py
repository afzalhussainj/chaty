"""High-level incremental operations: single URL refresh, add source, sync, full recrawl."""

from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.admin import AdminUser
from app.models.enums import CrawlJobType
from app.schemas.crawl_job import CrawlJobCreate, CrawlJobResponse
from app.services import crawl_job_service


def refresh_page_by_url(
    session: Session,
    tenant_id: int,
    crawl_config_id: int,
    url: str,
    actor: AdminUser,
    request: Request,
) -> CrawlJobResponse:
    """Queue a single-page crawl for an HTML URL (PDF URLs should use ``refresh_pdf_by_url``)."""
    body = CrawlJobCreate(
        crawl_config_id=crawl_config_id,
        job_type=CrawlJobType.incremental_url,
        seed_url=url,
        workflow="refresh_page",
    )
    return crawl_job_service.create_job(session, tenant_id, body, actor, request)


def refresh_pdf_by_url(
    session: Session,
    tenant_id: int,
    crawl_config_id: int,
    url: str,
    actor: AdminUser,
    request: Request,
) -> CrawlJobResponse:
    """Queue a single-URL fetch for a PDF resource."""
    body = CrawlJobCreate(
        crawl_config_id=crawl_config_id,
        job_type=CrawlJobType.incremental_pdf,
        seed_url=url,
        workflow="refresh_pdf",
    )
    return crawl_job_service.create_job(session, tenant_id, body, actor, request)


def add_source_url(
    session: Session,
    tenant_id: int,
    crawl_config_id: int,
    url: str,
    actor: AdminUser,
    request: Request,
) -> CrawlJobResponse:
    """Fetch one new URL; linked URLs are discovered-only until crawled separately."""
    body = CrawlJobCreate(
        crawl_config_id=crawl_config_id,
        job_type=CrawlJobType.add_source,
        seed_url=url,
        workflow="add_source",
    )
    return crawl_job_service.create_job(session, tenant_id, body, actor, request)


def sync_changed_sources(
    session: Session,
    tenant_id: int,
    crawl_config_id: int,
    actor: AdminUser,
    request: Request,
) -> CrawlJobResponse:
    """Re-fetch every active source under the config; extraction + indexing skip unchanged bytes."""
    body = CrawlJobCreate(
        crawl_config_id=crawl_config_id,
        job_type=CrawlJobType.sync_changed,
        workflow="sync_changed",
    )
    return crawl_job_service.create_job(session, tenant_id, body, actor, request)


def full_recrawl(
    session: Session,
    tenant_id: int,
    crawl_config_id: int,
    actor: AdminUser,
    request: Request,
    *,
    use_sitemap: bool = False,
) -> CrawlJobResponse:
    """Full BFS recrawl from the configured base URL."""
    body = CrawlJobCreate(
        crawl_config_id=crawl_config_id,
        job_type=CrawlJobType.full_recrawl,
        use_sitemap=use_sitemap,
        workflow="full_recrawl",
    )
    return crawl_job_service.create_job(session, tenant_id, body, actor, request)
