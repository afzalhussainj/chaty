"""Application lifespan (startup / shutdown hooks)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.redis_client import close_redis_pool
from app.core.settings import get_settings
from app.db.session import SessionLocal, dispose_engine, get_engine
from app.models.crawl_config import CrawlConfig
from app.models.enums import CrawlFrequency, TenantStatus
from app.models.tenant import Tenant
from app.repositories.crawl_config import CrawlConfigRepository
from app.repositories.tenant import TenantRepository


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Bootstrap single-site tenant/config; release DB/Redis pools on shutdown."""
    logger = get_logger(__name__)
    logger.info("lifespan_enter")
    _ensure_single_site()
    yield
    logger.info("lifespan_exit")
    dispose_engine()
    close_redis_pool()


def _ensure_single_site() -> None:
    """Ensure exactly one configured site exists for public chat + CLI operations."""
    logger = get_logger(__name__)
    settings = get_settings()
    session: Session = SessionLocal(bind=get_engine())
    try:
        tenant_repo = TenantRepository(session)
        cfg_repo = CrawlConfigRepository(session)
        tenant = tenant_repo.get_by_slug(settings.site_slug)
        allowed = [d.strip() for d in settings.site_allowed_domains.split(",") if d.strip()]
        if tenant is None:
            tenant = Tenant(
                name=settings.site_name,
                slug=settings.site_slug,
                status=TenantStatus.active,
                base_url=settings.site_base_url,
                allowed_domains=allowed or None,
                branding={
                    "app_title": settings.site_name,
                    "primary_color": "#2563eb",
                    "logo_url": None,
                },
            )
            tenant_repo.add(tenant)
            session.flush()
        cfg = None
        if tenant.default_crawl_config_id is not None:
            cfg = cfg_repo.get(tenant.default_crawl_config_id, tenant.id)
        if cfg is None:
            cfg = CrawlConfig(
                tenant_id=tenant.id,
                name="Default",
                base_url=settings.site_base_url,
                allowed_hosts=allowed or None,
                crawl_frequency=CrawlFrequency.manual,
                is_active=True,
            )
            cfg_repo.add(cfg)
            session.flush()
            tenant.default_crawl_config_id = cfg.id
        session.commit()
        logger.info(
            "single_site_ready",
            tenant_id=tenant.id,
            site_slug=tenant.slug,
            crawl_config_id=tenant.default_crawl_config_id,
        )
    except Exception:
        logger.exception("single_site_bootstrap_failed")
        session.rollback()
    finally:
        session.close()
