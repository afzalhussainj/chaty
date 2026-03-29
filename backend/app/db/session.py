"""SQLAlchemy 2.x engine and session factory."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import get_settings

_engine: Engine | None = None

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_engine() -> Engine:
    """Lazy singleton SQLAlchemy engine (respects get_settings() cache)."""
    global _engine
    if _engine is None:
        s = get_settings()
        _engine = create_engine(
            s.database_url,
            pool_pre_ping=True,
            pool_size=s.database_pool_size,
            max_overflow=s.database_max_overflow,
            pool_timeout=s.database_pool_timeout,
            echo=s.database_echo,
        )
    return _engine


def dispose_engine() -> None:
    """Dispose engine pool (shutdown hook and tests)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_db_session() -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""
    db = SessionLocal(bind=get_engine())
    try:
        yield db
    finally:
        db.close()


def reset_engine_for_tests() -> None:
    """Dispose engine so the next get_engine() rebuilds (tests only)."""
    dispose_engine()
