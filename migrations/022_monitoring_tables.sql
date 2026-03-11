-- Migration 011: Monitoring Tables for Phase 15.1 Database & Performance
-- Tables for advanced monitoring and alerting system

-- Extended monitoring metrics table
CREATE TABLE IF NOT EXISTS extended_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    labels JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT ARRAY,
    aggregation JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced alert system tables
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    rule_name VARCHAR(100) NOT NULL,
    rule_expression TEXT NOT NULL,
    condition_expression TEXT,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    comparison_operator VARCHAR(10) NOT NULL DEFAULT 'gt',
    cooldown_period_minutes INTEGER DEFAULT 5,
    notification_channels JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Alert notifications table
CREATE TABLE IF NOT EXISTS alert_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    alert_id UUID NOT NULL REFERENCES performance_alerts(id),
    notification_type VARCHAR(50) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alert escalation rules table
CREATE TABLE IF NOT EXISTS alert_escalation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    rule_name VARCHAR(100) NOT NULL,
    trigger_alert_type VARCHAR(50) NOT NULL,
    escalation_conditions JSONB DEFAULT '{}',
    escalation_interval_minutes INTEGER DEFAULT 10,
    max_escalations INTEGER DEFAULT 3,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Performance dashboards table
CREATE TABLE IF NOT EXISTS performance_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    dashboard_name VARCHAR(100) NOT NULL,
    dashboard_config JSONB DEFAULT '{}',
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    refresh_interval_seconds INTEGER DEFAULT 60,
    widgets JSONB DEFAULT '[]',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Performance alerts configuration table
CREATE TABLE IF NOT EXISTS performance_alerts_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    alert_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    comparison_operator VARCHAR(10) NOT NULL DEFAULT 'gt',
    cooldown_period_minutes INTEGER DEFAULT 5,
    notification_channels JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT TRUE,
    auto_resolve BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Performance trends table
CREATE TABLE IF NOT EXISTS performance_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100) NOT NULL,
    time_period_hours INTEGER NOT NULL,
    trend_direction VARCHAR(20) NOT NULL,
    current_value DOUBLE PRECISION NOT NULL,
    baseline_value DOUBLE PRECISION NOT NULL,
    trend_percentage DOUBLE PRECISION DEFAULT 0.0,
    confidence_score DOUBLE PRECISION DEFAULT 0.0,
    data_points INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_extended_metrics_tenant_timestamp ON extended_metrics(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_extended_metrics_name_timestamp ON extended_metrics(metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_extended_metrics_category_timestamp ON extended_metrics(metric_category, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_alert_rules_tenant_enabled ON alert_rules(tenant_id, enabled);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_tenant_status ON alert_notifications(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_alert_escalation_rules_tenant_enabled ON alert_escalation_rules(tenant_id, enabled);

CREATE INDEX IF NOT EXISTS idx_performance_dashboards_tenant_active ON performance_dashboards(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_config_tenant_enabled ON performance_alerts_config(tenant_id, enabled);
CREATE INDEX IF NOT EXISTS idx_performance_trends_tenant_metric ON performance_trends(tenant_id, metric_name);

-- Create views for performance analysis
CREATE OR REPLACE VIEW performance_alerts_summary AS
SELECT 
    severity,
    COUNT(*) as alert_count,
    COUNT(*) FILTER (resolved = FALSE) as active_count,
    COUNT(*) FILTER (resolved = TRUE) as resolved_count,
    MAX(timestamp) as last_alert_timestamp
FROM performance_alerts
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY severity
ORDER BY alert_count DESC;

CREATE OR REPLACE VIEW performance_metrics_summary AS
SELECT 
    metric_category,
    COUNT(*) as metric_count,
    AVG(value) as avg_value,
    MAX(value) as max_value,
    MIN(value) as min_value,
    MAX(timestamp) as last_timestamp
FROM extended_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY metric_category
ORDER BY metric_count DESC;

-- Create functions for performance analysis
CREATE OR REPLACE FUNCTION get_alert_statistics(
    tenant_id UUID,
    time_period_hours INTEGER DEFAULT 24
) RETURNS TABLE(
    severity TEXT,
    alert_count BIGINT,
    active_count BIGINT,
    resolved_count BIGINT,
    last_alert_timestamp TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        severity,
        COUNT(*) as alert_count,
        COUNT(*) FILTER (resolved = FALSE) as active_count,
        COUNT(*) FILTER (resolved = TRUE) as resolved_count,
        MAX(timestamp) as last_alert_timestamp
    FROM performance_alerts
    WHERE tenant_id = tenant_id
        AND timestamp >= NOW() - INTERVAL f'{time_period_hours} hours'
        GROUP BY severity
        ORDER BY alert_count DESC;
END;
$$;

CREATE OR REPLACE FUNCTION get_slow_queries(
    limit INTEGER DEFAULT 10,
    min_execution_time_ms REAL DEFAULT 1000.0
) RETURNS TABLE(
    query_hash TEXT,
    avg_execution_time_ms REAL,
    total_executions BIGINT,
    query TEXT,
    last_execution_time TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        query_hash,
        avg_execution_time_ms,
        total_executions,
        query,
        MAX(timestamp) as last_execution_time
    FROM query_performance_analysis
    WHERE avg_execution_time_ms > min_execution_time_ms
    ORDER BY avg_execution_time_ms DESC
    LIMIT limit;
END;
$$;

-- Create function for automatic cleanup
CREATE OR REPLACE FUNCTION cleanup_old_performance_data(
    days_old INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old performance data (older than specified days)
    DELETE FROM extended_metrics WHERE timestamp < NOW() - INTERVAL f'{days_old} days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM alert_notifications WHERE sent_at < NOW() - INTERVAL f'{days_old} days';
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    RETURN deleted_count;
END;
$$;

-- Create function for automatic statistics update
CREATE OR REPLACE FUNCTION update_performance_stats() RETURNS VOID AS $$
BEGIN
    -- Update performance statistics
    -- This would update aggregated statistics tables
    NULL;
END;
$$;

-- Add comments
COMMENT ON TABLE extended_metrics IS 'Stores extended performance metrics with labels and metadata';
COMMENT ON TABLE alert_rules IS 'Stores alert rules and conditions for monitoring';
COMMENT ON TABLE alert_notifications IS 'Stores alert notification history and status';
COMMENT ON TABLE alert_escalation_rules IS 'Stores alert escalation rules and conditions';
COMMENT ON TABLE performance_dashboards IS 'Stores performance dashboard configurations';
COMMENT ON TABLE performance_alerts_config IS 'Stores performance alert configurations';
COMMENT ON TABLE performance_trends IS 'Stores performance trend analysis data';

-- Grant permissions
GRANT SELECT ON extended_metrics TO postgres;
GRANT SELECT ON alert_rules TO postgres;
GRANT SELECT ON alert_notifications TO postgres;
GRANT SELECT ON alert_escalation_rules TO postgres;
GRANT SELECT ON performance_dashboards TO postgres;
GRANT SELECT ON performance_alerts_config TO postgres;
GRANT SELECT ON performance_trends TO postgres;
GRANT SELECT ON performance_alerts_summary TO postgres;
GRANT SELECT ON performance_metrics_summary TO postgres;
