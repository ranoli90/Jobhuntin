# Remaining Items — Full Sprint List

All outstanding items from the frontend quality audit, organized into sprints. No limit on scope.

**Status: Most items addressed.** See git history for implementation details.

---

## Sprint 1: Critical User-Facing Placeholders ✅

| # | Item | Location | Notes |
|---|------|----------|-------|
| 1.1 | **Team page** — "Coming soon" badge; no team members API | `AppLayout.tsx` L62, `TeamView.tsx` | TeamView shows "You (Owner)" + upgrade CTA; no real team members list. Need backend `me/team/members` or similar. |
| 1.2 | **Billing — Payment methods** | `Billing.tsx` L367 | "Payment methods feature coming soon" — placeholder section. |
| 1.3 | **Billing — Usage charts** | `Billing.tsx` L392 | "Usage charts coming soon" — placeholder section. |
| 1.4 | **Application Detail — Add Note** | `ApplicationDetailPage.tsx` L358 | "Notes feature coming soon" toast; should wire to `ux/notes` (notes API exists). |
| 1.5 | **JobNiche — Employer data** | `JobNiche.tsx` L640 | "Employer data coming soon for {city}" — placeholder for employer data. |
| 1.6 | **Social Login (Google/LinkedIn)** | `SocialLogin.tsx` L89–103 | Intentionally "Coming soon" and disabled. Product decision to enable when ready. |

---

## Sprint 2: Mock Data → Real API (User-Facing) ✅

| # | Item | Location | Notes |
|---|------|----------|-------|
| 2.1 | **BatchProcessor** — mock results, stats, user IDs | `BatchProcessor.tsx` L157–225 | Replace mock batch results, mock stats, mock user IDs with real API calls. |
| 2.2 | **UserInterests** — mock interaction history | `UserInterests.tsx` L157–193 | Replace `mockHistory` with real API. |
| 2.3 | **SemanticMatcher** — mock recommendations | `SemanticMatcher.tsx` L203–233 | Replace `mockRecommendations` with real API. |
| 2.4 | **NotificationCenter** — mock notifications | `NotificationCenter.tsx` L50–144 | Replace `mockNotifications` with `communications/notifications` or similar. |
| 2.5 | **CareerPath** — mock career data | `CareerPath.tsx` L45–169 | Replace `mockCareerData` with real API. |
| 2.6 | **Homepage** — dashboard mock | `Homepage.tsx` L565 | Comment: "Dashboard mock - more playful" — wire to real data if applicable. |

---

## Sprint 3: Admin / Internal Tools (Mock Data) ✅

| # | Item | Location | Notes |
|---|------|----------|-------|
| 3.1 | **Admin Alerts** — mockAlertsData | `admin/alerts.tsx` L39 | Replace with real API. |
| 3.2 | **Admin Matches** — mockMatchesData | `admin/matches.tsx` L45 | Replace with real API. |
| 3.3 | **Admin Usage** — mockUsageData | `admin/usage.tsx` L39 | Replace with real API. |

---

## Sprint 4: Application Export Pagination ✅

| # | Item | Location | Notes |
|---|------|----------|-------|
| 4.1 | **Application Export** — fetch all applications | `application-export/index.tsx`, `ApplicationExport.tsx` | `me/applications` returns max 25 (default limit). Export may miss apps. Add pagination loop or `limit=100` + multiple requests to fetch all. |
| 4.2 | **Backend** — optional `limit` param for export | `apps/api/user.py` | `list_applications` has `limit` max 100. Consider `?limit=1000` or dedicated export endpoint that returns all. |

---

## Sprint 5: Backend TODOs & Placeholders ✅

| # | Item | Location | Notes |
|---|------|----------|-------|
| 5.1 | **Billing** — concurrent_used | `billing.py` L175 | `"concurrent_used": 0  # TODO: Track concurrent usage` |
| 5.2 | **Resume integration** — template usage | `resume_integration.py` L482 | `# TODO: Implement actual template usage query` |
| 5.3 | **Voice interviews** — session retrieval | `voice_interviews.py` L286, L368 | `# TODO: Implement session retrieval from database` |
| 5.4 | **Enhanced notifications** — dashboard update | `enhanced_notifications.py` L575 | `# TODO: Implement dashboard update` |
| 5.5 | **Application export** — PDF format | `application_export.py` L345 | `Export to PDF format (placeholder implementation)` |
| 5.6 | **Application export** — scheduled export | `application_export.py` L484 | `# Placeholder for scheduled export functionality` |
| 5.7 | **Answer memory** — AI feedback | `answer_memory.py` L205, L631 | `# Generate AI feedback and score (placeholder)`, `# Placeholder implementation` |
| 5.8 | **Index analyzer** — placeholders | `index_analyzer.py` L1525, 1535, 1545 | `# For now, it's a placeholder` (x3) |
| 5.9 | **Database performance manager** — placeholders | `database_performance_manager.py` L1037, 1063, 1120 | Return placeholder instead of actual analysis. |
| 5.10 | **M4 metrics** — CAC placeholder | `m4_metrics.py` L53, L91 | `cac = 150  # placeholder — would come from marketing spend tracking` |
| 5.11 | **Multi-resume** — offer_rate placeholder | `multi_resume.py` L384 | `offer_rate = interview_rate * 0.3  # Placeholder` |
| 5.12 | **Connection pool manager** — placeholder configs | `connection_pool_manager.py` L451 | `# For now, we'll create placeholder configs` |
| 5.13 | **Contracts** — support ticket sentiment | `contracts.py` L109 | `Support ticket sentiment (0-10 pts, placeholder)` |

---

## Sprint 6: Dependency Injection / NotImplementedError ✅

| # | Item | Location | Notes |
|---|------|----------|-------|
| 6.1 | **user_experience_endpoints** — _get_pool, _get_tenant_ctx | `user_experience_endpoints.py` L54, L58 | `raise NotImplementedError("Pool dependency not injected")` — ensure DI is wired in main.py. |
| 6.2 | **billing** — _get_pool, _get_tenant_ctx | `billing.py` L53, L57 | Same pattern. |
| 6.3 | **auth** — _get_pool | `auth.py` L344 | Same pattern. |

---

## Sprint 7: Config & Environment Placeholders ✅

| # | Item | Location | Notes |
|---|------|----------|-------|
| 7.1 | **Stripe webhook secret** | `shared/config.py` L189 | `dev-placeholder-webhook-secret` — must be real in prod. |
| 7.2 | **Webhook signing secret** | `shared/config.py` L206 | `dev-placeholder-webhook-signing` — must be real in prod. |
| 7.3 | **App Store URL** | `shared/config.py` L278 | `idXXXXXXXXXX` — replace with real app ID. |
| 7.4 | **Browserless URL** | `shared/config.py` L247 | Empty = local Chromium; add token for remote. |
| 7.5 | **Setup monitoring** — Slack webhook | `scripts/setup_monitoring.py` L44 | `TXXX/BXXX/XXXX` — placeholder. |

---

## Sprint 8: Frontend MEDIUM/LOW Comments (Improvements) ✅

| # | Item | Location | Notes |
|---|------|----------|-------|
| 8.1 | **JobsView** — undo stack limit | `JobsView.tsx` L84 | `// MEDIUM: Limit undoStack size more aggressively` |
| 8.2 | **JobsView** — focus management after swipe | `JobsView.tsx` L118 | `// MEDIUM: Focus management after swipe - focus next card` |
| 8.3 | **JobsView** — live region for screen reader | `JobsView.tsx` L252, L284 | `// MEDIUM: Add live region for screen reader announcements` |
| 8.4 | **JobsView** — refs for timeout cleanup | `JobsView.tsx` L255 | `// MEDIUM: Refs for timeout cleanup` |
| 8.5 | **JobsView** — cleanup on unmount | `JobsView.tsx` L259 | `// MEDIUM: Cleanup state and timeouts on unmount` |
| 8.6 | **JobsView** — limit visible jobs | `JobsView.tsx` L362 | `// MEDIUM: Limit visible jobs to prevent memory issues` |
| 8.7 | **ApplicationDetailPage** — events timeline | `ApplicationDetailPage.tsx` L260 | `{/* LOW: Display Application Events Timeline with visual timeline */}` |
| 8.8 | **api/main** — error code extraction | `main.py` L1112 | `# MEDIUM: Extract error code from status code` |
| 8.9 | **api/main** — sanitize HTML/prompt injection | `main.py` L1309 | `# MEDIUM: Sanitize HTML and prompt injection in user input` |
| 8.10 | **api/main** — calculate_completeness | `main.py` L1540, L1674 | `# MEDIUM: Use centralized calculate_completeness()` instead of SQL increments` |
| 8.11 | **Worker agent** — stable selectors | `agent.py` L232 | `// MEDIUM: Prefer stable selectors (id, name) over nth-of-type` |
| 8.12 | **Worker agent** — screenshot storage | `agent.py` L1772 | `# MEDIUM: Implement screenshot storage using Supabase storage` |

---

## Sprint 9: Test & Mobile TODOs

| # | Item | Location | Notes |
|---|------|----------|-------|
| 9.1 | **test_critical_endpoints** | `tests/test_critical_endpoints.py` L282 | `pass  # TODO: Implement with proper error triggering` |
| 9.2 | **test_auth_flow** | `tests/test_auth_flow.py` L196 | `pass  # TODO: Implement with proper mocking` |
| 9.3 | **Mobile** — reCAPTCHA | `mobile/src/lib/supabase.ts` L78 | `TODO: Implement reCAPTCHA Enterprise Mobile SDK` |
| 9.4 | **Mobile** — deep link handling | `mobile/src/lib/supabase.ts` L251 | `TODO: Implement deep link handling for magic links` |

---

## Sprint 10: EmptyState & UI Polish

| # | Item | Location | Notes |
|---|------|----------|-------|
| 10.1 | **ComingSoonEmptyState** | `EmptyState.tsx` L272–281 | Generic "coming soon" component — ensure consistent usage. |
| 10.2 | **ButtonStyles** — xxxl size | `ButtonStyles.tsx` L65 | `xxxl: "p-16"` — verify usage or remove if unused. |
| 10.3 | **Main** — pg_notify placeholder | `main.py` L1942, L1970 | Placeholder for pg_notify push; worker polls regardless. |

---

## Sprint 11: SEO & Scripts

| # | Item | Location | Notes |
|---|------|----------|-------|
| 11.1 | **Automated ranking engine** — trending | `automated-ranking-engine.ts` L428 | `* Find trending opportunities (placeholder for real trend analysis)` |
| 11.2 | **Scrape competitor updates** | `scrape-competitor-updates.js` | Check for placeholders. |

---

## Sprint 12: Worker & Job Queue

| # | Item | Location | Notes |
|---|------|----------|-------|
| 12.1 | **job_queue_worker** — placeholder handlers | `job_queue_worker.py` L69 | `# Register placeholder handlers — extend as job types are added` |
| 12.2 | **job_queue_worker** — match score precompute | `job_queue_worker.py` L59 | `# LOW: Register match score pre-computation job handler` |

---

## Sprint 13: Domain-Specific Placeholders

| # | Item | Location | Notes |
|---|------|----------|-------|
| 13.1 | **job_search** — match score sorting | `job_search.py` L162 | `# MEDIUM: Optimize match score sorting for large datasets` |
| 13.2 | **match_score_precompute** | `match_score_precompute.py` L6 | `LOW: Performance optimization` |
| 13.3 | **interview_simulator** | `interview_simulator.py` L4 | "Asynchronous voice-interactive LLM mock interviews" — clarify mock vs real. |

---

## Summary Counts

| Sprint | Focus | Item Count |
|-------|-------|------------|
| 1 | Critical user-facing placeholders | 6 |
| 2 | Mock → real API (user-facing) | 6 |
| 3 | Admin mock data | 3 |
| 4 | Application export pagination | 2 |
| 5 | Backend TODOs & placeholders | 13 |
| 6 | Dependency injection | 3 |
| 7 | Config & environment | 5 |
| 8 | MEDIUM/LOW improvements | 12 |
| 9 | Test & mobile TODOs | 4 |
| 10 | EmptyState & UI polish | 3 |
| 11 | SEO & scripts | 2 |
| 12 | Worker & job queue | 2 |
| 13 | Domain-specific | 3 |
| **Total** | | **64** |

---

*Generated from codebase audit. Excludes: i18n placeholders (intentional), test mocks (expected), and form input placeholders (UX, not bugs).*
