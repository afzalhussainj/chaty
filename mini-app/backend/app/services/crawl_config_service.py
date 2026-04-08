"""Crawl configuration business logic."""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.auth.rbac import can_read_crawl_config, can_write_crawl_config
from app.core.exceptions import NotFoundError
from app.models.admin import AdminUser
from app.models.crawl_config import CrawlConfig
from app.models.enums import AuditAction
from app.models.tenant import Tenant
from app.repositories.crawl_config import CrawlConfigRepository
from app.schemas.crawl_config import CrawlConfigCreate, CrawlConfigResponse, CrawlConfigUpdate
from app.services.audit_service import write_audit


def list_configs(session: Session, tenant_id: int, actor: AdminUser) -> list[CrawlConfigResponse]:
    if not can_read_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = CrawlConfigRepository(session)
    return [CrawlConfigResponse.from_model(c) for c in repo.list_for_tenant(tenant_id)]


def get_config(
    session: Session,
    tenant_id: int,
    config_id: int,
    actor: AdminUser,
) -> CrawlConfigResponse:
    if not can_read_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = CrawlConfigRepository(session)
    cfg = repo.get(config_id, tenant_id)
    if cfg is None:
        raise NotFoundError("Crawl configuration not found")
    return CrawlConfigResponse.from_model(cfg)


def _apply_create(tenant_id: int, data: CrawlConfigCreate) -> CrawlConfig:
    return CrawlConfig(
        tenant_id=tenant_id,
        name=data.name,
        base_url=str(data.base_url),
        is_active=data.is_active,
        max_depth=data.max_depth,
        max_pages=data.max_pages,
        respect_robots_txt=data.respect_robots_txt,
        user_agent=data.user_agent,
        allow_pdf_crawling=data.allow_pdf_crawling,
        allow_js_rendering=data.allow_js_rendering,
        crawl_frequency=data.crawl_frequency,
        allowed_hosts=data.allowed_hosts or None,
        path_prefixes=data.include_path_rules or None,
        exclude_globs=data.exclude_path_rules or None,
        extras=data.extras,
    )


def create_config(
    session: Session,
    tenant_id: int,
    data: CrawlConfigCreate,
    actor: AdminUser,
    request: Request,
) -> CrawlConfigResponse:
    if not can_write_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = CrawlConfigRepository(session)
    cfg = _apply_create(tenant_id, data)
    repo.add(cfg)
    session.flush()
    write_audit(
        session,
        admin_user_id=actor.id,
        tenant_id=tenant_id,
        action=AuditAction.create,
        resource_type="CrawlConfig",
        resource_id=str(cfg.id),
        details={"name": cfg.name},
        request=request,
    )
    return CrawlConfigResponse.from_model(cfg)


def update_config(
    session: Session,
    tenant_id: int,
    config_id: int,
    data: CrawlConfigUpdate,
    actor: AdminUser,
    request: Request,
) -> CrawlConfigResponse:
    if not can_write_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = CrawlConfigRepository(session)
    cfg = repo.get(config_id, tenant_id)
    if cfg is None:
        raise NotFoundError("Crawl configuration not found")

    changed: dict = {}
    if data.name is not None:
        cfg.name = data.name
        changed["name"] = data.name
    if data.base_url is not None:
        cfg.base_url = str(data.base_url)
        changed["base_url"] = cfg.base_url
    if data.is_active is not None:
        cfg.is_active = data.is_active
        changed["is_active"] = data.is_active
    if data.max_depth is not None:
        cfg.max_depth = data.max_depth
        changed["max_depth"] = data.max_depth
    if data.max_pages is not None:
        cfg.max_pages = data.max_pages
        changed["max_pages"] = data.max_pages
    if data.respect_robots_txt is not None:
        cfg.respect_robots_txt = data.respect_robots_txt
        changed["respect_robots_txt"] = data.respect_robots_txt
    if data.user_agent is not None:
        cfg.user_agent = data.user_agent
        changed["user_agent"] = data.user_agent
    if data.allow_pdf_crawling is not None:
        cfg.allow_pdf_crawling = data.allow_pdf_crawling
        changed["allow_pdf_crawling"] = data.allow_pdf_crawling
    if data.allow_js_rendering is not None:
        cfg.allow_js_rendering = data.allow_js_rendering
        changed["allow_js_rendering"] = data.allow_js_rendering
    if data.crawl_frequency is not None:
        cfg.crawl_frequency = data.crawl_frequency
        changed["crawl_frequency"] = data.crawl_frequency.value
    if data.allowed_hosts is not None:
        cfg.allowed_hosts = data.allowed_hosts
        changed["allowed_hosts"] = data.allowed_hosts
    if data.include_path_rules is not None:
        cfg.path_prefixes = data.include_path_rules
        changed["include_path_rules"] = data.include_path_rules
    if data.exclude_path_rules is not None:
        cfg.exclude_globs = data.exclude_path_rules
        changed["exclude_path_rules"] = data.exclude_path_rules
    if data.extras is not None:
        cfg.extras = data.extras
        changed["extras"] = data.extras

    session.flush()
    write_audit(
        session,
        admin_user_id=actor.id,
        tenant_id=tenant_id,
        action=AuditAction.update,
        resource_type="CrawlConfig",
        resource_id=str(cfg.id),
        details=changed or None,
        request=request,
    )
    return CrawlConfigResponse.from_model(cfg)


def delete_config(
    session: Session,
    tenant_id: int,
    config_id: int,
    actor: AdminUser,
    request: Request,
) -> None:
    if not can_write_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = CrawlConfigRepository(session)
    cfg = repo.get(config_id, tenant_id)
    if cfg is None:
        raise NotFoundError("Crawl configuration not found")

    session.execute(
        update(Tenant)
        .where(Tenant.default_crawl_config_id == config_id)
        .values(default_crawl_config_id=None),
    )
    session.flush()

    write_audit(
        session,
        admin_user_id=actor.id,
        tenant_id=tenant_id,
        action=AuditAction.delete,
        resource_type="CrawlConfig",
        resource_id=str(config_id),
        details=None,
        request=request,
    )
    repo.delete(cfg)
