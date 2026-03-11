# Dashboard & API Audit Findings

**Generated:** 2026-03-11  
**Sources:** 3 sub-agent audits (dashboard, API security, frontend state/UX)

---

## CRITICAL

| ID | Finding | File | Status |
|----|---------|------|--------|
| C1 | Unsanitized `notes` in UpdateApplicationStatusBody — XSS risk | apps/api/user.py:826 | fixed |
| C2 | `app.job_title` null dereference in ApplicationsView search | Dashboard.tsx:1630 | fixed |
| API-1 | Error leakage in production (detail=str(e)) | multiple | deferred |

---

## HIGH

| ID | Finding | File | Status |
|----|---------|------|--------|
| H1 | PATCH application status omits tenant_id in WHERE | apps/api/user.py:868 | fixed |
| H2 | monthlyApps = total, not monthly | useApplications.ts:153 | fixed (totalApps) |
| H3 | Reset filters incomplete (sweep-complete) | Dashboard.tsx:1100 | fixed |
| API-3 | Resume integration GET/POST no ownership check | resume_integration.py | fixed |
| API-4 | batch_prepare_resumes no ownership validation | resume_integration.py:228 | fixed |
| API-5 | prepare_resume ownership not validated | resume_integration.py:151 | fixed |
| API-6 | Missing UUID validation on resume integration IDs | resume_integration.py | fixed |
| FE-1 | JobAlerts edit modal never opens (missing setShowCreateForm) | JobAlerts.tsx:149 | fixed |
| FE-2 | JobAlerts submit always calls create, not update | JobAlerts.tsx:355 | fixed |

---

## MEDIUM

| ID | Finding | File | Status |
|----|---------|------|--------|
| M1 | handleApplicationAction errors not shown to user | Dashboard.tsx:1642 | fixed |
| M2 | resetFilters out of sync with local inputs | Dashboard.tsx:817 | fixed (already synced) |
| M3 | Settings profile effects overwrite user edits | Settings.tsx:45 | fixed |
| M4 | app.job_title, app.company null checks | ApplicationsView, Dashboard | fixed |
| M5 | JobAlerts modal: no focus trap, no Escape | JobAlerts.tsx | fixed |
| M6 | JobCard touch handlers not cleaned on unmount | Dashboard.tsx:125 | fixed |
| API-7 | DB pool no command_timeout | dependencies.py | fixed |
| API-8 | Voice session user_id from request body | voice_interviews.py | fixed |

---

## LOW

| ID | Finding | File | Status |
|----|---------|------|--------|
| L1 | ApplicationsView/HoldsView no error UI | ApplicationsView, HoldsView | fixed |
| L2 | Sort select missing aria-label | Dashboard.tsx | fixed |
| L3 | JobAlerts search input missing aria-label | JobAlerts.tsx | fixed |
| L4 | JobsView filters not in URL | Dashboard.tsx | deferred |

---

**Priority:** Fix C1, C2, H1–H3, API-3–6, FE-1, FE-2 first.
