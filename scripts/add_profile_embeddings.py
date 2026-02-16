#!/usr/bin/env python
"""Add profile_embeddings table to Render PostgreSQL database."""

import asyncio

import asyncpg

DATABASE_URL = "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/jobhuntin?sslmode=require"


async def run_migration():
    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("Adding profile_embeddings table...")

        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS profile_embeddings (
                    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    embedding JSONB,
                    text_hash VARCHAR(64),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            print("  profile_embeddings: OK")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  profile_embeddings: already exists")
            else:
                print(f"  profile_embeddings: ERROR - {e}")

        # Verify
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('job_embeddings', 'profile_embeddings')
            ORDER BY table_name
        """)

        print("\nEmbedding tables:")
        for t in tables:
            print(f"  - {t['table_name']}")

        print("\nMigration completed!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
