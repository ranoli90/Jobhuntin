"""Database migration utilities."""

from __future__ import annotations

import pathlib
import re

import asyncpg

from shared.logging_config import get_logger
from shared.repo_root import find_repo_root

logger = get_logger("sorce.migrations")


async def run_migrations(conn: asyncpg.Connection, base_path: pathlib.Path) -> None:
    """Run auth shim + schema.sql + all numbered migrations."""
    # Supabase-only patterns to skip on plain Postgres
    _skip = re.compile(
        r"(ALTER\s+PUBLICATION|supabase_realtime|auth\.uid\(\)|auth\.role\(\))",
        re.IGNORECASE,
    )

    async def _exec_stmts(sql_text: str, label: str) -> tuple[int, int]:
        """Split SQL on semicolons, execute each statement, return (ok, skip)."""
        ok = skip = 0
        # Crude split — handles $ blocks by joining them back
        raw_parts = sql_text.split(";")
        stmts: list[str] = []
        buf = ""
        for part in raw_parts:
            buf += part + ";"
            if buf.count("$") % 2 == 0:
                stmts.append(buf.strip())
                buf = ""
            else:
                pass
        if buf.strip():
            stmts.append(buf.strip())
        
        # Also handle statements separated by \n\n for complex blocks
        # Join all and try to execute as single transaction for CREATE statements
        for stmt in stmts:
            stmt = stmt.strip().rstrip(";").strip()
            if not stmt or stmt.startswith("--"):
                continue
            if _skip.search(stmt):
                skip += 1
                continue
            
            # Try to execute - if it fails due to dependency, try as a transaction
            try:
                await conn.execute(stmt)
                ok += 1
            except Exception as e:
                msg = str(e)
                # Handle various error cases
                if "already exists" in msg.lower() or "duplicate" in msg.lower():
                    ok += 1
                elif "does not exist" in msg and "relation" in msg:
                    # This might be a dependency issue - table will be created later
                    # Log at debug level only
                    logger.debug("  [%s] stmt skipped (dependency): %s", label, msg[:100])
                    skip += 1
                else:
                    logger.warning("  [%s] stmt failed: %s", label, msg[:150])
        return ok, skip

    # 1. Auth compatibility shim
    await conn.execute("CREATE SCHEMA IF NOT EXISTS auth")
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS auth.users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            email text, encrypted_password text,
            email_confirmed_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            raw_user_meta_data jsonb DEFAULT '{}'::jsonb
        )
    """
    )
    logger.info("  auth shim created")

    repo_root = find_repo_root(base_path)
    postgres_dir = repo_root / "infra" / "postgres"
    if not postgres_dir.exists():
        postgres_dir = repo_root / "supabase"  # legacy fallback

    # 2. Base schema - execute as a single transaction
    schema_file = postgres_dir / "schema.sql"
    if schema_file.exists():
        # Remove Supabase-specific parts
        schema_sql = schema_file.read_text(encoding="utf-8")
        schema_sql = schema_sql.replace("REFERENCES auth.users (id)", "")
        if "-- Row-Level Security" in schema_sql:
            schema_sql = schema_sql.split("-- Row-Level Security")[0]
        
        # Execute entire schema as a single transaction
        try:
            await conn.execute(schema_sql)
            logger.info("  schema.sql: applied successfully")
            ok, skip = 1, 0
        except Exception as e:
            # Fall back to statement-by-statement execution
            logger.warning("  schema.sql bulk failed, trying statement-by-statement: %s", str(e)[:100])
            ok, skip = await _exec_stmts(schema_sql, "schema")
            logger.info("  schema.sql: %d applied, %d skipped", ok, skip)

    # 3. Numbered migrations
    mig_dir = postgres_dir / "migrations"
    if mig_dir.exists():
        for mf in sorted(mig_dir.glob("[0-9]*.sql")):
            sql = mf.read_text(encoding="utf-8").strip()
            if not sql:
                continue
            ok, skip = await _exec_stmts(sql, mf.name)
            logger.info("  %s: %d applied, %d skipped", mf.name, ok, skip)
