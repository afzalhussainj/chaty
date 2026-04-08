"""Fixtures for tests that need a real PostgreSQL database (migrations + seed admin)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _test_database_url() -> str:
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/chaty_test",
    )


@pytest.fixture(scope="session")
def integration_database_url():
    """
    Point the app at a dedicated test DB, run Alembic migrations, and yield the URL.

    Skips if Postgres is unreachable. Create the database once, e.g.:

        docker compose exec db psql -U postgres -c "CREATE DATABASE chaty_test;"
    """
    url = _test_database_url()
    os.environ["DATABASE_URL"] = url

    from app.core.settings import get_settings
    from app.db.session import reset_engine_for_tests

    get_settings.cache_clear()
    reset_engine_for_tests()

    try:
        eng = create_engine(url, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
    except OSError as exc:
        pytest.skip(f"Postgres not available for integration tests: {exc}")
    except Exception as exc:  # noqa: BLE001 — surface driver errors as skip
        pytest.skip(f"Postgres not available for integration tests: {exc}")

    env = {**os.environ, "DATABASE_URL": url}
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_ROOT),
        env=env,
        check=True,
    )

    yield url

    get_settings.cache_clear()
    reset_engine_for_tests()


@pytest.fixture(scope="session")
def integration_admin_credentials(integration_database_url: str) -> dict[str, str | int]:
    """Ensure a super admin exists and return login credentials."""
    from app.auth.password import hash_password
    from app.core.settings import get_settings
    from app.db.session import SessionLocal, get_engine
    from app.models.admin import AdminUser
    from app.models.enums import AdminRole
    from app.repositories.admin_user import AdminUserRepository

    get_settings.cache_clear()
    email = "integration-admin@example.com"
    password = "integration-test-secret-9"

    session = SessionLocal(bind=get_engine())
    try:
        repo = AdminUserRepository(session)
        user = repo.get_by_email(email)
        if user is None:
            user = AdminUser(
                email=email,
                password_hash=hash_password(password),
                full_name="Integration super admin",
                tenant_id=None,
                role=AdminRole.super_admin,
                is_active=True,
            )
            repo.add(user)
            session.commit()
            session.refresh(user)
        return {"email": email, "password": password, "user_id": user.id}
    finally:
        session.close()


@pytest.fixture(scope="session")
def integration_app(integration_admin_credentials: dict[str, str | int]):
    """Single app instance for the integration session (runs lifespan once)."""
    from app.main import create_app

    return create_app()


@pytest.fixture(scope="session")
def integration_client(integration_app):
    with TestClient(integration_app) as client:
        yield client
