# Environment configuration

Configuration is loaded from the process environment (and optional `.env` file) via Pydantic Settings. See `app/core/settings.py` for the full list of fields and defaults.

## Production checklist

1. Set `APP_ENV=production` and `DEBUG=false`.
2. Set `JWT_SECRET_KEY` to a long random value (never use `change-me`). The app refuses to start in production with weak secrets.
3. Set `LOG_JSON=true` if your platform expects JSON logs on stdout.
4. Set `DATABASE_URL`, `REDIS_URL`, and Celery broker URLs to managed services.
5. Set `OPENAI_API_KEY` for chat and embeddings.
6. Review `CORS_ORIGINS` — only list trusted web origins.
7. Set `PUBLIC_CHAT_ENABLED=false` if you do not want anonymous chat, or tune `PUBLIC_CHAT_RATE_LIMIT`.
8. Optionally set `HEALTH_CHECK_CELERY_WORKERS=true` if your orchestrator should treat missing workers as **degraded** (API still returns 200 on `/api/health` when DB+Redis are up).

## Health endpoints

| Path        | Purpose |
|------------|---------|
| `GET /health` | Liveness — process up only. |
| `GET /api/health` | Readiness — database, Redis, and optionally Celery workers. Returns **503** if PostgreSQL or Redis is down; **200** with `status: degraded` if only workers are down (when worker check is enabled). |

## Correlation IDs

Send `X-Request-ID` or `X-Correlation-ID` on API requests; the response echoes both headers with the same value. Structured logs include `request_id` when using structlog context (API middleware). Error JSON bodies may include `request_id` for support.

## Workers

Celery tasks bind `celery_task_id` and `celery_task_name` into structlog context for the duration of the task. The index pipeline task retries transient failures with backoff; full crawl jobs are not auto-retried at the Celery layer to avoid duplicate long runs.
