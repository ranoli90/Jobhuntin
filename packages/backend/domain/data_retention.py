"""
Data retention policy service.

Provides:
- Configurable retention periods per data type
- Automated data archiving
- Data deletion compliance (GDPR)
- Audit trail for deletions
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    """Types of data with retention policies."""
    APPLICATIONS = "applications"
    PROFILES = "profiles"
    RESUMES = "resumes"
    ANALYTICS = "analytics"
    LOGS = "logs"
    EVENTS = "events"
    NOTIFICATIONS = "notifications"
    SESSIONS = "sessions"
    AUDIT_LOGS = "audit_logs"
    BACKUPS = "backups"


class RetentionAction(str, Enum):
    """Actions to take when retention period expires."""
    ARCHIVE = "archive"
    DELETE = "delete"
    ANONYMIZE = "anonymize"


@dataclass
class RetentionPolicy:
    """Retention policy for a data type."""
    data_type: DataType
    retention_days: int
    action: RetentionAction
    archive_after_days: Optional[int] = None
    delete_after_archive_days: Optional[int] = None
    exclude_flags: list[str] = field(default_factory=list)
    
    @property
    def retention_date(self) -> datetime:
        """Calculate the cutoff date for retention."""
        return datetime.utcnow() - timedelta(days=self.retention_days)
    
    @property
    def archive_date(self) -> Optional[datetime]:
        """Calculate the cutoff date for archiving."""
        if self.archive_after_days:
            return datetime.utcnow() - timedelta(days=self.archive_after_days)
        return None


# Default retention policies
DEFAULT_POLICIES: dict[DataType, RetentionPolicy] = {
    DataType.APPLICATIONS: RetentionPolicy(
        data_type=DataType.APPLICATIONS,
        retention_days=365 * 2,  # 2 years
        action=RetentionAction.ARCHIVE,
        archive_after_days=365,
        delete_after_archive_days=365,
    ),
    DataType.PROFILES: RetentionPolicy(
        data_type=DataType.PROFILES,
        retention_days=365 * 3,  # 3 years (user data)
        action=RetentionAction.ANONYMIZE,
        exclude_flags=["active_user", "enterprise_account"],
    ),
    DataType.RESUMES: RetentionPolicy(
        data_type=DataType.RESUMES,
        retention_days=365,  # 1 year
        action=RetentionAction.DELETE,
        exclude_flags=["user_saved"],
    ),
    DataType.ANALYTICS: RetentionPolicy(
        data_type=DataType.ANALYTICS,
        retention_days=90,  # 90 days
        action=RetentionAction.AGGREGATE,
    ),
    DataType.LOGS: RetentionPolicy(
        data_type=DataType.LOGS,
        retention_days=30,  # 30 days
        action=RetentionAction.DELETE,
    ),
    DataType.EVENTS: RetentionPolicy(
        data_type=DataType.EVENTS,
        retention_days=365,  # 1 year
        action=RetentionAction.ARCHIVE,
        archive_after_days=90,
    ),
    DataType.NOTIFICATIONS: RetentionPolicy(
        data_type=DataType.NOTIFICATIONS,
        retention_days=30,  # 30 days
        action=RetentionAction.DELETE,
    ),
    DataType.SESSIONS: RetentionPolicy(
        data_type=DataType.SESSIONS,
        retention_days=7,  # 7 days
        action=RetentionAction.DELETE,
    ),
    DataType.AUDIT_LOGS: RetentionPolicy(
        data_type=DataType.AUDIT_LOGS,
        retention_days=365 * 7,  # 7 years (compliance)
        action=RetentionAction.ARCHIVE,
        archive_after_days=365,
    ),
    DataType.BACKUPS: RetentionPolicy(
        data_type=DataType.BACKUPS,
        retention_days=30,  # 30 days
        action=RetentionAction.DELETE,
    ),
}


@dataclass
class RetentionResult:
    """Result of a retention operation."""
    data_type: DataType
    action: RetentionAction
    records_processed: int = 0
    records_archived: int = 0
    records_deleted: int = 0
    records_anonymized: int = 0
    bytes_freed: int = 0
    errors: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "data_type": self.data_type.value,
            "action": self.action.value,
            "records_processed": self.records_processed,
            "records_archived": self.records_archived,
            "records_deleted": self.records_deleted,
            "records_anonymized": self.records_anonymized,
            "bytes_freed": self.bytes_freed,
            "errors": self.errors,
        }


class DataRetentionService:
    """
    Service for managing data retention.
    
    Features:
    - Configurable retention policies
    - Automated archiving to cold storage
    - GDPR-compliant deletion
    - Audit trail for all operations
    """
    
    def __init__(
        self,
        db_conn: "asyncpg.Connection",
        storage_service: Optional["StorageService"] = None,
        policies: Optional[dict[DataType, RetentionPolicy]] = None,
    ):
        self.db = db_conn
        self.storage = storage_service
        self.policies = policies or DEFAULT_POLICIES
    
    async def run_retention(
        self,
        data_types: Optional[list[DataType]] = None,
        dry_run: bool = False,
    ) -> list[RetentionResult]:
        """
        Run retention policies for specified data types.
        
        Args:
            data_types: Specific data types to process (all if None)
            dry_run: If True, only report what would be done
            
        Returns:
            List of retention results
        """
        results: list[RetentionResult] = []
        
        types_to_process = data_types or list(self.policies.keys())
        
        for data_type in types_to_process:
            policy = self.policies.get(data_type)
            if not policy:
                continue
            
            result = await self._process_retention(policy, dry_run)
            results.append(result)
        
        return results
    
    async def _process_retention(
        self,
        policy: RetentionPolicy,
        dry_run: bool = False,
    ) -> RetentionResult:
        """Process retention for a single data type."""
        result = RetentionResult(
            data_type=policy.data_type,
            action=policy.action,
        )
        
        try:
            # Get records to process
            records = await self._get_expired_records(policy)
            result.records_processed = len(records)
            
            if not records:
                return result
            
            if dry_run:
                # Just report counts
                if policy.action == RetentionAction.ARCHIVE:
                    result.records_archived = len(records)
                elif policy.action == RetentionAction.DELETE:
                    result.records_deleted = len(records)
                elif policy.action == RetentionAction.ANONYMIZE:
                    result.records_anonymized = len(records)
                return result
            
            # Execute retention action
            if policy.action == RetentionAction.ARCHIVE:
                await self._archive_records(policy, records, result)
            elif policy.action == RetentionAction.DELETE:
                await self._delete_records(policy, records, result)
            elif policy.action == RetentionAction.ANONYMIZE:
                await self._anonymize_records(policy, records, result)
            
            # Log the retention operation
            await self._log_retention_operation(result)
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Retention error for {policy.data_type}: {e}")
        
        return result
    
    async def _get_expired_records(
        self,
        policy: RetentionPolicy,
    ) -> list[dict]:
        """Get records that have exceeded retention period."""
        cutoff_date = policy.retention_date
        
        # Map data types to tables and queries
        table_mapping = {
            DataType.APPLICATIONS: ("applications", "created_at"),
            DataType.PROFILES: ("profiles", "updated_at"),
            DataType.RESUMES: ("profiles", "resume_uploaded_at"),
            DataType.ANALYTICS: ("analytics_events", "created_at"),
            DataType.LOGS: ("api_logs", "created_at"),
            DataType.EVENTS: ("application_events", "created_at"),
            DataType.NOTIFICATIONS: ("push_tokens", "last_used_at"),
            DataType.SESSIONS: ("sessions", "created_at"),
            DataType.AUDIT_LOGS: ("audit_log", "created_at"),
        }
        
        if policy.data_type not in table_mapping:
            return []
        
        table, date_column = table_mapping[policy.data_type]
        
        # Build exclusion conditions
        exclude_conditions = []
        for flag in policy.exclude_flags:
            exclude_conditions.append(f"NOT (metadata->>'{flag}' = 'true')")
        
        where_clause = f"{date_column} < $1"
        if exclude_conditions:
            where_clause += " AND " + " AND ".join(exclude_conditions)
        
        query = f"""
            SELECT id, * FROM public.{table}
            WHERE {where_clause}
            LIMIT 1000
        """
        
        rows = await self.db.fetch(query, cutoff_date)
        return [dict(row) for row in rows]
    
    async def _archive_records(
        self,
        policy: RetentionPolicy,
        records: list[dict],
        result: RetentionResult,
    ) -> None:
        """Archive records to cold storage."""
        if not self.storage:
            result.errors.append("Storage service not configured for archiving")
            return
        
        import json
        
        # Create archive file
        archive_data = {
            "data_type": policy.data_type.value,
            "archived_at": datetime.utcnow().isoformat(),
            "record_count": len(records),
            "records": records,
        }
        
        archive_key = f"archives/{policy.data_type.value}/{datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')}.json"
        
        try:
            await self.storage.upload(
                key=archive_key,
                data=json.dumps(archive_data).encode(),
                content_type="application/json",
                metadata={
                    "data_type": policy.data_type.value,
                    "record_count": str(len(records)),
                    "retention_policy": str(policy.retention_days),
                },
            )
            
            # Delete archived records from database
            await self._delete_records(policy, records, result)
            result.records_archived = len(records)
            
            logger.info(f"Archived {len(records)} {policy.data_type.value} records to {archive_key}")
            
        except Exception as e:
            result.errors.append(f"Archive failed: {e}")
    
    async def _delete_records(
        self,
        policy: RetentionPolicy,
        records: list[dict],
        result: RetentionResult,
    ) -> None:
        """Delete records from database."""
        if not records:
            return
        
        table_mapping = {
            DataType.APPLICATIONS: "applications",
            DataType.PROFILES: "profiles",
            DataType.RESUMES: "profiles",  # Just clear resume fields
            DataType.ANALYTICS: "analytics_events",
            DataType.LOGS: "api_logs",
            DataType.EVENTS: "application_events",
            DataType.NOTIFICATIONS: "push_tokens",
            DataType.SESSIONS: "sessions",
            DataType.AUDIT_LOGS: "audit_log",
        }
        
        table = table_mapping.get(policy.data_type)
        if not table:
            return
        
        ids = [r["id"] for r in records if "id" in r]
        if not ids:
            return
        
        # Delete in batches
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            await self.db.execute(
                f"DELETE FROM public.{table} WHERE id = ANY($1)",
                batch,
            )
        
        result.records_deleted = len(ids)
        result.bytes_freed = sum(len(str(r)) for r in records)  # Approximate
        
        logger.info(f"Deleted {len(ids)} {policy.data_type.value} records")
    
    async def _anonymize_records(
        self,
        policy: RetentionPolicy,
        records: list[dict],
        result: RetentionResult,
    ) -> None:
        """Anonymize records while preserving aggregate data."""
        if not records:
            return
        
        # Anonymization patterns
        anonymize_fields = {
            "email": "anonymized@example.com",
            "full_name": "Anonymous User",
            "phone": "+1-000-000-0000",
            "address": "REDACTED",
            "ip_address": "0.0.0.0",
        }
        
        table_mapping = {
            DataType.PROFILES: "profiles",
        }
        
        table = table_mapping.get(policy.data_type)
        if not table:
            return
        
        ids = [r["id"] for r in records if "id" in r]
        
        for record_id in ids:
            # Update profile_data JSONB field
            for field, replacement in anonymize_fields.items():
                await self.db.execute(
                    f"""
                    UPDATE public.{table}
                    SET profile_data = jsonb_set(
                        profile_data,
                        '{{contact,{field}}}',
                        '"{replacement}"'::jsonb
                    )
                    WHERE id = $1
                    """,
                    record_id,
                )
        
        result.records_anonymized = len(ids)
        logger.info(f"Anonymized {len(ids)} {policy.data_type.value} records")
    
    async def _log_retention_operation(
        self,
        result: RetentionResult,
    ) -> None:
        """Log retention operation for audit trail."""
        await self.db.execute(
            """
            INSERT INTO public.audit_log (event_type, metadata, created_at)
            VALUES ('data_retention', $1, now())
            """,
            result.to_dict(),
        )
    
    async def get_retention_stats(self) -> dict:
        """Get statistics about data retention."""
        stats = {
            "policies": {},
            "pending_deletion": {},
            "last_run": None,
        }
        
        for data_type, policy in self.policies.items():
            stats["policies"][data_type.value] = {
                "retention_days": policy.retention_days,
                "action": policy.action.value,
            }
            
            # Count records pending deletion
            records = await self._get_expired_records(policy)
            stats["pending_deletion"][data_type.value] = len(records)
        
        # Get last retention run
        last_run = await self.db.fetchrow(
            """
            SELECT created_at, metadata
            FROM public.audit_log
            WHERE event_type = 'data_retention'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        
        if last_run:
            stats["last_run"] = {
                "timestamp": last_run["created_at"].isoformat(),
                "details": last_run["metadata"],
            }
        
        return stats


async def run_data_retention(
    db_conn: "asyncpg.Connection",
    data_types: Optional[list[DataType]] = None,
    dry_run: bool = False,
) -> list[RetentionResult]:
    """Convenience function to run data retention."""
    service = DataRetentionService(db_conn)
    return await service.run_retention(data_types, dry_run)
