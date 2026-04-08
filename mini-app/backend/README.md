# Backend API

FastAPI application, Alembic migrations, Celery workers, and pytest suite.

**Project-wide setup, Docker, and documentation live in the [repository root README](../README.md).**

## Quick commands

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
celery -A app.workers.celery_app:celery_app worker -l info
pytest
```

## Configuration

See `.env.example` for local development. When using Docker Compose from the repo root, prefer the root `.env` (see root README).

## Demo tenant seed

```bash
python scripts/seed_demo_tenant.py
```

(Requires `DATABASE_URL` and migrations applied.)
