-- +migrate Up
-- Contact form submissions from public marketing site (jobhuntin.com/contact).
-- No auth required; rate-limited by IP.

CREATE TABLE IF NOT EXISTS public.contact_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    company VARCHAR(200),
    inquiry_type VARCHAR(50) NOT NULL DEFAULT 'general' CHECK (inquiry_type IN ('general', 'support', 'sales', 'partnership')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contact_messages_created_at ON public.contact_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contact_messages_inquiry_type ON public.contact_messages(inquiry_type);

-- +migrate Down
DROP TABLE IF EXISTS public.contact_messages;
