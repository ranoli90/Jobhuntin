import asyncio

import asyncpg

PROJECT_REF = "zglovpfwyobbbaaocawz"
USER = f"postgres.{PROJECT_REF}"
PASSWORD = "ravhuv-gitqec-nixvY4"
DATABASE = "postgres"

REGIONS = [
    "aws-0-us-east-1",
    "aws-0-us-west-1",
    "aws-0-eu-central-1",
    "aws-0-ap-southeast-1"
]

async def test_region(region):
    host = f"{region}.pooler.supabase.com"
    print(f"Testing {region} ({host})...")
    try:
        conn = await asyncpg.connect(
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            host=host,
            port=6543,
            timeout=10,
            ssl="require"
        )
        print(f"SUCCESS: Connected to {region}!")
        res = await conn.fetchval("SELECT version()")
        print(f"Version: {res}")
        await conn.close()
        return True
    except asyncio.TimeoutError:
        print(f"TIMEOUT: {region}")
    except Exception as e:
        print(f"FAILED: {region} ({e})")
    return False

async def main():
    for region in REGIONS:
        if await test_region(region):
            print(f"\nFinal Verdict: Your region is {region}")
            break

if __name__ == "__main__":
    asyncio.run(main())
