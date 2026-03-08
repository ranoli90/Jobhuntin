-- Migration 008: Enhanced Performance Features for Phase 15.1
-- Additional tables for advanced performance monitoring, caching, and connection pooling

-- Cache performance metrics table
CREATE TABLE IF NOT EXISTS cache_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    cache_type VARCHAR(50) NOT NULL,
    cache_level VARCHAR(50) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    key_name VARCHAR(255),
    hit BOOLEAN DEFAULT FALSE,
    response_time_ms DOUBLE PRECISION,
    size_bytes INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Connection pool metrics table
CREATE TABLE IF NOT EXISTS connection_pool_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    pool_name VARCHAR(100) NOT NULL,
    total_connections INTEGER NOT NULL,
    active_connections INTEGER NOT NULL,
    idle_connections INTEGER NOT NULL,
    queued_requests INTEGER DEFAULT 0,
    avg_connection_time_ms DOUBLE PRECISION DEFAULT 0.0,
    avg_query_time_ms DOUBLE PRECISION DEFAULT 0.0,
    connection_errors INTEGER DEFAULT 0,
    query_errors INTEGER DEFAULT 0,
    health_check_failures INTEGER DEFAULT 0,
    last_health_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'healthy',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance trends table
CREATE TABLE IF NOT EXISTS performance_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    trend_direction VARCHAR(20) NOT NULL CHECK (trend_direction IN ('increasing', 'decreasing', 'stable')),
    current_value DOUBLE PRECISION NOT NULL,
    average_value DOUBLE PRECISION NOT NULL,
    trend_percentage DOUBLE PRECISION DEFAULT 0.0,
    data_points INTEGER NOT NULL,
    period_hours INTEGER NOT NULL,
    confidence_score DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance recommendations table
CREATE TABLE IF NOT EXISTS performance_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    recommendation_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    impact_score DOUBLE PRECISION DEFAULT 0.0,
    implementation_cost VARCHAR(20) NOT NULL CHECK (implementation_cost IN ('low', 'medium', 'high')),
    estimated_benefit TEXT,
    risks TEXT[] DEFAULT '{}',
    sql_statement TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    implemented_at TIMESTAMP WITH TIME ZONE,
    implementation_result JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance dashboards table
CREATE TABLE IF NOT EXISTS performance_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    dashboard_name VARCHAR(100) NOT NULL,
    dashboard_config JSONB NOT NULL DEFAULT '{}',
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance alerts subscriptions table
CREATE TABLE IF NOT EXISTS performance_alert_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    enabled BOOLEAN DEFAULT TRUE,
    webhook_url TEXT,
    email_recipients TEXT[] DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance baselines table
CREATE TABLE IF NOT EXISTS performance_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    baseline_value DOUBLE PRECISION NOT NULL,
    baseline_period_hours INTEGER NOT NULL,
    confidence_interval_lower DOUBLE PRECISION,
    confidence_interval_upper DOUBLE PRECISION,
    sample_size INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, metric_name, metric_type)
);

-- Performance anomalies table
CREATE TABLE IF NOT EXISTS performance_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    anomaly_value DOUBLE PRECISION NOT NULL,
    expected_value DOUBLE PRECISION NOT NULL,
    anomaly_score DOUBLE PRECISION NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cache_performance_metrics_tenant_timestamp ON cache_performance_metrics(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cache_performance_metrics_type_level ON cache_performance_metrics(cache_type, cache_level);
CREATE INDEX IF NOT EXISTS idx_cache_performance_metrics_operation_hit ON cache_performance_metrics(operation_type, hit);

CREATE INDEX IF NOT EXISTS idx_connection_pool_metrics_tenant_timestamp ON connection_pool_metrics(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_connection_pool_metrics_pool_name ON connection_pool_metrics(pool_name);
CREATE INDEX IF NOT EXISTS idx_connection_pool_metrics_status ON connection_pool_metrics(status);

CREATE INDEX IF NOT EXISTS idx_performance_trends_tenant_metric ON performance_trends(tenant_id, metric_name, metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_trends_direction ON performance_trends(trend_direction);
CREATE INDEX IF NOT EXISTS idx_performance_trends_updated ON performance_trends(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_performance_recommendations_tenant_timestamp ON performance_recommendations(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_recommendations_type_priority ON performance_recommendations(recommendation_type, priority);
CREATE INDEX IF NOT EXISTS idx_performance_recommendations_status ON performance_recommendations(status);

CREATE INDEX IF NOT EXISTS idx_performance_dashboards_tenant_active ON performance_dashboards(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_performance_dashboards_default ON performance_dashboards(is_default);

CREATE INDEX IF NOT EXISTS idx_performance_alert_subscriptions_tenant_type ON performance_alert_subscriptions(tenant_id, alert_type);
CREATE INDEX IF NOT EXISTS idx_performance_alert_subscriptions_enabled ON performance_alert_subscriptions(enabled);

CREATE INDEX IF NOT EXISTS idx_performance_baselines_tenant_metric ON performance_baselines(tenant_id, metric_name, metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_baselines_updated ON performance_baselines(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_performance_anomalies_tenant_timestamp ON performance_anomalies(tenant_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_performance_anomalies_severity ON performance_anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_performance_anomalies_resolved ON performance_anomalies(resolved_at);

-- Create views for performance analytics
CREATE OR REPLACE VIEW cache_performance_summary AS
SELECT 
    tenant_id,
    cache_type,
    cache_level,
    operation_type,
    COUNT(*) as total_operations,
    COUNT(*) FILTER (WHERE hit = TRUE) as hits,
    COUNT(*) FILTER (WHERE hit = FALSE) as misses,
    CASE 
        WHEN COUNT(*) > 0 THEN (COUNT(*) FILTER (WHERE hit = TRUE) * 100.0 / COUNT(*))
        ELSE 0
    END as hit_rate_percent,
    AVG(response_time_ms) as avg_response_time_ms,
    AVG(size_bytes) as avg_size_bytes,
    MAX(timestamp) as last_operation_timestamp
FROM cache_performance_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY tenant_id, cache_type, cache_level, operation_type;

CREATE OR REPLACE VIEW connection_pool_summary AS
SELECT 
    tenant_id,
    pool_name,
    AVG(total_connections) as avg_total_connections,
    AVG(active_connections) as avg_active_connections,
    AVG(idle_connections) as avg_idle_connections,
    AVG(queued_requests) as avg_queued_requests,
    AVG(avg_connection_time_ms) as avg_connection_time_ms,
    AVG(avg_query_time_ms) as avg_query_time_ms,
    SUM(connection_errors) as total_connection_errors,
    SUM(query_errors) as total_query_errors,
    COUNT(*) as sample_count,
    MAX(created_at) as last_sample_timestamp
FROM connection_pool_metrics
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY tenant_id, pool_name;

CREATE OR REPLACE VIEW performance_anomalies_summary AS
SELECT 
    tenant_id,
    metric_name,
    metric_type,
    severity,
    COUNT(*) as anomaly_count,
    COUNT(*) FILTER (WHERE resolved_at IS NULL) as unresolved_count,
    AVG(anomaly_score) as avg_anomaly_score,
    MAX(detected_at) as last_anomaly_timestamp
FROM performance_anomalies
WHERE detected_at >= NOW() - INTERVAL '24 hours'
GROUP BY tenant_id, metric_name, metric_type, severity;

-- Insert default performance dashboards
INSERT INTO performance_dashboards (id, tenant_id, dashboard_name, dashboard_config, is_default, is_active)
SELECT 
    gen_random_uuid(),
    t.id,
    'System Overview',
    jsonb_build_object(
        'widgets', jsonb_build_array(
            jsonb_build_object('type', 'metric_chart', 'metric', 'cpu_percent', 'title', 'CPU Usage'),
            jsonb_build_object('type', 'metric_chart', 'metric', 'memory_percent', 'title', 'Memory Usage'),
            jsonb_build_object('type', 'alert_list', 'severity', 'critical', 'title', 'Critical Alerts'),
            jsonb_build_object('type', 'trend_chart', 'metric', 'response_time', 'title', 'Response Time Trends')
        ),
        'refresh_interval', 300,
        'time_range', '24h'
    ),
    true,
    true
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM performance_dashboards pd 
    WHERE pd.tenant_id = t.id 
    AND pd.dashboard_name = 'System Overview'
)
ON CONFLICT DO NOTHING;

INSERT INTO performance_dashboards (id, tenant_id, dashboard_name, dashboard_config, is_default, is_active)
SELECT 
    gen_random_uuid(),
    t.id,
    'Database Performance',
    jsonb_build_object(
        'widgets', jsonb_build_array(
            jsonb_build_object('type', 'metric_chart', 'metric', 'connection_pool_utilization', 'title', 'Connection Pool'),
            jsonb_build_object('type', 'metric_chart', 'metric', 'query_response_time', 'title', 'Query Response Time'),
            jsonb_build_object('type', 'metric_chart', 'metric', 'index_hit_rate', 'title', 'Index Hit Rate'),
            jsonb_build_object('type', 'recommendation_list', 'category', 'database', 'title', 'Database Recommendations')
        ),
        'refresh_interval', 300,
        'time_range', '24h'
    ),
    false,
    true
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM performance_dashboards pd 
    WHERE pd.tenant_id = t.id 
    AND pd.dashboard_name = 'Database Performance'
)
ON CONFLICT DO NOTHING;

-- Insert default performance baselines
INSERT INTO performance_baselines (id, tenant_id, metric_name, metric_type, baseline_value, baseline_period_hours, confidence_interval_lower, confidence_interval_upper, sample_size)
SELECT 
    gen_random_uuid(),
    t.id,
    unnest(ARRAY['cpu_percent', 'memory_percent', 'disk_percent', 'connection_pool_utilization']),
    unnest(ARRAY['cpu', 'memory', 'disk', 'database']),
    unnest(ARRAY[50.0, 60.0, 60.0, 70.0]),
    24,
    unnest(ARRAY[45.0, 55.0, 55.0, 65.0]),
    unnest(ARRAY[55.0, 65.0, 65.0, 75.0]),
    100
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM performance_baselines pb 
    WHERE pb.tenant_id = t.id 
    AND pb.metric_name IN ('cpu_percent', 'memory_percent', 'disk_percent', 'connection_pool_utilization')
)
ON CONFLICT (tenant_id, metric_name, metric_type) DO NOTHING;

-- Comments
COMMENT ON TABLE cache_performance_metrics IS 'Stores cache performance metrics including hits, misses, and response times';
COMMENT ON TABLE connection_pool_metrics IS 'Stores database connection pool metrics and health status';
COMMENT ON TABLE performance_trends IS 'Stores calculated performance trends and direction analysis';
COMMENT ON TABLE performance_recommendations IS 'Stores performance optimization recommendations';
COMMENT ON TABLE performance_dashboards IS 'Stores custom dashboard configurations for performance monitoring';
COMMENT ON TABLE performance_alert_subscriptions IS 'Stores user alert subscription preferences';
COMMENT ON TABLE performance_baselines IS 'Stores baseline values for performance metrics';
COMMENT ON TABLE performance_anomalies IS 'Stores detected performance anomalies and their resolution status';
