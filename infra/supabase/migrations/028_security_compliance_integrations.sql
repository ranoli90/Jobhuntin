-- +migrate Up
-- Migration 028: Security, Compliance, and Integration Tables
-- Creates tables for MFA, CCPA, Session Management, IP Allowlisting,
-- Password History, Data Residency, and Third-Party Integrations

-- ============================================================================
-- SECURITY TABLES
-- ============================================================================

-- MFA Enrollments (TOTP and WebAuthn)
CREATE TABLE IF NOT EXISTS public.user_mfa_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    mfa_type TEXT NOT NULL CHECK (mfa_type IN ('totp', 'webauthn')),
    is_verified BOOLEAN NOT NULL DEFAULT false,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    config JSONB NOT NULL DEFAULT '{}',
    verified_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mfa_enrollments_user_id ON public.user_mfa_enrollments(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mfa_enrollments_user_type ON public.user_mfa_enrollments(user_id, mfa_type) WHERE is_primary = true;

-- MFA Recovery Codes
CREATE TABLE IF NOT EXISTS public.mfa_recovery_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    used BOOLEAN NOT NULL DEFAULT false,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mfa_recovery_codes_user_id ON public.mfa_recovery_codes(user_id);

-- User Sessions
CREATE TABLE IF NOT EXISTS public.user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
    device_fingerprint TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT false,
    revoked_at TIMESTAMPTZ,
    revoked_reason TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON public.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON public.user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_fp ON public.user_sessions(device_fingerprint);

-- IP Allowlist
CREATE TABLE IF NOT EXISTS public.tenant_ip_allowlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    cidr TEXT NOT NULL,
    description TEXT,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT true,
    removed_at TIMESTAMPTZ,
    removed_by UUID REFERENCES public.users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ip_allowlist_tenant_id ON public.tenant_ip_allowlist(tenant_id);

-- Temporary Access Codes for IP Allowlist bypass
CREATE TABLE IF NOT EXISTS public.tenant_temp_access_codes (
    code TEXT PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    ip_address TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN NOT NULL DEFAULT false,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_temp_codes_tenant_id ON public.tenant_temp_access_codes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_temp_codes_expires_at ON public.tenant_temp_access_codes(expires_at);

-- Password History
CREATE TABLE IF NOT EXISTS public.password_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON public.password_history(user_id);

-- ============================================================================
-- COMPLIANCE TABLES
-- ============================================================================

-- CCPA Privacy Requests
CREATE TABLE IF NOT EXISTS public.ccpa_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_type TEXT NOT NULL CHECK (request_type IN ('know', 'delete', 'opt_out', 'correct', 'appeal', 'portability')),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    email TEXT NOT NULL,
    phone TEXT,
    verification_code TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'processing', 'completed', 'denied', 'expired')),
    details JSONB DEFAULT '{}',
    response JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ccpa_requests_email ON public.ccpa_requests(email);
CREATE INDEX IF NOT EXISTS idx_ccpa_requests_status ON public.ccpa_requests(status);
CREATE INDEX IF NOT EXISTS idx_ccpa_requests_user_id ON public.ccpa_requests(user_id);

-- User Privacy Settings (Do Not Sell, etc.)
CREATE TABLE IF NOT EXISTS public.user_privacy_settings (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    do_not_sell BOOLEAN NOT NULL DEFAULT false,
    opted_out_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Data Residency Configuration
CREATE TABLE IF NOT EXISTS public.tenant_data_residency (
    tenant_id UUID PRIMARY KEY REFERENCES public.tenants(id) ON DELETE CASCADE,
    primary_region TEXT NOT NULL,
    backup_region TEXT,
    enforced_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    data_types TEXT[] NOT NULL DEFAULT '{}',
    cross_region_transfer_allowed BOOLEAN NOT NULL DEFAULT false,
    last_audit_at TIMESTAMPTZ
);

-- Cross-Region Data Transfers Log
CREATE TABLE IF NOT EXISTS public.cross_region_transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    data_type TEXT NOT NULL,
    source_region TEXT NOT NULL,
    destination_region TEXT NOT NULL,
    bytes_transferred BIGINT NOT NULL DEFAULT 0,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cross_region_tenant_id ON public.cross_region_transfers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cross_region_created_at ON public.cross_region_transfers(created_at);

-- Audit Log Archive
CREATE TABLE IF NOT EXISTS public.audit_log_archive (
    id UUID PRIMARY KEY,
    tenant_id UUID,
    user_id UUID,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    resource_id TEXT,
    details JSONB DEFAULT '{}',
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_archive_created_at ON public.audit_log_archive(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_archive_tenant_id ON public.audit_log_archive(tenant_id);

-- ============================================================================
-- INTEGRATION TABLES
-- ============================================================================

-- API Keys with rotation support
ALTER TABLE public.api_keys ADD COLUMN IF NOT EXISTS rotated_from UUID REFERENCES public.api_keys(id) ON DELETE SET NULL;
ALTER TABLE public.api_keys ADD COLUMN IF NOT EXISTS rotated_to UUID REFERENCES public.api_keys(id) ON DELETE SET NULL;
ALTER TABLE public.api_keys ADD COLUMN IF NOT EXISTS rotated_at TIMESTAMPTZ;
ALTER TABLE public.api_keys ADD COLUMN IF NOT EXISTS grace_expires_at TIMESTAMPTZ;
ALTER TABLE public.api_keys ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;
ALTER TABLE public.api_keys ADD COLUMN IF NOT EXISTS revoked_reason TEXT;

-- Slack Integrations
CREATE TABLE IF NOT EXISTS public.slack_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID UNIQUE NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    slack_team_id TEXT NOT NULL,
    access_token TEXT NOT NULL,
    bot_user_id TEXT,
    default_channel TEXT,
    enabled_notifications TEXT[] DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_slack_tenant_id ON public.slack_integrations(tenant_id);

-- Zapier Webhooks
CREATE TABLE IF NOT EXISTS public.zapier_hooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hook_id TEXT UNIQUE NOT NULL,
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    webhook_url TEXT NOT NULL,
    event_types TEXT[] NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_triggered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_zapier_hooks_tenant_id ON public.zapier_hooks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_zapier_hooks_hook_id ON public.zapier_hooks(hook_id);

-- Notion Integrations
CREATE TABLE IF NOT EXISTS public.notion_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID UNIQUE NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    workspace_id TEXT,
    database_id TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Notion Export Records
CREATE TABLE IF NOT EXISTS public.notion_exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    application_id UUID UNIQUE REFERENCES public.applications(id) ON DELETE CASCADE,
    notion_page_id TEXT NOT NULL,
    exported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notion_tenant_id ON public.notion_integrations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notion_exports_application_id ON public.notion_exports(application_id);

-- Google Drive Integrations
CREATE TABLE IF NOT EXISTS public.google_drive_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    folder_id TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, user_id)
);

-- Google Drive Backup Records
CREATE TABLE IF NOT EXISTS public.google_drive_backups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    file_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    backup_type TEXT NOT NULL,
    backed_up_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, user_id, backup_type)
);

CREATE INDEX IF NOT EXISTS idx_google_drive_tenant_user ON public.google_drive_integrations(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_google_drive_backups_user ON public.google_drive_backups(user_id);

-- Calendar Integrations
CREATE TABLE IF NOT EXISTS public.calendar_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('google', 'outlook', 'apple', 'caldav')),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_calendar_tenant_user ON public.calendar_integrations(tenant_id, user_id);

-- Interview Sessions
CREATE TABLE IF NOT EXISTS public.interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    company TEXT NOT NULL,
    job_title TEXT NOT NULL,
    interview_type TEXT NOT NULL DEFAULT 'general',
    difficulty TEXT NOT NULL DEFAULT 'medium',
    questions JSONB NOT NULL DEFAULT '[]',
    responses JSONB NOT NULL DEFAULT '[]',
    feedback JSONB NOT NULL DEFAULT '[]',
    current_question_index INTEGER NOT NULL DEFAULT 0,
    total_score FLOAT NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'in_progress',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_id ON public.interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON public.interview_sessions(status);

-- Company Cache
CREATE TABLE IF NOT EXISTS public.company_cache (
    name_lower TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    cached_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_company_cache_cached_at ON public.company_cache(cached_at);

-- ============================================================================
-- EXTEND EXISTING TABLES
-- ============================================================================

-- Add IP allowlist flag to tenants
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS ip_allowlist_enabled BOOLEAN DEFAULT false;

-- Add password change tracking to users
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS password_expires_at TIMESTAMPTZ;

-- +migrate Down
-- This migration is additive; rollback is complex and typically not needed in production
-- However, for completeness:

DROP TABLE IF EXISTS public.interview_sessions;
DROP TABLE IF EXISTS public.calendar_integrations;
DROP TABLE IF EXISTS public.company_cache;
DROP TABLE IF EXISTS public.google_drive_backups;
DROP TABLE IF EXISTS public.google_drive_integrations;
DROP TABLE IF EXISTS public.notion_exports;
DROP TABLE IF EXISTS public.notion_integrations;
DROP TABLE IF EXISTS public.zapier_hooks;
DROP TABLE IF EXISTS public.slack_integrations;
DROP TABLE IF EXISTS public.cross_region_transfers;
DROP TABLE IF EXISTS public.tenant_data_residency;
DROP TABLE IF EXISTS public.user_privacy_settings;
DROP TABLE IF EXISTS public.ccpa_requests;
DROP TABLE IF EXISTS public.password_history;
DROP TABLE IF EXISTS public.tenant_temp_access_codes;
DROP TABLE IF EXISTS public.tenant_ip_allowlist;
DROP TABLE IF EXISTS public.user_sessions;
DROP TABLE IF EXISTS public.mfa_recovery_codes;
DROP TABLE IF EXISTS public.user_mfa_enrollments;
DROP TABLE IF EXISTS public.audit_log_archive;

ALTER TABLE public.tenants DROP COLUMN IF EXISTS ip_allowlist_enabled;
ALTER TABLE public.users DROP COLUMN IF EXISTS password_changed_at;
ALTER TABLE public.users DROP COLUMN IF EXISTS password_expires_at;
