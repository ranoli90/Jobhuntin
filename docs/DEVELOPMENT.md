# Development Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for local PostgreSQL)
- Git

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url>
cd jobhuntin
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
npm install   # from repo root (workspace)
```

### 2. Environment

```bash
cp .env.example .env
# Edit .env: set DATABASE_URL, JWT_SECRET, CSRF_SECRET, etc.
```

Required variables (see `.env.example`):
- `DATABASE_URL` – PostgreSQL connection string
- `JWT_SECRET` – Auth token signing
- `CSRF_SECRET` – CSRF protection
- `REDIS_URL` – For magic-link replay protection (optional locally)

### 3. Database

```bash
docker compose up db -d
# Run migrations (see infra/ and migrations/)
```

### 4. Run services

**Backend** (from repo root):
```bash
PYTHONPATH=apps:packages:. uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Web app**:
```bash
cd apps/web && npx vite --host 0.0.0.0 --port 5173
```

**Admin Dashboard** (operator UI):
```bash
cd apps/web-admin && npx vite --host 0.0.0.0 --port 5174
```

**Worker** (optional, for local automation):
```bash
PYTHONPATH=apps:packages:. python -m apps.worker.agent
```
Production uses `python -m apps.worker.scaling --instances N` (see render.yaml).

### 5. Verify

- API: http://localhost:8000/health
- Web: http://localhost:5173
- Admin Dashboard: http://localhost:5174

## PYTHONPATH

The backend requires `PYTHONPATH=apps:packages:.` (note the `.` for root-level `shared/`).

## Lint & Test

```bash
# Python
ruff check . --select E,W,F,I
PYTHONPATH=apps:packages:. pytest tests/ -v -s --tb=short

# Web
cd apps/web && npm run build && npx tsc --noEmit
```

## SEO Scripts

```bash
cd apps/web
npm run seo:engine    # AI content generation
npm run seo:monitor  # Indexing verification
```

## Local Auth (API Testing)

For Bearer-token testing (e.g. E2E, scripts): JWT must include `jti` claim. Bearer-only requests skip CSRF. See [Production Auth & CSRF](PRODUCTION_AUTH_CSRF.md).

## Troubleshooting

- **Import errors**: Ensure `PYTHONPATH=apps:packages:.`
- **DB connection**: Verify `DATABASE_URL` and that PostgreSQL is running
- **CORS**: Set `APP_BASE_URL` and `CORS_ALLOWED_ORIGINS` in `.env`
