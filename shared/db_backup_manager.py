"""Database backup automation and management system.

Provides:
- Automated backup scheduling
- Backup verification and integrity checking
- Backup retention policies
- Point-in-time recovery
- Backup monitoring and alerting

Usage:
    from shared.db_backup_manager import BackupManager

    backup_manager = BackupManager(db_pool)
    await backup_manager.create_backup("daily")
"""

from __future__ import annotations

import asyncio
import gzip
import os
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg

from shared.alerting import AlertSeverity, get_alert_manager
from shared.logging_config import get_logger

logger = get_logger("sorce.db_backup")


class BackupType(Enum):
    """Backup schedule types."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


class BackupStatus(Enum):
    """Backup operation status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFYING = "verifying"


@dataclass
class BackupConfig:
    """Backup configuration."""

    backup_type: BackupType
    retention_days: int
    compression_enabled: bool = True
    encryption_enabled: bool = False
    include_schema: bool = True
    include_data: bool = True
    exclude_tables: List[str] = field(default_factory=list)
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BackupRecord:
    """Backup operation record."""

    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    file_path: Optional[str] = None
    file_size_mb: Optional[float] = None
    compressed_size_mb: Optional[float] = None
    tables_count: Optional[int] = None
    rows_count: Optional[int] = None
    error_message: Optional[str] = None
    checksum: Optional[str] = None
    verified: bool = False
    created_at: float = field(default_factory=time.time)


@dataclass
class BackupStats:
    """Backup statistics."""

    total_backups: int
    successful_backups: int
    failed_backups: int
    avg_backup_time_minutes: float
    avg_backup_size_mb: float
    total_storage_used_mb: float
    last_backup_time: Optional[float] = None
    next_backup_time: Optional[float] = None


class BackupManager:
    """Advanced database backup management system."""

    def __init__(self, db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None):
        self.db_pool = db_pool
        self.alert_manager = alert_manager or get_alert_manager()

        # Backup configuration
        self.backup_configs: Dict[BackupType, BackupConfig] = {
            BackupType.HOURLY: BackupConfig(
                backup_type=BackupType.HOURLY,
                retention_days=7,
                compression_enabled=True,
                include_schema=True,
                include_data=True,
            ),
            BackupType.DAILY: BackupConfig(
                backup_type=BackupType.DAILY,
                retention_days=30,
                compression_enabled=True,
                include_schema=True,
                include_data=True,
            ),
            BackupType.WEEKLY: BackupConfig(
                backup_type=BackupType.WEEKLY,
                retention_days=90,
                compression_enabled=True,
                include_schema=True,
                include_data=True,
            ),
            BackupType.MONTHLY: BackupConfig(
                backup_type=BackupType.MONTHLY,
                retention_days=365,
                compression_enabled=True,
                include_schema=True,
                include_data=True,
            ),
            BackupType.ON_DEMAND: BackupConfig(
                backup_type=BackupType.ON_DEMAND,
                retention_days=90,
                compression_enabled=True,
                include_schema=True,
                include_data=True,
            ),
        }

        # Backup storage
        self.backup_records: deque[BackupRecord] = deque(maxlen=1000)
        self.backup_directory = Path(
            "/tmp/db_backups"
        )  # Configure based on environment

        # Active backup operations
        self.active_backups: Dict[str, asyncio.Task] = {}

        # Backup scheduling
        self._scheduler_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Ensure backup directory exists
        self.backup_directory.mkdir(parents=True, exist_ok=True)

    async def create_backup(
        self,
        backup_type: BackupType = BackupType.DAILY,
        custom_config: Optional[BackupConfig] = None,
    ) -> BackupRecord:
        """Create a database backup."""
        config = custom_config or self.backup_configs[backup_type]
        backup_id = self._generate_backup_id()

        # Create backup record
        backup = BackupRecord(
            backup_id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            start_time=time.time(),
        )

        # Store record
        self.backup_records.append(backup)

        # Start backup operation
        task = asyncio.create_task(self._execute_backup(backup, config))
        self.active_backups[backup_id] = task

        try:
            # Wait for completion
            result_backup = await task
            return result_backup
        finally:
            self.active_backups.pop(backup_id, None)

    async def _execute_backup(
        self, backup: BackupRecord, config: BackupConfig
    ) -> BackupRecord:
        """Execute backup operation."""
        backup.status = BackupStatus.RUNNING

        try:
            # Get database connection info
            db_info = await self._get_database_info()

            # Generate backup file path
            timestamp = datetime.fromtimestamp(backup.start_time).strftime(
                "%Y%m%d_%H%M%S"
            )
            filename = f"{backup.backup_type.value}_{backup.backup_id}_{timestamp}.sql"
            if config.compression_enabled:
                filename += ".gz"

            backup_file = self.backup_directory / filename

            # Build pg_dump command
            cmd = self._build_backup_command(db_info, config, backup_file)

            # Execute backup
            start_time = time.time()
            result = await self._run_backup_command(cmd, backup_file, config)
            duration = time.time() - start_time

            # Update backup record
            backup.end_time = time.time()
            backup.duration_seconds = duration
            backup.file_path = str(backup_file)

            if result["success"]:
                backup.status = BackupStatus.COMPLETED
                backup.file_size_mb = result["size_mb"]
                backup.compressed_size_mb = result["compressed_size_mb"]
                backup.tables_count = result["tables_count"]
                backup.rows_count = result["rows_count"]
                backup.checksum = result["checksum"]

                # Verify backup
                await self._verify_backup(backup)

                logger.info(f"Backup completed successfully: {backup.backup_id}")
            else:
                backup.status = BackupStatus.FAILED
                backup.error_message = result["error"]

                # Alert on failure
                await self.alert_manager.trigger_alert(
                    name="backup_failure",
                    severity=AlertSeverity.ERROR,
                    message=f"Backup failed: {backup.backup_id} - {result['error']}",
                    context={"backup_type": backup.backup_type.value},
                )

                logger.error(f"Backup failed: {backup.backup_id} - {result['error']}")

            return backup

        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            backup.end_time = time.time()
            backup.duration_seconds = time.time() - backup.start_time

            # Alert on failure
            await self.alert_manager.trigger_alert(
                name="backup_failure",
                severity=AlertSeverity.CRITICAL,
                message=f"Backup error: {backup.backup_id} - {str(e)}",
                context={"backup_type": backup.backup_type.value},
            )

            logger.error(f"Backup error: {backup.backup_id} - {str(e)}")
            return backup

    async def _get_database_info(self) -> Dict[str, str]:
        """Get database connection information."""
        # This should be configured based on your environment
        # For security, these should come from environment variables
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "jobhuntin"),
            "username": os.getenv("DB_USER", "jobhuntin_user"),
            "password": os.getenv("DB_PASSWORD", ""),
        }

    def _build_backup_command(
        self, db_info: Dict[str, str], config: BackupConfig, backup_file: Path
    ) -> List[str]:
        """Build pg_dump command."""
        cmd = ["pg_dump"]

        # Connection options
        cmd.extend(["-h", db_info["host"]])
        cmd.extend(["-p", db_info["port"]])
        cmd.extend(["-U", db_info["username"]])
        cmd.extend(["-d", db_info["database"]])

        # Format options
        if config.compression_enabled:
            cmd.extend(["-Z", "9"])  # Maximum compression
        else:
            cmd.extend(["-F", "p"])  # Plain SQL format

        # Content options
        if config.include_schema and not config.include_data:
            cmd.append("--schema-only")
        elif not config.include_schema and config.include_data:
            cmd.append("--data-only")

        # Exclude tables
        for table in config.exclude_tables:
            cmd.extend(["--exclude-table", table])

        # Custom options
        if config.custom_options:
            for key, value in config.custom_options.items():
                cmd.extend([f"--{key}", str(value)])

        # Output file
        cmd.extend(["-f", str(backup_file)])

        return cmd

    async def _run_backup_command(
        self, cmd: List[str], backup_file: Path, config: BackupConfig
    ) -> Dict[str, Any]:
        """Execute backup command and return results."""
        try:
            # Set environment variables for authentication
            env = os.environ.copy()
            env["PGPASSWORD"] = os.getenv("DB_PASSWORD", "")

            # Run backup command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode()
                    if stderr
                    else f"Exit code: {process.returncode}",
                }

            # Get file information
            file_size = backup_file.stat().st_size / 1024 / 1024  # MB

            # Count tables and rows if data backup
            tables_count = 0
            rows_count = 0

            if config.include_data:
                try:
                    async with self.db_pool.acquire() as conn:
                        # Count tables
                        tables_count = await conn.fetchval("""
                            SELECT COUNT(*) FROM information_schema.tables 
                            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                        """)

                        # Estimate total rows
                        rows_count = (
                            await conn.fetchval("""
                            SELECT SUM(n_tup_ins) FROM pg_stat_user_tables
                        """)
                            or 0
                        )
                except Exception as e:
                    logger.warning(f"Failed to get table/row counts: {e}")

            # Calculate checksum
            checksum = await self._calculate_checksum(backup_file)

            # Get compressed size if applicable
            compressed_size = file_size
            if config.compression_enabled and backup_file.suffix == ".gz":
                # For compressed files, the file_size is already compressed
                compressed_size = file_size

            return {
                "success": True,
                "size_mb": file_size,
                "compressed_size_mb": compressed_size,
                "tables_count": tables_count,
                "rows_count": rows_count,
                "checksum": checksum,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of backup file."""
        import hashlib

        hash_sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    async def _verify_backup(self, backup: BackupRecord) -> None:
        """Verify backup integrity."""
        if not backup.file_path or not os.path.exists(backup.file_path):
            return

        backup.status = BackupStatus.VERIFYING

        try:
            backup_path = Path(backup.file_path)

            # Check file exists and has content
            if backup_path.stat().st_size == 0:
                raise ValueError("Backup file is empty")

            # Verify checksum if available
            if backup.checksum:
                calculated_checksum = await self._calculate_checksum(backup_path)
                if calculated_checksum != backup.checksum:
                    raise ValueError("Backup checksum mismatch")

            # For compressed backups, try to decompress first few bytes
            if backup_path.suffix == ".gz":
                try:
                    with gzip.open(backup_path, "rb") as f:
                        f.read(1024)  # Read first 1KB to verify it's valid gzip
                except Exception as e:
                    raise ValueError(f"Invalid gzip file: {e}")

            backup.verified = True
            backup.status = BackupStatus.COMPLETED

            logger.info(f"Backup verified successfully: {backup.backup_id}")

        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = f"Verification failed: {str(e)}"

            await self.alert_manager.trigger_alert(
                name="backup_verification_failed",
                severity=AlertSeverity.ERROR,
                message=f"Backup verification failed: {backup.backup_id} - {str(e)}",
                context={"backup_type": backup.backup_type.value},
            )

            logger.error(f"Backup verification failed: {backup.backup_id} - {str(e)}")

    async def restore_backup(
        self,
        backup_id: str,
        target_database: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Restore database from backup."""
        # Find backup record
        backup = None
        for record in self.backup_records:
            if record.backup_id == backup_id:
                backup = record
                break

        if not backup:
            raise ValueError(f"Backup not found: {backup_id}")

        if backup.status != BackupStatus.COMPLETED or not backup.verified:
            raise ValueError(f"Backup not ready for restore: {backup_id}")

        if not backup.file_path or not os.path.exists(backup.file_path):
            raise ValueError(f"Backup file not found: {backup.file_path}")

        # Get database info
        db_info = await self._get_database_info()
        if target_database:
            db_info["database"] = target_database

        # Build restore command
        restore_cmd = self._build_restore_command(db_info, backup.file_path)

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "command": " ".join(restore_cmd),
                "backup_id": backup_id,
            }

        try:
            # Set environment variables
            env = os.environ.copy()
            env["PGPASSWORD"] = os.getenv("DB_PASSWORD", "")

            # Run restore command
            process = await asyncio.create_subprocess_exec(
                *restore_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode()
                    if stderr
                    else f"Exit code: {process.returncode}",
                    "backup_id": backup_id,
                }

            logger.info(f"Database restored successfully from backup: {backup_id}")

            return {
                "success": True,
                "backup_id": backup_id,
                "target_database": target_database,
                "rows_restored": backup.rows_count,
            }

        except Exception as e:
            logger.error(f"Database restore failed: {backup_id} - {str(e)}")
            return {"success": False, "error": str(e), "backup_id": backup_id}

    def _build_restore_command(
        self, db_info: Dict[str, str], backup_file: Path
    ) -> List[str]:
        """Build psql restore command."""
        cmd = ["psql"]

        # Connection options
        cmd.extend(["-h", db_info["host"]])
        cmd.extend(["-p", db_info["port"]])
        cmd.extend(["-U", db_info["username"]])
        cmd.extend(["-d", db_info["database"]])

        # Input file
        if backup_file.suffix == ".gz":
            # Use gunzip to decompress
            cmd = ["gunzip", "-c", str(backup_file), "|"] + cmd
        else:
            cmd.extend(["-f", str(backup_file)])

        return cmd

    def _generate_backup_id(self) -> str:
        """Generate unique backup ID."""
        import uuid

        return str(uuid.uuid4())[:8]

    async def list_backups(
        self,
        backup_type: Optional[BackupType] = None,
        status: Optional[BackupStatus] = None,
        limit: int = 100,
    ) -> List[BackupRecord]:
        """List backups with optional filtering."""
        backups = list(self.backup_records)

        # Apply filters
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]

        if status:
            backups = [b for b in backups if b.status == status]

        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b.created_at, reverse=True)

        return backups[:limit]

    async def delete_backup(self, backup_id: str) -> bool:
        """Delete backup file and record."""
        backup = None
        for record in self.backup_records:
            if record.backup_id == backup_id:
                backup = record
                break

        if not backup:
            return False

        # Delete file
        if backup.file_path and os.path.exists(backup.file_path):
            os.remove(backup.file_path)

        # Remove from records
        self.backup_records = deque(
            (r for r in self.backup_records if r.backup_id != backup_id), maxlen=1000
        )

        logger.info(f"Backup deleted: {backup_id}")
        return True

    async def cleanup_old_backups(self) -> int:
        """Clean up old backups based on retention policies."""
        deleted_count = 0
        current_time = time.time()

        for backup in list(self.backup_records):
            config = self.backup_configs[backup.backup_type]
            retention_seconds = config.retention_days * 24 * 60 * 60

            if current_time - backup.created_at > retention_seconds:
                await self.delete_backup(backup.backup_id)
                deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backups")

        return deleted_count

    def get_backup_stats(self) -> BackupStats:
        """Get backup statistics."""
        backups = list(self.backup_records)

        if not backups:
            return BackupStats(
                total_backups=0,
                successful_backups=0,
                failed_backups=0,
                avg_backup_time_minutes=0,
                avg_backup_size_mb=0,
                total_storage_used_mb=0,
            )

        successful = [b for b in backups if b.status == BackupStatus.COMPLETED]
        failed = [b for b in backups if b.status == BackupStatus.FAILED]

        # Calculate averages
        avg_time = (
            sum(b.duration_seconds or 0 for b in successful) / len(successful)
            if successful
            else 0
        )
        avg_size = (
            sum(b.file_size_mb or 0 for b in successful) / len(successful)
            if successful
            else 0
        )
        total_storage = sum(b.file_size_mb or 0 for b in successful)

        # Get last and next backup times
        last_backup = max(backups, key=lambda b: b.created_at)
        last_backup_time = last_backup.created_at

        # Estimate next backup time based on type
        next_backup_time = None
        if last_backup.backup_type == BackupType.DAILY:
            next_backup_time = last_backup_time + (24 * 60 * 60)
        elif last_backup.backup_type == BackupType.HOURLY:
            next_backup_time = last_backup_time + (60 * 60)

        return BackupStats(
            total_backups=len(backups),
            successful_backups=len(successful),
            failed_backups=len(failed),
            avg_backup_time_minutes=avg_time / 60,
            avg_backup_size_mb=avg_size,
            total_storage_used_mb=total_storage,
            last_backup_time=last_backup_time,
            next_backup_time=next_backup_time,
        )

    async def start_scheduler(self) -> asyncio.Task:
        """Start backup scheduler."""

        async def scheduler():
            while True:
                try:
                    current_time = datetime.now()

                    # Schedule hourly backups
                    if current_time.minute == 0:
                        await self.create_backup(BackupType.HOURLY)

                    # Schedule daily backups at 2 AM
                    if current_time.hour == 2 and current_time.minute == 0:
                        await self.create_backup(BackupType.DAILY)

                    # Schedule weekly backups on Sunday at 3 AM
                    if (
                        current_time.weekday() == 6
                        and current_time.hour == 3
                        and current_time.minute == 0
                    ):
                        await self.create_backup(BackupType.WEEKLY)

                    # Schedule monthly backups on 1st at 4 AM
                    if (
                        current_time.day == 1
                        and current_time.hour == 4
                        and current_time.minute == 0
                    ):
                        await self.create_backup(BackupType.MONTHLY)

                    # Wait until next minute
                    await asyncio.sleep(60)

                except Exception as e:
                    logger.error(f"Backup scheduler error: {e}")
                    await asyncio.sleep(60)

        self._scheduler_task = asyncio.create_task(scheduler)
        return self._scheduler_task

    async def start_cleanup_scheduler(self) -> asyncio.Task:
        """Start cleanup scheduler."""

        async def cleanup():
            while True:
                try:
                    await self.cleanup_old_backups()
                    # Run cleanup every 6 hours
                    await asyncio.sleep(6 * 60 * 60)
                except Exception as e:
                    logger.error(f"Cleanup scheduler error: {e}")
                    await asyncio.sleep(6 * 60 * 60)

        self._cleanup_task = asyncio.create_task(cleanup)
        return self._cleanup_task

    async def stop_schedulers(self) -> None:
        """Stop backup schedulers."""
        if self._scheduler_task:
            self._scheduler_task.cancel()
            self._scheduler_task = None

        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


# Global backup manager instance
_backup_manager: BackupManager | None = None


def get_backup_manager() -> BackupManager:
    """Get global backup manager instance."""
    global _backup_manager
    if _backup_manager is None:
        raise RuntimeError(
            "Backup manager not initialized. Call init_backup_manager() first."
        )
    return _backup_manager


async def init_backup_manager(
    db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None
) -> BackupManager:
    """Initialize global backup manager."""
    global _backup_manager
    _backup_manager = BackupManager(db_pool, alert_manager)
    return _backup_manager
