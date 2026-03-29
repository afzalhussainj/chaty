"""Admin user persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import AdminUser


class AdminUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: int) -> AdminUser | None:
        return self._session.get(AdminUser, user_id)

    def get_by_email(self, email: str) -> AdminUser | None:
        stmt = select(AdminUser).where(AdminUser.email == email.lower().strip())
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        from sqlalchemy import func

        return int(self._session.scalar(select(func.count()).select_from(AdminUser)) or 0)

    def add(self, user: AdminUser) -> AdminUser:
        self._session.add(user)
        self._session.flush()
        return user
