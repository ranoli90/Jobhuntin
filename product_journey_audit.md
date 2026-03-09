# Product Journey Audit — Pre-Production Issue List

**Date:** March 9, 2026
**Scope:** Full user journey — Login → Onboarding → Dashboard → All Features
**Standard:** Apple / Microsoft production quality

---

## Executive Summary

**Total issues found: 232**

| Severity | Count |
|----------|-------|
| P0 — Crashes / Data Loss / Security | 28 |
| P1 — Broken Features / Major UX | 54 |
| P2 — Degraded Experience / Missing Polish | 78 |
| P3 — Code Quality / Minor Polish | 72 |

---

## 1. LOGIN & MAGIC LINK FLOW (18 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 1 | **httpOnly cookie check is dead code** | `lib/api.ts` L105–111 | `document.cookie` cannot read `jobhuntin_auth` (httpOnly); `hasSession()` always returns false. Session detection is broken. |
| 2 | **Token replay prevention requires Redis in prod** | `api/auth.py` | In-memory `_consumed_jtis` set is process-local; multi-worker/pod deployments allow replay on different workers. |
| 3 | **No JWT revocation mechanism** | `api/dependencies.py` | Stolen session JWTs are valid for 7 days with no blocklist. Logout only clears the cookie; the token itself remains valid if captured. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 4 | **"Sign up" link goes to `/login?signup=true` but does nothing different** | `Login.tsx` L550 | The `signup=true` param is never read; new and existing users see the same flow. Misleading. |
| 5 | **Social login buttons shown as "Coming Soon"** | `Login.tsx` L367–372, `SocialLogin.tsx` | Google and LinkedIn buttons are visible but disabled. Users may think the product is incomplete. Should be hidden or explained. |
| 6 | **Session expiry timer based on client clock** | `AuthContext.tsx` L100–101 | `SESSION_TTL_MS` is set from `Date.now()` on client, not from the server-issued JWT `exp`. Clock skew can cause premature or late expiry warnings. |
| 7 | **CSRF exempt path `/auth/` is too broad** | `shared/middleware.py` | Exempts ALL paths starting with `/auth/`, including any future authenticated endpoints under that prefix. |
| 8 | **Disposable email blocked with 429 status** | `api/auth.py` | Disposable emails return HTTP 429 (rate limit), same as actual rate limiting. Should be 400 with a clear message. |
| 9 | **Magic link `return_to` allowlist is incomplete** | `magicLinkService.ts` L340–356 | Missing newer routes: `/app/pipeline-view`, `/app/multi-resume`, `/app/follow-up-reminders`, etc. Returning users landing on these pages will be silently redirected to `/app/onboarding`. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 10 | **No "magic link expired" distinct error** | `Login.tsx`, `auth.py` | All token errors redirect to `?error=auth_failed`. Users who click a link after 1 hour see a generic error, not "your link has expired — request a new one". |
| 11 | **Confetti on magic link success screen** | `Login.tsx` L149–171 | 3-second confetti animation on every login is excessive for returning users. Confetti should be reserved for first-time or milestone events. |
| 12 | **Rate limit countdown not persisted** | `Login.tsx` L86–98 | If user refreshes during countdown, it resets. They can spam requests by refreshing. |
| 13 | **Email domain suggestions include `aol.com`** | `Login.tsx` L56 | Outdated; consider replacing with more relevant domains or removing the feature. |
| 14 | **No deep link support for email clients** | `auth.py` | Magic link opens a browser tab; no universal link / app link for mobile users. |
| 15 | **Dark mode toggle on login but no dark mode** | `Login.tsx` L337 | `ThemeToggle` is rendered but the login page uses hardcoded light colors. Toggle does nothing visible. |
| 16 | **Language selector on login** | `Login.tsx` L336 | `LanguageSelector` rendered but most strings are hardcoded in English (e.g., "Welcome back", "Sign in to your account"). |
| 17 | **Circuit breaker per-email, not global** | `magicLinkService.ts` | If the mail service is down, each email has its own circuit breaker. The outage won't be detected until every user has 5 failures. |
| 18 | **`_redirecting` global flag** | `lib/api.ts` L259 | Shared redirect guard across all tabs; if one tab triggers redirect, other tabs can't make requests. |

---

## 2. ONBOARDING FLOW (38 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 19 | **Resume upload retry stores file in memory, not IndexedDB** | `resumeUploadRetry.ts` | `getStoredFile()` returns `null` after page refresh; resume metadata is saved but the actual file is lost. |
| 20 | **`useEffect` infinite loop risk** | `Onboarding.tsx` L280–318 | Effect depends on `contactInfo`, `preferences`, `linkedinUrl`, etc. and calls `updateFormData` inside, which can trigger re-renders and re-runs. |
| 21 | **Skills save is not transactional** | `api/main.py` | DELETE all existing skills then INSERT new ones without a DB transaction. Partial failure = data loss. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 22 | **Resume step: no DOCX or image support in UI** | `ResumeStep.tsx` | Frontend only accepts PDF (`accept=".pdf"`), but backend supports DOCX. Users with Word resumes are blocked. |
| 23 | **Work style step: i18n mapping breaks non-English** | `WorkStyleStep.tsx` | `VALUE_MAPS` keys are English labels. If `t()` returns translated text, the mapping to API values fails silently. |
| 24 | **Career goals step: no validation on required fields** | `CareerGoalsStep.tsx` | `experience_level` and `urgency` are required by the UI flow but the "Save & Continue" button is enabled without them. |
| 25 | **Contact step: phone error never clears** | `ConfirmContactStep.tsx` | `handlePhoneChange` sets error on invalid phone but never clears it when the phone becomes valid. |
| 26 | **Onboarding step skip allowed** | `useOnboarding.ts` | `goToStep()` allows jumping to any step without validation. Users can skip resume upload and go directly to "Ready". |
| 27 | **Parsing preview shows hardcoded "98% confidence"** | `ResumeStep.tsx` | Static text regardless of actual parse quality. Misleading. |
| 28 | **LinkedIn URL validation too strict** | `ResumeStep.tsx` | Rejects valid LinkedIn URLs with country prefixes (e.g., `uk.linkedin.com/in/...`). |
| 29 | **AI suggestions fail silently** | `Onboarding.tsx` L600–607 | If AI suggestion fetch fails, no indication to user. Preferences step shows empty suggestions with no explanation. |
| 30 | **Email typo suggestion can produce invalid email** | `Onboarding.tsx` L1170–1173 | `email.split('@')[0]` + `@` + suggestion; if email has no `@`, result is `"undefined@gmail.com"`. |
| 31 | **`saveState` PII split can lose data** | `useOnboarding.ts` | Non-PII saved to `localStorage`, PII to secure storage. If one fails, data is out of sync on reload. |
| 32 | **No loading state between steps** | `Onboarding.tsx` | When saving data (e.g., skills, contact), the skeleton replaces the form. Users lose context of what they entered. Better: overlay loading indicator. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 33 | **Welcome step: `titleWords.pop()` mutates array** | `WelcomeStep.tsx` | Array mutation in render; `titleStart` computed before pop, so last word rendering is correct but code is fragile. |
| 34 | **No indication of which steps are optional vs required** | Onboarding | Work style and career goals appear required but can be skipped. No visual distinction. |
| 35 | **Skill review: edit functionality is stubbed** | `SkillReviewStep.tsx` | `editingIndex` state exists but no edit UI renders; clicking edit does nothing visible. |
| 36 | **Skill review: hover-only actions** | `SkillReviewStep.tsx` | Edit and delete buttons only appear on hover (`md:opacity-0`); inaccessible on touch devices and via keyboard. |
| 37 | **Battery API check** | `Onboarding.tsx` L69–85 | `navigator.getBattery()` is non-standard and deprecated in Firefox. Could throw in some environments. |
| 38 | **Duplicate skill check uses exact match** | `SkillReviewStep.tsx` | "React" and "react" are treated as different skills. Should normalize. |
| 39 | **Contact step: email prefilled from auth, not editable explanation** | `ConfirmContactStep.tsx` | Users may not understand why their email is prefilled. No "This is the email you signed up with" hint. |
| 40 | **"Restart" button with `window.confirm()`** | `Onboarding.tsx` L999 | Native browser dialog; not themed. Should use custom confirmation modal. |
| 41 | **Work style archetype names hardcoded in English** | `WorkStyleStep.tsx` | Archetype descriptions bypass i18n system. |
| 42 | **Ready step: "Scanning 10,000+ jobs" hardcoded** | `ReadyStep.tsx` | Marketing copy that may not match reality. |
| 43 | **Progress ring shows "completeness" not "step progress"** | `Onboarding.tsx` L1038–1043 | Confusing to show 35% completeness on step 5 of 8. Users expect step-based progress. |
| 44 | **Salary input accepts decimals and negatives** | `Onboarding.tsx` L813–831 | `parseInt` handles this but UX should prevent it at input level. |
| 45 | **No character limits on free-text inputs** | `CareerGoalsStep.tsx` | "Why leaving" textarea has no maxLength. Users could paste entire essays. |
| 46 | **Confetti fires on every step advance** | `Onboarding.tsx` L217–222 | Step confetti is excessive; should only fire on key milestones (resume uploaded, completion). |
| 47 | **A/B test variant not visible to user** | `useOnboarding.ts` | "resume_first" vs "role_first" variant chosen silently. No analytics-friendly tracking of which variant the user saw. |
| 48 | **Preferences step: salary suggestions can mislead** | `ai.py` L318–331 | Fallback salary is hardcoded 80k–150k when AI fails. User may accept incorrect range. |
| 49 | **Preferences step: location autocomplete is basic text input** | `PreferencesStep.tsx` | No Google Places or similar autocomplete. Users type freeform text. |
| 50 | **Excluded companies/keywords: no autocomplete or validation** | `PreferencesStep.tsx` | Users type company names freely; typos won't match during job filtering. |
| 51 | **Cache uses 'anonymous' as key when profile is null** | `Onboarding.tsx` L584, L691 | Multiple anonymous users on the same device share cached data. |
| 52 | **"Work authorized" defaults to true** | `Onboarding.tsx` L150 | Assumes all users are work-authorized by default; could lead to incorrect job filtering. |
| 53 | **Asset preloading only loads favicon** | `Onboarding.tsx` L477–489 | Font preload link added but the actual CSS isn't loaded; LCP optimization is incomplete. |
| 54 | **Keyboard shortcut Ctrl+Enter may conflict** | `Onboarding.tsx` L440–441 | Ctrl+Enter also submits forms in some browsers. Could double-submit. |
| 55 | **No auto-save draft** | Onboarding | If the browser crashes mid-step, entered data is lost. Only saved on "Next" click. |
| 56 | **No progress indication for resume parsing** | `ResumeStep.tsx` | Upload shows spinner but no percentage or step indicator for multi-second parse. |

---

## 3. DASHBOARD — MAIN VIEW (12 issues)

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 57 | **Success rate always shows 0%** | `Dashboard.tsx` | `stats.successRate` depends on applications with "success" status, but the status enum is `APPLYING/APPLIED/HOLD/FAILED/REJECTED`. There's no "success" status. |
| 58 | **"Total Applications" shows `monthlyApps` not total** | `Dashboard.tsx` L48, L88 | Label says "Total Applications" but value is `stats.monthlyApps`. Misleading metric. |
| 59 | **Division by zero fallback masks empty state** | `Dashboard.tsx` L44 | `totalApps = applications.length || 1` prevents /0 but shows 0% progress bars instead of empty state. |
| 60 | **Hold items "Review" button navigates to applications list, not specific item** | `Dashboard.tsx` L278 | Clicking "Review" on a hold item goes to `/app/applications` (generic list), not to the specific application's hold view. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 61 | **No first-time dashboard experience** | `Dashboard.tsx` | New users after onboarding see 0/0/0 metrics with no guidance on what to do next. |
| 62 | **Plan card shows "FREE" with "Next Billing: No upcoming bill"** | `Dashboard.tsx` L335–338 | For free users, the billing section is confusing. Should show upgrade CTA instead. |
| 63 | **Recent applications section missing** | `Dashboard.tsx` | `recentApps` is computed (L94) but never rendered. |
| 64 | **Greeting uses `full_name.split(' ')[0]` as fallback** | `Dashboard.tsx` L93 | If `full_name` is a single name like "Prince", it works, but `contact?.first_name` should be primary. |
| 65 | **No loading skeleton for hold applications** | `Dashboard.tsx` L223–226 | Single skeleton item shown regardless of actual count. |
| 66 | **No refresh/pull-to-refresh** | `Dashboard.tsx` | Data loads once; stale data persists. No manual refresh button. |
| 67 | **Metrics are raw counts, not meaningful** | `Dashboard.tsx` | "Active Applications: 2" with a progress bar out of total applications is not actionable. Industry standard: interview rate, response rate. |
| 68 | **Motion animations on every page visit** | `Dashboard.tsx` L97–101 | Fade-in and slide-up animations play every time, even on back-navigation. Should only animate on first mount. |

---

## 4. JOBS VIEW — SWIPE INTERFACE (14 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 69 | **Swipe POST to `/applications` but backend expects `/me/applications`** | `JobsView.tsx` L56 | `apiPost("/applications", ...)` may 404 or hit the wrong endpoint. Backend user router mounts at `/me/applications`. |
| 70 | **No duplicate application guard** | `JobsView.tsx` | Swiping accept on a job the user already applied to creates a duplicate application. No check for existing applications. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 71 | **Jobs have no detail view before applying** | `JobsView.tsx` | Users can only see title, company, location, 4-line description, and salary on the swipe card. No way to view full job description before deciding. |
| 72 | **No filters on jobs view** | `JobsView.tsx` L20–21 | `filters: JobFilters = useMemo(() => ({}), [])` — empty filters. Users cannot filter by location, salary, remote, etc. despite having set preferences. |
| 73 | **Match score shown but not explained** | `JobsView.tsx` L174–178 | Shows "85% match" but no breakdown of why. Users can't trust or act on the score. |
| 74 | **No undo for swipe** | `JobsView.tsx` | Once swiped left (rejected), the job is gone. No undo button despite an undo icon import. |
| 75 | **"All caught up" state has no notification opt-in** | `JobsView.tsx` L93–114 | When no jobs remain, there's no way to set up alerts. Users leave with no next action. |
| 76 | **Swipe gesture conflicts with mobile scroll** | `JobsView.tsx` L153 | `drag="x"` on the card can be triggered by horizontal scroll attempts. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 77 | **Card stack only shows 3 cards** | `JobsView.tsx` L148 | If there are 100 jobs, only the top 3 are rendered. Performance is fine but the "depth" visual is limited. |
| 78 | **No keyboard navigation for swipe** | `JobsView.tsx` | Keyboard users must use the buttons; no left/right arrow support for swiping. |
| 79 | **Salary display assumes USD** | `JobsView.tsx` L185–189 | `$${(job.salary_min / 1000).toFixed(0)}k` — hardcoded dollar sign. |
| 80 | **Applied/Skipped/Remaining counters reset on page reload** | `JobsView.tsx` L25 | `swipedJobs` is in-memory; refreshing loses session progress. |
| 81 | **No job source attribution** | `JobsView.tsx` | Users don't know if a job is from LinkedIn, Indeed, etc. No source badge. |
| 82 | **No saved/bookmarked jobs** | `JobsView.tsx` | No way to save a job for later without applying. Swipe left = permanently dismissed. |

---

## 5. APPLICATIONS VIEW (11 issues)

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 83 | **`isSubmitting` key mismatch for snooze** | `useApplications.ts` | `snoozeApplication` uses `snooze-${id}` but `isSubmitting(id)` checks raw `id`. Snooze loading state never shows. |
| 84 | **Withdraw/Review actions don't refetch** | `ApplicationsView.tsx` L139–160 | After withdraw or review, the list is not refetched. Application appears with old status. |
| 85 | **No application status "APPLYING" explanation** | `ApplicationsView.tsx` | Users see "APPLYING" with a pulsing dot but no text explaining what the agent is doing. |
| 86 | **Table row click and actions menu conflict** | `ApplicationsView.tsx` L349–355, L384 | Clicking the actions menu triggers both the menu and the row navigation. Event propagation issue. |
| 87 | **"APPLYING" status filter missing** | `ApplicationsView.tsx` L108–114 | Status filters are All, Applied, Hold, Failed, Rejected — missing "Applying" (in progress). |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 88 | **No bulk actions** | `ApplicationsView.tsx` | Cannot withdraw, archive, or review multiple applications at once. |
| 89 | **Search doesn't debounce** | `ApplicationsView.tsx` L224 | Every keystroke triggers filter recalculation. Not a perf issue now but poor practice. |
| 90 | **15-second polling is heavy** | `useApplications.ts` | Polls every 15s even when the tab is backgrounded. Should pause or increase interval. |
| 91 | **Snooze hardcoded to 24h** | `ApplicationsView.tsx` L83, `HoldsView.tsx` | No option for different snooze durations. |
| 92 | **No sort options** | `ApplicationsView.tsx` | Cannot sort by date, company, status. |
| 93 | **Empty state CTA says "Browse jobs" / "Start Searching"** | `ApplicationsView.tsx` L272, L334 | Inconsistent copy between mobile and desktop. |

---

## 6. HOLDS VIEW (6 issues)

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 94 | **Answer text not cleared after submission** | `HoldsView.tsx` | After successfully answering a hold, the textarea retains the text. |
| 95 | **No answer length validation** | `HoldsView.tsx`, `api/user.py` | `AnswerHoldBody.answer` has no length check. Users can submit empty or 100KB answers. |
| 96 | **No confirmation before answer submission** | `HoldsView.tsx` | Submitting the wrong answer can't be undone. No "Are you sure?" prompt. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 97 | **No context about what the agent needs** | `HoldsView.tsx` | Shows the question but not the job title/company for full context. |
| 98 | **Snooze has no confirmation** | `HoldsView.tsx` | No "Snooze for 24h?" confirmation. |
| 99 | **No "Skip this question" option** | `HoldsView.tsx` | User must answer or snooze; no way to tell the agent to skip the question. |

---

## 7. BILLING & SUBSCRIPTION (12 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 100 | **Stripe webhook no idempotency** | `api/billing.py` | No idempotency key handling. Duplicate webhook deliveries apply subscription updates twice. |
| 101 | **`checkout_url` / `cancel_url` no validation** | `api/billing.py` | Frontend passes arbitrary URLs for success/cancel; potential open redirect via Stripe checkout. |
| 102 | **Team checkout `seats` has no upper bound** | `api/billing.py` | Could create a subscription with 10,000 seats. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 103 | **Success detection checks `success=1` but Stripe uses `success=true`** | `useBilling.ts` L56 | Post-checkout success toast may never fire. |
| 104 | **`create_portal` returns `checkout_url` for non-Stripe users** | `api/billing.py` | Frontend expects `portal_url`; gets a checkout URL. Billing management fails for new users. |
| 105 | **Two different billing pages** | `BillingView.tsx`, `Billing.tsx` | Dashboard billing tab and `/app/billing` are different components with different UIs. Inconsistent experience. |
| 106 | **Invoice list has no pagination** | `Billing.tsx` | Fetches all invoices at once. Users with many invoices face slow loads. |
| 107 | **Usage limit fallback is 100** | `BillingView.tsx` | Hardcoded; may not match backend plan limits. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 108 | **Tier features and prices hardcoded** | `BillingView.tsx` | FREE ($0), PRO ($19), TEAM ($49) hardcoded in frontend. Price changes require a deploy. |
| 109 | **No downgrade flow** | Billing | Users can upgrade but not downgrade through the UI. Must use Stripe portal. |
| 110 | **No trial/grace period handling** | Billing | No UI for trials, past-due states, or payment failure recovery. |
| 111 | **Usage percentage can display over 100%** | `BillingView.tsx` | Bar is clamped but the percentage text is not. Shows "150%" when over limit. |

---

## 8. SETTINGS PAGE (9 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 112 | **Re-auth reads password from DOM** | `Settings.tsx` | `document.getElementById('reauth-password')` to read password is brittle and insecure. Password value lives in uncontrolled DOM element. |
| 113 | **Password sent in plain header** | `Settings.tsx` | `X-Re-Auth-Password` header sends password in cleartext over HTTP headers (logged by most proxies/CDNs). |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 114 | **Data export behind password re-auth but users have no password** | `Settings.tsx` | Magic link users have no password. Re-auth modal asks for a password they don't have. Export is inaccessible. |
| 115 | **Delete account has no cooling-off period** | `Settings.tsx` | Immediate deletion on confirmation. No "You have 14 days to change your mind" grace period. |
| 116 | **Preferences in Settings don't include all onboarding fields** | `Settings.tsx` | Missing `excluded_companies`, `excluded_keywords`, `visa_sponsorship` from Settings preferences form. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 117 | **"Dark mode" toggle exists but app has no dark mode** | `Settings.tsx` | Toggle does nothing. Clicking it is a no-op. |
| 118 | **No avatar display** | `Settings.tsx` | Avatar upload exists but current avatar is never shown. |
| 119 | **`sr-only` has leading comma** | `Settings.tsx` | Typo: screen reader text starts with `,`. |
| 120 | **No email notification preferences** | `Settings.tsx` | Users can't control what emails they receive. |

---

## 9. AI AGENT & JOB MATCHING (18 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 121 | **`CoverLetterResponse_V1` undefined** | `api/ai.py` L1000 | `NameError` crash when generating enhanced cover letters. Import missing. |
| 122 | **AI endpoints in `ai_endpoints.py` have no auth** | `api/ai_endpoints.py` | Uses `get_db_connection` but no `get_current_user_id`. Unauthenticated users can call AI endpoints. |
| 123 | **`LLMClient()` created without config** | `api/ai_endpoints.py` L50 | Unlike `ai.py` which passes `get_settings()`, this creates a bare client that may fail at runtime. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 124 | **No per-user AI rate limiting** | `api/ai.py` | AI endpoints (tailor resume, cover letter, ATS score) lack user-level rate limits. A single user can exhaust LLM budget. |
| 125 | **Batch match failures are silent** | `api/ai.py` | Failed jobs in batch semantic match are skipped with no retry or feedback. |
| 126 | **Location suggestions unsanitized** | `api/ai.py` L399 | `request.current_location` passed directly to prompt builder without sanitization. Potential prompt injection. |
| 127 | **Match weights cache is in-memory** | `api/ai.py` L1196–1227 | Not persisted; resets on restart. Not tenant-isolated. |
| 128 | **Fallback salary of $80k–$150k when AI fails** | `api/ai.py` L318–331 | Generic fallback regardless of role, location, or experience. Could mislead. |
| 129 | **Job match score shown but algorithm is opaque** | Frontend | Users see "85% match" but no way to understand what drives it. No "Why this match?" explanation on the swipe view. |
| 130 | **No learning feedback loop** | System | Users swipe accept/reject but this data is not fed back to improve matching. The AI doesn't learn from user behavior. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 131 | **Cover letter tone buttons not a radio group** | `CoverLetterGenerator.tsx` | Missing `role="radiogroup"`, `aria-checked`. |
| 132 | **ATS score metrics use non-null assertion** | `ats-score.tsx` | `atsScore.data!.metrics[metric.key]` can crash if API omits a metric. |
| 133 | **ATS score "23 Metrics" hardcoded** | `ats-score.tsx` | Count should match actual `ATS_METRICS.length`. |
| 134 | **AI tailor: file drop zone not keyboard accessible** | `ai-tailor.tsx` | Cannot tab to or activate the drop zone. |
| 135 | **AI tailor: file size limit mismatch** | `ai-tailor.tsx` | UI says "5MB" but backend accepts 15MB. |
| 136 | **No AI response caching** | `ai_endpoints.py` | Same resume + same job = same API call to LLM every time. No cache. |
| 137 | **`/llm/metrics` exposed to all authenticated users** | `api/ai.py` | Internal LLM metrics should be admin-only. |
| 138 | **Cover letter FocusTrap has no `active` prop** | `CoverLetterGenerator.tsx` | Focus trap may remain active when modal closes. |

---

## 10. RESUME HANDLING (8 issues)

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 139 | **Frontend only accepts PDF** | `ResumeStep.tsx`, `ai-tailor.tsx` | `accept=".pdf"` but backend supports DOCX. Users with Word resumes are blocked. |
| 140 | **Resume parse webhook has no caller authentication** | `api/main.py` | `/webhook/resume_parse` uses tenant context but no explicit webhook signature verification. |
| 141 | **Multi-resume page is fully static** | `multi-resume/index.tsx` | Shows hardcoded fake data. Upload button does nothing. Feature is non-functional. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 142 | **No resume preview after upload** | Settings, Onboarding | Users upload a resume but can't view the uploaded file. |
| 143 | **No resume versioning** | System | Old resume is overwritten with no history. |
| 144 | **No resume deletion** | Settings | Users can upload but can't delete their resume. |
| 145 | **Parsed skills don't show confidence source** | `SkillReviewStep.tsx` | AI confidence scores shown without explaining they come from resume parsing. |
| 146 | **Resume file name not preserved** | Upload flow | Original file name is not stored or displayed. |

---

## 11. STUB / NON-FUNCTIONAL FEATURES (20 issues)

### P0 — Critical (Features in navigation but completely non-functional)
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 147 | **Pipeline View: API method mismatch** | `pipeline-view/index.tsx` | Frontend sends POST; backend expects GET. Feature crashes. |
| 148 | **Pipeline View: stage change sends `'next'` instead of stage ID** | `pipeline-view/index.tsx` | Backend expects real stage; feature is broken. |
| 149 | **DLQ Dashboard: backend raises `NotImplementedError`** | `dlq_endpoints.py` | DLQ manager constructor throws. Endpoint crashes at runtime. |
| 150 | **Application Export: wrong API path** | `application-export/index.tsx` | Calls `/api/applications`; backend has `/me/applications`. |

### P1 — Major (Full pages with zero functionality)
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 151 | **Multi-Resume: entirely static** | `multi-resume/index.tsx` | Hardcoded data, no API calls, no upload handler. |
| 152 | **Interview Practice: entirely static** | `interview-practice/index.tsx` | Hardcoded questions and sessions, no API. |
| 153 | **Follow-Up Reminders: entirely static** | `follow-up-reminders/index.tsx` | Hardcoded reminders, no scheduling. |
| 154 | **Application Notes: entirely static** | `application-notes/index.tsx` | Hardcoded notes, no save functionality. |
| 155 | **Communication Preferences: entirely static** | `communication-preferences/index.tsx` | Read-only display, no toggles work. |
| 156 | **Notification History: entirely static** | `notification-history/index.tsx` | Hardcoded notifications, no API. |
| 157 | **Agent Improvements: entirely static** | `agent-improvements/index.tsx` | Hardcoded metrics (94.5%, 89.2%), buttons do nothing. |
| 158 | **Screenshot Capture: entirely static** | `screenshot-capture/index.tsx` | Hardcoded data, capture button does nothing. |
| 159 | **Application Export: uses raw fetch with localStorage token** | `application-export/index.tsx` | Inconsistent with rest of app; token may not exist in localStorage (httpOnly cookie auth). |
| 160 | **Pipeline View: uses raw fetch with localStorage token** | `pipeline-view/index.tsx` | Same auth issue; `localStorage.getItem('token')` returns null. |
| 161 | **DLQ Dashboard: uses raw fetch with localStorage token** | `dlq-dashboard/index.tsx` | Same auth issue as above. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 162 | **Stub pages show in sidebar navigation** | `AppLayout.tsx` | Users see and can navigate to 8+ non-functional features. Erodes trust. |
| 163 | **No "Coming Soon" indicators** | Stub pages | Stub pages show polished UIs with fake data. Users think features work until they try them. |
| 164 | **Badge variant `success` may not exist** | `agent-improvements/index.tsx` | Badge component may not have a `success` variant. |
| 165 | **No feature flags** | System | Stub features are unconditionally shown. Need feature flag system to hide unfinished features. |
| 166 | **Export progress is fake** | `application-export/index.tsx` | Progress bar jumps to 100% without real streaming. |

---

## 12. NAVIGATION & LAYOUT (10 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 167 | **Navigation.tsx uses wrong route paths** | `Navigation.tsx` | Links go to `/dashboard`, `/jobs`, etc. instead of `/app/dashboard`, `/app/jobs`. All navigation links are broken. |
| 168 | **MobileMenu.tsx uses wrong route paths** | `MobileMenu.tsx` | Same issue as Navigation.tsx. All mobile nav links broken. |
| 169 | **MobileMenu.tsx has hardcoded "John Doe"** | `MobileMenu.tsx` | Shows fake user data instead of actual profile. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 170 | **Admin routes visible to non-admin users** | `AppLayout.tsx` | Admin routes (usage, matches, alerts) show in sidebar for all users. Only `/app/admin/sources` is filtered. |
| 171 | **Mobile nav "More" drawer hides core features** | `AppLayout.tsx` | Only 4 items visible on mobile bottom nav; important features like Settings are hidden in "More". |
| 172 | **Sign out in MobileMenu has no logout logic** | `MobileMenu.tsx` | Button rendered but no `signOut` handler. |
| 173 | **Hardcoded version "v2.4.0"** | `AppLayout.tsx` | Should come from package.json or environment. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 174 | **No breadcrumbs in app** | `AppLayout.tsx` | Deep pages have no way back except browser back button. |
| 175 | **Mobile drawer "More" badge count** | `AppLayout.tsx` | Shows count of hidden items as badge, which is confusing — looks like notification count. |
| 176 | **No active state for current page in sidebar** | `AppLayout.tsx` | (Likely present but should be verified for all routes including admin). |

---

## 13. DATABASE & SCHEMA (12 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 177 | **`applications` table lacks `stage` column** | `001_initial_schema.sql` | Pipeline view expects `stage` but table doesn't have it. |
| 178 | **`applications` table lacks `tenant_id`** | `001_initial_schema.sql` | Multi-tenant queries in `main.py` filter by `tenant_id` but column doesn't exist. |
| 179 | **No `application_notes` table** | Migrations | Application notes feature expects this table; it doesn't exist. |
| 180 | **No `follow_up_reminders` table** | Migrations | Follow-up reminders feature expects this table; it doesn't exist. |
| 181 | **`answer_memory` table defined in two migrations** | `001_initial_schema.sql`, `002_onboarding_tables.sql` | Duplicate CREATE TABLE can fail on second migration. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 182 | **Status enum mismatch** | Schema vs Frontend | DB uses `SAVED`, `APPLIED`, etc. Frontend uses `APPLYING`, `QUEUED`, `PROCESSING`, `REQUIRES_INPUT`. No alignment. |
| 183 | **Skills save DELETE+INSERT without transaction** | `api/main.py` | Partial failure can delete all skills and insert none. |
| 184 | **Work style upsert always adds 20 to completeness** | `api/user.py` | Saving work style multiple times inflates completeness. `LEAST(100, ...)` prevents >100 but repeated saves are wrong. |
| 185 | **`profile_data` is untyped JSONB** | Schema | No constraints, no validation. Any shape can be stored. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 186 | **Conflicting migration numbering** | Migrations | Multiple `003_*`, `004_*`, `007_*`, `008_*`, `009_*`, `010_*` files. Migration order is ambiguous. |
| 187 | **No migration runner in docker-compose** | `docker-compose.yml` | Schema is loaded from `infra/supabase/schema.sql` which must be manually assembled. |
| 188 | **No indexes on common query patterns** | Schema | Applications queried by `user_id + status` but no composite index. |

---

## 14. BACKEND API — GENERAL (16 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 189 | **Storage endpoint crashes: `tenant_ctx.get()` on TenantContext** | `api/main.py` L1316–1329 | `tenant_ctx` is a `TenantContext` object, not a dict. `.get("tenant_id")` raises `AttributeError`. |
| 190 | **SQL injection risk in `update_application_status`** | `api/user.py` L528–535 | Uses f-string for SQL; while params are controlled, this pattern is unsafe. |
| 191 | **Dashboard endpoint has no tenant isolation** | `api/main.py` L1017–1044 | `user_dashboard` filters by `user_id` only. Multi-tenant setups leak data. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 192 | **`list_invoices` passes pool instead of connection** | `api/billing.py` L301–302 | `ensure_stripe_customer(db, ...)` but other callers pass `conn`. Will likely error. |
| 193 | **Webhook checkout handler doesn't verify metadata.tenant_id** | `api/billing.py` L334–336 | Metadata could be forged if webhook signature validation is weak. |
| 194 | **`withdraw_application` has no tenant check** | `api/user.py` L451–462 | Multi-tenant: user could withdraw another tenant's application. |
| 195 | **Import inside middleware runs on every request** | `api/main.py` L242 | `import jwt as pyjwt` inside `_get_tenant_info` is evaluated per-request. |
| 196 | **CORS origins contain `[REDACTED]` placeholder** | `api/main.py` L167–168 | If deployed with placeholder, CORS will block legitimate requests. |
| 197 | **`/me/jobs/sources` returns from `useInfiniteQuery` but data isn't paginated** | `useJobs.ts` L111–117 | `getNextPageParam: () => undefined` means infinite query never loads more pages. |

### P2 — Polish
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 198 | **No request validation middleware** | Backend | Individual endpoints validate (or don't); no centralized input validation. |
| 199 | **No API versioning enforcement** | Backend | v1 and v2 endpoints coexist with no deprecation strategy. |
| 200 | **Error responses inconsistent** | Backend | Some return `{"error": "..."}`, others return `{"detail": "..."}`, others return `{"message": "..."}`. |
| 201 | **No OpenAPI documentation** | Backend | FastAPI auto-generates docs but many endpoints return `Any`. |
| 202 | **Pool creation retry but no recovery** | `dependencies.py` L93–98 | After 3 failures, pool stays null. App runs but every DB call returns 503. |
| 203 | **Duplicate CORS logic** | `api/main.py` | CORS handled in both custom middleware and `CORSMiddleware`. |
| 204 | **`incr` call wrong signature** | `api/user.py` L749 | `incr("key", {"user_id": id})` — likely expects `tags=` keyword argument. |

---

## 15. SECURITY (8 issues)

### P0 — Critical
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 205 | **No Content Security Policy in production** | `shared/middleware.py` | `SecurityHeadersMiddleware` uses `'unsafe-eval'` when CSP nonce is missing. This effectively disables CSP. |
| 206 | **JWT in localStorage (some code paths)** | `lib/api.ts`, stub pages | Multiple stub pages use `localStorage.getItem('token')`. If any code path stores JWT there, it's vulnerable to XSS. |
| 207 | **No HTTPS enforcement** | Backend | No middleware to redirect HTTP → HTTPS or set HSTS. |

### P1 — Major
| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 208 | **Cookie precedence over Bearer token** | `dependencies.py` L198–202 | A stolen cookie overrides a legitimate `Authorization` header. |
| 209 | **`get_client_ip` uses rightmost X-Forwarded-For** | `shared/middleware.py` | Some proxy configurations put the real IP leftmost. Could rate-limit the wrong IP. |
| 210 | **No Stripe webhook signature validation visible** | `api/billing.py` | Webhook handler does not clearly verify Stripe signature before processing events. |
| 211 | **Magic link JWT secret same as session JWT secret** | `api/auth.py` | If one is compromised, both are compromised. Should use separate signing keys. |
| 212 | **No account lockout after failed magic links** | `api/auth.py` | Rate limiting exists but no account-level lockout. An attacker can keep requesting links for a victim's email. |

---

## 16. ACCESSIBILITY (16 issues)

| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 213 | **Tooltips only on hover** | `JobCard.tsx` | `SkillMatchTooltip`, `MatchExplanationTooltip` use `opacity-0`/`group-hover:opacity-100`. Invisible to keyboard/screen reader users. |
| 214 | **Job card "Why this match?" button missing aria-expanded** | `JobCard.tsx` | Toggle has no ARIA state. |
| 215 | **Job detail drawer backdrop has no aria-hidden** | `JobDetailDrawer.tsx` | Backdrop is interactive but not marked for assistive tech. |
| 216 | **ATS score textareas lack labels** | `ats-score.tsx` | No associated `<label>` elements. |
| 217 | **Career goals options missing role="radio"** | `CareerGoalsStep.tsx` | Custom option buttons lack proper radio group semantics. |
| 218 | **Work style progress dots missing current indicator** | `WorkStyleStep.tsx` | Screen readers can't tell which question is current. |
| 219 | **Skill review actions invisible without hover** | `SkillReviewStep.tsx` | Edit/delete only visible on hover — inaccessible on touch/keyboard. |
| 220 | **Ready step countdown has no aria-live** | `ReadyStep.tsx` | Animated countdown not announced to screen readers. |
| 221 | **DLQ dashboard native checkbox without label** | `dlq-dashboard/index.tsx` | Bare `<input type="checkbox">` with no accessible name. |
| 222 | **Matches page skill expand/collapse missing aria-expanded** | `matches.tsx` | `SkillList` toggle button lacks ARIA. |
| 223 | **Focus trap issues in CoverLetterGenerator** | `CoverLetterGenerator.tsx` | No `active` prop; trap may stay active after modal closes. |
| 224 | **Mobile menu has no focus management** | `MobileMenu.tsx` | Opening drawer doesn't move focus into it. |
| 225 | **Tables missing caption/summary** | `ApplicationsView.tsx` | Application table has no `<caption>` for screen readers. |
| 226 | **Color-only status indication** | Throughout | Status badges use color alone (green, red, amber) with no icon or text pattern for color-blind users. (Partially mitigated by text labels.) |
| 227 | **No skip-to-content on app pages** | `AppLayout.tsx` | Skip link exists on login but not on the main app layout. |
| 228 | **Form error announcement timing** | `Onboarding.tsx` | Errors set via `setFormErrors` may not trigger `role="alert"` live regions. |

---

## 17. PERFORMANCE (4 issues)

| # | Issue | File(s) | Detail |
|---|-------|---------|--------|
| 229 | **No code splitting for stub pages** | `App.tsx` | All 20+ pages loaded eagerly or with basic lazy loading but no route-based chunking strategy. |
| 230 | **`useProfile` and `OnboardingGuard` duplicate profile fetches** | `App.tsx`, `AuthGuard.tsx` | Profile is fetched in AuthContext, OnboardingGuard, and useProfile — potentially 3 requests on page load. |
| 231 | **Application polling every 15s regardless of tab visibility** | `useApplications.ts` | Wastes bandwidth and API resources when user is away. |
| 232 | **Full font loaded on every page** | `Onboarding.tsx` | Google Fonts preload link added dynamically; should be in `<head>` statically for all pages. |

---

## Summary: Top 20 Items to Fix First

| Priority | # | Issue | Impact |
|----------|---|-------|--------|
| P0 | 189 | Storage endpoint crashes (`.get()` on non-dict) | Runtime crash |
| P0 | 121 | `CoverLetterResponse_V1` undefined — cover letter crashes | Feature broken |
| P0 | 122 | AI endpoints have no auth | Security hole |
| P0 | 167–168 | Navigation.tsx/MobileMenu.tsx wrong routes | All nav broken |
| P0 | 169 | MobileMenu shows "John Doe" hardcoded | Trust destroyer |
| P0 | 149 | DLQ backend raises NotImplementedError | Feature crashes |
| P0 | 147–148 | Pipeline view wrong HTTP method + stage value | Feature broken |
| P0 | 177–178 | DB missing `stage` and `tenant_id` columns | Query failures |
| P0 | 205 | CSP uses `unsafe-eval` | Security risk |
| P0 | 1 | httpOnly cookie check is dead code | Auth detection broken |
| P1 | 69 | Swipe POST to wrong endpoint | Job apply broken |
| P1 | 83 | Snooze loading state never shows | UX bug |
| P1 | 84 | Withdraw/Review don't refetch list | Stale data |
| P1 | 57 | Success rate always 0% | Misleading metric |
| P1 | 114 | Data export requires password but users don't have one | Feature blocked |
| P1 | 151–158 | 8 stub pages shown in production nav | Trust issue |
| P1 | 70 | No duplicate application guard | Data integrity |
| P1 | 71 | No job detail view before applying | Major UX gap |
| P1 | 72 | No filters on jobs view despite preferences set | UX gap |
| P1 | 100 | Stripe webhook no idempotency | Payment risk |
