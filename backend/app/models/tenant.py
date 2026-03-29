"""Tenant (organization) root entity."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TenantStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.admin import AdminUser, AuditLog
    from app.models.chat import ChatMessage, ChatSession
    from app.models.crawl_config import CrawlConfig
    from app.models.extracted import DocumentChunk, ExtractedDocument
    from app.models.job import CrawlJob, IndexJob
    from app.models.source import Source


class Tenant(Base, TimestampMixin):
    """
    Top-level isolation boundary: all domain rows are tenant-scoped
    (denormalized tenant_id on hot paths for query performance and RLS readiness).
    """

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    status: Mapped[TenantStatus] = mapped_column(
        SQLEnum(TenantStatus, native_enum=False, length=32),
        default=TenantStatus.active,
        server_default=TenantStatus.active.value,
    )
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    crawl_configs: Mapped[list[CrawlConfig]] = relationship(back_populates="tenant")
    sources: Mapped[list[Source]] = relationship(back_populates="tenant")
    extracted_documents: Mapped[list[ExtractedDocument]] = relationship(
        back_populates="tenant",
    )
    document_chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="tenant",
    )
    crawl_jobs: Mapped[list[CrawlJob]] = relationship(back_populates="tenant")
    index_jobs: Mapped[list[IndexJob]] = relationship(back_populates="tenant")
    chat_sessions: Mapped[list[ChatSession]] = relationship(back_populates="tenant")
    chat_messages: Mapped[list[ChatMessage]] = relationship(back_populates="tenant")
    admin_users: Mapped[list[AdminUser]] = relationship(back_populates="tenant")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="tenant")

    def __repr__(self) -> str:
        return f"Tenant(id={self.id}, slug={self.slug!r})"
