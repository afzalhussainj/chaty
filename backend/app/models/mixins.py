"""Reusable column groups."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column


@declarative_mixin
class TimestampMixin:
    """created_at / updated_at with server defaults (timestamptz)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


@declarative_mixin
class TenantIdFKMixin:
    """tenant_id foreign key (index on concrete table)."""

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
