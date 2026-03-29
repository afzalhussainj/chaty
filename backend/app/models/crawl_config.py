"""Crawl policy configuration per tenant (one or more entry points / rules)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CrawlFrequency
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
    max_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respect_robots_txt: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    allow_pdf_crawling: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    allow_js_rendering: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    crawl_frequency: Mapped[CrawlFrequency] = mapped_column(
        SQLEnum(CrawlFrequency, native_enum=False, length=32),
        default=CrawlFrequency.manual,
        server_default=CrawlFrequency.manual.value,
    )

    # Structured policy; keeps schema flexible as crawl rules evolve.
    allowed_hosts: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    path_prefixes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    exclude_globs: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    extras: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    tenant: Mapped[Tenant] = relationship(
        back_populates="crawl_configs",
        foreign_keys="CrawlConfig.tenant_id",
    )
    sources: Mapped[list[Source]] = relationship(back_populates="crawl_config")
    crawl_jobs: Mapped[list[CrawlJob]] = relationship(back_populates="crawl_config")
