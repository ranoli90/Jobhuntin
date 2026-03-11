-- Performance optimization indexes for Phase 1.2
-- These indexes address the most common slow queries and N+1 issues

-- Applications table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_user_id_created_at 
ON applications(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_status_created_at 
ON applications(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_job_id_status 
ON applications(job_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_tenant_id 
ON applications(tenant_id) WHERE tenant_id IS NOT NULL;

-- Jobs table indexes for job search and filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_location_remote 
ON jobs(location, remote) WHERE remote = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_salary_range 
ON jobs(salary_min, salary_max) WHERE salary_min > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_job_type_created_at 
ON jobs(job_type, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_company_name 
ON jobs(company_name) WHERE company_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_title_search 
ON jobs USING gin(to_tsvector('english', title || ' ' || description));

-- Users table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email 
ON users(email) WHERE email IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_has_completed_onboarding 
ON users(has_completed_onboarding) WHERE has_completed_onboarding = false;

-- Profiles table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_user_id 
ON profiles(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_headline_search 
ON profiles USING gin(to_tsvector('english', headline || ' ' || bio));

-- Saved jobs indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_jobs_user_id_created_at 
ON saved_jobs(user_id, saved_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_jobs_job_id 
ON saved_jobs(job_id);

-- Analytics events indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_user_id_created_at 
ON analytics_events(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_event_type_created_at 
ON analytics_events(event_type, created_at DESC);

-- Cover letters indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cover_letters_user_id_created_at 
ON cover_letters(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cover_letters_job_id 
ON cover_letters(job_id) WHERE job_id IS NOT NULL;

-- Profile embeddings indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profile_embeddings_user_id 
ON profile_embeddings(user_id) WHERE user_id IS NOT NULL;

-- User preferences indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_preferences_user_id 
ON user_preferences(user_id) WHERE user_id IS NOT NULL;

-- Input answers indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_input_answers_user_id_created_at 
ON input_answers(user_id, created_at DESC);

-- Email communications log indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_communications_user_id_created_at 
ON email_communications_log(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_communications_status_created_at 
ON email_communications_log(status, created_at DESC);

-- Notification delivery tracking indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notification_delivery_user_id_created_at 
ON notification_delivery_tracking(user_id, created_at DESC);

-- Match score history indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_match_score_history_user_id_created_at 
ON match_score_history(user_id, created_at DESC);

-- Resume PDFs indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resume_pdfs_user_id_created_at 
ON resume_pdfs(user_id, created_at DESC);

-- Application screenshots indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_application_screenshots_application_id_created_at 
ON application_screenshots(application_id, created_at DESC);

-- Complex composite indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_user_status_job 
ON applications(user_id, status, job_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_location_salary_remote 
ON jobs(location, salary_min, salary_max, remote) 
WHERE salary_min > 0 AND remote = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_user_type_date 
ON analytics_events(user_id, event_type, created_at DESC);

-- Partial indexes for frequently filtered data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_active 
ON applications(user_id, created_at DESC) 
WHERE status IN ('pending', 'submitted');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_active 
ON jobs(created_at DESC) 
WHERE status = 'active' AND created_at > NOW() - INTERVAL '30 days';

-- Tenant isolation indexes for multi-tenant queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_tenant_user 
ON applications(tenant_id, user_id) WHERE tenant_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_tenant_email 
ON users(tenant_id, email) WHERE tenant_id IS NOT NULL;

-- Full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_fulltext 
ON jobs USING gin(to_tsvector('english', title || ' ' || description || ' ' || company_name));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_fulltext 
ON profiles USING gin(to_tsvector('english', headline || ' ' || bio));

-- Performance monitoring indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_created_at 
ON api_usage(created_at DESC) WHERE created_at > NOW() - INTERVAL '7 days';

-- Cleanup old indexes that are no longer needed
-- (Keep these commented out for now, uncomment if needed)
-- DROP INDEX CONCURRENTLY IF EXISTS idx_old_unused_index;
