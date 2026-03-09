# Analytics Audit - Executive Summary

## Quick Stats
- **Total Missing Events**: 50+ critical tracking events
- **Performance Metrics**: 0% coverage (no latency tracking)
- **Error Tracking**: 50% coverage (backend only, no frontend)
- **Funnel Tracking**: Infrastructure exists but 0% utilization
- **Business Metrics**: Partial (dashboards exist but no real-time tracking)

---

## Top 5 Critical Gaps

### 1. 🔴 Magic Link Flow - No Tracking
**Impact**: Cannot measure signup conversion rate
- Missing: `magic_link_sent`, `magic_link_opened`, `magic_link_verified`, `magic_link_failed`
- **Fix**: Add tracking in `apps/web/src/pages/Login.tsx` and `apps/api/auth.py`

### 2. 🔴 Onboarding Funnel - Incomplete
**Impact**: Cannot identify drop-off points or optimize onboarding
- Missing: Step-by-step tracking, time-to-complete, abandonment reasons
- **Fix**: Integrate `funnelTracker` into `apps/web/src/pages/app/Onboarding.tsx`

### 3. 🔴 API Performance - No Metrics
**Impact**: Cannot identify slow endpoints or performance regressions
- Missing: All endpoint latency tracking
- **Fix**: Add middleware in `apps/api/main.py` to track all requests

### 4. 🔴 Frontend Errors - Not Tracked
**Impact**: Cannot debug production frontend issues
- Missing: Sentry initialization in frontend
- **Fix**: Initialize Sentry in `apps/web/src/main.tsx`

### 5. 🔴 Application Funnel - Cannot Track Conversion
**Impact**: Cannot measure application success rate or optimize flow
- Missing: `application_started`, `application_submitted`, `application_failed`
- **Fix**: Add tracking in job swipe and application submission flows

---

## Missing Tracking Events by Priority

### 🔴 Critical (Blocking Business Metrics)
1. `magic_link_sent` - Backend sends but frontend doesn't track
2. `magic_link_verified` - Authentication success
3. `onboarding_started` - Funnel entry point
4. `onboarding_step_viewed` - Each step tracking
5. `job_application_started` - When user swipes right
6. `job_application_submitted` - Backend completion
7. `application_status_changed` - Status updates
8. `session_started` / `session_ended` - User engagement

### 🟡 High (Important for Optimization)
9. `resume_upload_started` / `resume_upload_failed`
10. `resume_parsed_success` / `resume_parsed_failed`
11. `job_card_viewed` - Impression tracking
12. `job_details_opened`
13. `filter_applied` - Search/filter usage
14. `payment_started` / `payment_completed` / `payment_failed`
15. `dashboard_viewed` - Feature usage

### 🟢 Medium (Nice to Have)
16. `job_saved` / `job_unsaved`
17. `job_share`
18. `ai_suggestion_used`
19. `feature_discovery` - First use of features
20. `subscription_cancelled` / `subscription_renewed`

---

## Performance Metrics Missing

### Backend
- ❌ API endpoint latency (p50, p95, p99)
- ❌ Database query time
- ❌ External API call time (LLM, job boards, email)
- ❌ Request count by endpoint
- ❌ Error rate by endpoint

### Frontend
- ❌ Page load time
- ❌ Time to Interactive (TTI)
- ❌ First Contentful Paint (FCP)
- ❌ Largest Contentful Paint (LCP)
- ❌ Cumulative Layout Shift (CLS)
- ❌ First Input Delay (FID)

---

## Business Metrics Missing

### User Metrics
- ❌ Daily/Weekly/Monthly Active Users
- ❌ User retention (Day 1, Day 7, Day 30)
- ❌ User lifetime value (LTV)
- ❌ User acquisition cost (CAC)

### Conversion Metrics
- ❌ Visitor → Signup conversion rate
- ❌ Signup → First Application activation rate
- ❌ Application → Interview conversion rate
- ❌ Interview → Offer conversion rate

### Revenue Metrics
- ❌ Monthly Recurring Revenue (MRR)
- ❌ Annual Recurring Revenue (ARR)
- ❌ Churn rate
- ❌ Net Revenue Retention (NRR)
- ❌ LTV:CAC ratio

---

## Quick Wins (Can Implement Today)

### 1. Add Magic Link Tracking (30 min)
```typescript
// apps/web/src/pages/Login.tsx - After magic link request
telemetry.track("magic_link_sent", { 
  email: maskedEmail, 
  source: "login_page",
  timestamp: Date.now()
});
```

### 2. Add API Latency Middleware (1 hour)
```python
# apps/api/main.py
@app.middleware("http")
async def track_latency(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    metrics.observe("api.request.duration", duration, {
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code
    })
    return response
```

### 3. Initialize Frontend Sentry (15 min)
```typescript
// apps/web/src/main.tsx
import * as Sentry from "@sentry/react";
if (import.meta.env.PROD) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [new Sentry.BrowserTracing()],
    tracesSampleRate: 0.1,
  });
}
```

### 4. Add Onboarding Step Tracking (1 hour)
```typescript
// apps/web/src/pages/app/Onboarding.tsx
useEffect(() => {
  telemetry.track("onboarding_step_viewed", {
    step: currentStep,
    step_number: stepIndex,
    user_id: profile?.id
  });
}, [currentStep]);
```

### 5. Track Job Application Events (1 hour)
```typescript
// apps/web/src/pages/Dashboard.tsx - In handleSwipe
if (direction === "ACCEPT") {
  telemetry.track("job_application_started", {
    job_id: swipedJob.id,
    company: swipedJob.company,
    user_id: user?.id
  });
}
```

---

## Files That Need Updates

### Frontend
- `apps/web/src/pages/Login.tsx` - Add magic link tracking
- `apps/web/src/pages/app/Onboarding.tsx` - Add step tracking
- `apps/web/src/pages/Dashboard.tsx` - Add application tracking
- `apps/web/src/main.tsx` - Initialize Sentry
- `apps/web/src/lib/telemetry.ts` - Add event validation

### Backend
- `apps/api/main.py` - Add latency middleware
- `apps/api/auth.py` - Add magic link sent tracking
- `shared/metrics.py` - Already good, just needs usage
- `apps/api/analytics.py` - Already good

---

## Estimated Implementation Time

- **Critical Items**: 8-12 hours
- **High Priority**: 16-24 hours
- **Medium Priority**: 24-32 hours
- **Total**: 48-68 hours (1-2 sprints)

---

## Success Metrics

After implementation, you should be able to answer:
- ✅ What's our signup conversion rate?
- ✅ Where do users drop off in onboarding?
- ✅ What's our application success rate?
- ✅ Which API endpoints are slow?
- ✅ What's our Day 1, Day 7, Day 30 retention?
- ✅ What's our MRR and churn rate?
- ✅ Which features are most used?
- ✅ What errors are users experiencing?

---

## Next Steps

1. **Review this audit** with product/engineering team
2. **Prioritize** based on business goals
3. **Create tickets** for each item
4. **Start with critical items** (magic link, onboarding, API latency)
5. **Set up dashboards** to visualize new metrics
6. **Iterate** based on data insights
