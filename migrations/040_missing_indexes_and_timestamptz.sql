-- +migrate Up
-- DB-002: Add missing index on applications.job_id (foreign key)
-- DB-001: Convert core timestamp columns to TIMESTAMPTZ for timezone safety

-- DB-002: Missing foreign key index — queries joining applications→jobs
-- currently require sequential scans on larger datasets.
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);

-- DB-001: Convert TIMESTAMP → TIMESTAMPTZ on core tables.
-- PostgreSQL interprets bare TIMESTAMP as "without time zone"; TIMESTAMPTZ
-- stores UTC and converts on display, which is correct for multi-timezone users.
-- ALTER COLUMN TYPE … USING preserves existing data (interpreted as UTC).

ALTER TABLE tenants       ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE tenants       ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE users         ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE users         ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE jobs          ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE jobs          ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE applications  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE applications  ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE application_inputs ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE application_inputs ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE events        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

ALTER TABLE answer_memory ALTER COLUMN last_used_at TYPE TIMESTAMPTZ USING last_used_at AT TIME ZONE 'UTC';
ALTER TABLE answer_memory ALTER COLUMN created_at   TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

ALTER TABLE user_preferences ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE user_preferences ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE tenant_members   ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- +migrate Down
-- Revert TIMESTAMPTZ back to TIMESTAMP (data is preserved; TZ info stripped)

ALTER TABLE tenant_members   ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';

ALTER TABLE user_preferences ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE user_preferences ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';

ALTER TABLE answer_memory ALTER COLUMN created_at   TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';
ALTER TABLE answer_memory ALTER COLUMN last_used_at TYPE TIMESTAMP USING last_used_at AT TIME ZONE 'UTC';

ALTER TABLE events        ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';

ALTER TABLE application_inputs ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE application_inputs ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';

ALTER TABLE applications  ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE applications  ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';

ALTER TABLE jobs          ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE jobs          ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';

ALTER TABLE users         ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE users         ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';

ALTER TABLE tenants       ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE tenants       ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC';

DROP INDEX IF EXISTS idx_applications_job_id;
