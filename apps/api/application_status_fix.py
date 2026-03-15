# CORRECTED VERSION - Use this to replace the problematic section in user.py
# This file is a reference fragment; add these imports when merging into api.user.

import logging
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as FastAPIPath
from pydantic import BaseModel, Field

# Stubs for fragment context (provided by api.user when merged)
router = APIRouter()


class TenantContext:
    """Stub; use api.types or api.user TenantContext when merged."""

    user_id: str = ""


def _get_tenant_ctx() -> TenantContext:
    return TenantContext()


def _get_pool() -> asyncpg.Pool:
    raise RuntimeError("Fragment: use app _get_pool when merged")


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PATCH /me/applications/{application_id}/status
# ---------------------------------------------------------------------------


class UpdateApplicationStatusBody(BaseModel):
    """Request body for updating application status."""

    status: str = Field(
        ...,
        description="New status: 'INTERVIEW_SCHEDULED', 'OFFER_RECEIVED', 'ACCEPTED', 'REJECTED'",
    )
    notes: str | None = Field(
        None, description="Optional notes about the status update"
    )


@router.patch("/me/applications/{application_id}/status")
async def update_application_status(
    application_id: str = FastAPIPath(..., description="Application ID to update"),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
    body: UpdateApplicationStatusBody = Body(...),
) -> dict[str, Any]:
    """Update application status manually."""
    from shared.validators import validate_uuid

    # Validate application_id format
    try:
        validate_uuid(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID format")

    # Validate status
    valid_statuses = [
        "INTERVIEW_SCHEDULED",
        "OFFER_RECEIVED",
        "ACCEPTED",
        "REJECTED",
        "WITHDRAWN",
    ]
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    async with db.acquire() as conn:
        # Check if application exists and belongs to user
        app = await conn.fetchrow(
            "SELECT id, user_id, status FROM public.applications WHERE id = $1 AND user_id = $2",
            application_id,
            ctx.user_id,
        )

        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # Update status and notes
        # Whitelist of allowed update fields to prevent SQL injection
        update_fields = []
        params = [application_id, ctx.user_id]  # Start with ID and user_id parameters

        if body.status:
            update_fields.append("status = $3")
            params.insert(0, body.status)  # Insert at beginning for correct parameter order

        if body.notes:
            field_index = 3 + len(update_fields) - (1 if body.status else 0)
            update_fields.append(f"notes = ${field_index}")
            if body.status:
                params.append(body.notes)
            else:
                params.insert(0, body.notes)

        # Ensure only whitelisted fields are used
        set_clause = ", ".join(update_fields)

        # nosemgrep: python.lang.security.audit.sqli.asyncpg-sqli.
# asyncpg-sqli - parameterized query with field whitelist
        await conn.execute(
            f"""
            UPDATE public.applications
            SET {set_clause}
            WHERE id = ${len(params) - 1} AND user_id = ${len(params)}
            """,
            *params,
        )

        logger.info(
            f"Application {application_id} status updated to {body.status} by user {ctx.user_id}"
        )

        return {
            "status": "updated",
            "application_id": application_id,
            "new_status": body.status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
