"""initial_schema.

Revision ID: edde89a3dcba
Revises:
Create Date: 2026-02-09 23:15:44.562182

"""
from collections.abc import Sequence

from alembic import op

revision: str = 'edde89a3dcba'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) UNIQUE,
            domain VARCHAR(255) UNIQUE,
            plan VARCHAR(50) DEFAULT 'FREE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_members (
            tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            role VARCHAR(50) DEFAULT 'MEMBER',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (tenant_id, user_id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            full_name VARCHAR(255),
            avatar_url TEXT,
            linkedin_url TEXT,
            resume_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            location TEXT,
            role_type TEXT,
            salary_min INTEGER,
            remote_only BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            external_id VARCHAR(255),
            title VARCHAR(500) NOT NULL,
            company VARCHAR(255) NOT NULL,
            description TEXT,
            location TEXT,
            application_url TEXT,
            source VARCHAR(100),
            salary_min INTEGER,
            salary_max INTEGER,
            url TEXT,
            posted_date DATE,
            remote_policy VARCHAR(50) DEFAULT 'onsite',
            experience_level VARCHAR(50) DEFAULT 'mid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id),
            job_id UUID REFERENCES jobs(id),
            tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
            status VARCHAR(50) DEFAULT 'SAVED',
            attempt_count INTEGER DEFAULT 0,
            blueprint_key VARCHAR(255),
            priority_score INTEGER DEFAULT 0,
            available_at TIMESTAMPTZ,
            snoozed_until TIMESTAMPTZ,
            locked_at TIMESTAMPTZ,
            last_processed_at TIMESTAMPTZ,
            submitted_at TIMESTAMPTZ,
            last_error TEXT,
            notes TEXT,
            applied_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE application_event_type AS ENUM (
                'CREATED', 'CLAIMED', 'STARTED_PROCESSING',
                'FIELDS_EXTRACTED', 'FORM_FILLED', 'SUBMITTED',
                'APPLIED', 'FAILED', 'HOLD', 'RESUMED', 'RETRY_SCHEDULED'
            );
        EXCEPTION
            WHEN others THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE application_status AS ENUM (
                'SAVED', 'QUEUED', 'PROCESSING', 'REQUIRES_INPUT', 'APPLIED', 'FAILED'
            );
        EXCEPTION
            WHEN others THEN NULL;
        END $$;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS application_events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            event_type application_event_type NOT NULL,
            payload JSONB,
            tenant_id UUID,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS application_inputs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
            selector VARCHAR(500),
            question TEXT NOT NULL,
            field_type VARCHAR(50) DEFAULT 'text',
            answer TEXT,
            resolved BOOLEAN DEFAULT FALSE,
            meta JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
            event_type VARCHAR(100) NOT NULL,
            data JSONB,
            tenant_id UUID,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS answer_memory (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id),
            field_label TEXT NOT NULL,
            field_type VARCHAR(50) DEFAULT 'text',
            answer_value TEXT NOT NULL,
            use_count INTEGER DEFAULT 1,
            last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, field_label)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            profile_data JSONB NOT NULL DEFAULT '{}',
            tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS billing_customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
            provider VARCHAR(50) NOT NULL DEFAULT 'stripe',
            provider_customer_id VARCHAR(255),
            current_subscription_id VARCHAR(255),
            current_subscription_status VARCHAR(50),
            current_period_end TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS job_match_cache (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_id TEXT NOT NULL,
            profile_hash TEXT NOT NULL,
            score_data JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(job_id, profile_hash)
        )
    """)

    op.execute('CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_application_inputs_application_id ON application_inputs(application_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_events_application_id ON events(application_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_answer_memory_user_id ON answer_memory(user_id)')

    op.execute("""
        CREATE OR REPLACE FUNCTION public.claim_next_prioritized(p_max_attempts int DEFAULT 3)
        RETURNS SETOF public.applications AS $$
        BEGIN
            RETURN QUERY
            UPDATE public.applications
            SET status = 'PROCESSING', locked_at = now(), updated_at = now()
            WHERE id = (
                SELECT id FROM public.applications
                WHERE (status = 'QUEUED' OR (status = 'PROCESSING' AND locked_at < now() - interval '10 minutes'))
                  AND (snoozed_until IS NULL OR snoozed_until < now())
                  AND attempt_count < p_max_attempts
                ORDER BY priority_score DESC, created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_answer_memory_user_id')
    op.execute('DROP INDEX IF EXISTS idx_events_created_at')
    op.execute('DROP INDEX IF EXISTS idx_events_application_id')
    op.execute('DROP INDEX IF EXISTS idx_application_inputs_application_id')
    op.execute('DROP INDEX IF EXISTS idx_applications_status')
    op.execute('DROP INDEX IF EXISTS idx_applications_user_id')
    op.execute('DROP INDEX IF EXISTS idx_jobs_location')
    op.execute('DROP INDEX IF EXISTS idx_jobs_company')
    op.execute('DROP INDEX IF EXISTS idx_jobs_title')

    op.execute('DROP TABLE IF EXISTS billing_customers')
    op.execute('DROP FUNCTION IF EXISTS claim_next_prioritized(int)')
    op.execute('DROP TABLE IF EXISTS job_match_cache')
    op.execute('DROP TABLE IF EXISTS profiles')
    op.execute('DROP TABLE IF EXISTS application_events')
    op.execute('DROP TYPE IF EXISTS application_event_type')
    op.execute('DROP TABLE IF EXISTS answer_memory')
    op.execute('DROP TABLE IF EXISTS events')
    op.execute('DROP TABLE IF EXISTS application_inputs')
    op.execute('DROP TABLE IF EXISTS applications')
    op.execute('DROP TABLE IF EXISTS jobs')
    op.execute('DROP TABLE IF EXISTS user_preferences')
    op.execute('DROP TABLE IF EXISTS users')
    op.execute('DROP TABLE IF EXISTS tenant_members')
    op.execute('DROP TABLE IF EXISTS tenants')
