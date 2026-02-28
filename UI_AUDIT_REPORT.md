# JobHuntin (Sorce) — UI, Design System & Accessibility Audit

**Date:** 2026-02-28  
**Scope:** `apps/web/src/` and `apps/web-admin/src/`  
**Standard:** WCAG 2.2 AA/AAA, production readiness

---

## Executive Summary

The codebase has a solid foundation: lazy-loaded routes, a centralized copy file (`copy.ts`), nascent i18n (`lib/i18n.ts`), a decent CVA-based component library, and good skeleton/loading state coverage. However, there are **significant gaps** across design-system consistency, accessibility, dark-mode completeness, responsive design, and i18n readiness. Below are **85 findings** organized by category.

---

## 1. Design System Consistency

### Finding 1 — Dual, divergent theme systems
- **Files:** `apps/web/src/lib/theme.ts` (lines 1-44), `apps/web/tailwind.config.js` (lines 14-30), `apps/web/src/index.css` (lines 7-37)
- **Issue:** `theme.ts` defines a "JobHuntin" theme with colors like `sunrise: "#FF9C6B"`, `lagoon: "#17BEBB"`, `plum: "#6A4C93"`, `mango: "#FFC857"`, `ink: "#101828"`. Meanwhile, `tailwind.config.js` defines `brand.ink: "#1c1917"`, `brand.accent: "#d97706"`, `brand.shell: "#fafaf9"`, `brand.muted: "#78716c"`, and `index.css` defines yet another set of CSS custom properties with warm stone-based neutrals. The `theme.ts` `ink` is `#101828` (slate-900-ish blue) while `tailwind.config.js` `brand.ink` is `#1c1917` (stone-900 warm). **These are different brand identities that are never reconciled.**
- **Fix:** Consolidate into one single source of truth. Use CSS custom properties defined in `index.css` as the canonical values, reference them in `tailwind.config.js`, and remove the `theme.ts` file (or make it read from CSS vars).

### Finding 2 — `theme.ts` fonts never used
- **File:** `apps/web/src/lib/theme.ts`, lines 13-14
- **Issue:** `theme.ts` declares `typography.primary: "'Baloo 2'"` and `typography.secondary: "'Space Grotesk'"`, but neither font is loaded anywhere. The actual app uses Inter + Instrument Serif from `tailwind.config.js`.
- **Fix:** Remove the unused font declarations from `theme.ts` or replace them with the actual fonts.

### Finding 3 — Hardcoded colors outside the design system (web app)
- **File:** `apps/web/src/index.css`, lines 155-156
- **Issue:** `.gradient-primary` uses `#3b82f6` (blue-500) and `#2563eb` (blue-600), which is a "tech blue" that contradicts the warm amber/stone palette declared elsewhere. This blue also appears in `.drop-shadow-glow` (line 167), `.gradient-text-premium` (line 607), `.gradient-border` (line 614), `.glow-soft` (line 621), `.text-glow` (line 235).
- **Fix:** Replace all instances of blue-500/violet-500/pink-500 gradients with the brand accent color (`#d97706` amber) or create explicit "premium/AI" accent tokens if blue is intentional.

### Finding 4 — `error-600`, `success-600`, `warning-*` color tokens undefined
- **File:** `apps/web/src/components/ui/Button.tsx`, lines 18-19; `apps/web/src/components/ui/Badge.tsx`, lines 13-14
- **Issue:** Button variants reference `bg-error-600`, `bg-success-600`, `bg-success-700`. Badge variants reference `bg-success-100`, `text-success-700`, `bg-warning-100`, `bg-error-100`, etc. None of these tokens are defined in `tailwind.config.js`. These will produce no styles at all in a clean Tailwind build.
- **Fix:** Add `success`, `warning`, and `error` color scales to `tailwind.config.js` `theme.extend.colors`, or map them to existing Tailwind colors (e.g., `success: colors.emerald`).

### Finding 5 — `brand.sunrise`, `brand.lagoon` tokens undefined in Tailwind
- **File:** `apps/web/src/components/ui/LoadingSpinner.tsx`, line 26
- **Issue:** `border-brand-sunrise/40` and `border-t-brand-sunrise` reference `brand.sunrise`, which is not in `tailwind.config.js`. Only `brand.ink`, `brand.accent`, `brand.shell`, `brand.muted` are defined. The spinner will be invisible.
- **Fix:** Add `brand.sunrise`, `brand.lagoon`, `brand.mango`, `brand.plum` from `theme.ts` to `tailwind.config.js`.

### Finding 6 — Inconsistent border-radius scale
- **File:** `apps/web/src/lib/theme.ts`, lines 32-36; various components
- **Issue:** `theme.ts` defines radii `pill: "999px"`, `blob: "32px"`, `card: "24px"`, `chip: "999px"`. But components use a mix of Tailwind classes: `rounded-2xl` (16px), `rounded-3xl` (24px), `rounded-xl` (12px), `rounded-lg` (8px), `rounded-md` (6px), `rounded-full` (9999px). There are **at least 6 different border-radius values** in use without a clear hierarchy.
- **Fix:** Standardize on 3-4 radius tokens (e.g., `sm: 8px`, `md: 12px`, `lg: 24px`, `full: 9999px`) and document usage guidelines.

### Finding 7 — web-admin uses entirely different design token strategy
- **Files:** `apps/web-admin/tailwind.config.js` (lines 1-19), `apps/web-admin/src/index.css` (lines 1-26)
- **Issue:** web-admin uses HSL CSS variables (`--primary`, `--background`, `--foreground`, etc.) in a shadcn/ui-compatible setup, while web uses RGB CSS variables with Tailwind's alpha syntax. The two apps share zero design tokens.
- **Fix:** Extract shared CSS variable definitions into a `packages/ui-tokens` package or at minimum document that these are intentionally different.

### Finding 8 — No consistent shadow scale
- **File:** `apps/web/tailwind.config.js`, lines 32-35
- **Issue:** Only two shadows are defined: `subtle` and `elevated`. But components freely use Tailwind's built-in `shadow-sm`, `shadow-md`, `shadow-lg`, `shadow-xl`, `shadow-2xl`, plus custom inline box-shadows in CSS utilities. There are at least 12 different shadow values in use.
- **Fix:** Define a complete shadow scale in the theme config and enforce usage through linting or convention.

### Finding 9 — `font-display` class references CSS variable that doesn't exist
- **File:** `apps/web/src/index.css`, lines 88-90
- **Issue:** `.font-display { font-family: var(--font-display); }` but `--font-display` is never defined. Only `--font-body` is defined on `:root`. `tailwind.config.js` does define `display: ["'Instrument Serif'", ...]` but the CSS variable path is broken.
- **Fix:** Add `--font-display: 'Instrument Serif', Georgia, serif;` to `:root` in `index.css`.

---

## 2. Accessibility (WCAG 2.2 AA/AAA)

### Finding 10 — No skip link
- **File:** `apps/web/src/App.tsx`, `apps/web/src/layouts/AppLayout.tsx`, `apps/web/src/layouts/MarketingLayout.tsx`
- **Issue:** No skip-navigation link exists. Keyboard users must tab through the entire navbar and sidebar before reaching main content.
- **Fix:** Add `<a href="#main-content" className="sr-only focus:not-sr-only ...">Skip to content</a>` at the top of both layouts, and `id="main-content"` on the `<main>` element.

### Finding 11 — Missing landmark roles on marketing pages
- **File:** `apps/web/src/pages/Homepage.tsx`
- **Issue:** None of the `<section>` elements have `aria-labelledby` or `aria-label` attributes. Screen readers see generic "region" landmarks with no differentiation. The page has ~8 sections that all announce as "region".
- **Fix:** Add `aria-labelledby` pointing to each section's heading `id`, or `aria-label` descriptors.

### Finding 12 — `<nav>` lacks `aria-label` on marketing navbar
- **File:** `apps/web/src/components/marketing/MarketingNavbar.tsx`, line 41
- **Issue:** The `<nav>` element has no `aria-label`. When multiple `<nav>` elements exist on a page (navbar + footer links + mobile bottom nav), screen readers cannot distinguish them.
- **Fix:** Add `aria-label="Main navigation"` to the navbar `<nav>`.

### Finding 13 — Footer social links have no accessible text
- **File:** `apps/web/src/components/marketing/MarketingFooter.tsx`, lines 74-83
- **Issue:** Social media links (`<a href="#">`) contain only SVG icons (Twitter, LinkedIn, GitHub) with no `aria-label` or visually hidden text. They also use `href="#"` which is a broken link.
- **Fix:** Add `aria-label="Follow us on Twitter"` (etc.) to each social link and use actual URLs.

### Finding 14 — DealbreakerIndicator uses only `title` for tooltip
- **File:** `apps/web/src/components/Jobs/JobCard.tsx`, lines 46-66
- **Issue:** The dealbreaker tooltip uses `title` attribute for its tooltip text. `title` is not announced by all screen readers and is not keyboard-accessible.
- **Fix:** Use `aria-label` or a proper tooltip pattern with `aria-describedby`.

### Finding 15 — SkillMatchTooltip and MatchExplanationTooltip are not keyboard-accessible
- **File:** `apps/web/src/components/Jobs/JobCard.tsx`, lines 68-135
- **Issue:** Tooltips are visible on `:hover` via `opacity-0 group-hover:opacity-100` but have no keyboard trigger, no `role="tooltip"`, no `aria-describedby` link, and `pointer-events-none` prevents interaction.
- **Fix:** Use a proper tooltip component with focus trigger, or switch to a Radix UI tooltip primitive.

### Finding 16 — Toast dismiss button has no `aria-label`
- **File:** `apps/web/src/components/ui/ToastShelf.tsx`, line 41
- **Issue:** The dismiss `<button>` contains only an `<X>` icon with no accessible label.
- **Fix:** Add `aria-label="Dismiss notification"`.

### Finding 17 — Toast shelf has no live-region announcement
- **File:** `apps/web/src/components/ui/ToastShelf.tsx`, lines 24-48
- **Issue:** The toast container lacks `role="alert"` or `aria-live="polite"`. New toasts appear without being announced to screen readers.
- **Fix:** Add `role="status" aria-live="polite"` to the container div.

### Finding 18 — AutoCompleteInput dropdown lacks ARIA attributes
- **File:** `apps/web/src/components/ui/AutoCompleteInput.tsx`, lines 104-143
- **Issue:** The combobox pattern is missing `role="combobox"`, `aria-expanded`, `aria-autocomplete`, `aria-controls` on the input; `role="listbox"` on the `<ul>`; and `role="option"`, `aria-selected` on each `<li>`.
- **Fix:** Implement the ARIA combobox pattern per WAI-ARIA 1.2 specification.

### Finding 19 — FAQ accordion buttons lack `aria-expanded` and `aria-controls`
- **File:** `apps/web/src/components/marketing/FAQ.tsx`, lines 79-82
- **Issue:** The FAQ toggle `<button>` has no `aria-expanded` attribute and no `aria-controls` linking to the answer panel. The `id` on the answer panel is also missing.
- **Fix:** Add `aria-expanded={isOpen}`, `aria-controls={panelId}`, and `id={panelId}` on the answer panel.

### Finding 20 — SEO FAQ accordion has `aria-expanded` but no `aria-controls`
- **File:** `apps/web/src/components/seo/FAQAccordion.tsx`, line 47
- **Issue:** Has `aria-expanded` but missing `aria-controls` and answer `id`.
- **Fix:** Add `aria-controls={`faq-answer-${i}`}` and `id={`faq-answer-${i}`}` on each answer div.

### Finding 21 — Color contrast: amber warning text on amber background
- **File:** `apps/web/src/components/Jobs/JobCard.tsx`, line 240
- **Issue:** `text-amber-600` on `bg-amber-50` yields approximately 3.3:1 contrast ratio, below WCAG AA requirement of 4.5:1 for normal text.
- **Fix:** Use `text-amber-800` or `text-amber-900` for sufficient contrast.

### Finding 22 — Color contrast: slate-400 text on white
- **Files:** Multiple — `apps/web/src/components/Jobs/JobCard.tsx` line 228; `apps/web/src/pages/Dashboard.tsx` line 253; `apps/web/src/pages/Homepage.tsx` line 171
- **Issue:** `text-slate-400` (#94a3b8) on white (#ffffff) yields ~3.0:1, failing WCAG AA (4.5:1 for normal text). This is used extensively for secondary text.
- **Fix:** Use `text-slate-500` (#64748b, ~4.6:1) or `text-slate-600` (#475569, ~7.0:1) as minimum for body text.

### Finding 23 — Color contrast: `text-brand-ink/60` opacity pattern
- **Files:** Multiple — `apps/web/src/pages/Settings.tsx` line 154; `apps/web/src/components/Applications/AppCard.tsx` line 51
- **Issue:** `text-brand-ink/60` means 60% opacity of `#1c1917`. On white, the effective color ~`#878380` yields ~4.0:1. Below AA for small text.
- **Fix:** Use `text-brand-ink/70` minimum or `text-brand-muted` which is `#78716c` (~4.7:1).

### Finding 24 — `user-scalable=no` prevents zooming
- **File:** `apps/web/index.html`, line 5
- **Issue:** `maximum-scale=1.0, user-scalable=no` prevents users from zooming. This violates WCAG 1.4.4 (Resize Text) — a Level AA requirement.
- **Fix:** Remove `maximum-scale=1.0, user-scalable=no` from the viewport meta tag. The iOS input zoom issue is already handled via `font-size: 16px !important` in CSS.

### Finding 25 — Close button in JobDetailDrawer has no `aria-label`
- **File:** `apps/web/src/components/Jobs/JobDetailDrawer.tsx`, line 50-52
- **Issue:** Close button uses `<Button variant="ghost" size="sm"><X /></Button>` without aria-label.
- **Fix:** Add `aria-label="Close job details"`.

### Finding 26 — Close button in CoverLetterGenerator has no `aria-label`
- **File:** `apps/web/src/components/Jobs/CoverLetterGenerator.tsx`, line 69
- **Issue:** Same issue as Finding 25.
- **Fix:** Add `aria-label="Close cover letter generator"`.

### Finding 27 — JobDetailDrawer lacks dialog role and focus trap
- **File:** `apps/web/src/components/Jobs/JobDetailDrawer.tsx`, lines 24-183
- **Issue:** The drawer does not use `role="dialog"` or `aria-modal="true"`, and has no focus trap. Focus can escape behind the backdrop.
- **Fix:** Add ARIA dialog attributes and implement focus trap like `MobileDrawer.tsx` does.

### Finding 28 — CoverLetterGenerator modal lacks dialog role and focus trap
- **File:** `apps/web/src/components/Jobs/CoverLetterGenerator.tsx`, lines 50-184
- **Issue:** Same as Finding 27. Uses a backdrop but no `role="dialog"`, no `aria-modal`, no focus trap, no Escape key handler.
- **Fix:** Add ARIA attributes and focus management.

### Finding 29 — `<img>` in hero cards has no alt text
- **File:** `apps/web/src/pages/Homepage.tsx` — the decorative cards in the hero section
- **Issue:** While functional `<img>` tags in JobCard.tsx have alt text, there are no actual `<img>` elements in the hero — but the decorative color blocks should have `aria-hidden="true"`.
- **Fix:** Ensure all purely decorative elements have `aria-hidden="true"`.

### Finding 30 — web-admin login form inputs lack `aria-label` or visible `<label>`
- **File:** `apps/web-admin/src/pages/LoginPage.tsx`, lines 44-58
- **Issue:** Inputs use `placeholder` as the only label. Placeholders disappear on focus and are not reliably announced as labels.
- **Fix:** Add visible `<label>` elements or `aria-label` attributes.

### Finding 31 — web-admin sidebar navigation lacks `aria-label`
- **File:** `apps/web-admin/src/App.tsx`, line 94
- **Issue:** `<aside>` tag used for nav but no `role="navigation"` or `aria-label`.
- **Fix:** Use `<nav aria-label="Admin navigation">` inside the aside, or add `role="navigation" aria-label="Admin sidebar"` to the aside.

### Finding 32 — Heading hierarchy skip: H1 → H3
- **File:** `apps/web/src/pages/Homepage.tsx` — trust bar section uses `<h2>`, then feature cards immediately jump to `<h3>` without intervening `<h2>` in the same semantic tree.
- **Issue:** While technically the heading hierarchy is maintained within sections, screen reader users navigating by headings may find the structure confusing.
- **Fix:** Audit all page templates and ensure each section starts with an appropriate heading level.

### Finding 33 — Skeleton components lack `aria-busy` or `role="status"`
- **File:** `apps/web/src/components/ui/Skeleton.tsx`, lines 6-13
- **Issue:** Skeleton placeholders provide no screen reader feedback. Users don't know content is loading.
- **Fix:** Wrap skeleton groups in a container with `role="status" aria-label="Loading content" aria-busy="true"`.

### Finding 34 — Empty `<button>` wrapping `<Link>` pattern creates nested interactive elements
- **File:** `apps/web/src/components/marketing/MarketingNavbar.tsx`, lines 76-79, 87-89, 154, 165, 174
- **Issue:** `<Link to="..."><button>...</button></Link>` nests a `<button>` inside an `<a>` — invalid HTML. Screen readers may announce this confusingly as two clickable elements.
- **Fix:** Use either `<Link>` with button styling or `<Button asChild><Link>...</Link></Button>`, never nest them.

---

## 3. Responsive Design

### Finding 35 — Bottom mobile nav overlaps page content
- **File:** `apps/web/src/layouts/AppLayout.tsx`, line 179
- **Issue:** The fixed bottom nav (`fixed bottom-0`) is 56px tall but `<main>` only has `pb-20` (80px). On some views the last card is partially hidden.
- **Fix:** Add `pb-24` to `<main>` for consistent safe area.

### Finding 36 — Homepage sticky CTA conflicts with AppLayout bottom nav
- **File:** `apps/web/src/pages/Homepage.tsx`, lines 841-847
- **Issue:** Sticky mobile CTA at bottom may visually overlap with the marketing layout's potential bottom elements or compete with browser chrome.
- **Fix:** Ensure `safe-area-inset-bottom` padding: `pb-[env(safe-area-inset-bottom)]`.

### Finding 37 — Touch target too small: social media links in footer
- **File:** `apps/web/src/components/marketing/MarketingFooter.tsx`, lines 75-83
- **Issue:** Social links are `w-9 h-9` (36x36px), below the recommended 44x44px minimum touch target.
- **Fix:** Increase to `w-11 h-11` (44x44px).

### Finding 38 — Touch target too small: bottom nav items
- **File:** `apps/web/src/layouts/AppLayout.tsx`, lines 185-198
- **Issue:** Bottom nav items have `py-2` padding resulting in ~40px height, slightly under the 44px minimum.
- **Fix:** Increase to `py-3` for reliable 44px+ touch targets.

### Finding 39 — Touch target too small: badge-sized buttons on JobCard
- **File:** `apps/web/src/components/Jobs/JobCard.tsx`, lines 292-299
- **Issue:** `<Button variant="ghost" size="sm">` with icons produces touch targets around 32x32px.
- **Fix:** Use `size="md"` or add `min-h-[44px] min-w-[44px]` to ensure adequate touch targets.

### Finding 40 — web-admin has no mobile responsive layout
- **File:** `apps/web-admin/src/App.tsx`, line 94
- **Issue:** The sidebar is always 224px (`w-56`) with no mobile breakpoint handling. On screens under 768px, the sidebar takes ~30% of the viewport with no collapse mechanism.
- **Fix:** Add a responsive sidebar that collapses to a hamburger menu on mobile.

### Finding 41 — web-admin has no viewport `user-scalable` restriction (good) but lacks touch optimizations
- **File:** `apps/web-admin/index.html`, line 6
- **Issue:** The viewport meta is minimal. While not restrictive (good), the admin tables and inputs have no touch-target sizing considerations.
- **Fix:** Add touch-friendly padding to interactive elements in the admin.

### Finding 42 — Horizontal overflow risk on job swipe deck
- **File:** `apps/web/src/pages/Dashboard.tsx`, line 760
- **Issue:** The swipe card deck allows dragging on the X axis, which can cause visual overflow. While `overflow-x: hidden` is set on `html`, the card animation can briefly show horizontal scrollbar during swipe.
- **Fix:** Add `overflow-hidden` to the swipe deck container.

---

## 4. Dark Mode

### Finding 43 — Dark mode declared but never implemented in web app
- **File:** `apps/web/tailwind.config.js`, line 5
- **Issue:** `darkMode: ["class"]` is configured, but not a single component uses `dark:` variants. The entire app is light-mode only. The body has hardcoded `background-color: #fafaf9` and `color: #1c1917`.
- **Fix:** Either remove the `darkMode` config to avoid confusion, or implement dark mode across all components. At minimum, add CSS variables for background/foreground and swap them in a `dark` class.

### Finding 44 — web-admin is dark-only, no light mode toggle
- **File:** `apps/web-admin/src/index.css`
- **Issue:** CSS variables define a dark theme only (`--background: 222.2 84% 4.9%`). There's no theme toggle or light-mode option.
- **Fix:** If dark-only is intentional, document it. Otherwise add a theme toggle with light-mode variables.

### Finding 45 — Glass panel utilities assume light mode
- **File:** `apps/web/src/index.css`, lines 183-214
- **Issue:** `.glass-panel` has `background: rgba(255, 255, 255, 0.8)` and `.glass-panel-dark` exists separately. In a proper dark mode, `.glass-panel` should automatically adapt.
- **Fix:** Use `dark:` variant or CSS variable-based backgrounds.

---

## 5. Performance

### Finding 46 — All routes properly lazy-loaded ✅
- **File:** `apps/web/src/App.tsx`, lines 16-53
- **Issue:** None — good use of `React.lazy()` for all page-level components.

### Finding 47 — Framer Motion imported in many components (bundle impact)
- **Files:** `EmptyState.tsx`, `GoogleSearch.tsx`, `CoverLetterGenerator.tsx`, `MobileDrawer.tsx`, `FAQ.tsx`, `HowItWorks.tsx`, `Testimonials.tsx`, `Dashboard.tsx`, `Homepage.tsx`, `Login.tsx`, `AppLayout.tsx`
- **Issue:** `framer-motion` is imported in 11+ components. While tree-shaking helps, the base Framer Motion bundle is ~30KB gzipped. Many uses are simple fade/slide animations achievable with CSS.
- **Fix:** Replace simple animations (fade-in, slide-in) with CSS animations (already defined in `index.css`). Reserve Framer Motion for complex interactions (drag swipe, AnimatePresence exit).

### Finding 48 — Google Fonts loaded twice
- **Files:** `apps/web/index.html` (line 28-29), `apps/web/src/index.css` (line 1)
- **Issue:** Inter font is loaded via `<link>` in HTML and via `@import url(...)` in CSS. This causes a duplicate network request.
- **Fix:** Remove the `@import` in `index.css` since `index.html` already loads it with `<link>`.

### Finding 49 — No `loading="lazy"` on homepage decorative elements
- **File:** `apps/web/src/pages/Homepage.tsx`
- **Issue:** While there are no actual `<img>` tags (UI is CSS-only), the heavy SVG animations in `HowItWorks.tsx` (8 animated elements per step × 4 steps = 32+ animated DOM nodes) render on page load even if below the fold.
- **Fix:** Consider using `useInView` to delay rendering of HowItWorks step visuals until they're near the viewport (already partially done but the SVG radar/rocket animations render immediately).

### Finding 50 — Google Analytics script blocks parsing
- **File:** `apps/web/index.html`, lines 12-19
- **Issue:** The inline GA script runs synchronously before the app loads. While the gtag.js `<script>` has `async`, the inline config script is synchronous.
- **Fix:** Wrap the inline script in a `setTimeout` or move GA initialization to the React app via `useGoogleAnalytics` hook (which already exists).

### Finding 51 — No image optimization strategy
- **Files:** All component files
- **Issue:** While `loading="lazy"` is used on company logos in `JobCard.tsx` and `JobDetailDrawer.tsx`, there's no `<picture>` / `srcset` usage, no WebP serving, and no image CDN configuration.
- **Fix:** Add image optimization instructions or configure Vite image plugin for WebP generation.

### Finding 52 — Dashboard AnimatedNumber uses setInterval at 60fps
- **File:** `apps/web/src/pages/Dashboard.tsx`, lines 125-163
- **Issue:** `setInterval` at 16.67ms (60fps) for number animation is expensive. With 4 metric cards, that's 4 concurrent intervals.
- **Fix:** Use `requestAnimationFrame` instead, or use Framer Motion's `useSpring` for value animation.

---

## 6. Micro-Interactions & States

### Finding 53 — LoadingSpinner uses undefined brand colors
- **File:** `apps/web/src/components/ui/LoadingSpinner.tsx`, line 26
- **Issue:** As noted in Finding 5, `border-brand-sunrise` is undefined, making the spinner invisible.
- **Fix:** Use a defined color, e.g., `border-amber-500/40 border-t-amber-500`.

### Finding 54 — Button `wobble` variant declared but has empty styles
- **File:** `apps/web/src/components/ui/Button.tsx`, lines 28-31
- **Issue:** `wobble: { true: "", false: "" }` — the variant exists but applies no styles. Multiple components pass `wobble` prop (e.g., JobCard, JobDetailDrawer, CoverLetterGenerator).
- **Fix:** Either implement the wobble animation (e.g., keyframe wiggle on hover) or remove the prop.

### Finding 55 — No error boundary recovery for lazy-loaded routes
- **File:** `apps/web/src/App.tsx`, line 159
- **Issue:** If a lazy-loaded chunk fails to load (network issue), the `Suspense` fallback shows indefinitely. There's no `ErrorBoundary` wrapping the `Suspense` for chunk load failures.
- **Fix:** Wrap `<Suspense>` in an `<ErrorBoundary>` that shows a "Failed to load, click to retry" message.

### Finding 56 — No disabled state visual for input fields
- **File:** `apps/web/src/components/ui/Input.tsx`, line 30
- **Issue:** `disabled:cursor-not-allowed disabled:opacity-50` is applied but there's no visual differentiation (e.g., gray background) between disabled and enabled inputs.
- **Fix:** Add `disabled:bg-slate-100` for clearer visual distinction.

### Finding 57 — Swipe card has no keyboard alternative
- **File:** `apps/web/src/pages/Dashboard.tsx`, lines 759-863
- **Issue:** The swipe deck's primary interaction is drag-based. While accept/reject buttons exist, the drag-to-swipe gesture has no keyboard equivalent (e.g., arrow keys).
- **Fix:** Add keyboard event handlers for Left/Right arrow keys to trigger reject/accept.

### Finding 58 — No transition on skeleton-to-content swap
- **File:** `apps/web/src/components/ui/Skeleton.tsx`
- **Issue:** When content loads, skeletons abruptly disappear. No fade transition.
- **Fix:** Wrap content in a simple fade-in animation when it replaces skeletons.

---

## 7. Component Library Structure

### Finding 59 — Three separate ErrorBoundary components with overlapping scope
- **Files:** `apps/web/src/components/ui/ErrorBoundary.tsx`, `apps/web/src/components/ui/ErrorBoundaryAI.tsx`, `apps/web/src/components/ui/EnhancedErrorBoundary.tsx`, `apps/web/src/components/ErrorBoundary.tsx`
- **Issue:** Four error boundary files exist. `ErrorBoundary.tsx` appears in both `components/` and `components/ui/`. `ErrorBoundaryAI.tsx` categorizes errors. `EnhancedErrorBoundary.tsx` has retry logic and error reporting. These have overlapping functionality and it's unclear which to use where.
- **Fix:** Consolidate into one or two: a simple `ErrorBoundary` for general use and `ErrorBoundaryAI` for AI-specific features. Remove duplicates.

### Finding 60 — CVA-based components are well-typed ✅
- **Files:** `Button.tsx`, `Card.tsx`, `Badge.tsx`
- **Issue:** None — good use of CVA with TypeScript `VariantProps` for type-safe variants.

### Finding 61 — No Radix UI dialog primitive for modals
- **Files:** `JobDetailDrawer.tsx`, `CoverLetterGenerator.tsx`, `MobileDrawer.tsx`
- **Issue:** Only `MobileDrawer.tsx` properly implements focus trap and aria attributes. The other two modals are custom implementations missing accessibility features. `@radix-ui/react-slot` is already a dependency but no dialog primitive is used.
- **Fix:** Use `@radix-ui/react-dialog` for all modal/drawer components to get focus trap, aria attributes, and portal rendering for free.

### Finding 62 — SparklesIcon duplicated across components
- **Files:** `apps/web/src/components/ui/AIMatchBadge.tsx` (lines 13-25), `apps/web/src/components/ui/AISuggestionCard.tsx` (lines 12-26)
- **Issue:** The same SVG sparkles icon is defined as a local component in two different files.
- **Fix:** Extract to a shared `icons/` module or use lucide-react's `Sparkles` icon (which is already used in other components).

### Finding 63 — Input component allows both `onClear` and password toggle but not both
- **File:** `apps/web/src/components/ui/Input.tsx`, lines 39-62
- **Issue:** The component shows password toggle only when `isPassword && !onClear`, and shows clear only when `onClear && value && !isPassword`. A password field with clearable text isn't supported.
- **Fix:** Allow both controls simultaneously with proper spacing.

---

## 8. Copy & Microcopy

### Finding 64 — Copy file (`copy.ts`) exists but is rarely used
- **File:** `apps/web/src/copy.ts` (lines 1-151)
- **Issue:** A comprehensive copy file exists with standardized messages, but most components use hardcoded strings. For example, `Dashboard.tsx` uses `"Your Command Center"`, `"Active Applications"`, `"Active Transmissions"` etc. instead of `COPY.nav.dashboard` or other centralized strings.
- **Fix:** Migrate hardcoded UI strings to `copy.ts` references.

### Finding 65 — Inconsistent brand voice between marketing and app
- **Files:** `apps/web/src/pages/Homepage.tsx` vs `apps/web/src/pages/Dashboard.tsx`
- **Issue:** Marketing pages use clean, professional copy ("Upload your resume. Our AI tailors every application"). The app dashboard uses spy/military metaphor copy ("Active Transmissions", "Signal Silence", "Decrypting application signals", "Initialize Hunt", "Intercepting job signals"). These are completely different brand voices.
- **Fix:** Align on one voice. The `copy.ts` file uses a "playful, scrappy, energetic" voice (per `theme.ts`) which matches neither.

### Finding 66 — Militaristic jargon may confuse non-native speakers
- **File:** `apps/web/src/pages/Dashboard.tsx`
- **Issue:** Terms like "Radar Sweep Complete", "Active Transmissions", "Signal Silence", "Initialize Hunt", "Intercepting job signals", "Communication channels", "encryption key" are domain jargon that may confuse job seekers.
- **Fix:** Use plain language: "All caught up", "Applications", "No results", "Start searching", "Finding jobs", etc.

### Finding 67 — Emoji in status labels may not render on all platforms
- **File:** `apps/web/src/components/Applications/AppCard.tsx`, lines 8-12
- **Issue:** `STATUS_LABEL` uses emoji: `"✅ Applied"`, `"⏳ HOLD"`, `"❌ Failed"`. Emoji rendering varies across platforms and may not be announced consistently by screen readers.
- **Fix:** Use icon components instead of emoji characters for status indicators.

### Finding 68 — `"HOLD"` terminology unexplained to users
- **Files:** `apps/web/src/pages/Dashboard.tsx`, `apps/web/src/components/Applications/AppCard.tsx`
- **Issue:** "HOLD" is used throughout without explanation. New users won't understand what a "HOLD" means (the AI agent paused an application because it needs user input).
- **Fix:** Add a brief tooltip or first-use explanation: "The AI needs your help to complete this application."

### Finding 69 — Error messages reference objects in production
- **File:** `apps/web/src/pages/Login.tsx`, lines 87, 167
- **Issue:** Error handling checks for `[object` in message strings — this suggests `[object Object]` errors have leaked to users in the past.
- **Fix:** Use a typed error parser that never leaks raw objects. The check is good but indicates deeper error handling issues.

### Finding 70 — Placeholder text tone inconsistent
- **Files:** Various
- **Issue:** `"name@company.com"` (Homepage), `"you@example.com"` (Login), `"Filter location..."` (Dashboard), `"Search company or title..."` (ApplicationsView). Different placeholder styles and specificity levels.
- **Fix:** Standardize placeholder format in `copy.ts`.

---

## 9. i18n Readiness

### Finding 71 — i18n system exists but covers <5% of strings
- **File:** `apps/web/src/lib/i18n.ts`
- **Issue:** Only ~11 keys are translated (all dashboard-related). The rest of the app has hundreds of hardcoded English strings.
- **Fix:** Extract all user-facing strings to the i18n dictionary. Consider using a standard i18n library like `react-intl` or `i18next` for pluralization, date formatting, and number formatting.

### Finding 72 — French translations exist but are incomplete
- **File:** `apps/web/src/lib/i18n.ts`, lines 18-31
- **Issue:** Only `dashboard.*` and `holds.responseRequired` keys have French translations. All other UI text (marketing, onboarding, settings, billing, error messages) is English-only.
- **Fix:** Complete French translations or remove partial ones to avoid a half-translated UI.

### Finding 73 — RTL support declared but untested
- **File:** `apps/web/src/lib/i18n.ts`, lines 34, 43-46
- **Issue:** `rtlLocales` array and `isRTL()` function exist, and `Dashboard.tsx` passes `dir="rtl"` when RTL locale detected. However, no CSS is RTL-aware (all `left-4`, `right-4`, `pl-12`, `pr-12` etc. are physical, not logical properties).
- **Fix:** Convert to logical CSS properties (`ps-12` instead of `pl-12`, `start-4` instead of `left-4`) or use Tailwind's RTL plugin.

### Finding 74 — Currency formatting assumes USD
- **File:** `apps/web/src/components/ui/AISuggestionCard.tsx`, lines 281-287
- **Issue:** `SalarySuggestionCard` defaults to `currency = "USD"` and formats with `en-US` locale regardless of user locale.
- **Fix:** Use the user's detected locale for formatting: `new Intl.NumberFormat(getLocale(), ...)`.

### Finding 75 — Date formatting is locale-aware in some places but not others
- **Files:** `apps/web/src/pages/Dashboard.tsx` uses `formatDate(date, locale)`, but `apps/web/src/components/Applications/AppCard.tsx` line 52 uses `new Date(x).toLocaleDateString()` without locale parameter.
- **Fix:** Always pass locale to date formatting functions.

### Finding 76 — web-admin has zero i18n
- **File:** `apps/web-admin/src/`
- **Issue:** All admin strings are hardcoded English with no i18n infrastructure.
- **Fix:** At minimum, use constants for user-facing strings to prepare for future i18n.

---

## 10. Additional Findings

### Finding 77 — EnhancedErrorBoundary sends reports to `/api/errors/report` which may not exist
- **File:** `apps/web/src/components/ui/EnhancedErrorBoundary.tsx`, line 111
- **Issue:** Error reporting POSTs to `/api/errors/report` — this endpoint is not defined in the API. The `catch` silently swallows the 404.
- **Fix:** Either implement the endpoint or remove the reporting call. The silent failure creates false confidence.

### Finding 78 — EnhancedErrorBoundary uses `innerHTML` for success message
- **File:** `apps/web/src/components/ui/EnhancedErrorBoundary.tsx`, lines 222-243
- **Issue:** `document.createElement('div')` with `innerHTML` for showing "error report sent" notification. This bypasses React's DOM management and could create memory leaks.
- **Fix:** Use the existing `pushToast()` function instead.

### Finding 79 — `window.__USER_ID__` accessed without type safety
- **File:** `apps/web/src/components/ui/EnhancedErrorBoundary.tsx`, line 149
- **Issue:** `(window as any).__USER_ID__` is a type-unsafe global. No code sets this value.
- **Fix:** Remove or type properly with a `declare global` augmentation.

### Finding 80 — PerformanceMonitor component exists but is never used
- **File:** `apps/web/src/components/PerformanceMonitor.tsx`
- **Issue:** Component defined but never imported or rendered anywhere.
- **Fix:** Either integrate it into the app or remove dead code.

### Finding 81 — `lib/redis.ts` exists in a frontend app
- **File:** `apps/web/src/lib/redis.ts`
- **Issue:** A Redis client library in a browser-side frontend app is either dead code or a server-side leak.
- **Fix:** Remove if unused, or move to a backend package.

### Finding 82 — web-admin uses emoji for nav icons instead of icon components
- **File:** `apps/web-admin/src/App.tsx`, lines 68-82
- **Issue:** Navigation icons are emoji strings (`"📊"`, `"📡"`, `"👥"`, etc.). Emoji rendering is inconsistent across platforms and not screen-reader friendly.
- **Fix:** Use `lucide-react` icons for consistent rendering and accessibility.

### Finding 83 — web-admin auth stores token in localStorage (XSS risk)
- **File:** `apps/web-admin/src/App.tsx`, line 36; `apps/web-admin/src/pages/LoginPage.tsx`, line 27
- **Issue:** Auth token stored in `localStorage` is accessible to any JavaScript running on the page, making it vulnerable to XSS attacks.
- **Fix:** Use `httpOnly` cookies for auth tokens, or at minimum `sessionStorage`.

### Finding 84 — No `<h1>` on web-admin loading/access-denied screens
- **File:** `apps/web-admin/src/App.tsx`, lines 162-188
- **Issue:** Loading state shows "Verifying access..." as plain text. Access denied shows `<h1>` but the loading screen does not. Screen readers have no heading landmark.
- **Fix:** Add appropriate heading hierarchy.

### Finding 85 — Homepage `EmailForm` input has no visible label
- **File:** `apps/web/src/pages/Homepage.tsx`, lines 54-69
- **Issue:** The email input uses only `placeholder="name@company.com"` with no `<label>` or `aria-label`. The input is the primary CTA of the entire marketing site.
- **Fix:** Add `aria-label="Email address"` or a visually hidden `<label>`.

---

## Priority Matrix

| Priority | Count | Examples |
|----------|-------|---------|
| **P0 Critical** | 5 | Finding 4 (broken tokens), Finding 5 (invisible spinner), Finding 24 (zoom blocked), Finding 34 (nested interactive), Finding 83 (XSS risk) |
| **P1 High** | 18 | Findings 10, 12, 17, 18, 21-23, 27-28, 30, 40, 43, 53, 57, 65-66, 85 |
| **P2 Medium** | 35 | Findings 1-3, 6-9, 11, 13-16, 19-20, 25-26, 31-33, 35-39, 47-48, 55-56, 59, 61-63, 71-76 |
| **P3 Low** | 27 | Findings 41-42, 44-45, 49-52, 54, 58, 60, 64, 67-70, 77-82, 84 |

---

## Summary

**Strengths:**
- Lazy-loading of routes is comprehensive (Finding 46)
- CVA-based component system with TypeScript is well-structured (Finding 60)
- MobileDrawer has excellent a11y: focus trap, Escape handling, aria attributes, scroll lock
- Copy centralization started (`copy.ts`) with good brand voice guidelines
- i18n foundation exists with RTL awareness
- `prefers-reduced-motion` respected in Dashboard swipe deck
- `prefers-contrast: more` handled in CSS (high contrast mode)
- Good use of `<Helmet>` for SEO meta tags

**Critical gaps:**
1. Design tokens are fragmented across 3 systems with conflicting values
2. Multiple undefined Tailwind tokens will silently produce no styles
3. Accessibility is below WCAG 2.2 AA — major issues with zoom prevention, missing labels, inadequate contrast, no skip links
4. Dark mode is configured but 0% implemented
5. i18n covers <5% of strings
6. Brand voice is split between professional marketing and spy/military app UI
