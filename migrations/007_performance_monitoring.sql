-- Migration 007: Performance Monitoring Tables for Phase 15.1
-- Tables for performance metrics, alerts, thresholds, and optimization data

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_type VARCHAR(50) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance alerts table
CREATE TABLE IF NOT EXISTS performance_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    current_value DOUBLE PRECISION NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance thresholds table
CREATE TABLE IF NOT EXISTS performance_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    warning_threshold DOUBLE PRECISION NOT NULL,
    critical_threshold DOUBLE PRECISION NOT NULL,
    comparison_operator VARCHAR(10) NOT NULL DEFAULT 'gt',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, metric_name)
);

-- Query analyses table
CREATE TABLE IF NOT EXISTS query_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    original_query TEXT NOT NULL,
    normalized_query TEXT NOT NULL,
    execution_plan JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    identified_issues JSONB DEFAULT '[]',
    optimization_opportunities JSONB DEFAULT '[]',
    complexity_score DOUBLE PRECISION DEFAULT 0.0,
    estimated_cost DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query optimizations table
CREATE TABLE IF NOT EXISTS query_optimizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    query_id UUID REFERENCES query_analyses(id),
    optimization_type VARCHAR(50) NOT NULL,
    original_query TEXT NOT NULL,
    optimized_query TEXT NOT NULL,
    description TEXT NOT NULL,
    performance_improvement DOUBLE PRECISION DEFAULT 0.0,
    implementation_complexity VARCHAR(20) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    reasoning TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index analyses table
CREATE TABLE IF NOT EXISTS index_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    table_name VARCHAR(100) NOT NULL,
    total_indexes INTEGER DEFAULT 0,
    unused_indexes JSONB DEFAULT '[]',
    underutilized_indexes JSONB DEFAULT '[]',
    missing_indexes JSONB DEFAULT '[]',
    duplicate_indexes JSONB DEFAULT '[]',
    oversized_indexes JSONB DEFAULT '[]',
    fragmentation_score DOUBLE PRECISION DEFAULT 0.0,
    optimization_potential DOUBLE PRECISION DEFAULT 0.0,
    recommendations JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index recommendations table
CREATE TABLE IF NOT EXISTS index_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    recommendation_type VARCHAR(50) NOT NULL,
    index_name VARCHAR(100),
    table_name VARCHAR(100) NOT NULL,
    column_names TEXT[] DEFAULT '{}',
    index_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    impact_score DOUBLE PRECISION DEFAULT 0.0,
    implementation_cost VARCHAR(20) NOT NULL,
    reasoning TEXT NOT NULL,
    sql_statement TEXT,
    estimated_benefit TEXT,
    risks TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Database performance metrics table
CREATE TABLE IF NOT EXISTS database_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    metric_unit VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Database optimizations table
CREATE TABLE IF NOT EXISTS database_optimizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    optimization_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    description TEXT NOT NULL,
    sql_statement TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL,
    estimated_benefit TEXT,
    risks TEXT[] DEFAULT '{}',
    executed_at TIMESTAMP WITH TIME ZONE,
    execution_result JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_performance_metrics_tenant_timestamp ON performance_metrics(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_timestamp ON performance_metrics(name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type_category ON performance_metrics(metric_type, metric_category);

CREATE INDEX IF NOT EXISTS idx_performance_alerts_tenant_timestamp ON performance_alerts(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_severity_timestamp ON performance_alerts(severity, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_resolved_timestamp ON performance_alerts(resolved, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_performance_thresholds_tenant_name ON performance_thresholds(tenant_id, metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_thresholds_enabled ON performance_thresholds(enabled);

CREATE INDEX IF NOT EXISTS idx_query_analyses_tenant_timestamp ON query_analyses(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_query_analyses_complexity ON query_analyses(complexity_score DESC);

CREATE INDEX IF NOT EXISTS idx_query_optimizations_tenant_timestamp ON query_optimizations(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_query_optimizations_type_priority ON query_optimizations(optimization_type, priority);

CREATE INDEX IF NOT EXISTS idx_index_analyses_tenant_timestamp ON index_analyses(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_index_analyses_table_name ON index_analyses(table_name);

CREATE INDEX IF NOT EXISTS idx_index_recommendations_tenant_timestamp ON index_recommendations(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_index_recommendations_type_priority ON index_recommendations(recommendation_type, priority);

CREATE INDEX IF NOT EXISTS idx_database_performance_metrics_tenant_timestamp ON database_performance_metrics(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_database_performance_metrics_name_timestamp ON database_performance_metrics(metric_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_database_optimizations_tenant_timestamp ON database_optimizations(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_database_optimizations_status_priority ON database_optimizations(status, priority);

-- Insert default performance thresholds
INSERT INTO performance_thresholds (id, tenant_id, metric_name, metric_type, warning_threshold, critical_threshold, comparison_operator, enabled)
SELECT 
    gen_random_uuid(),
    t.id,
    unnest(ARRAY['cpu_percent', 'memory_percent', 'disk_percent', 'connection_pool_utilization', 'query_response_time']),
    unnest(ARRAY['cpu', 'memory', 'disk', 'database', 'database']),
    unnest(ARRAY[70.0, 80.0, 80.0, 80.0, 1000.0]),
    unnest(ARRAY[90.0, 95.0, 95.0, 95.0, 5000.0]),
    'gt',
    true
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM performance_thresholds pt 
    WHERE pt.tenant_id = t.id 
    AND pt.metric_name IN ('cpu_percent', 'memory_percent', 'disk_percent', 'connection_pool_utilization', 'query_response_time')
)
ON CONFLICT (tenant_id, metric_name) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW performance_metrics_summary AS
SELECT 
    tenant_id,
    metric_type,
    metric_category,
    name,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(*) as count,
    MAX(timestamp) as last_timestamp
FROM performance_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY tenant_id, metric_type, metric_category, name;

CREATE OR REPLACE VIEW performance_alerts_summary AS
SELECT 
    tenant_id,
    severity,
    COUNT(*) as alert_count,
    COUNT(*) FILTER (WHERE resolved = FALSE) as unresolved_count,
    MAX(timestamp) as last_alert_timestamp
FROM performance_alerts
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY tenant_id, severity;

CREATE OR REPLACE VIEW database_optimization_summary AS
SELECT 
    tenant_id,
    optimization_type,
    status,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    MAX(created_at) as last_created_at
FROM database_optimizations
GROUP BY tenant_id, optimization_type, status;

-- Comments
COMMENT ON TABLE performance_metrics IS 'Stores performance monitoring metrics collected from various sources';
COMMENT ON TABLE performance_alerts IS 'Stores performance alerts generated when thresholds are exceeded';
COMMENT ON TABLE performance_thresholds IS 'Stores threshold configurations for performance metrics';
COMMENT ON TABLE query_analyses IS 'Stores SQL query analysis results and optimization opportunities';
COMMENT ON TABLE query_optimizations IS 'Stores generated query optimizations with implementation details';
COMMENT ON TABLE index_analyses IS 'Stores index analysis results for database tables';
COMMENT ON TABLE index_recommendations IS 'Stores index recommendations for performance optimization';
COMMENT ON TABLE database_performance_metrics IS 'Stores database-specific performance metrics';
COMMENT ON TABLE database_optimizations IS 'Stores database optimization recommendations and execution results';
