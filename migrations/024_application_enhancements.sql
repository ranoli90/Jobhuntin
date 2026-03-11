-- +migrate Up

-- Add missing columns to applications table
ALTER TABLE applications ADD COLUMN IF NOT EXISTS stage VARCHAR(50) DEFAULT 'new';
ALTER TABLE applications ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS notes_count INTEGER DEFAULT 0;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS reminders_count INTEGER DEFAULT 0;

-- Create index for tenant_id lookups
CREATE INDEX IF NOT EXISTS idx_applications_tenant_id ON applications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id_status ON applications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_applications_tenant_user ON applications(tenant_id, user_id);

-- Application notes table
CREATE TABLE IF NOT EXISTS application_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    tenant_id UUID,
    content TEXT NOT NULL,
    note_type VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_application_notes_app_id ON application_notes(application_id);

-- Follow-up reminders table
CREATE TABLE IF NOT EXISTS follow_up_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    tenant_id UUID,
    remind_at TIMESTAMPTZ NOT NULL,
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_user ON follow_up_reminders(user_id, status);
CREATE INDEX IF NOT EXISTS idx_follow_up_reminders_remind_at ON follow_up_reminders(remind_at) WHERE status = 'pending';

-- +migrate Down
ALTER TABLE applications DROP COLUMN IF EXISTS stage;
ALTER TABLE applications DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE applications DROP COLUMN IF EXISTS priority;
ALTER TABLE applications DROP COLUMN IF EXISTS notes_count;
ALTER TABLE applications DROP COLUMN IF EXISTS reminders_count;
DROP TABLE IF EXISTS follow_up_reminders;
DROP TABLE IF EXISTS application_notes;
DROP INDEX IF EXISTS idx_applications_tenant_id;
DROP INDEX IF EXISTS idx_applications_user_id_status;
DROP INDEX IF EXISTS idx_applications_tenant_user;
