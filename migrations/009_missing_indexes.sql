-- Missing indexes for Phase 1.2 database migration fixes
-- These indexes address critical performance issues and missing constraints

-- Fix missing foreign key indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_job_id_fkey 
ON applications(job_id) WHERE job_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_user_id_fkey 
ON applications(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_user_id_fkey 
ON profiles(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cover_letters_job_id_fkey 
ON cover_letters(job_id) WHERE job_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cover_letters_user_id_fkey 
ON cover_letters(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_jobs_job_id_fkey 
ON saved_jobs(job_id) WHERE job_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_jobs_user_id_fkey 
ON saved_jobs(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resume_pdfs_user_id_fkey 
ON resume_pdfs(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_application_screenshots_application_id_fkey 
ON application_screenshots(application_id) WHERE application_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_input_answers_application_id_fkey 
ON input_answers(application_id) WHERE application_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_user_id_fkey 
ON analytics_events(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_preferences_user_id_fkey 
ON user_preferences(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profile_embeddings_user_id_fkey 
ON profile_embeddings(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_communications_log_user_id_fkey 
ON email_communications_log(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notification_delivery_tracking_user_id_fkey 
ON notification_delivery_tracking(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_match_score_history_user_id_fkey 
ON match_score_history(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_match_weight_analytics_user_id_fkey 
ON match_weight_analytics(user_id) WHERE user_id IS NOT NULL;

-- Fix missing unique constraints that should have indexes
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_unique 
ON users(email) WHERE email IS NOT NULL;

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_tenant_members_user_tenant_unique 
ON tenant_members(user_id, tenant_id) WHERE user_id IS NOT NULL AND tenant_id IS NOT NULL;

-- Add missing indexes for frequently queried timestamp columns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at 
ON users(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_created_at_desc 
ON applications(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_created_at_desc 
ON jobs(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_created_at_desc 
ON profiles(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_created_at_desc 
ON companies(created_at DESC);

-- Add indexes for status-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_status_created_at 
ON applications(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_status_created_at 
ON jobs(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_has_completed_onboarding 
ON users(has_completed_onboarding) WHERE has_completed_onboarding = false;

-- Add indexes for search and filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_title_lower 
ON jobs(LOWER(title)) WHERE title IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_company_name_lower 
ON jobs(LOWER(company_name)) WHERE company_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower 
ON users(LOWER(email)) WHERE email IS NOT NULL;

-- Add indexes for analytics and reporting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_event_type_created_at 
ON analytics_events(event_type, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_endpoint_created_at 
ON api_usage(endpoint, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_billing_invoices_status_created_at 
ON billing_invoices(status, created_at DESC);

-- Add indexes for tenant isolation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_tenant_id 
ON users(tenant_id) WHERE tenant_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenant_members_tenant_id 
ON tenant_members(tenant_id) WHERE tenant_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_tenant_id 
ON applications(tenant_id) WHERE tenant_id IS NOT NULL;

-- Add composite indexes for complex queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_user_status_created 
ON applications(user_id, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_job_status_created 
ON applications(job_id, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_company_status_created 
ON jobs(company_name, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_onboarding_created 
ON users(has_completed_onboarding, created_at DESC);

-- Add indexes for file storage paths
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resume_pdfs_storage_path 
ON resume_pdfs(storage_path) WHERE storage_path IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_application_screenshots_screenshot_path 
ON application_screenshots(screenshot_path) WHERE screenshot_path IS NOT NULL;

-- Add indexes for API rate limiting and monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_ip_address_created_at 
ON api_usage(ip_address, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_user_id_created_at 
ON api_usage(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Add indexes for search optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_fulltext_search 
ON jobs USING gin(to_tsvector('english', title || ' ' || description || ' ' || company_name));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profiles_fulltext_search 
ON profiles USING gin(to_tsvector('english', headline || ' ' || bio));

-- Add indexes for performance monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_worker_health_instance_id_created_at 
ON worker_health(instance_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_circuit_breaker_name_created_at 
ON circuit_breaker_state(name, created_at DESC);

-- Add indexes for billing and subscriptions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_billing_customers_user_id_status 
ON billing_customers(user_id, status) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_billing_subscriptions_customer_id_status 
ON billing_subscriptions(customer_id, status) WHERE customer_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_billing_invoices_customer_id_status 
ON billing_invoices(customer_id, status) WHERE customer_id IS NOT NULL;

-- Add indexes for marketplace and blueprints
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_marketplace_blueprints_author_status 
ON marketplace_blueprints(author_id, approval_status) WHERE author_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_marketplace_blueprints_category_created 
ON marketplace_blueprints(category, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_marketplace_blueprints_price_created 
ON marketplace_blueprints(price_cents, created_at DESC);

-- Add indexes for communication tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_communications_log_status_created 
ON email_communications_log(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notification_delivery_tracking_status_created 
ON notification_delivery_tracking(status, created_at DESC);

-- Add indexes for A/B testing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_experiment_assignments_experiment_user 
ON experiment_assignments(experiment_id, user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_experiment_results_experiment_variant 
ON experiment_results(experiment_id, variant_id);

-- Add indexes for vector database operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profile_embeddings_user_hash 
ON profile_embeddings(user_id, text_hash) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_profile_embeddings_hash_created 
ON profile_embeddings(text_hash, created_at DESC);

-- Add indexes for job sync and external data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_sync_jobs_source_created 
ON job_sync_jobs(source, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_sync_jobs_job_id_unique 
ON job_sync_jobs(job_id, source) WHERE job_id IS NOT NULL;

-- Add indexes for audit and compliance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_action_created_at 
ON audit_log(action, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_user_created_at 
ON audit_log(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Add indexes for bulk operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bulk_campaigns_status_created 
ON bulk_campaigns(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bulk_campaign_results_campaign_created 
ON bulk_campaign_results(campaign_id, created_at DESC);

-- Add indexes for interview sessions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interview_sessions_user_status_created 
ON interview_sessions(user_id, status, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interview_feedback_session_created 
ON interview_feedback(session_id, created_at DESC);

-- Add indexes for career path and recommendations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_career_path_recommendations_user_created 
ON career_path_recommendations(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_career_path_progress_user_created 
ON career_path_progress(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Add indexes for voice interviews
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_voice_interview_sessions_user_created 
ON voice_interview_sessions(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Add indexes for calendar integrations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_calendar_events_user_created 
ON calendar_events(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_calendar_events_provider_created 
ON calendar_events(provider, created_at DESC);

-- Add indexes for skills taxonomy
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_skills_taxonomy_category_name 
ON skills_taxonomy(category, name) WHERE name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_skills_taxonomy_parent_created 
ON skills_taxonomy(parent_id, created_at DESC) WHERE parent_id IS NOT NULL;

-- Add indexes for ATS recommendations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ats_recommendations_user_created 
ON ats_recommendations(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ats_recommendations_job_created 
ON ats_recommendations(job_id, created_at DESC) WHERE job_id IS NOT NULL;

-- Add indexes for communication preferences
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_preferences_user_created 
ON email_preferences(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notification_preferences_user_created 
ON notification_preferences(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Add indexes for semantic analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notification_semantic_tags_tag_created 
ON notification_semantic_tags(tag, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_interests_user_created 
ON user_interests(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Add indexes for batch processing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notification_batches_status_created 
ON notification_batches(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notification_batches_type_created 
ON notification_batches(batch_type, created_at DESC);

-- Add indexes for system health and monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_health_checks_name_created 
ON system_health_checks(check_name, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_health_checks_status_created 
ON system_health_checks(status, created_at DESC);

-- Add indexes for feature flags
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_feature_flags_key_created 
ON feature_flags(key, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_feature_flags_enabled_created 
ON feature_flags(enabled, created_at DESC);

-- Add indexes for experiments and A/B testing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_experiments_status_created 
ON experiments(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_experiment_variants_experiment_created 
ON experiment_variants(experiment_id, created_at DESC);

-- Add indexes for webhook delivery
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_webhook_delivery_status_created 
ON webhook_delivery(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_webhook_delivery_webhook_created 
ON webhook_delivery(webhook_id, created_at DESC) WHERE webhook_id IS NOT NULL;

-- Add indexes for API keys and authentication
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_user_status_created 
ON api_keys(user_id, is_active, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_prefix_created 
ON api_keys(key_prefix, created_at DESC);

-- Add indexes for SSO and authentication
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sso_sessions_user_created 
ON sso_sessions(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sso_sessions_token_created 
ON sso_sessions(session_token, created_at DESC);

-- Add indexes for multi-tenant operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenant_configurations_tenant_created 
ON tenant_configurations(tenant_id, created_at DESC) WHERE tenant_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenant_usage_tenant_created 
ON tenant_usage(tenant_id, created_at DESC) WHERE tenant_id IS NOT NULL;

-- Add indexes for data residency and compliance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_residency_logs_tenant_created 
ON data_residency_logs(tenant_id, created_at DESC) WHERE tenant_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_residency_logs_region_created 
ON data_residency_logs(source_region, created_at DESC);

-- Add indexes for external integrations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_integrations_user_provider_created 
ON integrations(user_id, provider, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_integrations_status_created 
ON integrations(status, created_at DESC);

-- Add indexes for push notifications
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_push_notification_tokens_user_created 
ON push_notification_tokens(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_push_notification_logs_status_created 
ON push_notification_logs(status, created_at DESC);

-- Add indexes for file processing and storage
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_file_processing_status_created 
ON file_processing(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_file_processing_type_created 
ON file_processing(file_type, created_at DESC);

-- Add indexes for background jobs and tasks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_background_jobs_status_created 
ON background_jobs(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_background_jobs_queue_created 
ON background_jobs(queue_name, created_at DESC);

-- Add indexes for error tracking and logging
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_error_logs_level_created 
ON error_logs(level, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_error_logs_service_created 
ON error_logs(service_name, created_at DESC);

-- Add indexes for performance metrics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_name_created 
ON performance_metrics(metric_name, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_service_created 
ON performance_metrics(service_name, created_at DESC);

-- Add indexes for user activity tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_user_created 
ON user_activity(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_activity_type_created 
ON user_activity(activity_type, created_at DESC);

-- Add indexes for session management
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_created 
ON sessions(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token_created 
ON sessions(session_token, created_at DESC);

-- Add indexes for cache invalidation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cache_invalidation_key_created 
ON cache_invalidation(cache_key, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cache_invalidation_pattern_created 
ON cache_invalidation(pattern, created_at DESC);

-- Add indexes for rate limiting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rate_limit_logs_key_created 
ON rate_limit_logs(rate_limit_key, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rate_limit_logs_status_created 
ON rate_limit_logs(status, created_at DESC);

-- Add indexes for security events
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_user_created 
ON security_events(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_type_created 
ON security_events(event_type, created_at DESC);

-- Add indexes for audit trails
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_trails_user_created 
ON audit_trails(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_trails_action_created 
ON audit_trails(action, created_at DESC);

-- Add indexes for data exports
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_exports_user_created 
ON data_exports(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_exports_type_created 
ON data_exports(export_type, created_at DESC);

-- Add indexes for backup operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backup_operations_status_created 
ON backup_operations(status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backup_operations_type_created 
ON backup_operations(operation_type, created_at DESC);

-- Add indexes for system configuration
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_configuration_key_created 
ON system_configuration(config_key, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_configuration_updated_created 
ON system_configuration(updated_at DESC);
