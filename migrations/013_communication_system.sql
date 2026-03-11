-- Phase 13.1 Communication System Database Migration
-- Tables for email communications, notifications, semantic matching, alerts, and batch processing

-- Email communications log table
CREATE TABLE IF NOT EXISTS email_communications_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    template_id UUID REFERENCES email_templates(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    to_email TEXT NOT NULL,
    from_email TEXT NOT NULL DEFAULT 'noreply@jobhuntin.com',
    reply_to TEXT,
    category TEXT NOT NULL DEFAULT 'general',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'bounced')),
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    delivery_provider TEXT NOT NULL DEFAULT 'resend',
    external_id TEXT,
    variables JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    subject_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    variables TEXT[] DEFAULT '{}',
    category TEXT NOT NULL DEFAULT 'general',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email preferences table
CREATE TABLE IF NOT EXISTS email_preferences (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT true,
    categories JSONB DEFAULT '{}',
    frequency_limits JSONB DEFAULT '{}',
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, tenant_id)
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    channels TEXT[] DEFAULT ARRAY['in_app'],
    data JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User preferences table (enhanced for notifications)
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    in_app_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    categories JSONB DEFAULT '{}',
    do_not_disturb_enabled BOOLEAN DEFAULT false,
    do_not_disturb_start TIME,
    do_not_disturb_end TIME,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, tenant_id)
);

-- Notification delivery tracking table
CREATE TABLE IF NOT EXISTS notification_delivery_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    channel TEXT NOT NULL CHECK (channel IN ('in_app', 'email', 'push', 'sms')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'read')),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notification batches table
CREATE TABLE IF NOT EXISTS notification_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id TEXT NOT NULL,
    total_notifications INTEGER NOT NULL,
    successful INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alert processing log table
CREATE TABLE IF NOT EXISTS alert_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'failed', 'resolved')),
    processed_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alert rules table
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    conditions JSONB NOT NULL,
    actions TEXT[] NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    enabled BOOLEAN DEFAULT true,
    throttle_minutes INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alert processing actions table
CREATE TABLE IF NOT EXISTS alert_processing_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL REFERENCES alert_processing_log(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
    result JSONB DEFAULT '{}',
    error_message TEXT,
    processing_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User interest profiles table
CREATE TABLE IF NOT EXISTS user_interest_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    interests JSONB DEFAULT '{}',
    keywords JSONB DEFAULT '{}',
    interaction_history JSONB DEFAULT '[]',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, tenant_id)
);

-- User interactions table
CREATE TABLE IF NOT EXISTS user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    interaction_type TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB DEFAULT '{}'
);

-- Notification relevance scores table
CREATE TABLE IF NOT EXISTS notification_relevance_scores (
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2) NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    category_scores JSONB DEFAULT '{}',
    keyword_matches TEXT[] DEFAULT '{}',
    semantic_factors JSONB DEFAULT '{}',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (notification_id, user_id)
);

-- Notification batches (for batch processing)
CREATE TABLE IF NOT EXISTS notification_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_ids TEXT[] NOT NULL,
    notification_template JSONB NOT NULL,
    batch_size INTEGER NOT NULL DEFAULT 100,
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User notification batches table
CREATE TABLE IF NOT EXISTS user_notification_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES notification_batches(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    notification_data JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'sent', 'failed', 'skipped')),
    error_message TEXT,
    processing_attempts INTEGER NOT NULL DEFAULT 0,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Batch processing results table
CREATE TABLE IF NOT EXISTS batch_processing_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES notification_batches(id) ON DELETE CASCADE,
    total_users INTEGER NOT NULL,
    successful INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    skipped INTEGER NOT NULL,
    processing_time_seconds DECIMAL(8,2) NOT NULL,
    error_details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_email_communications_log_user_id ON email_communications_log(user_id);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_tenant_id ON email_communications_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_status ON email_communications_log(status);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_category ON email_communications_log(category);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_created_at ON email_communications_log(created_at);

CREATE INDEX IF NOT EXISTS idx_email_templates_category ON email_templates(category);
CREATE INDEX IF NOT EXISTS idx_email_templates_is_active ON email_templates(is_active);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_tenant_id ON notifications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(category);
CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_tenant_id ON user_preferences(tenant_id);

CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_notification_id ON notification_delivery_tracking(notification_id);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_user_id ON notification_delivery_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_tenant_id ON notification_delivery_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_channel ON notification_delivery_tracking(channel);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_status ON notification_delivery_tracking(status);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_created_at ON notification_delivery_tracking(created_at);

CREATE INDEX IF NOT EXISTS idx_alert_processing_log_user_id ON alert_processing_log(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_tenant_id ON alert_processing_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_alert_type ON alert_processing_log(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_priority ON alert_processing_log(priority);
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_status ON alert_processing_log(status);
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_created_at ON alert_processing_log(created_at);

CREATE INDEX IF NOT EXISTS idx_alert_rules_alert_type ON alert_rules(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled);

CREATE INDEX IF NOT EXISTS idx_user_interest_profiles_user_id ON user_interest_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interest_profiles_tenant_id ON user_interest_profiles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_interest_profiles_last_updated ON user_interest_profiles(last_updated);

CREATE INDEX IF NOT EXISTS idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_tenant_id ON user_interactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_category ON user_interactions(category);
CREATE INDEX IF NOT EXISTS idx_user_interactions_timestamp ON user_interactions(timestamp);

CREATE INDEX IF NOT EXISTS idx_notification_relevance_scores_user_id ON notification_relevance_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_relevance_scores_relevance_score ON notification_relevance_scores(relevance_score);
CREATE INDEX IF NOT EXISTS idx_notification_relevance_scores_calculated_at ON notification_relevance_scores(calculated_at);

CREATE INDEX IF NOT EXISTS idx_notification_batches_tenant_id ON notification_batches(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notification_batches_status ON notification_batches(status);
CREATE INDEX IF NOT EXISTS idx_notification_batches_priority ON notification_batches(priority);
CREATE INDEX IF NOT EXISTS idx_notification_batches_created_at ON notification_batches(created_at);

CREATE INDEX IF NOT EXISTS idx_user_notification_batches_batch_id ON user_notification_batches(batch_id);
CREATE INDEX IF NOT EXISTS idx_user_notification_batches_user_id ON user_notification_batches(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notification_batches_tenant_id ON user_notification_batches(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_notification_batches_status ON user_notification_batches(status);
CREATE INDEX IF NOT EXISTS idx_user_notification_batches_created_at ON user_notification_batches(created_at);

CREATE INDEX IF NOT EXISTS idx_batch_processing_results_batch_id ON batch_processing_results(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_processing_results_created_at ON batch_processing_results(created_at);

-- Enable Row Level Security
ALTER TABLE email_communications_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_delivery_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_processing_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_interest_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_relevance_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_notification_batches ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view their own email communications" ON email_communications_log
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own email preferences" ON email_preferences
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own notifications" ON notifications
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own notification preferences" ON user_preferences
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own notification delivery tracking" ON notification_delivery_tracking
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own alerts" ON alert_processing_log
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own interest profiles" ON user_interest_profiles
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own interactions" ON user_interactions
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id') AND
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own relevance scores" ON notification_relevance_scores
    FOR ALL USING (
        user_id = current_setting('app.current_user_id')
    );

CREATE POLICY "Users can view their own notification batches" ON notification_batches
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant_id')
    );

CREATE POLICY "Users can view their own user notification batches" ON user_notification_batches
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
CREATE TRIGGER set_email_communications_log_updated_at
    BEFORE UPDATE ON email_communications_log
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_email_preferences_updated_at
    BEFORE UPDATE ON email_preferences
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_notifications_updated_at
    BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_notification_delivery_tracking_updated_at
    BEFORE UPDATE ON notification_delivery_tracking
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_alert_processing_log_updated_at
    BEFORE UPDATE ON alert_processing_log
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_user_interest_profiles_updated_at
    BEFORE UPDATE ON user_interest_profiles
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_notification_batches_updated_at
    BEFORE UPDATE ON notification_batches
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_user_notification_batches_updated_at
    BEFORE UPDATE ON user_notification_batches
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

-- Insert initial data
-- Default email templates
INSERT INTO email_templates (id, name, subject_template, body_template, variables, category) VALUES
    (gen_random_uuid(), 'Application Success', 'Application Submitted Successfully', 'Dear {{user_name}},\n\nYour application for {{job_title}} at {{company_name}} has been successfully submitted!\n\n{{message}}\n\nBest regards,\nJobHuntin Team', ARRAY['user_name', 'job_title', 'company_name', 'message'], 'application_status'),
    (gen_random_uuid(), 'Application Failed', 'Application Failed', 'Dear {{user_name}},\n\nWe encountered an issue while submitting your application for {{job_title}} at {{company_name}}.\n\n{{error_message}}\n\nPlease try again or contact support.\n\nBest regards,\nJobHuntin Team', ARRAY['user_name', 'job_title', 'company_name', 'error_message'], 'application_status'),
    (gen_random_uuid(), 'Rate Limit Warning', 'Usage Limit Warning', 'Dear {{user_name}},\n\nYou are approaching your usage limit for {{feature}}.\n\nCurrent usage: {{current_usage}}/{{limit}}\n\nConsider upgrading your plan for unlimited access.\n\nBest regards,\nJobHuntin Team', ARRAY['user_name', 'feature', 'current_usage', 'limit'], 'usage_limits')
ON CONFLICT DO NOTHING;

-- Default alert rules
INSERT INTO alert_rules (id, name, alert_type, conditions, actions, priority) VALUES
    (gen_random_uuid(), 'Application Success Notification', 'application_success', '{}', ARRAY['send_notification'], 'medium'),
    (gen_random_uuid(), 'Application Failed Alert', 'application_failed', '{}', ARRAY['send_notification', 'send_email'], 'high'),
    (gen_random_uuid(), 'Rate Limit Warning', 'rate_limit_warning', '{}', ARRAY['send_notification'], 'medium'),
    (gen_random_uuid(), 'Rate Limit Reached', 'rate_limit_reached', '{}', ARRAY['send_notification', 'send_email', 'suspend_service'], 'high'),
    (gen_random_uuid(), 'Security Alert', 'security_alert', '{}', ARRAY['send_notification', 'send_email', 'log_security_event'], 'critical')
ON CONFLICT DO NOTHING;

-- Default user interests
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
