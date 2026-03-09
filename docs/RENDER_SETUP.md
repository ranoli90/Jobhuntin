# Render Services Setup

This document describes how to connect and verify all Render services for JobHuntin.

> **Security**: Never commit `RENDER_API_KEY` to git. Use environment variables or Render Dashboard for secrets.

## Services Overview

| Service | Type | Purpose |
|---------|------|---------|
| jobhuntin-api | Web Service (Docker) | FastAPI backend |
| jobhuntin-web | Static Site | Vite/React frontend |
| jobhuntin-seo-engine | Background Worker | SEO content generation |
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

## Verify with Script

```bash
export RENDER_API_KEY=rnd_your_key
python scripts/render_connect.py
```

## Trigger Deploy via API

```bash
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.render.com/v1/services/srv-d63l79hr0fns73boblag/deploys" \
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

## Troubleshooting

1. **Deploy fails (update_failed)**: Check build logs in Render Dashboard → jobhuntin-api → Logs. Common causes: Docker build timeout, missing env vars, pip install failures.
2. **API won't start**: Verify DATABASE_URL, REDIS_URL, JWT_SECRET, RESEND_API_KEY, EMAIL_FROM.
3. **Health returns 404**: Ensure you're using the correct URL (slug-based: sorce-api.onrender.com). Free-tier services may return 404 when sleeping.
4. **Health returns 502**: Service is starting or crashed. Check runtime logs in Dashboard.
5. **Magic links not sent**: Check RESEND_API_KEY and EMAIL_FROM.
6. **CORS errors**: Ensure APP_BASE_URL and CORS_ORIGINS include your frontend URL.
