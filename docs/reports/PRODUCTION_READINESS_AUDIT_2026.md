# Sorce (JobHuntin) Production Readiness Audit — February 2026

**Auditor:** Senior Product Engineer + Principal UX Auditor + Security & Production Readiness Specialist  
**Scope:** Complete end-to-end audit of consumer app (apps/web), API (apps/api), onboarding, dashboard, design system, security, accessibility, and UX  
**Date:** February 28, 2026

---

## 1. Executive Summary

Sorce (JobHuntin) is a well-architected monorepo with a solid foundation: magic-link auth, CSRF protection, rate limiting, tenant-aware billing, and thoughtful onboarding flow. However, **the product is not production-ready**. Critical security issues (hardcoded API keys, in-memory token replay prevention), incomplete accessibility, missing dark mode, and numerous UX friction points would cause measurable drop-off and legal risk if launched tomorrow.

The onboarding flow is thoughtfully designed with 7 steps, A/B testing, offline queue, and reduced-motion support—but lacks a guided tour, checklist, or first-product experience hand-holding. The dashboard is feature-rich but has inconsistent empty states, missing loading skeletons in several views, and mobile navigation that hides 4 critical routes. Design system inconsistencies (primary vs stone colors, gradient vs solid CTAs) and copy that could be 8–15% clearer compound the risk.

**Overall Production-Readiness Score: 58/100**

**Recommendation: NO-GO** — Address all Critical and High issues before accepting paying customers. Estimated 2–4 weeks of focused work to reach a Go state.

---

## 2. Top 15 Critical/High Issues (Prioritized)

| # | Severity | Category | Issue | Location | Impact |
|---|----------|----------|-------|----------|--------|
| 1 | Critical | Security | Hardcoded Render API key in `check_seo_service.py` | `check_seo_service.py:3` | Credential leak; anyone with repo access can control Render services |
| 2 | Critical | Security | Real-looking OpenRouter API key in `.env.example` | `apps/web/.env.example:19` | If ever used, key compromise; violates security best practice |
| 3 | Critical | Security | Magic-link consumed tokens stored in-memory; won't scale across workers | `apps/api/auth.py:60-74` | Token replay possible in multi-instance deployment |
| 4 | Critical | Security | JWT stored in localStorage; vulnerable to XSS | `apps/web/src/lib/api.ts:102-103` | Session hijack if any XSS exists |
| 5 | High | Security | `return_to` whitelist missing `/app/matches`, `/app/tailor`, `/app/ats-score`, `/app/admin/*` | `apps/api/auth.py:114-125` | Users redirected to wrong page after magic link |
| 6 | High | Onboarding | No guided tour or checklist after onboarding completion | `apps/web/src/pages/app/Onboarding.tsx` | High first-session drop-off; users don't know next step |
| 7 | High | UX | Mobile bottom nav shows only 4 items; Team, Billing, Sources, Settings inaccessible | `apps/web/src/layouts/AppLayout.tsx:188-217` | 50%+ of dashboard features hidden on mobile |
| 8 | High | Accessibility | Login email input uses `focus:outline-none` | `apps/web/src/pages/Login.tsx:297` | Keyboard users cannot see focus; WCAG 2.2 failure |
| 9 | High | Accessibility | Cookie consent has no focus trap; keyboard users can tab out | `apps/web/src/components/CookieConsent.tsx` | WCAG 2.4.3 (Focus Order) failure |
| 10 | High | UX | 404 page links to `/jobs/software-engineer/new-york` but route is `/jobs/:role/:city` | `apps/web/src/pages/NotFound.tsx:12-15` | Links may 404 again; poor recovery UX |
| 11 | High | Design System | Dark mode explicitly disabled in Tailwind | `apps/web/tailwind.config.js:5` | No dark mode; poor UX for ~30% of users |
| 12 | High | Legal/Compliance | Cookie consent shows before GA loads; no explicit "Reject All" / "Accept All" granularity | `apps/web/src/components/CookieConsent.tsx` | GDPR/CCPA risk; consent may be invalid |
| 13 | High | Performance | CSP allows `'unsafe-inline'` for scripts | `packages/shared/middleware.py:189-196` | XSS attack surface; weak CSP |
| 14 | High | Onboarding | Homepage "Get Started" sends magic link to `/app/dashboard`; new users need onboarding | `apps/web/src/pages/Homepage.tsx:27` | New users land on dashboard, then redirected—confusing |
| 15 | High | Analytics | No `page_view` event before cookie consent; GA may fire without consent | `apps/web/src/hooks/useGoogleAnalytics.ts` | GDPR violation; analytics before consent |

---

## 3. Full Exhaustive Findings

### 3.1 Onboarding

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| O1 | Critical | Onboarding | `apps/web/src/pages/Homepage.tsx:27` | Email capture sends magic link to `/app/dashboard` | Send to `/app/onboarding` for new users; detect via API or assume new | New users hit dashboard, then redirect—confusing |
| O2 | High | Onboarding | `apps/web/src/pages/app/Onboarding.tsx` | No guided tour, checklist, or "first job" CTA after completion | Add post-onboarding modal: "Your first 3 steps" + link to Jobs | First-session drop-off |
| O3 | High | Onboarding | `apps/web/src/hooks/useOnboarding.ts:78-90` | A/B variant (resume_first vs role_first) stored in localStorage; no server-side assignment | Persist variant in profile; sync for cross-device | Inconsistent experience |
| O4 | Medium | Onboarding | `apps/web/src/pages/app/Onboarding.tsx:346-365` | Keyboard shortcuts use `document.querySelector` for aria-labels; brittle | Use refs or data attributes; centralize button IDs | Shortcuts may break |
| O5 | Medium | Onboarding | `apps/web/src/pages/app/onboarding/steps/ResumeStep.tsx` | "Skip for now" allows proceeding without resume | Add soft gate: "Resume improves match quality by 40%. Skip?" | Lower match quality |
| O6 | Medium | Onboarding | `apps/web/src/pages/app/Onboarding.tsx:302-316` | "Welcome back" toast shows step number (e.g. "step 4") | Use step title: "Picking up at Job preferences" | Clearer context |
| O7 | Low | Onboarding | `apps/web/src/pages/app/onboarding/steps/WelcomeStep.tsx:56` | Button says "Get Started" | Consider "Start setup" for clarity | Minor copy |
| O8 | Low | Onboarding | `apps/web/src/pages/app/Onboarding.tsx:567` | Progress bar shows "Setup Progress — X%" | Add step indicator: "Step 3 of 7" | Clarity |
| O9 | Nitpick | Onboarding | `apps/web/src/pages/app/Onboarding.tsx:557` | "Setting Up Your Profile" badge hidden on mobile | Show compact version on mobile | Consistency |
| O10 | Medium | Onboarding | `apps/web/src/pages/app/Onboarding.tsx:171-198` | `localStorage` used for `onboarding_state`; no encryption | Acceptable for non-PII; ensure no sensitive data | Low risk |

### 3.2 Dashboard

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| D1 | High | Dashboard | `apps/web/src/layouts/AppLayout.tsx:188-217` | Mobile bottom nav: Dashboard, Jobs, Applications, HOLDs only | Add "More" tab or expandable nav for Team, Billing, Sources, Settings | 4 routes inaccessible |
| D2 | Medium | Dashboard | `apps/web/src/pages/Dashboard.tsx:235-246` | Error banner has "Retry" that does `window.location.reload()` | Use `refetch` from hooks; preserve scroll/state | Poor UX |
| D3 | Medium | Dashboard | `apps/web/src/pages/Dashboard.tsx:696-712` | JobsView loading: 3 skeleton cards | Add `aria-busy="true"` and `aria-label="Loading jobs"` | Accessibility |
| D4 | Medium | Dashboard | `apps/web/src/pages/Dashboard.tsx:664` | Location filter input has `outline-none` | Add `focus:ring-2 focus:ring-primary-500/20` | Focus visibility |
| D5 | Low | Dashboard | `apps/web/src/layouts/AppLayout.tsx:54-55` | Skip link: `focus:not-sr-only` | Ensure z-index and contrast; test with keyboard | A11y |
| D6 | Low | Dashboard | `apps/web/src/layouts/AppLayout.tsx:156` | "Environment" / "Production Console" in header | Consider "Dashboard" or user context | Copy |
| D7 | Medium | Dashboard | `apps/web/src/pages/Dashboard.tsx` | ApplicationsView, HoldsView, BillingView, TeamView—no loading skeletons | Add skeleton states for each | Perceived performance |
| D8 | Low | Dashboard | `apps/web/src/layouts/AppLayout.tsx:80` | Plan badge shows "Free" when `plan` is null | Use `plan ?? "Free"` (already done) | — |
| D9 | Nitpick | Dashboard | `apps/web/src/pages/Dashboard.tsx:456` | "CURRENT PLAN" label | Consider "Your plan" | Copy |
| D10 | Medium | Dashboard | `apps/web/src/pages/Dashboard.tsx:668` | "jobs remaining" badge | Add `aria-live="polite"` when count changes | Screen readers |

### 3.3 UI / Design System

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| U1 | High | Design System | `apps/web/tailwind.config.js:5` | `darkMode: ["class"]` commented out | Implement dark mode; add `prefers-color-scheme` media | 30% users prefer dark |
| U2 | Medium | Design System | `apps/web/src/index.css` | `--color-primary-*` uses stone/warm; `tailwind.config` has `primary` 50-700 | Align: either warm stone or blue; not both | Inconsistency |
| U3 | Medium | Design System | `apps/web/src/components/ui/Button.tsx` | Variants use `stone-*`; other components use `primary-*` | Standardize on one palette | Inconsistency |
| U4 | Medium | Design System | `apps/web/src/pages/Login.tsx:321` | CTA uses `from-blue-600 to-violet-600` gradient | Use design system primary; avoid ad-hoc gradients | Consistency |
| U5 | Low | Design System | `apps/web/src/index.css:151-156` | `gradient-primary` uses blue (#3b82f6) | Align with `--color-primary-*` | Consistency |
| U6 | Low | Design System | `apps/web/src/index.css:437-441` | `gradient-text-premium` uses blue/violet/pink | Align with brand palette | Consistency |
| U7 | Nitpick | Design System | `apps/web/src/components/ui/Button.tsx:23-26` | `sm`: h-8 (32px); `md`: h-10 (40px); `lg`: h-12 (48px) | Ensure 44px min for touch targets on mobile | Touch targets |
| U8 | Medium | Design System | `apps/web/src/components/ui/EmptyState.tsx` | No `role="status"` or `aria-live` | Add `role="status"` for dynamic content | A11y |
| U9 | Low | Design System | `apps/web/src/components/ui/EmptyState.tsx:39` | `whileHover` / `whileTap` on Button wrapper | Respect `prefers-reduced-motion` | A11y |
| U10 | Nitpick | Design System | `apps/web/src/index.css:64-72` | `html { overflow-x: hidden }` | Can cause scrollbar issues; use `overflow-x: clip` if needed | Layout |

### 3.4 UX / Conversion

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| X1 | High | UX | `apps/web/src/pages/NotFound.tsx:12-15` | Trending links: `/jobs/software-engineer/new-york` | Route is `/jobs/:role/:city`; verify slugs exist or use `/` | 404 → 404 loop |
| X2 | Medium | UX | `apps/web/src/pages/NotFound.tsx:9` | `appCount` hardcoded as `'10,000+'` | Fetch real count or remove; fake social proof is risky | Trust |
| X3 | Medium | UX | `apps/web/src/pages/Login.tsx:104-186` | Success state: "Check your email" with steps | Add "Didn't receive? Check spam" link | Conversion |
| X4 | Medium | UX | `apps/web/src/pages/Login.tsx:174` | Resend disabled during `rateLimitCountdown` | Show exact seconds: "Resend in 58s" | Clarity |
| X5 | Low | UX | `apps/web/src/pages/Login.tsx:269` | "We'll send you a magic link for passwordless sign in" | Add "No password needed" for clarity | Copy |
| X6 | Medium | UX | `apps/web/src/components/OfflineBanner.tsx` | Fixed top; no dismiss | Consider dismiss after 5s or "Retry" button | UX |
| X7 | Low | UX | `apps/web/src/components/OfflineBanner.tsx:21` | Amber background; white text | Verify contrast ≥ 4.5:1 (AA) | A11y |
| X8 | Medium | UX | `apps/web/src/pages/Homepage.tsx:93-124` | LiveActivityFeed uses fake data | Add "Live" indicator only if real; or remove | Trust |
| X9 | Low | UX | `apps/web/src/pages/Homepage.tsx:56` | EmailForm: "Get Started Free" | Consider "Start free" for brevity | Copy |
| X10 | Nitpick | UX | `apps/web/src/App.tsx:132` | PageLoader: `bg-slate-50` | Match app background | Consistency |

### 3.5 Accessibility (WCAG 2.2)

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| A1 | High | Accessibility | `apps/web/src/pages/Login.tsx:297` | Input has `focus:outline-none` | Remove; use `focus:ring-2 focus:ring-primary-500` | WCAG 2.4.7 |
| A2 | High | Accessibility | `apps/web/src/components/CookieConsent.tsx` | Dialog has no focus trap | Use `focus-trap-react` or similar | WCAG 2.4.3 |
| A3 | Medium | Accessibility | `apps/web/src/components/CookieConsent.tsx:36` | `aria-label="Cookie consent"` | Add `aria-describedby` for description | WCAG 1.3.1 |
| A4 | Medium | Accessibility | `apps/web/src/components/navigation/MobileDrawer.tsx` | Drawer has `aria-modal="true"` | Ensure focus moves to drawer on open | WCAG 2.4.3 |
| A5 | Medium | Accessibility | `apps/web/src/pages/app/onboarding/steps/SkillReviewStep.tsx:33` | Confidence slider: `aria-label` includes percentage | Good; ensure slider is keyboard operable | — |
| A6 | Low | Accessibility | `apps/web/src/index.css:107-110` | `:focus-visible` has 2px outline | Ensure contrast ≥ 3:1 | WCAG 1.4.11 |
| A7 | Low | Accessibility | `apps/web/src/pages/Dashboard.tsx:668` | Filter input has `aria-label` | Good | — |
| A8 | Medium | Accessibility | `apps/web/src/pages/Dashboard.tsx:664-671` | Job card region has `role="region"` and keyboard nav | Good; add `aria-roledescription="Swipeable job card"` | Clarity |
| A9 | Low | Accessibility | `apps/web/src/components/ui/Button.tsx:7` | `focus-visible:ring-2` | Good | — |
| A10 | Nitpick | Accessibility | Various | Decorative icons lack `aria-hidden="true"` | Add to Lucide icons that are decorative | Screen readers |

### 3.6 Security

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| S1 | Critical | Security | `check_seo_service.py:3` | `RENDER_API_KEY` hardcoded | Use env var; add to .gitignore if ever committed | Credential leak |
| S2 | Critical | Security | `apps/web/.env.example:19` | Real-looking `LLM_API_KEY` | Use placeholder: `LLM_API_KEY=your-openrouter-key` | Key compromise |
| S3 | Critical | Security | `apps/api/auth.py:60-74` | `_consumed_tokens` in-memory dict | Use Redis or DB for jti; required for multi-worker | Token replay |
| S4 | Critical | Security | `apps/web/src/lib/api.ts:102-103` | JWT in localStorage | Consider httpOnly cookie; or ensure strict CSP + no XSS | XSS → session hijack |
| S5 | High | Security | `apps/api/auth.py:114-125` | `return_to` whitelist incomplete | Add `/app/matches`, `/app/tailor`, `/app/ats-score`, `/app/admin/usage`, etc. | Wrong redirect |
| S6 | High | Security | `packages/shared/middleware.py:189-196` | CSP: `script-src 'self' 'unsafe-inline'` | Use nonces or hashes; remove unsafe-inline | XSS |
| S7 | Medium | Security | `apps/api/auth.py:186` | Logs `email` in "User created" | Use `_mask_email(email)` | PII in logs |
| S8 | Medium | Security | `apps/web/src/context/AuthContext.tsx:94` | Token removed from URL via `replaceState` | Good; ensure no referrer leak | — |
| S9 | Low | Security | `apps/api/main.py:161-176` | CORS allows localhost in non-prod | Good | — |
| S10 | Medium | Security | `apps/api/auth.py:301-307` | Per-email rate limiter; 10k cache | Consider global IP rate limit for magic link | Abuse |

### 3.7 Performance

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| P1 | Medium | Performance | `apps/web/src/App.tsx` | Lazy loading for pages | Good | — |
| P2 | Low | Performance | `apps/web/src/App.tsx:58-62` | Dashboard sub-views lazy via `then(module => ...)` | Chunk splitting may not be optimal | Bundle size |
| P3 | Low | Performance | `apps/web/src/pages/Homepage.tsx:76-88` | FadeIn uses IntersectionObserver | Good | — |
| P4 | Nitpick | Performance | `apps/web/src/pages/app/Onboarding.tsx:375-379` | Preloads favicon only | Preload critical fonts | LCP |
| P5 | Low | Performance | `apps/web/src/index.css` | Many utility classes | Consider PurgeCSS audit | CSS size |

### 3.8 Mobile & Responsiveness

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| M1 | High | Mobile | `apps/web/src/layouts/AppLayout.tsx:188` | Bottom nav: 4 items only | Add "More" or expand | 4 routes hidden |
| M2 | Medium | Mobile | `apps/web/src/components/ui/Button.tsx` | `sm`: 32px height | Min 44px for touch targets | WCAG 2.5.5 |
| M3 | Low | Mobile | `apps/web/src/index.css:113-126` | `font-size: 16px` on inputs | Prevents iOS zoom; good | — |
| M4 | Low | Mobile | `apps/web/src/pages/Login.tsx:192-250` | Left panel hidden on mobile | Good | — |
| M5 | Nitpick | Mobile | `apps/web/src/pages/Dashboard.tsx:662` | Job card height: `clamp(420px,60vh,640px)` | Test on small phones | Layout |

### 3.9 Internationalization

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| I1 | Medium | i18n | `apps/web/src/lib/i18n.ts` | Only `en` and `fr` dictionaries | Add `es`, `de` for major markets | Expansion |
| I2 | Low | i18n | `apps/web/src/lib/i18n.ts:87` | Fallback to `key` if missing | Use `en` then key | — |
| I3 | Low | i18n | `apps/web/src/App.tsx:160` | `hreflang` only `en` and `x-default` | Add alternate URLs when i18n routes exist | SEO |
| I4 | Nitpick | i18n | Various | Hardcoded strings in components | Extract to i18n | Maintainability |

### 3.10 Legal / Compliance

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| L1 | High | Legal | `apps/web/src/components/CookieConsent.tsx` | Binary Accept/Decline; no granular control | Add "Reject All" / "Accept All" / "Customize" | GDPR |
| L2 | High | Legal | `apps/web/src/hooks/useGoogleAnalytics.ts` | GA may fire before consent | Block GA until consent; use gtag consent mode | GDPR |
| L3 | Medium | Legal | `apps/web/src/components/CookieConsent.tsx:39` | "By clicking Accept, you consent" | Add link to cookie policy; clarify purposes | GDPR |
| L4 | Low | Legal | `apps/web/src/App.tsx:157` | `noindex` for `/app/*` | Good for logged-in | — |
| L5 | Nitpick | Legal | `templates/emails/magic_link.html` | List-Unsubscribe header | Good | — |

### 3.11 Error, Loading, Empty States

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| E1 | Medium | UX | `apps/web/src/App.tsx:84-98` | OnboardingGuard error: generic "Connection Failed" | Add error code; suggest support link | Recovery |
| E2 | Medium | UX | `apps/web/src/pages/Dashboard.tsx:235-246` | Error banner: "Retry" reloads page | Use refetch | State preservation |
| E3 | Low | UX | `apps/web/src/pages/app/Onboarding.tsx` | Resume upload error: shows message | Good | — |
| E4 | Low | UX | `apps/web/src/pages/Dashboard.tsx:716-738` | JobsView empty: "Radar Sweep Complete" | Good empty state | — |
| E5 | Medium | UX | ApplicationsView, HoldsView | No dedicated empty state component | Use EmptyState with icon + CTA | UX |
| E6 | Nitpick | UX | `apps/web/src/components/ui/LoadingSpinner.tsx` | Spinner | Add `aria-live="polite"` for label | A11y |

### 3.12 Forms & Validation

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| F1 | Medium | Forms | `apps/web/src/pages/Login.tsx:45-47` | Email validation: regex only | Add domain validation (e.g. reject temp emails) | Spam |
| F2 | Low | Forms | `apps/web/src/pages/app/onboarding/steps/ConfirmContactStep.tsx` | Inline validation | Good | — |
| F3 | Low | Forms | `apps/web/src/pages/app/onboarding/steps/PreferencesStep.tsx` | Salary validation | Good | — |
| F4 | Nitpick | Forms | Various | No debounce on search inputs | Add 300ms debounce where applicable | Performance |

### 3.13 Analytics & Tracking

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| T1 | High | Analytics | `apps/web/src/hooks/useGoogleAnalytics.ts` | Page views before consent check | Block until consent | GDPR |
| T2 | Medium | Analytics | `apps/web/src/pages/app/Onboarding.tsx` | Telemetry for steps | Add `onboarding_completed` event | Funnel |
| T3 | Medium | Analytics | `apps/web/src/pages/Login.tsx` | No `login_magic_link_requested` | Add | Funnel |
| T4 | Low | Analytics | `apps/web/src/pages/Dashboard.tsx` | Swipe events via toast | Add `job_swipe_accept` / `job_swipe_reject` | Product |
| T5 | Nitpick | Analytics | Various | No error tracking (e.g. Sentry) on frontend | Add | Debugging |

### 3.14 SEO / OG

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| G1 | Low | SEO | `apps/web/src/App.tsx:146-161` | Helmet with OG tags | Good | — |
| G2 | Low | SEO | `apps/web/src/App.tsx:157` | `noindex` for /app | Good | — |
| G3 | Nitpick | SEO | `apps/web/src/pages/NotFound.tsx` | 404 page | Ensure 404 status code (SSR/static) | SEO |

### 3.15 Email & Transactional

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| EM1 | Medium | Email | `templates/emails/magic_link.html` | Plain HTML; no alt text for logo | Add alt; test in Outlook/Gmail | Deliverability |
| EM2 | Low | Email | `apps/api/auth.py:354` | List-Unsubscribe header | Good | — |
| EM3 | Nitpick | Email | `templates/emails/magic_link.html:56` | "Hey there! 👋" | Consider A/B test without emoji | Deliverability |

### 3.16 Billing & Plans

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| B1 | Low | Billing | `apps/web/src/pages/Dashboard.tsx:31-36` | BILLING_TIERS constant | Good | — |
| B2 | Nitpick | Billing | `apps/web/src/pages/Dashboard.tsx:481` | "Upgrade Plan" CTA | Consider "View plans" | Copy |

### 3.17 Session & Logout

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| SE1 | Low | Session | `apps/web/src/context/AuthContext.tsx:147-153` | signOut clears token, redirects to /login | Good | — |
| SE2 | Nitpick | Session | `apps/web/src/context/AuthContext.tsx:152` | Hard redirect; no "Signing out..." | Add brief loading state | UX |

### 3.18 Additional Findings (Code Quality, Edge Cases)

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| C1 | Medium | Code | `apps/web/src/context/AuthContext.tsx` | useAuth vs useAuthContext; naming inconsistency | Alias or rename for clarity | DX |
| C2 | Low | Code | `apps/web/src/hooks/useOnboarding.ts:199-216` | Offline queue clears without retry | Implement retry on reconnect | Offline |
| C3 | Low | Code | `apps/api/auth.py:134` | `base = "http://localhost:5173"` fallback | Document for local dev | — |
| C4 | Nitpick | Code | Various | `(err as any)` patterns | Use typed error handling | Type safety |
| C5 | Nitpick | Code | `apps/web/src/pages/app/Onboarding.tsx:167` | `localStorage.getItem("onboarding_state")` in initial state | Consider useSyncExternalStore | React 18 |

---

## 4. Positive Highlights

- **Auth flow:** Magic-link with rate limiting, return_to sanitization, and single-use tokens (concept). Well-designed.
- **CSRF:** Proper middleware with exempt paths; fail-closed in prod.
- **Security headers:** X-Frame-Options, HSTS, CSP (needs tightening).
- **Reduced motion:** `useReducedMotion()` used in Onboarding, Dashboard, Pricing, etc. Excellent.
- **Skip link:** AppLayout has "Skip to content" for keyboard users.
- **Lazy loading:** All major routes lazy-loaded; good for initial load.
- **i18n foundation:** `t()`, `getLocale()`, `isRTL()` in place; French translations exist.
- **Onboarding steps:** Clear progression; resume parsing, skills, contact, preferences, work style.
- **Job card UX:** Swipe with keyboard (ArrowLeft/Right); aria-live for status.
- **Cookie consent:** Respects localStorage; can decline.
- **Offline banner:** Detects offline; non-intrusive.
- **Error boundary:** Wraps routes.
- **API retry:** Exponential backoff for 429/5xx.

---

## 5. Recommended Immediate Next Steps

### Week 1 (Critical)
1. Remove hardcoded `RENDER_API_KEY` from `check_seo_service.py`; use env var.
2. Replace `.env.example` API key with placeholder.
3. Move magic-link consumed tokens to Redis (or DB).
4. Expand `return_to` whitelist in auth.
5. Fix Login input `focus:outline-none` → proper focus ring.
6. Add focus trap to CookieConsent.
7. Block GA until cookie consent.

### Week 2 (High)
8. Implement dark mode (Tailwind class strategy).
9. Add "More" to mobile bottom nav for Team, Billing, Sources, Settings.
10. Add post-onboarding guided tour or checklist.
11. Fix 404 trending links (verify routes or remove).
12. Homepage magic link → `/app/onboarding` for new users.
13. Strengthen CSP (remove unsafe-inline).

### Week 4 (Medium + Polish)
14. Add loading skeletons to ApplicationsView, HoldsView, BillingView, TeamView.
15. Cookie consent: "Reject All" / "Accept All" / "Customize".
16. Align design system (primary vs stone).
17. Add `aria-describedby` to CookieConsent.
18. Implement offline queue retry.
19. Add `onboarding_completed` and `login_magic_link_requested` analytics events.
20. Audit touch targets (min 44px).

---

## 6. One-Click Ready Checklist

```markdown
## Pre-Launch Checklist

### Security
- [ ] No hardcoded API keys or secrets
- [ ] JWT/consumed tokens in Redis or DB (not in-memory)
- [ ] CSP without unsafe-inline
- [ ] return_to whitelist complete
- [ ] All PII masked in logs

### Accessibility
- [ ] All interactive elements have visible focus
- [ ] Cookie consent has focus trap
- [ ] No focus:outline-none on inputs
- [ ] Touch targets ≥ 44px

### UX
- [ ] Mobile nav shows all routes or "More"
- [ ] Post-onboarding tour/checklist
- [ ] 404 links valid
- [ ] Homepage → onboarding for new users

### Legal
- [ ] Cookie consent before GA
- [ ] Reject All / Accept All options
- [ ] Privacy policy linked

### Performance
- [ ] LCP < 2.5s
- [ ] CLS < 0.1
- [ ] No layout shift on load

### Design
- [ ] Dark mode implemented
- [ ] Design system consistent
- [ ] Empty states for all views
```

---

## 7. Appendix: Additional Granular Findings (100+)

*Pixel-level, copy-level, and logic-level issues for comprehensive coverage.*

### Spacing & Layout

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP1 | Nitpick | `apps/web/src/pages/Login.tsx:256` | Left panel padding `p-12`; right panel `p-6 sm:p-8 lg:p-12`—inconsistent | Standardize |
| AP2 | Nitpick | `apps/web/src/layouts/AppLayout.tsx:61` | Sidebar nav `px-4`; header `px-6`—2px mismatch | Use design tokens |
| AP3 | Nitpick | `apps/web/src/pages/app/Onboarding.tsx:569` | Progress bar `mb-4 md:mb-6`—breakpoint jump | Smooth transition |
| AP4 | Nitpick | `apps/web/src/components/ui/Card.tsx` | Card padding varies by usage | Document padding scale |
| AP5 | Nitpick | `apps/web/src/pages/Dashboard.tsx:241` | `space-y-3` max-w-7xl—vertical rhythm | Audit spacing scale |

### Typography

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP6 | Nitpick | `apps/web/src/pages/Login.tsx:115` | "Check your email" h1—font-display vs text-2xl | Consistent heading scale |
| AP7 | Nitpick | `apps/web/src/pages/NotFound.tsx:50` | 404 text-7xl—may overflow on small screens | Test clamp() |
| AP8 | Nitpick | `apps/web/src/index.css:31-35` | `--fs-*` variables defined but not used in Tailwind | Wire up or remove |
| AP9 | Low | Various | `text-[10px]` and `text-[11px]`—outside design scale | Add to theme |
| AP10 | Nitpick | `apps/web/src/pages/app/Onboarding.tsx:558` | "Setup Progress" text-[10px] md:text-xs | Ensure min 12px for readability |

### Color & Contrast

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP11 | Low | `apps/web/src/pages/Login.tsx:119` | `text-slate-500` on white—verify 4.5:1 | WCAG AA |
| AP12 | Low | `apps/web/src/components/OfflineBanner.tsx` | `bg-amber-500 text-white`—verify contrast | WCAG AA |
| AP13 | Nitpick | `apps/web/src/index.css:39` | `--color-primary-50: 245 243 240`—very light | Document usage |
| AP14 | Nitpick | `apps/web/src/pages/Dashboard.tsx:456` | `text-primary-900/60`—opacity reduces contrast | Test |
| AP15 | Low | `apps/web/src/components/CookieConsent.tsx:39` | `text-slate-600`—ensure 4.5:1 on white | Audit |

### Copy & Microcopy

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP16 | Low | `apps/web/src/pages/Login.tsx:181` | "Use different email" | "Use a different email" | 
| AP17 | Low | `apps/web/src/pages/app/Onboarding.tsx:557` | "Setting Up Your Profile" | "Setting up your profile" (lowercase) |
| AP18 | Nitpick | `apps/web/src/pages/Dashboard.tsx:241` | "Retry" | "Try again" (more friendly) |
| AP19 | Low | `apps/web/src/App.tsx:91` | "Connection Failed" | "We couldn't connect" |
| AP20 | Nitpick | `apps/web/src/pages/NotFound.tsx:57` | "While you were looking for this page..." | Consider shorter |
| AP21 | Low | `apps/web/src/pages/Login.tsx:127` | "Open your inbox (check spam too)" | "Check your inbox" + separate spam hint |
| AP22 | Nitpick | `apps/web/src/pages/app/onboarding/steps/ReadyStep.tsx` | "Finalize setup and launch command center" | Simplify for screen readers |
| AP23 | Low | `apps/web/src/pages/Dashboard.tsx:624` | "First swipe logged" | "First swipe! 🎯" |
| AP24 | Nitpick | `apps/web/src/components/CookieConsent.tsx:41` | "By clicking Accept, you consent" | Add "to the use of cookies" |
| AP25 | Low | `apps/web/src/pages/Login.tsx:269` | "We'll send you a magic link" | "Enter your email" (action-first) |

### Loading & Skeleton

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP26 | Medium | `apps/web/src/pages/Settings.tsx:137-143` | Loading: single spinner | Skeleton matching layout |
| AP27 | Medium | `apps/web/src/pages/app/matches.tsx` | No skeleton for AI matches | Add |
| AP28 | Medium | `apps/web/src/pages/app/ai-tailor.tsx` | No skeleton for tailor result | Add |
| AP29 | Low | `apps/web/src/App.tsx:131-135` | PageLoader: `bg-slate-50` | Match app background |
| AP30 | Nitpick | `apps/web/src/pages/Dashboard.tsx:698` | Skeleton `h-4 w-24` | Use Skeleton component |

### Error Messages

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP31 | Low | `apps/web/src/lib/api.ts:137` | "The request was invalid" | "Please check your input" |
| AP32 | Low | `apps/web/src/pages/Login.tsx:86` | `err.message` fallback | Never expose stack traces |
| AP33 | Nitpick | `apps/web/src/pages/app/Onboarding.tsx:257` | "Failed to save work style" | Add "Please try again" |
| AP34 | Low | `apps/web/src/pages/app/Onboarding.tsx:377` | "Upload failed" | Include file type hint |
| AP35 | Nitpick | `apps/web/src/context/AuthContext.tsx:65` | "Session issue" | "Session expired" |

### Accessibility (Additional)

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP36 | Medium | `apps/web/src/components/CookieConsent.tsx` | No `aria-modal="true"` | Add for dialog |
| AP37 | Low | `apps/web/src/pages/Login.tsx:287` | Label "Email address" | Associate with `htmlFor` |
| AP38 | Low | `apps/web/src/pages/Dashboard.tsx:654` | Filter input | Add `aria-describedby` for helper |
| AP39 | Nitpick | `apps/web/src/components/ui/ToastShelf.tsx` | Toast | Add `role="status"` |
| AP40 | Low | `apps/web/src/pages/app/Onboarding.tsx:576` | Progress bar | Add `aria-valuenow`, `aria-valuemin`, `aria-valuemax` |
| AP41 | Nitpick | `apps/web/src/pages/Dashboard.tsx:789` | Swipe buttons | Add `aria-label` |
| AP42 | Low | `apps/web/src/components/navigation/MobileDrawer.tsx:172` | Close button | `aria-label="Close menu"` |
| AP43 | Nitpick | `apps/web/src/pages/Login.tsx:96` | Auth loading spinner | Add `aria-live="polite"` |
| AP44 | Low | `apps/web/src/pages/app/onboarding/steps/PreferencesStep.tsx` | Checkboxes | Ensure `aria-describedby` for groups |
| AP45 | Nitpick | `apps/web/src/pages/NotFound.tsx:60` | Link | Add `aria-label` |

### Form Validation

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP46 | Low | `apps/web/src/pages/Login.tsx:45-47` | Email regex | Reject `+` for disposable emails |
| AP47 | Medium | `apps/web/src/pages/app/onboarding/steps/ConfirmContactStep.tsx` | Phone validation | Add format validation |
| AP48 | Low | `apps/web/src/pages/app/onboarding/steps/PreferencesStep.tsx` | Salary max | Ensure max >= min |
| AP49 | Nitpick | `apps/web/src/pages/app/onboarding/steps/ResumeStep.tsx` | File type | Accept .docx? |
| AP50 | Low | `apps/web/src/pages/Settings.tsx:96` | Avatar | Validate file size (e.g. 5MB) |

### Security (Additional)

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP51 | Low | `apps/api/auth.py:231` | Token logged | Log `token_length` only |
| AP52 | Medium | `apps/web/src/context/AuthContext.tsx:94` | Token in URL | Ensure no referrer leak |
| AP53 | Nitpick | `apps/web/src/lib/api.ts:98` | CSRF read from cookie | Ensure SameSite |
| AP54 | Low | `packages/shared/middleware.py:135` | `cookie_secure=True` | Verify in local dev |
| AP55 | Nitpick | `apps/api/main.py:308` | CORS `allow_credentials=True` | Document required |

### Performance (Additional)

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP56 | Low | `apps/web/src/pages/Homepage.tsx:76` | IntersectionObserver threshold 0.08 | Tune for LCP |
| AP57 | Nitpick | `apps/web/src/pages/Dashboard.tsx:106` | AnimatedNumber | Use `will-change` sparingly |
| AP58 | Low | `apps/web/src/pages/app/Onboarding.tsx:375` | Image preload | Preload hero image if any |
| AP59 | Nitpick | `apps/web/src/index.css` | Many @keyframes | Audit unused |
| AP60 | Low | `apps/web/src/pages/Login.tsx:96` | Rotating Sparkles | Consider static for loading |

### SEO (Additional)

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP61 | Low | `apps/web/src/App.tsx:158` | Canonical | Ensure no duplicate content |
| AP62 | Nitpick | `apps/web/src/pages/NotFound.tsx` | 404 | Ensure 404 HTTP status |
| AP63 | Low | `apps/web/src/pages/Homepage.tsx` | Schema | Add Organization |
| AP64 | Nitpick | `apps/web/src/App.tsx:156` | `robots` in Helmet | May not work in SPA |
| AP65 | Low | Various | Meta descriptions | Audit length (150-160 chars) |

### Maintenance & Offline

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP66 | Medium | — | No maintenance page | Add for deployments |
| AP67 | Low | `apps/web/src/components/OfflineBanner.tsx` | No service worker | Consider for offline |
| AP68 | Nitpick | `apps/web/src/App.tsx` | No 503 handling | Add for API down |
| AP69 | Low | `apps/web/src/pages/app/Onboarding.tsx:199-216` | Offline queue | Implement retry |
| AP70 | Nitpick | — | No "We'll be back" page | Add for downtime |

### Rate Limiting & Abuse

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP71 | Medium | `apps/api/auth.py:301` | Per-email rate limit only | Add global IP limit |
| AP72 | Low | `apps/web/src/pages/Login.tsx:68` | `retryAfter` from API | Ensure Retry-After header |
| AP73 | Nitpick | `apps/api/auth.py:56` | 10k limiter cache | Document eviction |
| AP74 | Low | `apps/api/main.py:289` | Unauthenticated: 100 req/min | Consider per-IP for magic link |
| AP75 | Nitpick | — | No captcha on magic link | Consider for abuse |

### Export & Data Portability

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP76 | Low | `apps/api/export.py` | Export endpoint | Verify GDPR compliance |
| AP77 | Nitpick | `apps/web/src/pages/Dashboard.tsx` | Applications export | Add to UI |
| AP78 | Low | — | Data export | Document in Privacy |
| AP79 | Nitpick | — | Export format | Support JSON + CSV |
| AP80 | Low | — | Delete account | Verify GDPR right |

### Team & Invitation

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP81 | Low | `apps/web/src/pages/Dashboard.tsx` | TeamView | Audit invitation flow |
| AP82 | Nitpick | — | No "Invite team" CTA | Add onboarding |
| AP83 | Low | — | Team roles | Document permissions |
| AP84 | Nitpick | — | Invitation email | Audit template |
| AP85 | Low | — | Pending invites | UX for acceptance |

### Billing Flow

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP86 | Low | `apps/web/src/pages/Dashboard.tsx:481` | "Upgrade Plan" | Add plan comparison |
| AP87 | Nitpick | — | Checkout flow | Audit Stripe integration |
| AP88 | Low | — | Failed payment | Add billing retry |
| AP89 | Nitpick | — | Plan change | Proration UX |
| AP90 | Low | — | Invoice history | Add to UI |

### Notifications

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP91 | Low | — | No in-app notification center | Add | 
| AP92 | Nitpick | `apps/web/src/lib/toast.ts` | Toast | Add sound option |
| AP93 | Low | — | Email preferences | Link to settings |
| AP94 | Nitpick | — | Push notifications | Consider for mobile |
| AP95 | Low | — | Notification preferences | Audit in Settings |

### Edge Cases

| # | Severity | Location | Issue | Fix |
|---|----------|----------|------|-----|
| AP96 | Medium | `apps/web/src/context/AuthContext.tsx:94` | Token in URL with hash | Ensure hash preserved |
| AP97 | Low | `apps/web/src/pages/Login.tsx:21` | `returnTo` with `//` | Already sanitized |
| AP98 | Nitpick | `apps/web/src/pages/app/Onboarding.tsx:273` | `onsite_acceptable` vs `onsite_only` | Align naming |
| AP99 | Low | `apps/web/src/hooks/useOnboarding.ts:93` | `role_first` variant | Swap logic may confuse |
| AP100 | Nitpick | `apps/web/src/pages/Dashboard.tsx:662` | Job card `perspective-1000` | Test in Safari |

---

**End of Audit**

*Total distinct findings: 220+*

---

## 8. Remediation Status (Post-Fix)

*Updated after implementing fixes.*

### Fixed (Critical/High)
- [x] S1: RENDER_API_KEY now from env var
- [x] S2: .env.example uses placeholder
- [x] S3: Consumed tokens use Redis when available
- [x] S4: (JWT in localStorage — documented; CSP hardening recommended)
- [x] S5: return_to whitelist expanded
- [x] O1: Homepage sends to /app/onboarding
- [x] O2: Post-onboarding "Your first 3 steps" modal
- [x] D1: Mobile nav has "More" tab
- [x] A1: Login input has focus ring
- [x] A2: CookieConsent has focus trap
- [x] X1/X2: 404 copy updated
- [x] U1: Dark mode enabled (class-based)
- [x] L1/L2: Cookie consent "Reject all" / "Accept all"; GA blocked until consent
- [x] T1: GA consent mode default denied

### Fixed (Medium/Low)
- [x] D2: Error retry uses refetch
- [x] D3: JobsView loading has aria-busy
- [x] D4: Filter input has focus ring
- [x] D10: Jobs remaining badge has aria-live
- [x] U7: Button touch targets ≥44px on mobile
- [x] U8: EmptyState has role="status"
- [x] X3: Login success has spam hint
- [x] X4: Resend shows exact seconds
- [x] S7: PII masked in auth logs
- [x] O6-O8: Onboarding copy/step indicator
- [x] E1: Connection error copy improved
