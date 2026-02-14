# AUTONOMOUS FIX AGENT PROMPT - JobHuntin/Sorce Platform

## ROLE
You are an autonomous senior software engineer tasked with fixing all issues identified in the Master Audit Report. Work through sprints autonomously, verifying each fix before proceeding. You have full access to read, write, and execute commands.

## PROJECT CONTEXT

### Repository: C:\Users\Administrator\Desktop\Quickly
### Tech Stack:
- Frontend: React/Vite/TypeScript (apps/web)
- Admin: React/Vite/TypeScript (apps/web-admin)
- Mobile: Expo/React Native (mobile)
- Extension: Chrome Extension (apps/extension)
- Backend: FastAPI/Python (apps/api, packages/backend)
- Database: PostgreSQL (Render)
- Auth: Supabase Auth with JWT
- LLM: OpenRouter with Nvidia Nemotron

### Architecture:
apps/api/ - FastAPI v1 endpoints
apps/web/ - Vite/React JobHuntin UI
apps/web-admin/ - Operator dashboard
apps/extension/ - Chromium extension
packages/backend/ - Domain models, LLM orchestration
packages/shared/ - Config, logging, telemetry
mobile/ - Expo/React Native client

## WORKFLOW PROTOCOL

### Before Each Fix:
1. READ the target file completely
2. IDENTIFY exact lines/sections to modify
3. UNDERSTAND surrounding context
4. VERIFY no other code depends on broken pattern

### After Each Fix:
1. RUN syntax check: npx tsc --noEmit (frontend) or python -m py_compile (backend)
2. RUN lint: npx eslint or ruff check
3. RUN related tests: pytest or npm test
4. VERIFY fix doesn't break existing functionality

### Sprint Completion:
1. RUN full test suite
2. CHECK for regressions
3. PROCEED to next sprint only if all tests pass


## SPRINT 1: CRITICAL SECURITY FIXES

### Task 1.1: Remove Hardcoded Database Credentials
File: packages/shared/config.py:40
Problem: Production database password hardcoded in source

BEFORE (line 40):
database_url: str = "postgresql://dpg-d66ck524d50c73bas62g-a:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/dpg-d66ck524d50c73bas62g"

AFTER:
database_url: str = Field(default="", description="PostgreSQL connection URL from DATABASE_URL env var")

Verification: python -c "from packages.shared.config import Settings; s = Settings(); print('PASS' if not s.database_url or '60BpsY' not in str(s.database_url) else 'FAIL')"

---

### Task 1.2: Add Authentication to CCPA Endpoints
File: apps/api/ccpa.py
Problem: No auth check on GET /requests/{id} and POST /requests/{id}/process

Add import: from api.auth import get_current_user_id

Modify GET endpoint (around line 132):
@router.get("/requests/{request_id}", response_model=RequestStatusResponse)
async def get_request_status(
    request_id: str,
    user_id: str = Depends(get_current_user_id),  # ADD THIS
    db: asyncpg.Pool = Depends(_get_pool),
) -> RequestStatusResponse:
    row = await db.fetchrow(
        "SELECT * FROM ccpa_requests WHERE id = $1 AND user_id = $2",
        request_id, user_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")

Modify POST endpoint similarly (around line 213).

Verification: Start API, access endpoint without auth token - should return 401

---

### Task 1.3: Add Authentication to Zapier Hook Deletion
File: apps/api/integrations.py:441-453
Problem: No auth check on DELETE /zapier/hooks/{hook_id}

Add to function signature:
async def delete_zapier_hook(
    hook_id: str,
    user_id: str = Depends(_get_user_id),  # ADD THIS
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    owner = await db.fetchval(
        "SELECT user_id FROM zapier_integrations WHERE id = $1", hook_id
    )
    if owner != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

Verification: Delete hook without auth - should return 401

---

### Task 1.4: Add Authentication to AI Endpoints
File: apps/api/ai.py
Problem: Multiple endpoints lack JWT validation

Add import: from api.auth import get_current_user_id

Add to EACH AI endpoint function signature:
async def <endpoint_name>(
    ...,
    user_id: str = Depends(get_current_user_id),  # ADD TO ALL
    ...
):

Affected endpoints (ALL must have auth):
/ai/suggest-roles, /ai/suggest-salary, /ai/suggest-locations
/ai/match-job, /ai/match-jobs-batch, /ai/semantic-match
/ai/semantic-match/batch, /ai/tailor-resume, /ai/ats-score
/ai/generate-cover-letter

Verification: curl http://localhost:8000/ai/suggest-roles -X POST without auth - should return 401


---

### Task 1.5: Fix SQL Injection in GDPR Module
File: apps/api/gdpr.py:150-157, 214-219
Problem: Table/column names interpolated into SQL

Define whitelist at top of file:
ALLOWED_TABLES = {
    "users": "user_id",
    "profiles": "user_id", 
    "applications": "user_id",
    "application_inputs": "user_id",
    "events": "user_id",
    "answer_memory": "user_id",
    "profile_embeddings": "user_id",
}

Replace f-string SQL with validated queries - only use table names from whitelist.

Verification: pytest tests/test_gdpr.py -v

---

### Task 1.6: Implement Admin Role Verification
File: apps/web-admin/src/App.tsx:81-96
Problem: No role check - any authenticated user gets admin access

Add role checking function:
const checkAdminRole = async (session: Session) => {
  try {
    const response = await fetch('/api/admin/check-role', {
      headers: { Authorization: 'Bearer ' + session.access_token }
    });
    const data = await response.json();
    return data.is_admin === true;
  } catch { return false; }
};

Modify auth check in App component:
- Add isAdmin state
- Check role after session loads
- If !isAdmin, show AccessDenied component

Create AccessDenied component showing "Access Denied - You do not have admin privileges"

Backend endpoint (apps/api/admin.py):
@router.get("/check-role")
async def check_admin_role(user_id: str = Depends(get_current_user_id), db = Depends(get_pool)):
    role = await db.fetchval("SELECT role FROM tenant_members WHERE user_id = $1", user_id)
    return {"is_admin": role in ("OWNER", "ADMIN", "COMPLIANCE_OFFICER")}

Verification: Login as non-admin, access admin dashboard - should show Access Denied

---

### Task 1.7: Enable CSRF Middleware
File: apps/api/main.py
Problem: CSRF middleware imported but never enabled

Find import: from shared.middleware import setup_csrf_middleware, setup_request_id_middleware

After app creation, add:
app = FastAPI(...)
setup_request_id_middleware(app)
setup_csrf_middleware(app)  # ADD THIS LINE

Verify shared/middleware.py has setup_csrf_middleware function implementing CSRFMiddleware.

Verification: Make POST request without CSRF token - should return 403

---

### Task 1.8: Fix Bot Import in Login.tsx
File: apps/web/src/pages/Login.tsx:12
Problem: Bot icon used but not imported

Find import statement around line 12, add Bot:
import {
  ArrowRight, Mail, Lock, Sparkles, AlertCircle,
  Chrome, Linkedin, CheckCircle, ArrowLeft,
  ShieldCheck, MailCheck, Bot  // ADD Bot HERE
} from 'lucide-react';

Verification: cd apps/web && npx tsc --noEmit - should pass without Bot errors

---

### Task 1.9: Add Reset Function to useCoverLetter Hook
File: apps/web/src/hooks/useCoverLetter.ts
Problem: Missing reset function causes crash

Add reset function before return statement:
const reset = useCallback(() => {
  setResult(null);
  setError(null);
  setGenerationState({
    isGenerating: false,
    currentJobId: null,
    progress: 0,
    estimatedTime: 0,
  });
}, []);

Add to return object:
return {
  generate,
  reset,  // ADD THIS
  loading,
  error,
  result,
  // ... rest
};

Verification: cd apps/web && npx tsc --noEmit

---

### Task 1.10: Fix Corrupted requirements.txt
File: requirements.txt:20
Problem: Corrupted redis declaration

Find line with corrupted text like "redis>=5.0.0r e d i s"
Replace entire line with:
redis>=5.0.0

Verification: pip install -r requirements.txt --dry-run - should parse without errors


## SPRINT 2: HIGH PRIORITY FIXES

### Task 2.1: Fix Path Injection in Magic Link Service
File: apps/web/src/services/magicLinkService.ts
Problem: return_to parameter not properly sanitized

Enhance sanitization:
const ALLOWED_RETURN_PATHS = ['/app', '/app/dashboard', '/app/matches', '/app/onboarding', '/app/settings', '/app/admin'];

function sanitizeReturnTo(returnTo: string | null): string {
  if (!returnTo) return '/app';
  const decoded = decodeURIComponent(returnTo);
  if (decoded.includes('..') || decoded.includes('//') || decoded.includes('\')) return '/app';
  if (decoded.toLowerCase().startsWith('javascript:')) return '/app';
  if (!decoded.startsWith('/')) return '/app';
  const isAllowed = ALLOWED_RETURN_PATHS.some(path => decoded.startsWith(path));
  return isAllowed ? decoded : '/app';
}

Verification: Test with '../../../etc/passwd' - should return '/app'

---

### Task 2.2: Add Token Refresh for Google/Microsoft Integrations
File: packages/backend/domain/calendar.py
Problem: Tokens stored but never refreshed

Add refresh method to GoogleCalendarClient:
async def refresh_access_token(self) -> str:
    if not self.refresh_token:
        raise ValueError("No refresh token available")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Token refresh failed")
            data = await resp.json()
            self.access_token = data["access_token"]
            return self.access_token

Add auto-refresh wrapper that checks token validity and refreshes if expired.

Verification: Test calendar operations after 1+ hour - should auto-refresh

---

### Task 2.3: Fix LinkedIn API Authentication
File: packages/backend/domain/job_boards.py:211-212
Problem: Using client_secret as Bearer token (incorrect OAuth)

Implement proper OAuth client credentials flow:
- Add _get_access_token method that calls LinkedIn OAuth endpoint
- Store access token in instance variable
- Use access token (not client_secret) in Bearer header

Verification: Run LinkedIn job search - should return results

---

### Task 2.4: Add Undo for Job Swipe
File: apps/web/src/pages/Dashboard.tsx
Problem: No undo mechanism for swipe decisions

Add swipe history state:
const [swipeHistory, setSwipeHistory] = useState<Array<{jobId: string; direction: 'left' | 'right'; index: number}>>([]);

Modify handleSwipe to save to history.

Add undo function that restores previous index from history.

Add undo button to UI (disabled when history empty).

Import Undo2 from lucide-react.

Verification: Swipe a job, click undo, should return to previous job

---

### Task 2.5: Add Missing Mobile Dependencies
File: mobile/package.json
Problem: Missing critical dependencies

Run: cd mobile && npm install --save expo-document-picker expo-file-system expo-clipboard @react-navigation/native @react-navigation/native-stack react-native-screens react-native-safe-area-context react-native-url-polyfill @react-native-async-storage/async-storage expo-device

Verification: cd mobile && npx expo start - should not show missing module errors

---

### Task 2.6: Fix "Details" Button on Applications
File: apps/web/src/pages/Dashboard.tsx:748-749
Problem: Details button has no onClick handler

Add state for selectedApplication and showApplicationDetailModal.

Add onClick to Details button that sets selectedApplication and opens modal.

Create ApplicationDetailModal component or use existing one.

Verification: Click Details button - should open modal with application details

---

### Task 2.7: Disable Non-Functional Login Tabs
File: apps/web/src/pages/Login.tsx
Problem: Password/Register tabs and Social login buttons show error instead of being disabled

Add disabled attribute and opacity-50 cursor-not-allowed classes to:
- Password tab
- Register tab
- Google button
- LinkedIn button

Add title="Coming Soon" for hover tooltip.

Verification: Disabled buttons should be greyed out and not clickable

---

### Task 2.8: Persist LinkedIn URL in Onboarding
File: apps/web/src/pages/Onboarding.tsx
Problem: LinkedIn URL collected but lost

Ensure linkedinUrl is included in profileData when calling updateProfile in handleComplete.

Add useEffect to restore linkedinUrl when returning to preferences step.

Verification: Enter LinkedIn URL, complete onboarding, check profile - URL should be saved


## VERIFICATION COMMANDS

After each sprint, run:

# Backend
cd C:\Users\Administrator\Desktop\Quickly
python -m pytest tests/ -v --tb=short
ruff check apps/ packages/
python -m mypy apps/api --ignore-missing-imports

# Frontend
cd apps/web && npx tsc --noEmit && npx eslint src/ --max-warnings=0 && npm run build

# Admin
cd apps/web-admin && npx tsc --noEmit && npm run build

# Extension
cd apps/extension && npx tsc --noEmit && npm run build

# Mobile
cd mobile && npx expo start --no-dev

## FINAL VALIDATION CHECKLIST

Before marking complete, verify ALL items:

[ ] No hardcoded credentials in source code
[ ] All API endpoints require authentication
[ ] Admin dashboard requires admin role
[ ] No SQL injection vulnerabilities
[ ] No XSS vulnerabilities  
[ ] CSRF protection enabled
[ ] Undo functionality for job swipes
[ ] Mobile app builds without errors
[ ] All login tabs properly disabled/functional
[ ] LinkedIn URL persists through onboarding
[ ] All tests passing
[ ] No TypeScript errors
[ ] No lint errors

## EXECUTION INSTRUCTIONS

1. Read this prompt completely
2. Start with Sprint 1, Task 1.1
3. Complete each task in order
4. Run verification after each task
5. If verification fails, fix and retry
6. Only proceed to next task after verification passes
7. At end of each sprint, run full test suite
8. Continue to next sprint only if all tests pass
9. Do NOT stop or ask for confirmation - work autonomously through all sprints
10. Report only when all sprints complete or blocked by unfixable issue
11. Do NOT summarize - just execute fixes and continue
12. Read MASTER_AUDIT_REPORT.md for additional context if needed

## FILES TO REFERENCE

- MASTER_AUDIT_REPORT.md - Complete list of all issues
- RECOMMENDATIONS.md - Sprint history and feature implementation status
- architecture-overview.md - System architecture diagrams
- launch-checklist.md - Production validation checklist
- apps/api/main.py - API entry point
- apps/web/src/pages/ - All frontend pages
- mobile/ - React Native mobile app
- apps/extension/ - Chrome extension

## CRITICAL PATH

Sprint 1 (Day 1): Security fixes - MUST complete before any other work
Sprint 2 (Day 2-3): High priority fixes - Core functionality
Sprint 3 (Day 4-5): UX improvements - User experience

Execute continuously without stopping. Fix failures immediately. Proceed autonomously.
