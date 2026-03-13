-- Migration 039: User Consent Management Tables
-- Tables for GDPR-compliant consent tracking
-- Supports both authenticated users and anonymous visitors

-- +migrate Up

-- Table to store user consent preferences
CREATE TABLE IF NOT EXISTS user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    anonymous_id VARCHAR(255), -- Browser fingerprint for anonymous users
    consent_type VARCHAR(50) NOT NULL, -- 'marketing', 'analytics', 'cookies', 'functional', 'essential'
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    version VARCHAR(20) DEFAULT '2.0', -- Consent version for policy updates
    source VARCHAR(50) DEFAULT 'web', -- 'web', 'api', 'mobile', 'admin'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one consent record per user/type combination
    CONSTRAINT unique_user_consent UNIQUE (user_id, consent_type),
    CONSTRAINT unique_anonymous_consent UNIQUE (anonymous_id, consent_type)
);

-- Index for looking up consents by user
CREATE INDEX IF NOT EXISTS idx_user_consents_user_id 
ON user_consents(user_id);

-- Index for looking up consents by anonymous ID
CREATE INDEX IF NOT EXISTS idx_user_consents_anonymous_id 
ON user_consents(anonymous_id);

-- Index for looking up consents by type
CREATE INDEX IF NOT EXISTS idx_user_consents_type 
ON user_consents(consent_type);

-- Index for audit queries by timestamp
CREATE INDEX IF NOT EXISTS idx_user_consents_granted_at 
ON user_consents(granted_at DESC);

-- Index for audit queries by IP
CREATE INDEX IF NOT EXISTS idx_user_consents_ip 
ON user_consents(ip_address);

-- Table to track consent history/changes for audit trail
CREATE TABLE IF NOT EXISTS consent_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    anonymous_id VARCHAR(255),
    consent_type VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL, -- 'grant', 'revoke', 'update'
    previous_value BOOLEAN,
    new_value BOOLEAN,
    ip_address INET,
    user_agent TEXT,
    reason VARCHAR(255), -- Optional reason for consent change
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for consent audit by user
CREATE INDEX IF NOT EXISTS idx_consent_audit_user_id 
ON consent_audit_log(user_id);

-- Index for consent audit by anonymous ID
CREATE INDEX IF NOT EXISTS idx_consent_audit_anonymous_id 
ON consent_audit_log(anonymous_id);

-- Index for consent audit by timestamp
CREATE INDEX IF NOT idx_consent_audit_created_at 
ON consent_audit_log(created_at DESC);

-- Table to store consent policy versions
CREATE TABLE IF NOT EXISTS consent_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(20) NOT NULL UNIQUE,
    policy_text TEXT NOT NULL,
    effective_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for looking up active consent policy
CREATE INDEX IF NOT EXISTS idx_consent_policies_active 
ON consent_policies(is_active) WHERE is_active = TRUE;

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_consent_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamp on consent changes
CREATE TRIGGER trigger_update_user_consent_timestamp
    BEFORE UPDATE ON user_consents
    FOR EACH ROW
    EXECUTE FUNCTION update_user_consent_timestamp();

-- +migrate Down

DROP TRIGGER IF EXISTS trigger_update_user_consent_timestamp ON user_consents;
DROP FUNCTION IF EXISTS update_user_consent_timestamp();
DROP TABLE IF EXISTS consent_audit_log;
DROP TABLE IF EXISTS consent_policies;
DROP TABLE IF EXISTS user_consents;
