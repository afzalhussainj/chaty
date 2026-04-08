"""Admin authentication."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.password import verify_password
from app.auth.tokens import create_access_token
from app.core.settings import Settings
from app.models.admin import AdminUser
from app.repositories.admin_user import AdminUserRepository


def authenticate(
    session: Session,
    email: str,
    password: str,
    settings: Settings,
) -> tuple[str, int, AdminUser] | None:
    """Return (token, expires_in_seconds, user) or None if credentials invalid."""
    repo = AdminUserRepository(session)
    user = repo.get_by_email(email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    token, expires_in = create_access_token(
        subject=str(user.id),
        settings=settings,
        extra_claims={"email": user.email, "role": user.role.value},
    )
    user.last_login_at = datetime.now(timezone.utc)
    session.flush()
    return token, expires_in, user
