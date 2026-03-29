# Backend API

FastAPI application with structured logging, PostgreSQL (SQLAlchemy 2.x), Redis, Celery, and Alembic. See the repository root `README.md` for full stack setup.

## Requirements

- Python **3.12+** (see `pyproject.toml`)

## Local development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- OpenAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Liveness: `GET /health` (process up; does not check DB/Redis)
- Readiness: `GET /api/health` (checks database + Redis; returns **503** if any dependency is down)

## Configuration

Environment variables are documented in `.env.example`. Application settings are loaded via `app.core.settings.get_settings()` (cached); call `get_settings.cache_clear()` after changing env in tests.

## Migrations

```bash
alembic upgrade head
```

## Celery worker

```bash
celery -A app.workers.celery_app:celery_app worker -l info
```

## Tests and lint

```bash
pytest
ruff check app tests
ruff format app tests
```

Integration-style tests (live Postgres/Redis) can be marked with `@pytest.mark.integration` when added.
