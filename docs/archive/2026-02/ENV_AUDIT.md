# Render Environment Variables Audit - Updated Feb 16, 2026

## Services Found:
1. **jobhuntin-api** (srv-d63l79hr0fns73boblag) - Production API ✅
2. **jobhuntin-api-staging** (srv-d67760248b3s73c3vk40) - Staging API ✅
3. **jobhuntin-seo-engine** (srv-d66aadsr85hc73dastfg) - SEO Worker ⚠️
4. **jobhuntin-web** (srv-d63spbogjchc739akan0) - Static Site ✅
5. **PgHero** (srv-d66k2k5um26s73fvgrlg) - DB Monitor ✅

---

## Production API (jobhuntin-api) - ALL SET ✅

### Core Environment:
- ✅ ENV=prod
- ✅ APP_BASE_URL=https://jobhuntin.com

### Database & Cache:
- ✅ DATABASE_URL (PostgreSQL on Render)
- ✅ REDIS_URL (Redis on Render)

### LLM Configuration:
- ✅ LLM_API_KEY (OpenRouter)
- ✅ LLM_API_BASE=https://openrouter.ai/api/v1
- ✅ LLM_MODEL=google/gemini-2.0-flash
- ✅ LLM_FALLBACK_MODELS=openai/gpt-4o-mini
- ✅ LLM_TIMEOUT_SECONDS=45
- ✅ LLM_MAX_TOKENS=2048

### Security:
- ✅ JWT_SECRET
- ✅ CSRF_SECRET
- ✅ WEBHOOK_SIGNING_SECRET
- ✅ SSO_SESSION_SECRET

### Storage:
- ✅ STORAGE_TYPE=render_disk

### Email (Resend):
- ✅ RESEND_API_KEY
- ✅ EMAIL_FROM=JobHuntin <noreply@jobhuntin.com>

### Stripe:
- ✅ STRIPE_SECRET_KEY
- ✅ STRIPE_WEBHOOK_SECRET
- ✅ STRIPE_ENTERPRISE_PRICE_ID
- ✅ STRIPE_ENTERPRISE_ANNUAL_PRICE_ID

### JobSpy (Job Aggregation):
- ✅ JOBSPY_ENABLED=true
- ✅ JOBSPY_SOURCES=indeed,linkedin,zip_recruiter

### Legacy (can remove):
- ⚠️ ADZUNA_APP_ID - No longer used, switched to JobSpy

---

## Staging API (jobhuntin-api-staging) - ALL SET ✅

Same as production with ENV=staging

---

## SEO Worker (jobhuntin-seo-engine) - ALL SET ✅

### ✅ SET:
- ✅ LLM_API_KEY
- ✅ NODE_VERSION=20
- ✅ DATABASE_URL
- ✅ GOOGLE_SEARCH_CONSOLE_SITE=https://jobhuntin.com
- ✅ NODE_ENV=production
- ✅ **GOOGLE_SERVICE_ACCOUNT_KEY** - Full JSON updated!

### Cleaned up:
- ❌ Removed duplicate `GOOGLEd_SERVICE_ACCOUNT_KEY`
- ❌ Removed incorrect `KEY` env var

---

## Summary of Changes Made:
1. ✅ Added STORAGE_TYPE=render_disk (production & staging)
2. ✅ Added EMAIL_FROM (production & staging)
3. ✅ Added SSO_SESSION_SECRET (production)
4. ✅ Added JOBSPY_ENABLED=true (production & staging)
5. ✅ Added JOBSPY_SOURCES (production & staging)
6. ✅ Restored STRIPE_SECRET_KEY, STRIPE_ENTERPRISE_PRICE_ID, STRIPE_ENTERPRISE_ANNUAL_PRICE_ID
7. ✅ Restored RESEND_API_KEY

---

## Still Needed:
1. **GOOGLE_SERVICE_ACCOUNT_KEY** - Needs full JSON for SEO worker
2. **STRIPE_PRO_PRICE_ID** - If you have Pro tier pricing
3. **STRIPE_TEAM_BASE_PRICE_ID** - If you have Team tier pricing
4. **STRIPE_TEAM_SEAT_PRICE_ID** - If you have per-seat pricing

## Optional:
- SENTRY_DSN - Error tracking
- SLACK_WEBHOOK_URL - Alerts
- BROWSERLESS_URL - Scalable browser automation
