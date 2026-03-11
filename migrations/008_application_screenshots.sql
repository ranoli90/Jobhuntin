-- Migration for application screenshots table
-- This table stores screenshots captured during the application process
-- for success/failure proof and debugging

CREATE TABLE IF NOT EXISTS public.application_screenshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    stage VARCHAR(50) NOT NULL, -- pre_submit, post_submit, success, failure, etc.
    success BOOLEAN NOT NULL DEFAULT TRUE,
    screenshot_url TEXT,
    file_size INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_application_screenshots_application_id ON public.application_screenshots(application_id);
CREATE INDEX IF NOT EXISTS idx_application_screenshots_created_at ON public.application_screenshots(created_at);
CREATE INDEX IF NOT EXISTS idx_application_screenshots_stage ON public.application_screenshots(stage);
CREATE INDEX IF NOT EXISTS idx_application_screenshots_success ON public.application_screenshots(success);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_application_screenshots_updated_at 
    BEFORE UPDATE ON public.application_screenshots 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add RLS policies
ALTER TABLE public.application_screenshots ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view screenshots for their own applications
CREATE POLICY "Users can view own application screenshots" ON public.application_screenshots
    FOR SELECT USING (
        application_id IN (
            SELECT id FROM public.applications 
            WHERE user_id = auth.uid()
        )
    );

-- Policy: Admins can view all screenshots
CREATE POLICY "Admins can view all screenshots" ON public.application_screenshots
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Policy: System can insert screenshots (for the agent)
CREATE POLICY "System can insert screenshots" ON public.application_screenshots
    FOR INSERT WITH CHECK (true);

-- Policy: System can update screenshots (for the agent)
CREATE POLICY "System can update screenshots" ON public.application_screenshots
    FOR UPDATE WITH CHECK (true);

-- Comments
COMMENT ON TABLE public.application_screenshots IS 'Stores screenshots captured during job application process';
COMMENT ON COLUMN public.application_screenshots.application_id IS 'Reference to the application';
COMMENT ON COLUMN public.application_screenshots.filename IS 'Screenshot filename';
COMMENT ON COLUMN public.application_screenshots.stage IS 'Application stage when screenshot was captured';
COMMENT ON COLUMN public.application_screenshots.success IS 'Whether the application was successful at this stage';
COMMENT ON COLUMN public.application_screenshots.screenshot_url IS 'URL to access the screenshot';
COMMENT ON COLUMN public.application_screenshots.file_size IS 'Size of the screenshot file in bytes';
