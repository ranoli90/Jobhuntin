-- +migrate Up
-- Missing Components Fix Migration
-- Creates all missing database tables identified in comprehensive audit

-- AI System Tables
CREATE TABLE IF NOT EXISTS skills_taxonomy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    aliases TEXT[] DEFAULT '{}',
    demand_score DECIMAL(3,2) DEFAULT 0.5,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab_testing_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'DRAFT',
    traffic_allocation DECIMAL(3,2) DEFAULT 0.5,
    target_metrics TEXT[] DEFAULT '{}',
    sample_size INTEGER DEFAULT 1000,
    duration_days INTEGER DEFAULT 30,
    target_audience JSONB DEFAULT '{}',
    ai_model_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    session_type VARCHAR(50) DEFAULT 'GENERAL',
    difficulty VARCHAR(50) DEFAULT 'MEDIUM',
    question_count INTEGER DEFAULT 10,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    questions JSONB DEFAULT '[]',
    responses JSONB DEFAULT '[]',
    feedback JSONB DEFAULT '[]',
    total_score DECIMAL(3,2) DEFAULT 0.0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS voice_interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    voice_settings JSONB DEFAULT '{}',
    audio_files JSONB DEFAULT '[]',
    transcriptions JSONB DEFAULT '[]',
    voice_analytics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Improvements Tables
CREATE TABLE IF NOT EXISTS button_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    button_id VARCHAR(255) NOT NULL,
    button_type VARCHAR(50) NOT NULL CHECK (button_type IN ('submit', 'apply', 'next', 'continue', 'save', 'cancel', 'back', 'skip', 'upload', 'download', 'login', 'sign_in', 'register', 'sign_up', 'accept', 'decline', 'agree', 'disagree', 'confirm', 'yes', 'no', 'custom')),
    text TEXT NOT NULL,
    selector TEXT NOT NULL,
    xpath TEXT NOT NULL,
    coordinates JSONB NOT NULL,
    is_visible BOOLEAN DEFAULT true,
    is_enabled BOOLEAN DEFAULT true,
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    attributes JSONB DEFAULT '{}',
    detection_method VARCHAR(50) DEFAULT 'text',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS form_field_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    field_id VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    label TEXT NOT NULL,
    selector TEXT NOT NULL,
    xpath TEXT NOT NULL,
    is_required BOOLEAN DEFAULT false,
    is_visible BOOLEAN DEFAULT true,
    is_enabled BOOLEAN DEFAULT true,
    validation_rules TEXT[] DEFAULT '{}',
    placeholder TEXT,
    max_length INTEGER,
    accepted_file_types TEXT[] DEFAULT '{}',
    detection_method VARCHAR(50) DEFAULT 'html',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS oauth_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL CHECK (provider IN ('google', 'linkedin', 'microsoft', 'github', 'facebook', 'twitter', 'salesforce', 'workday', 'custom')),
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    scopes TEXT[] DEFAULT '{}',
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS concurrent_usage_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_type VARCHAR(50) DEFAULT 'agent_task',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    original_data JSONB NOT NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'PENDING',
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS screenshot_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_description TEXT NOT NULL,
    screenshot_path TEXT NOT NULL,
    thumbnail_path TEXT,
    viewport_size JSONB NOT NULL,
    full_page BOOLEAN DEFAULT false,
    elements_highlighted TEXT[] DEFAULT '{}',
    file_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_type_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    file_path TEXT,
    file_size INTEGER,
    mime_type VARCHAR(100),
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    processing_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    metric_unit VARCHAR(50),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Communication System Tables
CREATE TABLE IF NOT EXISTS email_communications_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email_type VARCHAR(100) NOT NULL,
    template_name VARCHAR(100),
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    content TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    provider VARCHAR(50),
    external_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    frequency VARCHAR(50) DEFAULT 'immediate',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, tenant_id, category)
);

CREATE TABLE IF NOT EXISTS notification_semantic_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    weight DECIMAL(3,2) DEFAULT 1.0,
    keywords TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    interest_category VARCHAR(100) NOT NULL,
    interest_keywords TEXT[] DEFAULT '{}',
    relevance_score DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_delivery_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    notification_id UUID NOT NULL,
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Experience Tables
CREATE TABLE IF NOT EXISTS resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    version_name VARCHAR(100) NOT NULL,
    file_path TEXT,
    file_size INTEGER,
    mime_type VARCHAR(100),
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS follow_up_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    difficulty VARCHAR(50),
    answer TEXT,
    feedback JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS answer_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    question_id UUID REFERENCES interview_questions(id) ON DELETE CASCADE,
    attempt_text TEXT NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    feedback JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS application_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    note_type VARCHAR(50) DEFAULT 'general',
    is_private BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_skills_taxonomy_category ON skills_taxonomy(category);
CREATE INDEX IF NOT EXISTS idx_skills_taxonomy_name ON skills_taxonomy(skill_name);
CREATE INDEX IF NOT EXISTS idx_ab_testing_experiments_status ON ab_testing_experiments(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_id ON interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_voice_interview_sessions_session_id ON voice_interview_sessions(interview_session_id);
CREATE INDEX IF NOT EXISTS idx_button_detections_application_id ON button_detections(application_id);
CREATE INDEX IF NOT EXISTS idx_form_field_detections_application_id ON form_field_detections(application_id);
CREATE INDEX IF NOT EXISTS idx_oauth_credentials_tenant_id ON oauth_credentials(tenant_id);
CREATE INDEX IF NOT EXISTS idx_concurrent_usage_sessions_user_id ON concurrent_usage_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_status ON dead_letter_queue(status);
CREATE INDEX IF NOT EXISTS idx_screenshot_captures_application_id ON screenshot_captures(application_id);
CREATE INDEX IF NOT EXISTS idx_document_type_tracking_application_id ON document_type_tracking(application_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_application_id ON agent_performance_metrics(application_id);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_user_id ON email_communications_log(user_id);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_status ON email_communications_log(status);
CREATE INDEX IF NOT EXISTS idx_email_preferences_user_id ON email_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_semantic_tags_category ON notification_semantic_tags(category);
CREATE INDEX IF NOT EXISTS idx_user_interests_user_id ON user_interests(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_user_id ON notification_delivery_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_resume_versions_user_id ON resume_versions(user_id);
CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_user_id ON follow_up_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_application_id ON follow_up_reminders(application_id);
CREATE INDEX IF NOT EXISTS idx_interview_questions_user_id ON interview_questions(user_id);
CREATE INDEX IF NOT EXISTS idx_answer_attempts_user_id ON answer_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_answer_attempts_question_id ON answer_attempts(question_id);
CREATE INDEX IF NOT EXISTS idx_application_notes_application_id ON application_notes(application_id);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to all tables
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY [
        'skills_taxonomy',
        'ab_testing_experiments',
        'interview_sessions',
        'voice_interview_sessions',
        'button_detections',
        'form_field_detections',
        'oauth_credentials',
        'concurrent_usage_sessions',
        'dead_letter_queue',
        'screenshot_captures',
        'document_type_tracking',
        'agent_performance_metrics',
        'email_communications_log',
        'email_preferences',
        'notification_semantic_tags',
        'user_interests',
        'notification_delivery_tracking',
        'resume_versions',
        'follow_up_reminders',
        'interview_questions',
        'answer_attempts',
        'application_notes'
    ]
    LOOP
        BEGIN
            EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();', table_name, table_name);
        EXCEPTION WHEN duplicate_object THEN
            -- Trigger already exists, continue
            NULL;
        END;
    END LOOP;
END $$;

-- +migrate Down
-- Rollback missing components migration
DROP TABLE IF EXISTS application_notes;
DROP TABLE IF EXISTS answer_attempts;
DROP TABLE IF EXISTS interview_questions;
DROP TABLE IF EXISTS follow_up_reminders;
DROP TABLE IF EXISTS resume_versions;
DROP TABLE IF EXISTS notification_delivery_tracking;
DROP TABLE IF EXISTS user_interests;
DROP TABLE IF EXISTS notification_semantic_tags;
DROP TABLE IF EXISTS email_preferences;
DROP TABLE IF EXISTS email_communications_log;
DROP TABLE IF EXISTS agent_performance_metrics;
DROP TABLE IF EXISTS document_type_tracking;
DROP TABLE IF EXISTS screenshot_captures;
DROP TABLE IF EXISTS dead_letter_queue;
DROP TABLE IF EXISTS concurrent_usage_sessions;
DROP TABLE IF EXISTS oauth_credentials;
DROP TABLE IF EXISTS form_field_detections;
DROP TABLE IF EXISTS button_detections;
DROP TABLE IF EXISTS voice_interview_sessions;
DROP TABLE IF EXISTS interview_sessions;
DROP TABLE IF EXISTS ab_testing_experiments;
DROP TABLE IF EXISTS skills_taxonomy;

DROP FUNCTION IF EXISTS update_updated_at_column();
