# Production Readiness Audit Findings

| File:Line | Issue | Priority |
|-----------|-------|----------|
| packages/backend/domain/index_analyzer.py:1445 | SQL injection: `table_name` used in f-string for VACUUM FULL without validation | High |
| apps/api/concurrent_usage_endpoints.py:171-196 | IDOR: get_session returns any session without tenant verification | High |
| apps/api/concurrent_usage_endpoints.py:105-145 | IDOR: complete_session/fail_session accept any session_id without tenant check | High |
| apps/api/concurrent_usage_endpoints.py:198-210 | IDOR: get_active_sessions returns all tenants' sessions | Medium |
| apps/api/integrations.py:54 | Swallowed exception: _decrypt_token returns encrypted on failure without logging | Medium |
| apps/api/gdpr.py:406 | list_data_categories has no auth (intentional for GDPR transparency) | Low |
| apps/api/feedback_endpoints.py:146 | user_id filter could allow non-admin to query other users' feedback (module not mounted) | Low |

## Fixes Applied

1. **index_analyzer.py**: Added regex validation for `table_name` before VACUUM FULL
2. **concurrent_usage_endpoints.py**: Added tenant verification for get_session, complete_session, fail_session; filter active_sessions by tenant
3. **integrations.py**: Added logger.warning on decryption failure
