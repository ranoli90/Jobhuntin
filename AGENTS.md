# AGENTS.md

## Cursor Cloud specific instructions

### Architecture overview

JobHuntin (Sorce) is a monorepo with Python backend (FastAPI) and multiple JS/TS frontends (Vite/React). See `README.md` for the full project map.

### Running services locally

**PostgreSQL** must run with SSL enabled. The DSN resolver in `packages/shared/db.py` (`resolve_dsn_ipv4`) forces `sslmode=require` on all connections, so a plain Docker Postgres without SSL will fail. Start it with self-signed certs:

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

**FastAPI backend** — there is a root-level `shared/` directory that shadows `packages/shared/`. You must ensure `packages` is first in `sys.path`:

```bash
python3 -c "
import sys; sys.path.insert(0, 'packages'); sys.path.insert(1, 'apps')
from uvicorn import run
run('api.main:app', host='0.0.0.0', port=8000, log_level='info')
"
```

Required env vars: `DATABASE_URL`, `ENV=local`, `CSRF_SECRET`, `JWT_SECRET`. Copy `.env.example` to `.env` and set `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sorce`.

**Web frontend**: `cd apps/web && npx vite --host 0.0.0.0 --port 5173`

### Lint, test, build

- **Python lint**: `source .venv/bin/activate && ruff check . --select E,W,F,I` (pre-existing warnings exist)
- **Python tests**: `source .venv/bin/activate && PYTHONPATH=apps:packages DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sorce" pytest tests/ -v -s --tb=short`
  - Integration tests need `auth.users` entries (foreign key); use `-k "not integration"` to skip them.
- **Web build**: `cd apps/web && npx vite build`
- Makefile targets: `make lint-backend`, `make test-backend`, `make dev-backend`

### Known issues

- Root `/workspace/shared/` directory shadows `packages/shared/` when running from workspace root — always put `packages` first in PYTHONPATH or sys.path.
- Migration `026_complete_tenant_isolation.sql` references role `authenticated` (Supabase-specific) — errors are expected locally.
- `conftest.py` references `job_match_cache` table that doesn't exist in current schema — 1 test error in `test_failure_drills.py`.
- The magic-link auth endpoint (`POST /auth/magic-link`) will produce an FK error locally unless the randomly-generated user UUID is pre-inserted into `auth.users`. This is expected; the endpoint is otherwise functional.
- Docker daemon must be started with `dockerd &>/tmp/dockerd.log &` before running any containers. Use `sudo` for docker commands since the default user is not in the `docker` group.
- The `.env` file is pre-configured with local dev defaults. If missing, copy from `.env.example` and set `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sorce`.
