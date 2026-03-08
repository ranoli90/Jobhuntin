-- Migration 009: Cache and Connection Pool Tables for Phase 15.1
-- Tables for advanced caching and connection pool management

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

-- Cache entries table (for persistent cache tracking)
CREATE TABLE IF NOT EXISTS cache_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    cache_name VARCHAR(100) NOT NULL,
    cache_key VARCHAR(500) NOT NULL,
    cache_type VARCHAR(50) NOT NULL,
    cache_level VARCHAR(50) NOT NULL,
    value_size_bytes INTEGER,
    hit_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    UNIQUE(tenant_id, cache_name, cache_key)
);

-- Connection pool configurations table
CREATE TABLE IF NOT EXISTS connection_pool_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    pool_name VARCHAR(100) NOT NULL,
    connection_type VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    database VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    min_connections INTEGER NOT NULL,
    max_connections INTEGER NOT NULL,
    ssl_mode VARCHAR(20) NOT NULL DEFAULT 'prefer',
    command_timeout INTEGER DEFAULT 30,
    statement_timeout INTEGER DEFAULT 30000,
    idle_timeout INTEGER DEFAULT 300,
    max_lifetime INTEGER DEFAULT 3600,
    max_queries_per_connection INTEGER DEFAULT 5000,
    health_check_interval INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    retry_delay DOUBLE PRECISION DEFAULT 1.0,
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
    memory_usage_percent DOUBLE PRECISION DEFAULT 0.0,
    cpu_usage_percent DOUBLE PRECISION DEFAULT 0.0,
    statistics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cache warming schedules table
CREATE TABLE IF NOT EXISTS cache_warming_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    schedule_name VARCHAR(100) NOT NULL,
    cache_name VARCHAR(100) NOT NULL,
    key_pattern VARCHAR(255),
    data_loader_function VARCHAR(255),
    ttl_seconds INTEGER,
    schedule_type VARCHAR(50) NOT NULL DEFAULT 'cron',
    schedule_expression VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cache invalidation rules table
CREATE TABLE IF NOT EXISTS cache_invalidation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    rule_name VARCHAR(100) NOT NULL,
    cache_name VARCHAR(100) NOT NULL,
    invalidation_type VARCHAR(50) NOT NULL,
    pattern VARCHAR(255),
    condition_expression TEXT,
    action_type VARCHAR(50) NOT NULL DEFAULT 'delete',
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance alerts configuration table
CREATE TABLE IF NOT EXISTS performance_alerts_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    alert_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    condition_expression TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    threshold_value DOUBLE PRECISION,
    comparison_operator VARCHAR(10) NOT NULL DEFAULT 'gt',
    cooldown_period_minutes INTEGER DEFAULT 5,
    notification_channels JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance alerts history table
CREATE TABLE IF NOT EXISTS performance_alerts_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    alert_config_id UUID REFERENCES performance_alerts_config(id),
    alert_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    current_value DOUBLE PRECISION NOT NULL,
    threshold_value DOUBLE PRECISION,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT,
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_results JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cache_configurations_tenant_name ON cache_configurations(tenant_id, cache_name);
CREATE INDEX IF NOT EXISTS idx_cache_configurations_type_active ON cache_configurations(cache_type, is_active);

CREATE INDEX IF NOT EXISTS idx_cache_entries_tenant_cache ON cache_entries(tenant_id, cache_name);
CREATE INDEX IF NOT EXISTS idx_cache_entries_key_accessed ON cache_entries(cache_key, last_accessed DESC);
CREATE INDEX IF NOT EXISTS idx_cache_entries_expires ON cache_entries(expires_at);

CREATE INDEX IF NOT EXISTS idx_connection_pool_configurations_tenant_name ON connection_pool_configurations(tenant_id, pool_name);
CREATE INDEX IF NOT EXISTS idx_connection_pool_configurations_type_active ON connection_pool_configurations(connection_type, is_active);

CREATE INDEX IF NOT EXISTS idx_connection_pool_statistics_tenant_timestamp ON connection_pool_statistics(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_connection_pool_statistics_pool_name ON connection_pool_statistics(pool_name);
CREATE INDEX IF NOT EXISTS idx_connection_pool_statistics_status ON connection_pool_statistics(status);

CREATE INDEX IF NOT EXISTS idx_cache_warming_schedules_tenant_active ON cache_warming_schedules(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_cache_warming_schedules_next_run ON cache_warming_schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_cache_warming_schedules_cache_name ON cache_warming_schedules(cache_name);

CREATE INDEX IF NOT EXISTS idx_cache_invalidation_rules_tenant_active ON cache_invalidation_rules(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_cache_invalidation_rules_cache_name ON cache_invalidation_rules(cache_name);
CREATE INDEX IF NOT EXISTS idx_cache_invalidation_rules_priority ON cache_invalidation_rules(priority DESC);

CREATE INDEX IF NOT EXISTS idx_performance_alerts_config_tenant_active ON performance_alerts_config(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_config_metric ON performance_alerts_config(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_config_severity ON performance_alerts_config(severity);

CREATE INDEX IF NOT EXISTS idx_performance_alerts_history_tenant_timestamp ON performance_alerts_history(tenant_id, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_history_config ON performance_alerts_history(alert_config_id);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_history_resolved ON performance_alerts_history(resolved_at DESC);

-- Create views for cache and connection pool analytics
CREATE OR REPLACE VIEW cache_performance_summary AS
SELECT 
    ce.tenant_id,
    ce.cache_name,
    ce.cache_type,
    ce.cache_level,
    COUNT(*) as total_entries,
    SUM(ce.hit_count) as total_hits,
    SUM(ce.miss_count) as total_misses,
    CASE 
        WHEN SUM(ce.hit_count + ce.miss_count) > 0 THEN 
            (SUM(ce.hit_count) * 100.0 / SUM(ce.hit_count + ce.miss_count))
        ELSE 0
    END as hit_rate_percent,
    SUM(ce.value_size_bytes) as total_size_bytes,
    AVG(ce.value_size_bytes) as avg_size_bytes,
    COUNT(*) FILTER (WHERE ce.expires_at <= NOW()) as expired_entries,
    MAX(ce.last_accessed) as last_accessed_timestamp
FROM cache_entries ce
GROUP BY ce.tenant_id, ce.cache_name, ce.cache_type, ce.cache_level;

CREATE OR REPLACE VIEW connection_pool_health_summary AS
SELECT 
    cps.tenant_id,
    cps.pool_name,
    cpc.connection_type,
    AVG(cps.total_connections) as avg_total_connections,
    AVG(cps.active_connections) as avg_active_connections,
    AVG(cps.idle_connections) as avg_idle_connections,
    AVG(cps.queued_requests) as avg_queued_requests,
    AVG(cps.avg_connection_time_ms) as avg_connection_time_ms,
    AVG(cps.avg_query_time_ms) as avg_query_time_ms,
    SUM(cps.connection_errors) as total_connection_errors,
    SUM(cps.query_errors) as total_query_errors,
    COUNT(*) FILTER (WHERE cps.status = 'healthy') as healthy_samples,
    COUNT(*) FILTER (WHERE cps.status = 'degraded') as degraded_samples,
    COUNT(*) FILTER (WHERE cps.status = 'critical') as critical_samples,
    MAX(cps.created_at) as last_sample_timestamp
FROM connection_pool_statistics cps
JOIN connection_pool_configurations cpc ON cps.pool_name = cpc.pool_name AND cps.tenant_id = cpc.tenant_id
WHERE cps.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY cps.tenant_id, cps.pool_name, cpc.connection_type;

CREATE OR REPLACE VIEW performance_alerts_summary AS
SELECT 
    pah.tenant_id,
    pac.alert_name,
    pac.alert_type,
    pac.metric_name,
    pah.severity,
    COUNT(*) as alert_count,
    COUNT(*) FILTER (WHERE pah.resolved_at IS NULL) as unresolved_count,
    AVG(pah.current_value) as avg_current_value,
    AVG(pah.threshold_value) as avg_threshold_value,
    MAX(pah.triggered_at) as last_triggered_timestamp,
    COUNT(*) FILTER (WHERE pah.notification_sent = TRUE) as notifications_sent
FROM performance_alerts_history pah
JOIN performance_alerts_config pac ON pah.alert_config_id = pac.id
WHERE pah.triggered_at >= NOW() - INTERVAL '24 hours'
GROUP BY pah.tenant_id, pac.alert_name, pac.alert_type, pac.metric_name, pah.severity;

-- Insert default cache configurations
INSERT INTO cache_configurations (id, tenant_id, cache_name, cache_type, max_size, ttl_seconds, strategy, compression_enabled, serialization_method, eviction_threshold, cleanup_interval_seconds, metrics_enabled)
SELECT 
    gen_random_uuid(),
    t.id,
    unnest(ARRAY['default', 'session', 'query', 'static']),
    unnest(ARRAY['hybrid', 'memory', 'redis', 'redis']),
    unnest(ARRAY[10000, 1000, 50000, 100000]),
    unnest(ARRAY[3600, 1800, 7200, 86400]),
    unnest(ARRAY['lru', 'ttl', 'lfu', 'lru']),
    unnest(ARRAY[false, false, true, true]),
    unnest(ARRAY['json', 'json', 'pickle', 'json']),
    unnest(ARRAY[0.8, 0.9, 0.7, 0.6]),
    unnest(ARRAY[300, 600, 300, 1800]),
    true
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM cache_configurations cc 
    WHERE cc.tenant_id = t.id 
    AND cc.cache_name IN ('default', 'session', 'query', 'static')
)
ON CONFLICT (tenant_id, cache_name) DO NOTHING;

-- Insert default connection pool configurations
INSERT INTO connection_pool_configurations (id, tenant_id, pool_name, connection_type, host, port, database, username, min_connections, max_connections, ssl_mode, command_timeout, statement_timeout, idle_timeout, max_lifetime, max_queries_per_connection, health_check_interval, retry_attempts, retry_delay)
SELECT 
    gen_random_uuid(),
    t.id,
    'default_pool',
    'read_write',
    'localhost',
    5432,
    'jobhuntin',
    'jobhuntin_user',
    5,
    20,
    'prefer',
    30,
    30000,
    300,
    3600,
    5000,
    30,
    3,
    1.0
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM connection_pool_configurations cpc 
    WHERE cpc.tenant_id = t.id 
    AND cpc.pool_name = 'default_pool'
)
ON CONFLICT (tenant_id, pool_name) DO NOTHING;

-- Insert default performance alert configurations
INSERT INTO performance_alerts_config (id, tenant_id, alert_name, alert_type, metric_name, condition_expression, severity, threshold_value, comparison_operator, cooldown_period_minutes, notification_channels, is_active)
SELECT 
    gen_random_uuid(),
    t.id,
    unnest(ARRAY['High CPU Usage', 'High Memory Usage', 'High Disk Usage', 'Connection Pool Exhaustion', 'Slow Query Response']),
    unnest(ARRAY['system', 'system', 'system', 'database', 'database']),
    unnest(ARRAY['cpu_percent', 'memory_percent', 'disk_percent', 'connection_pool_utilization', 'query_response_time']),
    unnest(ARRAY['value > threshold', 'value > threshold', 'value > threshold', 'value > threshold', 'value > threshold']),
    unnest(ARRAY['warning', 'warning', 'warning', 'critical', 'critical']),
    unnest(ARRAY[80.0, 85.0, 85.0, 90.0, 2000.0]),
    unnest(ARRAY['gt', 'gt', 'gt', 'gt', 'gt']),
    unnest(ARRAY[5, 5, 5, 2, 2]),
    unnest(ARRAY['["email"]', '["email"]', '["email"]', '["email", "webhook"]', '["email", "webhook"]']),
    true
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM performance_alerts_config pac 
    WHERE pac.tenant_id = t.id 
    AND pac.alert_name IN ('High CPU Usage', 'High Memory Usage', 'High Disk Usage', 'Connection Pool Exhaustion', 'Slow Query Response')
)
ON CONFLICT DO NOTHING;

-- Comments
COMMENT ON TABLE cache_configurations IS 'Stores cache configuration settings for different cache types';
COMMENT ON TABLE cache_entries IS 'Tracks cache entries for monitoring and analytics';
COMMENT ON TABLE connection_pool_configurations IS 'Stores database connection pool configuration settings';
COMMENT ON TABLE connection_pool_statistics IS 'Stores connection pool performance statistics';
COMMENT ON TABLE cache_warming_schedules IS 'Stores cache warming schedules and configurations';
COMMENT ON TABLE cache_invalidation_rules IS 'Stores cache invalidation rules and patterns';
COMMENT ON TABLE performance_alerts_config IS 'Stores performance alert configuration settings';
COMMENT ON TABLE performance_alerts_history IS 'Stores history of triggered performance alerts';
