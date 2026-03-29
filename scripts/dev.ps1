# Start only Postgres + Redis for local API/Next development (Docker required).
# Then run backend (uvicorn) and frontend (npm run dev) in separate terminals.

Set-Location $PSScriptRoot\..
docker compose up -d postgres redis
Write-Host "Postgres (5432) and Redis (6379) are up. Configure backend/.env and run uvicorn + celery + npm run dev. See README.md."
