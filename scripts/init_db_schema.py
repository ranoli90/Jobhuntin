"""
Direct schema initialization script.
Run this to initialize the database schema directly.
"""
import asyncio
import sys

import asyncpg


async def main():
    # Get DATABASE_URL from environment
    import os
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set")
        sys.exit(1)

    # Parse the URL to get connection params
    # Format: postgresql://user:password@host:port/dbname

    # Handle both formats - with and without sslmode
    url = database_url.split("?")[0]  # Remove sslmode params if present
    url = url.replace("postgresql://", "")

    parts = url.split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")

    user = user_pass[0]
    password = user_pass[1]
    host_port = host_db[0].split(":")
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 5432
    database = host_db[1]

    print(f"Connecting to {host}:{port}/{database}...")

    # Connect
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=database,
        database=database,
        ssl="require"
    )

    print("Connected!")

    # Create extension
    try:
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        print("Created uuid-ossp extension")
    except Exception as e:
        print(f"Extension error: {e}")

    # Read schema file
    import pathlib
    schema_path = pathlib.Path(__file__).parent / "infra" / "postgres" / "schema.sql"

    if not schema_path.exists():
        # Try alternative location
        schema_path = pathlib.Path(__file__).parent.parent / "infra" / "postgres" / "schema.sql"

    if not schema_path.exists():
        print(f"Schema file not found at {schema_path}")
        sys.exit(1)

    print(f"Reading schema from {schema_path}...")
    schema_sql = schema_path.read_text()

    # Split by semicolon and execute each statement
    statements = [s.strip() for s in schema_sql.split(";") if s.strip() and not s.strip().startswith("--")]

    print(f"Found {len(statements)} statements to execute...")

    ok_count = 0
    error_count = 0

    for i, stmt in enumerate(statements):
        if not stmt:
            continue
        try:
            await conn.execute(stmt)
            ok_count += 1
            if ok_count % 20 == 0:
                print(f"  Applied {ok_count} statements...")
        except Exception as e:
            error_count += 1
            error_msg = str(e)[:100]
            # Only print first few errors
            if error_count <= 5:
                print(f"  Error {error_count}: {error_msg}")
            elif error_count == 6:
                print("  ...")

    print(f"\nDone: {ok_count} applied, {error_count} errors")

    # List tables
    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    print(f"\nTables in database ({len(tables)}):")
    for t in tables:
        print(f"  - {t['table_name']}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
