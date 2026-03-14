#!/usr/bin/env python3
"""Apply SQL migrations to Render database."""

import asyncio
import glob

import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Use the correct database URL from memory
DATABASE_URL = "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a:5432/jobhuntin"

async def apply_migration(conn, migration_file):
    """Apply a single migration file."""
    print(f"\n📄 Applying {migration_file}...")

    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Split by semicolons and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

        for i, statement in enumerate(statements):
            if statement:
                try:
                    await conn.execute(statement)
                    print(f"  ✅ Statement {i+1}/{len(statements)} executed")
                except Exception as e:
                    if "already exists" in str(e).lower() or "does not exist" in str(e).lower():
                        print(f"  ⚠️  Statement {i+1}: {e}")
                    else:
                        print(f"  ❌ Statement {i+1} failed: {e}")
                        return False

        print(f"✅ {migration_file} applied successfully")
        return True

    except Exception as e:
        print(f"❌ Error reading {migration_file}: {e}")
        return False

async def main():
    print("🚀 Applying database migrations to Render...")

    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Database connected successfully")

        # Get list of migration files
        migration_files = sorted(glob.glob("migrations/*.sql"))
        print(f"\n📋 Found {len(migration_files)} migration files:")

        success_count = 0
        for migration_file in migration_files:
            if await apply_migration(conn, migration_file):
                success_count += 1

        print("\n🎉 Migration summary:")
        print(f"   Total files: {len(migration_files)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {len(migration_files) - success_count}")

        # Check if we can query the database
        print("\n🔍 Testing database connection...")
        try:
            result = await conn.fetchval("SELECT COUNT(*) FROM users")
            print(f"✅ Database test passed - Users table has {result} rows")
        except Exception as e:
            print(f"❌ Database test failed: {e}")

        await conn.close()
        print("✅ Database connection closed")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
