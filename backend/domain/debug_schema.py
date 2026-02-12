"""
Debug DDL statements for manual schema verification/fixing.
"""
from __future__ import annotations

import asyncpg


async def debug_auth_shim(conn: asyncpg.Connection, log_lines: list[str]) -> None:
    try:
        await conn.execute("CREATE SCHEMA IF NOT EXISTS auth")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS auth.users (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                email text, encrypted_password text,
                email_confirmed_at timestamptz,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                raw_user_meta_data jsonb DEFAULT '{}'::jsonb
            )
        """)
        log_lines.append("auth shim: OK")
    except Exception as e:
        log_lines.append(f"auth shim: FAIL {e}")

async def debug_critical_tables(conn: asyncpg.Connection, log_lines: list[str]) -> None:
    critical_stmts = [
        "CREATE TYPE public.application_status AS ENUM ('QUEUED','PROCESSING','REQUIRES_INPUT','APPLIED','FAILED')",
        """CREATE TABLE IF NOT EXISTS public.users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            full_name text, email text, avatar_url text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )""",
        """CREATE TABLE IF NOT EXISTS public.tenants (
            id text PRIMARY KEY, name text NOT NULL, slug text UNIQUE,
            plan text NOT NULL DEFAULT 'FREE', team_name text,
            seat_count int NOT NULL DEFAULT 1, max_seats int NOT NULL DEFAULT 1,
            stripe_customer_id text, stripe_subscription_id text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )""",
        """CREATE TABLE IF NOT EXISTS public.tenant_members (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id text NOT NULL, user_id uuid NOT NULL,
            role text NOT NULL DEFAULT 'MEMBER',
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(tenant_id, user_id, role)
        )""",
        """CREATE TABLE IF NOT EXISTS public.profiles (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
            profile_data jsonb NOT NULL DEFAULT '{}'::jsonb, resume_url text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )""",
        """CREATE TABLE IF NOT EXISTS public.jobs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            external_id text NOT NULL UNIQUE, title text NOT NULL, company text NOT NULL,
            description text, location text, salary_min numeric(12,2), salary_max numeric(12,2),
            category text, application_url text NOT NULL,
            source text NOT NULL DEFAULT 'adzuna', raw_data jsonb,
            created_at timestamptz NOT NULL DEFAULT now()
        )""",
        """CREATE TABLE IF NOT EXISTS public.applications (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            job_id uuid NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
            status public.application_status NOT NULL DEFAULT 'QUEUED',
            error_message text, locked_at timestamptz, submitted_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(user_id, job_id)
        )""",
        """CREATE TABLE IF NOT EXISTS public.application_inputs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id uuid NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
            selector text NOT NULL, question text NOT NULL,
            field_type text NOT NULL DEFAULT 'text', answer text,
            created_at timestamptz NOT NULL DEFAULT now(), answered_at timestamptz
        )""",
        """CREATE TABLE IF NOT EXISTS public.billing_customers (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id text NOT NULL UNIQUE, stripe_customer_id text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )""",
        """CREATE TABLE IF NOT EXISTS public.application_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id uuid, event_type text NOT NULL,
            payload jsonb DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now()
        )""",
    ]
    for stmt in critical_stmts:
        try:
            await conn.execute(stmt)
            name = stmt.split("(")[0].strip().split()[-1] if "TABLE" in stmt else stmt.split("(")[0].strip().split()[-1]
            log_lines.append(f"  created: {name}")
        except Exception as e:
            log_lines.append(f"  FAIL: {str(e)[:120]}")

async def debug_alter_stmts(conn: asyncpg.Connection, log_lines: list[str]) -> None:
    alter_stmts = [
        "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS tenant_id text",
        "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS attempt_count int NOT NULL DEFAULT 0",
        "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS last_processed_at timestamptz",
        "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS blueprint_key text",
        "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS locked_by text",
        "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS snoozed_until timestamptz",
        "CREATE OR REPLACE FUNCTION public.claim_next_prioritized(p_max_attempts int DEFAULT 3) RETURNS SETOF public.applications AS $$ BEGIN RETURN QUERY UPDATE public.applications SET status = 'PROCESSING', locked_at = now(), updated_at = now() WHERE id = ( SELECT id FROM public.applications WHERE (status = 'QUEUED' OR (status = 'PROCESSING' AND locked_at < now() - interval '10 minutes')) AND (snoozed_until IS NULL OR snoozed_until < now()) AND attempt_count < p_max_attempts ORDER BY priority_score DESC, created_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED ) RETURNING *; END; $$ LANGUAGE plpgsql;",
        "ALTER TABLE public.application_inputs ADD COLUMN IF NOT EXISTS resolved boolean NOT NULL DEFAULT false",
        "ALTER TABLE public.application_inputs ADD COLUMN IF NOT EXISTS meta jsonb DEFAULT '{}'::jsonb",
        "ALTER TABLE public.application_events ADD COLUMN IF NOT EXISTS tenant_id text",
        "CREATE INDEX IF NOT EXISTS idx_applications_tenant ON public.applications(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_applications_status ON public.applications(status)",
        "CREATE INDEX IF NOT EXISTS idx_applications_blueprint ON public.applications(blueprint_key)",
    ]
    for stmt in alter_stmts:
        try:
            await conn.execute(stmt)
            log_lines.append(f"  alter: {stmt[:60]}...")
        except Exception as e:
            log_lines.append(f"  alter FAIL: {str(e)[:80]}")
