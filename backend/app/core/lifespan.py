"""Application lifespan (startup / shutdown hooks)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.auth.password import hash_password
from app.core.logging import get_logger
from app.core.redis_client import close_redis_pool
from app.core.settings import get_settings
from app.db.session import SessionLocal, dispose_engine, get_engine
from app.models.admin import AdminUser
from app.models.enums import AdminRole
from app.repositories.admin_user import AdminUserRepository


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Bootstrap optional dev admin; release DB/Redis pools on shutdown."""
    logger = get_logger(__name__)
    logger.info("lifespan_enter")
    settings = get_settings()
    if settings.bootstrap_admin_email and settings.bootstrap_admin_password:
        _maybe_bootstrap_super_admin()
    yield
    logger.info("lifespan_exit")
    dispose_engine()
    close_redis_pool()


def _maybe_bootstrap_super_admin() -> None:
    """Create a super admin if env vars are set and that email does not exist."""
    logger = get_logger(__name__)
    settings = get_settings()
    email = (settings.bootstrap_admin_email or "").strip().lower()
    password = settings.bootstrap_admin_password or ""
    if not email or not password:
        return
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = AdminUserRepository(session)
        if repo.get_by_email(email) is not None:
            return
        user = AdminUser(
            email=email,
            password_hash=hash_password(password),
            full_name="Bootstrap super admin",
            tenant_id=None,
            role=AdminRole.super_admin,
            is_active=True,
        )
        repo.add(user)
        session.commit()
        logger.info("bootstrap_admin_created", email=email)
    except Exception:
        logger.exception("bootstrap_admin_failed")
        session.rollback()
    finally:
        session.close()
