import asyncio
import socket

import asyncpg

PROJECT_REF = "zglovpfwyobbbaaocawz"
USER = f"postgres.{PROJECT_REF}"
PASSWORD = "ravhuv-gitqec-nixvY4"
DATABASE = "postgres"

REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-south-1",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "eu-north-1",
    "sa-east-1",
    "ca-central-1",
    "me-central-1",
    "af-south-1",
]


async def test_region(region):
    host = f"aws-0-{region}.pooler.supabase.com"
    try:
        socket.gethostbyname(host)
    except Exception:
        return None

    print(f"Testing {region}...")
    try:
        conn = await asyncpg.connect(
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            host=host,
            port=6543,
            timeout=5,
            ssl="require",
        )
        print(f"SUCCESS: Connected to {region}!")
        await conn.close()
        return region
    except Exception:
        # print(f"  Failed {region}: {e}")
        pass
    return None


async def main():
    tasks = [test_region(r) for r in REGIONS]
    results = await asyncio.gather(*tasks)
    found = [r for r in results if r]
    if found:
        print(f"\nMatch found in region(s): {found}")
    else:
        print("\nNo matching region found.")


if __name__ == "__main__":
    asyncio.run(main())
