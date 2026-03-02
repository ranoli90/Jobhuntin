
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def test_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env file.")
        return

    import ssl

    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = True

    print(f"Attempting to connect to: {db_url.split('@')[-1]}") # Hide password
    try:
        conn = await asyncpg.connect(db_url, ssl=ctx)
        print("✅ Successfully connected to the database!")
        await conn.close()
        print("✅ Connection closed.")
    except asyncpg.InvalidPasswordError:
        print("❌ Authentication failed: Invalid password.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_db_connection())
