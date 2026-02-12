-- Match Feedback Table
-- Stores user feedback (thumbs up/down) on match results for ML improvement

CREATE TABLE IF NOT EXISTS public.match_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
    
    -- Feedback data
    rating SMALLINT NOT NULL CHECK (rating IN (1, -1)),  -- 1 = thumbs up, -1 = thumbs down
    match_score FLOAT NOT NULL,  -- The original match score (0-1)
    semantic_similarity FLOAT,
    skill_match_ratio FLOAT,
    
    -- Optional detailed feedback
    feedback_text TEXT,
    feedback_tags TEXT[],  -- e.g., ['good_skills_match', 'bad_location', 'salary_too_low']
    
    -- Context
    match_type VARCHAR(50) DEFAULT 'semantic',  -- 'semantic', 'llm', 'hybrid'
    job_title TEXT,
    company TEXT,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    
    -- Ensure one feedback per user per job
    UNIQUE(user_id, job_id)
);

-- Index for querying feedback by user
CREATE INDEX IF NOT EXISTS idx_match_feedback_user_id ON public.match_feedback(user_id);

-- Index for aggregating feedback by job
CREATE INDEX IF NOT EXISTS idx_match_feedback_job_id ON public.match_feedback(job_id);

-- Index for tenant-level analytics
CREATE INDEX IF NOT EXISTS idx_match_feedback_tenant_id ON public.match_feedback(tenant_id);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_match_feedback_created_at ON public.match_feedback(created_at DESC);

-- View for match feedback analytics
CREATE OR REPLACE VIEW public.match_feedback_stats AS
SELECT 
    job_id,
    COUNT(*) AS total_feedback,
    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS thumbs_up,
    SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) AS thumbs_down,
    ROUND(AVG(match_score)::numeric, 3) AS avg_match_score,
    ROUND(AVG(CASE WHEN rating = 1 THEN match_score ELSE NULL END)::numeric, 3) AS avg_score_positive,
    ROUND(AVG(CASE WHEN rating = -1 THEN match_score ELSE NULL END)::numeric, 3) AS avg_score_negative,
    ARRAY_AGG(DISTINCT unnest) FILTER (WHERE unnest IS NOT NULL) AS common_tags
FROM public.match_feedback
CROSS JOIN LATERAL unnest(feedback_tags)
GROUP BY job_id;

-- Function to compute feedback-adjusted match score
CREATE OR REPLACE FUNCTION public.compute_adjusted_match_score(
    p_job_id UUID,
    p_base_score FLOAT
) RETURNS FLOAT AS $$
DECLARE
    v_positive_ratio FLOAT;
    v_feedback_count INT;
BEGIN
    SELECT 
        COALESCE(SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0), 0.5),
        COUNT(*)
    INTO v_positive_ratio, v_feedback_count
    FROM public.match_feedback
    WHERE job_id = p_job_id;
    
    -- If no feedback, return base score
    IF v_feedback_count = 0 THEN
        RETURN p_base_score;
    END IF;
    
    -- Adjust score based on feedback (weight increases with more feedback)
    -- Max adjustment is 20% of base score, weighted by feedback count (capped at 10 samples)
    DECLARE
        v_weight FLOAT := LEAST(v_feedback_count::FLOAT / 10.0, 1.0);
        v_adjustment FLOAT := (v_positive_ratio - 0.5) * 0.4 * p_base_score * v_weight;
    BEGIN
        RETURN GREATEST(0.0, LEAST(1.0, p_base_score + v_adjustment));
    END;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON public.match_feedback TO authenticated;
GRANT SELECT ON public.match_feedback_stats TO authenticated;
GRANT EXECUTE ON FUNCTION public.compute_adjusted_match_score TO authenticated;

COMMENT ON TABLE public.match_feedback IS 'User feedback on job match quality for ML improvement';
COMMENT ON COLUMN public.match_feedback.rating IS '1 = thumbs up (good match), -1 = thumbs down (bad match)';
COMMENT ON COLUMN public.match_feedback.feedback_tags IS 'Array of categorical feedback tags for analysis';
