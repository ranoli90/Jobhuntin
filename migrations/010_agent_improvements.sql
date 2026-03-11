-- Phase 12.1 Agent Improvements Database Migration
-- Tables for enhanced button detection, OAuth handling, document types, concurrent usage tracking, DLQ management, screenshot capture

-- Enhanced button detection table
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
    coordinates JSONB NOT NULL, -- {x, y, width, height}
    is_visible BOOLEAN DEFAULT true,
    is_enabled BOOLEAN DEFAULT true,
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    attributes JSONB DEFAULT '{}',
    detection_method VARCHAR(50) DEFAULT 'text', -- text, attributes, visual, ml
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced form field detection table
CREATE TABLE IF NOT EXISTS form_field_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    field_id VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL, -- text, email, password, file, select, checkbox, radio, textarea
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
    detection_method VARCHAR(50) DEFAULT 'html', -- html, custom, dynamic
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OAuth credentials table
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

-- Screenshot capture table
CREATE TABLE IF NOT EXISTS screenshot_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_description TEXT NOT NULL,
    screenshot_path TEXT NOT NULL,
    thumbnail_path TEXT,
    viewport_size JSONB NOT NULL, -- {width, height}
    full_page BOOLEAN DEFAULT false,
    elements_highlighted TEXT[] DEFAULT '{}',
    error_detected BOOLEAN DEFAULT false,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Concurrent usage sessions table
CREATE TABLE IF NOT EXISTS concurrent_usage_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'cancelled')),
    steps_completed INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    screenshots_captured INTEGER DEFAULT 0,
    buttons_detected INTEGER DEFAULT 0,
    forms_processed INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dead Letter Queue table
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    failure_reason TEXT NOT NULL,
    error_details JSONB DEFAULT '{}',
    attempt_count INTEGER DEFAULT 1,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    payload JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'retrying', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document type tracking table
CREATE TABLE IF NOT EXISTS document_type_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tracking_id VARCHAR(255) NOT NULL,
    file_name TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    document_type VARCHAR(50) NOT NULL, -- pdf, docx, doc, txt, rtf, jpeg, png, tiff, bmp
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    content_preview TEXT,
    metadata JSONB DEFAULT '{}',
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent performance metrics table
CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_id VARCHAR(255) NOT NULL,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL, -- button_detection_accuracy, form_field_detection_accuracy, screenshot_capture_time, processing_time, success_rate, error_rate, concurrent_sessions, memory_usage, cpu_usage
    metric_value DECIMAL(10,2) NOT NULL,
    metric_unit VARCHAR(50), -- percentage, milliseconds, seconds, count, megabytes
    metadata JSONB DEFAULT '{}',
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notification semantic tags table (missing from Phase 13.1)
CREATE TABLE IF NOT EXISTS notification_semantic_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notification_delivery_tracking(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- job_match, application_status, security, marketing, usage_limits, reminders
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    context JSONB DEFAULT '{}',
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User interests table (missing from Phase 13.1)
CREATE TABLE IF NOT EXISTS user_interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    interest_category VARCHAR(100) NOT NULL, -- technology, healthcare, finance, education, government
    interest_keywords TEXT[] DEFAULT '{}',
    interest_score DECIMAL(3,2) DEFAULT 0.0 CHECK (interest_score >= 0 AND confidence_score <= 1),
    is_active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_button_detections_application_id ON button_detections(application_id);
CREATE INDEX IF NOT EXISTS idx_button_detections_tenant_id ON button_detections(tenant_id);
CREATE INDEX IF NOT EXISTS idx_button_detections_created_at ON button_detections(created_at);

CREATE INDEX IF NOT EXISTS idx_form_field_detections_application_id ON form_field_detections(application_id);
CREATE INDEX IF NOT EXISTS idx_form_field_detections_tenant_id ON form_field_detections(tenant_id);
CREATE INDEX IF NOT EXISTS idx_form_field_detections_created_at ON form_field_detections(created_at);

CREATE INDEX IF NOT EXISTS idx_oauth_credentials_tenant_id ON oauth_credentials(tenant_id);
CREATE INDEX IF NOT EXISTS idx_oauth_credentials_provider ON oauth_credentials(provider);

CREATE INDEX IF NOT EXISTS idx_screenshot_captures_application_id ON screenshot_captures(application_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_captures_tenant_id ON screenshot_captures(tenant_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_captures_created_at ON screenshot_captures(created_at);

CREATE INDEX IF NOT EXISTS idx_concurrent_usage_sessions_tenant_id ON concurrent_usage_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_concurrent_usage_sessions_status ON concurrent_usage_sessions(status);
CREATE INDEX IF NOT EXISTS idx_concurrent_usage_sessions_created_at ON concurrent_usage_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_tenant_id ON dead_letter_queue(tenant_id);
CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_status ON dead_letter_queue(status);
CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_next_retry_at ON dead_letter_queue(next_retry_at);
CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_created_at ON dead_letter_queue(created_at);

CREATE INDEX IF NOT EXISTS idx_document_type_tracking_tenant_id ON document_type_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_document_type_tracking_document_type ON document_type_tracking(document_type);
CREATE INDEX IF NOT EXISTS idx_document_type_tracking_created_at ON document_type_tracking(created_at);

CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_tenant_id ON agent_performance_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_application_id ON agent_performance_metrics(application_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_metric_type ON agent_performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_created_at ON agent_performance_metrics(created_at);

CREATE INDEX IF NOT EXISTS idx_notification_semantic_tags_notification_id ON notification_semantic_tags(notification_id);
CREATE INDEX IF NOT EXISTS idx_notification_semantic_tags_tenant_id ON notification_semantic_tags(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notification_semantic_tags_category ON notification_semantic_tags(category);

CREATE INDEX IF NOT EXISTS idx_user_interests_user_id ON user_interests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interests_tenant_id ON user_interests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_interests_category ON user_interests(interest_category);
CREATE INDEX IF NOT EXISTS idx_user_interests_is_active ON user_interests(is_active);

-- Enable Row Level Security
ALTER TABLE button_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE form_field_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE screenshot_captures ENABLE ROW LEVEL SECURITY;
ALTER TABLE concurrent_usage_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE dead_letter_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_type_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_semantic_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_interests ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view their own button detections" ON button_detections
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own form field detections" ON form_field_detections
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own oauth credentials" ON oauth_credentials
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id')
    );

CREATE POLICY "Users can view their own screenshot captures" ON screenshot_captures
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own concurrent usage sessions" ON concurrent_usage_sessions
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own dead letter queue items" ON dead_letter_queue
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id')
    );

CREATE POLICY "Users can view their own document type tracking" ON document_type_tracking
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id')
    );

CREATE POLICY "Users can view their own agent performance metrics" ON agent_performance_metrics
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id')
    );

CREATE POLICY "Users can view their own notification semantic tags" ON notification_semantic_tags
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id')
    );

CREATE POLICY "Users can view their own user interests" ON user_interests
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

-- Create functions for updated_at triggers
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER set_button_detections_updated_at
    BEFORE UPDATE ON button_detections
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_form_field_detections_updated_at
    BEFORE UPDATE ON form_field_detections
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_oauth_credentials_updated_at
    BEFORE UPDATE ON oauth_credentials
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_screenshot_captures_updated_at
    BEFORE UPDATE ON screenshot_captures
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_concurrent_usage_sessions_updated_at
    BEFORE UPDATE ON concurrent_usage_sessions
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_dead_letter_queue_updated_at
    BEFORE UPDATE ON dead_letter_queue
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_document_type_tracking_updated_at
    BEFORE UPDATE ON document_type_tracking
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_user_interests_updated_at
    BEFORE UPDATE ON user_interests
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

-- Insert initial data
INSERT INTO user_interests (user_id, tenant_id, interest_category, interest_keywords, interest_score)
SELECT 
    id,
    tenant_id,
    'technology',
    ARRAY['software', 'programming', 'development', 'engineering', 'tech'],
    0.8
FROM users
WHERE id IS NOT NULL
ON CONFLICT DO NOTHING;

COMMIT;
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL CHECK (provider IN ('google', 'linkedin', 'microsoft', 'github', 'facebook', 'twitter', 'salesforce', 'workday', 'ultimateprocurer', 'custom')),
    client_id VARCHAR(255) NOT NULL,
    client_secret TEXT NOT NULL, -- Encrypted in production
    redirect_uri TEXT NOT NULL,
    scopes TEXT[] DEFAULT '{}',
    access_token TEXT, -- Encrypted in production
    refresh_token TEXT, -- Encrypted in production
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Screenshot capture table
CREATE TABLE IF NOT EXISTS screenshot_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    capture_id VARCHAR(255) NOT NULL UNIQUE,
    step_number INTEGER NOT NULL,
    step_description TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    screenshot_path TEXT NOT NULL,
    thumbnail_path TEXT,
    viewport_size JSONB NOT NULL, -- {width, height}
    full_page BOOLEAN DEFAULT false,
    elements_highlighted TEXT[] DEFAULT '{}',
    error_detected BOOLEAN DEFAULT false,
    error_message TEXT,
    file_size BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Concurrent usage tracking table
CREATE TABLE IF NOT EXISTS concurrent_usage_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'cancelled')),
    steps_completed INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    screenshots_captured INTEGER DEFAULT 0,
    buttons_detected INTEGER DEFAULT 0,
    forms_processed INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced DLQ table (if not exists, create it)
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    failure_reason TEXT NOT NULL,
    error_details JSONB DEFAULT '{}',
    attempt_count INTEGER DEFAULT 1,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    payload JSONB NOT NULL,
    priority INTEGER DEFAULT 0, -- Higher priority = retry sooner
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'retrying', 'completed', 'failed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document type tracking table
CREATE TABLE IF NOT EXISTS document_type_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    document_type VARCHAR(10) NOT NULL CHECK (document_type IN ('pdf', 'docx', 'doc', 'txt', 'rtf', 'odt', 'png', 'jpeg', 'jpg', 'tiff', 'bmp', 'gif')),
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT NOT NULL,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processing_details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent performance metrics table
CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- button_detection, form_detection, oauth_flow, screenshot_capture, etc.
    metric_value DECIMAL(10,2) NOT NULL,
    metric_unit VARCHAR(20), -- count, seconds, percentage, score
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_button_detections_application ON button_detections(application_id);
CREATE INDEX IF NOT EXISTS idx_button_detections_user_tenant ON button_detections(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_button_detections_type ON button_detections(button_type);
CREATE INDEX IF NOT EXISTS idx_button_detections_confidence ON button_detections(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_form_field_detections_application ON form_field_detections(application_id);
CREATE INDEX IF NOT EXISTS idx_form_field_detections_user_tenant ON form_field_detections(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_form_field_detections_type ON form_field_detections(field_type);
CREATE INDEX IF NOT EXISTS idx_form_field_detections_required ON form_field_detections(is_required);

CREATE INDEX IF NOT EXISTS idx_oauth_credentials_tenant_provider ON oauth_credentials(tenant_id, provider);
CREATE INDEX IF NOT EXISTS idx_oauth_credentials_active ON oauth_credentials(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_screenshot_captures_application ON screenshot_captures(application_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_captures_user_tenant ON screenshot_captures(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_captures_timestamp ON screenshot_captures(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_screenshot_captures_step ON screenshot_captures(application_id, step_number);

CREATE INDEX IF NOT EXISTS idx_concurrent_usage_sessions_user_tenant ON concurrent_usage_sessions(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_concurrent_usage_sessions_status ON concurrent_usage_sessions(status);
CREATE INDEX IF NOT EXISTS idx_concurrent_usage_sessions_start_time ON concurrent_usage_sessions(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_concurrent_usage_sessions_session_id ON concurrent_usage_sessions(session_id);

CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_application ON dead_letter_queue(application_id);
CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_tenant ON dead_letter_queue(tenant_id);
CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_status_priority ON dead_letter_queue(status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_dead_letter_queue_next_retry ON dead_letter_queue(next_retry_at) WHERE next_retry_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_document_type_tracking_application ON document_type_tracking(application_id);
CREATE INDEX IF NOT EXISTS idx_document_type_tracking_user_tenant ON document_type_tracking(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_document_type_tracking_type ON document_type_tracking(document_type);
CREATE INDEX IF NOT EXISTS idx_document_type_tracking_status ON document_type_tracking(processing_status);

CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_application ON agent_performance_metrics(application_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_user_tenant ON agent_performance_metrics(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_type ON agent_performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metrics_timestamp ON agent_performance_metrics(timestamp DESC);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_button_detections_search ON button_detections USING gin(to_tsvector('english', text || ' ' || selector));
CREATE INDEX IF NOT EXISTS idx_form_field_detections_search ON form_field_detections USING gin(to_tsvector('english', label || ' ' || selector));

-- Enable RLS (Row Level Security)
ALTER TABLE button_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE form_field_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE screenshot_captures ENABLE ROW LEVEL SECURITY;
ALTER TABLE concurrent_usage_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE dead_letter_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_type_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_performance_metrics ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own button detections" ON button_detections
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own button detections" ON button_detections
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own button detections" ON button_detections
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own button detections" ON button_detections
    FOR DELETE USING (user_id = current_user_id());

-- Similar policies for other tables...
CREATE POLICY "Users can view their own form field detections" ON form_field_detections
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own form field detections" ON form_field_detections
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own form field detections" ON form_field_detections
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own form field detections" ON form_field_detections
    FOR DELETE USING (user_id = current_user_id());

CREATE POLICY "Tenants can manage their OAuth credentials" ON oauth_credentials
    FOR ALL USING (tenant_id = current_setting('app.tenant_id'));

CREATE POLICY "Users can view their own screenshot captures" ON screenshot_captures
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own screenshot captures" ON screenshot_captures
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own screenshot captures" ON screenshot_captures
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own screenshot captures" ON screenshot_captures
    FOR DELETE USING (user_id = current_user_id());

CREATE POLICY "Users can view their own concurrent sessions" ON concurrent_usage_sessions
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own concurrent sessions" ON concurrent_usage_sessions
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own concurrent sessions" ON concurrent_usage_sessions
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own concurrent sessions" ON concurrent_usage_sessions
    FOR DELETE USING (user_id = current_user_id());

CREATE POLICY "Users can view their own DLQ items" ON dead_letter_queue
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own DLQ items" ON dead_letter_queue
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own DLQ items" ON dead_letter_queue
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own DLQ items" ON dead_letter_queue
    FOR DELETE USING (user_id = current_user_id());

CREATE POLICY "Users can view their own document tracking" ON document_type_tracking
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own document tracking" ON document_type_tracking
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own document tracking" ON document_type_tracking
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own document tracking" ON document_type_tracking
    FOR DELETE USING (user_id = current_user_id());

CREATE POLICY "Users can view their own performance metrics" ON agent_performance_metrics
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own performance metrics" ON agent_performance_metrics
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own performance metrics" ON agent_performance_metrics
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own performance metrics" ON agent_performance_metrics
    FOR DELETE USING (user_id = current_user_id());

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_button_detections_updated_at BEFORE UPDATE ON button_detections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_form_field_detections_updated_at BEFORE UPDATE ON form_field_detections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_oauth_credentials_updated_at BEFORE UPDATE ON oauth_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_screenshot_captures_updated_at BEFORE UPDATE ON screenshot_captures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concurrent_usage_sessions_updated_at BEFORE UPDATE ON concurrent_usage_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dead_letter_queue_updated_at BEFORE UPDATE ON dead_letter_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_type_tracking_updated_at BEFORE UPDATE ON document_type_tracking
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_performance_metrics_updated_at BEFORE UPDATE ON agent_performance_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE button_detections IS 'Enhanced button detection results with multiple detection strategies';
COMMENT ON TABLE form_field_detections IS 'Enhanced form field detection with validation rules';
COMMENT ON TABLE oauth_credentials IS 'OAuth/SSO credentials for external service integration';
COMMENT ON TABLE screenshot_captures IS 'Screenshot captures with metadata for debugging and analysis';
COMMENT ON TABLE concurrent_usage_sessions IS 'Concurrent usage tracking for performance monitoring';
COMMENT ON TABLE dead_letter_queue IS 'Dead Letter Queue for failed application processing';
COMMENT ON TABLE document_type_tracking IS 'Document type tracking for upload processing';
COMMENT ON TABLE agent_performance_metrics IS 'Agent performance metrics for optimization and monitoring';
