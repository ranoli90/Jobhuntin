#!/usr/bin/env python3
"""Test Render database connection."""

import asyncio

import asyncpg


async def test_connection(db_url):
    try:
        conn = await asyncpg.connect(db_url)
        await conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    asyncio.run(test_connection(db_url))
