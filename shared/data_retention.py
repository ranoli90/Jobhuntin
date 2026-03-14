"""Data Retention Policies for GDPR compliance and storage optimization.

This module defines retention periods for different data types and provides
methods to check if data exceeds retention and to get data eligible for deletion.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from shared.logging_config import get_logger

logger = get_logger("sorce.data_retention")


class DataType(StrEnum):
    """Data types that can be retained with different policies."""

    SESSION_LOGS = "session_logs"
    ANALYTICS_EVENTS = "analytics_events"
    APPLICATION_DATA = "application_data"
    UPLOADED_RESUMES = "uploaded_resumes"
    API_LOGS = "api_logs"


class DeleteMode(StrEnum):
    """Mode of deletion."""

    HARD_DELETE = "hard_delete"  # Permanent deletion
    SOFT_DELETE = "soft_delete"  # Archive before deletion


@dataclass
class RetentionPolicy:
    """Defines retention policy for a data type."""

    data_type: DataType
    retention_days: int
    description: str
    legal_basis: str = ""  # e.g., "GDPR Art. 6(1)(a)", "Legitimate interest"
    allow_soft_delete: bool = True
    batch_size: int = 1000
    requires_archive: bool = False


@dataclass
class RetentionConfig:
    """Configuration for data retention settings."""

    # Retention periods in days (can be overridden by env vars)
    session_logs_days: int = 90
    analytics_events_days: int = 365
    application_data_days: int = 30  # After account deletion
    uploaded_resumes_days: int = 0  # 0 = indefinite (duration of account)
    api_logs_days: int = 90

    # Delete mode settings
    default_delete_mode: DeleteMode = DeleteMode.SOFT_DELETE

    # Batch processing settings
    batch_size: int = 1000

    # Schedule settings
    run_interval_hours: int = 24  # Daily run by default

    # Archive settings
    archive_before_delete: bool = True


class DataRetentionPolicy:
    """Main class for managing data retention policies.

    Provides methods to:
    - Get retention period for a data type
    - Check if data exceeds retention
    - Get data eligible for deletion
    """

    # Default retention policies
    DEFAULT_POLICIES: dict[DataType, RetentionPolicy] = {
        DataType.SESSION_LOGS: RetentionPolicy(
            data_type=DataType.SESSION_LOGS,
            retention_days=90,
            description="Session logs for security auditing",
            legal_basis="Legitimate interest - Security monitoring",
            batch_size=5000,
        ),
        DataType.ANALYTICS_EVENTS: RetentionPolicy(
            data_type=DataType.ANALYTICS_EVENTS,
            retention_days=365,
            description="Analytics events for product improvement",
            legal_basis="Consent - Analytics tracking",
            batch_size=10000,
        ),
        DataType.APPLICATION_DATA: RetentionPolicy(
            data_type=DataType.APPLICATION_DATA,
            retention_days=30,
            description="Job application data after account deletion",
            legal_basis="GDPR Art. 17 - Right to erasure",
            allow_soft_delete=True,
            batch_size=1000,
            requires_archive=True,
        ),
        DataType.UPLOADED_RESUMES: RetentionPolicy(
            data_type=DataType.UPLOADED_RESUMES,
            retention_days=0,  # 0 = indefinite
            description="Uploaded resumes - retained while account active",
            legal_basis="Contract performance",
            allow_soft_delete=True,
            batch_size=500,
            requires_archive=True,
        ),
        DataType.API_LOGS: RetentionPolicy(
            data_type=DataType.API_LOGS,
            retention_days=90,
            description="API request logs for debugging and security",
            legal_basis="Legitimate interest - API monitoring",
            batch_size=10000,
        ),
    }

    def __init__(self, config: RetentionConfig | None = None):
        """Initialize with optional custom configuration."""
        self._config = config or self._load_config_from_env()
        self._policies = self._build_policies()

    def _load_config_from_env(self) -> RetentionConfig:
        """Load configuration from environment variables."""
        return RetentionConfig(
            session_logs_days=int(
                os.environ.get("RETENTION_SESSION_LOGS_DAYS", "90")
            ),
            analytics_events_days=int(
                os.environ.get("RETENTION_ANALYTICS_EVENTS_DAYS", "365")
            ),
            application_data_days=int(
                os.environ.get("RETENTION_APPLICATION_DATA_DAYS", "30")
            ),
            uploaded_resumes_days=int(
                os.environ.get("RETENTION_UPLOADED_RESUMES_DAYS", "0")
            ),
            api_logs_days=int(os.environ.get("RETENTION_API_LOGS_DAYS", "90")),
            default_delete_mode=DeleteMode(
                os.environ.get("RETENTION_DEFAULT_DELETE_MODE", "soft_delete")
            ),
            batch_size=int(os.environ.get("RETENTION_BATCH_SIZE", "1000")),
            run_interval_hours=int(
                os.environ.get("RETENTION_RUN_INTERVAL_HOURS", "24")
            ),
            archive_before_delete=os.environ.get(
                "RETENTION_ARCHIVE_BEFORE_DELETE", "true"
            ).lower()
            == "true",
        )

    def _build_policies(self) -> dict[DataType, RetentionPolicy]:
        """Build policies from configuration."""
        return {
            DataType.SESSION_LOGS: RetentionPolicy(
                data_type=DataType.SESSION_LOGS,
                retention_days=self._config.session_logs_days,
                description="Session logs for security auditing",
                legal_basis="Legitimate interest - Security monitoring",
                batch_size=self._config.batch_size,
            ),
            DataType.ANALYTICS_EVENTS: RetentionPolicy(
                data_type=DataType.ANALYTICS_EVENTS,
                retention_days=self._config.analytics_events_days,
                description="Analytics events for product improvement",
                legal_basis="Consent - Analytics tracking",
                batch_size=self._config.batch_size,
            ),
            DataType.APPLICATION_DATA: RetentionPolicy(
                data_type=DataType.APPLICATION_DATA,
                retention_days=self._config.application_data_days,
                description="Job application data after account deletion",
                legal_basis="GDPR Art. 17 - Right to erasure",
                allow_soft_delete=True,
                batch_size=self._config.batch_size,
                requires_archive=self._config.archive_before_delete,
            ),
            DataType.UPLOADED_RESUMES: RetentionPolicy(
                data_type=DataType.UPLOADED_RESUMES,
                retention_days=self._config.uploaded_resumes_days,
                description="Uploaded resumes - retained while account active",
                legal_basis="Contract performance",
                allow_soft_delete=True,
                batch_size=self._config.batch_size,
                requires_archive=self._config.archive_before_delete,
            ),
            DataType.API_LOGS: RetentionPolicy(
                data_type=DataType.API_LOGS,
                retention_days=self._config.api_logs_days,
                description="API request logs for debugging and security",
                legal_basis="Legitimate interest - API monitoring",
                batch_size=self._config.batch_size,
            ),
        }

    @property
    def config(self) -> RetentionConfig:
        """Get the retention configuration."""
        return self._config

    def get_retention_period(self, data_type: DataType) -> int:
        """Get retention period in days for a data type.

        Args:
            data_type: The type of data to get retention for

        Returns:
            Retention period in days (0 = indefinite)
        """
        policy = self._policies.get(data_type)
        if policy:
            return policy.retention_days

        # Fallback to defaults
        default_policy = self.DEFAULT_POLICIES.get(data_type)
        return default_policy.retention_days if default_policy else 0

    def get_policy(self, data_type: DataType) -> RetentionPolicy | None:
        """Get the full retention policy for a data type.

        Args:
            data_type: The type of data to get policy for

        Returns:
            RetentionPolicy or None if not found
        """
        return self._policies.get(data_type)

    def exceeds_retention(
        self, data_type: DataType, created_at: datetime, deleted_at: datetime | None = None
    ) -> bool:
        """Check if data exceeds its retention period.

        Args:
            data_type: The type of data
            created_at: When the data was created
            deleted_at: When the data was soft-deleted (for application data)

        Returns:
            True if data exceeds retention period
        """
        retention_days = self.get_retention_period(data_type)

        # 0 = indefinite retention
        if retention_days == 0:
            return False

        # For soft-deleted data, check from deletion date
        reference_date = deleted_at if deleted_at else datetime.utcnow()
        cutoff_date = reference_date - timedelta(days=retention_days)

        return created_at < cutoff_date

    def get_cutoff_date(self, data_type: DataType) -> datetime:
        """Get the cutoff date for data deletion.

        Args:
            data_type: The type of data

        Returns:
            datetime representing the cutoff - data older than this is eligible
        """
        retention_days = self.get_retention_period(data_type)

        if retention_days == 0:
            # Return epoch for indefinite retention
            return datetime(1970, 1, 1)

        return datetime.utcnow() - timedelta(days=retention_days)

    def get_all_policies(self) -> list[RetentionPolicy]:
        """Get all configured retention policies.

        Returns:
            List of all RetentionPolicy objects
        """
        return list(self._policies.values())

    def is_active_account_data(self, data_type: DataType) -> bool:
        """Check if data type is retained while account is active.

        Args:
            data_type: The type of data

        Returns:
            True if data is retained while account is active
        """
        return data_type in [
            DataType.UPLOADED_RESUMES,
        ]

    def get_deletion_query(
        self, data_type: DataType, id_column: str = "id"
    ) -> tuple[str, dict[str, Any]]:
        """Get SQL query to find data eligible for deletion.

        Args:
            data_type: The type of data to query
            id_column: The primary key column name

        Returns:
            Tuple of (query, parameters)
        """
        cutoff = self.get_cutoff_date(data_type)

        queries = {
            DataType.SESSION_LOGS: (
                f"SELECT {id_column} FROM session_logs WHERE created_at < $1",
                {"cutoff": cutoff},
            ),
            DataType.ANALYTICS_EVENTS: (
                f"SELECT {id_column} FROM analytics_events WHERE created_at < $1",
                {"cutoff": cutoff},
            ),
            DataType.APPLICATION_DATA: (
                f"SELECT {id_column} FROM applications WHERE deleted_at IS NOT NULL AND deleted_at < $1",
                {"cutoff": cutoff},
            ),
            DataType.UPLOADED_RESUMES: (
                f"SELECT {id_column} FROM uploaded_resumes WHERE deleted_at IS NOT NULL AND deleted_at < $1",
                {"cutoff": cutoff},
            ),
            DataType.API_LOGS: (
                f"SELECT {id_column} FROM api_logs WHERE created_at < $1",
                {"cutoff": cutoff},
            ),
        }

        if data_type in queries:
            return queries[data_type]

        raise ValueError(f"Unknown data type: {data_type}")

    def get_count_query(self, data_type: DataType) -> tuple[str, dict[str, Any]]:
        """Get SQL query to count data eligible for deletion.

        Args:
            data_type: The type of data to count

        Returns:
            Tuple of (query, parameters)
        """
        cutoff = self.get_cutoff_date(data_type)

        queries = {
            DataType.SESSION_LOGS: (
                "SELECT COUNT(*) FROM session_logs WHERE created_at < $1",
                {"cutoff": cutoff},
            ),
            DataType.ANALYTICS_EVENTS: (
                "SELECT COUNT(*) FROM analytics_events WHERE created_at < $1",
                {"cutoff": cutoff},
            ),
            DataType.APPLICATION_DATA: (
                "SELECT COUNT(*) FROM applications WHERE deleted_at IS NOT NULL AND deleted_at < $1",
                {"cutoff": cutoff},
            ),
            DataType.UPLOADED_RESUMES: (
                "SELECT COUNT(*) FROM uploaded_resumes WHERE deleted_at IS NOT NULL AND deleted_at < $1",
                {"cutoff": cutoff},
            ),
            DataType.API_LOGS: (
                "SELECT COUNT(*) FROM api_logs WHERE created_at < $1",
                {"cutoff": cutoff},
            ),
        }

        if data_type in queries:
            return queries[data_type]

        raise ValueError(f"Unknown data type: {data_type}")


# Global instance for easy import
_default_policy: DataRetentionPolicy | None = None


def get_retention_policy() -> DataRetentionPolicy:
    """Get the global retention policy instance."""
    global _default_policy
    if _default_policy is None:
        _default_policy = DataRetentionPolicy()
    return _default_policy
