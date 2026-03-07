# AGENTS.md

## Cursor Cloud specific instructions

### Services Overview

| Service | Purpose | How to Run |
|---------|---------|------------|
| PostgreSQL 16 | Primary database | `docker compose up db -d` (from repo root) |
| FastAPI Backend | REST API (port 8000) | `source .venv/bin/activate && PYTHONPATH=apps:packages:. uvicorn api.main:app --reload --host 0.0.0.0 --port 8000` |
| Web App | Vite/React frontend (port 5173) | `cd apps/web && npx vite --host 0.0.0.0 --port 5173` |
| Admin Dashboard | Operator UI (port 5174) | `cd apps/web-admin && npx vite --host 0.0.0.0` |

### Key Gotchas

- **PYTHONPATH**: The backend needs `PYTHONPATH=apps:packages:.` (note the `.` for the root-level `shared/` package). The Makefile only sets `apps:packages` which misses `shared/`.
- **Docker socket permissions**: After starting Docker daemon, run `sudo chmod 666 /var/run/docker.sock` to allow non-root Docker access.
- **Docker daemon**: Start with `sudo dockerd > /tmp/dockerd.log 2>&1 &` (do NOT pass `--storage-driver=fuse-overlayfs` as a flag since it's already in `/etc/docker/daemon.json`).
- **DB schema files**: The `docker-compose.yml` expects `infra/supabase/schema.sql` and `infra/supabase/migrations.sql`, which must be assembled from `migrations/001_initial_schema.sql`, `migrations/002_onboarding_tables.sql`, and `supabase/migrations/20260211_seo_engine_progress.sql`. The schema.sql must only include the "Up" migration parts (exclude `-- +migrate Down` section).
- **`.env` file**: Copy `.env.example` to `.env` and set `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sorce` for local Docker Postgres. Generate dev secrets for `CSRF_SECRET`, `JWT_SECRET`, etc.
- **JWT auth for API testing**: Create tokens with `jwt.encode({'sub': '<user-uuid>', 'aud': 'authenticated'}, '<JWT_SECRET>', algorithm='HS256')`. CSRF middleware blocks non-GET mutations without a valid CSRF cookie; use GET endpoints or browser-based testing for write operations.
- **Pre-existing lint/type errors**: `ruff check` reports ~838 errors and `mypy` reports ~351 errors — these are pre-existing in the codebase.

### Lint / Test / Build Commands

See `Makefile` for canonical commands. Key additions:
- Python lint: `ruff check . --select E,W,F,I`
- Python types: `PYTHONPATH=apps:packages:. mypy apps/api/ apps/worker/ packages/backend/ shared/ --ignore-missing-imports`
- Python tests: `PYTHONPATH=apps:packages:. pytest tests/ -v -s --tb=short`
- Web build: `cd apps/web && npx vite build`
- Web types: `cd apps/web && npx tsc --noEmit`
