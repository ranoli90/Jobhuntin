---
description: Production readiness checklist for CI/CD, secrets, and SEO
---

# Production Readiness Checklist

## 🔴 CRITICAL — Must Fix Before Production

### 1. Rotate Leaked Database Credentials
**File:** `scripts/temp.env` (now removed from git tracking)
**Issue:** The file contained plaintext PostgreSQL credentials:
```
postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a:5432/jobhuntin
```
**Action Required:**
1. ✅ File removed from git tracking (`git rm --cached`)
2. ✅ Added to `.gitignore`
3. ⚠️ **YOU MUST rotate this database password** — it's in git history
4. Run `git filter-branch` or use BFG Repo-Cleaner to remove from history
5. Force-push the cleaned history

### 2. Missing GitHub Secrets
The following secrets are referenced in workflows but **not configured**:

| Secret | Used In | Status |
|--------|---------|--------|
| `RENDER_SEO_WORKER_ID` | `deploy-render-seo.yml` (lines 70, 83) | ❌ **MISSING** |
| `CODECOV_TOKEN` | `ci.yml` | ❌ **MISSING** |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | `deploy-render-seo.yml`, `seo-refresh.yml` | ❌ **MISSING** (optional, gracefully handled) |

**To add:**
```bash
# Required for SEO worker deployment
gh secret set RENDER_SEO_WORKER_ID --body "srv-XXXX" --repo ranoli90/sorce

# Required for code coverage
gh secret set CODECOV_TOKEN --body "YOUR_TOKEN" --repo ranoli90/sorce

# Optional — needed for Google URL submission
gh secret set GOOGLE_SERVICE_ACCOUNT_KEY --body '{"type":"service_account",...}' --repo ranoli90/sorce
```

## 🟡 SEO Engine Issues Fixed
 
### 3. Fabricated Schema Data & Client-Side Fixes
- ✅ **Client-Side Database Usage**: Fixed `apps/web/src/lib/redis.ts` import in `Onboarding.tsx` by creating `BrowserCacheService`.
- ✅ **Console Log Cleanup**: Wrapped excessive logs in `if (import.meta.env.DEV)`.
- ✅ **PII in Logs**: Masked email addresses in `magicLinkService.ts`.
- ✅ **Fake SEO Data**: Removed fabricated ratings and random job counts from `seoOptimizer.ts`.

### 4. Smart SEO Engine Corrections
**File:** `apps/web/scripts/seo/smart-seo-engine.ts`
- ✅ Fixed header claiming "Gemini 2.0 Flash" when code actually uses GPT-4o-mini
- ✅ Fixed inconsistent cost claims ($0.10/1M vs actual $0.15/1M)
- ✅ Removed debug log exposing first 50 chars of private key
- ✅ Removed log exposing service account email
- ✅ Made MODEL configurable via `LLM_MODEL` env var

### 5. Submit-to-Google Script
**File:** `apps/web/scripts/seo/submit-to-google.ts`
- ✅ Removed `DEBUG:` log that exposed API key presence

### 6. SEO Audit Script
**File:** `apps/web/scripts/seo/perform-seo-audit.ts`
- ✅ Fixed misleading "free models" log when paid models are used

## 🟢 CI/CD Pipeline Status

### Workflows Verified
| Workflow | Status | Key Changes |
|----------|--------|-------------|
| `ci.yml` | ✅ | Concurrency, caching, Buildx, E2E re-enabled |
| `staging-deploy.yml` | ✅ | Fixed broken job deps, proper smoke tests |
| `deploy-render-seo.yml` | ✅ | Removed leaked token & hardcoded IDs |
| `seo-refresh.yml` | ✅ | Pinned action version (@v0.8.0), safe git commits |
| `dependabot.yml` | ✅ | All ecosystems covered, weekly GHA updates |

### Requirements Updated
| File | Changes |
|------|---------|
| `requirements.txt` | Added `sentry-sdk[fastapi]`, organized sections, removed duplicate entries |
| `requirements-dev.txt` | Added `pytest-cov`, `psycopg2-binary`, version pins |

### .gitignore Updated
- Added `scripts/**/.env`
- Added `scripts/**/temp.env`
- Added `*.env.local`, `*.env.*.local`

## 📋 Remaining Configuration Tasks

1. **Rotate database password** (CRITICAL)
2. **Add `RENDER_SEO_WORKER_ID` secret** to GitHub
3. **Add `CODECOV_TOKEN` secret** to GitHub (get from codecov.io)
4. **Add `GOOGLE_SERVICE_ACCOUNT_KEY` secret** when ready for Google Indexing
5. **Clean git history** with BFG Repo-Cleaner to remove `temp.env`
6. **Add Render environment protection rules** (staging/prod) in Render dashboard
7. **Consider adding `CODEOWNERS` file** for PR review requirements
