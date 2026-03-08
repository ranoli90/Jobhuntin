-- Interview Sessions Table Migration
-- Add support for AI-powered interview preparation sessions

CREATE TABLE IF NOT EXISTS public.interview_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    company VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    interview_type VARCHAR(50) NOT NULL DEFAULT 'general',
    difficulty VARCHAR(20) NOT NULL DEFAULT 'medium',
    questions JSONB NOT NULL DEFAULT '[]',
    responses JSONB NOT NULL DEFAULT '[]',
    feedback JSONB NOT NULL DEFAULT '[]',
    current_question_index INTEGER NOT NULL DEFAULT 0,
    total_score DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_id ON public.interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_job_id ON public.interview_sessions(job_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON public.interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_started_at ON public.interview_sessions(started_at);

-- Add RLS policies for security
ALTER TABLE public.interview_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own interview sessions
CREATE POLICY "Users can view own interview sessions" ON public.interview_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own interview sessions" ON public.interview_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own interview sessions" ON public.interview_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own interview sessions" ON public.interview_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Add trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER handle_interview_sessions_updated_at
    BEFORE UPDATE ON public.interview_sessions
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Add comments for documentation
COMMENT ON TABLE public.interview_sessions IS 'AI-powered interview preparation sessions';
COMMENT ON COLUMN public.interview_sessions.session_id IS 'Unique identifier for the interview session';
COMMENT ON COLUMN public.interview_sessions.user_id IS 'User who owns this session';
COMMENT ON COLUMN public.interview_sessions.job_id IS 'Optional job this session is preparing for';
COMMENT ON COLUMN public.interview_sessions.company IS 'Company name for context';
COMMENT ON COLUMN public.interview_sessions.job_title IS 'Job title for context';
COMMENT ON COLUMN public.interview_sessions.interview_type IS 'Type of interview (general, technical, behavioral, etc.)';
COMMENT ON COLUMN public.interview_sessions.difficulty IS 'Difficulty level (easy, medium, hard)';
COMMENT ON COLUMN public.interview_sessions.questions IS 'JSON array of interview questions';
COMMENT ON COLUMN public.interview_sessions.responses IS 'JSON array of user responses';
COMMENT ON COLUMN public.interview_sessions.feedback IS 'JSON array of AI feedback';
COMMENT ON COLUMN public.interview_sessions.current_question_index IS 'Current question being answered';
COMMENT ON COLUMN public.interview_sessions.total_score IS 'Overall performance score (0-100)';
COMMENT ON COLUMN public.interview_sessions.status IS 'Session status (in_progress, completed, abandoned)';
COMMENT ON COLUMN public.interview_sessions.started_at IS 'When the session started';
COMMENT ON COLUMN public.interview_sessions.completed_at IS 'When the session was completed';
COMMENT ON COLUMN public.interview_sessions.created_at IS 'When the record was created';
COMMENT ON COLUMN public.interview_sessions.updated_at IS 'When the record was last updated';
