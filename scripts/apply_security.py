import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def apply():
    if not DATABASE_URL:
        print("DATABASE_URL not set")
        return

    print("Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    print("Reading security_hardening.sql...")
    try:
        with open("security_hardening.sql", "r", encoding="utf-8") as f:
            sql = f.read()
    except Exception:
        # Fallback for utf-16 if powershell created it
        with open("security_hardening.sql", "r", encoding="utf-16") as f:
            sql = f.read()

    print("Applying security hardening...")
    try:
        await conn.execute(sql)
        print("Security hardening applied successfully!")
    except Exception as e:
        print(f"Error applying security hardening: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(apply())
