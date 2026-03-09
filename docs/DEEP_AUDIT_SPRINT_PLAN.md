# Deep Audit & Sprint Plan — JobHuntin / Sorce

**Audit Date:** March 2026  
**Scope:** Onboarding, Dashboard, Jobs pipeline, Background services, Profile assembly, API completeness

---

## Sprint 1 Implementation (March 2026)

- **render.yaml**: Added `jobhuntin-job-sync` worker (JobSpy sync every 4h).
- **profile_assembly.py**: New module merging `profile_data`, `user_skills`, `work_style_profiles`, `user_preferences` into `DeepProfile`.
- **job_search.py**: Integrated `profile_assembly` + `score_job_match`; `sort_by` (match_score, salary, date_posted); returns full job dicts with `match_score`.
- **user.py**: `GET /me/jobs` now accepts `sort_by` and passes `user_id` for profile-based scoring.
- **cold_start.py**: Removed `j.status = 'ACTIVE'`; fixed `j.required_skills` → `j.skills`, `j.industry` → `j.company_industry`; simplified similar_users.

## Sprint 2 Implementation (March 2026)

- **ai.py**: `match-job` and `match-jobs-batch` now load profile server-side when client omits it; `profile` is optional.
- **deep_profile.py**: Added `deep_profile_to_llm_dict()` for LLM prompt conversion.
- **job_search.py**, **user.py**, **useJobs.ts**: Added `min_match_score` filter (0-100).
- **user.py**: `NOTIFY job_queue` on application create (ACCEPT) to wake auto-apply agent.

## Sprint 3 Implementation (March 2026)

- **useProfile.ts**, **Settings.tsx**: Accept DOCX/DOC in addition to PDF for resume upload.
- **Onboarding.tsx**: Persist LinkedIn URL when leaving Resume step (handleResumeNext); no longer lost if user skips to later steps.

---

## Executive Summary

The product has substantial infrastructure (JobSpy, match scoring, DeepProfile, AI match, auto-apply agent) but **critical connections are missing**. Jobs are not being synced, match scoring is not wired to the feed, profile assembly is fragmented, and several workers/features are stubs or not deployed.

---

## Part 1: Critical Gaps (Must Fix)

### Jobs Pipeline — Broken End-to-End

| # | Gap | Severity | Location |
|---|-----|----------|----------|
| 1 | Jobs table empty in prod — Job sync worker not deployed | **Critical** | `render.yaml`, `apps/worker/job_sync_worker.py` |
| 2 | Match scoring not used in jobs feed — `score_job_match` never called | **Critical** | `job_scoring.py`, `job_search.py`, `user.py` |
| 3 | API does not return `match_score` — jobs feed has no scores | **Critical** | `GET /me/jobs`, `search_and_list_jobs` |
| 4 | `sort_by` (match_score, salary) ignored by API | **High** | `user.py` list_jobs |
| 5 | Profile used only for filters, not for scoring/ranking | **High** | `job_search.py` |
| 6 | Cold start uses non-existent `j.status = 'ACTIVE'` | **High** | `cold_start.py` |

### Profile Assembly — Fragmented

| # | Gap | Severity | Location |
|---|-----|----------|----------|
| 7 | No unified profile assembly — `profile_data` + `user_skills` + `work_style_profiles` never merged | **Critical** | New `profile_assembly.py` needed |
| 8 | `user_skills` and `profile_data.skills` never merged — matching can miss skills | **High** | `ProfileRepo`, `job_scoring` |
| 9 | DeepProfile / `score_job_match` never called — dead code | **High** | `job_scoring.py` |
| 10 | Semantic matching and AI match expect profile from client — API does not load profile | **High** | `ai.py`, `semantic_matching.py` |
| 11 | `deep_profiles` table exists but never populated | **Medium** | `deep_profiles` |

### Onboarding — Data & Validation

| # | Gap | Severity | Location |
|---|-----|----------|----------|
| 12 | DOCX uploads rejected by frontend — `useProfile.uploadResume` only accepts PDF | **High** | `useProfile.ts`, `ResumeStep` |
| 13 | LinkedIn URL from Resume step not persisted until Preferences — lost if user skips | **Medium** | `ResumeStep`, `PreferencesStep` |
| 14 | Career goals: no backend validation for `experience_level`, `urgency` | **Medium** | `user.py` ProfileUpdate |
| 15 | Work style skip: `POST /me/work-style` called with empty answers | **Low** | `WorkStyleStep` |
| 16 | Missing i18n keys: `onboarding.allSet`, `onboarding.almostThere`, etc. | **Low** | `i18n.ts` |

### Dashboard — Missing Features

| # | Gap | Severity | Location |
|---|-----|----------|----------|
| 17 | TeamView is stub — no real team management, only "Upgrade to Team" | **High** | `TeamView.tsx` |
| 18 | Billing page: invoices only — no plan selection or upgrade UI | **High** | `Billing.tsx`, `BillingView.tsx` (unused) |
| 19 | HoldsView snooze: `isSubmitting(\`snooze-${app.id}\`)` never matches | **Medium** | `HoldsView.tsx`, `useApplications` |
| 20 | Phase 12–14 feature pages (pipeline, notifications, etc.) not in nav | **Medium** | `AppLayout.tsx` |
| 21 | BillingView and Dashboard.tsx duplicated — dead code | **Low** | `BillingView.tsx`, `pages/dashboard/Dashboard.tsx` |

### Background Services — Not Deployed

| # | Gap | Severity | Location |
|---|-----|----------|----------|
| 22 | Job sync worker not in Render | **Critical** | `render.yaml` |
| 23 | Job alerts: no cron — `process_alerts` is API-only | **High** | `job_alerts.py` |
| 24 | Email digest: no cron — `run_weekly_digest` is admin-only | **Medium** | `email_digest.py` |
| 25 | Follow-up reminders: not automated — user must trigger | **Medium** | `follow_up_reminders.py` |
| 26 | BackgroundJobQueue: `process_jobs()` never invoked | **Medium** | `job_queue.py` |
| 27 | `NOTIFY job_queue` never sent on application create — agent relies on polling only | **Low** | `user.py` applications |

---

## Part 2: TODO / Stub Implementations

| # | Item | File | Notes |
|---|------|------|-------|
| 28 | applications table lacks tenant_id filter | `main.py:1017` | Add tenant_id when column exists |
| 29 | TTS/STT service integration | `voice_interview_simulator.py` | Placeholder |
| 30 | Resume agent: storage, DB update, analytics, status check | `resume_agent_integration.py` | Multiple TODOs |
| 31 | Follow-up reminders: integrate with EmailCommunicationManager | `follow_up_reminders.py` |
| 32 | Enhanced notifications: support ticket, suspension, dashboard update | `enhanced_notifications.py` |
| 33 | Agent: cover letter generation, portfolio handling, screenshot storage | `agent.py` |
| 34 | Voice interviews: session retrieval from DB | `voice_interviews.py` | Multiple |
| 35 | Billing: concurrent usage tracking | `billing.py` |
| 36 | Resume PDF: cloud storage, statistics | `resume_pdf.py`, `resume_integration.py` |
| 37 | ATS: template retrieval, statistics | `ats_recommendations.py` |
| 38 | DLQ: wire real manager, oldest_item_age | `dlq_endpoints.py` |
| 39 | Communication endpoints: preferences, email sending, analytics, health | `communication_endpoints.py` | Many TODOs |
| 40 | Settings: dark mode | `Settings.tsx` |
| 41 | Mobile: reCAPTCHA, deep link handling | `mobile/src/lib/supabase.ts` |

---

## Part 3: Sprint Plan

### Sprint 1: Jobs Pipeline (Critical Path) — 1–2 weeks

| Task | Effort | Priority | Status |
|------|--------|----------|--------|
| Deploy job sync worker to Render | 2h | P0 | ✅ Done |
| Add job sync worker to `render.yaml` | 1h | P0 | ✅ Done |
| Create `profile_assembly.py` — merge profile_data + user_skills + work_style | 4h | P0 | ✅ Done |
| Wire `score_job_match` into `GET /me/jobs` — load profile, score jobs, return match_score | 6h | P0 | ✅ Done |
| Add `sort_by` param to jobs API (match_score, salary, date_posted) | 2h | P0 | ✅ Done |
| Fix cold start: remove `j.status = 'ACTIVE'` or use correct column | 1h | P0 | ✅ Done |
| Merge `user_skills` into profile for matching | 2h | P0 | ✅ Done (in profile_assembly) |

**Deliverable:** Jobs feed populated, scored, sorted by match.

---

### Sprint 2: Profile & Matching (Quality) — 1 week

| Task | Effort | Priority | Status |
|------|--------|----------|--------|
| Server-side profile loading for AI match — don't rely on client | 3h | P0 | ✅ Done |
| Add optional `min_match_score` filter to jobs API | 1h | P1 | ✅ Done |
| Add callback likelihood factor (optional — needs historical data or LLM) | 8h | P2 |
| Tenant-specific job sync queries (use preferences from onboarding) | 4h | P1 |
| Add `pg_notify('job_queue')` on application create | 1h | P2 |

**Deliverable:** Jobs feed uses full profile; matches are high-quality.

---

### Sprint 3: Onboarding Fixes — 3–5 days

| Task | Effort | Priority |
|------|--------|----------|
| Align `useProfile.uploadResume` with backend — accept DOCX | 1h | P0 |
| Persist LinkedIn URL in Resume step (not only Preferences) | 2h | P1 |
| Add backend validation for career_goals (experience_level, urgency) | 2h | P1 |
| Add missing i18n keys for onboarding | 1h | P2 |
| Fix work style skip — don't send empty answers | 1h | P2 |

**Deliverable:** Onboarding data complete and validated.

---

### Sprint 4: Dashboard & UX — 1 week

| Task | Effort | Priority |
|------|--------|----------|
| Fix HoldsView snooze loading state | 1h | P0 |
| Consolidate Billing UI — use BillingView or merge upgrade into Billing | 4h | P0 |
| Add nav entries for Phase 12–14 features (or "More" submenu) | 2h | P1 |
| Remove or integrate dead code (BillingView, Dashboard.tsx) | 2h | P2 |
| Team: implement real team management or mark "Coming soon" | 4h | P1 |

**Deliverable:** Dashboard functional, no broken UX.

---

### Sprint 5: Background Workers & Cron — 3–5 days

| Task | Effort | Priority |
|------|--------|----------|
| Add Render cron (or GitHub Actions) for job alerts daily/weekly | 2h | P0 |
| Add weekly cron for email digest | 1h | P1 |
| Add worker for follow-up reminders (poll pending, send) | 4h | P1 |
| Wire BackgroundJobQueue or deprecate | 2h | P2 |
| Add auto-apply agent to render-blueprint | 1h | P2 |

**Deliverable:** Job alerts, digest, reminders run automatically.

---

### Sprint 6: API & Backend TODOs — 1 week

| Task | Effort | Priority |
|------|--------|----------|
| Communication endpoints: implement preferences, email, analytics | 8h | P1 |
| DLQ: wire real manager | 2h | P1 |
| Resume PDF: cloud storage, statistics | 4h | P2 |
| ATS: template retrieval, statistics | 2h | P2 |
| Billing: concurrent usage tracking | 2h | P2 |
| Voice interviews: session retrieval from DB | 4h | P2 |

**Deliverable:** Stub endpoints implemented.

---

### Sprint 7: Agent & Integrations — 1 week

| Task | Effort | Priority |
|------|--------|----------|
| Agent: cover letter generation and storage | 4h | P1 |
| Agent: portfolio file handling | 2h | P2 |
| Agent: screenshot storage | 2h | P2 |
| Resume agent: DB storage, analytics, status | 6h | P2 |
| Follow-up reminders: EmailCommunicationManager integration | 2h | P2 |

**Deliverable:** Agent features complete.

---

### Sprint 8: Polish & Edge Cases — 3–5 days

| Task | Effort | Priority |
|------|--------|----------|
| Settings: dark mode toggle | 2h | P2 |
| Mobile: reCAPTCHA, deep links | 4h | P2 |
| Enhanced notifications: support ticket, suspension | 4h | P2 |
| Voice interviews: TTS/STT integration | 8h | P3 |
| Profile assembly: `profile_to_searchable_text` — handle RichSkill dicts | 1h | P2 |

**Deliverable:** Edge cases handled.

---

### Sprint 9: Tenant & Multi-Tenant — 2–3 days

| Task | Effort | Priority |
|------|--------|----------|
| Add tenant_id to applications (if not present) | 4h | P1 |
| Add tenant_id filter in main.py | 1h | P1 |
| Tenant-specific job sync queries | 4h | P1 |

**Deliverable:** Multi-tenant isolation correct.

---

### Sprint 10: Testing & Observability — Ongoing

| Task | Effort | Priority |
|------|--------|----------|
| E2E tests for onboarding flow | 4h | P1 |
| E2E tests for jobs → apply → agent flow | 6h | P1 |
| Add metrics for job sync, match scoring, agent latency | 4h | P2 |
| Add Sentry for critical paths | 2h | P2 |

**Deliverable:** Confidence in deployments.

---

## Part 4: Summary by Priority

### P0 (Must Have — Sprints 1–4)

- Deploy job sync worker
- Wire profile assembly + match scoring to jobs feed
- Fix onboarding DOCX, HoldsView snooze, Billing UI
- Job alerts cron

### P1 (Should Have — Sprints 2–6, 9)

- Server-side profile for AI match
- Tenant-specific sync, min_match_score
- Onboarding validation, LinkedIn persistence
- Communication endpoints, DLQ, Team
- Job digest cron, follow-up reminders worker
- Tenant_id in applications

### P2 (Nice to Have — Sprints 5–8)

- Callback likelihood, pg_notify
- Phase 12–14 nav, dead code cleanup
- Resume PDF storage, ATS templates, Billing concurrent
- Agent cover letter, portfolio, screenshot
- Dark mode, mobile reCAPTCHA, enhanced notifications

### P3 (Future)

- Voice TTS/STT
- Other enhancements

---

## Part 5: Dependency Graph

```
Sprint 1 (Jobs Pipeline)
    └── Sprint 2 (Profile & Matching) — depends on profile_assembly
    └── Sprint 5 (Workers) — job sync deployed first

Sprint 3 (Onboarding) — independent
Sprint 4 (Dashboard) — independent
Sprint 6 (API TODOs) — independent
Sprint 7 (Agent) — independent
Sprint 8 (Polish) — independent
Sprint 9 (Tenant) — can run after Sprint 1
Sprint 10 (Testing) — ongoing
```

---

## Part 6: Checklist — Quick Reference

- [ ] Job sync worker deployed
- [ ] Jobs feed returns match_score
- [ ] Jobs feed supports sort_by
- [ ] Profile assembly unified
- [ ] user_skills merged into profile
- [ ] DOCX accepted in resume upload
- [ ] LinkedIn persisted in Resume step
- [ ] Career goals backend validation
- [ ] HoldsView snooze fixed
- [ ] Billing upgrade UI
- [ ] Job alerts cron
- [ ] Email digest cron
- [ ] Follow-up reminders worker
- [ ] Communication endpoints implemented
- [ ] DLQ wired
- [ ] tenant_id in applications

---

*Generated from multi-agent deep audit. Update as work is completed.*
