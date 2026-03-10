# Render Environment Variables Checklist

**Last updated:** After API sync via Render API

## jobhuntin-api (srv-d63l79hr0fns73boblag)

| Variable | Status | Notes |
|----------|--------|-------|
| DATABASE_URL | ✅ Set | Internal connection string |
| REDIS_URL | ✅ Set | Required for prod (replay, revocation) |
| JWT_SECRET | ✅ Set | |
| CSRF_SECRET | ✅ Set | |
| WEBHOOK_SIGNING_SECRET | ✅ Set | |
| RESEND_API_KEY | ✅ Set | Magic link emails |
| EMAIL_FROM | ✅ Set | |
| API_PUBLIC_URL | ✅ Set | |
| APP_BASE_URL | ✅ Set | |
| STORAGE_TYPE | ✅ Set | `render` (disk at /opt/render/project/data/storage) |
| MAGIC_LINK_BIND_TO_IP | ✅ Set | `true` (P1 audit fix) |
| env | ✅ Set | `prod` |
| LLM_API_KEY | ✅ Set | |
| LLM_API_BASE | ✅ Set | |
| STRIPE_* | ✅ Set | |
| ADZUNA_* | ✅ Set | |
| AGENT_ENABLED | ✅ Set | `true` |

**Optional (set if needed):**
- DATABASE_READ_URL (read replica)
- RECAPTCHA_SECRET_KEY (bot protection)
- RESEND_WEBHOOK_SECRET

## jobhuntin-seo-engine (srv-d66aadsr85hc73dastfg)

| Variable | Status |
|----------|--------|
| DATABASE_URL | ✅ Set |
| REDIS_URL | ✅ Set |
| LLM_API_KEY | ✅ Set |
| GOOGLE_SERVICE_ACCOUNT_KEY | Set in dashboard |
| GOOGLE_SEARCH_CONSOLE_SITE | Set in dashboard |

## jobhuntin-web (srv-d63spbogjchc739akan0)

| Variable | Status |
|----------|--------|
| VITE_API_URL | Set in dashboard |
| VITE_APP_BASE_URL | Set in dashboard |
| NODE_VERSION | 20 |

## Sync Script

To sync DATABASE_URL from Postgres to all services:
```bash
# Uses RENDER_API_KEY from .env
python scripts/maintenance/fix_database_url.py
```

Or manually via API:
```bash
INTERNAL_URL=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/postgres/dpg-d66ck524d50c73bas62g-a/connection-info" \
  | jq -r '.internalConnectionString')

curl -X PUT -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"value\": \"$INTERNAL_URL\"}" \
  "https://api.render.com/v1/services/srv-d63l79hr0fns73boblag/env-vars/DATABASE_URL"
```
