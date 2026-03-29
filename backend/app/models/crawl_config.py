"""Crawl policy configuration per tenant (one or more entry points / rules)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TenantIdFKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.job import CrawlJob
    from app.models.source import Source
    from app.models.tenant import Tenant


class CrawlConfig(Base, TenantIdFKMixin, TimestampMixin):
    """
    Defines how crawling runs for a tenant (base URL, host allowlist, depth, robots).
    Sources discovered under a config reference it; manual sources may omit it.
    """

    __tablename__ = "crawl_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    max_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respect_robots_txt: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Structured policy; keeps schema flexible as crawl rules evolve.
    allowed_hosts: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    path_prefixes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    exclude_globs: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    extras: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="crawl_configs")
    sources: Mapped[list[Source]] = relationship(back_populates="crawl_config")
    crawl_jobs: Mapped[list[CrawlJob]] = relationship(back_populates="crawl_config")
