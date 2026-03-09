# Data & Analytics Audit Report

**Date:** March 9, 2026  
**Scope:** Tracking, Metrics, Logging, and Observability  
**Status:** ⚠️ **Critical Gaps Identified**

---

## Executive Summary

The codebase has foundational analytics infrastructure (telemetry, metrics, logging) but is missing critical tracking events, performance monitoring, and business metrics. Key user journeys cannot be fully tracked, making conversion optimization and product decisions difficult.

**Overall Health:** 🟡 **Moderate** - Infrastructure exists but underutilized

---

## 1. Frontend Tracking (`apps/web/src/lib/telemetry.ts`)

### ✅ What's Working
- Google Analytics integration via `gtag`
- GDPR-compliant cookie consent check
- Development mode console logging
- Basic error handling

### ❌ Critical Gaps

#### Missing Tracking Events (High Priority)
1. **Magic Link Flow**
   - ✅ `login_magic_link_requested` - EXISTS
   - ❌ `magic_link_sent` - MISSING (backend sends but not tracked)
   - ❌ `magic_link_opened` - MISSING (when user clicks link)
   - ❌ `magic_link_verified` - MISSING (successful authentication)
   - ❌ `magic_link_expired` - MISSING (expired token attempts)
   - ❌ `magic_link_failed` - MISSING (verification failures)

2. **Onboarding Funnel**
   - ✅ `onboarding_completed` - EXISTS
   - ✅ `AI Learned Work Style` - EXISTS (but inconsistent naming)
   - ✅ `AI Learned Resume Data` - EXISTS (but inconsistent naming)
   - ❌ `onboarding_started` - MISSING (first step entry)
   - ❌ `onboarding_step_viewed` - MISSING (each step view)
   - ❌ `onboarding_step_abandoned` - MISSING (drop-off tracking)
   - ❌ `resume_upload_started` - MISSING
   - ❌ `resume_upload_failed` - MISSING
   - ❌ `resume_parsed_success` - MISSING
   - ❌ `resume_parsed_failed` - MISSING
   - ❌ `onboarding_time_to_complete` - MISSING (duration metric)

3. **Job Swipe/Application Flow**
   - ✅ `job_swipe` - EXISTS (but only direction, missing context)
   - ❌ `job_card_viewed` - MISSING (impression tracking)
   - ❌ `job_details_opened` - MISSING
   - ❌ `job_application_started` - MISSING (when user swipes right)
   - ❌ `job_application_submitted` - MISSING (backend completes)
   - ❌ `job_application_failed` - MISSING
   - ❌ `job_saved` - MISSING
   - ❌ `job_unsaved` - MISSING
   - ❌ `job_share` - MISSING

4. **Application Tracking**
   - ✅ `application_viewed` - EXISTS
   - ❌ `application_status_changed` - MISSING (frontend doesn't track)
   - ❌ `application_hold_questions_shown` - MISSING
   - ❌ `application_hold_answered` - MISSING
   - ❌ `application_follow_up_clicked` - MISSING

5. **Feature Usage**
   - ❌ `dashboard_viewed` - MISSING
   - ❌ `jobs_tab_viewed` - MISSING
   - ❌ `applications_tab_viewed` - MISSING
   - ❌ `settings_viewed` - MISSING
   - ❌ `billing_viewed` - MISSING
   - ❌ `ai_suggestion_used` - MISSING
   - ❌ `filter_applied` - MISSING
   - ❌ `search_performed` - MISSING

6. **Conversion Events**
   - ✅ `upgrade_clicked` - EXISTS
   - ✅ `add_seats_clicked` - EXISTS
   - ❌ `pricing_page_viewed` - MISSING
   - ❌ `payment_started` - MISSING
   - ❌ `payment_completed` - MISSING
   - ❌ `payment_failed` - MISSING
   - ❌ `subscription_cancelled` - MISSING
   - ❌ `subscription_renewed` - MISSING

7. **User Engagement**
   - ❌ `session_started` - MISSING
   - ❌ `session_ended` - MISSING
   - ❌ `daily_active_user` - MISSING
   - ❌ `return_visit` - MISSING
   - ❌ `feature_discovery` - MISSING (first use of features)

### Issues with Existing Events
- **Inconsistent naming**: Mix of snake_case (`login_magic_link_requested`) and Title Case (`AI Learned Work Style`)
- **Missing context**: Events lack important metadata (user_id, session_id, timestamp often missing)
- **No event validation**: No schema validation for event properties
- **No event batching**: Each event sent individually (inefficient)

---

## 2. Backend Metrics (`shared/metrics.py`)

### ✅ What's Working
- In-process metrics storage (counters, observations, gauges)
- OpenTelemetry integration support
- Rate limiter metrics
- Basic counter increments (`incr()`)

### ❌ Critical Gaps

#### Missing Performance Metrics
1. **API Latency Tracking**
   - ❌ No `observe()` calls for endpoint latency
   - ❌ No p50/p95/p99 latency tracking
   - ❌ No request duration metrics
   - **Impact**: Cannot identify slow endpoints or performance regressions

2. **Database Performance**
   - ❌ No query latency tracking
   - ❌ No connection pool metrics
   - ❌ No slow query detection

3. **External Service Latency**
   - ❌ No LLM API latency tracking
   - ❌ No job board scraping latency
   - ❌ No email service latency
   - ❌ No storage service latency

#### Missing Business Metrics
1. **User Metrics**
   - ❌ No daily/weekly/monthly active users
   - ❌ No user retention cohorts
   - ❌ No user lifetime value tracking

2. **Application Metrics**
   - ❌ No applications per user
   - ❌ No application success rate
   - ❌ No time-to-application metric

3. **Revenue Metrics**
   - ❌ No MRR/ARR tracking via metrics
   - ❌ No conversion rate tracking
   - ❌ No churn rate tracking

#### Underutilized Metrics
- `observe()` function exists but **never used** in codebase
- `gauge()` function exists but **rarely used**
- Most metrics are simple counters (`incr()`)

**Recommendation**: Add middleware to automatically track all API endpoint latencies.

---

## 3. Logging (`shared/logging_config.py`)

### ✅ What's Working
- Structured JSON logging for production
- Human-readable logging for development
- Context correlation (user_id, job_id, application_id, tenant_id)
- PII sanitization (email, phone, names automatically redacted)
- Log levels properly configured

### ❌ Critical Gaps

#### Missing Context
1. **Request Context**
   - ❌ No request ID in all logs (only some endpoints)
   - ❌ No IP address logging (for security)
   - ❌ No user agent logging
   - ❌ No session ID in logs

2. **Error Context**
   - ❌ Errors logged but not enriched with user context
   - ❌ No error fingerprinting for grouping
   - ❌ No stack trace correlation with user actions

3. **Performance Context**
   - ❌ No timing information in logs
   - ❌ No slow operation warnings

#### Logging Gaps
- Many error paths use `logger.error()` but don't include enough context
- No structured error logging format (should include error_code, error_type)
- Missing correlation between frontend errors and backend logs

---

## 4. Error Tracking

### ✅ What's Working
- Sentry integration configured in `apps/api/main.py`
- Error boundary component exists (`ErrorBoundary.tsx`)
- Basic error logging

### ❌ Critical Gaps

1. **Frontend Error Tracking**
   - ❌ Sentry not initialized in frontend (only backend)
   - ❌ JavaScript errors not sent to Sentry
   - ❌ React error boundaries don't report to Sentry
   - ❌ Unhandled promise rejections not tracked

2. **Error Context**
   - ❌ Errors lack user context (user_id, session_id)
   - ❌ Errors lack request context (endpoint, method, params)
   - ❌ No error severity classification

3. **Error Monitoring**
   - ❌ No error rate alerts
   - ❌ No error trend analysis
   - ❌ No error grouping/fingerprinting

---

## 5. Performance Monitoring

### ❌ Critical Gaps

1. **Frontend Performance**
   - ❌ No page load time tracking
   - ❌ No Time to Interactive (TTI) tracking
   - ❌ No First Contentful Paint (FCP) tracking
   - ❌ No Largest Contentful Paint (LCP) tracking
   - ❌ No Cumulative Layout Shift (CLS) tracking
   - ❌ No Web Vitals tracking
   - **Note**: `PerformanceMonitor.tsx` exists but appears incomplete

2. **Backend Performance**
   - ❌ No endpoint response time tracking
   - ❌ No database query time tracking
   - ❌ No external API call time tracking
   - ❌ No memory usage tracking
   - ❌ No CPU usage tracking

3. **Real User Monitoring (RUM)**
   - ❌ No real user performance data
   - ❌ No geographic performance breakdown
   - ❌ No device/browser performance breakdown

---

## 6. Business Metrics & Funnels

### ✅ What's Working
- Funnel tracking infrastructure exists (`funnelTracking.ts`)
- Analytics events endpoint (`/analytics/events`)
- Some business dashboards (M1-M6) exist

### ❌ Critical Gaps

1. **Incomplete Funnels**
   - **Onboarding Funnel**: Missing entry point, step-by-step tracking
   - **Application Funnel**: Cannot track conversion from swipe → application → interview → offer
   - **Conversion Funnel**: Cannot track visitor → signup → onboarding → paid
   - **Retention Funnel**: Cannot track daily/weekly/monthly retention

2. **Missing Business Metrics**
   - ❌ Conversion rate (visitor → signup)
   - ❌ Activation rate (signup → first application)
   - ❌ Retention rate (day 1, day 7, day 30)
   - ❌ Churn rate
   - ❌ Net Revenue Retention (NRR)
   - ❌ Customer Lifetime Value (LTV)
   - ❌ Customer Acquisition Cost (CAC)
   - ❌ LTV:CAC ratio

3. **Funnel Tracking Not Used**
   - `funnelTracking.ts` exists but **not integrated** into key flows
   - Onboarding doesn't use funnel tracker
   - Application flow doesn't use funnel tracker
   - Pricing/upgrade flow doesn't use funnel tracker

---

## 7. A/B Testing & Experimentation

### ✅ What's Working
- A/B test assignment tracking exists (`useOnboarding.ts`)
- Experiment readout endpoint exists (`/admin/experiments/{key}/results`)

### ❌ Critical Gaps

1. **Missing Experiment Tracking**
   - ❌ No experiment assignment tracking in backend
   - ❌ No variant performance comparison
   - ❌ No statistical significance testing
   - ❌ No experiment graduation logic

2. **Missing A/B Test Events**
   - ❌ No `experiment_assigned` event
   - ❌ No `experiment_conversion` event
   - ❌ No `experiment_exposure` event

---

## 8. User Behavior Analytics

### ❌ Critical Gaps

1. **Session Analytics**
   - ❌ No session duration tracking
   - ❌ No page views per session
   - ❌ No bounce rate tracking
   - ❌ No session replay capability

2. **User Journey Tracking**
   - ❌ Cannot track user paths through the app
   - ❌ No heatmap data
   - ❌ No click tracking
   - ❌ No scroll depth tracking

3. **Feature Adoption**
   - ❌ No feature usage tracking
   - ❌ No feature discovery tracking
   - ❌ No feature abandonment tracking

---

## Priority Recommendations

### 🔴 **Critical (Implement Immediately)**

1. **Add Magic Link Tracking**
   ```typescript
   // In apps/web/src/pages/Login.tsx
   telemetry.track("magic_link_sent", { email, source });
   telemetry.track("magic_link_verified", { success: true });
   ```

2. **Add Onboarding Step Tracking**
   ```typescript
   // Track each onboarding step
   telemetry.track("onboarding_step_viewed", { 
     step: currentStep, 
     step_number: stepIndex,
     time_on_previous_step: duration 
   });
   ```

3. **Add API Latency Middleware**
   ```python
   # In apps/api/main.py
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

4. **Initialize Frontend Error Tracking**
   ```typescript
   // In apps/web/src/main.tsx or App.tsx
   import * as Sentry from "@sentry/react";
   Sentry.init({
     dsn: import.meta.env.VITE_SENTRY_DSN,
     integrations: [new Sentry.BrowserTracing()],
     tracesSampleRate: 0.1,
   });
   ```

### 🟡 **High Priority (Implement This Sprint)**

5. **Complete Application Funnel Tracking**
   - Track job swipe → application started → application submitted → status changes
   - Add conversion events at each step

6. **Add Performance Metrics**
   - Implement Web Vitals tracking
   - Add API endpoint latency tracking
   - Track database query times

7. **Integrate Funnel Tracker**
   - Use `funnelTracker` in onboarding flow
   - Use `funnelTracker` in application flow
   - Use `funnelTracker` in pricing flow

8. **Add Business Metrics**
   - Track daily/weekly/monthly active users
   - Track conversion rates
   - Track retention cohorts

### 🟢 **Medium Priority (Next Sprint)**

9. **Standardize Event Naming**
   - Use consistent snake_case for all events
   - Create event schema/types
   - Add event validation

10. **Add User Behavior Analytics**
    - Session tracking
    - Feature usage tracking
    - User journey mapping

11. **Enhance Error Tracking**
    - Add error context
    - Add error grouping
    - Set up error alerts

---

## Implementation Checklist

### Frontend Tracking
- [ ] Add magic link flow events (sent, opened, verified, failed)
- [ ] Add onboarding step-by-step tracking
- [ ] Add job application funnel events
- [ ] Add feature usage tracking
- [ ] Add conversion event tracking
- [ ] Standardize event naming (snake_case)
- [ ] Add event schema validation
- [ ] Initialize Sentry for frontend
- [ ] Add Web Vitals tracking
- [ ] Integrate funnelTracker into key flows

### Backend Metrics
- [ ] Add API latency middleware
- [ ] Add database query time tracking
- [ ] Add external service latency tracking
- [ ] Add business metrics (DAU, retention, conversion)
- [ ] Use `observe()` for latency metrics
- [ ] Use `gauge()` for current state metrics
- [ ] Add performance alerts

### Logging
- [ ] Add request ID to all logs
- [ ] Add session ID to logs
- [ ] Add structured error logging
- [ ] Add performance timing to logs
- [ ] Correlate frontend/backend logs

### Error Tracking
- [ ] Initialize Sentry in frontend
- [ ] Add error context (user_id, session_id)
- [ ] Add error grouping/fingerprinting
- [ ] Set up error alerts
- [ ] Track unhandled promise rejections

### Business Metrics
- [ ] Track conversion rates
- [ ] Track retention cohorts
- [ ] Track LTV, CAC, NRR
- [ ] Complete funnel tracking
- [ ] Add A/B test conversion tracking

---

## Metrics to Add

### Performance Metrics
- `api.request.duration` (histogram) - API endpoint latency
- `api.request.count` (counter) - Request count by endpoint
- `db.query.duration` (histogram) - Database query time
- `external_api.duration` (histogram) - External API call time
- `page.load.time` (histogram) - Frontend page load time
- `web.vitals.lcp` (histogram) - Largest Contentful Paint
- `web.vitals.fid` (histogram) - First Input Delay
- `web.vitals.cls` (histogram) - Cumulative Layout Shift

### Business Metrics
- `user.daily_active` (gauge) - Daily active users
- `user.weekly_active` (gauge) - Weekly active users
- `user.monthly_active` (gauge) - Monthly active users
- `conversion.signup_rate` (gauge) - Visitor to signup rate
- `conversion.activation_rate` (gauge) - Signup to first application rate
- `conversion.retention_day1` (gauge) - Day 1 retention
- `conversion.retention_day7` (gauge) - Day 7 retention
- `conversion.retention_day30` (gauge) - Day 30 retention
- `revenue.mrr` (gauge) - Monthly Recurring Revenue
- `revenue.arr` (gauge) - Annual Recurring Revenue
- `revenue.churn_rate` (gauge) - Monthly churn rate

### Feature Usage Metrics
- `feature.job_swipe.used` (counter) - Job swipe feature usage
- `feature.application.used` (counter) - Application feature usage
- `feature.ai_suggestion.used` (counter) - AI suggestion usage
- `feature.resume_upload.used` (counter) - Resume upload usage

---

## Conclusion

The analytics infrastructure is **foundational but incomplete**. Critical user journeys cannot be fully tracked, making it difficult to:
- Optimize conversion rates
- Identify drop-off points
- Measure feature adoption
- Track business metrics
- Debug performance issues
- Monitor error rates

**Immediate action required** on critical items (magic link tracking, onboarding funnel, API latency) to enable data-driven product decisions.
