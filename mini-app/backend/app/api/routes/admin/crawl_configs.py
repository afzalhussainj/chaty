"""Crawl configuration administration (scoped under a tenant)."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.api.deps import SessionDep
from app.auth.deps import CurrentAdminDep, TenantReaderDep
from app.schemas.crawl_config import CrawlConfigCreate, CrawlConfigResponse, CrawlConfigUpdate
from app.services import crawl_config_service

router = APIRouter(prefix="/tenants/{tenant_id}/crawl-configs", tags=["admin-crawl-configs"])


@router.get("", response_model=list[CrawlConfigResponse])
def list_crawl_configs(
    tenant_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
) -> list[CrawlConfigResponse]:
    return crawl_config_service.list_configs(session, tenant_id, actor)


@router.post("", response_model=CrawlConfigResponse, status_code=status.HTTP_201_CREATED)
def create_crawl_config(
    tenant_id: int,
    body: CrawlConfigCreate,
    session: SessionDep,
    actor: CurrentAdminDep,
    request: Request,
) -> CrawlConfigResponse:
    return crawl_config_service.create_config(session, tenant_id, body, actor, request)


@router.get("/{config_id}", response_model=CrawlConfigResponse)
def get_crawl_config(
    tenant_id: int,
    config_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
) -> CrawlConfigResponse:
    return crawl_config_service.get_config(session, tenant_id, config_id, actor)


@router.patch("/{config_id}", response_model=CrawlConfigResponse)
def update_crawl_config(
    tenant_id: int,
    config_id: int,
    body: CrawlConfigUpdate,
    session: SessionDep,
    actor: CurrentAdminDep,
    request: Request,
) -> CrawlConfigResponse:
    return crawl_config_service.update_config(session, tenant_id, config_id, body, actor, request)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crawl_config(
    tenant_id: int,
    config_id: int,
    session: SessionDep,
    actor: CurrentAdminDep,
    request: Request,
) -> Response:
    crawl_config_service.delete_config(session, tenant_id, config_id, actor, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
