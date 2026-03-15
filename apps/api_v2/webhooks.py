"""Webhook Delivery Engine — fires signed webhook payloads on application status changes.

Called by the worker after status transitions. Retries up to 3 times with exponential backoff.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import asyncpg
from api_v2.auth import sign_webhook_payload

from shared.logging_config import get_logger

logger = get_logger("sorce.webhooks")

EVENT_MAP = {
    "APPLIED": "application.completed",
    "SUBMITTED": "application.completed",
    "COMPLETED": "application.completed",
    "REGISTERED": "application.completed",
    "FAILED": "application.failed",
    "REQUIRES_INPUT": "application.hold",
    "QUEUED": "application.queued",
}

MAX_RETRIES = 3
RETRY_DELAYS = [5, 30, 120]  # seconds


async def _schedule_retry(
    pool: asyncpg.Pool,
    endpoint: dict,
    payload: bytes,
    signature: str,
    attempt: int,
    delay: int,
) -> None:
    """Schedule a webhook retry after delay."""
    await asyncio.sleep(delay)
    await _deliver_webhook(pool, endpoint, payload, signature, attempt)


async def fire_webhooks_for_status_change(
    pool: asyncpg.Pool,
    tenant_id: str,
    application_id: str,
    new_status: str,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fire all matching webhooks for a tenant when an application status changes.
    Returns list of delivery results.
    """
    event_type = EVENT_MAP.get(new_status)
    if not event_type:
        return []

    async with pool.acquire() as conn:
        endpoints = await conn.fetch(
            """SELECT id, url, secret, events FROM public.webhook_endpoints
               WHERE tenant_id = $1 AND is_active = true AND failure_count < 10""",
            tenant_id,
        )

    if not endpoints:
        return []

    payload = {
        "event": event_type,
        "application_id": str(application_id),
        "status": new_status,
        "tenant_id": str(tenant_id),
        "timestamp": int(time.time()),
        **(metadata or {}),
    }
    payload_bytes = json.dumps(payload).encode()

    results = []
    for ep in endpoints:
        if event_type not in (ep["events"] or []):
            continue

        signature = sign_webhook_payload(payload_bytes, ep["secret"])
        result = await _deliver_webhook(pool, ep, payload_bytes, signature)
        results.append(result)

    return results


async def _deliver_webhook(
    pool: asyncpg.Pool,
    endpoint: dict,
    payload: bytes,
    signature: str,
    attempt: int = 1,
) -> dict[str, Any]:
    """Deliver a single webhook with retry logic."""
    try:
        import httpx
    except ImportError:
        logger.warning("httpx not installed — webhook delivery disabled")
        return {
            "endpoint_id": str(endpoint["id"]),
            "status": "skipped",
            "reason": "httpx not installed",
        }

    headers = {
        "Content-Type": "application/json",
        "X-Sorce-Signature": signature,
        "X-Sorce-Event": "application.status_changed",
        "User-Agent": "Sorce-Webhooks/2.0",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                endpoint["url"],
                content=payload,
                headers=headers,
            )

        status_code = resp.status_code
        response_body = resp.text[:500]
        success = 200 <= status_code < 300

        # Record delivery
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO public.webhook_deliveries
                       (endpoint_id, event_type, payload, response_status, response_body, attempt)
                   VALUES ($1, $2, $3::jsonb, $4, $5, $6)""",
                endpoint["id"],
                "application.status_changed",
                payload.decode(),
                status_code,
                response_body,
                attempt,
            )

            if success:
                await conn.execute(
                    "UPDATE public.webhook_endpoints SET last_success_at = now(), failure_count = 0 WHERE id = $1",
                    endpoint["id"],
                )
            else:
                await conn.execute(
                    "UPDATE public.webhook_endpoints SET last_failure_at = now(), "
                    "failure_count = failure_count + 1 WHERE id = $1",
                    endpoint["id"],
                )

                # Retry asynchronously
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAYS[attempt - 1]
                    logger.info(
                        "Webhook retry %d for %s scheduled in %ds",
                        attempt + 1,
                        endpoint["url"],
                        delay,
                    )
                    # Schedule retry asynchronously to avoid blocking
                    asyncio.create_task(
                        _schedule_retry(
                            pool, endpoint, payload, signature, attempt + 1, delay
                        )
                    )
                    return {
                        "endpoint_id": str(endpoint["id"]),
                        "url": endpoint["url"],
                        "status": "retry_scheduled",
                        "attempt": attempt,
                        "next_attempt_in": delay,
                    }

        return {
            "endpoint_id": str(endpoint["id"]),
            "url": endpoint["url"],
            "status": "delivered" if success else "failed",
            "status_code": status_code,
            "attempt": attempt,
        }

    except Exception as exc:
        logger.error("Webhook delivery failed for %s: %s", endpoint["url"], exc)

        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO public.webhook_deliveries
                       (endpoint_id, event_type, payload, response_status, response_body, attempt)
                   VALUES ($1, $2, $3::jsonb, 0, $4, $5)""",
                endpoint["id"],
                "application.status_changed",
                payload.decode(),
                str(exc)[:500],
                attempt,
            )
            await conn.execute(
                "UPDATE public.webhook_endpoints SET last_failure_at = now(
    ), failure_count = failure_count + 1 WHERE id = $1",
                endpoint["id"],
            )

        if attempt < MAX_RETRIES:
            delay = RETRY_DELAYS[attempt - 1]
            logger.info(
                "Webhook retry %d for %s scheduled in %ds",
                attempt + 1,
                endpoint["url"],
                delay,
            )
            # Schedule retry asynchronously to avoid blocking
            asyncio.create_task(
                _schedule_retry(pool, endpoint, payload, signature, attempt + 1, delay)
            )
            return {
                "endpoint_id": str(endpoint["id"]),
                "url": endpoint["url"],
                "status": "retry_scheduled",
                "error": str(exc),
                "attempt": attempt,
                "next_attempt_in": delay,
            }

        return {
            "endpoint_id": str(endpoint["id"]),
            "url": endpoint["url"],
            "status": "failed",
            "error": str(exc),
            "attempt": attempt,
        }


async def fire_staffing_batch_completed(
    pool: asyncpg.Pool,
    tenant_id: str,
    batch_id: str,
    results: dict[str, Any],
) -> list[dict[str, Any]]:
    """Fire webhook when a staffing batch completes."""
    async with pool.acquire() as conn:
        endpoints = await conn.fetch(
            """SELECT id, url, secret, events FROM public.webhook_endpoints
               WHERE tenant_id = $1 AND is_active = true
                 AND 'staffing.batch_completed' = ANY(events)""",
            tenant_id,
        )

    if not endpoints:
        return []

    payload = {
        "event": "staffing.batch_completed",
        "batch_id": str(batch_id),
        "tenant_id": str(tenant_id),
        "timestamp": int(time.time()),
        **results,
    }
    payload_bytes = json.dumps(payload).encode()

    delivery_results = []
    for ep in endpoints:
        signature = sign_webhook_payload(payload_bytes, ep["secret"])
        r = await _deliver_webhook(pool, ep, payload_bytes, signature)
        delivery_results.append(r)

    return delivery_results
