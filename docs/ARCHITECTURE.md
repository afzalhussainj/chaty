# Architecture

## High-level

The platform is a **multi-tenant RAG** system for university web content:

1. **Crawl** — Discover and fetch HTML pages and PDFs under configured rules (hosts, paths, depth).
2. **Extract** — HTML via Trafilatura-style extraction; PDFs via PyMuPDF text.
3. **Index** — Chunk text, embed with OpenAI, store in PostgreSQL with **pgvector**; full-text search via PostgreSQL **FTS** on chunk text.
4. **Retrieve** — Hybrid search (vector + FTS) merged and ranked per tenant.
5. **Answer** — Grounded chat via OpenAI Responses API using only retrieved chunks; responses include **citations** (source URL, optional PDF page).

## Tenant isolation

- Every domain row carries **`tenant_id`** (sources, chunks, jobs, chat sessions, etc.).
- Retrieval and public chat resolve the tenant by **slug** (`/public/tenants/{slug}/...`) or admin routes by numeric id.
- SQL filters always constrain `DocumentChunk.tenant_id` and `Source.tenant_id` together so a query cannot return another tenant’s vectors or FTS hits.

## Services

| Component | Role |
|-----------|------|
| **backend** | FastAPI: auth, admin CRUD, crawl job orchestration, chat, health. |
| **worker** | Celery: crawl tasks, extraction, indexing (calls OpenAI embeddings). |
| **postgres** | Data + pgvector + FTS (`tsvector` on chunks). |
| **redis** | Celery broker and result backend. |
| **frontend** | Next.js: admin dashboard, public chat UI (`/chat/[slug]`). |

## Request flow (public chat)

1. Browser loads tenant branding by slug.
2. User message → `POST /api/public/tenants/{slug}/chat/query` (rate-limited).
3. Backend embeds the question, runs hybrid retrieval **for that tenant only**, builds context + citation list, calls OpenAI, returns answer + citations.
4. UI renders citations; only **http(s)** URLs become clickable links (see `frontend/lib/safe-url.ts`).

## Request flow (admin)

- JWT **Bearer** token after `POST /api/auth/login`.
- Super admins manage tenants; tenant admins are scoped to their `tenant_id`.
- Crawl and incremental actions enqueue **CrawlJob** rows; the worker executes them asynchronously.

## Related code

- Retrieval: `backend/app/retrieval/retrieval_service.py`
- Indexing: `backend/app/indexing/`
- Crawl engine: `backend/app/crawler/engine.py`
- Chat: `backend/app/chat/answer_service.py`
