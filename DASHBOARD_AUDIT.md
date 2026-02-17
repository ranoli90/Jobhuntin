# Dashboard Comprehensive Audit Report

**Date:** 2026-02-12 (Updated 2026-02-17)  
**Scope:** Dashboard page (`Dashboard.tsx`), Settings page, all dashboard hooks, supporting libraries, backend endpoints  
**Files Audited:** 15 files, ~3400 LOC

---

## Executive Summary

The dashboard is a 1225-line monolith (`Dashboard.tsx`) containing 6 exported components: `Dashboard`, `JobsView`, `ApplicationsView`, `HoldsView`, `TeamView`, and `BillingView`. Supporting hooks (`useApplications`, `useBilling`, `useJobs`, `useKeyboardShortcuts`, `useCelebrations`) and libraries (`api.ts`, `format.ts`, `i18n.ts`, `toast.ts`, `confetti.ts`) are well-structured but have several issues.

**Findings: 38 total**
- **🔴 High (5):** Memory leaks, security issues, data bugs
- **🟡 Medium (12):** UX problems, missing error handling, logic flaws
- **🟢 Low (11):** Code quality, minor UX improvements
- **⚪ Nitpick (10):** Style, naming, conventions

---

## ✅ FIXED ITEMS (22 of 38)

| ID | Severity | Description | File(s) |
|----|----------|-------------|---------|
| H-1 | 🔴 | Timeout cleanup on unmount | `Dashboard.tsx` |
| H-2 | 🔴 | Removed hardcoded "124 jobs" number | `Dashboard.tsx` |
| H-4 | 🔴 | Added maxLength=5000 to hold answers textarea | `Dashboard.tsx` |
| H-5 | 🔴 | Guarded AnimatedNumber for NaN/≤0 edge values | `Dashboard.tsx` |
| M-1 | 🟡 | Rewrote useBilling with react-query + auto-refetch on tab focus | `useBilling.ts` |
| M-2 | 🟡 | Reduced polling from 5s→15s, disabled background polling | `useApplications.ts` |
| M-3 | 🟡 | Added 400ms debounce to location filter | `Dashboard.tsx` |
| M-4 | 🟡 | Captured swipedJob reference before state updates | `Dashboard.tsx` |
| M-5 | 🟡 | Added error banner when useApplications fails | `Dashboard.tsx` |
| M-6 | 🟡 | fireUpgradeConfetti returns cancel function | `confetti.ts` |
| M-8 | 🟡 | Added min/max/inputMode to salary input | `Settings.tsx` |
| M-10 | 🟡 | Billing portal uses separate manageBilling function | `useBilling.ts`, `Dashboard.tsx` |
| M-11 | 🟡 | ?success=1 triggers celebration toast + polling | `useBilling.ts` |
| L-1 | 🟢 | Removed unused isHovered state | `Dashboard.tsx` |
| L-4 | 🟢 | Made job type badge dynamic | `Dashboard.tsx` |
| L-5 | 🟢 | Added aria-label on filter input | `Dashboard.tsx` |
| L-7 | 🟢 | Added toast feedback to snooze | `useApplications.ts` |
| L-8 | 🟢 | "Add Seats" → "Upgrade to Team" for non-TEAM plans | `Dashboard.tsx` |
| L-9 | 🟢 | Added isNaN guard to formatTimeAgo | `useJobs.ts` |
| L-10 | 🟢 | Added per-application loading state (isSubmitting) | `useApplications.ts`, `Dashboard.tsx` |
| N-6 | ⚪ | Fixed swipeTimeoutRef from `any` to proper type | `Dashboard.tsx` |
| N-9 | ⚪ | Removed unused `rtl` variable from ApplicationsView | `Dashboard.tsx` |

---

## 🔴 REMAINING HIGH SEVERITY (1)

### H-3 — `handleSwipe` Calls `apiPost` for REJECT, Which Creates a FAILED Application
**File:** `Dashboard.tsx` / `user.py` (line 166-191)  
**Issue:** Every REJECT swipe creates a `FAILED` status application record in the database. The `stats.monthlyApps` count includes rejected jobs, inflating user metrics. "FAILED" suggests the application failed, not that the user rejected it.  
**Fix:** Add a proper `REJECTED` status or use a separate `rejections` table. At minimum, filter `FAILED` from stats.  
**Status:** ⚠️ Requires backend schema migration — recommended for next sprint.

---

## 🟡 REMAINING MEDIUM SEVERITY (3)

### M-7 — Undo API Route Semantics Confusing
**File:** `Dashboard.tsx` (line 506) vs `user.py` (line 240)  
**Issue:** URL says `applications/{id}/undo` but the param is a `job_id`, not an `application_id`.  
**Fix:** Rename for clarity or document convention.

### M-9 — `useKeyboardShortcut` Has Stale Handler Reference
**File:** `useKeyboardShortcuts.ts` (lines 385-428)  
**Issue:** `handler` in effect dependency causes re-registration on every render when callers pass inline functions.  
**Fix:** Use a ref for the handler.

### M-12 — ApplicationsView Renders All Applications Without Pagination
**File:** `Dashboard.tsx` (ApplicationsView)  
**Issue:** All applications rendered at once. Performance problem for heavy users.  
**Fix:** Add client-side pagination or virtual scrolling.

---

## 🟢 REMAINING LOW SEVERITY (5)

### L-2 — Dashboard Metrics Progress Bars Are Decorative, Not Data-Driven
**File:** `Dashboard.tsx` (lines 184-186)  
**Issue:** Always show 30%, 40%, 50%, 60% regardless of actual values.

### L-3 — No Visual Drag Threshold Feedback on Job Cards
**File:** `Dashboard.tsx` (lines 636-641)  
**Issue:** No color/opacity indication when user has dragged far enough to trigger accept/reject.

### L-6 — Settings Salary Input Missing Helper Text
**File:** `Settings.tsx` (lines 283-289)  
**Status:** ✅ Partially fixed (added helper text "Annual salary in USD").

### L-11 — Keyboard Shortcut Binding Strings Rebuilt Every Keypress
**File:** `useKeyboardShortcuts.ts` (lines 318-325)

---

## ⚪ REMAINING NITPICK (8)

### N-1 — `Dashboard.tsx` Is a 1225-line Monolith (6 Components in One File)
### N-2 — `locale` Detection Duplicated Across Three Views
### N-3 — Inconsistent Error Handling Patterns (toast vs console vs silent)
### N-4 — `cn` Utility Imported But Used Only Once
### N-5 — Overlapping Milestone Thresholds Between Swipe and Session Toasts
### N-7 — `compute_priority_score` Import Inside Function Body
### N-8 — Billing Tier Pricing Hardcoded in Component
### N-10 — Inline Conditional Rendering Inside Badge Component

---

## Priority Fix Order (Remaining)

### Next Sprint
1. H-3 — Add REJECTED status (backend migration)
2. M-9 — Fix stale keyboard shortcut handler
3. M-12 — Add client-side pagination to ApplicationsView

### Backlog
4-16. All remaining LOW and NITPICK items
