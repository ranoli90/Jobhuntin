# Sorce MVP – Development Commands
# Usage: make <target>

.PHONY: dev-backend dev-mobile test-backend test-mobile lint-backend lint-mobile lint test docker-up docker-down

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

dev-backend:
	PYTHONPATH=apps:packages uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	PYTHONPATH=apps:packages python -m worker.agent

test-backend:
	pytest tests/ -v -s --tb=short

lint-backend:
	ruff check . --select E,W,F,I
	PYTHONPATH=apps:packages mypy apps/api/ apps/worker/ packages/backend/ packages/shared/ --ignore-missing-imports

fmt-backend:
	ruff format .

# ---------------------------------------------------------------------------
# Mobile
# ---------------------------------------------------------------------------

dev-mobile:
	cd mobile && npx expo start

test-mobile:
	cd mobile && npx jest --passWithNoTests

lint-mobile:
	cd mobile && npx eslint src/ --ext .ts,.tsx
	cd mobile && npx tsc --noEmit

fmt-mobile:
	cd mobile && npx prettier --write "src/**/*.{ts,tsx}"

# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------

lint: lint-backend lint-mobile

test: test-backend test-mobile

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# ---------------------------------------------------------------------------
# Render API
# ---------------------------------------------------------------------------

render-api-verify:
	PYTHONPATH=packages python scripts/render_api_verify.py

render-sync-envs:
	PYTHONPATH=packages python scripts/sync_render_envs.py

# ---------------------------------------------------------------------------
# Database (local)
# ---------------------------------------------------------------------------

db-reset:
	@echo "Resetting local database..."
	docker compose down -v
	docker compose up db -d
	sleep 3
	psql $(DATABASE_URL) -c "CREATE SCHEMA IF NOT EXISTS auth; CREATE TABLE IF NOT EXISTS auth.users (id uuid PRIMARY KEY);"
	psql $(DATABASE_URL) -c "CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS \$$\$$ SELECT '00000000-0000-0000-0000-000000000000'::uuid; \$$\$$ LANGUAGE sql;"
	psql $(DATABASE_URL) -c "CREATE PUBLICATION IF NOT EXISTS supabase_realtime;"
	psql $(DATABASE_URL) -f infra/supabase/schema.sql
	for f in infra/supabase/migrations/0*.sql; do psql $(DATABASE_URL) -f "$$f"; done
	@echo "Done."
