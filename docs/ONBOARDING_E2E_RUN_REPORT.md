# Onboarding E2E Run Report

## Environment

- **Backend**: FastAPI on http://localhost:8000 (started with `ENV=local DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sorce`)
- **Frontend**: Vite on http://localhost:5173
- **Database**: PostgreSQL (Docker) with `sorce` database
- **Test user**: test-onboarding@example.com (ID: 4d02659a-dd8e-4102-ae10-1c8ad2510c22)

## Prerequisites Fixed

1. **Missing Python deps**: Installed `python-docx`, `pytesseract`, `reportlab`
2. **DATABASE_URL**: Must use local URL (`postgresql://postgres:postgres@localhost:5432/sorce`). Remote Render URL causes "Name or service not known"
3. **JWT token**: Must include `jti` claim for backend to accept (revocation check)
4. **Frontend mode**: Must run `npx vite` (dev) not `vite preview` (prod). In prod mode, `getAuthToken()` returns null and localStorage token is ignored

## Console Logs Captured

### Initial page load (localhost:5173)
```
[AUTH] Starting initAuth...
[AUTH] Checking for existing session...
GET http://localhost:8000/me/profile 401 (Unauthorized)
[AUTH] Auth initialization complete
```

### Auth flow
- App fetches `/me/profile` to check session
- 401 → redirect to `/login?returnTo=%2Fapp%2Fonboarding`
- No `Authorization` header sent when frontend runs in production mode (localStorage token disabled)

### Token setup (manual, for dev testing)
```javascript
localStorage.setItem('auth_token', '<JWT with sub, aud, jti>');
```
Token must be generated with correct `JWT_SECRET` from `.env` and include `jti` claim.

## Onboarding Flow Structure (from code)

| Step | Component | Purpose |
|------|-----------|---------|
| 1 | WelcomeStep | Introduction |
| 2 | ResumeStep | Upload resume, parse skills |
| 3 | SkillReviewStep | Review extracted skills |
| 4 | ConfirmContactStep | Verify contact info |
| 5 | PreferencesStep | Job preferences (location, salary, remote) |
| 6 | WorkStyleStep | Work style assessment |
| 7 | CareerGoalsStep | Career objectives |
| 8 | ReadyStep | Final confirmation |

Progress synced via `PATCH /me/profile` with `onboarding_step`, `onboarding_completed_steps`.

## Blockers Encountered

1. **Frontend prod mode**: When `npx vite build && npx vite preview` or similar is used, `import.meta.env.PROD` is true → `getAuthToken()` returns null → no Authorization header
2. **Database schema**: `profiles` table may be missing in fresh DB; migrations may need to be run
3. **CSRF**: Mutations require CSRF cookie; GET `/csrf` or similar may be needed first

## How to Run Full E2E Manually

```bash
# Terminal 1: Backend
cd /workspace && source .venv/bin/activate
export ENV=local DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sorce
PYTHONPATH=apps:packages:. uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (DEV mode - critical for localStorage auth)
cd apps/web && npx vite --host 0.0.0.0 --port 5173

# Browser:
# 1. Open http://localhost:5173
# 2. F12 → Console: localStorage.setItem('auth_token', '<token>')
# 3. Navigate to http://localhost:5173/app/onboarding
# 4. Complete each step, watch Console for errors
```

## JWT Token Generation

```python
import jwt
payload = {
    "sub": "<user-uuid>",
    "aud": "authenticated",
    "jti": "<uuid>",  # Required by backend
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
```
