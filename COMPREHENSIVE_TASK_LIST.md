# Comprehensive Task List - All Remaining Items + New Discoveries

**Date:** 2026-03-09  
**Status:** 60/65 Original Issues Fixed + 12 New Discoveries

---

## 📋 Remaining Original Issues (5 items)

### 1. Job Discovery: Add Virtualization for Large Job Lists
- **Priority:** Medium
- **Status:** Pending
- **Issue:** Memory leak risk with large job lists (100+ jobs)
- **Fix Required:**
  - Install: `npm install @tanstack/react-virtual`
  - Replace `visibleJobs.slice(0, 3).map()` with virtualized rendering
  - Only render visible cards + 1-2 buffer cards
- **Files:** `apps/web/src/pages/dashboard/JobsView.tsx`
- **Estimated Time:** 2-3 hours

### 2. Backend: Standardize Pagination Format
- **Priority:** Medium
- **Status:** Pending
- **Issue:** 8+ endpoints use different pagination formats (offset/limit, page/per_page, etc.)
- **Fix Required:**
  - Create shared `PaginatedResponse` model
  - Standardize on `offset/limit` format
  - Update all endpoints incrementally
- **Files:** 
  - `apps/api/user.py` (lines 163-250, 784-811)
  - `apps/api/job_details.py` (lines 97-104)
  - `apps/api/performance_metrics_endpoints.py`
  - `apps/api/screenshot_endpoints.py`
  - `apps/api/user_behavior_endpoints.py`
  - `apps/api/concurrent_usage_endpoints.py`
  - `apps/api/feedback_endpoints.py`
  - `apps/api/admin.py`
- **Estimated Time:** 6-8 hours

### 3. Dashboard: Add Timeline Visualization to Application Detail
- **Priority:** Low (Feature Enhancement)
- **Status:** Pending
- **Issue:** Application events exist but no visual timeline
- **Fix Required:**
  - Add timeline component (vertical timeline with events)
  - Show event types with icons
  - Group by date
- **Files:** `apps/web/src/pages/app/ApplicationDetailPage.tsx`
- **Estimated Time:** 3-4 hours

### 4. Dashboard: Add Notes/Annotations to Application Detail
- **Priority:** Low (Feature Enhancement)
- **Status:** Pending
- **Issue:** Users can't add notes to applications
- **Fix Required:**
  - Add notes table/field to database
  - Add UI for creating/editing notes
  - Display notes in Application Detail page
- **Files:** 
  - Database migration needed
  - `apps/web/src/pages/app/ApplicationDetailPage.tsx`
  - `apps/api/main.py` (add endpoint)
- **Estimated Time:** 4-5 hours

### 5. Dashboard: Add Payment Methods & Usage Charts to Billing
- **Priority:** Low (Feature Enhancement)
- **Status:** Pending
- **Issue:** Billing page missing payment methods management and usage visualization
- **Fix Required:**
  - Add payment methods UI (Stripe integration)
  - Add usage charts (applications over time, etc.)
  - Add billing history
- **Files:** `apps/web/src/pages/app/Billing.tsx`
- **Estimated Time:** 6-8 hours

---

## 🔍 New Discoveries While Working (12 items)

### Critical Issues Discovered

#### 1. TypeScript Error: Dashboard.tsx JSX Structure Issue
- **Priority:** High (Blocks Build)
- **Status:** Pending
- **Issue:** TypeScript reports missing closing tag for `<main>` element
- **Error:** `TS17008: JSX element 'main' has no corresponding closing tag`
- **Location:** `apps/web/src/pages/Dashboard.tsx:442`
- **Details:** 
  - Line 442 opens `<main>` tag
  - Line 1880 has `</main>` but TypeScript doesn't recognize it
  - Likely a JSX structure issue (nested elements, conditional rendering)
- **Fix Required:**
  - Review JSX structure between lines 442-1880
  - Ensure all opening tags have matching closing tags
  - Check for unclosed conditional renders
- **Files:** `apps/web/src/pages/Dashboard.tsx`
- **Estimated Time:** 30 minutes - 1 hour

#### 2. Embedding Cache Integration Incomplete
- **Priority:** Medium
- **Status:** Partially Fixed
- **Issue:** `compute_match_score` accepts `db_conn` parameter but callers don't pass it
- **Location:** `packages/backend/domain/semantic_matching.py:150`
- **Details:**
  - Added `db_conn` parameter to `compute_match_score()`
  - But all callers need to be updated to pass database connection
  - Cache won't work until callers are updated
- **Found Callers:**
  - `apps/api/ai.py:704` - `compute_match_score()` call
  - `apps/api/ai.py:813` - `compute_match_score()` call
  - Need to check for other callers
- **Fix Required:**
  - Update all callers to pass `db_conn` parameter
  - Ensure database connection is available in calling context
  - Test cache hit/miss behavior
- **Files:** 
  - `packages/backend/domain/semantic_matching.py`
  - `apps/api/ai.py` (lines 704, 813)
  - Search for other callers
- **Estimated Time:** 2-3 hours

#### 3. setTimeout Cleanup Issue in JobsView
- **Priority:** Medium
- **Status:** Partially Fixed
- **Issue:** setTimeout in error handler can't be cleaned up properly
- **Location:** `apps/web/src/pages/dashboard/JobsView.tsx:88, 107`
- **Details:**
  - Two setTimeout calls: one for focus management (line 88), one for navigation (line 107)
  - setTimeout is inside `handleSwipe` callback (not useEffect)
  - Can't use useEffect cleanup pattern
  - Navigation will occur even if component unmounts
- **Fix Required:**
  - Use `useRef` to store timeout IDs
  - Clear timeouts in component cleanup useEffect
  - Check if component is still mounted before navigation
- **Files:** `apps/web/src/pages/dashboard/JobsView.tsx`
- **Estimated Time:** 30 minutes

### Medium Priority Issues

#### 4. Missing Import: field_validator in main.py
- **Priority:** Medium
- **Status:** Fixed (but verify)
- **Issue:** Added `field_validator` import but need to verify it's used correctly
- **Location:** `apps/api/main.py:45`
- **Fix Required:** Verify all validators work correctly
- **Estimated Time:** 15 minutes

#### 5. Ruff Linting Issues
- **Priority:** Low
- **Status:** Pending
- **Issue:** Several linting issues found:
  - Blank line contains whitespace (line 114)
  - Line too long (line 119, 106 > 88 chars)
- **Location:** `apps/api/main.py`
- **Additional Issues:**
  - May have more linting issues across codebase
  - Should run full `ruff check` after fixes
- **Fix Required:**
  - Remove whitespace from blank lines
  - Break long lines
  - Run `ruff check . --select E,W,F,I` and fix all issues
- **Files:** `apps/api/main.py` (and potentially others)
- **Estimated Time:** 30 minutes - 1 hour

#### 6. Screenshot Storage Import Error Handling
- **Priority:** Medium
- **Status:** Partially Fixed
- **Issue:** Screenshot storage uses `upload_to_supabase_storage` but import might fail
- **Location:** `apps/worker/agent.py:1307`
- **Details:**
  - Import is inside try/except but error handling could be better
  - Should verify storage service is available
- **Fix Required:**
  - Add better error handling
  - Verify storage service availability
  - Add fallback storage mechanism
- **Files:** `apps/worker/agent.py`
- **Estimated Time:** 1 hour

#### 7. Profile Completeness: SQL Updates Still Exist
- **Priority:** Medium
- **Status:** Partially Fixed
- **Issue:** Fixed calculation logic but SQL-based increments still exist
- **Location:** `apps/api/main.py` (lines 1361, 1483)
- **Details:**
  - Lines 1361 and 1483 have SQL UPDATE statements that modify `profile_completeness`
  - These bypass the centralized `calculate_completeness()` function
  - Risk of inconsistency and scores > 100%
- **Fix Required:**
  - Replace SQL UPDATE with calls to `calculate_completeness()`
  - Use the function result to update the database
- **Files:** `apps/api/main.py` (lines 1361, 1483)
- **Estimated Time:** 1-2 hours

#### 8. Match Score Pre-computation Not Implemented
- **Priority:** Low (Performance Optimization)
- **Status:** Pending
- **Issue:** Match scores computed on-demand, should be pre-computed and cached
- **Location:** `packages/backend/domain/job_search.py:143`
- **Details:**
  - Added comment about pre-computation but not implemented
  - For 5000+ users, on-demand computation will be slow
- **Fix Required:**
  - Add background job to pre-compute match scores
  - Store in `job_match_cache` table
  - Use cached scores in queries
- **Files:** 
  - `packages/backend/domain/job_search.py`
  - New background job needed
- **Estimated Time:** 4-6 hours

### Low Priority Issues

#### 9. Edge Cases: Null Checks Before DB Operations
- **Priority:** Medium
- **Status:** Pending
- **Issue:** Some database operations might not check for null values
- **Details:** Requires systematic review
- **Fix Required:**
  - Review all database operations
  - Add null checks where needed
  - Add validation before DB writes
- **Estimated Time:** 4-6 hours

#### 10. Edge Cases: Resource Leaks
- **Priority:** Medium
- **Status:** Partially Fixed
- **Issue:** Browser cleanup implemented but other resources might leak
- **Details:**
  - Browser contexts: Fixed
  - DB connections: Need to verify all are properly closed
  - File handles: Need to verify
- **Fix Required:**
  - Audit all resource usage (connections, files, etc.)
  - Ensure proper cleanup in finally blocks
- **Estimated Time:** 3-4 hours

#### 11. Edge Cases: Circuit Breakers
- **Priority:** Medium
- **Status:** Pending
- **Issue:** No circuit breakers for external API calls
- **Details:**
  - OpenRouter API calls
  - Email service calls
  - Storage service calls
- **Fix Required:**
  - Implement circuit breaker pattern
  - Add to external service calls
  - Add fallback mechanisms
- **Files:** 
  - `packages/backend/domain/llm_client.py`
  - `apps/api/auth.py` (email service)
  - `packages/backend/domain/resume.py` (storage)
- **Estimated Time:** 4-6 hours

#### 12. Onboarding Session Persistence Still TODO
- **Priority:** High (Security)
- **Status:** Pending
- **Issue:** Sessions are in-memory, authorization checks are placeholders
- **Location:** `apps/api/ai_onboarding.py:202`
- **Details:**
  - `_verify_session_ownership` has TODO comment (line 202)
  - Sessions not persisted to database
  - Authorization checks are basic validation only
  - Security risk: users could potentially access other users' sessions
- **Fix Required:**
  - Create `onboarding_sessions` table migration
  - Persist sessions to database (session_id, user_id, tenant_id, state, created_at, updated_at)
  - Implement proper ownership verification in `_verify_session_ownership`
  - Update all session endpoints to use database
  - Add session expiration/cleanup
- **Files:** 
  - New migration: `migrations/017_onboarding_sessions.sql`
  - `apps/api/ai_onboarding.py`
  - `packages/backend/domain/ai_onboarding.py`
- **Estimated Time:** 4-6 hours

#### 13. Portfolio File Handling TODO
- **Priority:** Low
- **Status:** Pending
- **Issue:** Portfolio file handling not implemented
- **Location:** `apps/worker/agent.py:1296`
- **Details:**
  - `_get_portfolio_path()` returns None
  - Portfolio files mentioned in form fields but not handled
- **Fix Required:**
  - Implement portfolio file retrieval from user profile/storage
  - Add portfolio file upload support
  - Integrate with form filling
- **Files:** `apps/worker/agent.py`
- **Estimated Time:** 2-3 hours

#### 14. Other Document Type Handling TODO
- **Priority:** Low
- **Status:** Pending
- **Issue:** Other document types not handled
- **Location:** `apps/worker/agent.py:1302`
- **Details:**
  - `_get_document_path()` returns None
  - Documents like cover letters, certificates, etc. not handled
- **Fix Required:**
  - Implement document type detection
  - Add document retrieval from storage
  - Integrate with form filling
- **Files:** `apps/worker/agent.py`
- **Estimated Time:** 2-3 hours

---

## 📊 Summary

### Total Remaining Tasks: 17
- **Original Issues:** 5
- **New Discoveries:** 12

### Priority Breakdown:
- **Critical/High:** 3 (TypeScript error, embedding cache, onboarding persistence)
- **Medium:** 8 (various fixes and improvements)
- **Low:** 6 (feature enhancements, optimizations)

### Estimated Total Time: 40-55 hours

### Immediate Action Items (Blocking/High Priority):
1. 🔴 **Fix TypeScript error in Dashboard.tsx** (blocks build) - 30 min - 1 hour
2. 🔴 **Complete embedding cache integration** (pass db_conn) - 2-3 hours
3. 🔴 **Implement onboarding session persistence** (security) - 4-6 hours
4. 🟡 **Fix SQL-based completeness updates** (data consistency) - 1-2 hours
5. 🟡 **Fix setTimeout cleanup** (memory leak) - 30 minutes

### Next Phase (Medium Priority):
4. Add virtualization for job lists
5. Standardize pagination format
6. Fix setTimeout cleanup
7. Add null checks and resource leak fixes
8. Implement circuit breakers

### Future Enhancements (Low Priority):
9. Dashboard timeline visualization
10. Notes/annotations feature
11. Billing page enhancements
12. Match score pre-computation

---

## 🎯 Recommended Execution Order

### Week 1 (Critical):
1. Fix TypeScript error (1 hour)
2. Complete embedding cache integration (2-3 hours)
3. Implement onboarding session persistence (4-6 hours)

### Week 2 (High Priority):
4. Fix setTimeout cleanup (30 min)
5. Add null checks (4-6 hours)
6. Fix resource leaks (3-4 hours)
7. Add virtualization (2-3 hours)

### Week 3 (Medium Priority):
8. Standardize pagination (6-8 hours)
9. Implement circuit breakers (4-6 hours)
10. Fix screenshot storage error handling (1 hour)
11. Remove SQL-based completeness updates (1-2 hours)

### Week 4+ (Enhancements):
12. Dashboard timeline (3-4 hours)
13. Notes feature (4-5 hours)
14. Billing enhancements (6-8 hours)
15. Match score pre-computation (4-6 hours)

---

**All tasks are documented and ready for execution. Critical items should be addressed before production deployment.**
