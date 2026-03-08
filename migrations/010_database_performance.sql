-- Migration 010: Database Performance Tables for Phase 15.1
-- Additional performance monitoring and optimization tables

-- Performance monitoring tables
CREATE TABLE IF NOT EXISTS performance_monitoring_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    snapshot_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    snapshot_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query performance analysis tables
CREATE TABLE IF NOT EXISTS query_performance_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    query_hash VARCHAR(64) NOT NULL,
    normalized_query TEXT NOT NULL,
    execution_plan JSONB NOT NULL DEFAULT '{}',
    performance_metrics JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    query_count INTEGER DEFAULT 0,
    avg_execution_time_ms REAL DEFAULT 0.0,
    total_execution_time_ms REAL DEFAULT 0.0,
    slow_queries_count INTEGER DEFAULT 0,
    optimization_opportunities JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Database connection pool monitoring
CREATE TABLE IF NOT EXISTS connection_pool_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    pool_name VARCHAR(100) NOT NULL,
    pool_status VARCHAR(20) NOT NULL,
    total_connections INTEGER DEFAULT 0,
    active_connections INTEGER DEFAULT 0,
    idle_connections INTEGER DEFAULT 0,
    queued_requests INTEGER DEFAULT 0,
    avg_connection_time_ms REAL DEFAULT 0.0,
    avg_query_time_ms REAL DEFAULT 0.0,
    connection_errors INTEGER DEFAULT 0,
    query_errors INTEGER DEFAULT 0,
    health_check_failures INTEGER DEFAULT 0,
    snapshot_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index usage analysis tables
CREATE TABLE IF NOT EXISTS index_usage_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    table_name VARCHAR(100) NOT NULL,
    index_name VARCHAR(100),
    index_type VARCHAR(50) NOT NULL,
    scans INTEGER DEFAULT 0,
    tuples_read INTEGER DEFAULT 0,
    tuples_returned INTEGER DEFAULT 0,
    avg_scan_time_ms REAL DEFAULT 0.0,
    size_bytes BIGINT DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance optimization tracking
CREATE TABLE IF NOT EXISTS performance_optimizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    optimization_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    index_name VARCHAR(100),
    optimization_sql TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    estimated_improvement REAL DEFAULT 0.0,
    implementation_cost VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    implemented_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    implementation_result JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query performance trends
CREATE TABLE IF NOT EXISTS query_performance_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    query_hash VARCHAR(64) NOT NULL,
    time_period_hours INTEGER NOT NULL,
    trend_direction VARCHAR(20) NOT NULL,
    current_avg_time_ms REAL DEFAULT 0.0,
    baseline_avg_time_ms REAL DEFAULT 0.0,
    improvement_percentage REAL DEFAULT 0.0,
    confidence_score REAL DEFAULT 0.0,
    data_points INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance alerts
CREATE TABLE IF NOT EXISTS performance_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    current_value REAL DEFAULT 0.0,
    threshold_value REAL DEFAULT 0.0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Database performance metrics
CREATE TABLE IF NOT EXISTS database_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance recommendations
CREATE TABLE IF NOT EXISTS performance_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    recommendation_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL,
    impact_score REAL DEFAULT 0.0,
    implementation_cost VARCHAR(20) NOT NULL,
    estimated_benefit TEXT,
    sql_statement TEXT,
    risks TEXT[] DEFAULT ARRAY,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create views for performance analysis
CREATE OR REPLACE VIEW performance_overview AS
SELECT 
    'database_performance' as category,
    COUNT(*) as total_metrics,
    COUNT(*) FILTER (metric_value > 1000) as slow_metrics,
        AVG(CASE WHEN metric_value IS NOT NULL) as avg_value,
        MAX(CASE WHEN metric_value IS NOT NULL) as max_value,
        MIN(CASE WHEN metric_value IS NOT NULL) as min_value,
        MAX(timestamp) as latest_timestamp
FROM database_performance_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY category
ORDER BY latest_timestamp DESC;

CREATE OR REPLACE VIEW slow_queries_overview AS
SELECT 
    query_hash,
        avg_execution_time_ms,
        total_executions,
        slow_queries_count,
        COUNT(*) FILTER (avg_execution_time > 1000) as slow_count
FROM query_performance_analysis
WHERE avg_execution_time > 1000
ORDER BY avg_execution_time DESC
LIMIT 20;

CREATE OR REPLACE VIEW index_usage_overview AS
SELECT 
    table_name,
    index_name,
    index_type,
        scans,
        tuples_read,
        tuples_returned,
        avg_scan_time_ms,
        size_bytes,
        last_used,
        created_at
FROM index_usage_analysis
WHERE last_used >= NOW() - INTERVAL '24 hours'
ORDER BY last_used DESC;

CREATE OR REPLACE VIEW optimization_overview AS
SELECT 
    optimization_type,
    COUNT(*) as total_optimizations,
        COUNT(*) FILTER (status = 'completed') as completed_count,
        COUNT(*) FILTER (status = 'pending') as pending_count,
        AVG(estimated_improvement) as avg_improvement,
        COUNT(*) FILTER (implementation_cost = 'low') as low_cost_count,
        COUNT(*) FILTER (implementation_cost = 'high') as high_cost_count,
        MAX(estimated_improvement) as max_improvement,
        AVG(estimated_improvement) as avg_improvement,
        created_at
FROM performance_optimizations
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY optimization_type
ORDER BY avg_improvement DESC
LIMIT 20;

-- Create functions for performance analysis
CREATE OR REPLACE FUNCTION calculate_query_hash(query TEXT) RETURNS TEXT AS $$
BEGIN
    -- Remove whitespace and normalize
    query = regexp_replace('\s+', ' ', query, 'g')
    query = regexp_replace('\s+', ' ', query, 'g')
    query = regexp_replace('\s+', ' ', query, 'g')
    query = regexp_replace('\s+', ' ', query, 'g')
    query = regexp_replace('\s+', ' ', query, 'g')
    query = regexp_replace('\s+', ' ', query, 'g')
    query = regexp_replace('\s+', ' ', query, 'g')
    query = regexp_replace('\s+', ' ', query, 'g')
    
    -- Create hash
    query = encode(decode(query, 'utf-8', 'ignore')
    query = encode(query, 'utf-8', 'ignore')
    query = encode(query, 'utf-8', 'ignore')
    
    RETURN query;
END;

CREATE OR REPLACE FUNCTION is_slow_query(query TEXT) RETURNS BOOLEAN AS $$
BEGIN
    RETURN (
        SELECT COUNT(*) > 10 AND
        EXISTS (
            SELECT 1 FROM pg_stat_statements 
            WHERE query = calculate_query_hash(query)
            AND mean_exec_time > 1000
        )
    );
END;

CREATE OR REPLACE FUNCTION get_query_performance_stats(query_hash TEXT) RETURNS TABLE(
    query_hash TEXT,
    avg_execution_time_ms REAL,
    total_executions INTEGER,
    slow_queries_count INTEGER,
        last_execution_time TIMESTAMP,
        execution_plan JSONB
    ) AS $$
BEGIN
    SELECT 
        calculate_query_hash(query_hash) as query_hash,
        avg_execution_time_ms,
        total_executions,
        COUNT(*) FILTER (mean_exec_time > 1000) as slow_queries_count,
        MAX(execution_time) as last_execution_time,
        execution_plan
    FROM query_performance_analysis
    WHERE query_hash = query_hash;
END;

-- Create trigger for automatic cleanup
CREATE OR REPLACE FUNCTION cleanup_old_performance_data() RETURNS INT AS $$
BEGIN
    -- Clean up old performance data (older than 30 days)
    DELETE FROM performance_metrics WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM query_performance_analysis WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM connection_pool_snapshots WHERE timestamp < NOW() - INTERVAL '7 days';
    DELETE FROM index_usage_analysis WHERE last_used < NOW() - INTERVAL '7 days';
    DELETE FROM performance_optimizations WHERE created_at < NOW() - INTERVAL '30 days';
    DELETE FROM performance_alerts WHERE timestamp < NOW() - INTERVAL '7 days';
    
    RETURN 1;
END;

-- Create trigger for automatic statistics updates
CREATE OR REPLACE FUNCTION update_performance_stats() RETURNS TRIGGER AS $$
BEGIN
    UPDATE performance_metrics SET total_entries = (
        SELECT COUNT(*) FROM performance_metrics
    );
    
    UPDATE performance_metrics SET avg_query_time_ms = (
        SELECT AVG(CASE WHEN metric_name LIKE '%_time%' AND metric_value IS NOT NULL) 
        FROM performance_metrics
        WHERE metric_name LIKE '%_time%'
    );
    
    UPDATE performance_metrics SET avg_query_time_ms = COALESCE(
        CASE 
            WHEN COUNT(*) > 0 THEN 
                (SELECT AVG(CASE WHEN metric_name LIKE '%_time%' AND metric_value IS NOT NULL) FROM performance_metrics WHERE metric_name LIKE '%_time%')
            WHEN COUNT(*) = 0 THEN 0
            ELSE 0
        END
    );
    
    UPDATE performance_metrics SET hit_rate = (
        CASE 
            WHEN (SELECT COUNT(*) FROM performance_metrics) > 0 THEN
                (SELECT (SELECT COUNT(*) FILTER (metric_value IS NOT NULL) FROM performance_metrics) * 100.0 / COUNT(*)) / COUNT(*))
            WHEN (SELECT COUNT(*) FROM performance_metrics) = 0 THEN 0.0
            ELSE 0.0
        END
    );
    
    UPDATE performance_metrics SET last_updated = NOW();
END;

-- Create trigger for automatic snapshots
CREATE OR REPLACE FUNCTION create_performance_snapshot() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO performance_monitoring_snapshots (
        tenant_id,
        'automatic',
        jsonb_build_object(
            'metrics', (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'name', name,
                        'value', metric_value,
                        'unit', unit,
                        'labels', labels
                    )
                    ORDER BY timestamp DESC
                ),
                'alerts', (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'title', title,
                            'message', message,
                            'severity', severity,
                            'timestamp', timestamp
                        )
                    ORDER BY timestamp DESC
                )
            )
        )
    );
END;

-- Schedule automatic cleanup
CREATE OR REPLACE FUNCTION schedule_cleanup() RETURNS VOID AS $$
BEGIN
    SELECT schedule_cleanup();
END;

-- Schedule automatic snapshots
CREATE OR REPLACE FUNCTION schedule_snapshots() RETURNS VOID AS $$
BEGIN
    SELECT schedule_snapshots();
    SELECT schedule_cleanup();
END;

-- Schedule automatic stats updates
CREATE OR REPLACE FUNCTION schedule_stats_update() RETURNS VOID AS $$
BEGIN
    SELECT schedule_stats_update();
END;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_performance_metrics_tenant_timestamp ON performance_metrics(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_timestamp ON performance_metrics(name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_category_timestamp ON performance_metrics(category, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_query_analysis_tenant_hash ON query_analysis(tenant_id, query_hash);
CREATE INDEX IF NOT EXISTS idx_query_analysis_timestamp ON query_analysis(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_index_usage_table_name_timestamp ON index_usage(table_name, last_used DESC);
CREATE INDEX IF NOT EXISTS idx_performance_optimizations_tenant_timestamp ON performance_optimizations(tenant_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_performance_alerts_tenant_timestamp ON performance_alerts(tenant_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_database_performance_metrics_category_timestamp ON database_performance_metrics(category, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_query_performance_analysis_tenant_hash_timestamp ON query_performance_analysis(tenant_id, query_hash, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_connection_pool_snapshots_tenant_timestamp ON connection_pool_snapshots(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_index_usage_analysis_tenant_timestamp ON index_usage(tenant_id, last_used DESC);
CREATE INDEX IF NOT EXISTS idx_performance_optimizations_tenant_timestamp ON performance_optimizations(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_tenant_timestamp ON performance_alerts(tenant_id, timestamp DESC);

-- Add comments
COMMENT ON TABLE performance_monitoring_snapshots IS 'Stores performance monitoring snapshots for analysis';
COMMENT ON TABLE query_performance_analysis IS 'Stores SQL query performance analysis results';
COMMENT ON index_usage_analysis IS 'Stores index usage statistics and analysis';
COMMENT ON performance_optimizations IS 'Stores database optimization recommendations and tracking';
COMMENT ON query_performance_trends IS 'Stores query performance trend analysis over time';
COMMENT ON performance_alerts IS 'Stores performance alerts and their resolution status';
COMMENT ON database_performance_metrics IS 'Stores database performance metrics over time';
COMMENT ON performance_recommendations IS 'Stores performance optimization recommendations';
COMMENT ON performance_overview IS 'Provides overview of all performance metrics';

-- Grant permissions
GRANT SELECT ON performance_monitoring_snapshots TO postgres;
GRANT SELECT ON query_performance_analysis TO postgres;
GRANT SELECT ON index_usage_analysis TO postgres;
GRANT SELECT ON performance_optimizations TO postgres;
GRANT SELECT ON query_performance_trends TO postgres;
GRANT SELECT ON performance_alerts TO postgres;
GRANT SELECT ON database_performance_metrics TO postgres;
GRANT SELECT ON performance_recommendations TO postgres;
GRANT SELECT ON performance_overview TO postgres;

-- Add comments for tables
COMMENT ON TABLE performance_monitoring_snapshots IS 'Stores performance monitoring snapshots for analysis';
COMMENT ON TABLE query_performance_analysis IS 'Stores SQL query performance analysis results';
COMMENT ON index_usage_analysis IS 'Stores index usage statistics and analysis';
COMMENT ON performance_optimizations IS 'Stores database optimization recommendations and tracking';
COMMENT ON query_performance_trends IS 'Stores query performance trend analysis over time';
COMMENT ON performance_alerts IS 'Stores performance alerts and their resolution status';
COMMENT ON database_performance_metrics IS 'Stores database performance metrics over time';
COMMENT ON performance_recommendations IS 'Stores performance optimization recommendations';
COMMENT ON performance_overview IS 'Provides overview of all performance metrics';

-- Create trigger to schedule cleanup (every hour)
CREATE OR REPLACE FUNCTION schedule_cleanup() RETURNS VOID AS $$
BEGIN
    -- Clean up old performance data (older than 30 days)
    DELETE FROM performance_metrics WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM query_performance_analysis WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM connection_pool_snapshots WHERE timestamp < NOW() - INTERVAL '7 days';
    DELETE FROM index_usage_analysis WHERE last_used < NOW() - INTERVAL '7 days';
    DELETE FROM performance_optimizations WHERE created_at < NOW() - INTERVAL '30 days';
    DELETE FROM performance_alerts WHERE timestamp < NOW() - INTERVAL '7 days';
    
    RETURN 1;
END;

-- Create trigger to schedule snapshots (every 5 minutes)
CREATE OR REPLACE FUNCTION schedule_snapshots() RETURNS VOID AS $$
BEGIN
    PERFORM create_performance_snapshot();
END;

-- Create trigger to update statistics (every minute)
CREATE OR REPLACE FUNCTION schedule_stats_update() RETURNS VOID AS $$
BEGIN
    PERFORM update_performance_stats();
END;

-- Create trigger to schedule snapshots (every 5 minutes)
CREATE OR REPLACE FUNCTION schedule_snapshots() RETURNS VOID AS $$
BEGIN
    PERFORM schedule_snapshots();
END;

-- Create trigger to update statistics (every minute)
CREATE OR REPLACE FUNCTION schedule_stats_update() RETURNS VOID AS $$
BEGIN
    PERFORM update_performance_stats();
END;

-- Create trigger to schedule cleanup (every hour)
CREATE OR REPLACE FUNCTION schedule_cleanup() RETURNS VOID AS $$
BEGIN
    PERFORM schedule_cleanup();
END;
