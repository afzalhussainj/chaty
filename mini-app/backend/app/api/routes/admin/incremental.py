"""Incremental crawl/sync endpoints (single URL, add source, sync, full recrawl)."""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.api.deps import SessionDep
from app.auth.deps import TenantAdminDep
from app.schemas.crawl_job import CrawlJobResponse
from app.schemas.incremental import (
    AddSourceRequest,
    FullRecrawlRequest,
    RefreshUrlRequest,
    SyncChangedRequest,
)
from app.services import incremental_update_service

router = APIRouter(prefix="/tenants/{tenant_id}/incremental", tags=["admin-incremental"])


@router.post("/refresh-page", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
def post_refresh_page(
    tenant_id: int,
    body: RefreshUrlRequest,
    session: SessionDep,
    actor: TenantAdminDep,
    request: Request,
) -> CrawlJobResponse:
    """Re-crawl one HTML page; extract/index only for sources touched by this job."""
    return incremental_update_service.refresh_page_by_url(
        session,
        tenant_id,
        body.crawl_config_id,
        str(body.url),
        actor,
        request,
    )


@router.post("/refresh-pdf", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
def post_refresh_pdf(
    tenant_id: int,
    body: RefreshUrlRequest,
    session: SessionDep,
    actor: TenantAdminDep,
    request: Request,
) -> CrawlJobResponse:
    """Re-fetch one PDF by URL."""
    return incremental_update_service.refresh_pdf_by_url(
        session,
        tenant_id,
        body.crawl_config_id,
        str(body.url),
        actor,
        request,
    )


@router.post("/add-source", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
def post_add_source(
    tenant_id: int,
    body: AddSourceRequest,
    session: SessionDep,
    actor: TenantAdminDep,
    request: Request,
) -> CrawlJobResponse:
    """Add a single URL under the crawl config without running a full-site crawl."""
    return incremental_update_service.add_source_url(
        session,
        tenant_id,
        body.crawl_config_id,
        str(body.url),
        actor,
        request,
    )


@router.post("/sync-changed", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
def post_sync_changed(
    tenant_id: int,
    body: SyncChangedRequest,
    session: SessionDep,
    actor: TenantAdminDep,
    request: Request,
) -> CrawlJobResponse:
    """Re-extract every active source; index tasks skip when fingerprints are unchanged."""
    return incremental_update_service.sync_changed_sources(
        session,
        tenant_id,
        body.crawl_config_id,
        actor,
        request,
    )


@router.post("/full-recrawl", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
def post_full_recrawl(
    tenant_id: int,
    body: FullRecrawlRequest,
    session: SessionDep,
    actor: TenantAdminDep,
    request: Request,
) -> CrawlJobResponse:
    """Full BFS recrawl from the configured base URL."""
    return incremental_update_service.full_recrawl(
        session,
        tenant_id,
        body.crawl_config_id,
        actor,
        request,
        use_sitemap=body.use_sitemap,
    )
