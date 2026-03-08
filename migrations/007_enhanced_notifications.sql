-- Migration for enhanced notifications and alert processing
-- This migration adds tables for semantic notifications, alert processing, and user preferences

-- Enhanced alert processing log
CREATE TABLE IF NOT EXISTS public.alert_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
    alert_type VARCHAR(50) NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    alert_data JSONB NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for alert processing log
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_user_id ON public.alert_processing_log(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_tenant_id ON public.alert_processing_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_alert_type ON public.alert_processing_log(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_processing_log_processed_at ON public.alert_processing_log(processed_at);

-- Add updated_at trigger
CREATE TRIGGER update_alert_processing_log_updated_at 
    BEFORE UPDATE ON public.alert_processing_log 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enhanced user preferences table
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    dnd_active BOOLEAN DEFAULT FALSE,
    dnd_start_time TIME,
    dnd_end_time TIME,
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_sound BOOLEAN DEFAULT TRUE,
    notification_vibration BOOLEAN DEFAULT TRUE,
    notification_badge BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Add updated_at trigger for user preferences
CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON public.user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default user preferences for existing users
INSERT INTO public.user_preferences (user_id)
SELECT id FROM public.users u
WHERE NOT EXISTS (
    SELECT 1 FROM public.user_preferences up WHERE up.user_id = u.id
);

-- Notification semantic tags table for analytics
CREATE TABLE IF NOT EXISTS public.notification_semantic_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID REFERENCES public.notification_log(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    relevance_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for semantic tags
CREATE INDEX IF NOT EXISTS idx_notification_semantic_tags_notification_id ON public.notification_semantic_tags(notification_id);
CREATE INDEX IF NOT EXISTS idx_notification_semantic_tags_tag ON public.notification_semantic_tags(tag);
CREATE INDEX IF NOT EXISTS idx_notification_semantic_tags_category ON public.notification_semantic_tags(category);

-- User interests for semantic matching
CREATE TABLE IF NOT EXISTS public.user_interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    interest VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, interest)
);

-- Add updated_at trigger for user interests
CREATE TRIGGER update_user_interests_updated_at 
    BEFORE UPDATE ON public.user_interests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Notification delivery tracking
CREATE TABLE IF NOT EXISTS public.notification_delivery_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID REFERENCES public.notification_log(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    delivery_status VARCHAR(20) NOT NULL, -- pending, sent, delivered, failed, expired
    delivery_method VARCHAR(20) NOT NULL, -- push, email, sms, in_app
    device_token VARCHAR(255),
    error_message TEXT,
    delivered_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for delivery tracking
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_notification_id ON public.notification_delivery_tracking(notification_id);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_user_id ON public.notification_delivery_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_status ON public.notification_delivery_tracking(delivery_status);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_tracking_delivered_at ON public.notification_delivery_tracking(delivered_at);

-- Add updated_at trigger for delivery tracking
CREATE TRIGGER update_notification_delivery_tracking_updated_at 
    BEFORE UPDATE ON public.notification_delivery_tracking 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Notification batching table
CREATE TABLE IF NOT EXISTS public.notification_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id VARCHAR(50) NOT NULL UNIQUE,
    total_notifications INTEGER NOT NULL DEFAULT 0,
    sent_notifications INTEGER NOT NULL DEFAULT 0,
    failed_notifications INTEGER NOT NULL DEFAULT 0,
    batch_status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    processing_started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add updated_at trigger for notification batches
CREATE TRIGGER update_notification_batches_updated_at 
    BEFORE UPDATE ON public.notification_batches 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS policies for new tables
ALTER TABLE public.alert_processing_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_semantic_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_delivery_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_batches ENABLE ROW LEVEL SECURITY;

-- Policies for alert processing log
CREATE POLICY "Users can view own alert processing log" ON public.alert_processing_log
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Admins can view all alert processing logs" ON public.alert_processing_log
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "System can manage alert processing log" ON public.alert_processing_log
    FOR ALL WITH CHECK (true);

-- Policies for user preferences
CREATE POLICY "Users can manage own preferences" ON public.user_preferences
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Admins can manage all user preferences" ON public.user_preferences
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

-- Policies for notification semantic tags
CREATE POLICY "Users can view own notification semantic tags" ON public.notification_semantic_tags
    FOR SELECT USING (
        notification_id IN (
            SELECT id FROM public.notification_log WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Admins can view all notification semantic tags" ON public.notification_semantic_tags
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "System can manage notification semantic tags" ON public.notification_semantic_tags
    FOR ALL WITH CHECK (true);

-- Policies for user interests
CREATE POLICY "Users can manage own interests" ON public.user_interests
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Admins can manage all user interests" ON public.user_interests
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

-- Policies for notification delivery tracking
CREATE POLICY "Users can view own delivery tracking" ON public.notification_delivery_tracking
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Admins can view all delivery tracking" ON public.notification_delivery_tracking
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "System can manage delivery tracking" ON public.notification_delivery_tracking
    FOR ALL WITH CHECK (true);

-- Policies for notification batches
CREATE POLICY "Admins can manage notification batches" ON public.notification_batches
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "System can manage notification batches" ON public.notification_batches
    FOR ALL WITH CHECK (true);

-- Default user interests for existing users
INSERT INTO public.user_interests (user_id, interest, category, weight)
SELECT u.id, 'job applications', 'career', 1.0
FROM public.users u
WHERE NOT EXISTS (
    SELECT 1 FROM public.user_interests ui 
    WHERE ui.user_id = u.id AND ui.interest = 'job applications'
);

INSERT INTO public.user_interests (user_id, interest, category, weight)
SELECT u.id, 'job search', 'career', 1.0
FROM public.users u
WHERE NOT EXISTS (
    SELECT 1 FROM public.user_interests ui 
    WHERE ui.user_id = u.id AND ui.interest = 'job search'
);

-- Comments
COMMENT ON TABLE public.alert_processing_log IS 'Log of all alerts processed by the system';
COMMENT ON TABLE public.user_preferences IS 'Enhanced user preferences for notifications and DND';
COMMENT ON TABLE public.notification_semantic_tags IS 'Semantic tags for notifications for analytics';
COMMENT ON TABLE public.user_interests IS 'User interests for semantic matching of notifications';
COMMENT ON TABLE public.notification_delivery_tracking IS 'Tracking of notification delivery status across channels';
COMMENT ON TABLE public.notification_batches IS 'Batch processing information for notifications';
COMMENT ON COLUMN public.user_preferences.dnd_active IS 'Whether Do Not Disturb mode is active';
COMMENT ON COLUMN public.user_preferences.dnd_start_time IS 'Start time for Do Not Disturb mode';
COMMENT ON COLUMN public.user_preferences.dnd_end_time IS 'End time for Do Not Disturb mode';
COMMENT ON COLUMN public.notification_delivery_tracking.delivery_status IS 'Delivery status: pending, sent, delivered, failed, expired';
COMMENT ON COLUMN public.notification_delivery_tracking.delivery_method IS 'Delivery method: push, email, sms, in_app';
