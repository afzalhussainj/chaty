"""Source (URL, PDF, or manual text) and immutable snapshots for history."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import SourceStatus, SourceType
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.crawl_config import CrawlConfig
    from app.models.extracted import DocumentChunk, ExtractedDocument
    from app.models.job import IndexJob
    from app.models.tenant import Tenant


class Source(Base, TimestampMixin):
    """
    Logical content unit: HTML page, PDF, or manually supplied text.
    `canonical_url` is unique per tenant for deduplication; `url` may differ (redirects).
    """

    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "canonical_url", name="uq_sources_tenant_canonical_url"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crawl_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("crawl_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    discovered_from_source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_type: Mapped[SourceType] = mapped_column(
        SQLEnum(SourceType, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[SourceStatus] = mapped_column(
        SQLEnum(SourceStatus, native_enum=False, length=32),
        nullable=False,
        index=True,
        default=SourceStatus.pending,
    )

    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        index=True,
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    extras: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="sources")
    crawl_config: Mapped[CrawlConfig | None] = relationship(back_populates="sources")
    discovered_from: Mapped[Source | None] = relationship(
        "Source",
        remote_side="Source.id",
        foreign_keys="Source.discovered_from_source_id",
        back_populates="discovered_children",
    )
    discovered_children: Mapped[list[Source]] = relationship(
        "Source",
        foreign_keys="Source.discovered_from_source_id",
        back_populates="discovered_from",
    )

    snapshots: Mapped[list[SourceSnapshot]] = relationship(
        back_populates="source",
        order_by="SourceSnapshot.version",
    )
    extracted_documents: Mapped[list[ExtractedDocument]] = relationship(
        back_populates="source",
    )
    index_jobs: Mapped[list[IndexJob]] = relationship(back_populates="source")
    document_chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="source",
    )


class SourceSnapshot(Base):
    """
    Immutable snapshot when raw bytes or content hash changes.
    Enables audit and rollback of what was indexed at a point in time.
    """

    __tablename__ = "source_snapshots"
    __table_args__ = (
        UniqueConstraint("source_id", "version", name="uq_source_snapshots_source_version"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    raw_content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    byte_length: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source: Mapped[Source] = relationship(back_populates="snapshots")
    extracted_documents: Mapped[list[ExtractedDocument]] = relationship(
        back_populates="source_snapshot",
    )
