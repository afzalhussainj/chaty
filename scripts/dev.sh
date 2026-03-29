#!/usr/bin/env sh
# Start only Postgres + Redis for local API/Next development.
set -e
cd "$(dirname "$0")/.."
docker compose up -d postgres redis
echo "Postgres (5432) and Redis (6379) are up. Configure backend/.env and run uvicorn + celery + npm run dev. See README.md."
