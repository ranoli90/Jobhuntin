-- +migrate Up
-- PRIV-006: gdpr_requests table for request_id verification and status lookup.
-- Enables GET /gdpr/status/{request_id} with ownership verification (prevents IDOR).

CREATE TABLE IF NOT EXISTS public.gdpr_requests (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('export', 'delete')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_gdpr_requests_user_id ON public.gdpr_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_gdpr_requests_created_at ON public.gdpr_requests(created_at);

-- +migrate Down
DROP TABLE IF EXISTS public.gdpr_requests;
