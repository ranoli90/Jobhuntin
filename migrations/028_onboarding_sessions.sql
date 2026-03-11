-- Migration: Onboarding Sessions Persistence
-- Date: 2026-03-09
-- Purpose: Persist onboarding sessions to database for security and authorization

-- HIGH: Create onboarding_sessions table for session persistence
CREATE TABLE IF NOT EXISTS public.onboarding_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    flow_type VARCHAR(50) NOT NULL DEFAULT 'professional',
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    current_step INTEGER NOT NULL DEFAULT 0,
    completion_percentage FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT fk_onboarding_sessions_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_onboarding_sessions_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_user_id ON public.onboarding_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_tenant_id ON public.onboarding_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_session_id ON public.onboarding_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_created_at ON public.onboarding_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_onboarding_sessions_expires_at ON public.onboarding_sessions(expires_at) WHERE expires_at IS NOT NULL;

-- Add comment
COMMENT ON TABLE public.onboarding_sessions IS 'Stores onboarding session state for user authorization and session management';
