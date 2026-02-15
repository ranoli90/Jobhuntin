#!/usr/bin/env python3
"""Test Render database connection"""
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
    db_url = "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a:5432/jobhuntin"
    asyncio.run(test_connection(db_url))
