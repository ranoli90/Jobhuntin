import asyncio
import asyncpg
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "")


async def check_tables():
    conn = await asyncpg.connect(DATABASE_URL, ssl="require")
    tables = await conn.fetch("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    print("Existing tables:")
    for t in tables:
        print(f"  - {t['table_name']}")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_tables())
