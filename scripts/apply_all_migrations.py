import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def read_file_content(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"UTF-8 decode failed for {path}, trying UTF-16...")
        with open(path, "r", encoding="utf-16") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None

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

    print("Reading remediation.sql...")
    sql_remediation = read_file_content("remediation.sql")
    if sql_remediation:
        print("Applying remediation (indexes, roles)...")
        try:
            await conn.execute(sql_remediation)
            print("Remediation applied successfully!")
        except Exception as e:
            print(f"Error applying remediation: {e}")

    print("Reading security_hardening.sql...")
    sql_security = read_file_content("security_hardening.sql")
    if sql_security:
        print("Applying security hardening (RLS, headers logic)...")
        try:
            await conn.execute(sql_security)
            print("Security hardening applied successfully!")
        except Exception as e:
            print(f"Error applying security hardening: {e}")

    await conn.close()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(apply())
