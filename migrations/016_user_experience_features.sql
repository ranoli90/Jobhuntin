-- Phase 14.1 User Experience Database Migration
-- Tables for pipeline view, export, follow-up reminders, answer memory, multi-resume, and application notes

-- Resume versions table for multi-resume support
CREATE TABLE IF NOT EXISTS resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    resume_type VARCHAR(50) NOT NULL CHECK (resume_type IN ('general', 'technical', 'management', 'executive', 'creative', 'academic', 'entry_level', 'career_change')),
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_format VARCHAR(10) NOT NULL CHECK (file_format IN ('pdf', 'docx', 'doc', 'txt')),
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    target_industries TEXT[] DEFAULT '{}',
    target_roles TEXT[] DEFAULT '{}',
    skills_emphasized TEXT[] DEFAULT '{}',
    ats_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Follow-up reminders table
CREATE TABLE IF NOT EXISTS follow_up_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled', 'completed')),
    sent_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interview questions table for answer memory
CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('behavioral', 'technical', 'situational', 'leadership', 'problem_solving', 'cultural_fit', 'salary_negotiation', 'company_specific', 'role_specific', 'general')),
    difficulty VARCHAR(10) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard', 'expert')),
    context TEXT,
    tags TEXT[] DEFAULT '{}',
    company_specific BOOLEAN DEFAULT false,
    role_specific BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Answer attempts table
CREATE TABLE IF NOT EXISTS answer_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES interview_questions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    feedback TEXT,
    ai_score DECIMAL(3,2) CHECK (ai_score >= 0 AND ai_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed BOOLEAN DEFAULT false,
    notes TEXT
);

-- Answer memory table
CREATE TABLE IF NOT EXISTS answer_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES interview_questions(id) ON DELETE CASCADE,
    memorized_answer TEXT NOT NULL,
    key_points TEXT[] DEFAULT '{}',
    examples TEXT[] DEFAULT '{}',
    follow_up_questions TEXT[] DEFAULT '{}',
    last_reviewed TIMESTAMP WITH TIME ZONE,
    review_count INTEGER DEFAULT 0,
    mastery_level DECIMAL(3,2) DEFAULT 0.0 CHECK (mastery_level >= 0 AND mastery_level <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Application notes table
CREATE TABLE IF NOT EXISTS application_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general' CHECK (category IN ('general', 'contact_info', 'interview_prep', 'follow_up', 'feedback', 'questions', 'research', 'salary_info', 'next_steps', 'personal_notes')),
    tags TEXT[] DEFAULT '{}',
    is_private BOOLEAN DEFAULT true,
    is_pinned BOOLEAN DEFAULT false,
    reminder_date TIMESTAMP WITH TIME ZONE,
    author_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add resume_id column to applications table
ALTER TABLE applications ADD COLUMN IF NOT EXISTS resume_id UUID REFERENCES resume_versions(id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_resume_versions_user_tenant ON resume_versions(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_resume_versions_primary ON resume_versions(user_id, tenant_id) WHERE is_primary = true;
CREATE INDEX IF NOT EXISTS idx_resume_versions_active ON resume_versions(user_id, tenant_id) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_application ON follow_up_reminders(application_id);
CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_user_tenant ON follow_up_reminders(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_status_scheduled ON follow_up_reminders(status, scheduled_for);

CREATE INDEX IF NOT EXISTS idx_interview_questions_category ON interview_questions(category);
CREATE INDEX IF NOT EXISTS idx_interview_questions_difficulty ON interview_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_interview_questions_usage ON interview_questions(usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_answer_attempts_question_user ON answer_attempts(question_id, user_id);
CREATE INDEX IF NOT EXISTS idx_answer_attempts_user_tenant ON answer_attempts(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_answer_attempts_created ON answer_attempts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_answer_memory_user_question ON answer_memory(user_id, question_id);
CREATE INDEX IF NOT EXISTS idx_answer_memory_mastery ON answer_memory(user_id, mastery_level DESC);

CREATE INDEX IF NOT EXISTS idx_application_notes_application ON application_notes(application_id);
CREATE INDEX IF NOT EXISTS idx_application_notes_user_tenant ON application_notes(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_application_notes_category ON application_notes(category);
CREATE INDEX IF NOT EXISTS idx_application_notes_pinned ON application_notes(is_pinned DESC) WHERE is_pinned = true;
CREATE INDEX IF NOT EXISTS idx_application_notes_reminder ON application_notes(reminder_date) WHERE reminder_date IS NOT NULL;

-- Full-text search indexes for notes and questions
CREATE INDEX IF NOT EXISTS idx_application_notes_search ON application_notes USING gin(to_tsvector('english', title || ' ' || content));
CREATE INDEX IF NOT EXISTS idx_interview_questions_search ON interview_questions USING gin(to_tsvector('english', question));

-- Enable RLS (Row Level Security)
ALTER TABLE resume_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE follow_up_reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE application_notes ENABLE ROW LEVEL SECURITY;

-- RLS Policies for resume_versions
CREATE POLICY "Users can view their own resume versions" ON resume_versions
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own resume versions" ON resume_versions
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own resume versions" ON resume_versions
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own resume versions" ON resume_versions
    FOR DELETE USING (user_id = current_user_id());

-- RLS Policies for follow_up_reminders
CREATE POLICY "Users can view their own follow-up reminders" ON follow_up_reminders
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own follow-up reminders" ON follow_up_reminders
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own follow-up reminders" ON follow_up_reminders
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own follow-up reminders" ON follow_up_reminders
    FOR DELETE USING (user_id = current_user_id());

-- RLS Policies for answer_attempts
CREATE POLICY "Users can view their own answer attempts" ON answer_attempts
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own answer attempts" ON answer_attempts
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own answer attempts" ON answer_attempts
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own answer attempts" ON answer_attempts
    FOR DELETE USING (user_id = current_user_id());

-- RLS Policies for answer_memory
CREATE POLICY "Users can view their own answer memory" ON answer_memory
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own answer memory" ON answer_memory
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own answer memory" ON answer_memory
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own answer memory" ON answer_memory
    FOR DELETE USING (user_id = current_user_id());

-- RLS Policies for application_notes
CREATE POLICY "Users can view their own application notes" ON application_notes
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can insert their own application notes" ON application_notes
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update their own application notes" ON application_notes
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own application notes" ON application_notes
    FOR DELETE USING (user_id = current_user_id());

-- Insert default interview questions
INSERT INTO interview_questions (id, question, category, difficulty, context, tags) VALUES
(gen_random_uuid(), 'Tell me about yourself.', 'behavioral', 'easy', 'Icebreaker question', ARRAY['introduction', 'personal']),
(gen_random_uuid(), 'What are your greatest strengths and weaknesses?', 'behavioral', 'medium', 'Self-assessment', ARRAY['self-awareness', 'improvement']),
(gen_random_uuid(), 'Describe a challenging technical problem you''ve solved.', 'technical', 'hard', 'Problem-solving', ARRAY['technical', 'problem-solving']),
(gen_random_uuid(), 'How do you handle conflicts with team members?', 'situational', 'medium', 'Team dynamics', ARRAY['conflict', 'teamwork']),
(gen_random_uuid(), 'Describe your leadership experience.', 'leadership', 'medium', 'Leadership assessment', ARRAY['leadership', 'management']),
(gen_random_uuid(), 'Where do you see yourself in 5 years?', 'general', 'medium', 'Career goals', ARRAY['career', 'goals', 'future'])
ON CONFLICT DO NOTHING;

-- Create updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_resume_versions_updated_at BEFORE UPDATE ON resume_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_follow_up_reminders_updated_at BEFORE UPDATE ON follow_up_reminders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_answer_memory_updated_at BEFORE UPDATE ON answer_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_application_notes_updated_at BEFORE UPDATE ON application_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE resume_versions IS 'Stores multiple resume versions per user with metadata and analytics';
COMMENT ON TABLE follow_up_reminders IS 'Automated and manual follow-up reminders for applications';
COMMENT ON TABLE interview_questions IS 'Interview question bank with categories and difficulty levels';
COMMENT ON TABLE answer_attempts IS 'User practice attempts at answering interview questions';
COMMENT ON TABLE answer_memory IS 'Memorized answers and key points for interview questions';
COMMENT ON TABLE application_notes IS 'User notes and annotations for job applications';
