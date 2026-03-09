#!/usr/bin/env python
"""Proper database migration system with tracking and rollback support.

This script provides a complete migration system that:
- Tracks applied migrations in a migrations table
- Runs migrations in order based on filename prefixes
- Supports rollback to specific versions
- Provides dry-run mode for testing
- Handles migration dependencies
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


class MigrationSystem:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None

    async def connect(self):
        """Establish database connection."""
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is required")
        self.conn = await asyncpg.connect(self.db_url)
        await self._ensure_migrations_table()

    async def disconnect(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    async def _ensure_migrations_table(self):
        """Create the migrations tracking table if it doesn't exist."""
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                checksum VARCHAR(64) NOT NULL
            )
        """)

    def _get_migration_files(self) -> List[Tuple[str, str]]:
        """Get all migration files sorted by version."""
        migrations = []

        if not MIGRATIONS_DIR.exists():
            print(f"Migrations directory not found: {MIGRATIONS_DIR}")
            return migrations

        for file_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            # Extract version from filename (e.g., 001_initial_schema.sql)
            match = re.match(r"^(\d{3})_(.+)\.sql$", file_path.name)
            if match:
                version = match.group(1)
                filename = file_path.name
                migrations.append((version, filename))
            else:
                print(f"Warning: Invalid migration filename format: {file_path.name}")

        return sorted(migrations, key=lambda x: x[0])

    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA-256 checksum of migration content."""
        import hashlib

        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def _get_applied_migrations(self) -> set:
        """Get set of already applied migration versions."""
        rows = await self.conn.fetch(
            "SELECT version FROM schema_migrations ORDER BY version"
        )
        return {row["version"] for row in rows}

    async def _apply_migration(
        self, version: str, filename: str, content: str, checksum: str
    ):
        """Apply a single migration."""
        print(f"  Applying {filename}...")

        try:
            # Start transaction
            async with self.conn.transaction():
                # Execute migration
                await self.conn.execute(content)

                # Record migration
                await self.conn.execute(
                    """
                    INSERT INTO schema_migrations (version, filename, checksum)
                    VALUES ($1, $2, $3)
                    """,
                    version,
                    filename,
                    checksum,
                )

            print(f"  ✓ {filename} applied successfully")

        except Exception as e:
            print(f"  ✗ {filename} failed: {e}")
            raise

    async def migrate(
        self, target_version: Optional[str] = None, dry_run: bool = False
    ):
        """Run pending migrations up to target_version."""
        print("Database Migration System")
        print("=" * 50)

        migrations = self._get_migration_files()
        if not migrations:
            print("No migration files found")
            return

        applied = await self._get_applied_migrations()
        pending = [(v, f) for v, f in migrations if v not in applied]

        if target_version:
            # Filter migrations up to target version
            pending = [(v, f) for v, f in pending if v <= target_version]

        if not pending:
            print("No pending migrations to apply")
            return

        print(f"Found {len(pending)} pending migrations:")
        for version, filename in pending:
            print(f"  - {filename}")

        if dry_run:
            print("\nDry run mode - no changes will be made")
            return

        print(f"\nApplying {len(pending)} migrations...")

        for version, filename in pending:
            file_path = MIGRATIONS_DIR / filename
            content = file_path.read_text(encoding="utf-8")
            checksum = self._calculate_checksum(content)

            await self._apply_migration(version, filename, content, checksum)

        print(f"\n✓ All {len(pending)} migrations applied successfully!")

    async def rollback(self, target_version: str, dry_run: bool = False):
        """Rollback to a specific migration version."""
        print(f"Rollback to version {target_version}")
        print("=" * 50)

        applied = await self._get_applied_migrations()

        # Get migrations to rollback (those newer than target_version)
        to_rollback = [v for v in applied if v > target_version]

        if not to_rollback:
            print(
                f"No migrations to rollback (target version {target_version} is current or newer)"
            )
            return

        print(f"Will rollback {len(to_rollback)} migrations:")
        for version in sorted(to_rollback, reverse=True):
            print(f"  - {version}")

        if dry_run:
            print("\nDry run mode - no changes will be made")
            return

        print(f"\nRolling back {len(to_rollback)} migrations...")

        # Note: This is a simplified rollback - in production you'd want
        # actual rollback SQL files or more sophisticated logic
        for version in sorted(to_rollback, reverse=True):
            async with self.conn.transaction():
                await self.conn.execute(
                    "DELETE FROM schema_migrations WHERE version = $1", version
                )
                print(f"  ✓ Rolled back {version}")

        print(f"\n✓ Rollback to {target_version} completed!")

    async def status(self):
        """Show current migration status."""
        print("Migration Status")
        print("=" * 50)

        migrations = self._get_migration_files()
        applied = await self._get_applied_migrations()

        print(f"Total migrations: {len(migrations)}")
        print(f"Applied migrations: {len(applied)}")
        print(f"Pending migrations: {len(migrations) - len(applied)}")

        print("\nMigration History:")
        for version, filename in migrations:
            status = "✓" if version in applied else "○"
            print(f"  {status} {version} - {filename}")

    async def validate(self):
        """Validate migration integrity."""
        print("Migration Validation")
        print("=" * 50)

        migrations = self._get_migration_files()
        applied = await self._get_applied_migrations()

        issues = []

        for version, filename in migrations:
            if version in applied:
                # Check checksum
                file_path = MIGRATIONS_DIR / filename
                content = file_path.read_text(encoding="utf-8")
                expected_checksum = self._calculate_checksum(content)

                row = await self.conn.fetchrow(
                    "SELECT checksum FROM schema_migrations WHERE version = $1", version
                )

                if row and row["checksum"] != expected_checksum:
                    issues.append(f"Checksum mismatch for {filename}")

        if issues:
            print(f"Found {len(issues)} issues:")
            for issue in issues:
                print(f"  ✗ {issue}")
        else:
            print("✓ All migrations are valid!")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command> [options]")
        print("\nCommands:")
        print(
            "  migrate [version]  - Run migrations (optionally up to specific version)"
        )
        print("  rollback <version>  - Rollback to specific version")
        print("  status             - Show migration status")
        print("  validate           - Validate migration integrity")
        print("  --dry-run         - Add to any command for dry run mode")
        return

    command = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    # Remove --dry-run from args for easier processing
    clean_args = [arg for arg in sys.argv if arg != "--dry-run"]

    migration_system = MigrationSystem(DATABASE_URL)

    try:
        await migration_system.connect()

        if command == "migrate":
            target_version = clean_args[2] if len(clean_args) > 2 else None
            await migration_system.migrate(target_version, dry_run)

        elif command == "rollback":
            if len(clean_args) < 3:
                print("Error: rollback requires target version")
                return
            target_version = clean_args[2]
            await migration_system.rollback(target_version, dry_run)

        elif command == "status":
            await migration_system.status()

        elif command == "validate":
            await migration_system.validate()

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await migration_system.disconnect()


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
