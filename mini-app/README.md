# Mini Chatbot App (Single Site)

This is an extracted standalone mini app from the full multi-tenant platform.

## What is simplified

- Single configured site only (`SITE_SLUG`, `SITE_BASE_URL`)
- No admin panel, no tenant management UI, no admin auth routes exposed
- One frontend page (chatbot)
- Crawl/update/index operations via CLI scripts

## What stays the same (core logic)

- Crawl engine with nested internal link traversal
- PDF discovery + ingestion
- HTML/PDF extraction
- Chunking + embeddings + indexing
- Hybrid retrieval (vector + FTS)
- Grounded chat answers with citations
- Incremental flows (single page, single PDF, add source, sync changed)

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Frontend: `http://localhost:3000`  
API docs: `http://localhost:8000/docs`

## CLI operations

Run from `mini-app/backend` (same env as API):

```bash
python scripts/site_cli.py full-crawl
python scripts/site_cli.py refresh-page --url "https://example.edu/admissions"
python scripts/site_cli.py refresh-pdf --url "https://example.edu/catalog.pdf"
python scripts/site_cli.py add-source --url "https://example.edu/new-page"
python scripts/site_cli.py sync-changed
python scripts/site_cli.py reindex-source --source-id 123
python scripts/site_cli.py rebuild-all
```

## Notes

- Startup auto-ensures one site record + default crawl config.
- Chat endpoint used by UI remains grounded-only (`/api/public/tenants/{slug}/chat/query` and `/api/public/chat/query`).
- This mini app is standalone in this folder; you can move it out independently.

