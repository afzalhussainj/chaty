"""Crawl configuration persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crawl_config import CrawlConfig


class CrawlConfigRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, config_id: int, tenant_id: int) -> CrawlConfig | None:
        stmt = select(CrawlConfig).where(
            CrawlConfig.id == config_id,
            CrawlConfig.tenant_id == tenant_id,
        )
        return self._session.scalars(stmt).first()

    def list_for_tenant(self, tenant_id: int) -> list[CrawlConfig]:
        stmt = (
            select(CrawlConfig)
            .where(CrawlConfig.tenant_id == tenant_id)
            .order_by(CrawlConfig.id)
        )
        return list(self._session.scalars(stmt).all())

    def add(self, config: CrawlConfig) -> CrawlConfig:
        self._session.add(config)
        self._session.flush()
        return config

    def delete(self, config: CrawlConfig) -> None:
        self._session.delete(config)
