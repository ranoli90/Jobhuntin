
import asyncio
import asyncpg
import os
import uuid
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Mock env setup - usually loaded from .env
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Fallback for verification if not in env
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    DATABASE_URL = line.strip().split("=", 1)[1]
                    break
    except Exception:
        pass

if not DATABASE_URL:
    logger.error("DATABASE_URL not found")
    exit(1)

async def test_full_flow():
    logger.info(f"Connecting to DB: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '...'}")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return


    async def setup_schema(conn):
        logger.info("Setting up schema if needed...")
        # Schema derived from debug_schema.py (decoupled version)
        stmts = [
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
            # Alter statements
            "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS tenant_id text",
            "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS attempt_count int NOT NULL DEFAULT 0",
            "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS last_processed_at timestamptz",
            "ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS blueprint_key text",
            "CREATE INDEX IF NOT EXISTS idx_applications_tenant ON public.applications(tenant_id)",
        ]
        
        for stmt in stmts:
            try:
                await conn.execute(stmt)
            except Exception as e:
                # Type existing error ignore
                if "already exists" not in str(e):
                    logger.warning(f"Schema setup warning: {e}")
        logger.info("   ✅ Schema setup checks complete")

    try:
        await setup_schema(conn)

        # 1. Registration (Simulate SSO/Auth creating a user in public.users)
        user_id = uuid.uuid4()
        email = f"test_verify_{str(user_id)[:8]}@example.com"
        full_name = "Test User Verification"
        
        logger.info(f"1. Testing Registration for {email}...")
        await conn.execute(
            """
            INSERT INTO public.users (id, email, full_name, created_at, updated_at)
            VALUES ($1, $2, $3, now(), now())
            """,
            user_id, email, full_name
        )
        logger.info("   ✅ User created in public.users")

        # 2. Onboarding (Create Profile)
        logger.info("2. Testing Onboarding (Profile Creation)...")
        profile_data = json.dumps({"onboarding_step": "completed", "role": "software_engineer"})
        await conn.execute(
            """
            INSERT INTO public.profiles (user_id, profile_data, resume_url)
            VALUES ($1, $2, 'skipped')
            """,
            user_id, profile_data
        )
        logger.info("   ✅ Profile created in public.profiles")

        # Verify Tenant Creation
        tenant_id = str(uuid.uuid4()) # Keep as string for text column
        await conn.execute(
            """
            INSERT INTO public.tenants (id, name, slug, plan, seat_count, max_seats)
            VALUES ($1, $2, $3, 'FREE', 1, 1)
            """,
            tenant_id, "Test Tenant", f"test-tenant-{str(user_id)[:8]}"
        )
        await conn.execute(
             """
             INSERT INTO public.tenant_members (tenant_id, user_id, role)
             VALUES ($1, $2, 'OWNER')
             """,
             tenant_id, user_id
        )
        logger.info("   ✅ Tenant created and user assigned")


        # 3. Dashboard Features
        logger.info("3. Testing Dashboard Features...")
        
        # Create Job
        logger.info("   Creating Job...")
        job_id = uuid.uuid4()
        await conn.execute(
             """
            INSERT INTO public.jobs (id, external_id, title, company, application_url, source)
            VALUES ($1, $2, 'Senior Backend Engineer', 'Tech Corp', 'https://example.com/apply', 'internal')
            """,
            job_id, f"ext-{str(job_id)}"
        )
        logger.info("   ✅ Job created")
        
        # Create Application
        logger.info("   Creating Application...")
        app_id = uuid.uuid4()
        print(f"DEBUG: Application Insert Args: app_id={app_id}, user_id={user_id}, job_id={job_id}, tenant_id={tenant_id}")
        await conn.execute(
            """
            INSERT INTO public.applications (id, user_id, job_id, status, tenant_id)
            VALUES ($1, $2, $3, 'QUEUED'::public.application_status, $4)
            """,
            app_id, user_id, job_id, tenant_id
        )
        logger.info("   ✅ Application created")

        # Fetch Dashboard Data (Simulate queries from api/main.py and email_digest.py)
        import sys
        
        # Test Simple Count
        try:
            c = await conn.fetchval("SELECT count(*) FROM public.applications")
            print(f"DEBUG: Count applications = {c}")
        except Exception as e:
            print(f"DEBUG: Simple Count Failed: {e}", file=sys.stderr)

        # Test Status Fetch
        try:
            s = await conn.fetchval("SELECT status FROM public.applications LIMIT 1")
            print(f"DEBUG: Status fetch = {s} (type: {type(s)})")
        except Exception as e:
            print(f"DEBUG: Status Fetch Failed: {e}", file=sys.stderr)

        # Main Dashboard Stats
        try:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE status IN ('QUEUED'::public.application_status, 'PROCESSING'::public.application_status))::int as active,
                    COUNT(*) FILTER (WHERE status = 'COMPLETED'::public.application_status)::int as completed
                FROM public.applications WHERE user_id = $1
                """,
                user_id
            )
            logger.info(f"   Dashboard Stats: Active={stats['active']}, Completed={stats['completed']}")
            if stats['active'] == 1:
                logger.info("   ✅ Verification SUCCEEDED")
            else:
                logger.error("   ❌ Dashboard stats mismatch")
                # Don't exit here, let team check pass too if possible to see more info
        except Exception as e:
             logger.error(f"❌ Stats Query Failed: {e}")
             import traceback
             traceback.print_exc()

        # Verify Team/Member lookup (teams.py logic)

        # Verify Team/Member lookup (teams.py logic)
        member = await conn.fetchrow(
            """
            SELECT u.full_name, tm.role 
            FROM public.tenant_members tm
            JOIN public.users u ON u.id = tm.user_id
            WHERE tm.tenant_id = $1 AND tm.user_id = $2
            """,
            tenant_id, user_id
        )
        if member and member['full_name'] == full_name:
             logger.info(f"   ✅ Team member lookup successful: {member['full_name']} ({member['role']})")
        else:
             logger.error("   ❌ Team member lookup failed")

    except Exception as e:
        import traceback
        msg = f"❌ Verification failed: {e}\nTraceback:\n{traceback.format_exc()}"
        logger.error(msg)
        print(msg) # Print to stdout/stderr to be sure
        exit(1)
    finally:
        await conn.close()
        logger.info("Verification complete.")
        logging.shutdown()

if __name__ == "__main__":
    asyncio.run(test_full_flow())
