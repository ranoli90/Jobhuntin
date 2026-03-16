"""Apply migrations to Render PostgreSQL database."""
from __future__ import annotations

import asyncio
import os
import ssl
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "packages"))

import asyncpg


async def apply_migrations():
    """Apply all migrations to the database."""
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    print(f"Connecting to database...")
    
    # Create SSL context for Render PostgreSQL
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True  # Enable for production security
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    # Connect to database with SSL
    conn = await asyncpg.connect(database_url, statement_cache_size=0, ssl=ssl_context)
    
    try:
        # Read and apply migration 042
        migration_path = os.path.join(_root, "migrations", "042_job_sync_tables.sql")
        if os.path.exists(migration_path):
            with open(migration_path, "r") as f:
                migration_sql = f.read()
            
            # Split by semicolon and execute each statement
            # Skip the migrate comments and just get the SQL
            statements = []
            in_up = False
            for line in migration_sql.split('\n'):
                if '-- +migrate Up' in line:
                    in_up = True
                    continue
                if '-- +migrate Down' in line:
                    in_up = False
                    continue
                if in_up and line.strip() and not line.strip().startswith('--'):
                    statements.append(line)
            
            full_sql = '\n'.join(statements)
            
            # Execute the migration
            print("Applying migration 042_job_sync_tables.sql...")
            await conn.execute(full_sql)
            print("Migration applied successfully!")
        else:
            print(f"Migration file not found: {migration_path}")
        
        # Verify tables exist
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('popular_searches', 'job_sync_runs', 'job_sync_config', 'job_source_stats')
        """)
        print(f"Verified tables: {[t['table_name'] for t in tables]}")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(apply_migrations())
