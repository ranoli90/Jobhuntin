import asyncio
import os

os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/sorce"
os.environ["JWT_SECRET"] = "dummy"

from shared.metrics import get_rate_limiter


async def main():
    try:
        limiter = get_rate_limiter("api:127.0.0.1", 100, 60)
        res = await limiter.acquire()
        print("RESULT:", res)
    except Exception as e:
        print("ERROR:", repr(e))


asyncio.run(main())
