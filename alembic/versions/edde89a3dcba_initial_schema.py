"""initial_schema

Revision ID: edde89a3dcba
Revises: 
Create Date: 2026-02-09 23:15:44.562182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edde89a3dcba'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    -- Enable UUID extension
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Tenants table
    CREATE TABLE IF NOT EXISTS tenants (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name VARCHAR(255) NOT NULL,
        domain VARCHAR(255) UNIQUE,
        plan VARCHAR(50) DEFAULT 'FREE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tenant members
    CREATE TABLE IF NOT EXISTS tenant_members (
        tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
        user_id UUID NOT NULL,
        role VARCHAR(50) DEFAULT 'MEMBER',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (tenant_id, user_id)
    );

    -- Users table (extends Supabase auth.users)
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        full_name VARCHAR(255),
        avatar_url TEXT,
        linkedin_url TEXT,
        resume_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- User preferences
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        location TEXT,
        role_type TEXT,
        salary_min INTEGER,
        remote_only BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Jobs table
    CREATE TABLE IF NOT EXISTS jobs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        title VARCHAR(500) NOT NULL,
        company VARCHAR(255) NOT NULL,
        description TEXT,
        location TEXT,
        salary_min INTEGER,
        salary_max INTEGER,
        url TEXT,
        posted_date DATE,
        remote_policy VARCHAR(50) DEFAULT 'onsite',
        experience_level VARCHAR(50) DEFAULT 'mid',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Job applications
    CREATE TABLE IF NOT EXISTS applications (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id),
        job_id UUID REFERENCES jobs(id),
        status VARCHAR(50) DEFAULT 'SAVED',
        notes TEXT,
        applied_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Application inputs (for dynamic forms)
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
    );

    -- Events table for audit trail
    CREATE TABLE IF NOT EXISTS events (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
        event_type VARCHAR(100) NOT NULL,
        data JSONB,
        tenant_id UUID,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Answer memory for smart pre-fill
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
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
    CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
    CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
    CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
    CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
    CREATE INDEX IF NOT EXISTS idx_application_inputs_application_id ON application_inputs(application_id);
    CREATE INDEX IF NOT EXISTS idx_events_application_id ON events(application_id);
    CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
    CREATE INDEX IF NOT EXISTS idx_answer_memory_user_id ON answer_memory(user_id);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    DROP INDEX IF EXISTS idx_answer_memory_user_id;
    DROP INDEX IF EXISTS idx_events_created_at;
    DROP INDEX IF EXISTS idx_events_application_id;
    DROP INDEX IF EXISTS idx_application_inputs_application_id;
    DROP INDEX IF EXISTS idx_applications_status;
    DROP INDEX IF EXISTS idx_applications_user_id;
    DROP INDEX IF EXISTS idx_jobs_location;
    DROP INDEX IF EXISTS idx_jobs_company;
    DROP INDEX IF EXISTS idx_jobs_title;

    DROP TABLE IF EXISTS answer_memory;
    DROP TABLE IF EXISTS events;
    DROP TABLE IF EXISTS application_inputs;
    DROP TABLE IF EXISTS applications;
    DROP TABLE IF EXISTS jobs;
    DROP TABLE IF EXISTS user_preferences;
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS tenant_members;
    DROP TABLE IF EXISTS tenants;
    """)
