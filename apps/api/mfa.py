"""MFA API endpoints — TOTP and recovery code management."""

from __future__ import annotations

import json
import time
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from packages.backend.domain.mfa import MFAManager
from shared.error_responses import RateLimitError
from shared.logging_config import get_logger
from shared.metrics import get_rate_limiter

from api.deps import get_pool, get_current_user_id

_get_pool = get_pool
_get_user_id = get_current_user_id

logger = get_logger("sorce.api.mfa")

_totp_attempt_limiters: dict[str, tuple[int, float]] = {}
_TOTP_MAX_ATTEMPTS = 5
_TOTP_WINDOW_SECONDS = 300  # 5 minutes


def _check_totp_rate_limit(user_id: str) -> bool:
    """Returns True if allowed, False if rate limited."""
    now = time.monotonic()
    entry = _totp_attempt_limiters.get(user_id)
    if entry:
        count, window_start = entry
        if now - window_start < _TOTP_WINDOW_SECONDS:
            if count >= _TOTP_MAX_ATTEMPTS:
                return False
            _totp_attempt_limiters[user_id] = (count + 1, window_start)
            return True
        # Window expired, reset
    _totp_attempt_limiters[user_id] = (1, now)
    # Evict old entries
    expired = [
        k
        for k, (_, ts) in _totp_attempt_limiters.items()
        if now - ts > _TOTP_WINDOW_SECONDS
    ]
    for k in expired:
        _totp_attempt_limiters.pop(k, None)
    return True


async def _enforce_mfa_rate_limit(
    user_id: str,
    action: str,
    *,
    max_calls: int,
    window_seconds: int,
    message: str,
) -> None:
    """Enforce per-user MFA endpoint rate limits."""
    limiter = get_rate_limiter(
        f"mfa:{action}:{user_id}",
        max_calls=max_calls,
        window_seconds=window_seconds,
    )
    if not await limiter.acquire():
        retry_after = max(1, int(limiter.next_available_in()))
        raise RateLimitError(message, retry_after=retry_after)


router = APIRouter(prefix="/auth/mfa", tags=["mfa"])


class TOTPEnrollRequest(BaseModel):
    pass


class TOTPEnrollResponse(BaseModel):
    enrollment_id: str
    provisioning_uri: str
    secret: str


class TOTPVerifyRequest(BaseModel):
    enrollment_id: str
    code: str


class TOTPVerifyResponse(BaseModel):
    success: bool
    recovery_codes: list[str] | None = None


class TOTPChallengeRequest(BaseModel):
    code: str


class RecoveryCodeRequest(BaseModel):
    code: str


class RecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]
    remaining: int


class MFAMethodsResponse(BaseModel):
    methods: list[dict[str, Any]]


class DisableMFARequest(BaseModel):
    enrollment_id: str | None = None
    code: str | None = None


@router.post("/totp/enroll", response_model=TOTPEnrollResponse)
async def enroll_totp(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> TOTPEnrollResponse:
    await _enforce_mfa_rate_limit(
        user_id,
        "totp_enroll",
        max_calls=3,
        window_seconds=3600,
        message="Too many MFA enrollment attempts. Please try again later.",
    )
    manager = MFAManager(db)

    async with db.acquire() as conn:
        email = await conn.fetchval(
            "SELECT email FROM public.users WHERE id = $1",
            user_id,
        )

    if not email:
        raise HTTPException(status_code=404, detail="User not found")

    enrollment_id, uri = await manager.enroll_totp(user_id, email)

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT config FROM public.user_mfa_enrollments WHERE id = $1",
            enrollment_id,
        )
        config = (
            row["config"]
            if isinstance(row["config"], dict)
            else json.loads(row["config"] or "{}")
        )
        secret = config.get("secret", "")

    return TOTPEnrollResponse(
        enrollment_id=enrollment_id,
        provisioning_uri=uri,
        secret=secret,
    )


@router.post("/totp/verify-enrollment", response_model=TOTPVerifyResponse)
async def verify_totp_enrollment(
    body: TOTPVerifyRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> TOTPVerifyResponse:
    await _enforce_mfa_rate_limit(
        user_id,
        "verify_enrollment",
        max_calls=10,
        window_seconds=300,
        message="Too many MFA verification attempts. Please wait 5 minutes.",
    )
    manager = MFAManager(db)

    result = await manager.verify_totp_enrollment(
        body.enrollment_id, body.code, user_id=user_id
    )

    if isinstance(result, tuple):
        success, recovery_codes = result
        return TOTPVerifyResponse(success=success, recovery_codes=recovery_codes)

    return TOTPVerifyResponse(success=result)


@router.post("/totp/challenge", response_model=TOTPVerifyResponse)
async def verify_totp_challenge(
    body: TOTPChallengeRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> TOTPVerifyResponse:
    if not _check_totp_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="Too many verification attempts. Please wait 5 minutes.",
        )

    manager = MFAManager(db)

    success = await manager.verify_totp(user_id, body.code)

    return TOTPVerifyResponse(success=success)


@router.post("/recovery/verify", response_model=TOTPVerifyResponse)
async def verify_recovery_code(
    body: RecoveryCodeRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> TOTPVerifyResponse:
    if not _check_totp_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="Too many verification attempts. Please wait 5 minutes.",
        )

    manager = MFAManager(db)

    success = await manager.verify_recovery_code(user_id, body.code)

    return TOTPVerifyResponse(success=success)


@router.post("/recovery/regenerate", response_model=RecoveryCodesResponse)
async def regenerate_recovery_codes(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> RecoveryCodesResponse:
    await _enforce_mfa_rate_limit(
        user_id,
        "recovery_regenerate",
        max_calls=3,
        window_seconds=3600,
        message="Too many recovery code regeneration attempts. Please try again later.",
    )
    manager = MFAManager(db)

    codes = await manager.regenerate_recovery_codes(user_id)
    remaining = await manager.get_remaining_recovery_codes(user_id)

    return RecoveryCodesResponse(recovery_codes=codes, remaining=remaining)


@router.get("/status")
async def get_mfa_status(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> dict[str, Any]:
    manager = MFAManager(db)

    enabled = await manager.is_mfa_enabled(user_id)
    remaining = await manager.get_remaining_recovery_codes(user_id)

    return {
        "enabled": enabled,
        "remaining_recovery_codes": remaining,
    }


@router.get("/methods", response_model=MFAMethodsResponse)
async def list_mfa_methods(
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> MFAMethodsResponse:
    manager = MFAManager(db)

    methods = await manager.list_user_mfa_methods(user_id)

    return MFAMethodsResponse(
        methods=[
            {
                "id": m.id,
                "type": m.mfa_type.value,
                "is_verified": m.is_verified,
                "is_primary": m.is_primary,
                "created_at": m.created_at.isoformat(),
                "last_used_at": m.last_used_at.isoformat() if m.last_used_at else None,
            }
            for m in methods
        ]
    )


@router.delete("/disable")
async def disable_mfa(
    body: DisableMFARequest | None = None,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> dict[str, str]:
    await _enforce_mfa_rate_limit(
        user_id,
        "disable",
        max_calls=5,
        window_seconds=300,
        message="Too many MFA disable attempts. Please wait 5 minutes.",
    )
    manager = MFAManager(db)

    # Require re-authentication: must provide valid TOTP code or recovery code
    if not body or not body.code:
        raise HTTPException(
            status_code=400,
            detail="A valid TOTP code or recovery code is required to disable MFA",
        )

    # Verify the code before allowing disable
    totp_valid = await manager.verify_totp(user_id, body.code)
    recovery_valid = False
    if not totp_valid:
        recovery_valid = await manager.verify_recovery_code(user_id, body.code)

    if not totp_valid and not recovery_valid:
        raise HTTPException(status_code=403, detail="Invalid verification code")

    enrollment_id = body.enrollment_id if body else None
    success = await manager.disable_mfa(user_id, enrollment_id)

    if not success:
        raise HTTPException(status_code=404, detail="MFA enrollment not found")

    logger.info("MFA disabled for user", extra={"user_id": user_id})
    return {"status": "disabled"}
