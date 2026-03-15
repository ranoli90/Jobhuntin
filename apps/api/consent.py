"""Consent Management API - GDPR/CCPA Compliant Consent Tracking.

This module provides endpoints for:
- Saving user consent preferences
- Retrieving current consent status
- Revoking specific consent types
- Exporting consent data for GDPR compliance

Supports both authenticated users and anonymous visitors (via browser fingerprint).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from api.dependencies import get_current_user_id, get_pool
from shared.logging_config import get_logger

logger = get_logger("sorce.consent")

router = APIRouter(prefix="/consent", tags=["Consent Management"])

# Valid consent types
VALID_CONSENT_TYPES = {"marketing", "analytics", "cookies", "functional", "essential"}


class ConsentPreferences(BaseModel):
    """User consent preferences."""

    essential: bool = Field(default=True, description="Essential cookies (always true)")
    analytics: bool = Field(default=False, description="Analytics cookies")
    marketing: bool = Field(default=False, description="Marketing cookies")
    cookies: bool = Field(default=False, description="Non-essential cookies")
    functional: bool = Field(default=False, description="Functional cookies")


class ConsentRequest(BaseModel):
    """Request to save consent preferences."""

    preferences: ConsentPreferences
    anonymous_id: str | None = Field(
        default=None,
        description="Browser fingerprint for anonymous users",
    )
    version: str = Field(default="2.0", description="Consent policy version")


class ConsentResponse(BaseModel):
    """Response with consent status."""

    preferences: ConsentPreferences
    user_id: str | None = None
    anonymous_id: str | None = None
    version: str
    last_updated: datetime


class ConsentAuditEntry(BaseModel):
    """Single consent audit entry."""

    id: str
    consent_type: str
    action: str
    previous_value: bool | None
    new_value: bool | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    reason: str | None


class ConsentExportResponse(BaseModel):
    """GDPR export of all consent data."""

    user_id: str | None = None
    anonymous_id: str | None = None
    consents: list[dict[str, Any]]
    audit_log: list[ConsentAuditEntry]
    exported_at: datetime
    version: str


async def _get_client_info(request: Request) -> tuple[str | None, str | None]:
    """Extract IP address and user agent from request."""
    ip_address = request.client.host if request.client else None
    # Check for forwarded header (proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()

    user_agent = request.headers.get("User-Agent", "")
    return ip_address, user_agent


async def _save_consent_audit(
    pool: asyncpg.Pool,
    user_id: str | None,
    anonymous_id: str | None,
    consent_type: str,
    action: str,
    previous_value: bool | None,
    new_value: bool,
    ip_address: str | None,
    user_agent: str,
    reason: str | None = None,
) -> None:
    """Save consent change to audit log."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO consent_audit_log
            (user_id, anonymous_id, consent_type, action, previous_value, new_value, ip_address, user_agent, reason)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            user_id,
            anonymous_id,
            consent_type,
            action,
            previous_value,
            new_value,
            ip_address,
            user_agent,
            reason,
        )


@router.post("", response_model=ConsentResponse)
async def save_consent(
    consent_req: ConsentRequest,
    request: Request,
    user_id: str | None = Depends(get_current_user_id),
    pool=Depends(get_pool),
) -> ConsentResponse:
    """Save user consent preferences.

    For authenticated users, consent is linked to their user_id.
    For anonymous users, consent is linked to their anonymous_id (browser fingerprint).
    """
    ip_address, user_agent = await _get_client_info(request)
    preferences = consent_req.preferences
    version = consent_req.version

    # Determine which identifier to use
    identifier = user_id or consent_req.anonymous_id
    if not identifier:
        raise HTTPException(
            status_code=400,
            detail="Either user_id (authenticated) or anonymous_id is required",
        )

    async with pool.acquire() as conn:
        # Save each consent type
        consent_types = {
            "essential": preferences.essential,
            "analytics": preferences.analytics,
            "marketing": preferences.marketing,
            "cookies": preferences.cookies,
            "functional": preferences.functional,
        }

        for consent_type, granted in consent_types.items():
            # Get previous value for audit
            prev_row = await conn.fetchrow(
                """
                SELECT granted FROM user_consents
                WHERE ($1::uuid IS NOT NULL AND user_id = $1)
                   OR ($2 IS NOT NULL AND anonymous_id = $2)
                AND consent_type = $3
                """,
                user_id,
                consent_req.anonymous_id,
                consent_type,
            )
            previous_value = prev_row["granted"] if prev_row else None

            # Upsert consent record
            await conn.execute(
                """
                INSERT INTO user_consents
                (
    user_id, anonymous_id, consent_type, granted, granted_at, revoked_at, ip_address, user_agent, version, source)
                VALUES ($1, $2, $3, $4, NOW(), NULL, $5, $6, $7, 'web')
                ON CONFLICT
                    (CASE WHEN $1::uuid IS NOT NULL THEN user_id ELSE NULL END,
                     CASE WHEN $1::uuid IS NOT NULL THEN NULL ELSE anonymous_id END,
                     consent_type)
                DO UPDATE SET
                    granted = $4,
                    granted_at = CASE WHEN $4 = TRUE THEN NOW() ELSE granted_at END,
                    revoked_at = CASE WHEN $4 = FALSE THEN NOW() ELSE NULL END,
                    ip_address = $5,
                    user_agent = $6,
                    version = $7,
                    updated_at = NOW()
                """,
                user_id,
                consent_req.anonymous_id,
                consent_type,
                granted,
                ip_address,
                user_agent,
                version,
            )

            # Log audit entry if value changed
            if previous_value is None or previous_value != granted:
                action = "grant" if granted else "revoke"
                if previous_value is not None:
                    action = "update"
                await _save_consent_audit(
                    pool=pool,
                    user_id=user_id,
                    anonymous_id=consent_req.anonymous_id,
                    consent_type=consent_type,
                    action=action,
                    previous_value=previous_value,
                    new_value=granted,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

    return ConsentResponse(
        preferences=preferences,
        user_id=user_id,
        anonymous_id=consent_req.anonymous_id,
        version=version,
        last_updated=datetime.now(timezone.utc),
    )


@router.get("", response_model=ConsentResponse)
async def get_consent(
    request: Request,
    user_id: str | None = Depends(get_current_user_id),
    anonymous_id: str | None = Header(None, alias="X-Anonymous-ID"),
    pool=Depends(get_pool),
) -> ConsentResponse:
    """Get current consent status for the user.

    Checks both authenticated user_id and anonymous_id (from header).
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT consent_type, granted, version, updated_at
            FROM user_consents
            WHERE ($1::uuid IS NOT NULL AND user_id = $1)
               OR ($2 IS NOT NULL AND anonymous_id = $2)
            ORDER BY consent_type
            """,
            user_id,
            anonymous_id,
        )

    if not rows:
        # Return default preferences if no consent found
        return ConsentResponse(
            preferences=ConsentPreferences(),
            user_id=user_id,
            anonymous_id=anonymous_id,
            version="2.0",
            last_updated=datetime.now(timezone.utc),
        )

    # Build preferences from database
    preferences = ConsentPreferences()
    version = "2.0"
    last_updated = datetime.now(timezone.utc)

    for row in rows:
        consent_type = row["consent_type"]
        granted = row["granted"]

        if consent_type == "essential":
            preferences.essential = granted
        elif consent_type == "analytics":
            preferences.analytics = granted
        elif consent_type == "marketing":
            preferences.marketing = granted
        elif consent_type == "cookies":
            preferences.cookies = granted
        elif consent_type == "functional":
            preferences.functional = granted

        if row["version"]:
            version = row["version"]
        if row["updated_at"]:
            last_updated = row["updated_at"]

    return ConsentResponse(
        preferences=preferences,
        user_id=user_id,
        anonymous_id=anonymous_id,
        version=version,
        last_updated=last_updated,
    )


@router.delete("/{consent_type}", response_model=ConsentResponse)
async def revoke_consent(
    consent_type: str,
    request: Request,
    user_id: str | None = Depends(get_current_user_id),
    anonymous_id: str | None = Header(None, alias="X-Anonymous-ID"),
    pool=Depends(get_pool),
) -> ConsentResponse:
    """Revoke a specific consent type."""
    if consent_type not in VALID_CONSENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid consent type. Must be one of: {', '.join(VALID_CONSENT_TYPES)}",
        )

    # Essential consent cannot be revoked
    if consent_type == "essential":
        raise HTTPException(
            status_code=400,
            detail="Essential consent cannot be revoked",
        )

    ip_address, user_agent = await _get_client_info(request)

    async with pool.acquire() as conn:
        # Get previous value
        prev_row = await conn.fetchrow(
            """
            SELECT granted FROM user_consents
            WHERE ($1::uuid IS NOT NULL AND user_id = $1)
               OR ($2 IS NOT NULL AND anonymous_id = $2)
            AND consent_type = $3
            """,
            user_id,
            anonymous_id,
            consent_type,
        )

        previous_value = prev_row["granted"] if prev_row else None

        # Revoke consent
        await conn.execute(
            """
            UPDATE user_consents
            SET granted = FALSE,
                revoked_at = NOW(),
                ip_address = $4,
                user_agent = $5,
                updated_at = NOW()
            WHERE ($1::uuid IS NOT NULL AND user_id = $1)
               OR ($2 IS NOT NULL AND anonymous_id = $2)
            AND consent_type = $3
            """,
            user_id,
            anonymous_id,
            consent_type,
            ip_address,
            user_agent,
        )

        # Log audit entry
        await _save_consent_audit(
            pool=pool,
            user_id=user_id,
            anonymous_id=anonymous_id,
            consent_type=consent_type,
            action="revoke",
            previous_value=previous_value,
            new_value=False,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="User revoked consent",
        )

    # Return updated consent status
    return await get_consent(request=request, user_id=user_id, anonymous_id=anonymous_id, pool=pool)


@router.get("/export", response_model=ConsentExportResponse)
async def export_consent_data(
    request: Request,
    user_id: str | None = Depends(get_current_user_id),
    anonymous_id: str | None = Header(None, alias="X-Anonymous-ID"),
    pool=Depends(get_pool),
) -> ConsentExportResponse:
    """Export all consent data for GDPR compliance.

    Returns all consent records and audit history for the user.
    """
    if not user_id and not anonymous_id:
        raise HTTPException(
            status_code=400,
            detail="Either authentication or X-Anonymous-ID header is required",
        )

    async with pool.acquire() as conn:
        # Get all consent records
        consent_rows = await conn.fetch(
            """
            SELECT id, consent_type, granted, granted_at, revoked_at, ip_address, user_agent, version, source,
created_at, updated_at
            FROM user_consents
            WHERE ($1::uuid IS NOT NULL AND user_id = $1)
               OR ($2 IS NOT NULL AND anonymous_id = $2)
            ORDER BY consent_type, created_at DESC
            """,
            user_id,
            anonymous_id,
        )

        # Get audit log
        audit_rows = await conn.fetch(
            """
            SELECT id, consent_type, action, previous_value, new_value, ip_address, user_agent, reason, created_at
            FROM consent_audit_log
            WHERE ($1::uuid IS NOT NULL AND user_id = $1)
               OR ($2 IS NOT NULL AND anonymous_id = $2)
            ORDER BY created_at DESC
            """,
            user_id,
            anonymous_id,
        )

    # Format consents
    consents = []
    for row in consent_rows:
        consents.append({
            "id": str(row["id"]),
            "consent_type": row["consent_type"],
            "granted": row["granted"],
            "granted_at": row["granted_at"].isoformat() if row["granted_at"] else None,
            "revoked_at": row["revoked_at"].isoformat() if row["revoked_at"] else None,
            "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
            "user_agent": row["user_agent"],
            "version": row["version"],
            "source": row["source"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        })

    # Format audit log
    audit_log = []
    for row in audit_rows:
        audit_log.append(ConsentAuditEntry(
            id=str(row["id"]),
            consent_type=row["consent_type"],
            action=row["action"],
            previous_value=row["previous_value"],
            new_value=row["new_value"],
            ip_address=str(row["ip_address"]) if row["ip_address"] else None,
            user_agent=row["user_agent"],
            created_at=row["created_at"],
            reason=row["reason"],
        ))

    return ConsentExportResponse(
        user_id=user_id,
        anonymous_id=anonymous_id,
        consents=consents,
        audit_log=audit_log,
        exported_at=datetime.now(timezone.utc),
        version="2.0",
    )
