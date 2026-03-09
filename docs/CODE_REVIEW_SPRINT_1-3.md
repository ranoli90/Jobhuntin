# Code Review: Sprint 1–3 Implementation

**Review Date:** March 2026  
**Scope:** All changes from Sprint 1 (Jobs Pipeline), Sprint 2 (Profile & Matching), Sprint 3 (Onboarding)

---

## Summary

End-to-end review of the implemented features, data flow, and connections between onboarding, profile assembly, job search, and matching.

---

## Data Flow Verified

### 1. Onboarding → Profile

| Step | Data | Storage |
|------|------|---------|
| Resume upload | Parsed skills, contact, preferences | `profiles.profile_data` (canonical) |
| Resume step LinkedIn | `linkedin_url` | `profile_data.contact` (via `handleResumeNext`) |
| Skill Review | Rich skills | `user_skills` table (POST /me/skills) |
| Confirm Contact | first_name, last_name, email, phone | `profile_data.contact` |
| Preferences | location, role_type, salary_min, remote_only | `profile_data.preferences` |
| Work Style | behavioral answers | `work_style_profiles` table + `profile_data.work_style` |
| Career Goals | experience_level, urgency, etc. | `profile_data.career_goals` |

### 2. Profile Assembly → Job Scoring

`profile_assembly.assemble_profile()` merges:

- **profiles.profile_data** → skills (from resume parse), preferences, contact
- **user_skills** → explicit skills with confidence (from Skill Review)
- **work_style_profiles** → behavioral calibration (or `profile_data.work_style`)
- **user_preferences** → overlay (table often empty; profile_data is primary)

Output: `DeepProfile` used by `score_job_match()` for match_score.

### 3. Jobs API → Frontend

- `GET /me/jobs` passes `user_id` from `TenantContext`
- `search_and_list_jobs` loads profile, scores jobs, returns `match_score` (0–100)
- `sort_by`, `min_match_score` applied when profile exists
- JobsView displays match_score (handles both 0–1 and 0–100 legacy)

---

## Fixes Applied During Review

### 1. Job search pagination (user_id, no profile)

**Issue:** When `user_id` was provided but user had no profile, we fetched `fetch_limit` (up to 200) jobs but never sliced. Result: API returned up to 200 jobs instead of `limit`.

**Fix:** Always slice `result[offset:offset+limit]` when `user_id` is provided, regardless of whether profile exists.

### 2. Profile assembly salary coercion

**Issue:** `profile_data.preferences` may have `salary_min`/`salary_max` as strings (from form inputs). `DealbreakerConfig` expects `int | None`.

**Fix:** Added `_to_int()` helper in profile_assembly to coerce string/number to int.

---

## Connections Verified

| Connection | Status |
|------------|--------|
| Resume upload → profile_data | ✅ `process_resume_upload` → `ProfileRepo.upsert` |
| Skill Review → user_skills | ✅ POST /me/skills → `user_skills` table |
| LinkedIn (Resume step) → profile | ✅ `handleResumeNext` → `updateProfile({ contact: { linkedin_url } })` |
| Preferences → profile_data | ✅ `savePreferences` → `updateProfile({ preferences })` |
| profile_assembly → job scoring | ✅ `assemble_profile` → `score_job_match` |
| Jobs API → profile | ✅ `user_id` from ctx → `assemble_profile` |
| pg_notify on application create | ✅ `NOTIFY job_queue` after INSERT |
| DOCX upload | ✅ useProfile, Settings, backend all accept DOCX |

---

## Edge Cases & Notes

1. **user_preferences table:** Rarely populated by current flows. Profile assembly uses `profile_data.preferences` as primary; `user_preferences` is overlay only.

2. **jobs.skills column:** Required for scoring. Schema has it; older deployments may need migration.

3. **handleConfirmParsing:** Calls `handleResumeNext()` (persists LinkedIn, then nextStep). Correct flow.

4. **Cold start:** Uses `last_synced_at` / `created_at` instead of non-existent `j.status`. Similar-users strategy simplified to application-based popularity.

---

## Remaining Gaps (from DEEP_AUDIT_SPRINT_PLAN)

- Tenant-specific job sync (use onboarding preferences for search queries)
- Job alerts cron, email digest cron, follow-up reminders automation
- Backend validation for career_goals (experience_level, urgency)
- Missing i18n keys, work style skip handling
