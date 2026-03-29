# API usage examples

Base URL: `http://localhost:8000/api` (local). Interactive docs: [Swagger UI](http://localhost:8000/docs).

Replace `TOKEN` with a JWT from login, `TENANT_ID` with your tenant id, `CRAWL_CONFIG_ID` from crawl configs.

## Auth

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@localhost","password":"YourPassword"}'
```

Response includes `access_token`. Use it as:

```bash
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

## Create tenant (super admin)

```bash
curl -s -X POST http://localhost:8000/api/admin/tenants \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example University",
    "slug": "example-u",
    "status": "active",
    "base_url": "https://www.example.edu/",
    "allowed_domains": ["example.edu"]
  }'
```

## Create crawl config

```bash
curl -s -X POST http://localhost:8000/api/admin/tenants/TENANT_ID/crawl-configs \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main",
    "base_url": "https://www.example.edu/",
    "allowed_hosts": ["example.edu"],
    "respect_robots_txt": true
  }'
```

## Queue full recrawl

```bash
curl -s -X POST http://localhost:8000/api/admin/tenants/TENANT_ID/crawl-jobs \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "crawl_config_id": CRAWL_CONFIG_ID,
    "job_type": "full_recrawl"
  }'
```

## Single page refresh (HTML)

```bash
curl -s -X POST http://localhost:8000/api/admin/tenants/TENANT_ID/incremental/refresh-page \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "crawl_config_id": CRAWL_CONFIG_ID,
    "url": "https://www.example.edu/admissions/"
  }'
```

## Single PDF refresh

```bash
curl -s -X POST http://localhost:8000/api/admin/tenants/TENANT_ID/incremental/refresh-pdf \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "crawl_config_id": CRAWL_CONFIG_ID,
    "url": "https://www.example.edu/catalog.pdf"
  }'
```

## Public chat (by tenant slug)

```bash
curl -s -X POST http://localhost:8000/api/public/tenants/demo/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the tuition deadlines?",
    "answer_mode": "concise",
    "stream": false
  }'
```

Public chat can be disabled with `PUBLIC_CHAT_ENABLED=false` on the server.

## Health

- **Liveness:** `GET http://localhost:8000/health` (process up)
- **Readiness:** `GET http://localhost:8000/api/health` (database + Redis; may be degraded if optional checks fail)
