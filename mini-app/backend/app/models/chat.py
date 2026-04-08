"""Chat sessions and messages (tenant-isolated)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ChatRole
from app.models.mixins import TenantIdFKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class ChatSession(Base, TenantIdFKMixin, TimestampMixin):
    """A conversation thread within a tenant."""

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    external_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    extras: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="chat_sessions")
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        order_by="ChatMessage.sequence",
    )


class ChatMessage(Base, TenantIdFKMixin, TimestampMixin):
    """Single turn in a session (user / assistant / system / tool)."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_chat_messages_session_sequence"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[ChatRole] = mapped_column(
        SQLEnum(ChatRole, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retrieval_trace: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="chat_messages")
    session: Mapped[ChatSession] = relationship(back_populates="messages")
