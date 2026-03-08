# CORRECTED VERSION - Use this to replace the problematic section in user.py

# Add this import at the top with other imports:
from datetime import datetime, timezone

# Replace the problematic section starting around line 548:

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
        update_fields = ["status = $3", "updated_at = CURRENT_TIMESTAMP"]
        params = [body.status, application_id, ctx.user_id]

        if body.notes:
            update_fields.append("notes = $4")
            params.append(body.notes)

        # nosemgrep: python.lang.security.audit.sqli.asyncpg-sqli.asyncpg-sqli - parameterized query
        await conn.execute(
            f"""
            UPDATE public.applications 
            SET {", ".join(update_fields)}
            WHERE id = ${len(params)} AND user_id = ${len(params) + 1}
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
