# University Chatbot Platform

Multi-tenant **RAG** stack for university websites: crawl HTML/PDFs, index with **PostgreSQL + pgvector** and full-text search, answer questions with **OpenAI** using **grounded citations**. **FastAPI** backend, **Next.js** frontend, **Redis** + **Celery** workers.

## Features (summary)

| Area | Behavior |
|------|----------|
| **Single page update** | Queue `incremental_url` / `refresh_page` for one HTML URL. |
| **Single PDF update** | Queue `incremental_pdf` / `refresh_pdf` for one PDF URL; indexing skips work if extraction hash unchanged. |
| **New source** | `add_source` job ingests one URL and registers related links per crawl rules. |
| **Citations** | Answers return source titles, URLs, PDF page numbers; UI only links safe `http(s)` URLs. |
| **Tenant isolation** | All chunks and retrieval are filtered by `tenant_id`; public chat uses tenant **slug**. |

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** (system design), **[docs/CRAWL_AND_INDEX.md](docs/CRAWL_AND_INDEX.md)** (workflows), **[docs/API.md](docs/API.md)** (curl examples).

---

## Repository layout

```
chaty/
├── backend/                 # FastAPI app, Alembic, Celery, pytest
│   ├── app/
│   ├── alembic/
│   ├── scripts/           # e.g. seed_demo_tenant.py
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── frontend/                # Next.js 15 (App Router)
│   ├── app/
│   ├── components/
│   ├── tests/
│   └── .env.example
├── infra/docker/            # Dockerfiles + API entrypoint (migrations)
├── docs/                    # Architecture, crawl/index, API examples
├── docker-compose.yml       # postgres, redis, backend, worker, frontend
├── .env.example             # variables for Docker Compose
└── README.md
```

---

## Prerequisites

- **Docker** + Docker Compose v2 (recommended for full stack)
- **Python 3.12+** and **Node.js 22+** (for local dev without Docker)
- **OpenAI API key** (embeddings + chat)

---

## Quick start: Docker (full stack)

1. **Copy environment file**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set **`OPENAI_API_KEY`**. Optionally set **`JWT_SECRET_KEY`**, **`BOOTSTRAP_ADMIN_EMAIL`**, **`BOOTSTRAP_ADMIN_PASSWORD`** (first super admin is created on API startup if that email does not exist).

2. **Start everything**

   ```bash
   docker compose up --build
   ```

   - **Frontend:** [http://localhost:3000](http://localhost:3000)  
   - **API docs:** [http://localhost:8000/docs](http://localhost:8000/docs)  
   - **Liveness:** [http://localhost:8000/health](http://localhost:8000/health)  
   - **Readiness (DB + Redis):** [http://localhost:8000/api/health](http://localhost:8000/api/health)

3. **Migrations** run automatically when the **backend** container starts (`alembic upgrade head` in the API entrypoint).

4. **Optional demo tenant** (slug `demo`, example.edu placeholder):

   ```bash
   docker compose exec backend python scripts/seed_demo_tenant.py
   ```

   Public chat URL pattern: `/chat/demo` (after indexing content for that tenant).

Compose service names: **`postgres`**, **`redis`**, **`backend`**, **`worker`**, **`frontend`**.

To bring up **only** Postgres and Redis (API + Next on the host), use **`scripts/dev.sh`** (Unix) or **`scripts/dev.ps1`** (Windows).

If you change **`NEXT_PUBLIC_*`** values, rebuild the **frontend** image (`docker compose build frontend`).

---

## Quick start: local development (no app containers)

Use Docker only for **Postgres + Redis**, run API and Next.js on the host (fast iteration).

1. **Infrastructure**

   ```bash
   docker compose up -d postgres redis
   ```

2. **Backend** (`backend/.env` from `backend/.env.example`)

   ```bash
   cd backend
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # Unix:   source .venv/bin/activate
   pip install -r requirements-dev.txt
   copy .env.example .env   # or cp; set DATABASE_URL, Redis, OPENAI_API_KEY, JWT_SECRET_KEY
   alembic upgrade head
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Celery worker** (separate terminal, same venv)

   ```bash
   cd backend
   celery -A app.workers.celery_app:celery_app worker -l info
   ```

4. **Frontend**

   ```bash
   cd frontend
   npm install
   copy .env.example .env.local
   npm run dev
   ```

`NEXT_PUBLIC_API_BASE_URL` must end with **`/api`** (see `frontend/lib/api.ts`).

---

## Migrations

- **Upgrade:** `cd backend && alembic upgrade head`
- **Create revision** (after model changes): `alembic revision --autogenerate -m "describe change"`
- **Docker:** migrations run on **backend** container start; to run manually:  
  `docker compose exec backend alembic upgrade head`

---

## Tests and lint

**Backend** (from `backend/`):

```bash
pytest
ruff check .
ruff format .
```

**Frontend** (from `frontend/`):

```bash
npm test
npm run lint
npm run typecheck
```

---

## Configuration reference

| File | Purpose |
|------|---------|
| **`.env`** (repo root) | Used by **Docker Compose** for `OPENAI_API_KEY`, `JWT_SECRET_KEY`, bootstrap admin, etc. |
| **`backend/.env`** | Local **uvicorn** / **pytest** (see `backend/.env.example`). |
| **`frontend/.env.local`** | `NEXT_PUBLIC_*` for `npm run dev` (see `frontend/.env.example`). |

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| Jobs stay **queued** | **Worker** running? **Redis** reachable? |
| Chat / index errors | **`OPENAI_API_KEY`** set on **backend** and **worker**? |
| Frontend cannot reach API | **`NEXT_PUBLIC_API_BASE_URL`** includes `/api` and matches backend URL. |
| CORS errors | **`CORS_ORIGINS`** includes your frontend origin (`http://localhost:3000`). |

---

## License

Add a license as required by your institution.
