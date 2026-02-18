"""
Webhook delivery with exponential backoff retry logic.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import httpx
from shared.logging_config import get_logger

logger = get_logger("sorce.webhook")


@dataclass
class WebhookConfig:
    """Configuration for webhook delivery."""
    max_retries: int = 5
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    timeout_seconds: float = 10.0
    backoff_multiplier: float = 2.0


@dataclass
class WebhookAttempt:
    """Record of a webhook delivery attempt."""
    webhook_id: str
    attempt_number: int
    timestamp: datetime
    success: bool
    status_code: int | None
    error: str | None
    next_retry: datetime | None


class WebhookDelivery:
    """Handles webhook delivery with retry logic."""

    def __init__(self, config: WebhookConfig | None = None):
        self.config = config or WebhookConfig()
        self._pending: dict[str, list[WebhookAttempt]] = {}

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.config.initial_delay_seconds * (self.config.backoff_multiplier ** attempt)
        return min(delay, self.config.max_delay_seconds)

    def _sign_payload(self, payload: str, secret: str, timestamp: int) -> str:
        """Create HMAC signature for webhook payload."""
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    async def deliver(
        self,
        url: str,
        payload: dict[str, Any],
        secret: str,
        webhook_id: str,
    ) -> bool:
        """
        Deliver webhook with exponential backoff retry.

        Returns True if delivery succeeded, False if all retries exhausted.
        """
        payload_str = json.dumps(payload)
        timestamp = int(datetime.now().timestamp())
        signature = self._sign_payload(payload_str, secret, timestamp)

        self._pending[webhook_id] = []

        for attempt in range(self.config.max_retries + 1):
            delay = self._calculate_delay(attempt) if attempt > 0 else 0

            if delay > 0:
                logger.info(
                    "Webhook retry scheduled",
                    extra={
                        "webhook_id": webhook_id,
                        "attempt": attempt + 1,
                        "delay_seconds": delay,
                    },
                )
                await asyncio.sleep(delay)

            try:
                async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                    response = await client.post(
                        url,
                        content=payload_str,
                        headers={
                            "Content-Type": "application/json",
                            "X-Webhook-Signature": signature,
                            "X-Webhook-ID": webhook_id,
                        },
                    )

                attempt_record = WebhookAttempt(
                    webhook_id=webhook_id,
                    attempt_number=attempt + 1,
                    timestamp=datetime.now(),
                    success=response.status_code < 400,
                    status_code=response.status_code,
                    error=None if response.status_code < 400 else f"HTTP {response.status_code}",
                    next_retry=None,
                )
                self._pending[webhook_id].append(attempt_record)

                if response.status_code < 400:
                    logger.info(
                        "Webhook delivered successfully",
                        extra={
                            "webhook_id": webhook_id,
                            "url": url,
                            "attempts": attempt + 1,
                        },
                    )
                    return True

                # Non-2xx response - retry
                logger.warning(
                    "Webhook returned non-success status",
                    extra={
                        "webhook_id": webhook_id,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                    },
                )

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                attempt_record = WebhookAttempt(
                    webhook_id=webhook_id,
                    attempt_number=attempt + 1,
                    timestamp=datetime.now(),
                    success=False,
                    status_code=None,
                    error=str(e),
                    next_retry=None,
                )
                self._pending[webhook_id].append(attempt_record)

                logger.warning(
                    "Webhook delivery failed",
                    extra={
                        "webhook_id": webhook_id,
                        "error": str(e),
                        "attempt": attempt + 1,
                    },
                )

        # All retries exhausted
        logger.error(
            "Webhook delivery failed after all retries",
            extra={
                "webhook_id": webhook_id,
                "url": url,
                "total_attempts": self.config.max_retries + 1,
            },
        )
        return False

    async def deliver_with_callback(
        self,
        url: str,
        payload: dict[str, Any],
        secret: str,
        webhook_id: str,
        on_success: Callable[[str], None] | None = None,
        on_failure: Callable[[str, list[WebhookAttempt]], None] | None = None,
    ) -> bool:
        """Deliver webhook and call callbacks based on result."""
        success = await self.deliver(url, payload, secret, webhook_id)

        if success and on_success:
            on_success(webhook_id)
        elif not success and on_failure:
            on_failure(webhook_id, self._pending.get(webhook_id, []))

        return success

    def get_attempts(self, webhook_id: str) -> list[WebhookAttempt]:
        """Get all delivery attempts for a webhook."""
        return self._pending.get(webhook_id, [])


# Global instance
_webhook_delivery = WebhookDelivery()


async def send_webhook(
    url: str,
    event_type: str,
    data: dict[str, Any],
    secret: str,
) -> bool:
    """
    Send a webhook notification.

    Usage:
        await send_webhook(
            url="https://example.com/webhooks",
            event_type="job.matched",
            data={"job_id": "123", "score": 95},
            secret="whsec_xxx",
        )
    """
    import uuid

    webhook_id = str(uuid.uuid4())
    payload = {
        "id": webhook_id,
        "event": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }

    return await _webhook_delivery.deliver(url, payload, secret, webhook_id)
