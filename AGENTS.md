# AGENTS.md

Instructions for AI agents (e.g. Cursor) working in this codebase. Use this file to bootstrap local development, run tests, and avoid common pitfalls.

## Architecture overview

JobHuntin (Sorce) is a monorepo with Python backend (FastAPI) and multiple JS/TS frontends (Vite/React). See `README.md` for the full project map.

- **APIs** – `apps/api` (FastAPI v1) and `apps/api_v2` (experimental auth, magic-link, OpenAPI)
- **Frontends** – `apps/web` (consumer UI), `apps/web-admin` (operator dashboard)
- **Worker** – `apps/worker` (Playwright FormAgent, polls PostgreSQL queues)
- **Shared** – `packages/shared` (config, logging, redis, telemetry), `packages/backend` (domain, LLM, blueprints)

---

## Running services locally

### PostgreSQL (required)

PostgreSQL must run with **SSL enabled**. The DSN resolver in `packages/shared/db.py` (`resolve_dsn_ipv4`) forces `sslmode=require` on all connections, so a plain Docker Postgres without SSL will fail. Start it with self-signed certs:

```bash
mkdir -p /tmp/pgssl && cd /tmp/pgssl
openssl req -new -x509 -days 365 -nodes -text -out server.crt -keyout server.key -subj "/CN=localhost"
sudo chown 70:70 server.key
sudo docker run -d --name sorce-db \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=sorce \
  -p 5432:5432 \
  -v /tmp/pgssl/server.crt:/var/lib/postgresql/server.crt:ro \
  -v /tmp/pgssl/server.key:/var/lib/postgresql/server.key:ro \
  postgres:16-alpine \
  -c ssl=on -c ssl_cert_file=/var/lib/postgresql/server.crt -c ssl_key_file=/var/lib/postgresql/server.key
```

After Postgres is ready, create the Supabase auth stub schema before applying the main schema:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sorce"
psql "$DATABASE_URL" -c "CREATE SCHEMA IF NOT EXISTS auth; CREATE TABLE IF NOT EXISTS auth.users (id uuid PRIMARY KEY);"
psql "$DATABASE_URL" -c "CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS \$\$ SELECT '00000000-0000-0000-0000-000000000000'::uuid; \$\$ LANGUAGE sql;"
psql "$DATABASE_URL" -f infra/supabase/schema.sql
for f in infra/supabase/migrations/0*.sql; do psql "$DATABASE_URL" -f "$f"; done
```

> **Note:** `docker compose up` uses a Postgres image without SSL. Use the manual Docker run above instead, or the `db-reset` Make target will fail when connecting from host.

### Environment

Copy `.env.example` to `.env` and set at minimum:

- `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sorce`
- `ENV=local`
- `CSRF_SECRET`, `JWT_SECRET` (generate with `python scripts/generate_secrets.py` if available)
- `API_PUBLIC_URL` - Public API URL for magic-link httpOnly cookie flow (e.g. `http://localhost:8000` locally; set to production API URL in prod)

### FastAPI backend

There is a root-level `shared/` directory that shadows `packages/shared/`. Always put `packages` first in `PYTHONPATH` or `sys.path`:

```bash
# Via Makefile (recommended)
make dev-backend

# Or manually
PYTHONPATH=apps:packages uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Worker

```bash
make dev-worker
# Or: PYTHONPATH=apps:packages python -m worker.agent
```

### Web frontends

- **Web:** `cd apps/web && npx vite --host 0.0.0.0 --port 5173`
- **Web-admin:** `cd apps/web-admin && npx vite --host 0.0.0.0 --port 5174` (may auto-increment to 5175 if 5174 is taken by Vite HMR)

### Mobile

```bash
make dev-mobile
# Or: cd mobile && npx expo start
```

---

## Lint, test, build

| Command | Description |
|---------|-------------|
| `make lint-backend` | `ruff check . --select E,W,F,I` + mypy |
| `make test-backend` | `pytest tests/ -v -s --tb=short` |
| `make fmt-backend` | `ruff format .` |
| `make lint-mobile` | ESLint + tsc in mobile |
| `make test-mobile` | Jest in mobile |

**Python tests** require `DATABASE_URL` and `PYTHONPATH=apps:packages`. Integration tests need `auth.users` entries (foreign key); use `-k "not integration"` to skip them:

```bash
source .venv/bin/activate
PYTHONPATH=apps:packages DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sorce" pytest tests/ -v -s --tb=short
```

**Web build:** `cd apps/web && npx vite build`

---

## Known issues

- **Path shadowing** – Root `/workspace/shared/` shadows `packages/shared/`. Always put `packages` first in `PYTHONPATH` or `sys.path`.
- **Migration 026** – `026_complete_tenant_isolation.sql` references role `authenticated` (Supabase-specific). Errors are expected locally.
- **conftest.py** – References `job_match_cache` table that may not exist in current schema; 1 test error in `test_failure_drills.py`.
- **Magic-link auth** – `POST /auth/magic-link` may produce an FK error locally unless the randomly-generated user UUID is pre-inserted into `auth.users`. This is expected; the endpoint is otherwise functional.
- **Docker** – Daemon must be started with `dockerd &>/tmp/dockerd.log &` before running containers. Use `sudo` for docker commands if the default user is not in the `docker` group.
- **.env** – If missing, copy from `.env.example` and set `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sorce`.

---

## Agent-specific tips

- When editing Python code, ensure imports use `packages` and `apps` correctly. `PYTHONPATH=apps:packages` is the canonical order.
- API entry point: `apps/api/main.py` – mounts `api_v2` router at `/api/v2`.
- For database changes, add migrations under `infra/supabase/migrations/` following the `NNN_description.sql` convention.
- See `CONTRIBUTING.md` for quality gates, branch conventions, and Zero-Defect / No-Scroll UI standards.
