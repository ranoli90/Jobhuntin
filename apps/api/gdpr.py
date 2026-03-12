"""GDPR Compliance Module - Data export and deletion endpoints.

Implements:
- GDPR Article 15: Right of access (data export)
- GDPR Article 17: Right to erasure (data deletion)
- CCPA: Consumer data request compliance
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from packages.backend.domain.repositories import db_transaction
from shared.logging_config import get_logger
from shared.metrics import incr
from shared.validators import validate_uuid

logger = get_logger("sorce.gdpr")

router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])


class DataExportRequest(BaseModel):
    """Request for GDPR data export."""

    format: str = Field(default="json", max_length=20, description="Export format: json or csv")
    include_analytics: bool = Field(
        default=True, description="Include analytics events"
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v.lower() not in ("json", "csv"):
            raise ValueError("format must be 'json' or 'csv'")
        return v.lower()


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
    reason: str | None = Field(default=None, max_length=500, description="Optional reason for deletion")


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


# PRIV-005: Use application_inputs (hold questions) and answer_memory (smart pre-fill),
# not legacy input_answers which may not exist. application_inputs is keyed by
# application_id; answer_memory by user_id.
TABLES_WITH_USER_DATA = [
    ("public.profiles", "user_id", ["profile_data", "resume_url", "preferences"]),
    (
        "public.applications",
        "user_id",
        ["application_url", "status", "created_at", "updated_at"],
    ),
    ("public.saved_jobs", "user_id", ["job_id", "saved_at"]),
    (
        "public.answer_memory",
        "user_id",
        ["field_label", "field_type", "answer_value", "use_count", "created_at"],
    ),
    ("public.cover_letters", "user_id", ["content", "job_id", "created_at"]),
    ("public.profile_embeddings", "user_id", ["embedding", "text_hash", "created_at"]),
    (
        "public.user_preferences",
        "user_id",
        ["min_salary", "max_salary", "preferred_locations", "remote_only"],
    ),
    ("public.analytics_events", "user_id", ["event_type", "properties", "created_at"]),
]

# application_inputs: delete via application_id (child of applications)
CUSTOM_DELETION_QUERIES = [
    (
        "public.application_inputs",
        "DELETE FROM public.application_inputs WHERE application_id IN "
        "(SELECT id FROM public.applications WHERE user_id = $1)",
    ),
]

TABLES_FOR_DELETION = [
    ("public.profile_embeddings", "user_id"),
    ("public.user_preferences", "user_id"),
    ("public.answer_memory", "user_id"),
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
ALLOWED_TABLES.update({t for t, _ in CUSTOM_DELETION_QUERIES})
ALLOWED_USER_COLUMNS = {
    "public.profiles": "user_id",
    "public.applications": "user_id",
    "public.saved_jobs": "user_id",
    "public.answer_memory": "user_id",
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

        # PRIV-005: application_inputs is keyed by application_id; export via user's apps
        try:
            app_ids = [r["id"] for r in export_data["data"].get("public.applications", [])]
            if app_ids:
                rows = await conn.fetch(
                    """
                    SELECT application_id, selector, question, field_type, answer,
                           resolved, created_at
                    FROM public.application_inputs
                    WHERE application_id = ANY($1::uuid[])
                    ORDER BY created_at DESC
                    """,
                    app_ids,
                )
                if rows:
                    export_data["data"]["public.application_inputs"] = [
                        dict(row) for row in rows
                    ]
                    data_categories.append("public.application_inputs")
        except Exception as e:
            logger.warning(
                "Failed to export application_inputs",
                extra={"error": str(e)},
            )

    # PRIV-008: Upload to storage, return secure download URL instead of raw data
    json_export = json.dumps(export_data, indent=2, default=str)
    download_url: str | None = None
    expires_at: str | None = None
    export_ttl_seconds = 3600  # 1 hour

    try:
        from shared.storage import get_storage_service

        storage = get_storage_service()
        storage_path = f"{user_id}/{export_id}.json"
        await storage.upload_file(
            "gdpr-exports",
            storage_path,
            json_export.encode("utf-8"),
            content_type="application/json",
        )
        full_storage_path = f"gdpr-exports/{storage_path}"
        download_url = await storage.generate_signed_url(
            full_storage_path, ttl_seconds=export_ttl_seconds
        )
        # For local storage (file://) or relative paths, use our API endpoint
        if download_url.startswith("file://") or (
            download_url.startswith("/") and "http" not in download_url[:8]
        ):
            download_url = f"/gdpr/export/{export_id}/download"
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=export_ttl_seconds)
        ).isoformat()
    except Exception as e:
        logger.warning("GDPR export storage upload failed, using Redis fallback: %s", e)
        from shared.config import get_settings

        if get_settings().redis_url:
            from shared.redis_client import get_redis

            r = await get_redis()
            key = f"gdpr_export:{user_id}:{export_id}"
            await r.setex(key, export_ttl_seconds, json_export)
            download_url = f"/gdpr/export/{export_id}/download"
            expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=export_ttl_seconds)
            ).isoformat()
        else:
            raise HTTPException(
                status_code=503,
                detail="Export storage unavailable. Please try again later.",
            ) from e

    incr("gdpr.export_completed", tags={"tenant_id": tenant_id})

    # PRIV-006: Record in gdpr_requests for status lookup with ownership verification
    try:
        await pool.execute(
            """
            INSERT INTO public.gdpr_requests (id, user_id, request_type, status, completed_at)
            VALUES ($1, $2, 'export', 'completed', NOW())
            """,
            export_id,
            user_id,
        )
    except Exception as e:
        logger.warning("Failed to record export in gdpr_requests: %s", e)

    return DataExportResponse(
        export_id=export_id,
        status="completed",
        download_url=download_url,
        expires_at=expires_at,
        data=None,  # PRIV-008: no raw data in response
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
            # PRIV-005: Custom deletions (application_inputs before applications)
            for table, query in CUSTOM_DELETION_QUERIES:
                try:
                    result = await conn.execute(query, user_id)
                    deleted_counts[table] = int(result.split()[-1]) if result else 0
                except Exception as e:
                    logger.warning(
                        "Failed to delete from table",
                        extra={"table": table, "error": str(e)},
                    )
                    retention_exceptions.append(f"{table}: {str(e)}")

            for table, user_col in TABLES_FOR_DELETION:
                try:
                    # PRIV-003: Remove profile from vector DB before deleting profile_embeddings
                    if table == "public.profile_embeddings":
                        try:
                            from packages.backend.domain.semantic_matching import (
                                get_matching_service,
                            )

                            svc = get_matching_service()
                            await svc.remove_profile(user_id, conn=conn)
                        except Exception as ve:
                            logger.warning(
                                "Failed to remove profile from vector DB: %s", ve
                            )
                            retention_exceptions.append(
                                f"profile_embeddings(vector): {str(ve)}"
                            )

                    # PRIV-002: Delete resume file from storage before deleting profile
                    if table == "public.profiles":
                        try:
                            row = await conn.fetchrow(
                                "SELECT resume_url FROM public.profiles WHERE user_id = $1",
                                user_id,
                            )
                            if row and row.get("resume_url"):
                                from shared.storage import get_storage_service

                                storage = get_storage_service()
                                await storage.delete_file(row["resume_url"])
                                logger.info(
                                    "Deleted resume file for user %s", user_id
                                )
                        except Exception as se:
                            logger.warning(
                                "Failed to delete resume file from storage: %s", se
                            )
                            retention_exceptions.append(
                                f"profiles(resume_file): {str(se)}"
                            )

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

    # PRIV-006: Record in gdpr_requests for status lookup with ownership verification
    try:
        await pool.execute(
            """
            INSERT INTO public.gdpr_requests (id, user_id, request_type, status, completed_at)
            VALUES ($1, $2, 'delete', 'completed', NOW())
            """,
            deletion_id,
            user_id,
        )
    except Exception as e:
        logger.warning("Failed to record deletion in gdpr_requests: %s", e)

    return DeletionResponse(
        deletion_id=deletion_id,
        status="completed",
        scheduled_at=datetime.now(timezone.utc).isoformat(),
        retention_exceptions=retention_exceptions,
    )


@router.get("/export/{export_id}/download")
async def download_export(
    export_id: str,
    user_id: str = Depends(_get_user_id),
) -> Response:
    """PRIV-008: Secure download of GDPR export. No raw data in POST response."""
    try:
        validate_uuid(export_id, "export_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid export ID format")

    # Try storage first
    try:
        from shared.storage import get_storage_service

        storage = get_storage_service()
        storage_path = f"gdpr-exports/{user_id}/{export_id}.json"
        data = await storage.download_file(storage_path)
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="gdpr_export_{export_id}.json"'},
        )
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning("GDPR export download from storage failed: %s", e)

    # Fallback: Redis (when storage upload failed)
    from shared.config import get_settings

    if get_settings().redis_url:
        from shared.redis_client import get_redis

        r = await get_redis()
        key = f"gdpr_export:{user_id}:{export_id}"
        raw = await r.get(key)
        if raw:
            content = raw.encode("utf-8") if isinstance(raw, str) else raw
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="gdpr_export_{export_id}.json"'},
            )

    raise HTTPException(status_code=404, detail="Export not found or expired")


@router.get("/status/{request_id}")
async def get_request_status(
    request_id: str,
    user_id: str = Depends(_get_user_id),
    pool: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get the status of a GDPR request. PRIV-006: Verifies ownership via gdpr_requests."""
    try:
        validate_uuid(request_id, "request_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")

    row = await pool.fetchrow(
        """
        SELECT id, request_type, status, created_at, completed_at
        FROM public.gdpr_requests
        WHERE id = $1 AND user_id = $2
        """,
        request_id,
        user_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Request not found or access denied")

    return {
        "request_id": str(row["id"]),
        "request_type": row["request_type"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
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
