# Backend API

FastAPI application, Celery workers, Alembic migrations. See repository root `README.md` for full setup.

## Local development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Migrations

```bash
alembic upgrade head
```

## Tests & lint

```bash
pytest
ruff check .
ruff format .
```
