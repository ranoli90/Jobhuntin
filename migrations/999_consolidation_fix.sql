-- =============================================================================
-- MIGRATION CONSOLIDATION: Duplicate Table Definitions Fixed
-- =============================================================================
-- This migration consolidates duplicate table definitions from migrations:
-- 001, 002, 009, 010, 011, 013, 014, 016, 017, 020, 021, 022, 023, 024, 025
--
-- CONSOLIDATION STRATEGY:
-- 1. Keep the most comprehensive table definition (canonical version)
-- 2. Use ALTER TABLE to add missing columns from other versions
-- 3. Remove duplicate CREATE TABLE statements
-- 4. Add comments explaining each table's canonical version source
--
-- Key Tables Consolidated:
-- - user_preferences (001, 011, 013) -> Use 013 version with tenant_id
-- - answer_memory (001, 002, 016, 021) -> Use 016 version with full schema
-- - interview_sessions (003, 021) -> Use 003 version with RLS
-- - button_detections (010, 021) -> Use 010 version (more complete)
-- - form_field_detections (010, 021) -> Use 010 version (more complete)
-- - oauth_credentials (010, 021) -> Use 010 version (more complete)
-- - concurrent_usage_sessions (010, 021) -> Use 010 version (more complete)
-- - dead_letter_queue (010, 021, 025) -> Use 010 version (most complete)
-- - screenshot_captures (010, 021) -> Use 010 version (more complete)
-- - document_type_tracking (010, 021) -> Use 010 version (more complete)
-- - agent_performance_metrics (010, 021) -> Use 010 version (more complete)
-- - notification_semantic_tags (010, 011, 021) -> Use 010 version
-- - user_interests (010, 011, 013, 021) -> Use 010 version
-- - notification_delivery_tracking (011, 013, 021) -> Use 013 version (most complete)
-- - email_communications_log (009, 013, 021) -> Use 013 version (most complete)
-- - email_preferences (009, 013, 021) -> Use 013 version (most complete)
-- - notification_batches (011, 013) -> Use 013 version (more complete)
-- - alert_processing_log (011, 013) -> Use 013 version (more complete)
-- - alert_rules (013, 022) -> Use 013 version
-- - resume_versions (016, 021) -> Use 016 version (more complete)
-- - follow_up_reminders (016, 021, 024) -> Use 016 version (more complete)
-- - interview_questions (016, 021) -> Use 016 version (more complete)
-- - answer_attempts (016, 021) -> Use 016 version (more complete)
-- - application_notes (016, 021, 024) -> Use 016 version (more complete)
-- - performance_dashboards (014, 022) -> Use 014 version (more complete)
-- - performance_alerts_config (017, 022, 023) -> Use 017 version
-- - performance_trends (014, 022) -> Use 014 version (more complete)
-- - cache_configurations (017, 023) -> Use 017 version
-- - cache_entries (017, 023) -> Use 017 version
-- - connection_pool_configurations (017, 023) -> Use 017 version
-- - connection_pool_statistics (017, 023) -> Use 017 version
-- - cache_warming_schedules (017, 023) -> Use 017 version
-- - cache_invalidation_rules (017, 023) -> Use 017 version
-- - performance_alerts_history (017, 023) -> Use 017 version
-- - cache_performance_metrics (014, 023) -> Use 014 version (different schema)
-- =============================================================================

-- +migrate Up

-- =============================================================================
-- SECTION 1: CORE TABLES (from 001_initial_schema.sql - canonical)
-- =============================================================================

-- Tenants table (canonical from 001)
-- Already created in 001_initial_schema.sql, adding TIMESTAMPTZ if not exists
ALTER TABLE tenants ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE tenants ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- Users table (canonical from 001)
ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- Jobs table (canonical from 001)
ALTER TABLE jobs ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE jobs ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- Applications table (canonical from 001)
ALTER TABLE applications ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE applications ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- =============================================================================
-- SECTION 2: USER PREFERENCES (consolidated from 001, 011, 013)
-- Canonical version: 013_communication_system.sql (most complete with tenant_id)
-- =============================================================================

-- The 013 version is the canonical one:
-- - Has user_id + tenant_id as PRIMARY KEY (composite)
-- - Has in_app_enabled, email_enabled, push_enabled, sms_enabled
-- - Has categories JSONB, do_not_disturb settings

-- Add missing columns from 011 version to existing user_preferences
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}';
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS dnd_active BOOLEAN DEFAULT FALSE;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS dnd_start_time TIME;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS dnd_end_time TIME;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC';
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS notification_sound BOOLEAN DEFAULT TRUE;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS notification_vibration BOOLEAN DEFAULT TRUE;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS notification_badge BOOLEAN DEFAULT TRUE;

-- Add tenant_id if not exists (from 013 version)
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Add notification channel columns from 013 version
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS in_app_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS email_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS push_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS sms_enabled BOOLEAN DEFAULT FALSE;

-- Add categories and do_not_disturb from 013 version
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS categories JSONB DEFAULT '{}';
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS do_not_disturb_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS do_not_disturb_start TIME;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS do_not_disturb_end TIME;

-- =============================================================================
-- SECTION 3: ANSWER MEMORY (consolidated from 001, 002, 016, 021)
-- Canonical version: 016_user_experience_features.sql (most complete)
-- =============================================================================

-- The 016 version is canonical with: question_id, mastery_level, etc.
-- Add missing columns from other versions

ALTER TABLE answer_memory ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE answer_memory ADD COLUMN IF NOT EXISTS question_id UUID;
ALTER TABLE answer_memory ADD COLUMN IF NOT EXISTS key_points TEXT[] DEFAULT '{}';
ALTER TABLE answer_memory ADD COLUMN IF NOT EXISTS examples TEXT[] DEFAULT '{}';
ALTER TABLE answer_memory ADD COLUMN IF NOT EXISTS follow_up_questions TEXT[] DEFAULT '{}';
ALTER TABLE answer_memory ADD COLUMN IF NOT EXISTS last_reviewed TIMESTAMPTZ;
ALTER TABLE answer_memory ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;
ALTER TABLE answer_memory ADD COLUMN IF NOT EXISTS mastery_level DECIMAL(3,2) DEFAULT 0.0;

-- Convert TIMESTAMP to TIMESTAMPTZ
ALTER TABLE answer_memory ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE answer_memory ALTER COLUMN updated_at TYPE TIMESTAMPTZ;
ALTER TABLE answer_memory ALTER COLUMN last_used_at TYPE TIMESTAMPTZ;

-- =============================================================================
-- SECTION 4: INTERVIEW SESSIONS (consolidated from 003, 021)
-- Canonical version: 003_interview_sessions.sql (has RLS policies)
-- =============================================================================

-- Add missing columns from 021 version to 003 version
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS job_id UUID REFERENCES jobs(id) ON DELETE CASCADE;
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS session_type VARCHAR(50) DEFAULT 'GENERAL';
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS difficulty VARCHAR(50) DEFAULT 'MEDIUM';
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS question_count INTEGER DEFAULT 10;
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS questions JSONB DEFAULT '[]';
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS responses JSONB DEFAULT '[]';
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS feedback JSONB DEFAULT '[]';
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS total_score DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Convert timestamps to TIMESTAMPTZ
ALTER TABLE interview_sessions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE interview_sessions ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- =============================================================================
-- SECTION 5: AGENT TABLES (from 010_agent_improvements.sql - canonical)
-- button_detections, form_field_detections, oauth_credentials, concurrent_usage_sessions,
-- dead_letter_queue, screenshot_captures, document_type_tracking, agent_performance_metrics
-- These are already complete in 010, add any missing columns from 021
-- =============================================================================

-- button_detections - add missing columns from 021
ALTER TABLE button_detections ADD COLUMN IF NOT EXISTS file_size INTEGER;
ALTER TABLE button_detections ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE button_detections ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- form_field_detections - already complete in 010
ALTER TABLE form_field_detections ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE form_field_detections ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- oauth_credentials - add is_active from 010 version
ALTER TABLE oauth_credentials ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE oauth_credentials ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE oauth_credentials ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- concurrent_usage_sessions - add missing columns from 021
ALTER TABLE concurrent_usage_sessions ADD COLUMN IF NOT EXISTS application_id UUID REFERENCES applications(id) ON DELETE CASCADE;
ALTER TABLE concurrent_usage_sessions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE concurrent_usage_sessions ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- dead_letter_queue - consolidate from 010, 021, 025
-- Use 010 version as base, add error_type, resolution_notes, resolved_at from 021
ALTER TABLE dead_letter_queue ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);
ALTER TABLE dead_letter_queue ADD COLUMN IF NOT EXISTS resolution_notes TEXT;
ALTER TABLE dead_letter_queue ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;
ALTER TABLE dead_letter_queue ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE dead_letter_queue ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- screenshot_captures - add missing from 021
ALTER TABLE screenshot_captures ADD COLUMN IF NOT EXISTS capture_id VARCHAR(255) UNIQUE;
ALTER TABLE screenshot_captures ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;
ALTER TABLE screenshot_captures ADD COLUMN IF NOT EXISTS file_size BIGINT DEFAULT 0;
ALTER TABLE screenshot_captures ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE screenshot_captures ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- document_type_tracking - consolidate
ALTER TABLE document_type_tracking ADD COLUMN IF NOT EXISTS tracking_id VARCHAR(255);
ALTER TABLE document_type_tracking ADD COLUMN IF NOT EXISTS file_name TEXT;
ALTER TABLE document_type_tracking ADD COLUMN IF NOT EXISTS original_filename TEXT;
ALTER TABLE document_type_tracking ADD COLUMN IF NOT EXISTS upload_timestamp TIMESTAMPTZ;
ALTER TABLE document_type_tracking ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20);
ALTER TABLE document_type_tracking ADD COLUMN IF NOT EXISTS processing_details JSONB;
ALTER TABLE document_type_tracking ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE document_type_tracking ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- agent_performance_metrics - consolidate
ALTER TABLE agent_performance_metrics ADD COLUMN IF NOT EXISTS metric_id VARCHAR(255);
ALTER TABLE agent_performance_metrics ADD COLUMN IF NOT EXISTS metric_type VARCHAR(100);
ALTER TABLE agent_performance_metrics ADD COLUMN IF NOT EXISTS metric_unit VARCHAR(50);
ALTER TABLE agent_performance_metrics ADD COLUMN IF NOT EXISTS metadata JSONB;
ALTER TABLE agent_performance_metrics ADD COLUMN IF NOT EXISTS session_id VARCHAR(255);
ALTER TABLE agent_performance_metrics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

-- =============================================================================
-- SECTION 6: COMMUNICATION TABLES (consolidated from 009, 011, 013)
-- email_communications_log, email_preferences, notifications
-- =============================================================================

-- email_communications_log - use 013 as canonical
ALTER TABLE email_communications_log ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE email_communications_log ADD COLUMN IF NOT EXISTS template_id UUID;
ALTER TABLE email_communications_log ADD COLUMN IF NOT EXISTS from_email TEXT;
ALTER TABLE email_communications_log ADD COLUMN IF NOT EXISTS reply_to TEXT;
ALTER TABLE email_communications_log ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE email_communications_log ADD COLUMN IF NOT EXISTS delivery_provider TEXT;
ALTER TABLE email_communications_log ADD COLUMN IF NOT EXISTS variables JSONB;
ALTER TABLE email_communications_log ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE email_communications_log ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- email_preferences - use 013 as canonical
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS email_enabled BOOLEAN DEFAULT true;
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS categories JSONB DEFAULT '{}';
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS frequency_limits JSONB DEFAULT '{}';
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS quiet_hours_enabled BOOLEAN DEFAULT false;
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS quiet_hours_start TIME;
ALTER TABLE email_preferences ADD COLUMN IF NOT EXISTS quiet_hours_end TIME;
ALTER TABLE email_preferences ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE email_preferences ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- =============================================================================
-- SECTION 7: NOTIFICATION TABLES (consolidated from 010, 011, 013)
-- notification_semantic_tags, user_interests, notification_delivery_tracking
-- =============================================================================

-- notification_semantic_tags - use 010 as canonical
ALTER TABLE notification_semantic_tags ADD COLUMN IF NOT EXISTS notification_id UUID;
ALTER TABLE notification_semantic_tags ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE notification_semantic_tags ADD COLUMN IF NOT EXISTS context JSONB;
ALTER TABLE notification_semantic_tags ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE notification_semantic_tags ALTER COLUMN created_at TYPE TIMESTAMPTZ;

-- user_interests - use 010 as canonical
ALTER TABLE user_interests ADD COLUMN IF NOT EXISTS interest_category VARCHAR(100);
ALTER TABLE user_interests ADD COLUMN IF NOT EXISTS interest_keywords TEXT[] DEFAULT '{}';
ALTER TABLE user_interests ADD COLUMN IF NOT EXISTS interest_score DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE user_interests ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE user_interests ADD COLUMN IF NOT EXISTS last_updated TIMESTAMPTZ;
ALTER TABLE user_interests ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE user_interests ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- notification_delivery_tracking - use 013 as canonical
ALTER TABLE notification_delivery_tracking ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE notification_delivery_tracking ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(20);
ALTER TABLE notification_delivery_tracking ADD COLUMN IF NOT EXISTS delivery_method VARCHAR(20);
ALTER TABLE notification_delivery_tracking ADD COLUMN IF NOT EXISTS device_token VARCHAR(255);
ALTER TABLE notification_delivery_tracking ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;
ALTER TABLE notification_delivery_tracking ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE notification_delivery_tracking ADD COLUMN IF NOT EXISTS metadata JSONB;
ALTER TABLE notification_delivery_tracking ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE notification_delivery_tracking ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- notification_batches - use 013 as canonical (has more columns)
ALTER TABLE notification_batches ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE notification_batches ADD COLUMN IF NOT EXISTS user_ids TEXT[];
ALTER TABLE notification_batches ADD COLUMN IF NOT EXISTS notification_template JSONB;
ALTER TABLE notification_batches ADD COLUMN IF NOT EXISTS batch_size INTEGER DEFAULT 100;
ALTER TABLE notification_batches ADD COLUMN IF NOT EXISTS priority VARCHAR(20);
ALTER TABLE notification_batches ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE notification_batches ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- alert_processing_log - use 013 as canonical
ALTER TABLE alert_processing_log ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE alert_processing_log ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE alert_processing_log ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE alert_processing_log ADD COLUMN IF NOT EXISTS context JSONB;
ALTER TABLE alert_processing_log ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE alert_processing_log ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- =============================================================================
-- SECTION 8: USER EXPERIENCE TABLES (consolidated from 016, 021, 024)
-- resume_versions, follow_up_reminders, interview_questions, answer_attempts, application_notes
-- =============================================================================

-- resume_versions - use 016 as canonical
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS resume_type VARCHAR(50);
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS file_format VARCHAR(10);
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT false;
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS target_industries TEXT[] DEFAULT '{}';
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS target_roles TEXT[] DEFAULT '{}';
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS skills_emphasized TEXT[] DEFAULT '{}';
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS ats_score DECIMAL(3,2);
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;
ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS success_rate DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE resume_versions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE resume_versions ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- follow_up_reminders - use 016 as canonical
ALTER TABLE follow_up_reminders ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE follow_up_reminders ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE follow_up_reminders ADD COLUMN IF NOT EXISTS reminder_type VARCHAR(50);
ALTER TABLE follow_up_reminders ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMPTZ;
ALTER TABLE follow_up_reminders ADD COLUMN IF NOT EXISTS metadata JSONB;
ALTER TABLE follow_up_reminders ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE follow_up_reminders ALTER COLUMN updated_at TYPE TIMESTAMPTZ;
ALTER TABLE follow_up_reminders ALTER COLUMN sent_at TYPE TIMESTAMPTZ;
ALTER TABLE follow_up_reminders ALTER COLUMN completed_at TYPE TIMESTAMPTZ;

-- interview_questions - use 016 as canonical
ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS question_text TEXT;
ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS question_type VARCHAR(50);
ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS answer TEXT;
ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS feedback JSONB;
ALTER TABLE interview_questions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE interview_questions ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- answer_attempts - use 016 as canonical
ALTER TABLE answer_attempts ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE answer_attempts ADD COLUMN IF NOT EXISTS attempt_text TEXT;
ALTER TABLE answer_attempts ADD COLUMN IF NOT EXISTS feedback TEXT;
ALTER TABLE answer_attempts ADD COLUMN IF NOT EXISTS ai_score DECIMAL(3,2);
ALTER TABLE answer_attempts ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT false;
ALTER TABLE answer_attempts ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE answer_attempts ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE answer_attempts ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- application_notes - use 016 as canonical
ALTER TABLE application_notes ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE application_notes ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE application_notes ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE application_notes ADD COLUMN IF NOT EXISTS category VARCHAR(50);
ALTER TABLE application_notes ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
ALTER TABLE application_notes ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT false;
ALTER TABLE application_notes ADD COLUMN IF NOT EXISTS reminder_date TIMESTAMPTZ;
ALTER TABLE application_notes ADD COLUMN IF NOT EXISTS author_id UUID REFERENCES users(id);
ALTER TABLE application_notes ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE application_notes ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- =============================================================================
-- SECTION 9: PERFORMANCE TABLES (consolidated from 012, 014, 017, 020, 022, 023)
-- performance_dashboards, performance_alerts_config, performance_trends
-- cache_configurations, cache_entries, connection_pool_configurations, etc.
-- =============================================================================

-- performance_dashboards - use 014 as canonical
ALTER TABLE performance_dashboards ADD COLUMN IF NOT EXISTS dashboard_config JSONB;
ALTER TABLE performance_dashboards ADD COLUMN IF NOT EXISTS refresh_interval_seconds INTEGER DEFAULT 60;
ALTER TABLE performance_dashboards ADD COLUMN IF NOT EXISTS widgets JSONB DEFAULT '[]';
ALTER TABLE performance_dashboards ADD COLUMN IF NOT EXISTS metadata JSONB;
ALTER TABLE performance_dashboards ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE performance_dashboards ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- performance_alerts_config - use 017 as canonical (most complete)
ALTER TABLE performance_alerts_config ADD COLUMN IF NOT EXISTS condition_expression TEXT;
ALTER TABLE performance_alerts_config ADD COLUMN IF NOT EXISTS auto_resolve BOOLEAN DEFAULT FALSE;
ALTER TABLE performance_alerts_config ADD COLUMN IF NOT EXISTS escalation_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE performance_alerts_config ADD COLUMN IF NOT EXISTS last_triggered TIMESTAMPTZ;
ALTER TABLE performance_alerts_config ADD COLUMN IF NOT EXISTS trigger_count INTEGER DEFAULT 0;
ALTER TABLE performance_alerts_config ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE performance_alerts_config ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- performance_trends - use 014 as canonical
ALTER TABLE performance_trends ADD COLUMN IF NOT EXISTS metric_type VARCHAR(50);
ALTER TABLE performance_trends ADD COLUMN IF NOT EXISTS trend_direction VARCHAR(20);
ALTER TABLE performance_trends ADD COLUMN IF NOT EXISTS average_value DOUBLE PRECISION;
ALTER TABLE performance_trends ADD COLUMN IF NOT EXISTS period_hours INTEGER;
ALTER TABLE performance_trends ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION;
ALTER TABLE performance_trends ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE performance_trends ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- cache_configurations - use 017 as canonical
ALTER TABLE cache_configurations ADD COLUMN IF NOT EXISTS compression_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE cache_configurations ADD COLUMN IF NOT EXISTS serialization_method VARCHAR(50) DEFAULT 'json';
ALTER TABLE cache_configurations ADD COLUMN IF NOT EXISTS eviction_threshold DOUBLE PRECISION DEFAULT 0.8;
ALTER TABLE cache_configurations ADD COLUMN IF NOT EXISTS cleanup_interval_seconds INTEGER DEFAULT 300;
ALTER TABLE cache_configurations ADD COLUMN IF NOT EXISTS metrics_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE cache_configurations ADD COLUMN IF NOT EXISTS configuration JSONB;
ALTER TABLE cache_configurations ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE cache_configurations ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE cache_configurations ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- cache_entries - use 017 as canonical
ALTER TABLE cache_entries ADD COLUMN IF NOT EXISTS cache_key VARCHAR(500);
ALTER TABLE cache_entries ADD COLUMN IF NOT EXISTS cache_type VARCHAR(50);
ALTER TABLE cache_entries ADD COLUMN IF NOT EXISTS cache_level VARCHAR(50);
ALTER TABLE cache_entries ADD COLUMN IF NOT EXISTS value_size_bytes INTEGER;
ALTER TABLE cache_entries ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE cache_entries ALTER COLUMN expires_at TYPE TIMESTAMPTZ;

-- connection_pool_configurations - use 017 as canonical
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS connection_type VARCHAR(50);
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS host VARCHAR(255);
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS port INTEGER;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS database VARCHAR(100);
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS ssl_mode VARCHAR(20) DEFAULT 'prefer';
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS command_timeout INTEGER DEFAULT 30;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS statement_timeout INTEGER DEFAULT 30000;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS idle_timeout INTEGER DEFAULT 300;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS max_lifetime INTEGER DEFAULT 3600;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS max_queries_per_connection INTEGER DEFAULT 5000;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS health_check_interval INTEGER DEFAULT 30;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS retry_attempts INTEGER DEFAULT 3;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS retry_delay DOUBLE PRECISION DEFAULT 1.0;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS configuration JSONB;
ALTER TABLE connection_pool_configurations ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE connection_pool_configurations ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE connection_pool_configurations ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- connection_pool_statistics - use 017 as canonical
ALTER TABLE connection_pool_statistics ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'healthy';
ALTER TABLE connection_pool_statistics ADD COLUMN IF NOT EXISTS memory_usage_percent DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE connection_pool_statistics ADD COLUMN IF NOT EXISTS cpu_usage_percent DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE connection_pool_statistics ADD COLUMN IF NOT EXISTS statistics JSONB;
ALTER TABLE connection_pool_statistics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

-- cache_warming_schedules - use 017 as canonical
ALTER TABLE cache_warming_schedules ADD COLUMN IF NOT EXISTS cache_name VARCHAR(100);
ALTER TABLE cache_warming_schedules ADD COLUMN IF NOT EXISTS key_pattern VARCHAR(255);
ALTER TABLE cache_warming_schedules ADD COLUMN IF NOT EXISTS data_loader_function VARCHAR(255);
ALTER TABLE cache_warming_schedules ADD COLUMN IF NOT EXISTS ttl_seconds INTEGER;
ALTER TABLE cache_warming_schedules ADD COLUMN IF NOT EXISTS schedule_type VARCHAR(50) DEFAULT 'cron';
ALTER TABLE cache_warming_schedules ADD COLUMN IF NOT EXISTS schedule_expression VARCHAR(100);
ALTER TABLE cache_warming_schedules ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE cache_warming_schedules ADD COLUMN IF NOT EXISTS configuration JSONB;
ALTER TABLE cache_warming_schedules ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE cache_warming_schedules ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- cache_invalidation_rules - use 017 as canonical
ALTER TABLE cache_invalidation_rules ADD COLUMN IF NOT EXISTS invalidation_type VARCHAR(50);
ALTER TABLE cache_invalidation_rules ADD COLUMN IF NOT EXISTS pattern VARCHAR(255);
ALTER TABLE cache_invalidation_rules ADD COLUMN IF NOT EXISTS condition_expression TEXT;
ALTER TABLE cache_invalidation_rules ADD COLUMN IF NOT EXISTS action_type VARCHAR(50) DEFAULT 'delete';
ALTER TABLE cache_invalidation_rules ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;
ALTER TABLE cache_invalidation_rules ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE cache_invalidation_rules ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- performance_alerts_history - use 017 as canonical
ALTER TABLE performance_alerts_history ADD COLUMN IF NOT EXISTS title VARCHAR(200);
ALTER TABLE performance_alerts_history ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE performance_alerts_history ADD COLUMN IF NOT EXISTS triggered_at TIMESTAMPTZ;
ALTER TABLE performance_alerts_history ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;
ALTER TABLE performance_alerts_history ADD COLUMN IF NOT EXISTS resolution_note TEXT;
ALTER TABLE performance_alerts_history ADD COLUMN IF NOT EXISTS notification_sent BOOLEAN DEFAULT FALSE;
ALTER TABLE performance_alerts_history ADD COLUMN IF NOT EXISTS notification_results JSONB;
ALTER TABLE performance_alerts_history ADD COLUMN IF NOT EXISTS metadata JSONB;

-- =============================================================================
-- SECTION 10: UNIQUE TABLES FROM 021 (skills_taxonomy, ab_testing_experiments, voice_interview_sessions)
-- These were only in 021, keeping them as-is but converting timestamps
-- =============================================================================

-- skills_taxonomy - only in 021
ALTER TABLE skills_taxonomy ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE skills_taxonomy ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- ab_testing_experiments - only in 021
ALTER TABLE ab_testing_experiments ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE ab_testing_experiments ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- voice_interview_sessions - only in 021
ALTER TABLE voice_interview_sessions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
ALTER TABLE voice_interview_sessions ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

-- =============================================================================
-- SECTION 11: CLEANUP - Drop migration 021 tables that are duplicates
-- These tables are already covered by earlier migrations or consolidated above
-- =============================================================================

-- Drop duplicate tables from 021 that are now consolidated
-- NOTE: Only drop if they exist and have no critical data
-- This is a safety measure - in production, you'd want to migrate data first

-- These tables were already created in earlier migrations, so the IF NOT EXISTS
-- in 021 would have skipped them. The schema is now unified above.

-- =============================================================================
-- SECTION 12: STANDARDIZE TIMESTAMPTZ CONVERSION (from 040)
-- Convert all remaining TIMESTAMP columns to TIMESTAMPTZ
-- =============================================================================

-- Convert all remaining TIMESTAMP columns to TIMESTAMPTZ across all tables
DO $$
BEGIN
    -- Convert tenant_members
    ALTER TABLE tenant_members ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert application_inputs
    ALTER TABLE application_inputs ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE application_inputs ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert events
    ALTER TABLE events ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert saved_jobs
    ALTER TABLE saved_jobs ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert application_screenshots
    ALTER TABLE application_screenshots ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert resume_pdfs
    ALTER TABLE resume_pdfs ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE resume_pdfs ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert resume_pdf_analytics
    ALTER TABLE resume_pdf_analytics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert resume_pdf_templates
    ALTER TABLE resume_pdf_templates ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE resume_pdf_templates ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert api_request_logs
    ALTER TABLE api_request_logs ALTER COLUMN timestamp TYPE TIMESTAMPTZ;
    ALTER TABLE api_request_logs ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_request_logs ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert api_performance_metrics
    ALTER TABLE api_performance_metrics ALTER COLUMN timestamp TYPE TIMESTAMPTZ;
    ALTER TABLE api_performance_metrics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert api_security_events
    ALTER TABLE api_security_events ALTER COLUMN timestamp TYPE TIMESTAMPTZ;
    ALTER TABLE api_security_events ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_security_events ALTER COLUMN updated_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_security_events ALTER COLUMN resolved_at TYPE TIMESTAMPTZ;

    -- Convert api_endpoint_stats
    ALTER TABLE api_endpoint_stats ALTER COLUMN date_hour TYPE TIMESTAMPTZ;
    ALTER TABLE api_endpoint_stats ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_endpoint_stats ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert api_daily_metrics
    ALTER TABLE api_daily_metrics ALTER COLUMN date TYPE DATE;
    ALTER TABLE api_daily_metrics ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_daily_metrics ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert api_user_activity
    ALTER TABLE api_user_activity ALTER COLUMN date TYPE DATE;
    ALTER TABLE api_user_activity ALTER COLUMN last_request_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_user_activity ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_user_activity ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert api_system_health
    ALTER TABLE api_system_health ALTER COLUMN timestamp TYPE TIMESTAMPTZ;
    ALTER TABLE api_system_health ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert api_alerts
    ALTER TABLE api_alerts ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_alerts ALTER COLUMN updated_at TYPE TIMESTAMPTZ;
    ALTER TABLE api_alerts ALTER COLUMN resolved_at TYPE TIMESTAMPTZ;

    -- Convert notifications
    ALTER TABLE notifications ALTER COLUMN expires_at TYPE TIMESTAMPTZ;
    ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE notifications ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert alert_rules
    ALTER TABLE alert_rules ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE alert_rules ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert alert_processing_actions
    ALTER TABLE alert_processing_actions ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert user_interest_profiles
    ALTER TABLE user_interest_profiles ALTER COLUMN last_updated TYPE TIMESTAMPTZ;
    ALTER TABLE user_interest_profiles ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE user_interest_profiles ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert user_interactions
    ALTER TABLE user_interactions ALTER COLUMN timestamp TYPE TIMESTAMPTZ;

    -- Convert notification_relevance_scores
    ALTER TABLE notification_relevance_scores ALTER COLUMN calculated_at TYPE TIMESTAMPTZ;

    -- Convert user_notification_batches
    ALTER TABLE user_notification_batches ALTER COLUMN sent_at TYPE TIMESTAMPTZ;
    ALTER TABLE user_notification_batches ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE user_notification_batches ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert batch_processing_results
    ALTER TABLE batch_processing_results ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert performance_metrics
    ALTER TABLE performance_metrics ALTER COLUMN timestamp TYPE TIMESTAMPTZ;
    ALTER TABLE performance_metrics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert performance_alerts
    ALTER TABLE performance_alerts ALTER COLUMN timestamp TYPE TIMESTAMPTZ;
    ALTER TABLE performance_alerts ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE performance_alerts ALTER COLUMN resolved_at TYPE TIMESTAMPTZ;

    -- Convert performance_thresholds
    ALTER TABLE performance_thresholds ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE performance_thresholds ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert query_analyses
    ALTER TABLE query_analyses ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert query_optimizations
    ALTER TABLE query_optimizations ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert index_analyses
    ALTER TABLE index_analyses ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert index_recommendations
    ALTER TABLE index_recommendations ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert database_performance_metrics
    ALTER TABLE database_performance_metrics ALTER COLUMN timestamp TYPE TIMESTAMPTZ;
    ALTER TABLE database_performance_metrics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert database_optimizations
    ALTER TABLE database_optimizations ALTER COLUMN executed_at TYPE TIMESTAMPTZ;
    ALTER TABLE database_optimizations ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert cache_performance_metrics
    ALTER TABLE cache_performance_metrics ALTER COLUMN timestamp TYPE TIMESTAMPTZ;
    ALTER TABLE cache_performance_metrics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert connection_pool_metrics
    ALTER TABLE connection_pool_metrics ALTER COLUMN last_health_check TYPE TIMESTAMPTZ;
    ALTER TABLE connection_pool_metrics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert performance_recommendations
    ALTER TABLE performance_recommendations ALTER COLUMN implemented_at TYPE TIMESTAMPTZ;
    ALTER TABLE performance_recommendations ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE performance_recommendations ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert performance_alert_subscriptions
    ALTER TABLE performance_alert_subscriptions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE performance_alert_subscriptions ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert performance_baselines
    ALTER TABLE performance_baselines ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE performance_baselines ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert performance_anomalies
    ALTER TABLE performance_anomalies ALTER COLUMN detected_at TYPE TIMESTAMPTZ;
    ALTER TABLE performance_anomalies ALTER COLUMN resolved_at TYPE TIMESTAMPTZ;
    ALTER TABLE performance_anomalies ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert user_events
    ALTER TABLE user_events ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert job_views
    ALTER TABLE job_views ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert application_outcomes
    ALTER TABLE application_outcomes ALTER COLUMN outcome_date TYPE TIMESTAMPTZ;
    ALTER TABLE application_outcomes ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert swipe_events
    ALTER TABLE swipe_events ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert page_views
    ALTER TABLE page_views ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert user_actions
    ALTER TABLE user_actions ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert conversion_events
    ALTER TABLE conversion_events ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert funnel_analyses
    ALTER TABLE funnel_analyses ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert feedback_responses
    ALTER TABLE feedback_responses ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert feedback_categories
    ALTER TABLE feedback_categories ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert nps_responses
    ALTER TABLE nps_responses ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert feedback_analyses
    ALTER TABLE feedback_analyses ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert experiments
    ALTER TABLE experiments ALTER COLUMN start_date TYPE TIMESTAMPTZ;
    ALTER TABLE experiments ALTER COLUMN end_date TYPE TIMESTAMPTZ;
    ALTER TABLE experiments ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE experiments ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert experiment_variants
    ALTER TABLE experiment_variants ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert user_assignments
    ALTER TABLE user_assignments ALTER COLUMN assigned_at TYPE TIMESTAMPTZ;
    ALTER TABLE user_assignments ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert experiment_results
    ALTER TABLE experiment_results ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert statistical_analyses
    ALTER TABLE statistical_analyses ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert behavior_events
    ALTER TABLE behavior_events ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert behavior_profiles
    ALTER TABLE behavior_profiles ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE behavior_profiles ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert behavior_analyses
    ALTER TABLE behavior_analyses ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert ux_metric_definitions
    ALTER TABLE ux_metric_definitions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE ux_metric_definitions ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert ux_metrics
    ALTER TABLE ux_metrics ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert ux_metric_aggregations
    ALTER TABLE ux_metric_aggregations ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert ux_metric_alerts
    ALTER TABLE ux_metric_alerts ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE ux_metric_alerts ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert match_scores
    ALTER TABLE match_scores ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert onboarding_sessions
    ALTER TABLE onboarding_sessions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE onboarding_sessions ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert job_dead_letter_queue
    ALTER TABLE job_dead_letter_queue ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert contact_messages
    ALTER TABLE contact_messages ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert user_consents
    ALTER TABLE user_consents ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE user_consents ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert consent_audit_log
    ALTER TABLE consent_audit_log ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert consent_policies
    ALTER TABLE consent_policies ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE consent_policies ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert retention_policies
    ALTER TABLE retention_policies ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE retention_policies ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert data_retention_logs
    ALTER TABLE data_retention_logs ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert companies
    ALTER TABLE companies ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE companies ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert user_skills
    ALTER TABLE user_skills ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert work_style_profiles
    ALTER TABLE work_style_profiles ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE work_style_profiles ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert email_templates
    ALTER TABLE email_templates ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE email_templates ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert alert_notifications
    ALTER TABLE alert_notifications ALTER COLUMN sent_at TYPE TIMESTAMPTZ;
    ALTER TABLE alert_notifications ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert alert_escalation_rules
    ALTER TABLE alert_escalation_rules ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    ALTER TABLE alert_escalation_rules ALTER COLUMN updated_at TYPE TIMESTAMPTZ;

    -- Convert performance_monitoring_snapshots
    ALTER TABLE performance_monitoring_snapshots ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert query_performance_analysis
    ALTER TABLE query_performance_analysis ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert connection_pool_snapshots
    ALTER TABLE connection_pool_snapshots ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert index_usage_analysis
    ALTER TABLE index_usage_analysis ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert performance_optimizations
    ALTER TABLE performance_optimizations ALTER COLUMN created_at TYPE TIMESTAMPTZ;

    -- Convert query_performance_trends
    ALTER TABLE query_performance_trends ALTER COLUMN created_at TYPE TIMESTAMPTZ;
END $$;

-- =============================================================================
-- SECTION 13: CONSOLIDATE DUPLICATE INDEXES
-- Remove duplicate index definitions - keep only unique indexes
-- =============================================================================

-- Many indexes are duplicated across migrations (e.g., idx_applications_user_id)
-- The IF NOT EXISTS clause means they don't cause errors, but we can clean up
-- by ensuring only the most comprehensive version exists

-- Common duplicated indexes (these are fine with IF NOT EXISTS):
-- idx_applications_user_id
-- idx_applications_status
-- idx_applications_job_id

-- =============================================================================
-- SECTION 14: CREATE OR REPLACE DUPLICATE FUNCTIONS
-- Consolidate duplicate function definitions
-- =============================================================================

-- Consolidate update_updated_at_column function (defined in 005, 006, 008, 010, 016, 021)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Consolidate trigger_set_timestamp function (defined in 010, 013)
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =============================================================================
-- +migrate Down
-- Rollback is not recommended for this consolidation migration
-- as it would require complex data migration
-- =============================================================================
