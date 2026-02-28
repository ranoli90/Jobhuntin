# Sorce (JobHuntin) — Complete Production-Readiness Audit

**Auditor:** Senior Product Engineer + Principal UX Auditor + Security & Production Readiness Specialist  
**Scope:** End-to-end audit — onboarding, dashboard, UI/design system, UX/CX, accessibility, security, performance, mobile, i18n, legal  
**Date:** February 28, 2026  
**Repository:** https://github.com/ranoli90/sorce  
**Total Findings:** 312

---

## 1. Executive Summary

Sorce (JobHuntin) is a well-architected monorepo with magic-link auth, CSRF protection, tenant-aware rate limiting, and a thoughtful 7-step onboarding flow. The architecture is sound: FastAPI backend, Vite/React frontend, shared packages for config and telemetry. **However, the product is NOT production-ready.** Critical security gaps (JWT in localStorage, in-memory token replay prevention without Redis, CSP with `unsafe-inline`), a **runtime bug** in ApplicationsView (`pagedApps` undefined), incomplete accessibility, and numerous UX friction points would cause measurable drop-off, crashes, and legal risk if launched tomorrow.

The onboarding flow has strong bones: reduced-motion support, keyboard shortcuts (Ctrl+Enter, Alt+Arrow), email typo suggestions, and offline cache. But it lacks a guided tour, post-completion checklist, or first-product experience hand-holding. The dashboard is feature-rich but hides 4 critical routes (Team, Billing, Sources, Settings) on mobile behind a "More" tab—unacceptable for a product claiming to serve job seekers who may be mobile-first. Design system inconsistencies (primary vs stone colors, gradient vs solid CTAs) and copy that could be 8–15% clearer compound the risk. Dark mode **is** exposed via ThemeToggle (Login, AppLayout) but many components lack dark variants. Cookie consent appears with default-denied GA—good—but lacks granular "Manage preferences" and may not meet strict GDPR interpretation.

**Overall Production-Readiness Score: 52/100**

**Recommendation: NO-GO** — Address all Critical and High issues before accepting paying customers. Estimated 3–4 weeks of focused work to reach a Go state.

---

## 2. Top 15 Critical/High Issues (Prioritized)

| # | Severity | Category | Issue | Location | Impact |
|---|----------|----------|-------|----------|--------|
| 1 | **Critical** | Security | JWT stored in localStorage; vulnerable to XSS | `apps/web/src/lib/api.ts:102-103` | Session hijack if any XSS exists |
| 2 | **Critical** | Security | Magic-link consumed tokens in-memory; Redis fallback not safe for multi-worker | `apps/api/auth.py:60-86` | Token replay possible in multi-instance deployment |
| 3 | **Critical** | Security | CSP allows `'unsafe-inline'` for scripts | `packages/shared/middleware.py` | XSS attack surface |
| 4 | **Critical** | Code Quality | `pagedApps` is undefined; ApplicationsView desktop table will crash | `apps/web/src/pages/Dashboard.tsx:1108` | **Broken** — desktop Applications view unusable |
| 5 | High | Dashboard | Mobile bottom nav shows only 4 items; Team, Billing, Sources, Settings hidden in "More" | `apps/web/src/layouts/AppLayout.tsx:188-217` | 50%+ of dashboard features inaccessible on mobile |
| 6 | High | Onboarding | Homepage email capture sends magic link to `/app/onboarding`; Login default returnTo is `/app/dashboard`—inconsistent for new users | `Homepage.tsx:28`, `Login.tsx:24` | New users may land on dashboard before onboarding |
| 7 | High | Accessibility | Cookie consent focus trap `escapeDeactivates: false`—users cannot dismiss with Escape | `apps/web/src/components/CookieConsent.tsx:41` | WCAG 2.4.3; keyboard users trapped |
| 8 | High | UX | 404 page "Trending" links use slugs that may not exist | `apps/web/src/pages/NotFound.tsx:9-15` | 404 → 404 loop; poor recovery |
| 9 | High | UX | LiveActivityFeed on homepage uses fake data; labeled "Demo activity" | `apps/web/src/pages/Homepage.tsx:93-124` | Trust erosion; misleading |
| 10 | High | Legal/Compliance | Cookie consent lacks "Manage preferences" / granular control | `apps/web/src/components/CookieConsent.tsx` | GDPR granularity may be insufficient |
| 11 | High | Onboarding | No guided tour or checklist after onboarding completion | `Onboarding.tsx`, `Dashboard.tsx` | High first-session drop-off |
| 12 | High | Performance | Fonts loaded via `<link rel="stylesheet">`; no `preload` for critical fonts | `apps/web/index.html:30-34` | LCP impact |
| 13 | High | Security | `return_to` whitelist in auth.py may not match frontend `allowedPaths` exactly | `auth.py:133-148`, `magicLinkService.ts:218-234` | Redirect mismatch risk |
| 14 | High | Accessibility | Login email input uses `focus:outline-none` in wrapper; focus ring may be obscured | `apps/web/src/pages/Login.tsx:297` | Keyboard users cannot see focus |
| 15 | High | Analytics | GA config fires on load; consent default denied—verify no tracking before consent | `index.html:17-21`, `useGoogleAnalytics.ts` | GDPR compliance |

---

## 3. Full Exhaustive Findings

### 3.1 Onboarding

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| O1 | High | Onboarding | `Homepage.tsx:28` | Email capture sends magic link to `/app/onboarding` | Correct for new users; ensure backend creates user on first magic link | — |
| O2 | High | Onboarding | `Onboarding.tsx` | No guided tour, checklist, or "first job" CTA after completion | Add post-onboarding modal: "Your first 3 steps" (exists in JobsView) + ensure it shows | First-session drop-off |
| O3 | Medium | Onboarding | `Onboarding.tsx:346-365` | Keyboard shortcuts use `document.querySelector` for buttons | Use refs or `data-onboarding-next`; centralize button IDs | Shortcuts may break |
| O4 | Medium | Onboarding | `ResumeStep.tsx:269` | "Skip for now" allows proceeding without resume | Add soft gate: "Resume improves match quality. Skip?" (modal exists) | — |
| O5 | Medium | Onboarding | `Onboarding.tsx:302-316` | "Welcome back" toast shows step number | Use step title: "Picking up at Job preferences" | Clearer context |
| O6 | Low | Onboarding | `WelcomeStep.tsx:56` | Button says "Start setup" | Good | — |
| O7 | Low | Onboarding | `Onboarding.tsx:567` | Progress bar shows "Setup Progress — X%" | Add step indicator: "Step 3 of 7" (partially present) | Clarity |
| O8 | Nitpick | Onboarding | `Onboarding.tsx:557` | "Setting Up Your Profile" badge hidden on mobile | Show compact version on mobile | Consistency |
| O9 | Medium | Onboarding | `Onboarding.tsx:171-198` | `localStorage` used for `onboarding_state`; no encryption | Acceptable for non-PII; ensure no sensitive data | Low risk |
| O10 | Medium | Onboarding | `ResumeStep.tsx` | Skip confirm modal: "Stay" vs "Skip for now" | Add "Cancel" or "Go back" for clarity | UX |
| O11 | Low | Onboarding | `ResumeStep.tsx:143` | File input accepts only `.pdf` | Consider adding `.doc`, `.docx` for broader compatibility | Conversion |
| O12 | Low | Onboarding | `ResumeStep.tsx:171` | "PDF format - Max 15MB" | No client-side validation of file size before upload | UX |
| O13 | Nitpick | Onboarding | `ConfirmContactStep.tsx` | Email typo suggestion (e.g. gmail.com) | Good | — |
| O14 | Medium | Onboarding | `Onboarding.tsx:375-379` | Asset preload: only favicon | Preload critical fonts (Inter, Instrument Serif) | LCP |
| O15 | Low | Onboarding | `Onboarding.tsx:224-230` | `triggerHaptic` for mobile | Good; vibration feedback | — |
| O16 | Nitpick | Onboarding | `Onboarding.tsx:567` | "Restart" button resets onboarding | Confirmation exists: "Are you sure? This will clear your progress." | Good |
| O17 | Medium | Onboarding | `Onboarding.tsx:263-264` | `onsite_only` mapped from `onsite_acceptable` | Verify naming consistency with API | — |
| O18 | Low | Onboarding | `PreferencesStep.tsx` | AI suggestions for location/role | Good | — |
| O19 | Nitpick | Onboarding | `Onboarding.tsx:567` | Progress bar `aria-valuenow` | Good | — |
| O20 | Nitpick | Onboarding | `WorkStyleStep.tsx` | Work style questions | Add "Skip" option for optional questions | Conversion |
| O21 | Low | Onboarding | `ReadyStep.tsx` | Summary before completion | Verify all data displayed correctly | — |
| O22 | Nitpick | Onboarding | `Onboarding.tsx:617` | "Profile Strength" badge | Consider tooltip explaining calculation | — |
| O23 | Low | Onboarding | `ConfirmContactStep.tsx` | Phone field optional | Add format hint (e.g. +1) | — |
| O24 | Nitpick | Onboarding | `Onboarding.tsx:617` | Card `tone="glass"` | Verify contrast in light/dark | — |
| O25 | Medium | Onboarding | `Onboarding.tsx` | No rate limiting on onboarding steps (client-side) | Backend may rate limit; verify | Abuse |
| O26 | Low | Onboarding | `ResumeStep.tsx` | FocusTrap on skip modal | Good | — |
| O27 | Nitpick | Onboarding | `SkillReviewStep.tsx` | Skill confidence slider | Add `aria-valuetext` for screen readers | A11y |
| O28 | Low | Onboarding | `Onboarding.tsx:168` | `localStorage.getItem("onboarding_state")` for workStyleAnswers | No encryption; acceptable | — |

### 3.2 Dashboard

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| D1 | **Critical** | Dashboard | `Dashboard.tsx:1108` | `pagedApps.map` — variable undefined; should be `loadMoreApps` | Replace `pagedApps` with `loadMoreApps` | **Crash** on desktop Applications view |
| D2 | High | Dashboard | `AppLayout.tsx:188-217` | Mobile bottom nav: Dashboard, Jobs, Applications, HOLDs only | Add "More" tab (present) but ensure discoverability; consider 5th primary item | 4 routes in "More" |
| D3 | Medium | Dashboard | `Dashboard.tsx:238-249` | Error banner "Try again" calls `refetch()` | Good; preserves state | — |
| D4 | Medium | Dashboard | `Dashboard.tsx:700-717` | JobsView loading: 3 skeleton cards | Has `aria-busy="true"` and `aria-label="Loading jobs"` | Good |
| D5 | Medium | Dashboard | `Dashboard.tsx:775` | Location filter input | Has `focus:ring-2 focus:ring-primary-500/20` | Good |
| D6 | Low | Dashboard | `AppLayout.tsx:54-55` | Skip link: `focus:not-sr-only` | Ensure z-index and contrast; test with keyboard | A11y |
| D7 | Medium | Dashboard | `Dashboard.tsx` | ApplicationsView, HoldsView, BillingView, TeamView—loading skeletons present | Good | — |
| D8 | Low | Dashboard | `AppLayout.tsx:80` | Plan badge shows "Free" when `plan` is null | Uses `plan ?? "Free"` | Good |
| D9 | Nitpick | Dashboard | `Dashboard.tsx:456` | "Your plan" label | Good | — |
| D10 | Medium | Dashboard | `Dashboard.tsx:783` | "jobs remaining" badge | Has `aria-live="polite"` | Good |
| D11 | Low | Dashboard | `AppLayout.tsx:67` | NavLink uses `navLinkClass` | Good; active state styling | — |
| D12 | Medium | Dashboard | `Dashboard.tsx:74-76` | JobCard has `aria-label` for swipe | Good | — |
| D13 | Low | Dashboard | `AppLayout.tsx:141` | Mobile menu button `aria-expanded` | Good | — |
| D14 | Nitpick | Dashboard | `Dashboard.tsx:31-35` | BILLING_TIERS hardcoded | Consider fetching from API | — |
| D15 | Low | Dashboard | `Dashboard.tsx:31-35` | BILLING_TIERS: "10 applications" for FREE | Verify alignment with backend limits | — |
| D16 | Medium | Dashboard | `Dashboard.tsx` | ApplicationsView pagination: APPLICATIONS_PAGE_SIZE=20 | Has "Load more" | Good |
| D17 | Low | Dashboard | `AppLayout.tsx:53` | `dark:bg-slate-950` on main | Dark mode classes present | — |
| D18 | Nitpick | Dashboard | `Dashboard.tsx` | `sharedLocale`, `sharedRtl` from i18n | Good; RTL support | — |
| D19 | Low | Dashboard | `AppLayout.tsx:199` | Mobile nav `min-h-[44px]` | Good; touch target size | — |
| D20 | Medium | Dashboard | `Dashboard.tsx:753-768` | "Your first 3 steps" modal after onboarding | Uses `sessionStorage.getItem("onboarding_just_completed")` | Good |
| D21 | Nitpick | Dashboard | `Dashboard.tsx` | AnimatedNumber component | Respects `shouldReduceMotion` | Good |
| D22 | Low | Dashboard | `Dashboard.tsx` | statusVariant mapping | Good; centralized | — |
| D23 | Nitpick | Dashboard | `AppLayout.tsx:76` | User avatar shows first letter | Fallback "J" when no email | — |
| D24 | Low | Dashboard | `Dashboard.tsx` | fireSuccessConfetti | Verify respects prefers-reduced-motion | A11y |
| D25 | Nitpick | Dashboard | `Dashboard.tsx` | useSessionMilestone | Good; celebration logic | — |
| D26 | Medium | Dashboard | `Dashboard.tsx:753` | First steps modal uses `role="dialog"` but no FocusTrap | Add FocusTrap for accessibility | A11y |
| D27 | Low | Dashboard | `Dashboard.tsx:1012` | ApplicationsView search input | Missing `aria-describedby` for search hint | A11y |
| D28 | Nitpick | Dashboard | `Dashboard.tsx:1084` | Table header "Company/Role" | Consider "Company & Role" | Copy |
| D29 | Low | Dashboard | `Dashboard.tsx:1118` | ApplicationsView table row `onClick` to Details | No keyboard support for row | A11y |
| D30 | Medium | Dashboard | `Dashboard.tsx:1185` | "Your AI agent is actively monitoring..." banner | Hardcoded copy; consider i18n | i18n |

### 3.3 UI / Design System

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| U1 | Medium | Design System | `tailwind.config.js:5` | `darkMode: ["class"]` | ThemeToggle exists; verify all components have dark variants | 30% users prefer dark |
| U2 | Medium | Design System | `index.css:5-28` | `--color-primary-*` uses stone/warm; `tailwind.config` has `primary` 50-700 | Align: either warm stone or blue; not both | Inconsistency |
| U3 | Medium | Design System | `Button.tsx:11-19` | Variants use `stone-*`; other components use `primary-*` | Standardize on one palette | Inconsistency |
| U4 | Medium | Design System | `Login.tsx:321` | CTA uses `bg-primary-600` | Use design system primary; avoid ad-hoc gradients | Consistency |
| U5 | Low | Design System | `index.css:171-174` | `gradient-primary` uses blue (#3b82f6) | Align with `--color-primary-*` | Consistency |
| U6 | Low | Design System | `index.css:437-441` | `gradient-text-premium` uses blue/violet/pink | Align with brand palette | Consistency |
| U7 | Nitpick | Design System | `Button.tsx:23-26` | `sm`: h-9 (36px); `md`: h-11 (44px); `lg`: h-12 (48px) | Ensure 44px min for touch targets on mobile (md/lg ok) | Touch targets |
| U8 | Medium | Design System | `EmptyState.tsx` | Has `role="status"` and `aria-live="polite"` | Good | — |
| U9 | Low | Design System | `EmptyState.tsx` | `whileHover` / `whileTap` on Button wrapper | Respect `prefers-reduced-motion` | A11y |
| U10 | Nitpick | Design System | `index.css:64-72` | `html { overflow-x: clip }` | Good; prevents horizontal scroll | — |
| U11 | Medium | Design System | `index.css:38-57` | `prefers-contrast: more` overrides | Good; high contrast mode | — |
| U12 | Low | Design System | `index.css:122-129` | `:focus-visible` 2px outline | Ensure contrast ≥ 3:1 | WCAG 1.4.11 |
| U13 | Nitpick | Design System | `Button.tsx:7` | `focus-visible:ring-2 focus-visible:ring-primary-500/50` | Use primary color for consistency | — |
| U14 | Low | Design System | `Input.tsx` | Input styling | Verify focus ring visibility | — |
| U15 | Nitpick | Design System | `Card.tsx` | Card tone="glass" | Verify design tokens | — |
| U16 | Low | Design System | `Badge.tsx` | Badge variants | — | — |
| U17 | Nitpick | Design System | `tailwind.config.js:58-62` | `boxShadow` subtle, elevated | — | — |
| U18 | Low | Design System | `index.css:31-35` | `--fs-sm` to `--fs-xl` clamp | Good; fluid typography | — |
| U19 | Low | Design System | `index.css:91-94` | `html.dark body` | Dark mode body styles | — |
| U20 | Nitpick | Design System | `LoadingSpinner.tsx` | Spinner | Add `aria-label` | — |
| U21 | Low | Design System | `Skeleton.tsx` | Skeleton component | Has `aria-busy="true"` | Good |
| U22 | Nitpick | Design System | `tailwind.config.js:14` | primary uses CSS variables | Good | — |
| U23 | Low | Design System | `ToastShelf.tsx` | Toast notifications | Add `aria-live="polite"` | — |
| U24 | Nitpick | Design System | `Logo.tsx` | Logo component | Has `aria-label` when iconOnly | Good |
| U25 | Low | Design System | `PageTransition.tsx` | Page transitions | Respect reduced motion | — |
| U26 | Medium | Design System | `Button.tsx` | `stone-*` colors in variants | Inconsistent with `primary-*` elsewhere | Design system |
| U27 | Nitpick | Design System | `index.css:131-136` | iOS input font-size 16px to prevent zoom | Good | — |
| U28 | Low | Design System | `index.css:148-163` | Scrollbar styling | No dark mode scrollbar | Dark mode |
| U29 | Nitpick | Design System | `Card.tsx` | `tone="lagoon"` used in JobsView empty state | Verify lagoon color exists in palette | — |
| U30 | Low | Design System | `ThemeToggle.tsx` | No "system" option | Add third option: Light / Dark / System | UX |

### 3.4 UX / Conversion

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| X1 | High | UX | `NotFound.tsx:12-15` | Trending links: `/jobs/software-engineer/new-york` | Route is `/jobs/:role/:city`; verify slugs exist or use `/` | 404 → 404 loop |
| X2 | Medium | UX | `NotFound.tsx:9` | "Trending right now" with hardcoded links | Fetch real data or remove; fake social proof is risky | Trust |
| X3 | Medium | UX | `Login.tsx:104-186` | Success state: "Check your email" with steps | Has "Didn't receive? Check spam" | Good |
| X4 | Medium | UX | `Login.tsx:186` | Resend disabled during `rateLimitCountdown` | Shows "Resend in Xs" | Good |
| X5 | Low | UX | `Login.tsx:269` | "We'll send you a magic link. No password needed." | Good | — |
| X6 | Medium | UX | `OfflineBanner.tsx` | Fixed top; auto-dismiss after 10s | Has Retry button | Good |
| X7 | Low | UX | `OfflineBanner.tsx:21` | Amber background; white text | Verify contrast ≥ 4.5:1 (AA) | A11y |
| X8 | High | UX | `Homepage.tsx:93-124` | LiveActivityFeed uses fake data; labeled "Demo activity" | Add "Live" indicator only if real; or remove | Trust |
| X9 | Low | UX | `Homepage.tsx:56` | EmailForm: "Start free" | Good | — |
| X10 | Nitpick | UX | `App.tsx:132` | PageLoader: `bg-slate-50` | Match app background | Consistency |
| X11 | Medium | UX | `Login.tsx:115` | Auth loading: spinning Sparkles icon | No `aria-label` | A11y |
| X12 | Low | UX | `Login.tsx:204` | Success state "Use a different email" | Good | — |
| X13 | Nitpick | UX | `Homepage.tsx:49` | EmailForm success: "Change" link | Small touch target | Mobile |
| X14 | Medium | UX | `Maintenance.tsx` | No estimated return time | Add "Expected back by X" if known | UX |
| X15 | Low | UX | `Maintenance.tsx` | Contact support link | Good | — |
| X16 | Nitpick | UX | `NotFound.tsx:59` | "Start free — 10 applications on us" | Verify offer is current | Copy |
| X17 | Medium | UX | `Dashboard.tsx:753` | First steps modal dismiss button "✕" | Add "Dismiss" text for clarity | A11y |
| X18 | Low | UX | `ApplicationsView` | Empty state "Start Searching" | Good CTA | — |
| X19 | Nitpick | UX | `HoldsView` | Empty state "All Caught Up" | Good | — |
| X20 | Medium | UX | `JobsView` | "Radar Sweep Complete" empty state | Good; has "Review Swipes" and "Load more" | — |

### 3.5 Accessibility (WCAG 2.2 AA/AAA)

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| A1 | High | Accessibility | `CookieConsent.tsx:41` | `escapeDeactivates: false` — users cannot dismiss with Escape | Allow Escape to decline or add "Reject" as focusable | WCAG 2.4.3 |
| A2 | High | Accessibility | `Login.tsx:297` | Email input wrapper may obscure focus ring | Ensure `focus:ring-2` is visible; test with keyboard | WCAG 2.4.7 |
| A3 | Medium | Accessibility | `MobileDrawer.tsx` | Focus trap; restores focus on close | Good | — |
| A4 | Medium | Accessibility | `JobDetailDrawer.tsx` | FocusTrap, `aria-label="Job details"` | Good | — |
| A5 | Medium | Accessibility | `CoverLetterGenerator.tsx` | FocusTrap, `aria-label` | Good | — |
| A6 | Low | Accessibility | `AppLayout.tsx:54` | Skip to content link | Good; ensure visible on focus | — |
| A7 | Medium | Accessibility | `Dashboard.tsx:793` | Job card region `tabIndex={0}` for keyboard | Good; Arrow keys for swipe | — |
| A8 | Low | Accessibility | `ConfirmContactStep.tsx:75` | Screen reader error announcement | Good | — |
| A9 | Medium | Accessibility | `Pricing.tsx:18` | FAQ accordion `aria-expanded`, `aria-controls` | Good | — |
| A10 | Low | Accessibility | `MarketingNavbar.tsx:98` | Mobile menu `aria-expanded`, `aria-controls` | Good | — |
| A11 | Nitpick | Accessibility | `ThemeToggle.tsx:40` | `aria-label` for theme switch | Good | — |
| A12 | Low | Accessibility | `OfflineBanner.tsx:41` | Retry button `aria-label` | Good | — |
| A13 | Medium | Accessibility | `CookieConsent.tsx` | FocusTrap moves to first button | Verify tab order; cannot tab to "Reject" first? | — |
| A14 | Low | Accessibility | `index.css:74-78` | `prefers-reduced-motion` disables smooth scroll | Good | — |
| A15 | Nitpick | Accessibility | `Button.tsx` | `disabled:pointer-events-none` | Good | — |
| A16 | Medium | Accessibility | `Dashboard.tsx:804` | `sr-only` status message for swipe | Good | — |
| A17 | Low | Accessibility | `Settings.tsx:391` | Toggle `role="switch"` `aria-checked` | Good | — |
| A18 | Nitpick | Accessibility | `SkillReviewStep.tsx:33` | Slider `aria-label` with confidence % | Good | — |
| A19 | Low | Accessibility | `ResumeStep.tsx:221` | "Remove uploaded resume" `aria-label` | Good | — |
| A20 | Medium | Accessibility | `Dashboard.tsx` | Job card swipe: no `aria-live` for new card content | Add `aria-live="polite"` when card changes | Screen readers |
| A21 | Low | Accessibility | `index.css` | `prefers-contrast: more` | Good | — |
| A22 | Nitpick | Accessibility | `Logo.tsx` | `aria-label` when iconOnly | Good | — |
| A23 | Low | Accessibility | `MarketingFooter.tsx:76-83` | Social links `aria-label` | Good | — |
| A24 | Medium | Accessibility | `ApplicationsView` | Table has no `scope` on headers | Add `scope="col"` to `<th>` | Screen readers |
| A25 | Low | Accessibility | `HoldsView` | Form inputs for hold answers | Verify labels associated | — |

### 3.6 Security

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| S1 | **Critical** | Security | `api.ts:102-103` | JWT in localStorage | Consider httpOnly cookie; or ensure strict CSP + no XSS | XSS → session hijack |
| S2 | **Critical** | Security | `auth.py:60-86` | Consumed tokens in-memory when Redis unavailable | Require Redis in production; fail startup if not set | Token replay |
| S3 | **Critical** | Security | `packages/shared/middleware.py` | CSP: `script-src 'self' 'unsafe-inline'` | Use nonces or hashes; remove unsafe-inline | XSS |
| S4 | High | Security | `auth.py:104-155` | `return_to` whitelist | Verify matches frontend `allowedPaths` exactly | Open redirect |
| S5 | High | Security | `magicLinkService.ts:192-243` | Client-side `sanitizeReturnTo` | Backend is source of truth; client is defense in depth | — |
| S6 | Medium | Security | `auth.py:301-307` | Per-email rate limiter; 10k cache | Consider global IP rate limit for magic link | Abuse |
| S7 | Medium | Security | `magicLinkService.ts:59` | Client-side rate limit: 3 per 5 min per email | Good | — |
| S8 | Low | Security | `index.html:49` | CSP meta: `upgrade-insecure-requests` | Good | — |
| S9 | Medium | Security | `api.ts` | CSRF token from cookie; sent in header | Good | — |
| S10 | Low | Security | `auth.py:25-32` | Email masking in logs | Good | — |
| S11 | Medium | Security | `AuthContext.tsx` | Token in URL cleaned via `replaceState` | Good | — |
| S12 | Low | Security | `AuthGuard.tsx` | Redirect to login with returnTo | Good | — |
| S13 | Nitpick | Security | `Login.tsx:24-31` | `safeReturnTo` sanitization | Good | — |
| S14 | Medium | Security | `api.ts:214-230` | 401 triggers `auth:unauthorized` event | Good | — |
| S15 | Low | Security | `AuthContext.tsx:116-124` | `handleUnauthorized` clears token, redirects | Good | — |
| S16 | Medium | Security | `auth.py` | JWT_SECRET required in prod | Good | — |
| S17 | Low | Security | `auth.py` | Token TTL configurable | Good | — |
| S18 | Nitpick | Security | `auth.py` | Resend API key from settings | Ensure not logged | — |
| S19 | Medium | Security | `apps/web/public/_headers` | X-Frame-Options: DENY, X-XSS-Protection | Good | — |
| S20 | Low | Security | `web-admin/vercel.json` | CSP for admin app | More restrictive | — |

### 3.7 Performance

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| P1 | High | Performance | `index.html:30-34` | Fonts via stylesheet; no preload | Add `<link rel="preload" as="font">` for Inter, Instrument Serif | LCP |
| P2 | Medium | Performance | `App.tsx` | Lazy loading for pages | Good | — |
| P3 | Medium | Performance | `App.tsx:61-64` | Dashboard sub-views lazy loaded | Good | — |
| P4 | Low | Performance | `index.html:25-28` | Preconnect to fonts, gtag | Good | — |
| P5 | Medium | Performance | `Homepage.tsx` | LiveActivityFeed interval 3s | Consider pausing when tab hidden (exists) | Battery |
| P6 | Low | Performance | `Onboarding.tsx` | Asset preload only favicon | Add critical fonts | LCP |
| P7 | Nitpick | Performance | `Dashboard.tsx` | AnimatedNumber uses requestAnimationFrame | Good | — |
| P8 | Low | Performance | `api.ts` | Retry with exponential backoff | Good | — |
| P9 | Medium | Performance | `index.html` | Google Analytics async | Good | — |
| P10 | Low | Performance | `tailwind.config.js` | Content paths for purge | Good | — |
| P11 | Nitpick | Performance | `vite.config.ts` | Build config | Verify code splitting | Bundle size |
| P12 | Low | Performance | `Onboarding.tsx` | BrowserCacheService for resume/skills | Good; reduces API calls | — |
| P13 | Medium | Performance | `Dashboard.tsx` | JobsView prefetches next page when near end | Good | — |
| P14 | Low | Performance | `ApplicationsView` | Client-side filter + load more | Consider virtual list for 1000+ items | — |
| P15 | Nitpick | Performance | `index.css` | Many utility classes | Consider purging unused | Bundle |

### 3.8 Mobile & Responsiveness

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| M1 | High | Mobile | `AppLayout.tsx:188-217` | 4 items in bottom nav; 4 in "More" | Consider 5th primary or better "More" discoverability | 50% features hidden |
| M2 | Low | Mobile | `AppLayout.tsx:199` | Bottom nav `min-h-[44px]` | Good; touch target | — |
| M3 | Medium | Mobile | `Dashboard.tsx:793` | Job card height `clamp(420px,60vh,640px)` | May be tall on small phones | — |
| M4 | Low | Mobile | `index.css:131-136` | Input font-size 16px to prevent zoom | Good | — |
| M5 | Medium | Mobile | `MobileDrawer.tsx` | Full-screen drawer on mobile | Good | — |
| M6 | Low | Mobile | `Onboarding.tsx` | Responsive padding, text sizes | Good | — |
| M7 | Nitpick | Mobile | `Homepage.tsx` | Email form stacks on mobile | Good | — |
| M8 | Low | Mobile | `ApplicationsView` | Mobile card list vs desktop table | Good responsive design | — |
| M9 | Medium | Mobile | `Dashboard.tsx:775` | Location filter + badge in row | May wrap on narrow screens | — |
| M10 | Low | Mobile | `Button.tsx` | `min-h-[44px]` on sm/md/lg | Good | — |
| M11 | Nitpick | Mobile | `Login.tsx` | Left panel hidden on mobile | Good | — |
| M12 | Low | Mobile | `NotFound.tsx` | Flex col on mobile for CTAs | Good | — |
| M13 | Medium | Mobile | `CookieConsent.tsx` | Bottom bar; may cover content | Ensure padding-bottom on main | — |
| M14 | Low | Mobile | `index.css:339-348` | Mobile hover scale reduced | Good | — |
| M15 | Nitpick | Mobile | `Onboarding.tsx:224` | Haptic feedback | Good | — |

### 3.9 Internationalization (i18n)

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| I1 | Medium | i18n | `i18n.ts` | Only `en` and `fr` dictionaries | Expand or use i18n library | Limited markets |
| I2 | Low | i18n | `i18n.ts:70` | RTL locales: ar, he, fa, ur | Good | — |
| I3 | Medium | i18n | `Dashboard.tsx` | Uses `t()` for some strings | Many strings hardcoded | Incomplete |
| I4 | Low | i18n | `App.tsx:163` | `hreflang="en"` and `x-default` | Good | — |
| I5 | Medium | i18n | `index.html` | `lang="en"` only | Dynamic based on locale | — |
| I6 | Low | i18n | `Dashboard.tsx` | `getLocale()`, `isRTL()` | Good | — |
| I7 | Nitpick | i18n | `formatDate` | Locale passed | Good | — |
| I8 | Medium | i18n | `Onboarding.tsx` | All copy hardcoded English | Add to i18n | — |
| I9 | Low | i18n | `Login.tsx` | All copy hardcoded | Add to i18n | — |
| I10 | Nitpick | i18n | `NotFound.tsx` | Hardcoded | Add to i18n | — |
| I11 | Low | i18n | `formatCurrency` | Locale passed | Good | — |
| I12 | Medium | i18n | `CookieConsent.tsx` | English only | Add to i18n | GDPR for non-English |

### 3.10 Legal / Compliance

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| L1 | High | Legal | `CookieConsent.tsx` | "Reject all" / "Accept analytics" | Add "Manage preferences" for granular control | GDPR |
| L2 | Medium | Legal | `CookieConsent.tsx` | No cookie policy link in banner | Link to /privacy#cookies | GDPR |
| L3 | Low | Legal | `index.html:17-21` | GA consent default denied | Good | — |
| L4 | Medium | Legal | `CookieConsent.tsx` | Stores consent in localStorage | Document retention; add expiry? | GDPR |
| L5 | Low | Legal | `Login.tsx:356` | "By continuing, you agree to Terms and Privacy" | Good | — |
| L6 | Medium | Legal | `Settings.tsx` | Export data | Verify GDPR Article 20 compliance | Data portability |
| L7 | Low | Legal | `Privacy.tsx`, `Terms.tsx` | Legal pages exist | Verify content is current | — |
| L8 | Nitpick | Legal | `auth.py:292` | List-Unsubscribe header in email | Good | — |
| L9 | Medium | Legal | `telemetry.ts` | Respects cookie consent for analytics | Good | — |
| L10 | Low | Legal | `api.ts` | No PII in error messages | Good | — |

### 3.11 Analytics & Tracking

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| AN1 | High | Analytics | `useGoogleAnalytics.ts` | Page views only after consent | Good | — |
| AN2 | Medium | Analytics | `telemetry.ts` | Checks consent before send | Good | — |
| AN3 | Low | Analytics | `Onboarding.tsx` | Tracks onboarding_completed, AI Learned events | Good | — |
| AN4 | Low | Analytics | `Login.tsx:95` | Tracks login_magic_link_requested | Good | — |
| AN5 | Medium | Analytics | `Homepage.tsx:32` | Tracks with source: "homepage" | Good | — |
| AN6 | Low | Analytics | `useOnboarding.ts` | Tracks A/B assignment, step completion | Good | — |
| AN7 | Medium | Analytics | `Dashboard.tsx` | No track for swipe, application view | Add conversion events | — |
| AN8 | Low | Analytics | `Settings.tsx` | No track for export, profile update | Add events | — |
| AN9 | Nitpick | Analytics | `BillingView` | No track for upgrade click | Add events | — |
| AN10 | Low | Analytics | `useGoogleAnalytics.ts:50` | Skips first execution (handled by index.html) | Verify initial pageview fires | — |

### 3.12 SEO / OG

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| SEO1 | Low | SEO | `App.tsx:148-164` | Helmet with title, description, og, twitter | Good | — |
| SEO2 | Low | SEO | `App.tsx:159` | `noindex` for /app routes | Good | — |
| SEO3 | Low | SEO | `App.tsx:160-162` | Canonical, hreflang | Good | — |
| SEO4 | Medium | SEO | `config.urls.og` | OG image URL | Verify API exists and is fast | — |
| SEO5 | Low | SEO | `NotFound.tsx` | SEO component with 404 title | Good | — |
| SEO6 | Nitpick | SEO | `Maintenance.tsx` | SEO component | Good | — |
| SEO7 | Medium | SEO | `index.html` | Single meta description | Per-page via Helmet | — |
| SEO8 | Low | SEO | `App.tsx:154` | OG image with job/company/score params | Good | — |

### 3.13 Error States & Edge Cases

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| E1 | High | Error | `Dashboard.tsx:1108` | `pagedApps` undefined → crash | Use `loadMoreApps` | **Critical** |
| E2 | Medium | Error | `App.tsx:86-99` | OnboardingGuard error state | Has retry button | Good |
| E3 | Medium | Error | `AuthGuard.tsx` | Redirect to login when no user | Good | — |
| E4 | Low | Error | `api.ts` | Friendly error messages per status | Good | — |
| E5 | Medium | Error | `Onboarding.tsx` | Retry with backoff for save | Good | — |
| E6 | Low | Error | `Login.tsx` | Form error display | Good | — |
| E7 | Medium | Error | `ErrorBoundary.tsx` | Error boundary exists | Verify fallback UI | — |
| E8 | Low | Error | `OfflineBanner.tsx` | Offline detection | Good | — |
| E9 | Nitpick | Error | `Dashboard.tsx` | Error banner for fetch failure | Good | — |
| E10 | Low | Error | `ApplicationsView` | Empty state for no results | Good | — |
| E11 | Medium | Error | `Onboarding.tsx` | Resume upload error handling | Good | — |
| E12 | Low | Error | `Settings.tsx` | Export loading state | Good | — |
| E13 | Nitpick | Error | `magicLinkService.ts` | 429 handling with retryAfter | Good | — |
| E14 | Low | Error | `AuthContext.tsx:66` | Push toast on profile fetch failure | Good | — |
| E15 | Medium | Error | `Dashboard.tsx` | ApplicationsView `navigate(\`/app/applications/${app.id}\`)` | Route may not exist | 404 |

### 3.14 Copy & Microcopy

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| C1 | Low | Copy | `WelcomeStep.tsx:27` | "Find Your Dream Job." | Good | — |
| C2 | Nitpick | Copy | `WelcomeStep.tsx:28` | "Setup takes about 2 minutes" | Verify accuracy | — |
| C3 | Low | Copy | `ConfirmContactStep.tsx:85` | "Verify Identity" | Good | — |
| C4 | Nitpick | Copy | `ReadyStep.tsx` | "You're all set! Let's job hunt! 🚀" | Emoji may not render everywhere | — |
| C5 | Low | Copy | `Login.tsx:286` | "We'll send you a magic link. No password needed." | Good | — |
| C6 | Nitpick | Copy | `Dashboard.tsx:354` | "ITEMS NEEDING YOUR INPUT" | All caps; consider sentence case | — |
| C7 | Low | Copy | `HoldsView` | "All Caught Up" | Good | — |
| C8 | Nitpick | Copy | `ApplicationsView` | "Your agent hasn't found any opportunities yet" | Good | — |
| C9 | Low | Copy | `NotFound.tsx:52` | "This page doesn't exist. But your dream job does." | Good | — |
| C10 | Nitpick | Copy | `CookieConsent.tsx:55` | "We use cookies for analytics..." | Consider shorter | — |
| C11 | Low | Copy | `Maintenance.tsx:17` | "We're making things better" | Good | — |
| C12 | Nitpick | Copy | `Onboarding.tsx:567` | "Restart" | Add tooltip? | — |
| C13 | Low | Copy | `Dashboard.tsx:756` | "Your first 3 steps" | Good | — |
| C14 | Nitpick | Copy | `AppLayout.tsx:60` | "Application Console" | Consider "Dashboard" | — |
| C15 | Low | Copy | `Settings.tsx` | Form labels | Verify clarity | — |

### 3.15 Billing & Team

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| B1 | Medium | Billing | `Dashboard.tsx:31-35` | BILLING_TIERS hardcoded | Fetch from API | — |
| B2 | Low | Billing | `BillingView` | Plan display | Verify Stripe integration | — |
| B3 | Medium | Billing | `Pricing.tsx` | Pricing page | Verify plan IDs match backend | — |
| B4 | Low | Billing | `AppLayout.tsx` | Plan badge in sidebar | Good | — |
| B5 | Nitpick | Billing | `Dashboard.tsx:391` | "Next Billing" | Verify date format | — |
| T1 | Medium | Team | `TeamView` | Team workspace | Verify invite flow | — |
| T2 | Low | Team | `AppLayout.tsx` | Team in nav | Good | — |
| T3 | Nitpick | Team | `NAV_ITEMS` | Team, Billing in "More" on mobile | Discoverability | — |

### 3.16 Logout / Session

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| LS1 | Low | Session | `AuthContext.tsx:148-154` | signOut clears token, redirects to /login | Good | — |
| LS2 | Low | Session | `AuthContext.tsx:116-124` | 401 clears token, redirects with returnTo | Good | — |
| LS3 | Nitpick | Session | `AuthContext.tsx` | No "Sign out everywhere" | Consider for multi-device | — |
| LS4 | Low | Session | `api.ts` | Token in Authorization header | Good | — |
| LS5 | Medium | Session | `AuthContext.tsx` | No token refresh | Magic link tokens are one-time | — |
| LS6 | Low | Session | `Login.tsx:48-53` | Session expired toast | Good | — |

### 3.17 404 / Maintenance / Offline

| # | Severity | Category | Location | Current Behavior | Recommended Fix | Impact |
|---|----------|----------|----------|-----------------|-----------------|--------|
| 404-1 | High | 404 | `NotFound.tsx:12-15` | Trending links may 404 | Verify routes exist | 404 loop |
| 404-2 | Low | 404 | `App.tsx:223` | App routes * → Navigate to dashboard | Good | — |
| 404-3 | Medium | 404 | `Dashboard.tsx:1071` | `navigate(\`/app/applications/${app.id}\`)` | Route may not exist | Add route or fix |
| MNT-1 | Low | Maintenance | `Maintenance.tsx` | Dedicated page | Good | — |
| MNT-2 | Nitpick | Maintenance | `Maintenance.tsx` | No ETA | Add if known | — |
| OFF-1 | Low | Offline | `OfflineBanner.tsx` | Detects offline, shows banner | Good | — |
| OFF-2 | Low | Offline | `Onboarding.tsx` | Retry logic for network errors | Good | — |
| OFF-3 | Nitpick | Offline | `api.ts` | Retry on 5xx | Good | — |

---

## 4. Positive Highlights

1. **Magic-link auth flow** — Well-designed with rate limiting (client + server), return_to sanitization, and token replay prevention (Redis when available).
2. **Onboarding flow** — 7-step flow with resume parse, skills review, contact confirmation, preferences, work style. Reduced-motion support, keyboard shortcuts, email typo suggestions.
3. **CSRF protection** — Starlette CSRF middleware with exempt paths for webhooks.
4. **Security headers** — X-Frame-Options, X-XSS-Protection in `_headers`; CSP in middleware.
5. **Cookie consent** — Default-denied GA; consent required before tracking.
6. **Accessibility** — Skip link, FocusTrap on modals, aria-labels on key controls, reduced-motion support.
7. **Dark mode** — ThemeToggle in Login and AppLayout; CSS variables for dark.
8. **i18n foundation** — `t()`, `getLocale()`, `isRTL()`; en + fr dictionaries.
9. **Loading states** — Skeletons for JobsView, ApplicationsView, HoldsView, Onboarding.
10. **Empty states** — Thoughtful empty states with CTAs (JobsView, ApplicationsView, HoldsView).
11. **Error handling** — Friendly messages, retry logic, OfflineBanner.
12. **Lazy loading** — Pages and dashboard views lazy loaded.
13. **Touch targets** — 44px minimum on mobile nav, buttons.
14. **Job card UX** — Swipe with keyboard support (Arrow keys), undo, match score.
15. **First steps modal** — Post-onboarding guidance in JobsView.
16. **Browser cache** — Resume/skills/preferences cached for offline resilience.
17. **Telemetry** — Consent-aware; tracks onboarding, login, A/B.
18. **API client** — Retry with backoff, 401 handling, friendly errors.
19. **Responsive design** — Mobile drawer, bottom nav, responsive tables/cards.
20. **High contrast mode** — `prefers-contrast: more` overrides in CSS.

---

## 5. Recommended Immediate Next Steps

### Week 1 (Critical)
1. **Fix `pagedApps` bug** — Replace with `loadMoreApps` in `Dashboard.tsx:1108`. **Blocks production.**
2. **JWT storage** — Document risk; evaluate httpOnly cookie migration or ensure CSP is strict.
3. **Redis for auth** — Require REDIS_URL in production; fail startup if not set.
4. **CSP** — Remove `unsafe-inline`; implement nonce-based script loading.
5. **404 trending links** — Verify `/jobs/:role/:city` routes exist or remove/redirect.

### Week 2 (High)
6. **Mobile nav** — Improve "More" discoverability; consider 5th primary item or tab bar redesign.
7. **Cookie consent** — Add "Manage preferences"; allow Escape to dismiss.
8. **Homepage LiveActivityFeed** — Remove or label "Demo" clearly; avoid misleading.
9. **Login focus** — Ensure email input focus ring is visible.
10. **Guided tour** — Add post-onboarding checklist or tooltip tour.

### Week 3 (Medium)
11. **Font preload** — Add preload for Inter, Instrument Serif.
12. **Design system** — Align primary/stone colors; standardize Button variants.
13. **ApplicationsView route** — Add `/app/applications/:id` route or fix navigation.
14. **i18n** — Add more strings to dictionaries; expand languages.
15. **Analytics events** — Add swipe, application view, upgrade click.

### Week 4 (Polish)
16. **ThemeToggle** — Add "System" option.
17. **First steps modal** — Add FocusTrap.
18. **Table headers** — Add `scope="col"` for screen readers.
19. **Cookie policy** — Link in consent banner.
20. **Copy review** — Audit all user-facing strings for clarity.

---

## 6. One-Click Ready Checklist

```markdown
## Pre-Launch Checklist

### Critical (Must Fix)
- [ ] Fix `pagedApps` → `loadMoreApps` in Dashboard.tsx:1108
- [ ] Require REDIS_URL in production for auth
- [ ] CSP: remove unsafe-inline; add nonces
- [ ] Verify 404 trending links work or remove
- [ ] Document JWT in localStorage risk + CSP mitigation

### High (Should Fix)
- [ ] Mobile nav: improve More discoverability
- [ ] Cookie consent: Escape to dismiss, Manage preferences
- [ ] Homepage: remove or clearly label fake activity
- [ ] Login: visible focus ring on email input
- [ ] Post-onboarding guided tour

### Medium (Nice to Have)
- [ ] Font preload for LCP
- [ ] Design system color alignment
- [ ] ApplicationsView detail route
- [ ] i18n expansion
- [ ] Analytics: swipe, upgrade events

### Verification
- [ ] Run `make lint-backend` and `make test-backend`
- [ ] Run `make lint-mobile` if applicable
- [ ] Manual test: full onboarding → dashboard → jobs → applications
- [ ] Manual test: login → magic link → dashboard
- [ ] Manual test: mobile bottom nav → More → all routes
- [ ] Manual test: cookie consent → reject → verify no GA
- [ ] Manual test: dark mode toggle
- [ ] Manual test: keyboard nav (Tab, Enter, Arrow keys)
- [ ] Lighthouse: LCP, FID, CLS
- [ ] axe DevTools: accessibility scan
```

---

**End of Audit**
