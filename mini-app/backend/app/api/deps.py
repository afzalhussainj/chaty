"""FastAPI dependencies (settings, DB session; extend with auth/tenant later)."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.settings import Settings, get_settings
from app.db.session import get_db_session


def get_settings_dep() -> Settings:
    """Inject cached application settings."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_db() -> Generator[Session, None, None]:
    """Request-scoped SQLAlchemy session."""
    yield from get_db_session()


SessionDep = Annotated[Session, Depends(get_db)]
