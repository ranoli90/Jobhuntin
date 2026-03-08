-- Migration for email communications log and enhanced notification tracking
-- This table stores all email communications sent to users

CREATE TABLE IF NOT EXISTS public.email_communications_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
    email_type VARCHAR(50) NOT NULL, -- status_change, magic_link_expiry, rate_limit_warning, etc.
    template_name VARCHAR(100) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    metadata JSONB,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_email_communications_log_user_id ON public.email_communications_log(user_id);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_tenant_id ON public.email_communications_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_email_type ON public.email_communications_log(email_type);
CREATE INDEX IF NOT EXISTS idx_email_communications_log_sent_at ON public.email_communications_log(sent_at);

-- Add updated_at trigger
CREATE TRIGGER update_email_communications_log_updated_at 
    BEFORE UPDATE ON public.email_communications_log 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enhanced email preferences table (if not exists)
CREATE TABLE IF NOT EXISTS public.email_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status_changes BOOLEAN DEFAULT TRUE,
    security BOOLEAN DEFAULT TRUE,
    usage_alerts BOOLEAN DEFAULT TRUE,
    marketing BOOLEAN DEFAULT FALSE,
    weekly_digest BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Add updated_at trigger for email preferences
CREATE TRIGGER update_email_preferences_updated_at 
    BEFORE UPDATE ON public.email_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default email preferences for existing users
INSERT INTO public.email_preferences (user_id)
SELECT id FROM public.users u
WHERE NOT EXISTS (
    SELECT 1 FROM public.email_preferences ep WHERE ep.user_id = u.id
);

-- Add email preferences column to users table as JSON for flexibility
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS email_preferences JSONB DEFAULT '{"status_changes": true, "security": true, "usage_alerts": true, "marketing": false, "weekly_digest": true}'::jsonb;

-- Update existing users to have default preferences
UPDATE public.users 
SET email_preferences = '{"status_changes": true, "security": true, "usage_alerts": true, "marketing": false, "weekly_digest": true}'::jsonb
WHERE email_preferences IS NULL;

-- RLS policies for email communications log
ALTER TABLE public.email_communications_log ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own email communications
CREATE POLICY "Users can view own email communications" ON public.email_communications_log
    FOR SELECT USING (
        user_id = auth.uid()
    );

-- Policy: Admins can view all email communications
CREATE POLICY "Admins can view all email communications" ON public.email_communications_log
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Policy: System can insert email communications
CREATE POLICY "System can insert email communications" ON public.email_communications_log
    FOR INSERT WITH CHECK (true);

-- RLS policies for email preferences
ALTER TABLE public.email_preferences ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own email preferences
CREATE POLICY "Users can manage own email preferences" ON public.email_preferences
    FOR ALL USING (
        user_id = auth.uid()
    );

-- Policy: Admins can manage all email preferences
CREATE POLICY "Admins can manage all email preferences" ON public.email_preferences
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Comments
COMMENT ON TABLE public.email_communications_log IS 'Log of all email communications sent to users';
COMMENT ON COLUMN public.email_communications_log.email_type IS 'Type of email: status_change, magic_link_expiry, rate_limit_warning, etc.';
COMMENT ON COLUMN public.email_communications_log.template_name IS 'Name of the email template used';
COMMENT ON COLUMN public.email_communications_log.metadata IS 'Additional metadata about the email (JSON)';
COMMENT ON TABLE public.email_preferences IS 'User email preferences and notification settings';
COMMENT ON COLUMN public.email_preferences.status_changes IS 'Receive application status change emails';
COMMENT ON COLUMN public.email_preferences.security IS 'Receive security-related emails (magic links, etc.)';
COMMENT ON COLUMN public.email_preferences.usage_alerts IS 'Receive usage limit and quota alerts';
COMMENT ON COLUMN public.email_preferences.marketing IS 'Receive marketing and promotional emails';
COMMENT ON COLUMN public.email_preferences.weekly_digest IS 'Receive weekly digest emails';
