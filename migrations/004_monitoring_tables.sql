-- Monitoring and Analytics Tables
-- Create tables for API monitoring, metrics, and analytics

-- API request logs for detailed request tracking
CREATE TABLE IF NOT EXISTS api_request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    url TEXT NOT NULL,
    path VARCHAR(500) NOT NULL,
    query_params JSONB,
    headers JSONB,
    user_agent TEXT,
    ip_address INET NOT NULL,
    user_id UUID REFERENCES users(id),
    tenant_id UUID,
    session_id VARCHAR(255),
    api_key VARCHAR(255),
    content_type VARCHAR(100),
    content_length BIGINT,
    status_code INTEGER,
    response_time_ms FLOAT NOT NULL,
    error_message TEXT,
    error_traceback TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance metrics for detailed analysis
CREATE TABLE IF NOT EXISTS api_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(255) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms FLOAT NOT NULL,
    db_query_time_ms FLOAT DEFAULT 0.0,
    cache_lookup_time_ms FLOAT DEFAULT 0.0,
    auth_time_ms FLOAT DEFAULT 0.0,
    validation_time_ms FLOAT DEFAULT 0.0,
    memory_usage_mb FLOAT DEFAULT 0.0,
    cpu_usage_percent FLOAT DEFAULT 0.0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Security events for security monitoring
CREATE TABLE IF NOT EXISTS api_security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) NOT NULL UNIQUE,
    request_id VARCHAR(255),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    ip_address INET NOT NULL,
    user_agent TEXT,
    user_id UUID REFERENCES users(id),
    details JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Endpoint statistics aggregation
CREATE TABLE IF NOT EXISTS api_endpoint_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    date_hour TIMESTAMP WITH TIME ZONE NOT NULL, -- Truncated to hour
    request_count INTEGER DEFAULT 0,
    total_response_time_ms FLOAT DEFAULT 0.0,
    avg_response_time_ms FLOAT DEFAULT 0.0,
    min_response_time_ms FLOAT DEFAULT 0.0,
    max_response_time_ms FLOAT DEFAULT 0.0,
    error_count INTEGER DEFAULT 0,
    status_code_distribution JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(endpoint, method, date_hour)
);

-- Daily metrics summary
CREATE TABLE IF NOT EXISTS api_daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT DEFAULT 0.0,
    min_response_time_ms FLOAT DEFAULT 0.0,
    max_response_time_ms FLOAT DEFAULT 0.0,
    unique_users INTEGER DEFAULT 0,
    unique_ips INTEGER DEFAULT 0,
    top_endpoints JSONB DEFAULT '{}'::jsonb,
    error_distribution JSONB DEFAULT '{}'::jsonb,
    security_events_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date)
);

-- User activity tracking
CREATE TABLE IF NOT EXISTS api_user_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    request_count INTEGER DEFAULT 0,
    unique_endpoints INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT DEFAULT 0.0,
    last_request_at TIMESTAMP WITH TIME ZONE,
    user_agent TEXT,
    ip_addresses JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- System health metrics
CREATE TABLE IF NOT EXISTS api_system_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cpu_usage_percent FLOAT,
    memory_usage_percent FLOAT,
    disk_usage_percent FLOAT,
    active_connections INTEGER,
    database_connections INTEGER,
    cache_hit_rate FLOAT,
    error_rate FLOAT DEFAULT 0.0,
    health_score INTEGER DEFAULT 100 CHECK (health_score >= 0 AND health_score <= 100),
    alerts JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API alerts and notifications
CREATE TABLE IF NOT EXISTS api_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    metric_name VARCHAR(100),
    threshold_value FLOAT,
    current_value FLOAT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'suppressed')),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_request_logs_timestamp ON api_request_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_request_id ON api_request_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_user_id ON api_request_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_ip_address ON api_request_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_status_code ON api_request_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_path ON api_request_logs(path);

CREATE INDEX IF NOT EXISTS idx_api_performance_metrics_timestamp ON api_performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_performance_metrics_endpoint ON api_performance_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_performance_metrics_response_time ON api_performance_metrics(response_time_ms);

CREATE INDEX IF NOT EXISTS idx_api_security_events_timestamp ON api_security_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_security_events_severity ON api_security_events(severity);
CREATE INDEX IF NOT EXISTS idx_api_security_events_event_type ON api_security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_api_security_events_ip_address ON api_security_events(ip_address);
CREATE INDEX IF NOT EXISTS idx_api_security_events_resolved ON api_security_events(resolved);

CREATE INDEX IF NOT EXISTS idx_api_endpoint_stats_date_hour ON api_endpoint_stats(date_hour);
CREATE INDEX IF NOT EXISTS idx_api_endpoint_stats_endpoint ON api_endpoint_stats(endpoint);

CREATE INDEX IF NOT EXISTS idx_api_daily_metrics_date ON api_daily_metrics(date);
CREATE INDEX IF NOT EXISTS idx_api_user_activity_date ON api_user_activity(date);
CREATE INDEX IF NOT EXISTS idx_api_user_activity_user_id ON api_user_activity(user_id);

CREATE INDEX IF NOT EXISTS idx_api_system_health_timestamp ON api_system_health(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_alerts_status ON api_alerts(status);
CREATE INDEX IF NOT EXISTS idx_api_alerts_severity ON api_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_api_alerts_created_at ON api_alerts(created_at);

-- Row Level Security policies
ALTER TABLE api_request_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_security_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_user_activity ENABLE ROW LEVEL SECURITY;

-- Only superusers and admins can see monitoring data
CREATE POLICY monitoring_admin_policy ON api_request_logs
    FOR ALL TO authenticated_users
    USING (EXISTS (
        SELECT 1 FROM users u 
        JOIN user_roles ur ON u.id = ur.user_id 
        JOIN roles r ON ur.role_id = r.id 
        WHERE u.id = current_user_id() 
        AND r.name IN ('admin', 'super_admin')
    ));

CREATE POLICY monitoring_admin_policy ON api_performance_metrics
    FOR ALL TO authenticated_users
    USING (EXISTS (
        SELECT 1 FROM users u 
        JOIN user_roles ur ON u.id = ur.user_id 
        JOIN roles r ON ur.role_id = r.id 
        WHERE u.id = current_user_id() 
        AND r.name IN ('admin', 'super_admin')
    ));

CREATE POLICY monitoring_admin_policy ON api_security_events
    FOR ALL TO authenticated_users
    USING (EXISTS (
        SELECT 1 FROM users u 
        JOIN user_roles ur ON u.id = ur.user_id 
        JOIN roles r ON ur.role_id = r.id 
        WHERE u.id = current_user_id() 
        AND r.name IN ('admin', 'super_admin')
    ));

-- Users can see their own activity
CREATE POLICY user_own_activity_policy ON api_user_activity
    FOR ALL TO authenticated_users
    USING (user_id = current_user_id());

-- Functions for automatic data aggregation
CREATE OR REPLACE FUNCTION aggregate_endpoint_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO api_endpoint_stats (
        endpoint, method, date_hour, request_count, total_response_time_ms,
        avg_response_time_ms, min_response_time_ms, max_response_time_ms,
        error_count, status_code_distribution
    )
    VALUES (
        NEW.path,
        NEW.method,
        date_trunc('hour', NEW.timestamp),
        1,
        NEW.response_time_ms,
        NEW.response_time_ms,
        NEW.response_time_ms,
        NEW.response_time_ms,
        CASE WHEN NEW.status_code >= 400 THEN 1 ELSE 0 END,
        jsonb_build_object(NEW.status_code::text, 1)
    )
    ON CONFLICT (endpoint, method, date_hour)
    DO UPDATE SET
        request_count = api_endpoint_stats.request_count + 1,
        total_response_time_ms = api_endpoint_stats.total_response_time_ms + NEW.response_time_ms,
        avg_response_time_ms = (api_endpoint_stats.total_response_time_ms + NEW.response_time_ms) / (api_endpoint_stats.request_count + 1),
        min_response_time_ms = LEAST(api_endpoint_stats.min_response_time_ms, NEW.response_time_ms),
        max_response_time_ms = GREATEST(api_endpoint_stats.max_response_time_ms, NEW.response_time_ms),
        error_count = api_endpoint_stats.error_count + CASE WHEN NEW.status_code >= 400 THEN 1 ELSE 0 END,
        status_code_distribution = api_endpoint_stats.status_code_distribution || 
            jsonb_build_object(NEW.status_code::text, 
                COALESCE((api_endpoint_stats.status_code_distribution->NEW.status_code::text)::int, 0) + 1),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic endpoint stats aggregation
CREATE TRIGGER trigger_aggregate_endpoint_stats
    AFTER INSERT ON api_request_logs
    FOR EACH ROW
    EXECUTE FUNCTION aggregate_endpoint_stats();

-- Function to aggregate daily metrics
CREATE OR REPLACE FUNCTION aggregate_daily_metrics()
RETURNS VOID AS $$
BEGIN
    INSERT INTO api_daily_metrics (
        date,
        total_requests,
        successful_requests,
        failed_requests,
        avg_response_time_ms,
        min_response_time_ms,
        max_response_time_ms,
        unique_users,
        unique_ips,
        top_endpoints,
        error_distribution,
        security_events_count
    )
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as total_requests,
        COUNT(*) FILTER (WHERE status_code < 400) as successful_requests,
        COUNT(*) FILTER (WHERE status_code >= 400) as failed_requests,
        AVG(response_time_ms) as avg_response_time_ms,
        MIN(response_time_ms) as min_response_time_ms,
        MAX(response_time_ms) as max_response_time_ms,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(DISTINCT ip_address) as unique_ips,
        jsonb_object_agg(endpoint, request_count) as top_endpoints,
        jsonb_object_agg(status_code, error_count) as error_distribution,
        (SELECT COUNT(*) FROM api_security_events WHERE DATE(timestamp) = DATE(NOW())) as security_events_count
    FROM (
        SELECT 
            timestamp, status_code, response_time_ms, user_id, ip_address,
            path as endpoint,
            COUNT(*) as request_count,
            COUNT(*) FILTER (WHERE status_code >= 400) as error_count
        FROM api_request_logs 
        WHERE DATE(timestamp) = CURRENT_DATE
        GROUP BY timestamp, status_code, response_time_ms, user_id, ip_address, path
    ) daily_data
    ON CONFLICT (date)
    DO UPDATE SET
        total_requests = EXCLUDED.total_requests,
        successful_requests = EXCLUDED.successful_requests,
        failed_requests = EXCLUDED.failed_requests,
        avg_response_time_ms = EXCLUDED.avg_response_time_ms,
        min_response_time_ms = EXCLUDED.min_response_time_ms,
        max_response_time_ms = EXCLUDED.max_response_time_ms,
        unique_users = EXCLUDED.unique_users,
        unique_ips = EXCLUDED.unique_ips,
        top_endpoints = EXCLUDED.top_endpoints,
        error_distribution = EXCLUDED.error_distribution,
        security_events_count = EXCLUDED.security_events_count,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Schedule daily aggregation (this would typically be handled by a cron job)
-- CREATE OR REPLACE FUNCTION schedule_daily_aggregation()
-- RETURNS VOID AS $$
-- BEGIN
--     PERFORM pg_cron.schedule('daily-metrics-aggregation', '0 1 * * *', 'SELECT aggregate_daily_metrics();');
-- END;
-- $$ LANGUAGE plpgsql;

-- Function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_monitoring_data(retention_days INTEGER DEFAULT 90)
RETURNS VOID AS $$
BEGIN
    -- Clean old request logs
    DELETE FROM api_request_logs 
    WHERE timestamp < NOW() - INTERVAL '1 day' * retention_days;
    
    -- Clean old performance metrics
    DELETE FROM api_performance_metrics 
    WHERE timestamp < NOW() - INTERVAL '1 day' * retention_days;
    
    -- Clean old resolved security events
    DELETE FROM api_security_events 
    WHERE resolved = TRUE 
    AND timestamp < NOW() - INTERVAL '1 day' * retention_days;
    
    -- Clean old endpoint stats (keep last 30 days)
    DELETE FROM api_endpoint_stats 
    WHERE date_hour < NOW() - INTERVAL '30 days';
    
    -- Clean old system health data (keep last 7 days)
    DELETE FROM api_system_health 
    WHERE timestamp < NOW() - INTERVAL '7 days';
    
    -- Clean old resolved alerts (keep last 30 days)
    DELETE FROM api_alerts 
    WHERE status = 'resolved' 
    AND created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at triggers
CREATE TRIGGER update_api_request_logs_updated_at
    BEFORE UPDATE ON api_request_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_security_events_updated_at
    BEFORE UPDATE ON api_security_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_endpoint_stats_updated_at
    BEFORE UPDATE ON api_endpoint_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_daily_metrics_updated_at
    BEFORE UPDATE ON api_daily_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_user_activity_updated_at
    BEFORE UPDATE ON api_user_activity
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_alerts_updated_at
    BEFORE UPDATE ON api_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW api_request_summary AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status_code < 400) as successful_requests,
    COUNT(*) FILTER (WHERE status_code >= 400) as failed_requests,
    AVG(response_time_ms) as avg_response_time_ms,
    MIN(response_time_ms) as min_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT ip_address) as unique_ips
FROM api_request_logs
GROUP BY DATE(timestamp)
ORDER BY date DESC;

CREATE OR REPLACE VIEW api_security_summary AS
SELECT 
    DATE(timestamp) as date,
    event_type,
    severity,
    COUNT(*) as event_count,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT user_id) as unique_users
FROM api_security_events
GROUP BY DATE(timestamp), event_type, severity
ORDER BY date DESC, event_count DESC;

CREATE OR REPLACE VIEW api_top_endpoints AS
SELECT 
    endpoint,
    method,
    SUM(request_count) as total_requests,
    AVG(avg_response_time_ms) as avg_response_time,
    SUM(error_count) as total_errors,
    ROUND((SUM(error_count)::FLOAT / SUM(request_count) * 100), 2) as error_rate
FROM api_endpoint_stats
WHERE date_hour >= NOW() - INTERVAL '24 hours'
GROUP BY endpoint, method
ORDER BY total_requests DESC
LIMIT 20;
