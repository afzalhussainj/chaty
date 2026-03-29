# Unix/macOS helpers. On Windows, use equivalent PowerShell or `docker compose` directly.

.PHONY: up down logs ps migrate seed test-backend test-frontend

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f backend worker

ps:
	docker compose ps

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python scripts/seed_demo_tenant.py

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test
