import asyncio

import asyncpg


async def main():
    try:
        conn = await asyncpg.connect(
            user="postgres", password="postgres", host="127.0.0.1", port=5432
        )
        await conn.execute("CREATE DATABASE sorce")
        await conn.close()
        print('Database "sorce" created successfully.')
    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == "__main__":
    asyncio.run(main())
