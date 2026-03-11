# Sorce MVP – Development Commands
# Usage: make <target>

.PHONY: dev-backend dev-web dev-worker dev-mobile test-backend test-mobile lint-backend lint-mobile lint test docker-up docker-down

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

dev-backend:
	PYTHONPATH=apps:packages:. uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd apps/web && npx vite --host 0.0.0.0 --port 5173

dev-worker:
	PYTHONPATH=apps:packages:. python -m apps.worker.agent

test-backend:
	PYTHONPATH=apps:packages:. pytest tests/ -v -s --tb=short

lint-backend:
	ruff check . --select E,W,F,I
	PYTHONPATH=apps:packages:. mypy apps/api/ apps/worker/ packages/backend/ shared/ --ignore-missing-imports

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
# Full-stack audit (all debugging tools: ruff, mypy, bandit, semgrep, etc.)
# ---------------------------------------------------------------------------

audit:
	node scripts/full-stack-audit.js --skip-install

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
	psql $(DATABASE_URL) -f infra/postgres/schema.sql
	psql $(DATABASE_URL) -f infra/postgres/migrations.sql 2>/dev/null || true
	@echo "Done."
