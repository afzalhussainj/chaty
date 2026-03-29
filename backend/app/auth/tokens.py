"""JWT access tokens for admin sessions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.settings import Settings


def create_access_token(
    *,
    subject: str,
    settings: Settings,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, int]:
    """
    Return (token, expires_in_seconds).
    `subject` is typically the admin user id as string.
    """
    now = datetime.now(timezone.utc)
    expire_minutes = settings.access_token_expire_minutes
    exp = now + timedelta(minutes=expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expire_minutes * 60


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and validate JWT; raises jwt.PyJWTError on failure."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
