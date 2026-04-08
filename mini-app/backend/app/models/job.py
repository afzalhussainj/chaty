"""Background job records for crawl and index pipelines."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CrawlJobType, IndexJobType, JobStatus
from app.models.mixins import TenantIdFKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.admin import AdminUser
    from app.models.crawl_config import CrawlConfig
    from app.models.extracted import ExtractedDocument
    from app.models.source import Source
    from app.models.tenant import Tenant


class CrawlJob(Base, TenantIdFKMixin, TimestampMixin):
    """Tracks crawl runs (full site, single URL, PDF-only, etc.)."""

    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    crawl_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("crawl_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    job_type: Mapped[CrawlJobType] = mapped_column(
        SQLEnum(CrawlJobType, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, native_enum=False, length=32),
        nullable=False,
        index=True,
        default=JobStatus.queued,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="crawl_jobs")
    crawl_config: Mapped[CrawlConfig | None] = relationship(back_populates="crawl_jobs")
    created_by: Mapped[AdminUser | None] = relationship(
        "AdminUser",
        back_populates="crawl_jobs_created",
    )


class IndexJob(Base, TenantIdFKMixin, TimestampMixin):
    """Tracks embedding / index rebuild work."""

    __tablename__ = "index_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    extracted_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("extracted_documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    job_type: Mapped[IndexJobType] = mapped_column(
        SQLEnum(IndexJobType, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, native_enum=False, length=32),
        nullable=False,
        index=True,
        default=JobStatus.queued,
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="index_jobs")
    source: Mapped[Source | None] = relationship(back_populates="index_jobs")
    extracted_document: Mapped[ExtractedDocument | None] = relationship(
        back_populates="index_jobs",
    )
    created_by: Mapped[AdminUser | None] = relationship(
        "AdminUser",
        back_populates="index_jobs_created",
    )
