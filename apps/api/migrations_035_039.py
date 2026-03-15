"""Database migrations 035-039 for API startup.

This module runs migrations automatically when the API starts.
All migrations use IF NOT EXISTS for idempotency.
"""

import asyncpg
from asyncpg import Pool


async def run_migrations(pool: Pool) -> None:
    """Run all migrations (035-039) on API startup.
    
    Uses IF NOT EXISTS for idempotent execution.
    """
    async with pool.acquire() as conn:
        # Migration 035: Job Quality Fields
        await _run_migration_035(conn)

        # Migration 036: Companies Table
        await _run_migration_036(conn)

        # Migration 037: Analytics Tables
        await _run_migration_037(conn)

        # Migration 038: Data Retention Tables
        await _run_migration_038(conn)

        # Migration 039: User Consents
        await _run_migration_039(conn)


async def _run_migration_035(conn: asyncpg.Connection) -> None:
    """Migration 035: Job Quality Fields"""
    # Spam detection fields
    await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_spam BOOLEAN DEFAULT FALSE")
    await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS spam_score FLOAT")

    # Salary validation fields
    await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_validated BOOLEAN")
    await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_validation_notes TEXT")

    # Duplicate detection
    await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS canonical_job_id UUID REFERENCES jobs(id)")

    # Company verification
    await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_score FLOAT")

    # Quality flags
    await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS quality_flags JSONB")

    # Indexes
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_is_spam ON jobs(is_spam)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_canonical_job_id ON jobs(canonical_job_id)")
    await conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_jobs_company_score ON jobs(company_score) WHERE company_score IS NOT NULL")


async def _run_migration_036(conn: asyncpg.Connection) -> None:
    """Migration 036: Companies Table"""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(500) NOT NULL,
            domain VARCHAR(255),
            industry VARCHAR(255),
            employee_count_range VARCHAR(50),
            linkedin_url VARCHAR(500),
            description TEXT,
            is_verified BOOLEAN DEFAULT FALSE,
            verification_level VARCHAR(50) DEFAULT 'none',
            verified_at TIMESTAMPTZ,
            verified_by UUID REFERENCES users(id),
            reputation_score FLOAT,
            company_score FLOAT,
            last_scored_at TIMESTAMPTZ,
            domain_registered BOOLEAN,
            domain_age_days INTEGER,
            domain_registrar VARCHAR(255),
            founded_year INTEGER,
            company_type VARCHAR(100),
            company_size VARCHAR(50),
            headquarters VARCHAR(255),
            is_known_good BOOLEAN DEFAULT FALSE,
            is_suspicious BOOLEAN DEFAULT FALSE,
            known_scam BOOLEAN DEFAULT FALSE,
            verification_data JSONB,
            raw_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT unique_company_domain UNIQUE (domain)
        )
    """)

    # Indexes
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_reputation_score "
        "ON companies(reputation_score) WHERE reputation_score IS NOT NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_company_score "
        "ON companies(company_score) WHERE company_score IS NOT NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_is_verified "
        "ON companies(is_verified) WHERE is_verified = TRUE"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_suspicious "
        "ON companies(is_suspicious) WHERE is_suspicious = TRUE"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_known_scam "
        "ON companies(known_scam) WHERE known_scam = TRUE"
    )

    # Add company_id to jobs
    await conn.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company_id ON jobs(company_id)")


async def _run_migration_037(conn: asyncpg.Connection) -> None:
    """Migration 037: Analytics Tables"""
    # User events
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_type VARCHAR(100) NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_user_id ON user_events(user_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_event_type ON user_events(event_type)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_created_at ON user_events(created_at)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_user_type ON user_events(user_id, event_type)")
    await conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_user_events_user_created ON user_events(user_id, created_at DESC)")

    # Job views
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS job_views (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_views_user_id ON job_views(user_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_views_job_id ON job_views(job_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_views_created_at ON job_views(created_at)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_job_views ON job_views(user_id, job_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_job_views_engagement ON job_views(job_id, created_at DESC)")

    # Application outcomes
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS application_outcomes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            response_time_days INTEGER,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_application_outcomes_application_id ON application_outcomes(application_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_application_outcomes_status ON application_outcomes(status)")
    await conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_application_outcomes_created_at ON application_outcomes(created_at)")


async def _run_migration_038(conn: asyncpg.Connection) -> None:
    """Migration 038: Data Retention Tables"""
    # Retention policies
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS retention_policies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            data_type VARCHAR(100) NOT NULL UNIQUE,
            retention_days INTEGER NOT NULL DEFAULT 90,
            description TEXT,
            legal_basis VARCHAR(255),
            allow_soft_delete BOOLEAN DEFAULT TRUE,
            batch_size INTEGER DEFAULT 1000,
            requires_archive BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_retention_policies_data_type ON retention_policies(data_type)")

    # Data retention logs
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS data_retention_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id VARCHAR(100) NOT NULL,
            data_type VARCHAR(100) NOT NULL,
            deleted_count INTEGER NOT NULL DEFAULT 0,
            batch_number INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_data_retention_logs_job_id ON data_retention_logs(job_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_data_retention_logs_data_type ON data_retention_logs(data_type)")
    await conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_data_retention_logs_created_at ON data_retention_logs(created_at DESC)")

    # Trigger function
    await conn.execute("""
        CREATE OR REPLACE FUNCTION update_retention_policy_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    await conn.execute("DROP TRIGGER IF EXISTS update_retention_policy_timestamp_trigger ON retention_policies")
    await conn.execute("""
        CREATE TRIGGER update_retention_policy_timestamp_trigger
            BEFORE UPDATE ON retention_policies
            FOR EACH ROW
            EXECUTE FUNCTION update_retention_policy_timestamp()
    """)

    # Default policies (ignore conflicts)
    await conn.execute("""
        INSERT INTO retention_policies (
    data_type, retention_days, description, legal_basis, allow_soft_delete, batch_size, requires_archive)
        VALUES 
            (
    'session_logs', 90, 'Session logs for security auditing', 'Legitimate interest - Security monitoring', TRUE, 5000,
    FALSE),
            (
    'analytics_events', 365, 'Analytics events for product improvement', 'Consent - Analytics tracking', TRUE, 10000,
    FALSE),
            (
    'application_data', 30, 'Job application data after account deletion', 'GDPR Art. 17 - Right to erasure', TRUE,
    1000, TRUE),
            (
    'uploaded_resumes', 0, 'Uploaded resumes - retained while account active', 'Contract performance', TRUE, 500, TRUE),
            (
    'api_logs', 90, 'API request logs for debugging and security', 'Legitimate interest - API monitoring', TRUE, 10000,
    FALSE)
        ON CONFLICT (data_type) DO NOTHING
    """)


async def _run_migration_039(conn: asyncpg.Connection) -> None:
    """Migration 039: User Consents"""
    # User consents
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_consents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            anonymous_id VARCHAR(255),
            consent_type VARCHAR(50) NOT NULL,
            granted BOOLEAN NOT NULL DEFAULT FALSE,
            granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            revoked_at TIMESTAMP WITH TIME ZONE,
            ip_address INET,
            user_agent TEXT,
            version VARCHAR(20) DEFAULT '2.0',
            source VARCHAR(50) DEFAULT 'web',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT unique_user_consent UNIQUE (user_id, consent_type),
            CONSTRAINT unique_anonymous_consent UNIQUE (anonymous_id, consent_type)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_consents_user_id ON user_consents(user_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_consents_anonymous_id ON user_consents(anonymous_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(consent_type)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_consents_granted_at ON user_consents(granted_at DESC)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_consents_ip ON user_consents(ip_address)")

    # Consent audit log
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS consent_audit_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            anonymous_id VARCHAR(255),
            consent_type VARCHAR(50) NOT NULL,
            action VARCHAR(20) NOT NULL,
            previous_value BOOLEAN,
            new_value BOOLEAN,
            ip_address INET,
            user_agent TEXT,
            reason VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_audit_user_id ON consent_audit_log(user_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_audit_anonymous_id ON consent_audit_log(anonymous_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_audit_created_at ON consent_audit_log(created_at DESC)")

    # Consent policies
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS consent_policies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version VARCHAR(20) NOT NULL UNIQUE,
            policy_text TEXT NOT NULL,
            effective_date DATE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_consent_policies_version ON consent_policies(version)")
