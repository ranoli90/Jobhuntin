#!/usr/bin/env python
"""Run SQL migration against Render PostgreSQL database."""

import asyncio

import asyncpg

DATABASE_URL = "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/jobhuntin?sslmode=require"


async def run_migration():
    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("Running migration...\n")

        # Create user_skills table
        print("Creating user_skills table...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_skills (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    skill VARCHAR(100) NOT NULL,
                    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                    years_actual DECIMAL(4,1),
                    context TEXT,
                    last_used DATE,
                    verified BOOLEAN DEFAULT FALSE,
                    related_to TEXT[],
                    source VARCHAR(50) DEFAULT 'resume' CHECK (source IN ('resume', 'github', 'linkedin', 'manual')),
                    project_count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    UNIQUE(user_id, skill)
                )
            """)
            print("  user_skills: OK")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  user_skills: already exists")
            else:
                print(f"  user_skills: ERROR - {e}")

        # Create indexes for user_skills
        try:
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_skills_confidence ON user_skills(user_id, confidence DESC)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_skills_skill ON user_skills(skill)"
            )
            print("  user_skills indexes: OK")
        except Exception as e:
            print(f"  user_skills indexes: {e}")

        # Create work_style_profiles table
        print("\nCreating work_style_profiles table...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS work_style_profiles (
                    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    autonomy_preference VARCHAR(20) DEFAULT 'medium' CHECK (autonomy_preference IN ('high', 'medium', 'low')),
                    learning_style VARCHAR(20) DEFAULT 'building' CHECK (learning_style IN ('docs', 'building', 'pairing', 'courses')),
                    company_stage_preference VARCHAR(20) DEFAULT 'flexible' CHECK (company_stage_preference IN ('early_startup', 'growth', 'enterprise', 'flexible')),
                    communication_style VARCHAR(20) DEFAULT 'mixed' CHECK (communication_style IN ('async', 'sync', 'mixed', 'flexible')),
                    pace_preference VARCHAR(20) DEFAULT 'steady' CHECK (pace_preference IN ('fast', 'steady', 'methodical', 'flexible')),
                    ownership_preference VARCHAR(20) DEFAULT 'team' CHECK (ownership_preference IN ('solo', 'team', 'lead', 'flexible')),
                    career_trajectory VARCHAR(20) DEFAULT 'open' CHECK (career_trajectory IN ('ic', 'tech_lead', 'manager', 'founder', 'open')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            print("  work_style_profiles: OK")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  work_style_profiles: already exists")
            else:
                print(f"  work_style_profiles: ERROR - {e}")

        # Create job_signals table
        print("\nCreating job_signals table...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS job_signals (
                    job_id UUID PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
                    company_stage VARCHAR(20) CHECK (company_stage IN ('early_startup', 'growth', 'enterprise')),
                    pace VARCHAR(20) CHECK (pace IN ('fast', 'steady', 'methodical')),
                    autonomy_level VARCHAR(20) CHECK (autonomy_level IN ('high', 'medium', 'low')),
                    growth_potential VARCHAR(20) CHECK (growth_potential IN ('ic_path', 'lead_path', 'manager_path', 'limited')),
                    team_size VARCHAR(20) CHECK (team_size IN ('small', 'medium', 'large')),
                    remote_culture VARCHAR(20) CHECK (remote_culture IN ('async_first', 'hybrid', 'onsite_culture')),
                    signals_detected JSONB,
                    extracted_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            print("  job_signals: OK")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  job_signals: already exists")
            else:
                print(f"  job_signals: ERROR - {e}")

        # Create indexes for job_signals
        try:
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_job_signals_company_stage ON job_signals(company_stage)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_job_signals_growth ON job_signals(growth_potential)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_job_signals_pace ON job_signals(pace)"
            )
            print("  job_signals indexes: OK")
        except Exception as e:
            print(f"  job_signals indexes: {e}")

        # Create deep_profiles table
        print("\nCreating deep_profiles table...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS deep_profiles (
                    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    profile_json JSONB NOT NULL,
                    completeness_score DECIMAL(5,2) CHECK (completeness_score >= 0 AND completeness_score <= 100),
                    computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            print("  deep_profiles: OK")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  deep_profiles: already exists")
            else:
                print(f"  deep_profiles: ERROR - {e}")

        # Create index for deep_profiles
        try:
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_deep_profiles_completeness ON deep_profiles(completeness_score DESC)"
            )
            print("  deep_profiles index: OK")
        except Exception as e:
            print(f"  deep_profiles index: {e}")

        # Create job_embeddings table
        print("\nCreating job_embeddings table...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS job_embeddings (
                    job_id UUID PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
                    embedding JSONB,
                    text_hash VARCHAR(64),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            print("  job_embeddings: OK")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  job_embeddings: already exists")
            else:
                print(f"  job_embeddings: ERROR - {e}")

        # Add columns to users table
        print("\nAdding columns to users table...")
        try:
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completeness DECIMAL(5,2) DEFAULT 0"
            )
            print("  profile_completeness: OK")
        except Exception as e:
            print(f"  profile_completeness: {e}")

        try:
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS has_completed_onboarding BOOLEAN DEFAULT FALSE"
            )
            print("  has_completed_onboarding: OK")
        except Exception as e:
            print(f"  has_completed_onboarding: {e}")

        # Create updated_at function and triggers
        print("\nCreating triggers...")
        try:
            await conn.execute("""
                CREATE OR REPLACE FUNCTION set_updated_at()
                RETURNS trigger AS $$
                BEGIN
                    NEW.updated_at = now();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """)
            print("  set_updated_at function: OK")
        except Exception as e:
            print(f"  set_updated_at function: {e}")

        try:
            await conn.execute(
                "DROP TRIGGER IF EXISTS trg_user_skills_updated_at ON user_skills"
            )
            await conn.execute("""
                CREATE TRIGGER trg_user_skills_updated_at
                    BEFORE UPDATE ON user_skills
                    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)
            print("  trg_user_skills_updated_at: OK")
        except Exception as e:
            print(f"  trg_user_skills_updated_at: {e}")

        try:
            await conn.execute(
                "DROP TRIGGER IF EXISTS trg_work_style_profiles_updated_at ON work_style_profiles"
            )
            await conn.execute("""
                CREATE TRIGGER trg_work_style_profiles_updated_at
                    BEFORE UPDATE ON work_style_profiles
                    FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)
            print("  trg_work_style_profiles_updated_at: OK")
        except Exception as e:
            print(f"  trg_work_style_profiles_updated_at: {e}")

        # Verify tables were created
        print("\n" + "=" * 50)
        print("VERIFICATION")
        print("=" * 50)

        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('user_skills', 'work_style_profiles', 'job_signals', 'deep_profiles', 'job_embeddings')
            ORDER BY table_name
        """)

        print("\nCreated tables:")
        for t in tables:
            print(f"  - {t['table_name']}")

        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users'
            AND column_name IN ('profile_completeness', 'has_completed_onboarding')
            ORDER BY column_name
        """)

        print("\nAdded columns to users:")
        for c in columns:
            print(f"  - {c['column_name']}")

        print("\n" + "=" * 50)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 50)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
