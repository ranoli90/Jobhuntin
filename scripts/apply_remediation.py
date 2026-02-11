import asyncio
import os
import asyncpg
from runpy import run_path

# Hack to get settings from shared.config which expects certain paths
import sys
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "packages"))
sys.path.append(os.path.join(os.getcwd(), "apps"))

from shared.config import get_settings

async def apply_sql():
    print("Connecting to database...")
    settings = get_settings()
    # The config might not have DATABASE_URL directly if it constructs it?
    # checking config.py... it usually has database_url property or similar.
    # But Settings model usually parses env vars.
    # Let's assume settings has database_url.
    # Inspecting config.py in step 61: 
    # class Settings(BaseSettings): ... database_url: PostgresDsn
    # So we can use str(settings.database_url)
    
    dsn = str(settings.database_url)
    print(f"Target DB: {dsn.split('@')[-1]}") # hide credentials
    
    try:
        conn = await asyncpg.connect(dsn)
        print("Connected.")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    try:
        # 1. Apply remediation.sql
        print("Reading remediation.sql...")
        with open("remediation.sql", "r", encoding="utf-8") as f:
            sql = f.read()
        await conn.execute(sql)
        print("remediation.sql applied successfully!")

        # 2. Apply security_hardening.sql
        if os.path.exists("security_hardening.sql"):
            print("Applying security_hardening.sql...")
            with open("security_hardening.sql", "r") as f:
                sql2 = f.read()
            await conn.execute(sql2)
            print("security_hardening.sql applied successfully!")
        else:
            print("security_hardening.sql not found, skipping.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_sql())
