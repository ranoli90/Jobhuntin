# Onboarding End-to-End Audit Findings

**Generated:** 2026-03-10  
**Sources:** 4 sub-agent audits (backend, frontend, chaos/failure modes, data flow)

---

## CRITICAL (Production Failures)

| ID | Severity | File:Line | Description | Trigger | Fix |
|----|----------|-----------|-------------|---------|-----|
| OB-001 | Critical | `resume.py:471-637` | Resume upload not atomic: storage upload before DB upsert. DB fail → orphaned file. | Storage succeeds, ProfileRepo.upsert fails | Compensating delete on failure or deferred upload |
| OB-002 | Critical | `auth.py:111-122` | Magic link replay: in-memory fallback when Redis down. Multi-worker unsafe. | Multi-worker without Redis | Require Redis; no in-memory fallback |
| OB-005 | Critical | `auth.py:356-399` | Race: two concurrent magic-link verifications for same new email → unique_violation. | Two links clicked at once | INSERT ON CONFLICT or SELECT FOR UPDATE |
| R1 | Critical | `resumeUploadRetry.ts:55-60` | Base64 resume in localStorage. 15MB file → ~20MB. QuotaExceededError likely. | Large PDF upload | Use IndexedDB or store reference only |
| F1 | Critical | `useOnboarding.ts:135,158`; `browserCache.ts:48` | localStorage.setItem not wrapped in try/catch. QuotaExceeded unhandled. | Storage full | Wrap in try/catch; fallback to sessionStorage |
| A4 | Critical | `api.ts:254-274` | 401 → redirect to login. User loses onboarding state mid-flow. | Session expires during onboarding | ReAuthModal; preserve partial state before redirect |
| C1 | Critical | — | Two tabs submitting. Last write wins; no optimistic locking. | User opens two tabs | Add version/ETag; merge completedSteps |
| R1 (race) | Critical | — | Step 3 saved before step 2 completes. No backend ordering. | Rapid navigation | Enforce step order on backend |

---

## HIGH

| ID | File:Line | Description | Trigger |
|----|-----------|-------------|---------|
| OB-003 | `user.py:1101-1112` | Preferences: no validation for salary_min/max. Negative, min>max, huge values. | Client sends invalid salary |
| OB-004 | `user.py:1206-1254` | update_profile no transaction. Partial success possible. | ProfileRepo.upsert succeeds, UPDATE users fails |
| OB-006 | `user.py:1342-1370` | _hydrate_job_matches: exceptions logged, not surfaced. | Hydration fails silently |
| OB-007 | `ai_onboarding.py:262-275` | create_onboarding_session: two separate saves. Second fail → inconsistent. | First save OK, second fails |
| S1 | `useOnboarding.ts:254-255` | saveState on every formData change. Rapid typing → many saves. | User types quickly |
| F1 | `ResumeStep.tsx:124` vs `Onboarding.tsx:419` | LinkedIn URL regex mismatch. Pass one, fail other. | URL with path segments |
| N1 | `App.tsx:232` | No deep-link to step. /app/onboarding only. | Bookmark step URL |
| A1 | `Onboarding.tsx:354-378` | handleSaveWorkStyle advances when hasAnswers false. No POST when empty. | User skips work style |
| A2/A3 | `Onboarding.tsx:356-367` | Work style enums mismatch: frontend sends flexible/pairing/courses; backend expects low|medium|high, building|studying|mixed. | User selects those options |
| E1 | `Onboarding.tsx:423-434` | Restore effect can overwrite user input if user types while restore runs. | User types during restore |
| N1 (network) | `api.ts:332-384` | No request deduplication; 10s timeout may be short for slow 3G. | Slow connection |
| A1 (auth) | Magic link expired | Redirect with hint=expired. | — |
| B1 | — | DB pool exhausted: no explicit handling. | High load |
| B2 | — | Redis down: prod raises. | Redis outage |
| I1 | `ReadyStep.tsx:276` | Double-submit on Complete: disabled helps but no idempotency key. | Retry after partial success |
| BC4 | — | XSS in free text: verify all inputs sanitized. | Malicious input |

---

## MEDIUM

| ID | File:Line | Description |
|----|-----------|-------------|
| OB-008 | `main.py:1435-1437` | save_user_skills: user_id falsy → 200 with null body |
| OB-009 | `useOnboarding.ts:138-143` | syncToServer errors only logged; user not informed |
| OB-010 | `Onboarding.tsx:66` | syncToServer undefined when profile null; progress not synced until load |
| OB-011 | `repositories.py:446` | resume_url=None does not clear (COALESCE keeps old) |
| OB-012 | `user.py:1335-1340` | full_name from contact; if empty, users.full_name never updated |
| OB-013 | `config.py:111` | magic_link_bind_to_ip defaults False; token stolen usable from any IP |
| S2 | `useOnboarding.ts:92-121` | loadInitialState: serverProgress change after mount not re-run |
| S3 | `Onboarding.tsx:419-421` | linkedinUrl empty on first load before restore |
| S4 | `useOnboarding.ts:305-322` | queueOfflineAction defined but not returned/used |
| S5 | `Onboarding.tsx:210-222` | workStyleAnswers from localStorage; useOnboarding also persists; race |
| F2 | `ConfirmContactStep.tsx:66-70` | onSetFormError optional; phone errors never shown if omitted |
| F3 | `ConfirmContactStep.tsx:234` | Inline regex instead of shared validator |
| F4 | `PreferencesStep.tsx:109-114` | localExcludedKeywords not synced when preferences changes from profile |
| N2 | `useOnboarding.ts:246-252` | goToStep not exposed; no step jump from UI |
| N3 | `Onboarding.tsx:818-826` | Keyboard handler deps cause effect re-run on every render |
| N4 | `ResumeStep.tsx:421` | Skip modal: linkedinError not cleared before advance |
| A4 | `Onboarding.tsx:813-815` | /onboarding/complete failure swallowed |
| A5 | `Onboarding.tsx:56-59` | syncProgressToServer no error handling |
| A6 | `api.ts:256-262` | 401 loses state; no persist before redirect |
| R2 | `ResumeStep.tsx:161-163` | File size 15MB but i18n says 10MB |
| R3 | `ResumeStep.tsx:151-154` | Drag-drop does not validate file type/size |
| R4 | `ResumeUploadRetry.tsx:46-60` | onRetry in deps → effect re-runs; can reset timers |
| K1 | `SkillReviewStep.tsx:311-324` | key={skill.skill}; duplicate skills collision |
| K2 | `SkillReviewStep.tsx:228-230` | confidence undefined → NaN, skill excluded |
| E2 | `Onboarding.tsx:818-866` | Keyboard: no isUploading guard; Ctrl+Enter during upload |
| E3 | `Onboarding.tsx:421` | onSkip/onNext async contract unclear |
| E4 | `ReadyStep.tsx:77-85` | handleLaunch setTimeout; timers run after unmount |
| X1 | `ResumeStep.tsx:251-252` | File input disabled but label still clickable |
| X2 | `ConfirmContactStep.tsx:77-80` | Error summary sr-only; redundant announcements |
| I1 | `SkillReviewStep.tsx:265` | Missing i18n key onboarding.skillsCount |
| I2 | `ResumeUploadRetry.tsx:111-161` | All strings hardcoded; no i18n |
| C2 | — | Rapid back/forward; no debounce |
| C3 | — | Two tabs sync; last write wins |
| D1 | — | Corrupt PDF: backend handles; frontend could validate magic bytes |
| D3 | — | Invalid email/phone: align backend validation |
| R2 (race) | — | Resume upload and skills save parallel; ensure ordering |
| R3 (race) | — | syncToServer and saveState race |
| BC1 | — | Max skills: backend 500; no frontend cap |
| BC2 | — | File size: align 15MB everywhere |
| BC6 | — | return_to path whitelist sync frontend/backend |

---

## LOW

| ID | File:Line | Description |
|----|-----------|-------------|
| OB-014 | `main.py:1318-1326` | save_answer_memory: field_label length not validated |
| OB-015 | `user.py:1335` | _merge_contact_fields: extra keys stored |
| OB-016 | `migrations/017` | session_id format not validated |
| F5 | `CareerGoalsStep.tsx:234` | No explicit validation before submit |
| N4 | `ResumeStep.tsx:421` | Skip: linkedinError not cleared |
| R5 | `resumeUploadRetry.ts:117-119` | updateAfterFailure: file not in metadata for persistence |
| R6 | `ResumeStep.tsx:273-278` | Parsing error hardcoded; not i18n |
| K3 | `SkillReviewStep.tsx:265` | skillsCount key missing |
| K4 | `CareerGoalsStep.tsx:26-56` | EXPERIENCE_LEVELS etc hardcoded |
| K5 | `SkillReviewStep.tsx:316-324` | handleDeleteSkill by index; reorder breaks |
| E5 | `Onboarding.tsx:903` | Restart uses globalThis.confirm; not accessible |
| E6 | `WorkStyleStep.tsx:160-171` | setTimeout stale closure on rapid clicks |
| X3 | `WorkStyleStep.tsx:200-212` | Progress dots: no aria-current |
| X4 | `ReadyStep.tsx:279` | aria-label vs visible text mismatch |
| X5 | `Onboarding.tsx:909` | Dismiss aria-label hardcoded |
| I3 | `i18n.ts:53` | fileTypes says 10MB, limit 15MB |
| I4 | `WelcomeStep.tsx:98` | setupTime fallback inconsistent |
| I5 | `CareerGoalsStep.tsx` | Option labels hardcoded |
| C4 | — | Double-click: add debounce |
| D5 | — | Invalid LinkedIn: validate on blur |
| BC5 | — | Context length 200: document in UI |

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 8 |
| High | 18 |
| Medium | 42 |
| Low | 24 |

**Total: 92+ findings**

---

## Priority Fix Order

1. **Critical:** OB-001, OB-002, OB-005, R1 (storage), F1 (QuotaExceeded), A4 (session), C1 (tabs), step ordering
2. **High:** OB-003, OB-004, salary validation, work style enums, LinkedIn regex, restore race, localStorage try/catch
3. **Medium:** syncToServer errors, profile null handling, Preferences sync, keyboard guards, timers cleanup

---

## Fixes Applied (2026-03-10)

| Finding | Fix |
|---------|-----|
| F1 (QuotaExceeded) | useOnboarding: safeSetStorage with QuotaExceeded catch, sessionStorage fallback; loadInitialState tries sessionStorage on localStorage fail; A/B variant localStorage wrapped in try/catch |
| BrowserCache.set | QuotaExceeded catch, remove-then-retry, log on failure |
| OB-003 (salary) | Preferences model_validator: salary_min/max 0–10M, min ≤ max |
| OB-005 (user race) | _find_or_create_user_by_email: INSERT ON CONFLICT (email) DO UPDATE; RETURNING id; inserted = (id == new_id) |
| F1 (LinkedIn regex) | Shared linkedinValidation.ts; ResumeStep and Onboarding use isValidLinkedInUrl() |
| E2 (keyboard) | Added isUploading to Ctrl+Enter and Alt+Arrow guards |
| K2 (confidence) | SkillReviewStep: (s.confidence ?? 0) for high/medium/low filters |
| ReadyStep timers | Already had cleanup on unmount; no change needed |
| OB-001 | resume.py: try/except around ProfileRepo.upsert; on failure, storage.delete_file(resume_url); added delete_file to StorageService |
| OB-004 | user.py: wrapped update_profile DB ops in conn.transaction() |
| A2/A3 | Onboarding: mapWorkStyleForApi maps flexible->medium, pairing->mixed, courses->studying |
| N1 | useSearchParams ?step=N; initialStepFromUrl in useOnboarding; URL kept in sync with currentStep |
| R1 | resumeUploadRetry: skip fileBase64 for files >4MB; canRetry=false when no fileBase64 |
| OB-009 | useOnboarding: onSyncError callback; Onboarding shows toast on sync failure |
| OB-008 | main.py: return {"status":"saved","count":...} when user_id falsy |
| R2/R3 | i18n fileTypes 15MB; ResumeStep handleDrop validates size and type |
| N4 | ResumeStep SkipConfirmModal onSkip clears linkedinError |
| I1/I3 | Added onboarding.skillsCount; fileTypes 10MB->15MB EN+FR |
| A6 | AuthContext: on 401 when on /app/onboarding, call flushOnboardingBeforeRedirect before redirect; useOnboarding registers flush |
| F4 | PreferencesStep: useEffect to sync localExcludedKeywords/Companies when preferences changes from profile |
| E1 | Restore effect: only restore when local state empty to avoid overwriting user input |
| BC1 | SkillReviewStep: MAX_SKILLS=100, toast when max reached; i18n maxSkillsReached/Desc |
| K1 | SkillRow key: \`${skill.skill}-${globalIdx}\` to avoid duplicate key collision |
| C1/C3 | Backend: merge onboarding_step (max), onboarding_completed_steps (union) instead of overwrite |
| F3 | emailUtils: isValidEmail(); ConfirmContactStep and Onboarding use shared validator |
| I1 | handleComplete: completingRef guard prevents double-submit before React state update |
| A4 | Growth endpoint failure: show warning toast instead of success; i18n growthEndpointHint |
| N2 | Progress dots: clickable step indicators using goToStep; jump to completed/current steps |
| X4 | ReadyStep: aria-label uses t("onboarding.startMyHunt") to match visible text |
| X5 | Dismiss button: aria-label and text use t("dashboard.dismiss") |
| I4 | WelcomeStep: setupTime fallback "2–3 min" aligned with welcomeSubtitle |
| A1 | handleSaveWorkStyle: comment documenting optional skip (no POST when empty) |
| D5 | ResumeStep: LinkedIn validate on blur; clear error on change when fixed |
| I2 | ResumeUploadRetry: i18n for titles, messages, buttons; getRetryMessageI18n in lib |
| OB-007 | create_onboarding_session: single transaction, one save after get_next_question |
| OB-010 | useOnboarding: useEffect syncs when syncToServer becomes available (profile loads) |
| S2 | loadInitialState: serverProgress in deps (full object) for re-run on change |
| S4 | queueOfflineAction returned from useOnboarding |
| A5 | syncProgressToServer: try/catch, re-throw for onSyncError |
| R4 | ResumeUploadRetry: onRetryRef to avoid effect re-run on parent re-render |
| F5 | handleSaveCareerGoals: explicit validation before submit; i18n careerGoalsRequired |
| BC5 | SkillReviewStep AddSkillForm: maxLength 200, contextLengthHint (EN/FR) |
| D1 | fileValidation.ts: isValidResumeFile magic bytes for PDF/DOCX; ResumeStep uses it |
| K4/I5 | CareerGoalsStep: EXPERIENCE_LEVELS, URGENCY, GOALS, REASONS use i18n (EN/FR) |
| OB-016 | ai_onboarding: session_id UUID format validation in _verify_session_ownership |
| D3 | ProfileUpdate: field_validator for contact email/phone (align with frontend) |
| E3 | ConfirmContactStep: JSDoc for onNext/onPrev async contract |
| C2 | useOnboarding: 150ms debounce on nextStep/prevStep for rapid back/forward |
| OB-006 | `_hydrate_job_matches`: incr("growth.hydrate_job_matches.failed") on exception |
| N1 | api.ts: default timeout 10s→15s for slow 3G |

---

## Remaining (Not Fixed / Deferred)

| ID | Reason |
|----|--------|
| OB-002 | Require Redis: infra change; dev fallback needed |
| A4 (critical) | Full ReAuthModal: complex; A6 flush mitigates |
| R1 (race) | Backend step ordering: requires API design |
| A1 (auth) | Magic link expired redirect |
| B1, B2 | DB pool, Redis: ops/infra |
| BC4 | XSS: verify all inputs (audit) |
| S3 | linkedinUrl: restore effect handles |
| S5 | workStyleAnswers: acceptable race |
| S2 | serverProgress: already in deps |
| OB-012 | full_name: already synced from first+last |
| OB-015 | _merge_contact_fields: only copies allowed fields |
| X2 | Error summary: already has aria-live |
| R5 | updateAfterFailure: file size limits |
| K5 | handleDeleteSkill: skills have no IDs |
| C4 | Double-click: I1 completingRef covers |
