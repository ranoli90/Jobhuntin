"""Webhook HMAC Signing — secure webhook payload verification.

Provides:
- HMAC-SHA256 signature generation
- Signature verification with timing-safe comparison
- Configurable secret per tenant
- Timestamp-based replay attack prevention
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.webhook_signing")


class WebhookSigner:
    def __init__(
        self,
        secret: str,
        algorithm: str = "sha256",
        timestamp_tolerance_seconds: int = 300,
    ):
        self.secret = secret.encode("utf-8")
        self.algorithm = algorithm
        self.timestamp_tolerance = timestamp_tolerance_seconds

    def sign(
        self,
        payload: bytes | str | dict[str, Any],
        include_timestamp: bool = True,
    ) -> str:
        if isinstance(payload, dict):
            payload = json.dumps(payload, separators=(",", ":"))

        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        if include_timestamp:
            timestamp = str(int(time.time()))
            payload_to_sign = f"{timestamp}.{payload.decode('utf-8')}".encode()
        else:
            timestamp = ""
            payload_to_sign = payload

        signature = hmac.new(
            self.secret,
            payload_to_sign,
            hashlib.sha256,
        ).hexdigest()

        incr("webhook.signed")

        if timestamp:
            return f"t={timestamp},v1={signature}"
        return f"v1={signature}"

    def verify(
        self,
        payload: bytes | str | dict[str, Any],
        signature_header: str,
    ) -> tuple[bool, str | None]:
        if isinstance(payload, dict):
            payload = json.dumps(payload, separators=(",", ":"))

        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        parts = {}
        for part in signature_header.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                parts[key] = value

        if "v1" not in parts:
            incr("webhook.verify_failed", {"reason": "missing_signature"})
            return False, "Missing signature"

        provided_signature = parts["v1"]

        if "t" in parts:
            timestamp = parts["t"]
            try:
                ts_int = int(timestamp)
            except ValueError:
                incr("webhook.verify_failed", {"reason": "invalid_timestamp"})
                return False, "Invalid timestamp"

            current_time = int(time.time())
            if abs(current_time - ts_int) > self.timestamp_tolerance_seconds:
                incr("webhook.verify_failed", {"reason": "expired_timestamp"})
                return False, "Timestamp expired"

            payload_to_verify = f"{timestamp}.{payload.decode('utf-8')}".encode()
        else:
            payload_to_verify = payload

        expected_signature = hmac.new(
            self.secret,
            payload_to_verify,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, provided_signature):
            incr("webhook.verify_failed", {"reason": "invalid_signature"})
            return False, "Invalid signature"

        incr("webhook.verify_success")
        return True, None

    def verify_stripe_signature(
        self,
        payload: bytes,
        signature_header: str,
    ) -> tuple[bool, str | None]:
        parts = {}
        for part in signature_header.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                parts[key] = value

        if "t" not in parts:
            return False, "Missing timestamp"

        timestamp = parts["t"]
        expected_signature = parts.get("v1")

        if not expected_signature:
            return False, "Missing signature"

        signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode()

        computed = hmac.new(
            self.secret,
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(computed, expected_signature):
            incr("webhook.stripe_verify_failed")
            return False, "Invalid Stripe signature"

        incr("webhook.stripe_verify_success")
        return True, None


def sign_webhook_payload(
    payload: bytes | str | dict[str, Any],
    secret: str | None = None,
) -> str:
    s = get_settings()
    secret = secret or s.webhook_signing_secret

    if not secret:
        raise ValueError("Webhook signing secret not configured")

    signer = WebhookSigner(secret)
    return signer.sign(payload)


def verify_webhook_signature(
    payload: bytes | str | dict[str, Any],
    signature_header: str,
    secret: str | None = None,
) -> tuple[bool, str | None]:
    s = get_settings()
    secret = secret or s.webhook_signing_secret

    if not secret:
        return False, "Webhook signing secret not configured"

    signer = WebhookSigner(secret)
    return signer.verify(payload, signature_header)


def generate_webhook_secret() -> str:
    import secrets

    return secrets.token_hex(32)


class WebhookDelivery:
    def __init__(
        self,
        endpoint_url: str,
        secret: str,
        max_retries: int = 5,
        timeout_seconds: float = 10.0,
    ):
        self.endpoint_url = endpoint_url
        self.secret = secret
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self._signer = WebhookSigner(secret)

    async def deliver(
        self,
        event_type: str,
        payload: dict[str, Any],
        event_id: str | None = None,
    ) -> tuple[bool, int | None]:
        import uuid

        import httpx

        event_id = event_id or str(uuid.uuid4())

        webhook_payload = {
            "id": event_id,
            "type": event_type,
            "created": int(time.time()),
            "data": payload,
        }

        payload_bytes = json.dumps(webhook_payload, separators=(",", ":")).encode(
            "utf-8"
        )
        signature = self._signer.sign(payload_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event-Type": event_type,
            "X-Webhook-Event-ID": event_id,
        }

        backoff = 1
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(
                        self.endpoint_url,
                        content=payload_bytes,
                        headers=headers,
                    )

                    if resp.status_code in (200, 201, 202, 204):
                        incr("webhook.delivered", {"event_type": event_type})
                        return True, resp.status_code

                    if resp.status_code >= 500 and attempt < self.max_retries - 1:
                        await self._backoff(backoff)
                        backoff *= 2
                        continue

                    incr(
                        "webhook.delivery_failed",
                        {"event_type": event_type, "status": str(resp.status_code)},
                    )
                    return False, resp.status_code

            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    await self._backoff(backoff)
                    backoff *= 2
                    continue
                incr("webhook.timeout", {"event_type": event_type})
                return False, None

            except Exception as e:
                logger.error("Webhook delivery error: %s", e)
                if attempt < self.max_retries - 1:
                    await self._backoff(backoff)
                    backoff *= 2
                    continue
                incr("webhook.error", {"event_type": event_type})
                return False, None

        return False, None

    async def _backoff(self, seconds: int):
        import asyncio

        await asyncio.sleep(seconds)
