-- Resume PDF generation and storage
-- This migration creates tables for storing generated resume PDFs
-- and tracking their usage and performance

-- Resume PDFs table
CREATE TABLE IF NOT EXISTS resume_pdfs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    profile_id UUID REFERENCES user_profiles(id),
    
    -- PDF metadata
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    file_path VARCHAR(500),
    template_style VARCHAR(50) NOT NULL DEFAULT 'professional',
    
    -- Tailoring results
    original_summary TEXT,
    tailored_summary TEXT,
    highlighted_skills JSONB DEFAULT '[]',
    emphasized_experiences JSONB DEFAULT '[]',
    added_keywords JSONB DEFAULT '[]',
    ats_optimization_score FLOAT DEFAULT 0.5 CHECK (ats_optimization_score >= 0.0 AND ats_optimization_score <= 1.0),
    tailoring_confidence VARCHAR(20) DEFAULT 'medium' CHECK (tailoring_confidence IN ('high', 'medium', 'low')),
    
    -- Generation metadata
    generation_time FLOAT DEFAULT 0.0, -- seconds
    pdf_content BYTEA, -- Store PDF bytes (for small files)
    storage_url VARCHAR(500), -- Cloud storage URL for large files
    
    -- Usage tracking
    download_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resume PDF analytics table
CREATE TABLE IF NOT EXISTS resume_pdf_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_pdf_id UUID NOT NULL REFERENCES resume_pdfs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    
    -- Analytics data
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('generated', 'downloaded', 'viewed', 'shared', 'applied_with')),
    event_data JSONB DEFAULT '{}',
    
    -- Performance metrics
    ats_score_before FLOAT,
    ats_score_after FLOAT,
    keyword_match_count INTEGER,
    skills_highlighted_count INTEGER,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resume PDF templates table
CREATE TABLE IF NOT EXISTS resume_pdf_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    ats_optimized BOOLEAN DEFAULT TRUE,
    
    -- Template configuration
    template_config JSONB DEFAULT '{}',
    preview_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage statistics
    usage_count INTEGER DEFAULT 0,
    average_ats_score FLOAT DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_resume_pdfs_user_id ON resume_pdfs(user_id);
CREATE INDEX IF NOT EXISTS idx_resume_pdfs_job_id ON resume_pdfs(job_id);
CREATE INDEX IF NOT EXISTS idx_resume_pdfs_profile_id ON resume_pdfs(profile_id);
CREATE INDEX IF NOT EXISTS idx_resume_pdfs_created_at ON resume_pdfs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_resume_pdfs_template_style ON resume_pdfs(template_style);
CREATE INDEX IF NOT EXISTS idx_resume_pdfs_ats_score ON resume_pdfs(ats_optimization_score);

CREATE INDEX IF NOT EXISTS idx_resume_pdf_analytics_resume_pdf_id ON resume_pdf_analytics(resume_pdf_id);
CREATE INDEX IF NOT EXISTS idx_resume_pdf_analytics_user_id ON resume_pdf_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_resume_pdf_analytics_job_id ON resume_pdf_analytics(job_id);
CREATE INDEX IF NOT EXISTS idx_resume_pdf_analytics_event_type ON resume_pdf_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_resume_pdf_analytics_created_at ON resume_pdf_analytics(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_resume_pdf_templates_template_id ON resume_pdf_templates(template_id);
CREATE INDEX IF NOT EXISTS idx_resume_pdf_templates_category ON resume_pdf_templates(category);
CREATE INDEX IF NOT EXISTS idx_resume_pdf_templates_is_active ON resume_pdf_templates(is_active);

-- Insert default templates
INSERT INTO resume_pdf_templates (template_id, name, description, category, ats_optimized) VALUES
('professional', 'Professional', 'Clean, traditional format suitable for most industries', 'professional', TRUE),
('modern', 'Modern', 'Contemporary design with subtle visual elements', 'modern', TRUE),
('executive', 'Executive', 'Sophisticated format for senior-level positions', 'executive', TRUE),
('technical', 'Technical', 'Format optimized for technical and engineering roles', 'technical', TRUE),
('creative', 'Creative', 'Stylish format for creative and design roles', 'creative', FALSE)
ON CONFLICT (template_id) DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_resume_pdfs_updated_at BEFORE UPDATE ON resume_pdfs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resume_pdf_templates_updated_at BEFORE UPDATE ON resume_pdf_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to increment template usage count
CREATE OR REPLACE FUNCTION increment_template_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE resume_pdf_templates 
    SET usage_count = usage_count + 1 
    WHERE template_id = NEW.template_style;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to increment template usage
CREATE TRIGGER increment_template_usage_trigger AFTER INSERT ON resume_pdfs
    FOR EACH ROW EXECUTE FUNCTION increment_template_usage_count();

-- Function to record analytics event
CREATE OR REPLACE FUNCTION record_resume_pdf_analytics(
    p_resume_pdf_id UUID,
    p_user_id UUID,
    p_job_id UUID,
    p_event_type VARCHAR(50),
    p_event_data JSONB DEFAULT '{}',
    p_ats_score_before FLOAT DEFAULT NULL,
    p_ats_score_after FLOAT DEFAULT NULL,
    p_keyword_match_count INTEGER DEFAULT NULL,
    p_skills_highlighted_count INTEGER DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    analytics_id UUID;
BEGIN
    INSERT INTO resume_pdf_analytics (
        resume_pdf_id,
        user_id,
        job_id,
        event_type,
        event_data,
        ats_score_before,
        ats_score_after,
        keyword_match_count,
        skills_highlighted_count
    ) VALUES (
        p_resume_pdf_id,
        p_user_id,
        p_job_id,
        p_event_type,
        p_event_data,
        p_ats_score_before,
        p_ats_score_after,
        p_keyword_match_count,
        p_skills_highlighted_count
    ) RETURNING id INTO analytics_id;
    
    RETURN analytics_id;
END;
$$ LANGUAGE plpgsql;

-- View for resume PDF statistics
CREATE OR REPLACE VIEW resume_pdf_stats AS
SELECT 
    u.id as user_id,
    COUNT(rp.id) as total_generated,
    AVG(rp.ats_optimization_score) as average_ats_score,
    AVG(rp.generation_time) as average_generation_time,
    COUNT(DISTINCT rp.job_id) as unique_jobs_applied,
    MAX(rp.created_at) as last_generated_at
FROM users u
LEFT JOIN resume_pdfs rp ON u.id = rp.user_id
WHERE rp.is_active = TRUE
GROUP BY u.id;

-- View for template performance
CREATE OR REPLACE VIEW template_performance_stats AS
SELECT 
    rpt.template_id,
    rpt.name,
    rpt.category,
    rpt.usage_count,
    AVG(rp.ats_optimization_score) as average_ats_score,
    COUNT(rp.id) as total_generated,
    AVG(rp.generation_time) as average_generation_time
FROM resume_pdf_templates rpt
LEFT JOIN resume_pdfs rp ON rpt.template_id = rp.template_style
WHERE rpt.is_active = TRUE
GROUP BY rpt.template_id, rpt.name, rpt.category, rpt.usage_count
ORDER BY rpt.usage_count DESC;

-- Function to clean up old resume PDFs (cleanup job)
CREATE OR REPLACE FUNCTION cleanup_old_resume_pdfs(days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM resume_pdfs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_old
    AND is_active = FALSE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
