"""Admin users and audit trail."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import AdminRole, AuditAction
from app.models.mixins import TimestampMixin
from app.models.tenant import Tenant

if TYPE_CHECKING:
    from app.models.job import CrawlJob, IndexJob


class AuditLog(Base):
    """Append-only record of privileged actions (compliance / debugging)."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    admin_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(INET(), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    tenant: Mapped[Tenant | None] = relationship(back_populates="audit_logs")
    admin_user: Mapped[AdminUser | None] = relationship(
        "AdminUser",
        foreign_keys=[admin_user_id],
        back_populates="audit_logs",
    )


class AdminUser(Base, TimestampMixin):
    """
    Staff accounts. Super admins have tenant_id NULL; tenant roles require tenant_id.
    Enforced with a CHECK constraint at the database level.
    """

    __tablename__ = "admin_users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'super_admin' AND tenant_id IS NULL) OR "
            "(role IN ('tenant_admin', 'tenant_viewer') AND tenant_id IS NOT NULL)",
            name="ck_admin_users_role_tenant_consistency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    role: Mapped[AdminRole] = mapped_column(
        SQLEnum(AdminRole, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped[Tenant | None] = relationship(back_populates="admin_users")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="admin_user")
    crawl_jobs_created: Mapped[list[CrawlJob]] = relationship(
        "CrawlJob",
        back_populates="created_by",
    )
    index_jobs_created: Mapped[list[IndexJob]] = relationship(
        "IndexJob",
        back_populates="created_by",
    )
