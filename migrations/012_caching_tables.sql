-- Migration 012: Caching Tables for Phase 15.1 Database & Performance
-- Tables for advanced caching and cache management

-- Cache configurations table
CREATE TABLE IF NOT EXISTS cache_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    cache_name VARCHAR(100) NOT NULL,
    cache_type VARCHAR(50) NOT NULL,
    max_size INTEGER NOT NULL,
    ttl_seconds INTEGER NOT NULL,
    strategy VARCHAR(50) NOT NULL DEFAULT 'lru',
    compression_enabled BOOLEAN DEFAULT FALSE,
    serialization_method VARCHAR(50) NOT NULL DEFAULT 'json',
    eviction_threshold DOUBLE PRECISION DEFAULT 0.8,
    cleanup_interval_seconds INTEGER DEFAULT 300,
    metrics_enabled BOOLEAN DEFAULT TRUE,
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, cache_name)
);

-- Cache entries table
CREATE TABLE IF NOT EXISTS cache_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    cache_name VARCHAR(100) NOT NULL,
    key_name VARCHAR(255) NOT NULL,
    value_data BYTEA NOT NULL,
    value_type VARCHAR(50) NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    hit_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    compressed BOOLEAN DEFAULT FALSE,
    encrypted BOOLEAN DEFAULT FALSE,
    tags TEXT[] DEFAULT ARRAY,
    metadata JSONB DEFAULT '{}',
    UNIQUE(tenant_id, cache_name, key_name)
);

-- Connection pool configurations table
CREATE TABLE IF NOT EXISTS connection_pool_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    pool_name VARCHAR(100) NOT NULL,
    database_url VARCHAR(500) NOT NULL,
    min_connections INTEGER NOT NULL DEFAULT 5,
    max_connections INTEGER NOT NULL DEFAULT 20,
    connection_timeout_seconds INTEGER NOT NULL DEFAULT 30,
    idle_timeout_seconds INTEGER NOT NULL DEFAULT 300,
    max_lifetime_seconds INTEGER NOT NULL DEFAULT 3600,
    health_check_interval_seconds INTEGER NOT NULL DEFAULT 60,
    retry_attempts INTEGER NOT NULL DEFAULT 3,
    retry_delay_seconds INTEGER NOT NULL DEFAULT 1,
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, pool_name)
);

-- Connection pool statistics table
CREATE TABLE IF NOT EXISTS connection_pool_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    pool_name VARCHAR(100) NOT NULL,
    total_connections INTEGER DEFAULT 0,
    active_connections INTEGER DEFAULT 0,
    idle_connections INTEGER DEFAULT 0,
    queued_requests INTEGER DEFAULT 0,
    connection_errors INTEGER DEFAULT 0,
    query_errors INTEGER DEFAULT 0,
    health_check_failures INTEGER DEFAULT 0,
    avg_connection_time_ms REAL DEFAULT 0.0,
    avg_query_time_ms REAL DEFAULT 0.0,
    avg_wait_time_ms REAL DEFAULT 0.0,
    pool_utilization_percent REAL DEFAULT 0.0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    statistics_data JSONB DEFAULT '{}'
);

-- Cache warming schedules table
CREATE TABLE IF NOT EXISTS cache_warming_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    cache_name VARCHAR(100) NOT NULL,
    schedule_name VARCHAR(100) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,
    warmup_keys JSONB DEFAULT '[]',
    warmup_queries JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_run_duration_ms REAL DEFAULT 0.0,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, cache_name, schedule_name)
);

-- Cache invalidation rules table
CREATE TABLE IF NOT EXISTS cache_invalidation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    rule_name VARCHAR(100) NOT NULL,
    cache_name VARCHAR(100) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_conditions JSONB DEFAULT '{}',
    invalidation_pattern VARCHAR(255) NOT NULL,
    invalidation_action VARCHAR(50) NOT NULL DEFAULT 'delete',
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, rule_name)
);

-- Performance alerts config table
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
    escalation_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(tenant_id, alert_name)
);

-- Performance alerts history table
CREATE TABLE IF NOT EXISTS performance_alerts_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    alert_config_id UUID NOT NULL REFERENCES performance_alerts_config(id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    current_value DOUBLE PRECISION NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    resolution_note TEXT,
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cache performance metrics table
CREATE TABLE IF NOT EXISTS cache_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    cache_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    key_name VARCHAR(255),
    hit BOOLEAN DEFAULT FALSE,
    response_time_ms REAL DEFAULT 0.0,
    size_bytes INTEGER DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cache_configurations_tenant_active ON cache_configurations(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_cache_entries_tenant_cache ON cache_entries(tenant_id, cache_name);
CREATE INDEX IF NOT EXISTS idx_cache_entries_expires_at ON cache_entries(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_entries_cache_key ON cache_entries(cache_name, key_name);

CREATE INDEX IF NOT EXISTS idx_connection_pool_configurations_tenant_active ON connection_pool_configurations(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_connection_pool_statistics_tenant_pool ON connection_pool_statistics(tenant_id, pool_name);
CREATE INDEX IF NOT EXISTS idx_connection_pool_statistics_timestamp ON connection_pool_statistics(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_cache_warming_schedules_tenant_active ON cache_warming_schedules(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_cache_warming_schedules_next_run ON cache_warming_schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_cache_invalidation_rules_tenant_active ON cache_invalidation_rules(tenant_id, is_active);

CREATE INDEX IF NOT EXISTS idx_performance_alerts_config_tenant_active ON performance_alerts_config(tenant_id, enabled);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_history_tenant_timestamp ON performance_alerts_history(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_history_resolved ON performance_alerts_history(resolved);

CREATE INDEX IF NOT EXISTS idx_cache_performance_metrics_tenant_cache ON cache_performance_metrics(tenant_id, cache_name);
CREATE INDEX IF NOT EXISTS idx_cache_performance_metrics_timestamp ON cache_performance_metrics(timestamp DESC);

-- Create views for cache analysis
CREATE OR REPLACE VIEW cache_overview AS
SELECT 
    c.cache_name,
    c.cache_type,
    c.max_size,
    c.ttl_seconds,
    c.strategy,
    c.is_active,
    COUNT(e.id) as entry_count,
    COALESCE(SUM(e.size_bytes), 0) as total_size_bytes,
    COALESCE(SUM(e.hit_count), 0) as total_hits,
    COALESCE(SUM(e.access_count), 0) as total_accesses,
    CASE 
        WHEN COALESCE(SUM(e.access_count), 0) > 0 
        THEN (COALESCE(SUM(e.hit_count), 0) * 100.0 / COALESCE(SUM(e.access_count), 0))
        ELSE 0 
    END as hit_rate_percent,
    MAX(e.last_accessed) as last_accessed_time,
    c.created_at
FROM cache_configurations c
LEFT JOIN cache_entries e ON c.cache_name = e.cache_name AND c.tenant_id = e.tenant_id
WHERE c.tenant_id = e.tenant_id
GROUP BY c.cache_name, c.cache_type, c.max_size, c.ttl_seconds, c.strategy, c.is_active, c.created_at
ORDER BY c.cache_name;

CREATE OR REPLACE VIEW connection_pool_overview AS
SELECT 
    p.pool_name,
    p.min_connections,
    p.max_connections,
    p.is_active,
    COALESCE(s.total_connections, 0) as current_total,
    COALESCE(s.active_connections, 0) as current_active,
    COALESCE(s.idle_connections, 0) as current_idle,
    COALESCE(s.queued_requests, 0) as current_queued,
    COALESCE(s.pool_utilization_percent, 0) as utilization_percent,
    COALESCE(s.avg_connection_time_ms, 0) as avg_connection_time_ms,
    COALESCE(s.avg_query_time_ms, 0) as avg_query_time_ms,
    s.timestamp as last_updated,
    p.created_at
FROM connection_pool_configurations p
LEFT JOIN LATERAL (
    SELECT *
    FROM connection_pool_statistics s2
    WHERE s2.pool_name = p.pool_name AND s2.tenant_id = p.tenant_id
    ORDER BY s2.timestamp DESC
    LIMIT 1
) s ON true
WHERE p.tenant_id = s.tenant_id
ORDER BY p.pool_name;

CREATE OR REPLACE VIEW cache_performance_summary AS
SELECT 
    cache_name,
    operation_type,
    COUNT(*) as operation_count,
    COUNT(*) FILTER (hit = TRUE) as hit_count,
    COUNT(*) FILTER (hit = FALSE) as miss_count,
    CASE 
        WHEN COUNT(*) > 0 
        THEN (COUNT(*) FILTER (hit = TRUE) * 100.0 / COUNT(*))
        ELSE 0 
    END as hit_rate_percent,
    AVG(response_time_ms) as avg_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms,
    MIN(response_time_ms) as min_response_time_ms,
    AVG(size_bytes) as avg_size_bytes,
    SUM(size_bytes) as total_size_bytes,
    MAX(timestamp) as last_operation_time
FROM cache_performance_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY cache_name, operation_type
ORDER BY cache_name, operation_type;

-- Create functions for cache management
CREATE OR REPLACE FUNCTION cleanup_expired_cache_entries() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up expired cache entries
    DELETE FROM cache_entries 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$;

CREATE OR REPLACE FUNCTION cleanup_old_cache_metrics(
    days_old INTEGER DEFAULT 7
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old cache performance metrics
    DELETE FROM cache_performance_metrics 
    WHERE timestamp < NOW() - INTERVAL f'{days_old} days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$;

CREATE OR REPLACE FUNCTION get_cache_statistics(
    tenant_id UUID,
    cache_name VARCHAR DEFAULT NULL
) RETURNS TABLE(
    cache_name TEXT,
    total_entries BIGINT,
    total_size_bytes BIGINT,
    hit_rate_percent REAL,
    avg_response_time_ms REAL,
    last_accessed_time TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.cache_name,
        COUNT(*) as total_entries,
        COALESCE(SUM(e.size_bytes), 0) as total_size_bytes,
        CASE 
            WHEN COALESCE(SUM(e.access_count), 0) > 0 
            THEN (COALESCE(SUM(e.hit_count), 0) * 100.0 / COALESCE(SUM(e.access_count), 0))
            ELSE 0 
        END as hit_rate_percent,
        COALESCE(AVG(m.response_time_ms), 0) as avg_response_time_ms,
        MAX(e.last_accessed) as last_accessed_time
    FROM cache_entries e
    LEFT JOIN cache_performance_metrics m ON e.cache_name = m.cache_name 
        AND e.tenant_id = m.tenant_id
        AND m.timestamp >= NOW() - INTERVAL '24 hours'
    WHERE e.tenant_id = tenant_id
        AND (cache_name IS NULL OR e.cache_name = cache_name)
    GROUP BY e.cache_name
    ORDER BY e.cache_name;
END;
$$;

CREATE OR REPLACE FUNCTION get_connection_pool_statistics(
    tenant_id UUID,
    pool_name VARCHAR DEFAULT NULL
) RETURNS TABLE(
    pool_name TEXT,
    total_connections INTEGER,
    active_connections INTEGER,
    idle_connections INTEGER,
    queued_requests INTEGER,
    utilization_percent REAL,
    avg_connection_time_ms REAL,
    avg_query_time_ms REAL,
    last_updated TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.pool_name,
        s.total_connections,
        s.active_connections,
        s.idle_connections,
        s.queued_requests,
        s.pool_utilization_percent,
        s.avg_connection_time_ms,
        s.avg_query_time_ms,
        s.timestamp as last_updated
    FROM connection_pool_statistics s
    WHERE s.tenant_id = tenant_id
        AND (pool_name IS NULL OR s.pool_name = pool_name)
        AND s.timestamp = (
            SELECT MAX(timestamp) 
            FROM connection_pool_statistics s2 
            WHERE s2.tenant_id = s.tenant_id 
                AND (pool_name IS NULL OR s2.pool_name = pool_name)
                AND s2.pool_name = s.pool_name
        )
    ORDER BY s.pool_name;
END;
$$;

-- Insert default cache configurations
INSERT INTO cache_configurations (tenant_id, cache_name, cache_type, max_size, ttl_seconds, strategy) VALUES
('00000000-0000-0000-0000-000000000000', 'default', 'memory', 10000, 3600, 'lru'),
('00000000-0000-0000-0000-000000000000', 'query_cache', 'memory', 5000, 1800, 'lru'),
('00000000-0000-0000-0000-000000000000', 'session_cache', 'memory', 2000, 7200, 'lru'),
('00000000-0000-0000-0000-000000000000', 'redis_cache', 'redis', 50000, 3600, 'lru')
ON CONFLICT (tenant_id, cache_name) DO NOTHING;

-- Insert default connection pool configuration
INSERT INTO connection_pool_configurations (
    tenant_id, pool_name, database_url, min_connections, max_connections
) VALUES (
    '00000000-0000-0000-0000-000000000000', 
    'default', 
    'postgresql://localhost:5432/sorce', 
    5, 
    20
) ON CONFLICT (tenant_id, pool_name) DO NOTHING;

-- Add comments
COMMENT ON TABLE cache_configurations IS 'Stores cache configuration settings';
COMMENT ON TABLE cache_entries IS 'Stores individual cache entries with metadata';
COMMENT ON TABLE connection_pool_configurations IS 'Stores database connection pool configurations';
COMMENT ON TABLE connection_pool_statistics IS 'Stores connection pool performance statistics';
COMMENT ON TABLE cache_warming_schedules IS 'Stores cache warming schedule configurations';
COMMENT ON TABLE cache_invalidation_rules IS 'Stores cache invalidation rule configurations';
COMMENT ON TABLE performance_alerts_config IS 'Stores performance alert configurations';
COMMENT ON TABLE performance_alerts_history IS 'Stores performance alert history';
COMMENT ON TABLE cache_performance_metrics IS 'Stores cache performance metrics';

-- Grant permissions
GRANT SELECT ON cache_configurations TO postgres;
GRANT SELECT ON cache_entries TO postgres;
GRANT SELECT ON connection_pool_configurations TO postgres;
GRANT SELECT ON connection_pool_statistics TO postgres;
GRANT SELECT ON cache_warming_schedules TO postgres;
GRANT SELECT ON cache_invalidation_rules TO postgres;
GRANT SELECT ON performance_alerts_config TO postgres;
GRANT SELECT ON performance_alerts_history TO postgres;
GRANT SELECT ON cache_performance_metrics TO postgres;
GRANT SELECT ON cache_overview TO postgres;
GRANT SELECT ON connection_pool_overview TO postgres;
GRANT SELECT ON cache_performance_summary TO postgres;
