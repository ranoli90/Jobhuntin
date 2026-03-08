-- Migration: Add saved_jobs table for job bookmarking
-- Description: Allows users to save/bookmark jobs without applying
-- Created: 2026-03-08

-- Create saved_jobs table
CREATE TABLE IF NOT EXISTS public.saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique user+job combination
    UNIQUE(user_id, job_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_id ON public.saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_tenant_id ON public.saved_jobs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_created_at ON public.saved_jobs(created_at DESC);

-- Enable Row Level Security
ALTER TABLE public.saved_jobs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see their own saved jobs
CREATE POLICY "Users can view their own saved jobs" ON public.saved_jobs
    FOR SELECT USING (user_id = auth.uid());

-- Users can only insert their own saved jobs
CREATE POLICY "Users can insert their own saved jobs" ON public.saved_jobs
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Users can only delete their own saved jobs
CREATE POLICY "Users can delete their own saved jobs" ON public.saved_jobs
    FOR DELETE USING (user_id = auth.uid());

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_saved_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_saved_jobs_updated_at
    BEFORE UPDATE ON public.saved_jobs
    FOR EACH ROW
    EXECUTE FUNCTION public.update_saved_jobs_updated_at();

-- Add comments
COMMENT ON TABLE public.saved_jobs IS 'Table for storing user bookmarked/saved jobs';
COMMENT ON COLUMN public.saved_jobs.id IS 'Primary key for saved job record';
COMMENT ON COLUMN public.saved_jobs.user_id IS 'Reference to user who saved the job';
COMMENT ON COLUMN public.saved_jobs.job_id IS 'Reference to the saved job';
COMMENT ON COLUMN public.saved_jobs.tenant_id IS 'Reference to tenant for multi-tenancy';
COMMENT ON COLUMN public.saved_jobs.created_at IS 'When the job was saved';
COMMENT ON COLUMN public.saved_jobs.updated_at IS 'When the saved job record was last updated';
