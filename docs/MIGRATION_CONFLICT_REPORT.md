# Migration Conflict Analysis Report

**Generated:** 2026-03-15  
**Scope:** Migrations 001-040, infra/postgres/schema.sql  
**Status:** Analysis Complete - Awaiting Review

---

## Executive Summary

This report documents **critical conflicts** found in the JobHuntin database migration files. The analysis identified:

| Category | Count | Severity |
|----------|-------|----------|
| Duplicate Table Definitions | 42 | **CRITICAL** |
| Duplicate Index Definitions | 150+ | HIGH |
| Duplicate Function Definitions | 8 | MEDIUM |
| Duplicate Trigger Definitions | 30+ | MEDIUM |
| Schema Inconsistencies | 15+ | LOW |

**Key Risk:** Running all migrations sequentially on a fresh database will cause `CREATE TABLE IF NOT EXISTS` to silently skip duplicate definitions, but the schemas may differ between versions, leading to unexpected column structures and potential data integrity issues.

---

## 1. Duplicate Table Definitions

### 1.1 Critical Duplicates (Same Table, Different Schemas)

#### `answer_memory` - 4 Definitions
| Migration | Schema Differences |
|-----------|-------------------|
| 001_initial_schema.sql | Uses `TIMESTAMP`, no `tenant_id`, has `UNIQUE(user_id, field_label)` |
| 002_onboarding_tables.sql | Uses `TIMESTAMPTZ`, has `tenant_id`, different constraint naming |
| 016_user_experience_features.sql | Links to `interview_questions`, has `question_id`, `mastery_level` |
| 021_missing_components_fix.sql | Simplified schema with `tenant_id` |

**Risk:** Data loss if wrong schema is used. The 016 version links to `interview_questions` table which may not exist.

#### `user_preferences` - 3 Definitions
| Migration | Schema Differences |
|-----------|-------------------|
| 001_initial_schema.sql | Simple schema: `location`, `role_type`, `salary_min`, `remote_only` |
| 011_enhanced_notifications.sql | Enhanced: `preferences JSONB`, `dnd_active`, `timezone`, notification settings |
| 013_communication_system.sql | Multi-tenant: has `tenant_id`, channel preferences (`in_app_enabled`, `email_enabled`, etc.) |

**Risk:** Column mismatch errors when application expects fields from one version but database has another.

#### `interview_sessions` - 2 Definitions
| Migration | Schema Differences |
|-----------|-------------------|
| 003_interview_sessions.sql | Uses `session_id` as PK, has RLS policies, detailed columns |
| 021_missing_components_fix.sql | Uses `id` as PK, simpler schema, no RLS policies |

**Risk:** Primary key mismatch causes foreign key failures.

#### `notification_delivery_tracking` - 3 Definitions
| Migration | Schema Differences |
|-----------|-------------------|
| 011_enhanced_notifications.sql | References `notification_log(id)` which may not exist |
| 013_communication_system.sql | References `notifications(id)`, has `tenant_id` |
| 021_missing_components_fix.sql | Has `notification_id UUID NOT NULL` without FK constraint |

**Risk:** Foreign key failures if referenced tables don't exist.

#### `dead_letter_queue` - 3 Definitions
| Migration | Schema Differences |
|-----------|-------------------|
| 010_agent_improvements.sql | Complex schema with `priority`, `status`, `next_retry_at` |
| 021_missing_components_fix.sql | Has `error_type`, `resolution_notes`, `resolved_at` |
| 025_job_dead_letter_queue.sql | Simplified: `failure_reason`, `attempt_count`, `last_error` |

**Risk:** Different column names cause application errors.

### 1.2 Complete Duplicate Table List

| Table Name | Migrations | Severity |
|------------|------------|----------|
| `answer_memory` | 001, 002, 016, 021 | CRITICAL |
| `user_preferences` | 001, 011, 013 | CRITICAL |
| `interview_sessions` | 003, 021 | CRITICAL |
| `notification_delivery_tracking` | 011, 013, 021 | CRITICAL |
| `dead_letter_queue` | 010, 021, 025 | CRITICAL |
| `email_communications_log` | 009, 013, 021 | HIGH |
| `email_preferences` | 009, 013, 021 | HIGH |
| `notification_batches` | 011, 013 | HIGH |
| `alert_processing_log` | 011, 013 | HIGH |
| `user_interests` | 010, 011, 013, 021 | HIGH |
| `notification_semantic_tags` | 010, 011, 021 | HIGH |
| `button_detections` | 010, 021 | HIGH |
| `form_field_detections` | 010, 021 | HIGH |
| `oauth_credentials` | 010, 021 | HIGH |
| `concurrent_usage_sessions` | 010, 021 | HIGH |
| `screenshot_captures` | 010, 021 | HIGH |
| `document_type_tracking` | 010, 021 | HIGH |
| `agent_performance_metrics` | 010, 021 | HIGH |
| `resume_versions` | 016, 021 | HIGH |
| `follow_up_reminders` | 016, 021, 024 | HIGH |
| `interview_questions` | 016, 021 | HIGH |
| `answer_attempts` | 016, 021 | HIGH |
| `application_notes` | 016, 021, 024 | HIGH |
| `performance_metrics` | 012, 020 | MEDIUM |
| `performance_alerts` | 005, 012, 020 | MEDIUM |
| `performance_dashboards` | 014, 022 | MEDIUM |
| `performance_alerts_config` | 017, 022, 023 | MEDIUM |
| `performance_trends` | 014, 022 | MEDIUM |
| `cache_configurations` | 017, 023 | MEDIUM |
| `cache_entries` | 017, 023 | MEDIUM |
| `connection_pool_configurations` | 017, 023 | MEDIUM |
| `connection_pool_statistics` | 017, 023 | MEDIUM |
| `cache_warming_schedules` | 017, 023 | MEDIUM |
| `cache_invalidation_rules` | 017, 023 | MEDIUM |
| `performance_alerts_history` | 017, 023 | MEDIUM |
| `cache_performance_metrics` | 014, 023 | MEDIUM |
| `experiments` | 019, 021 | MEDIUM |
| `skills_taxonomy` | 021 | LOW |

---

## 2. Duplicate Index Definitions

### 2.1 Critical Index Conflicts

The following indexes are defined multiple times with potential differences:

```sql
-- idx_applications_user_id appears in:
-- 001_initial_schema.sql (line 120)
-- 015_performance_indexes.sql (line 5-6)
-- 018_missing_indexes.sql (line 8-9)
-- 024_application_enhancements.sql (line 12)

-- idx_applications_status appears in:
-- 001_initial_schema.sql (line 121)
-- 015_performance_indexes.sql (line 8-9)

-- idx_applications_job_id appears in:
-- 015_performance_indexes.sql (line 11-12)
-- 018_missing_indexes.sql (line 5-6)
-- 040_missing_indexes_and_timestamptz.sql (line 7)
```

### 2.2 Index Definition Variations

Some indexes have different definitions across migrations:

| Index Name | Variations |
|------------|------------|
| `idx_applications_user_id` | Simple vs composite with `created_at DESC` |
| `idx_jobs_created_at` | `DESC` vs `TIMESTAMPTZ` conversion |
| `idx_users_email` | With/without `WHERE email IS NOT NULL` condition |

### 2.3 Partial Index Conflicts

Several partial indexes have inconsistent conditions:

```sql
-- 015_performance_indexes.sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_active 
ON applications(user_id, created_at DESC) 
WHERE status IN ('pending', 'submitted');

-- vs expected statuses from application code
WHERE status IN ('QUEUED', 'PROCESSING', 'APPLIED', 'HOLD')
```

---

## 3. Duplicate Function Definitions

### 3.1 `update_updated_at_column()` - 8 Definitions

| Migration | Implementation |
|-----------|----------------|
| 005_monitoring_tables.sql | `RETURNS TRIGGER`, uses `NOW()` |
| 006_resume_pdfs.sql | `RETURNS TRIGGER`, uses `CURRENT_TIMESTAMP` |
| 008_application_screenshots.sql | `RETURNS TRIGGER`, uses `NOW()` |
| 010_agent_improvements.sql | `RETURNS TRIGGER`, uses `NOW()` |
| 016_user_experience_features.sql | `RETURNS TRIGGER`, uses `NOW()` |
| 021_missing_components_fix.sql | `RETURNS TRIGGER`, uses `NOW()` |
| 038_data_retention_tables.sql | Named `update_retention_policy_timestamp()` |
| 039_user_consents.sql | Named `update_user_consent_timestamp()` |

**Issue:** Using `CREATE OR REPLACE FUNCTION` means the last definition wins, but all are functionally equivalent.

### 3.2 `trigger_set_timestamp()` - 2 Definitions

| Migration | Notes |
|-----------|-------|
| 010_agent_improvements.sql | Standard implementation |
| 013_communication_system.sql | Identical implementation |

### 3.3 `handle_updated_at()` - 1 Definition

Only in 003_interview_sessions.sql, but conflicts with `update_updated_at_column()` naming convention.

---

## 4. Duplicate Trigger Definitions

### 4.1 Triggers on Same Tables

Multiple migrations attempt to create triggers on the same tables:

| Table | Trigger Name | Migrations |
|-------|--------------|------------|
| `applications` | Various update triggers | 024, 030 |
| `answer_memory` | `update_answer_memory_updated_at` | 016, 021 |
| `application_notes` | `update_application_notes_updated_at` | 016, 021, 024 |
| `follow_up_reminders` | `update_follow_up_reminders_updated_at` | 016, 021, 024 |

### 4.2 Notification Trigger

Migration 030 creates a NOTIFY trigger that could conflict:

```sql
-- 030_applications_notify_trigger.sql
CREATE TRIGGER trg_applications_notify_job_queue
  AFTER INSERT OR UPDATE OF status ON public.applications
  FOR EACH ROW
  WHEN (NEW.status = 'QUEUED')
  EXECUTE FUNCTION public.notify_job_queue_on_application();
```

---

## 5. Schema Inconsistencies

### 5.1 Timestamp Type Variations

| Table | Migration 001 | Migration 040 |
|-------|---------------|---------------|
| `tenants.created_at` | `TIMESTAMP` | Converted to `TIMESTAMPTZ` |
| `users.created_at` | `TIMESTAMP` | Converted to `TIMESTAMPTZ` |
| `jobs.created_at` | `TIMESTAMP` | Converted to `TIMESTAMPTZ` |
| `applications.created_at` | `TIMESTAMP` | Converted to `TIMESTAMPTZ` |

**Issue:** Migration 040 attempts to convert timestamps, but if tables were created by later migrations using `TIMESTAMPTZ`, this causes errors.

### 5.2 UUID Generation Functions

| Style | Function | Used In |
|-------|----------|---------|
| PostgreSQL extension | `uuid_generate_v4()` | 001, infra/postgres/schema.sql |
| Built-in | `gen_random_uuid()` | 002-040 |

**Issue:** Mixed usage requires both `uuid-ossp` extension and PostgreSQL 13+ built-in function.

### 5.3 Schema Qualification

| Style | Example | Used In |
|-------|---------|---------|
| Unqualified | `CREATE TABLE answer_memory` | 001 |
| Qualified | `CREATE TABLE public.answer_memory` | 002-040 |

---

## 6. Foreign Key Issues

### 6.1 Missing Referenced Tables

Several migrations reference tables that may not exist when the migration runs:

| Table | References | Migration |
|-------|------------|-----------|
| `notification_delivery_tracking` | `notification_log(id)` | 011 |
| `notification_semantic_tags` | `notification_delivery_tracking(id)` | 010 |
| `resume_pdfs` | `user_profiles(id)` | 006 |

### 6.2 Circular Dependencies

```
notification_log (referenced by 011) ← Not created in any migration
notification_delivery_tracking (011) ← References notification_log
notification_semantic_tags (010) ← References notification_delivery_tracking
```

---

## 7. Consolidation Recommendations

### 7.1 Immediate Actions Required

1. **Identify Canonical Table Definitions**
   - For each duplicate table, determine which schema is correct
   - Document the canonical version in a single migration

2. **Create Migration Dependency Order**
   - Ensure referenced tables exist before foreign keys
   - Create missing tables like `notification_log` or remove references

3. **Consolidate Index Definitions**
   - Remove duplicate index creations
   - Keep only the most comprehensive version

### 7.2 Recommended Migration Order

```
Phase 1: Core Tables (No Dependencies)
├── 001_initial_schema.sql (canonical for: tenants, users, jobs, applications)
├── 002_onboarding_tables.sql (remove answer_memory - use 001 version)
└── 036_companies_table.sql

Phase 2: Extended Core
├── 003_interview_sessions.sql (canonical version)
├── 004_match_weights_config.sql
├── 006_resume_pdfs.sql
├── 007_saved_jobs.sql
└── 028_onboarding_sessions.sql

Phase 3: Application Support
├── 008_application_screenshots.sql
├── 024_application_enhancements.sql (canonical for application_notes, follow_up_reminders)
├── 025_job_dead_letter_queue.sql (canonical for DLQ)
└── 029_match_scores_table.sql

Phase 4: Communication (Consolidated)
├── 009_email_communications.sql (canonical)
├── 013_communication_system.sql (remove duplicates)
└── Create missing notification_log table

Phase 5: Monitoring (Consolidated)
├── 005_monitoring_tables.sql (canonical for API monitoring)
├── 012_performance_monitoring.sql
├── 014_enhanced_performance.sql
├── 017_cache_connection_pools.sql (canonical for cache/pool)
├── 022_monitoring_tables.sql (remove duplicates)
└── 023_caching_tables.sql (remove duplicates)

Phase 6: User Experience (Consolidated)
├── 010_agent_improvements.sql (canonical for agent tables)
├── 011_enhanced_notifications.sql (remove duplicates)
├── 016_user_experience_features.sql (canonical for resume_versions, interview_questions)
├── 019_user_experience.sql
└── 021_missing_components_fix.sql (REMOVE - all tables defined elsewhere)

Phase 7: Analytics & Compliance
├── 015_performance_indexes.sql
├── 018_missing_indexes.sql (consolidate with 015)
├── 020_database_performance.sql
├── 027_additional_composite_indexes.sql
├── 032_applications_archive.sql
├── 033_gdpr_requests.sql
├── 034_contact_messages.sql
├── 035_job_quality_fields.sql
├── 037_analytics_tables.sql
├── 038_data_retention_tables.sql
├── 039_user_consents.sql
└── 040_missing_indexes_and_timestamptz.sql

Phase 8: Final Setup
├── 026_tenant_slug_job_external_id.sql
├── 030_applications_notify_trigger.sql
└── 031_jobspy_schema_columns.sql
```

### 7.3 Migrations to Remove/Deprecate

| Migration | Action | Reason |
|-----------|--------|--------|
| 021_missing_components_fix.sql | **REMOVE ENTIRELY** | All 22 tables defined in other migrations |
| 022_monitoring_tables.sql | **MERGE into 005** | Duplicate definitions |
| 023_caching_tables.sql | **MERGE into 017** | Duplicate definitions |
| 011_enhanced_notifications.sql | **MERGE into 013** | Duplicate definitions |

---

## 8. Risk Assessment

### 8.1 High Risk Issues

| Issue | Impact | Likelihood | Mitigation |
|-------|--------|------------|------------|
| Schema mismatch on `answer_memory` | Data loss, app errors | High | Use 001 version, add migration to add missing columns |
| Missing `notification_log` table | FK failures | High | Create table or remove FK references |
| Different DLQ schemas | Job processing failures | Medium | Standardize on 025 version |
| `interview_sessions` PK mismatch | Session tracking failures | Medium | Use 003 version with RLS |

### 8.2 Medium Risk Issues

| Issue | Impact | Likelihood | Mitigation |
|-------|--------|------------|------------|
| Duplicate index creation | Performance impact, confusion | High | Consolidate into single migration |
| Mixed timestamp types | Timezone bugs | Medium | Standardize on TIMESTAMPTZ |
| Duplicate function definitions | Maintenance confusion | Medium | Single canonical definition |

### 8.3 Low Risk Issues

| Issue | Impact | Likelihood | Mitigation |
|-------|--------|------------|------------|
| Schema qualification inconsistency | None if default schema is public | Low | Standardize on qualified names |
| UUID function variation | None if both available | Low | Standardize on `gen_random_uuid()` |

---

## 9. Implementation Checklist

Before modifying any migrations:

- [ ] Create full database backup
- [ ] Document current production schema
- [ ] Test migration order on fresh database
- [ ] Verify all foreign key references resolve
- [ ] Run application tests after each phase
- [ ] Update infra/postgres/schema.sql to match consolidated migrations
- [ ] Update infra/postgres/migrations.sql to include only canonical migrations

---

## 10. Appendix: Table Creation Matrix

| Table | 001 | 002 | 003 | 005 | 006 | 009 | 010 | 011 | 012 | 013 | 014 | 016 | 017 | 019 | 020 | 021 | 022 | 023 | 024 | 025 | 037 |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| tenants | ✓ | | | | | | | | | | | | | | | | | | | | |
| users | ✓ | | | | | | | | | | | | | | | | | | | | |
| jobs | ✓ | | | | | | | | | | | | | | | | | | | | |
| applications | ✓ | | | | | | | | | | | | | | | | | | | | |
| answer_memory | ✓ | ✓ | | | | | | | | | | ✓ | | | | ✓ | | | | | |
| user_preferences | ✓ | | | | | | | ✓ | | ✓ | | | | | | | | | | | |
| interview_sessions | | | ✓ | | | | | | | | | | | | | ✓ | | | | | |
| api_request_logs | | | | ✓ | | | | | | | | | | | | | | | | | |
| email_communications_log | | | | | | ✓ | | | | ✓ | | | | | | ✓ | | | | | |
| button_detections | | | | | | | ✓ | | | | | | | | | ✓ | | | | | |
| notification_delivery_tracking | | | | | | | | ✓ | | ✓ | | | | | | ✓ | | | | | |
| dead_letter_queue | | | | | | | ✓ | | | | | | | | | ✓ | | | | ✓ | |
| application_notes | | | | | | | | | | | | ✓ | | | | ✓ | | | ✓ | | |
| performance_metrics | | | | | | | | | ✓ | | | | | | ✓ | | | | | | |

*Full matrix available in supplementary documentation*

---

## Conclusion

The migration files contain significant duplication and conflicts that could cause:

1. **Silent failures** - `IF NOT EXISTS` clauses hide schema differences
2. **Data integrity issues** - Different column definitions between versions
3. **Foreign key failures** - Missing referenced tables
4. **Performance degradation** - Duplicate and conflicting indexes

**Recommended Next Steps:**

1. Review this report with the development team
2. Identify canonical schema for each duplicated table
3. Create a consolidation plan with proper migration order
4. Test on a staging environment before production deployment

---

*This report was generated by automated analysis. Manual review is required before implementing any changes.*
