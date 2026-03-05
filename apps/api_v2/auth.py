"""API v2 authentication — API key validation, rate limiting, usage metering.

Keys are stored hashed (SHA-256). The raw key is only shown once at creation.
Format: sk_live_<32 hex chars>
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any

import asyncpg
from fastapi import HTTPException, Request

from shared.logging_config import get_logger

logger = get_logger("sorce.api_v2.auth")

# In-memory rate limit buckets: {key_prefix: (count, window_start)}
_rate_buckets: dict[str, tuple[int, float]] = {}


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key. Returns (raw_key, key_hash, key_prefix)."""
    raw = "sk_live_" + secrets.token_hex(32)
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    prefix = raw[:16]
    return raw, key_hash, prefix


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def resolve_api_key(
    request: Request,
    pool: asyncpg.Pool,
) -> dict[str, Any]:
    """Validate API key from Authorization header.
    Returns the api_key row dict or raises 401/403/429.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer sk_"):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    raw_key = auth.replace("Bearer ", "").strip()
    h = hash_key(raw_key)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT ak.*, t.plan::text AS tenant_plan, t.name AS tenant_name
               FROM public.api_keys ak
               JOIN public.tenants t ON t.id = ak.tenant_id
               WHERE ak.key_hash = $1""",
            h,
        )

    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="API key is deactivated")
    if row["expires_at"] and row["expires_at"].timestamp() < time.time():
        raise HTTPException(status_code=403, detail="API key has expired")

    # Rate limiting (in-memory, per-key, per-minute window)
    prefix = row["key_prefix"]
    rpm = row["rate_limit_rpm"] or 60
    now = time.time()
    bucket = _rate_buckets.get(prefix, (0, now))
    if now - bucket[1] > 60:
        _rate_buckets[prefix] = (1, now)
    elif bucket[0] >= rpm:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({rpm} requests/minute)",
            headers={"Retry-After": str(int(60 - (now - bucket[1])))},
        )
    else:
        _rate_buckets[prefix] = (bucket[0] + 1, bucket[1])

    # Monthly quota check
    quota = row["monthly_quota"] or 0
    if quota > 0 and (row["calls_this_month"] or 0) >= quota:
        raise HTTPException(status_code=429, detail="Monthly API quota exceeded")

    # Update last_used_at and calls_this_month
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.api_keys SET last_used_at = now(), calls_this_month = calls_this_month + 1 WHERE id = $1",
            row["id"],
        )

    return dict(row)


async def record_api_usage(
    pool: asyncpg.Pool,
    api_key_id: str,
    tenant_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    latency_ms: int = 0,
) -> None:
    """Record API usage for metering and analytics."""
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO public.api_usage
                       (api_key_id, tenant_id, endpoint, method, status_code, latency_ms)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                api_key_id,
                tenant_id,
                endpoint,
                method,
                status_code,
                latency_ms,
            )
    except Exception as exc:
        logger.warning("Failed to record API usage: %s", exc)


# ---------------------------------------------------------------------------
# Webhook signing
# ---------------------------------------------------------------------------


def sign_webhook_payload(payload: bytes, secret: str) -> str:
    """Sign a webhook payload with HMAC-SHA256."""
    ts = str(int(time.time()))
    sig = hmac.new(
        secret.encode(),
        f"{ts}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    return f"t={ts},v1={sig}"


def verify_webhook_signature(
    payload: bytes, signature: str, secret: str, tolerance: int = 300
) -> bool:
    """Verify a webhook signature."""
    parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
    ts = parts.get("t", "")
    sig = parts.get("v1", "")
    if not ts or not sig:
        return False
    if abs(time.time() - int(ts)) > tolerance:
        return False
    expected = hmac.new(
        secret.encode(),
        f"{ts}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(sig, expected)
