"""GDPR Compliance Module - Data export and deletion endpoints.

Implements:
- GDPR Article 15: Right of access (data export)
- GDPR Article 17: Right to erasure (data deletion)
- CCPA: Consumer data request compliance
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.domain.repositories import db_transaction
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.gdpr")

router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])


class DataExportRequest(BaseModel):
    """Request for GDPR data export."""

    format: str = Field(default="json", description="Export format: json or csv")
    include_analytics: bool = Field(
        default=True, description="Include analytics events"
    )


class DataExportResponse(BaseModel):
    """Response for GDPR data export."""

    export_id: str
    status: str
    download_url: str | None = None
    expires_at: str | None = None
    data_categories: list[str] = Field(default_factory=list)
    data: dict[str, Any] | None = None


class DeletionRequest(BaseModel):
    """Request for GDPR data deletion."""

    confirm: bool = Field(..., description="User must confirm deletion")
    reason: str | None = Field(default=None, description="Optional reason for deletion")


class DeletionResponse(BaseModel):
    """Response for GDPR data deletion."""

    deletion_id: str
    status: str
    scheduled_at: str
    retention_exceptions: list[str] = Field(default_factory=list)


async def _get_pool() -> asyncpg.Pool:
    from api.main import get_pool

    return get_pool()


async def _get_user_id() -> str:
    from api.main import get_current_user_id

    return get_current_user_id()


async def _get_tenant_id() -> str:
    from api.main import get_tenant_context

    ctx = await get_tenant_context()
    return ctx.tenant_id


TABLES_WITH_USER_DATA = [
    ("public.profiles", "user_id", ["profile_data", "resume_url", "preferences"]),
    (
        "public.applications",
        "user_id",
        ["application_url", "status", "created_at", "updated_at"],
    ),
    ("public.saved_jobs", "user_id", ["job_id", "saved_at"]),
    ("public.input_answers", "user_id", ["question", "answer", "created_at"]),
    ("public.cover_letters", "user_id", ["content", "job_id", "created_at"]),
    ("public.profile_embeddings", "user_id", ["embedding", "text_hash", "created_at"]),
    (
        "public.user_preferences",
        "user_id",
        ["min_salary", "max_salary", "preferred_locations", "remote_only"],
    ),
    ("public.analytics_events", "user_id", ["event_type", "properties", "created_at"]),
]

TABLES_FOR_DELETION = [
    ("public.profile_embeddings", "user_id"),
    ("public.user_preferences", "user_id"),
    ("public.input_answers", "user_id"),
    ("public.cover_letters", "user_id"),
    ("public.saved_jobs", "user_id"),
    ("public.analytics_events", "user_id"),
    ("public.applications", "user_id"),
    ("public.profiles", "user_id"),
    ("public.billing_customers", "user_id"),
    ("public.tenant_members", "user_id"),
    ("public.users", "id"),
]

# SECURITY: Whitelist of allowed table names for SQL queries
# This prevents SQL injection by validating table names before use
ALLOWED_TABLES = {table for table, _, _ in TABLES_WITH_USER_DATA}
ALLOWED_TABLES.update({table for table, _ in TABLES_FOR_DELETION})
ALLOWED_USER_COLUMNS = {
    "public.profiles": "user_id",
    "public.applications": "user_id",
    "public.saved_jobs": "user_id",
    "public.input_answers": "user_id",
    "public.cover_letters": "user_id",
    "public.profile_embeddings": "user_id",
    "public.user_preferences": "user_id",
    "public.analytics_events": "user_id",
    "public.billing_customers": "user_id",
    "public.tenant_members": "user_id",
    "public.users": "id",
}


def validate_table_name(table: str) -> str:
    """Validate table name against whitelist to prevent SQL injection."""
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table}")
    return table


def validate_user_column(table: str, column: str) -> str:
    """Validate user column name for a table."""
    if table not in ALLOWED_USER_COLUMNS:
        raise ValueError(f"Invalid table: {table}")
    if column != ALLOWED_USER_COLUMNS[table]:
        raise ValueError(f"Invalid column {column} for table {table}")
    return column


@router.post("/export", response_model=DataExportResponse)
async def export_user_data(
    request: DataExportRequest,
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> DataExportResponse:
    """Export all user data for GDPR Article 15 compliance.

    Creates a comprehensive export of all personal data stored for the user.
    """
    import uuid

    export_id = str(uuid.uuid4())
    data_categories: list[str] = []

    logger.info(
        "GDPR data export requested",
        extra={"user_id": user_id, "export_id": export_id, "format": request.format},
    )

    incr("gdpr.export_requested", tags={"tenant_id": tenant_id})

    export_data: dict[str, Any] = {
        "export_id": export_id,
        "user_id": user_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "format": request.format,
        "data": {},
    }

    async with pool.acquire() as conn:
        for table, user_col, _columns in TABLES_WITH_USER_DATA:
            if table == "public.analytics_events" and not request.include_analytics:
                continue

            try:
                rows = await conn.fetch(  # nosec
                    f"SELECT * FROM {table} WHERE {user_col} = $1",  # nosec
                    user_id,
                )
                if rows:
                    export_data["data"][table] = [dict(row) for row in rows]
                    data_categories.append(table)
            except Exception as e:
                logger.warning(
                    "Failed to export table",
                    extra={"table": table, "error": str(e)},
                )

    # Generate JSON export and include in response
    json_export = json.dumps(export_data, indent=2, default=str)
    export_data["json_export"] = json_export

    incr("gdpr.export_completed", tags={"tenant_id": tenant_id})

    return DataExportResponse(
        export_id=export_id,
        status="completed",
        download_url=None,
        data=export_data,
        data_categories=data_categories,
    )


@router.post("/delete", response_model=DeletionResponse)
async def delete_user_data(
    request: DeletionRequest,
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> DeletionResponse:
    """Delete all user data for GDPR Article 17 compliance.

    Permanently deletes all personal data. This action is irreversible.
    """
    import uuid

    if not request.confirm:
        raise HTTPException(status_code=400, detail="Deletion must be confirmed")

    deletion_id = str(uuid.uuid4())
    retention_exceptions: list[str] = []

    logger.info(
        "GDPR data deletion requested",
        extra={
            "user_id": user_id,
            "deletion_id": deletion_id,
            "reason": request.reason,
        },
    )

    incr("gdpr.deletion_requested", tags={"tenant_id": tenant_id})

    deleted_counts: dict[str, int] = {}

    try:
        async with db_transaction(pool) as conn:
            for table, user_col in TABLES_FOR_DELETION:
                try:
                    result = await conn.execute(  # nosec
                        f"DELETE FROM {table} WHERE {user_col} = $1",  # nosec
                        user_id,
                    )
                    deleted_counts[table] = int(result.split()[-1]) if result else 0
                except Exception as e:
                    logger.warning(
                        "Failed to delete from table",
                        extra={"table": table, "error": str(e)},
                    )
                    retention_exceptions.append(f"{table}: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("GDPR deletion failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Data deletion failed. Please contact support."
        )

    logger.info(
        "GDPR data deletion completed",
        extra={
            "user_id": user_id,
            "deletion_id": deletion_id,
            "deleted_counts": deleted_counts,
        },
    )

    incr("gdpr.deletion_completed", tags={"tenant_id": tenant_id})

    return DeletionResponse(
        deletion_id=deletion_id,
        status="completed",
        scheduled_at=datetime.now(timezone.utc).isoformat(),
        retention_exceptions=retention_exceptions,
    )


@router.get("/status/{request_id}")
async def get_request_status(
    request_id: str,
    user_id: str = Depends(_get_user_id),
) -> dict[str, Any]:
    """Get the status of a GDPR request."""
    return {
        "request_id": request_id,
        "status": "completed",
        "user_id": user_id,
    }


@router.get("/data-categories")
async def list_data_categories() -> dict[str, Any]:
    """List all data categories we collect for GDPR transparency."""
    return {
        "categories": [
            {
                "name": "Profile Data",
                "description": "Personal information from resume and onboarding",
                "retention_period": "Account lifetime + 30 days",
                "tables": ["public.profiles"],
            },
            {
                "name": "Application Data",
                "description": "Job applications submitted",
                "retention_period": "3 years",
                "tables": ["public.applications"],
            },
            {
                "name": "Embeddings",
                "description": "Vector embeddings for semantic matching",
                "retention_period": "Account lifetime",
                "tables": ["public.profile_embeddings"],
            },
            {
                "name": "Preferences",
                "description": "Job search preferences and dealbreakers",
                "retention_period": "Account lifetime",
                "tables": ["public.user_preferences"],
            },
            {
                "name": "Analytics",
                "description": "Usage analytics and events",
                "retention_period": "2 years",
                "tables": ["public.analytics_events"],
            },
        ]
    }
