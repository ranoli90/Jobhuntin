# Render Setup Checklist

Use this checklist to ensure the project is fully configured on Render.

## Services

| Service | ID | URL |
|---------|-----|-----|
| jobhuntin-api | srv-d63l79hr0fns73boblag | https://sorce-api.onrender.com |
| jobhuntin-web | srv-d63spbogjchc739akan0 | https://sorce-web.onrender.com |
| jobhuntin-seo-engine | srv-d66aadsr85hc73dastfg | (background worker) |

## Required Environment Variables

### jobhuntin-api (Backend)

| Variable | Required | Notes |
|----------|----------|-------|
| DATABASE_URL | ✅ | PostgreSQL connection string (Render Postgres or external) |
| REDIS_URL | ✅ | **Required in prod** – API fails startup without it. Create Redis on Render. |
| API_PUBLIC_URL | ✅ | `https://sorce-api.onrender.com` – for magic-link httpOnly cookies |
| APP_BASE_URL | ✅ | `https://sorce-web.onrender.com` |
| CSRF_SECRET | ✅ | Generate: `python scripts/generate_secrets.py` |
| JWT_SECRET | ✅ | Generate: `python scripts/generate_secrets.py` |
| WEBHOOK_SIGNING_SECRET | ✅ | Generate or set in dashboard |
| LLM_API_KEY | ✅ | OpenRouter API key |
| RESEND_API_KEY | Optional | For magic-link emails |
| STRIPE_* | Optional | If using billing |

### jobhuntin-web (Frontend – build-time)

| Variable | Required | Notes |
|----------|----------|-------|
| VITE_API_URL | ✅ | `https://sorce-api.onrender.com` |
| VITE_APP_BASE_URL | ✅ | `https://sorce-web.onrender.com` |
| NODE_VERSION | ✅ | `20` |

### jobhuntin-seo-engine

| Variable | Required | Notes |
|----------|----------|-------|
| GOOGLE_SERVICE_ACCOUNT_KEY | ✅ | JSON for Google Indexing API |
| GOOGLE_SEARCH_CONSOLE_SITE | ✅ | `https://sorce-web.onrender.com` |
| LLM_API_KEY | ✅ | OpenRouter |
| DATABASE_URL | Optional | For progress tracking |
| REDIS_URL | Optional | For caching |

## Sync Env Vars via Script

```bash
export RENDER_API_KEY=your-key
make render-sync-envs
```

Or: `PYTHONPATH=packages python scripts/sync_render_envs.py`

This updates APP_BASE_URL, API_PUBLIC_URL, VITE_*, and other non-secret vars. **Secrets must be set manually** in the Render dashboard.

## Critical: Redis

The API **requires** REDIS_URL in production. Without it, startup fails.

1. Create a Redis instance in Render (Dashboard → New → Redis)
2. Copy the Internal Redis URL
3. Add to jobhuntin-api env vars: `REDIS_URL=redis://...`

## Verify

```bash
# Check API health
curl https://sorce-api.onrender.com/health

# Verify Render connection
make render-api-verify
```

## Redeploy After Env Changes

Env var changes require a redeploy. Either:

- Trigger via Render dashboard: Manual Deploy → Deploy latest commit
- Or: `render deploys create srv-d63l79hr0fns73boblag` (with Render CLI)
