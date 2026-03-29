# University Chatbot Platform

Monorepo for a **multi-tenant** university website RAG chatbot: **FastAPI** backend (crawl, index, retrieve, chat), **Next.js** frontend (admin + public chat), **PostgreSQL** with **pgvector**, **Redis**, **Celery**.

This repository currently contains **project structure and tooling** only; domain features are implemented in later phases.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI app, SQLAlchemy, Alembic, Celery workers |
| `frontend/` | Next.js (App Router), Tailwind, ESLint, Prettier |
| `infra/docker/` | Dockerfiles for API, worker, and web |

## Prerequisites

- **Python 3.12+**
- **Node.js 22+** (LTS) and npm
- **Docker** (optional, for Compose stack)

## Quick start (local)

### 1. Database and Redis

```bash
docker compose up -d db redis
```

Or run PostgreSQL (with pgvector) and Redis yourself; set `DATABASE_URL` and Redis URLs in `backend/.env`.

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env   # Windows; use cp on Unix
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: [http://localhost:8000](http://localhost:8000) — `GET /health`, `GET /api/health`
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Celery worker (optional)

```bash
cd backend
celery -A app.workers.celery_app:celery_app worker -l info
```

### 4. Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

- App: [http://localhost:3000](http://localhost:3000) — home, `/admin`, `/chat`

## Docker (full stack)

Build and run API, worker, web, database, and Redis:

```bash
docker compose build
docker compose up -d
```

Run migrations inside the API container when models exist:

```bash
docker compose exec api alembic upgrade head
```

Adjust `NEXT_PUBLIC_API_URL` / `CORS_ORIGINS` for your hostnames when not using localhost.

## Environment files

- `backend/.env.example` — API, DB, Redis, Celery, JWT, OpenAI (placeholders)
- `frontend/.env.example` — public app URL and API URL for the browser

Copy to `.env` / `.env.local` and edit; do not commit secrets.

## Quality checks

**Backend** (from `backend/`):

```bash
pytest
ruff check .
ruff format .
```

**Frontend** (from `frontend/`):

```bash
npm run lint
npm run format
npm run typecheck
```

**Pre-commit** (optional, from repo root):

```bash
pip install pre-commit
pre-commit install
```

## License

Add a license as required by your institution.
