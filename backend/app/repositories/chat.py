"""Chat session and message persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession
from app.models.enums import ChatRole


class ChatSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, session_id: int, tenant_id: int) -> ChatSession | None:
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.tenant_id == tenant_id,
        )
        return self._session.scalars(stmt).first()

    def create(self, tenant_id: int, *, title: str | None = None) -> ChatSession:
        row = ChatSession(tenant_id=tenant_id, title=title)
        self._session.add(row)
        self._session.flush()
        return row

    def next_sequence(self, session_id: int) -> int:
        stmt = select(ChatMessage.sequence).where(ChatMessage.session_id == session_id).order_by(
            ChatMessage.sequence.desc(),
        ).limit(1)
        last = self._session.scalars(stmt).first()
        return int(last) + 1 if last is not None else 0


class ChatMessageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        tenant_id: int,
        session_id: int,
        role: ChatRole,
        content: str,
        sequence: int,
        retrieval_trace: dict | None = None,
        token_count: int | None = None,
    ) -> ChatMessage:
        row = ChatMessage(
            tenant_id=tenant_id,
            session_id=session_id,
            role=role,
            content=content,
            sequence=sequence,
            retrieval_trace=retrieval_trace,
            token_count=token_count,
        )
        self._session.add(row)
        self._session.flush()
        return row
