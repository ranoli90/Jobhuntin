-- Migration: Match Scores Pre-computation Table
-- Date: 2026-03-09
-- Purpose: Store pre-computed match scores for performance optimization

-- LOW: Create match_scores table for storing pre-computed scores
CREATE TABLE IF NOT EXISTS public.match_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_id UUID NOT NULL,
    score FLOAT NOT NULL CHECK (score >= 0 AND score <= 100),
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    
    CONSTRAINT fk_match_scores_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_match_scores_job FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE,
    CONSTRAINT uq_match_scores_user_job UNIQUE (user_id, job_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_match_scores_user_id ON public.match_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_match_scores_job_id ON public.match_scores(job_id);
CREATE INDEX IF NOT EXISTS idx_match_scores_score ON public.match_scores(score DESC);
CREATE INDEX IF NOT EXISTS idx_match_scores_computed_at ON public.match_scores(computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_match_scores_user_score ON public.match_scores(user_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_match_scores_expires_at ON public.match_scores(expires_at) WHERE expires_at IS NOT NULL;

-- Add comment
COMMENT ON TABLE public.match_scores IS 'Pre-computed match scores for users and jobs to improve query performance';
