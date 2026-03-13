-- Migration 038: Data Retention Tables
-- Tables for tracking data retention policies and deletion audit logs
-- Required for GDPR compliance and storage optimization

-- +migrate Up

-- Table to track retention policies configuration
CREATE TABLE IF NOT EXISTS retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_type VARCHAR(100) NOT NULL UNIQUE,
    retention_days INTEGER NOT NULL DEFAULT 90,
    description TEXT,
    legal_basis VARCHAR(255),
    allow_soft_delete BOOLEAN DEFAULT TRUE,
    batch_size INTEGER DEFAULT 1000,
    requires_archive BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for looking up policies by data type
CREATE INDEX IF NOT EXISTS idx_retention_policies_data_type 
ON retention_policies(data_type);

-- Table to track all deletion operations for audit purposes
CREATE TABLE IF NOT EXISTS data_retention_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(100) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    deleted_count INTEGER NOT NULL DEFAULT 0,
    batch_number INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for querying logs by job
CREATE INDEX IF NOT EXISTS idx_data_retention_logs_job_id 
ON data_retention_logs(job_id);

-- Index for querying logs by data type
CREATE INDEX IF NOT EXISTS idx_data_retention_logs_data_type 
ON data_retention_logs(data_type);

-- Index for querying logs by date
CREATE INDEX IF NOT EXISTS idx_data_retention_logs_created_at 
ON data_retention_logs(created_at DESC);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_retention_policy_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update timestamp
DROP TRIGGER IF EXISTS update_retention_policy_timestamp_trigger 
ON retention_policies;
CREATE TRIGGER update_retention_policy_timestamp_trigger
    BEFORE UPDATE ON retention_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_retention_policy_timestamp();

-- Insert default retention policies
INSERT INTO retention_policies (data_type, retention_days, description, legal_basis, allow_soft_delete, batch_size, requires_archive)
VALUES 
    ('session_logs', 90, 'Session logs for security auditing', 'Legitimate interest - Security monitoring', TRUE, 5000, FALSE),
    ('analytics_events', 365, 'Analytics events for product improvement', 'Consent - Analytics tracking', TRUE, 10000, FALSE),
    ('application_data', 30, 'Job application data after account deletion', 'GDPR Art. 17 - Right to erasure', TRUE, 1000, TRUE),
    ('uploaded_resumes', 0, 'Uploaded resumes - retained while account active', 'Contract performance', TRUE, 500, TRUE),
    ('api_logs', 90, 'API request logs for debugging and security', 'Legitimate interest - API monitoring', TRUE, 10000, FALSE)
ON CONFLICT (data_type) DO NOTHING;

-- +migrate Down

DROP TRIGGER IF EXISTS update_retention_policy_timestamp_trigger 
ON retention_policies;
DROP FUNCTION IF EXISTS update_retention_policy_timestamp();

DROP TABLE IF EXISTS data_retention_logs;
DROP TABLE IF EXISTS retention_policies;
