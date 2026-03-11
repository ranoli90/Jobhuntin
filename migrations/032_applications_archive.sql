-- +migrate Up
-- PRIV-007: Archive applications before retention delete (was hard-delete only).
-- applications_archive stores historical records for compliance/audit.

CREATE TABLE IF NOT EXISTS public.applications_archive (
    LIKE public.applications INCLUDING DEFAULTS
);

-- Primary key for ON CONFLICT; no FKs (LIKE DEFAULTS excludes them) so archive keeps orphaned refs
ALTER TABLE public.applications_archive ADD PRIMARY KEY (id);

CREATE INDEX IF NOT EXISTS idx_applications_archive_created_at
    ON public.applications_archive(created_at);

CREATE INDEX IF NOT EXISTS idx_applications_archive_user_id
    ON public.applications_archive(user_id);

-- +migrate Down
DROP TABLE IF EXISTS public.applications_archive;
