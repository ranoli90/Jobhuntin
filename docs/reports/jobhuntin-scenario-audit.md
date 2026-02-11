# JobHuntin Scenario Audit & UX Uplift Report

## <comprehensive_scenario_alignment_report>
- **Jobs feed pagination gap (high-volume users):** `useJobs` calls `GET /jobs` without pagination; backend `list_jobs` also returns full result set, risking slow/empty loads for 10k+ items and making swipe deck unusable under load @apps/web/src/hooks/useJobs.ts#28-38, @apps/api/user.py#263-280. **Fix:** add cursor/limit params frontend+backend; show incremental loading skeletons.
- **Swipe REJECT is a no-op server-side:** Frontend sends `decision: "REJECT"`, backend returns `{status:"skipped"}`, so rejected jobs aren’t recorded for deduping; users may re-see the same job after refetch @apps/web/src/pages/Dashboard.tsx#380-404, @apps/api/user.py#115-164. **Fix:** store rejects (with TTL) to avoid resurfacing.
- **Holds subscription noise:** Supabase channel listens to all `applications` changes (no user filter), causing spurious invalidations and churn on slow networks or multi-tenant setups @apps/web/src/hooks/useApplications.ts#31-44. **Fix:** filter channel by user/tenant or debounce invalidations.
- **AI suggestions dependency sequencing:** `fetchAllSuggestions` chains salary suggestions only if `primary_role` exists; errors return `null` silently, leaving UI without guidance @apps/web/src/hooks/useAISuggestions.ts#168-194. **Fix:** surface contextual error toasts and retry affordances; add fallback role from parsed resume headline.
- **Resume upload path lacks partial failure guidance:** Upload errors show generic toast without context (e.g., file size/type) and no retry helper @apps/web/src/pages/app/Onboarding.tsx#84-121. **Fix:** map backend errors to actionable tips and suggest sample resume upload.

## <contextual_dead_code_validation>
- No confidently orphaned hooks/components identified yet; areas to verify: unused swipe decision storage, legacy job card variants. Need codeowner confirmation before removal.

## <adaptive_pixel_perfect_viewport_audit>
- **Onboarding overflow on mobile/keyboard:** Long forms (contact/preferences) can push CTAs below fold on 720p/landscape; no sticky actions @apps/web/src/pages/app/Onboarding.tsx#124-221. **Fix:** add sticky bottom bar for primary CTA, compact spacing, and input zoom-safe styles.
- **Jobs swipe deck fixed height:** `h-[min(550px,65vh)]` may clip on 13" laptops with browser UI or 200% zoom; top controls can force scroll @apps/web/src/pages/Dashboard.tsx#469-505. **Fix:** use `clamp()` heights and responsive stack; ensure filters/CTA visible without scroll.
- **Holds inbox vertical bloat:** Large padding and quotes risk scroll before action buttons on small screens @apps/web/src/pages/Dashboard.tsx#751-843. **Fix:** reduce padding on <md, keep action row sticky.
- **No reduced-motion placeholders on job deck:** When `useReducedMotion` true, animations are removed but no progressive skeletons; initial blank space @apps/web/src/pages/Dashboard.tsx#486-505. **Fix:** add skeleton cards for first fetch and when refetching.

## <situational_copywriting_transformation>
- **Before:** Generic errors like "Failed to record decision" @apps/web/src/pages/Dashboard.tsx#405-413.
- **After (examples):**
  - Jobs swipe failure: "We couldn’t log that swipe. Your choices are safe—tap retry when you’re back online."
  - Empty jobs after filters: "Radar sweep found no matches. Try widening location or lowering salary to discover more leads."
  - Resume upload stall: "Upload stalled—check file size (PDF under 5MB) or try our sample resume to continue."

## <edge_case_functionality_audit>
- **Zero/empty jobs:** Deck shows completion card but no CTA to broaden filters beyond reset; add inline filter suggestions @apps/web/src/pages/Dashboard.tsx#431-445.
- **High-volume jobs:** No pagination/streaming; swipe deck will block and memory spike. See mismatch above.
- **Interrupted flows:** Onboarding progress stored in localStorage only; no cross-device resume, and data can be stale if profile already updated elsewhere @apps/web/src/hooks/useOnboarding.ts#30-140.
- **Multi-device sync:** Applications view relies on Supabase channel without user scoping; possible outdated/inconsistent lists.
- **Hold answers:** No validation or optimism; long answers could fail silently. Add length check and optimistic UI.

## <internationalization_audit_report>
- **Hard-coded English strings across app:** Onboarding, dashboard, jobs, holds, copy all inline with no i18n layer @apps/web/src/pages/app/Onboarding.tsx, @apps/web/src/pages/Dashboard.tsx.
- **No locale formatting:** Dates use `toLocaleDateString()` without locale prop; currencies/salaries rendered as `$` only @apps/web/src/pages/Dashboard.tsx#334-342, @apps/web/src/components/Jobs/JobCard.tsx#60-67. **Fix:** introduce i18n (e.g., react-i18next) and Intl.DateTimeFormat/NumberFormat with locale from browser.
- **RTL/text expansion untested:** Layouts rely on left/right padding and absolute badges; risk clipping in RTL and long strings. Add `dir` support and flex reversal where needed.
- **Backend i18n:** API accepts plain strings; ensure Unicode-safe (asyncpg already), but no timezone/currency locale handling. Add locale params to jobs/profile endpoints and format server-side where appropriate.

## <dopamine_and_ux_enhancements>
- Existing: confetti on ACCEPT swipe and success toast @apps/web/src/pages/Dashboard.tsx#393-400.
- Proposed additions:
  1) **Onboarding completion burst** with celebratory toast + badge unlock.
  2) **First job saved micro-anim** when bookmarking.
  3) **Match Alert banner** when match_score ≥ 80.
  4) **Streak badge** after 10 swipes in a session with reduced-motion-friendly pulse.
  5) **Milestone modal** at 50 views: "You’ve scouted 50 roles—nice hustle!" with quick actions.
- Contextual error guidance: see copy transformations above for upload/swipe/empty states.
- Dynamic empty states: tailor messages for new vs returning vs dormant users (based on swipeCount, last_activity) in jobs/applications views.

## <kickstarter_readiness_verdict>
- **Current state:** Core flows wired but fragile under high data volume, slow/unstable networks, and non-English locales. No pagination, limited offline/placeholder handling, and generic error guidance reduce polish.
- **Blocking gaps before launch:**
  - Add pagination/streaming for jobs feed and reject-tracking to prevent resurfacing.
  - Implement scoped realtime subscriptions to avoid noisy refreshes.
  - Introduce i18n/Intl formatting and RTL-safe layouts; audit all strings.
  - Harden onboarding/resume upload with actionable errors and sticky CTAs for small viewports.
- **Verdict:** Not Kickstarter-ready yet; needs the above fixes plus micro-celebration/empty-state polish to reach high-end SaaS feel.
