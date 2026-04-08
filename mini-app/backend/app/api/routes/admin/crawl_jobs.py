"""Crawl job administration (queue background crawl runs)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request, status

from app.api.deps import SessionDep
from app.auth.deps import CurrentAdminDep, TenantReaderDep
from app.schemas.crawl_job import CrawlJobCreate, CrawlJobResponse
from app.services import crawl_job_service

router = APIRouter(prefix="/tenants/{tenant_id}/crawl-jobs", tags=["admin-crawl-jobs"])


@router.get("", response_model=list[CrawlJobResponse])
def list_crawl_jobs(
    tenant_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CrawlJobResponse]:
    return crawl_job_service.list_jobs(session, tenant_id, actor, limit=limit, offset=offset)


@router.post("", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
def create_crawl_job(
    tenant_id: int,
    body: CrawlJobCreate,
    session: SessionDep,
    actor: CurrentAdminDep,
    request: Request,
) -> CrawlJobResponse:
    return crawl_job_service.create_job(session, tenant_id, body, actor, request)


@router.get("/{job_id}", response_model=CrawlJobResponse)
def get_crawl_job(
    tenant_id: int,
    job_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
) -> CrawlJobResponse:
    return crawl_job_service.get_job(session, tenant_id, job_id, actor)
