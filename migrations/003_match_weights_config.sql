-- Match Weights Configuration Migration
-- Creates tables for storing per-tenant match weights and scoring configurations

-- Create tenant match configurations table
CREATE TABLE IF NOT EXISTS tenant_match_configs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    config_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    
    -- Constraints
    CONSTRAINT tenant_match_configs_unique UNIQUE (tenant_id, version)
);

-- Create index for efficient tenant lookups
CREATE INDEX IF NOT EXISTS idx_tenant_match_configs_tenant_id 
    ON tenant_match_configs(tenant_id);

-- Create index for version lookups
CREATE INDEX IF NOT EXISTS idx_tenant_match_configs_version 
    ON tenant_match_configs(tenant_id, version DESC);

-- Create match score history table for analytics and calibration
CREATE TABLE IF NOT EXISTS match_score_history (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    match_score DECIMAL(5,4) NOT NULL,
    category_scores JSONB,
    config_version INTEGER,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_action VARCHAR(50), -- 'viewed', 'applied', 'skipped', 'rejected'
    outcome VARCHAR(50), -- 'success', 'pending', 'failed', 'withdrawn'
    
    -- Constraints
    CONSTRAINT match_score_history_unique UNIQUE (tenant_id, user_id, job_id, applied_at)
);

-- Create indexes for match score history
CREATE INDEX IF NOT EXISTS idx_match_score_history_tenant_user 
    ON match_score_history(tenant_id, user_id);

CREATE INDEX IF NOT EXISTS idx_match_score_history_job 
    ON match_score_history(job_id);

CREATE INDEX IF NOT EXISTS idx_match_score_history_applied_at 
    ON match_score_history(applied_at);

CREATE INDEX IF NOT EXISTS idx_match_score_history_outcome 
    ON match_score_history(outcome);

-- Create match weight analytics table for tracking performance
CREATE TABLE IF NOT EXISTS match_weight_analytics (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    weight_value DECIMAL(4,2) NOT NULL,
    performance_score DECIMAL(5,4), -- How well this weight performed
    sample_size INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT match_weight_analytics_unique UNIQUE (tenant_id, category, period_start)
);

-- Create indexes for analytics
CREATE INDEX IF NOT EXISTS idx_match_weight_analytics_tenant_category 
    ON match_weight_analytics(tenant_id, category);

CREATE INDEX IF NOT EXISTS idx_match_weight_analytics_period 
    ON match_weight_analytics(period_start, period_end);

-- Create default match configurations for new tenants
INSERT INTO tenant_match_configs (tenant_id, config_data, version, created_by)
SELECT 
    'default',
    jsonb_build_object(
        'weights', jsonb_build_object(
            'skills_match', jsonb_build_object(
                'weight', 1.5,
                'enabled', true,
                'priority', 1,
                'custom_rules', jsonb_build_object(
                    'exact_match_bonus', 0.5,
                    'partial_match_penalty', 0.2,
                    'demand_score_weight', 0.3
                ),
                'description', 'Weight for skills matching between user profile and job requirements'
            ),
            'experience_match', jsonb_build_object(
                'weight', 1.2,
                'enabled', true,
                'priority', 2,
                'custom_rules', jsonb_build_object(
                    'exact_years_bonus', 0.3,
                    'under_experience_penalty', 0.4,
                    'over_experience_penalty', 0.1
                ),
                'description', 'Weight for experience level matching'
            ),
            'location_match', jsonb_build_object(
                'weight', 1.0,
                'enabled', true,
                'priority', 3,
                'custom_rules', jsonb_build_object(
                    'exact_location_bonus', 0.4,
                    'same_region_bonus', 0.2,
                    'remote_work_bonus', 0.3
                ),
                'description', 'Weight for location and remote work preferences'
            ),
            'salary_match', jsonb_build_object(
                'weight', 0.8,
                'enabled', true,
                'priority', 4,
                'custom_rules', jsonb_build_object(
                    'exact_match_bonus', 0.3,
                    'within_range_bonus', 0.2,
                    'below_expected_penalty', 0.3
                ),
                'description', 'Weight for salary range matching'
            ),
            'education_match', jsonb_build_object(
                'weight', 0.6,
                'enabled', true,
                'priority', 5,
                'custom_rules', jsonb_build_object(
                    'degree_level_bonus', jsonb_build_object(
                        'high_school', 0.1,
                        'bachelor', 0.3,
                        'master', 0.4,
                        'phd', 0.5
                    )
                ),
                'description', 'Weight for education level matching'
            ),
            'company_size_match', jsonb_build_object(
                'weight', 0.4,
                'enabled', true,
                'priority', 6,
                'custom_rules', jsonb_build_object(
                    'size_preference_bonus', jsonb_build_object(
                        'startup', 0.2,
                        'small', 0.1,
                        'medium', 0.3,
                        'large', 0.2,
                        'enterprise', 0.1
                    )
                ),
                'description', 'Weight for company size preferences'
            ),
            'remote_work_match', jsonb_build_object(
                'weight', 0.7,
                'enabled', true,
                'priority', 3,
                'custom_rules', jsonb_build_object(
                    'fully_remote_bonus', 0.4,
                    'hybrid_bonus', 0.2,
                    'onsite_penalty', 0.3
                ),
                'description', 'Weight for remote work compatibility'
            ),
            'industry_match', jsonb_build_object(
                'weight', 0.5,
                'enabled', true,
                'priority', 7,
                'custom_rules', jsonb_build_object(
                    'exact_industry_bonus', 0.3,
                    'related_industry_bonus', 0.15
                ),
                'description', 'Weight for industry experience matching'
            ),
            'job_type_match', jsonb_build_object(
                'weight', 0.6,
                'enabled', true,
                'priority', 8,
                'custom_rules', jsonb_build_object(
                    'preferred_type_bonus', 0.3,
                    'acceptable_type_bonus', 0.15
                ),
                'description', 'Weight for job type matching'
            ),
            'seniority_match', jsonb_build_object(
                'weight', 0.9,
                'enabled', true,
                'priority', 2,
                'custom_rules', jsonb_build_object(
                    'exact_level_bonus', 0.4,
                    'one_level_difference_penalty', 0.2,
                    'two_level_difference_penalty', 0.4
                ),
                'description', 'Weight for seniority level matching'
            )
        ),
        'global_multiplier', 1.0,
        'min_match_score', 0.3,
        'max_results', 100,
        'enable_ml_scoring', true,
        'custom_scoring_rules', jsonb_build_object()
    ),
    1,
    'system'
ON CONFLICT (tenant_id, version) DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE tenant_match_configs IS 'Stores per-tenant match weight configurations and scoring rules';
COMMENT ON TABLE match_score_history IS 'Tracks match scores and outcomes for analytics and calibration';
COMMENT ON TABLE match_weight_analytics IS 'Stores performance analytics for match weight tuning';

COMMENT ON COLUMN tenant_match_configs.config_data IS 'JSON configuration containing weights, rules, and scoring parameters';
COMMENT ON COLUMN match_score_history.category_scores IS 'JSON object containing individual category scores used in calculation';
COMMENT ON COLUMN match_weight_analytics.performance_score IS 'Performance metric indicating how well the weight performed (0-1 scale)';

-- Create function to get current tenant config
CREATE OR REPLACE FUNCTION get_current_match_config(p_tenant_id TEXT)
RETURNS JSONB AS $$
DECLARE
    config_record RECORD;
BEGIN
    SELECT config_data INTO config_record
    FROM tenant_match_configs 
    WHERE tenant_id = p_tenant_id 
    ORDER BY version DESC 
    LIMIT 1;
    
    IF NOT FOUND THEN
        -- Return default configuration
        SELECT config_data INTO config_record
        FROM tenant_match_configs 
        WHERE tenant_id = 'default' 
        LIMIT 1;
    END IF;
    
    RETURN COALESCE(config_record.config_data, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Create function to record match score
CREATE OR REPLACE FUNCTION record_match_score(
    p_tenant_id TEXT,
    p_user_id TEXT,
    p_job_id TEXT,
    p_match_score DECIMAL,
    p_category_scores JSONB,
    p_config_version INTEGER DEFAULT NULL,
    p_user_action TEXT DEFAULT NULL,
    p_outcome TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO match_score_history (
        tenant_id, user_id, job_id, match_score, category_scores, 
        config_version, user_action, outcome
    ) VALUES (
        p_tenant_id, p_user_id, p_job_id, p_match_score, p_category_scores,
        p_config_version, p_user_action, p_outcome
    )
    ON CONFLICT (tenant_id, user_id, job_id, applied_at) 
    DO UPDATE SET
        match_score = EXCLUDED.match_score,
        category_scores = EXCLUDED.category_scores,
        config_version = EXCLUDED.config_version,
        user_action = EXCLUDED.user_action,
        outcome = EXCLUDED.outcome;
END;
$$ LANGUAGE plpgsql;

-- Create view for tenant match analytics
CREATE OR REPLACE VIEW tenant_match_analytics AS
SELECT 
    tmc.tenant_id,
    tmc.version,
    tmc.updated_at,
    tmc.updated_by,
    (tmc.config_data->>'global_multiplier')::DECIMAL as global_multiplier,
    (tmc.config_data->>'min_match_score')::DECIMAL as min_match_score,
    (tmc.config_data->>'max_results')::INTEGER as max_results,
    (tmc.config_data->>'enable_ml_scoring')::BOOLEAN as enable_ml_scoring,
    COUNT(msh.id) as total_matches,
    AVG(msh.match_score) as avg_match_score,
    COUNT(CASE WHEN msh.outcome = 'success' THEN 1 END) as successful_matches,
    COUNT(CASE WHEN msh.outcome = 'applied' THEN 1 END) as total_applications,
    (COUNT(CASE WHEN msh.outcome = 'success' THEN 1 END)::DECIMAL / NULLIF(COUNT(CASE WHEN msh.outcome = 'applied' THEN 1 END), 0))::DECIMAL as success_rate
FROM tenant_match_configs tmc
LEFT JOIN match_score_history msh ON tmc.tenant_id = msh.tenant_id 
    AND msh.applied_at >= tmc.created_at
GROUP BY tmc.tenant_id, tmc.version, tmc.updated_at, tmc.updated_by, 
    tmc.config_data->>'global_multiplier', 
    tmc.config_data->>'min_match_score', 
    tmc.config_data->>'max_results', 
    tmc.config_data->>'enable_ml_scoring'
ORDER BY tmc.tenant_id, tmc.version DESC;

COMMENT ON VIEW tenant_match_analytics IS 'Analytics view showing match performance per tenant and configuration version';
