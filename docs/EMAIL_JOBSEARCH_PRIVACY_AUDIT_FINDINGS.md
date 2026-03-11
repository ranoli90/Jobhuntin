# Email, Job Search, and Privacy Audit Findings

**Generated:** 2026-03-11  
**Sources:** 3 sub-agent audits (Email/Communications, Job Search/Match, Data/Privacy)

---

## CRITICAL

| ID | Audit | File:Line | Description | Status |
|----|-------|-----------|-------------|--------|
| COM-001 | Email | auth.py:1333-1386 | Webhook accepts unauthenticated when RESEND_WEBHOOK_SECRET empty | fixed |
| COM-002 | Email | auth.py:1335-1370 | No Svix timestamp replay check | fixed |
| COM-003 | Email | email_communication_manager.py:436-443 | HTML injection in template rendering | fixed |
| COM-004 | Email | communications_endpoints.py:39-50, 156-175 | Arbitrary email sending to any address | fixed |
| F001 | Job | user.py:1416-1424 | _hydrate_job_matches does not pass user_id to search_and_list_jobs | fixed |
| F005 | Job | semantic_matching.py:261-262 | IndexError when tech_skills empty | fixed |
| F007 | Job | job_search.py:196-197, 206-208 | ILIKE wildcard injection | fixed |
| F002 | Job | match_feedback.py:141-159 | get_job_stats CROSS JOIN drops empty feedback_tags | fixed |
| F003 | Job | match_feedback.py:186 | compute_adjusted_match_score not in migrations | documented (fallback) |
| F004 | Job | match_score_precompute.py | Pre-computed scores never read | deferred |
| PRIV-001 | Privacy | gdpr.py:251-254 | GDPR status endpoint IDOR | fixed |
| PRIV-002 | Privacy | gdpr.py, ccpa.py | Resume files not deleted on user deletion | fixed |
| PRIV-003 | Privacy | gdpr.py, ccpa.py | Vector DB profile embeddings not removed on deletion | fixed |

---

## HIGH

| ID | Audit | File:Line | Description | Status |
|----|-------|-----------|-------------|--------|
| F006 | Job | vectordb.py:310-348 | PgVector fallback OOM on large tables | fixed |
| F008 | Job | vectordb.py:420-424 | Pinecone sync API in async methods | fixed |
| F009 | Job | job_search.py:146-155 | recently_matched sort same as match_score | fixed |
| F004 | Job | match_score_precompute.py | Pre-computed scores never read | fixed |
| PRIV-004 | Privacy | ccpa.py | CCPA data access returns limited fields | fixed |
| PRIV-005 | Privacy | gdpr.py | GDPR export vs deletion table mismatch | pending |
| PRIV-006 | Privacy | ccpa.py, main.py | CCPA router has no prefix | fixed |
| PRIV-007 | Privacy | data_retention.py:96-106 | Applications hard-deleted, not archived | deferred |
| PRIV-008 | Privacy | gdpr.py:181-212 | GDPR export returns raw data in response | deferred |

---

## MEDIUM (deferred for later)

COM-005, COM-006, COM-007, COM-008, COM-009; F010-F016; PRIV-009–PRIV-014

---

## Fix Order

1. COM-001, PRIV-001, F001 (security/correctness)
2. PRIV-002, PRIV-003 (deletion completeness)
3. COM-003, COM-004, COM-002 (email security)
4. F002, F003, F004, F005, F007 (job pipeline)
