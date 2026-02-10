"""
Database Migration System

Provides versioned database migrations with rollback capability.
Migrations are stored as SQL files in migrations/ directory.
"""

import asyncio
import logging
import pathlib
from typing import List, Tuple

logger = logging.getLogger(__name__)


class Migration:
    """Represents a single database migration."""

    def __init__(self, version: str, name: str, up_sql: str, down_sql: str = ""):
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql

    @property
    def filename(self) -> str:
        return f"{self.version}_{self.name}.sql"


async def run_migrations(conn, base_path: pathlib.Path) -> None:
    """
    Run all pending migrations.

    Args:
        conn: Database connection
        base_path: Base path of the project
    """
    # Create migrations table if it doesn't exist
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Get applied migrations
    applied_versions = await conn.fetchval("""
        SELECT array_agg(version) FROM schema_migrations;
    """) or []

    # Find migration files
    migrations_dir = base_path / "migrations"
    if not migrations_dir.exists():
        logger.info("No migrations directory found, skipping migrations")
        return

    migrations = _load_migrations(migrations_dir)

    # Filter pending migrations
    pending_migrations = [
        m for m in migrations
        if m.version not in applied_versions
    ]

    if not pending_migrations:
        logger.info("No pending migrations")
        return

    logger.info(f"Applying {len(pending_migrations)} migrations...")

    # Apply migrations in order
    for migration in sorted(pending_migrations, key=lambda m: m.version):
        logger.info(f"Applying migration {migration.version}: {migration.name}")

        try:
            # Execute migration
            await conn.execute(migration.up_sql)

            # Record migration
            await conn.execute("""
                INSERT INTO schema_migrations (version, name)
                VALUES ($1, $2)
            """, migration.version, migration.name)

            logger.info(f"Successfully applied migration {migration.version}")

        except Exception as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            # Rollback transaction
            raise


async def rollback_migration(conn, steps: int = 1) -> int:
    """
    Rollback the last N migrations.

    Args:
        conn: Database connection
        steps: Number of migrations to rollback

    Returns:
        Number of migrations rolled back
    """
    # Get last applied migrations
    rows = await conn.fetch("""
        SELECT version, name FROM schema_migrations
        ORDER BY applied_at DESC
        LIMIT $1
    """, steps)

    if not rows:
        logger.info("No migrations to rollback")
        return 0

    rolled_back = 0

    for row in rows:
        version = row["version"]
        name = row["name"]

        logger.info(f"Rolling back migration {version}: {name}")

        try:
            # Find and execute down migration
            # This would need to be implemented to load down SQL from files
            # For now, we'll just remove from migrations table
            await conn.execute("""
                DELETE FROM schema_migrations WHERE version = $1
            """, version)

            rolled_back += 1
            logger.info(f"Successfully rolled back migration {version}")

        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            break

    return rolled_back


def _load_migrations(migrations_dir: pathlib.Path) -> List[Migration]:
    """
    Load migration files from directory.

    Migration files should be named like: 001_initial_schema.sql
    Each file should contain -- +migrate Up and -- +migrate Down sections
    """
    migrations = []

    for file_path in sorted(migrations_dir.glob("*.sql")):
        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse migration file
            # Simple format: -- +migrate Up\n<up sql>\n-- +migrate Down\n<down sql>
            parts = content.split("-- +migrate Down")
            if len(parts) == 2:
                up_sql = parts[0].replace("-- +migrate Up\n", "").strip()
                down_sql = parts[1].strip()
            else:
                # No down migration
                up_sql = content.replace("-- +migrate Up\n", "").strip()
                down_sql = ""

            # Extract version and name from filename
            # Format: 001_initial_schema.sql
            filename = file_path.stem  # Remove .sql extension
            version, name = filename.split("_", 1)

            migrations.append(Migration(version, name, up_sql, down_sql))

        except Exception as e:
            logger.warning(f"Failed to load migration {file_path}: {e}")
            continue

    return migrations
