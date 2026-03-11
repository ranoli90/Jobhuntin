"""Session management API endpoints.

Endpoints for:
  - GET  /sessions          — list active sessions for current user
  - DELETE /sessions/{id}   — revoke a specific session
  - DELETE /sessions/all    — revoke all other sessions
  - GET  /sessions/security — check for suspicious activity
"""

from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.domain.session_manager import SessionManager
from backend.domain.tenant import TenantContext
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.api.sessions")

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    raise NotImplementedError("Tenant context dependency not injected")


def _get_user_id():
    raise NotImplementedError("User ID dependency not injected")


class SessionResponse(BaseModel):
    session_id: str
    device_fingerprint: str
    ip_address: str | None
    user_agent: str | None
    created_at: str
    last_activity_at: str
    expires_at: str
    is_current: bool = False


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


class RevokeResponse(BaseModel):
    revoked: bool
    session_id: str | None = None
    count: int = 0


class SecurityCheckResponse(BaseModel):
    suspicious: bool
    reasons: list[str]
    active_sessions: int
    known_ips: list[str]


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    request: Request,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> SessionListResponse:
    manager = SessionManager(db)
    sessions = await manager.list_user_sessions(ctx.user_id, include_revoked=False)

    # M2: Extract session_id from JWT cookie
    current_session_id = None
    jobhuntin_auth = request.cookies.get("jobhuntin_auth")
    if jobhuntin_auth:
        try:
            import jwt as pyjwt

            from shared.config import get_settings

            settings = get_settings()
            payload = pyjwt.decode(
                jobhuntin_auth,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            current_session_id = payload.get("session_id")
        except Exception as e:
            logger.debug("Could not extract session_id from JWT cookie: %s", e)

    session_responses = []
    for s in sessions:
        session_responses.append(
            SessionResponse(
                session_id=s.session_id,
                device_fingerprint=s.device_fingerprint,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                created_at=s.created_at.isoformat(),
                last_activity_at=s.last_activity_at.isoformat(),
                expires_at=s.expires_at.isoformat(),
                is_current=(s.session_id == current_session_id),
            )
        )

    incr("sessions.list")
    return SessionListResponse(sessions=session_responses, total=len(session_responses))


@router.delete("/{session_id}", response_model=RevokeResponse)
async def revoke_session(
    session_id: str,
    request: Request,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> RevokeResponse:
    manager = SessionManager(db)

    # M2: Extract session_id from JWT cookie
    current_session_id = None
    jobhuntin_auth = request.cookies.get("jobhuntin_auth")
    if jobhuntin_auth:
        try:
            import jwt as pyjwt

            from shared.config import get_settings

            settings = get_settings()
            payload = pyjwt.decode(
                jobhuntin_auth,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            current_session_id = payload.get("session_id")
        except Exception as e:
            logger.debug("Could not extract session_id from JWT cookie: %s", e)
    if session_id == current_session_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke current session. Use /sessions/all to revoke others.",
        )

    row = await manager.revoke_session(
        session_id,
        reason="USER_REVOKED",
        revoked_by_user_id=ctx.user_id,
        user_id=ctx.user_id,
    )

    if not row:
        raise HTTPException(
            status_code=404, detail="Session not found or already revoked"
        )

    # Add JTI to Redis blacklist so the revoked JWT is immediately invalid
    meta = row.get("metadata")
    jti = meta.get("jti") if isinstance(meta, dict) else None
    if jti:
        try:
            from apps.api.auth import _revoke_session_token
            from shared.config import get_settings
            await _revoke_session_token(jti, get_settings())
        except Exception as e:
            logger.warning("Failed to revoke session token in Redis: %s", e)

    incr("sessions.revoke_single")
    return RevokeResponse(revoked=True, session_id=session_id, count=1)


@router.delete("/all", response_model=RevokeResponse)
async def revoke_all_other_sessions(
    request: Request,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> RevokeResponse:
    manager = SessionManager(db)

    # M2: Extract session_id from JWT cookie
    current_session_id = None
    jobhuntin_auth = request.cookies.get("jobhuntin_auth")
    if jobhuntin_auth:
        try:
            import jwt as pyjwt

            from shared.config import get_settings

            settings = get_settings()
            payload = pyjwt.decode(
                jobhuntin_auth,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            current_session_id = payload.get("session_id")
        except Exception as e:
            logger.debug("Could not extract session_id from JWT cookie: %s", e)

    count, jtis = await manager.revoke_all_user_sessions(
        ctx.user_id,
        reason="USER_REVOKED_ALL",
        except_session_id=current_session_id,
    )

    for jti in jtis:
        try:
            from apps.api.auth import _revoke_session_token
            from shared.config import get_settings
            await _revoke_session_token(jti, get_settings())
        except Exception as e:
            logger.warning("Failed to revoke session token in Redis: %s", e)

    incr("sessions.revoke_all")
    return RevokeResponse(revoked=True, count=count)


@router.get("/security", response_model=SecurityCheckResponse)
async def check_security(
    request: Request,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> SecurityCheckResponse:
    manager = SessionManager(db)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = await manager.detect_suspicious_activity(
        ctx.user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    incr("sessions.security_check")
    return SecurityCheckResponse(
        suspicious=result["suspicious"],
        reasons=result["reasons"],
        active_sessions=result["active_sessions"],
        known_ips=result["known_ips"],
    )


@router.post("/cleanup", response_model=RevokeResponse)
async def cleanup_expired_sessions(
    user_id: str = Depends(_get_user_id),
    db: asyncpg.Pool = Depends(_get_pool),
) -> RevokeResponse:
    # Require admin role for cleanup
    async with db.acquire() as conn:
        role = await conn.fetchval(
            "SELECT role FROM public.tenant_members WHERE user_id = $1 LIMIT 1",
            user_id,
        )
        if role not in ("ADMIN", "OWNER"):
            raise HTTPException(status_code=403, detail="Admin access required")

    manager = SessionManager(db)
    count = await manager.cleanup_expired_sessions()

    incr("sessions.cleanup")
    return RevokeResponse(revoked=True, count=count)
