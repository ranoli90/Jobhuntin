import asyncio

import asyncpg


async def check_migrations():
    conn = await asyncpg.connect(
        "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a:5432/jobhuntin"
    )

    # Check existing migrations
    try:
        rows = await conn.fetch(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 5"
        )
        print("Current migrations:")
        for row in rows:
            print(f"  {row['version']}")
    except Exception as e:
        print(f"No schema_migrations table: {e}")

    # Check if our new tables exist
    tables = [
        "resume_versions",
        "follow_up_reminders",
        "interview_questions",
        "answer_attempts",
        "answer_memory",
        "application_notes",
    ]

    for table in tables:
        try:
            await conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
            print(f"✓ Table {table} exists")
        except Exception as e:
            print(f"✗ Table {table} missing: {e}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_migrations())
