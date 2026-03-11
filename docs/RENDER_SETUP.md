# Render Services Setup

This document describes how to connect and verify all Render services for JobHuntin.

> **Security**: Never commit `RENDER_API_KEY` to git. Use environment variables or Render Dashboard for secrets.

## Services Overview

| Service | Type | Purpose |
|---------|------|---------|
| jobhuntin-api | Web Service (Python or Docker) | FastAPI backend |
| jobhuntin-web | Static Site | Vite/React frontend |
| jobhuntin-seo-engine | Background Worker (Node) | SEO content generation |
| jobhuntin-job-sync | Background Worker (Python) | JobSpy job sync |
| jobhuntin-job-queue | Background Worker (Python) | Background job queue |
| jobhuntin-follow-up-reminders | Background Worker (Python) | Follow-up reminders |
| sorce-auto-apply-agent | Background Worker (Python) | Auto-apply Playwright agent |
| jobhuntin-job-alerts-daily | Cron | Daily job alerts |
| jobhuntin-job-alerts-weekly | Cron | Weekly job alerts |
| jobhuntin-weekly-digest | Cron | Weekly email digest |
| jobhuntin-db | PostgreSQL | Primary database |
| jobhuntin-redis | Redis | Magic-link replay protection, caching |

## Required Connections

### API → Database
- **DATABASE_URL**: Set in Render Dashboard (Environment) or via linked Postgres.
- Go to jobhuntin-api → Environment → Add from Database (jobhuntin-db).

### API → Redis
- **REDIS_URL**: Set in Render Dashboard.
- Get from jobhuntin-redis → Connect → Internal Redis URL.

### API → Resend
- **RESEND_API_KEY**: From [Resend Dashboard](https://resend.com/api-keys).
- **EMAIL_FROM**: e.g. `JobHuntin <noreply@yourdomain.com>`.

### Web → API
- **VITE_API_URL**: Must point to API URL (e.g. `https://jobhuntin-api.onrender.com` or custom domain).
- **VITE_APP_BASE_URL**: Frontend URL (e.g. `https://jobhuntin.com`).

### API → Web (for CORS, magic links)
- **APP_BASE_URL**: Same as VITE_APP_BASE_URL.
- **API_PUBLIC_URL**: API URL (for magic-link verify redirect).
- **CSRF_SECRET**: Required in production. See [Production Auth & CSRF](PRODUCTION_AUTH_CSRF.md) for auth architecture.
- **CORS_ALLOWED_ORIGINS**: Optional; comma-separated origins if you need to override defaults.

## Variables to Set in Render Dashboard

For each service, set these in the dashboard (sync: false or [REDACTED] in render.yaml):

| Variable | Service(s) | Purpose |
|----------|------------|---------|
| DATABASE_URL | API, workers, crons | PostgreSQL connection |
| REDIS_URL | API, SEO, auto-apply | Redis for caching/sessions |
| JWT_SECRET | API, auto-apply | Token signing |
| CSRF_SECRET | API, auto-apply | CSRF protection |
| LLM_API_KEY | API, SEO, auto-apply | OpenRouter/LLM |
| RESEND_API_KEY | API, weekly-digest, job-alerts | Email (magic links, digests, alerts) |
| EMAIL_FROM | API, weekly-digest, job-alerts | Sender address |
| STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET | API | Payments |
| VITE_API_URL, VITE_APP_BASE_URL | Web | Frontend API/base URL |
| GOOGLE_SERVICE_ACCOUNT_KEY | SEO | Search Console (JSON) |
| LLM_API_BASE, LLM_MODEL, STORAGE_TYPE, APP_BASE_URL, API_PUBLIC_URL | Per service | See .env.example |

## Verify with Script

```bash
export RENDER_API_KEY=rnd_your_key
python scripts/render_connect.py           # Verify only
python scripts/render_connect.py --fix     # Add missing API_PUBLIC_URL, env
```

## Trigger Deploy via API

```bash
# Replace <SERVICE_ID> with your API service ID from Render Dashboard
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.render.com/v1/services/<SERVICE_ID>/deploys" \
  -d '{}'
```

## Health Checks

- **API**: `GET /health` (simple), `GET /healthz` (DB + Redis)
- **Web**: Static site, no health endpoint.

## API URL

Render uses the service **slug** for the public URL. The jobhuntin-api service slug is `sorce-api`, so the API URL is typically:
- `https://<service-slug>.onrender.com` (e.g. sorce-api, or your custom domain)

Set this URL in your Web and API environment variables.

## Logs

Render does not expose deploy/build logs via the public API. To view logs:
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select **jobhuntin-api** → **Logs**
3. Filter by Build or Runtime logs

## Build Modes

- **render.yaml** (native Python): Uses `pip install` + `uvicorn` directly. Requires `PYTHONPATH=apps:packages:.` in startCommand and envVars for API and all Python workers. Web uses `npm ci` from repo root (workspace).
- **render-blueprint.yaml** (Docker for API, Node for SEO): API uses Dockerfile; SEO worker uses Node (same as render.yaml). Web uses `npm ci` from repo root.

## Troubleshooting

1. **Deploy fails (update_failed)**: Check build logs in Render Dashboard → jobhuntin-api → Logs. Common causes: Docker build timeout, missing env vars, pip install failures.
2. **ModuleNotFoundError (api, shared, packages)**: Ensure `PYTHONPATH=apps:packages:.` is set in the service's startCommand and envVars (for native Python builds).
2. **API won't start**: Verify DATABASE_URL, REDIS_URL, JWT_SECRET, RESEND_API_KEY, EMAIL_FROM.
3. **Health returns 404**: Ensure you're using the correct URL (slug-based: sorce-api.onrender.com). Free-tier services may return 404 when sleeping.
4. **Health returns 502**: Service is starting or crashed. Check runtime logs in Dashboard.
5. **Magic links not sent**: Check RESEND_API_KEY and EMAIL_FROM.
6. **CORS errors**: Ensure APP_BASE_URL and CORS_ALLOWED_ORIGINS include your frontend URL.
