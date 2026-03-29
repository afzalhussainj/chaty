"""FastAPI dependencies (DB session, auth, tenant context)."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db as get_db_session


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()
