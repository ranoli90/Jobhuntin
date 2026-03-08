-- Phase 14.1 User Experience Database Migration
-- Creates tables for UI analytics, feedback, A/B testing, user behavior analysis, and UX metrics

-- UI Analytics Tables
CREATE TABLE IF NOT EXISTS page_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    session_id TEXT NOT NULL,
    page_url TEXT NOT NULL,
    page_title TEXT,
    referrer TEXT,
    user_agent TEXT,
    ip_address TEXT,
    device_type TEXT DEFAULT 'web',
    browser TEXT,
    screen_resolution TEXT,
    load_time DOUBLE PRECISION,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    time_on_page INTEGER,
    scroll_depth DOUBLE PRECISION,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_page_views_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_page_views_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    session_id TEXT NOT NULL,
    page_url TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_name TEXT NOT NULL,
    element_selector TEXT,
    element_text TEXT,
    element_attributes JSONB,
    coordinates JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_user_actions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_actions_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversion_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_name TEXT NOT NULL,
    page_url TEXT NOT NULL,
    conversion_value DOUBLE PRECISION,
    conversion_currency TEXT,
    funnel_step INTEGER,
    funnel_name TEXT,
    properties JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_conversion_events_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_conversion_events_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS funnel_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    funnel_name TEXT NOT NULL,
    total_users INTEGER NOT NULL,
    step_analytics JSONB NOT NULL,
    conversion_rate DOUBLE PRECISION NOT NULL,
    abandonment_rate DOUBLE PRECISION NOT NULL,
    avg_time_to_convert INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_funnel_analyses_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Feedback System Tables
CREATE TABLE IF NOT EXISTS feedback_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    feedback_type TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    sentiment_score DOUBLE PRECISION,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    page_url TEXT,
    session_id TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved', 'rejected')),
    admin_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_feedback_responses_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_feedback_responses_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_feedback_categories_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE(tenant_id, name)
);

CREATE TABLE IF NOT EXISTS nps_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 10),
    promoter_type TEXT NOT NULL CHECK (promoter_type IN ('promoter', 'passive', 'detractor')),
    reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_nps_responses_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_nps_responses_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    analysis_type TEXT NOT NULL,
    period_days INTEGER NOT NULL,
    total_responses INTEGER NOT NULL,
    average_rating DOUBLE PRECISION,
    sentiment_distribution JSONB,
    category_distribution JSONB,
    nps_score INTEGER,
    nps_distribution JSONB,
    key_themes JSONB,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_feedback_analyses_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- A/B Testing Tables
CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'running', 'paused', 'completed', 'cancelled')),
    traffic_allocation DOUBLE PRECISION DEFAULT 1.0,
    sample_size INTEGER NOT NULL,
    duration_days INTEGER NOT NULL,
    target_metrics JSONB NOT NULL,
    target_audience JSONB,
    ai_model_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_experiments_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS experiment_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    variant_type TEXT NOT NULL,
    configuration JSONB NOT NULL,
    traffic_weight DOUBLE PRECISION DEFAULT 1.0,
    traffic_allocation DOUBLE PRECISION,
    is_control BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_experiment_variants_experiment FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    experiment_id UUID NOT NULL,
    variant_id UUID NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_user_assignments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_assignments_experiment FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_assignments_variant FOREIGN KEY (variant_id) REFERENCES experiment_variants(id) ON DELETE CASCADE,
    UNIQUE(user_id, experiment_id)
);

CREATE TABLE IF NOT EXISTS experiment_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL,
    variant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_experiment_results_experiment FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    CONSTRAINT fk_experiment_results_variant FOREIGN KEY (variant_id) REFERENCES experiment_variants(id) ON DELETE CASCADE,
    CONSTRAINT fk_experiment_results_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS statistical_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL,
    variant_a_id UUID NOT NULL,
    variant_b_id UUID NOT NULL,
    metric TEXT NOT NULL,
    variant_a_mean DOUBLE PRECISION NOT NULL,
    variant_b_mean DOUBLE PRECISION NOT NULL,
    variant_a_std DOUBLE PRECISION NOT NULL,
    variant_b_std DOUBLE PRECISION NOT NULL,
    variant_a_count INTEGER NOT NULL,
    variant_b_count INTEGER NOT NULL,
    n_a INTEGER NOT NULL,
    n_b INTEGER NOT NULL,
    p_value DOUBLE PRECISION NOT NULL,
    confidence_level DOUBLE PRECISION NOT NULL,
    confidence_interval JSONB NOT NULL,
    is_significant BOOLEAN NOT NULL,
    effect_size DOUBLE PRECISION NOT NULL,
    winner TEXT,
    recommended_action TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_statistical_analyses_experiment FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    CONSTRAINT fk_statistical_analyses_variant_a FOREIGN KEY (variant_a_id) REFERENCES experiment_variants(id) ON DELETE CASCADE,
    CONSTRAINT fk_statistical_analyses_variant_b FOREIGN KEY (variant_b_id) REFERENCES experiment_variants(id) ON DELETE CASCADE
);

-- User Behavior Analysis Tables
CREATE TABLE IF NOT EXISTS behavior_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_name TEXT NOT NULL,
    page_url TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,
    properties JSONB,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_behavior_events_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_behavior_events_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS behavior_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    behavior_type TEXT NOT NULL,
    behavior_pattern TEXT NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    characteristics JSONB,
    metrics JSONB,
    session_count INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_behavior_profiles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_behavior_profiles_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE(user_id, tenant_id)
);

CREATE TABLE IF NOT EXISTS behavior_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    analysis_type TEXT NOT NULL,
    period_days INTEGER NOT NULL,
    total_users INTEGER NOT NULL,
    behavior_patterns JSONB NOT NULL,
    behavior_metrics JSONB NOT NULL,
    insights JSONB,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_behavior_analyses_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- UX Metrics Tables
CREATE TABLE IF NOT EXISTS ux_metric_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    metric_type TEXT NOT NULL,
    metric_category TEXT NOT NULL,
    unit TEXT NOT NULL,
    calculation_method TEXT NOT NULL,
    thresholds JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_ux_metric_definitions_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE(tenant_id, name)
);

CREATE TABLE IF NOT EXISTS ux_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    session_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    metric_category TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    context JSONB,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_ux_metrics_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_ux_metrics_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ux_metric_aggregations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    metric_type TEXT NOT NULL,
    metric_category TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    aggregation_type TEXT NOT NULL,
    period_hours INTEGER NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    sample_size INTEGER NOT NULL,
    threshold_compliance JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_ux_metric_aggregations_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    UNIQUE(tenant_id, metric_name, period_hours, aggregation_type)
);

CREATE TABLE IF NOT EXISTS ux_metric_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    metric_name TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message TEXT NOT NULL,
    current_value DOUBLE PRECISION NOT NULL,
    threshold_value DOUBLE PRECISION,
    trend_data JSONB,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_ux_metric_alerts_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Create Indexes for Performance

-- UI Analytics Indexes
CREATE INDEX IF NOT EXISTS idx_page_views_tenant_timestamp ON page_views(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_page_views_user_timestamp ON page_views(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_page_views_session ON page_views(session_id);
CREATE INDEX IF NOT EXISTS idx_page_views_page_url ON page_views(page_url);

CREATE INDEX IF NOT EXISTS idx_user_actions_tenant_timestamp ON user_actions(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_timestamp ON user_actions(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_actions_session ON user_actions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_type_name ON user_actions(action_type, action_name);

CREATE INDEX IF NOT EXISTS idx_conversion_events_tenant_timestamp ON conversion_events(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversion_events_user_timestamp ON conversion_events(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversion_events_funnel ON conversion_events(funnel_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_funnel_analyses_tenant_name ON funnel_analyses(tenant_id, funnel_name);

-- Feedback System Indexes
CREATE INDEX IF NOT EXISTS idx_feedback_responses_tenant_timestamp ON feedback_responses(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_responses_user_timestamp ON feedback_responses(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_responses_category ON feedback_responses(tenant_id, category);
CREATE INDEX IF NOT EXISTS idx_feedback_responses_status ON feedback_responses(tenant_id, status);

CREATE INDEX IF NOT EXISTS idx_feedback_categories_tenant_active ON feedback_categories(tenant_id, is_active);

CREATE INDEX IF NOT EXISTS idx_nps_responses_tenant_timestamp ON nps_responses(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nps_responses_user_timestamp ON nps_responses(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_feedback_analyses_tenant_type ON feedback_analyses(tenant_id, analysis_type);

-- A/B Testing Indexes
CREATE INDEX IF NOT EXISTS idx_experiments_tenant_status ON experiments(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_experiments_tenant_updated ON experiments(tenant_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_variants_experiment ON experiment_variants(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_variants_active ON experiment_variants(experiment_id, is_active);

CREATE INDEX IF NOT EXISTS idx_user_assignments_tenant_user ON user_assignments(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_user_assignments_experiment ON user_assignments(experiment_id);
CREATE INDEX IF NOT EXISTS idx_user_assignments_variant ON user_assignments(variant_id);

CREATE INDEX IF NOT EXISTS idx_experiment_results_experiment ON experiment_results(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_results_variant ON experiment_results(variant_id);
CREATE INDEX IF NOT EXISTS idx_experiment_results_user ON experiment_results(user_id);

CREATE INDEX IF NOT EXISTS idx_statistical_analyses_experiment ON statistical_analyses(experiment_id);

-- User Behavior Analysis Indexes
CREATE INDEX IF NOT EXISTS idx_behavior_events_tenant_timestamp ON behavior_events(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_behavior_events_user_timestamp ON behavior_events(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_behavior_events_session ON behavior_events(session_id);
CREATE INDEX IF NOT EXISTS idx_behavior_events_type_name ON behavior_events(event_type, event_name);

CREATE INDEX IF NOT EXISTS idx_behavior_profiles_tenant_pattern ON behavior_profiles(tenant_id, behavior_pattern);
CREATE INDEX IF NOT EXISTS idx_behavior_profiles_user_tenant ON behavior_profiles(user_id, tenant_id);

CREATE INDEX IF NOT EXISTS idx_behavior_analyses_tenant_type ON behavior_analyses(tenant_id, analysis_type);

-- UX Metrics Indexes
CREATE INDEX IF NOT EXISTS idx_ux_metrics_tenant_timestamp ON ux_metrics(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ux_metrics_user_timestamp ON ux_metrics(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ux_metrics_name_timestamp ON ux_metrics(tenant_id, metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ux_metrics_type_category ON ux_metrics(tenant_id, metric_type, metric_category);

CREATE INDEX IF NOT EXISTS idx_ux_metric_definitions_tenant_active ON ux_metric_definitions(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_ux_metric_definitions_name ON ux_metric_definitions(tenant_id, name);

CREATE INDEX IF NOT EXISTS idx_ux_metric_aggregations_tenant_period ON ux_metric_aggregations(tenant_id, period_hours);
CREATE INDEX IF NOT EXISTS idx_ux_metric_aggregations_name_period ON ux_metric_aggregations(tenant_id, metric_name, period_hours);

CREATE INDEX IF NOT EXISTS idx_ux_metric_alerts_tenant_resolved ON ux_metric_alerts(tenant_id, is_resolved);
CREATE INDEX IF NOT EXISTS idx_ux_metric_alerts_metric_severity ON ux_metric_alerts(metric_name, severity);

-- Row Level Security (RLS) Policies

-- UI Analytics RLS
ALTER TABLE page_views ENABLE ROW LEVEL SECURITY;
CREATE POLICY page_views_tenant_policy ON page_views FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE user_actions ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_actions_tenant_policy ON user_actions FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE conversion_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY conversion_events_tenant_policy ON conversion_events FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE funnel_analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY funnel_analyses_tenant_policy ON funnel_analyses FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Feedback System RLS
ALTER TABLE feedback_responses ENABLE ROW LEVEL SECURITY;
CREATE POLICY feedback_responses_tenant_policy ON feedback_responses FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE feedback_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY feedback_categories_tenant_policy ON feedback_categories FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE nps_responses ENABLE ROW LEVEL SECURITY;
CREATE POLICY nps_responses_tenant_policy ON nps_responses FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE feedback_analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY feedback_analyses_tenant_policy ON feedback_analyses FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- A/B Testing RLS
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
CREATE POLICY experiments_tenant_policy ON experiments FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE experiment_variants ENABLE ROW LEVEL SECURITY;
CREATE POLICY experiment_variants_tenant_policy ON experiment_variants FOR ALL TO authenticated_users 
    USING (experiment_id IN (
        SELECT id FROM experiments WHERE tenant_id = current_setting('app.current_tenant_id')::UUID
    ));

ALTER TABLE user_assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_assignments_tenant_policy ON user_assignments FOR ALL TO authenticated_users 
    USING (experiment_id IN (
        SELECT id FROM experiments WHERE tenant_id = current_setting('app.current_tenant_id')::UUID
    ));

ALTER TABLE experiment_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY experiment_results_tenant_policy ON experiment_results FOR ALL TO authenticated_users 
    USING (experiment_id IN (
        SELECT id FROM experiments WHERE tenant_id = current_setting('app.current_tenant_id')::UUID
    ));

ALTER TABLE statistical_analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY statistical_analyses_tenant_policy ON statistical_analyses FOR ALL TO authenticated_users 
    USING (experiment_id IN (
        SELECT id FROM experiments WHERE tenant_id = current_setting('app.current_tenant_id')::UUID
    ));

-- User Behavior Analysis RLS
ALTER TABLE behavior_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY behavior_events_tenant_policy ON behavior_events FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE behavior_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY behavior_profiles_tenant_policy ON behavior_profiles FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE behavior_analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY behavior_analyses_tenant_policy ON behavior_analyses FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- UX Metrics RLS
ALTER TABLE ux_metric_definitions ENABLE ROW LEVEL SECURITY;
CREATE POLICY ux_metric_definitions_tenant_policy ON ux_metric_definitions FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE ux_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY ux_metrics_tenant_policy ON ux_metrics FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE ux_metric_aggregations ENABLE ROW LEVEL SECURITY;
CREATE POLICY ux_metric_aggregations_tenant_policy ON ux_metric_aggregations FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

ALTER TABLE ux_metric_alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY ux_metric_alerts_tenant_policy ON ux_metric_alerts FOR ALL TO authenticated_users 
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Triggers for Updated At Timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_page_views_updated_at BEFORE UPDATE ON page_views 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_responses_updated_at BEFORE UPDATE ON feedback_responses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_categories_updated_at BEFORE UPDATE ON feedback_categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiments_updated_at BEFORE UPDATE ON experiments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiment_variants_updated_at BEFORE UPDATE ON experiment_variants 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_behavior_profiles_updated_at BEFORE UPDATE ON behavior_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ux_metric_definitions_updated_at BEFORE UPDATE ON ux_metric_definitions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert Default Feedback Categories
INSERT INTO feedback_categories (tenant_id, name, description, is_active) VALUES
    (gen_random_uuid(), 'General', 'General feedback about the platform', true),
    (gen_random_uuid(), 'UI/UX', 'User interface and user experience feedback', true),
    (gen_random_uuid(), 'Features', 'Feature requests and feedback', true),
    (gen_random_uuid(), 'Bugs', 'Bug reports and issues', true),
    (gen_random_uuid(), 'Performance', 'Performance-related feedback', true),
    (gen_random_uuid(), 'Support', 'Customer support feedback', true)
ON CONFLICT DO NOTHING;

-- Insert Default UX Metric Definitions
INSERT INTO ux_metric_definitions (tenant_id, name, description, metric_type, metric_category, unit, calculation_method, thresholds, is_active) VALUES
    (gen_random_uuid(), 'page_load_time', 'Time taken to load a page completely', 'performance', 'page_performance', 'seconds', 'navigation_timing', '{"excellent": 1.0, "good": 2.0, "acceptable": 3.0, "poor": 5.0}', true),
    (gen_random_uuid(), 'time_to_interactive', 'Time until page becomes interactive', 'performance', 'page_performance', 'seconds', 'performance_timing', '{"excellent": 2.0, "good": 3.0, "acceptable": 5.0, "poor": 8.0}', true),
    (gen_random_uuid(), 'click_through_rate', 'Percentage of users who click on elements', 'engagement', 'user_interaction', 'percentage', 'event_tracking', '{"excellent": 0.1, "good": 0.05, "acceptable": 0.02, "poor": 0.01}', true),
    (gen_random_uuid(), 'form_completion_rate', 'Percentage of forms successfully completed', 'conversion', 'form_completion', 'percentage', 'form_tracking', '{"excellent": 0.9, "good": 0.8, "acceptable": 0.6, "poor": 0.4}', true),
    (gen_random_uuid(), 'search_success_rate', 'Percentage of successful search queries', 'usability', 'search_efficiency', 'percentage', 'search_tracking', '{"excellent": 0.9, "good": 0.8, "acceptable": 0.6, "poor": 0.4}', true),
    (gen_random_uuid(), 'error_rate', 'Percentage of user actions resulting in errors', 'error_rate', 'error_handling', 'percentage', 'error_tracking', '{"excellent": 0.01, "good": 0.02, "acceptable": 0.05, "poor": 0.1}', true),
    (gen_random_uuid(), 'user_satisfaction', 'User satisfaction score', 'satisfaction', 'task_completion', 'score', 'survey_tracking', '{"excellent": 4.5, "good": 4.0, "acceptable": 3.5, "poor": 3.0}', true),
    (gen_random_uuid(), 'task_completion_time', 'Time taken to complete primary tasks', 'usability', 'task_completion', 'seconds', 'task_tracking', '{"excellent": 30.0, "good": 60.0, "acceptable": 120.0, "poor": 300.0}', true)
ON CONFLICT DO NOTHING;

COMMIT;
