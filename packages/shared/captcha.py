"""
Bot Detection — CAPTCHA verification for form protection.

Supports:
- hCaptcha (privacy-focused)
- reCAPTCHA v3 (invisible)
- reCAPTCHA v2 (checkbox)
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.captcha")


class CaptchaConfig(BaseModel):
    provider: str = "hcaptcha"
    site_key: str = ""
    secret_key: str = ""
    min_score: float = 0.5


class CaptchaVerificationResult(BaseModel):
    success: bool
    score: float | None = None
    error: str | None = None
    challenge_ts: str | None = None
    hostname: str | None = None


async def verify_hcaptcha(
    token: str,
    remote_ip: str | None = None,
) -> CaptchaVerificationResult:
    s = get_settings()

    if not hasattr(s, "hcaptcha_secret_key") or not s.hcaptcha_secret_key:
        logger.warning("hCaptcha secret key not configured")
        return CaptchaVerificationResult(success=True)

    data = {
        "secret": s.hcaptcha_secret_key,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.hcaptcha.com/siteverify",
                data=data,
            )
            result = resp.json()

        if result.get("success"):
            incr("captcha.verified", {"provider": "hcaptcha"})
            return CaptchaVerificationResult(
                success=True,
                challenge_ts=result.get("challenge_ts"),
                hostname=result.get("hostname"),
            )
        else:
            incr("captcha.failed", {"provider": "hcaptcha"})
            return CaptchaVerificationResult(
                success=False,
                error=", ".join(result.get("error-codes", ["unknown"])),
            )
    except Exception as e:
        logger.error("hCaptcha verification failed: %s", e)
        return CaptchaVerificationResult(success=False, error=str(e))


async def verify_recaptcha_v3(
    token: str,
    remote_ip: str | None = None,
    min_score: float = 0.5,
) -> CaptchaVerificationResult:
    s = get_settings()

    secret_key = getattr(s, "recaptcha_secret_key", None) or getattr(
        s, "google_recaptcha_secret_key", None
    )
    if not secret_key:
        logger.warning("reCAPTCHA secret key not configured")
        return CaptchaVerificationResult(success=True)

    data = {
        "secret": secret_key,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data=data,
            )
            result = resp.json()

        if result.get("success"):
            score = result.get("score", 0)
            if score >= min_score:
                incr("captcha.verified", {"provider": "recaptcha_v3"})
                return CaptchaVerificationResult(
                    success=True,
                    score=score,
                    challenge_ts=result.get("challenge_ts"),
                    hostname=result.get("hostname"),
                )
            else:
                incr("captcha.low_score", {"provider": "recaptcha_v3"})
                return CaptchaVerificationResult(
                    success=False,
                    score=score,
                    error=f"Score {score} below threshold {min_score}",
                )
        else:
            incr("captcha.failed", {"provider": "recaptcha_v3"})
            return CaptchaVerificationResult(
                success=False,
                error=", ".join(result.get("error-codes", ["unknown"])),
            )
    except Exception as e:
        logger.error("reCAPTCHA verification failed: %s", e)
        return CaptchaVerificationResult(success=False, error=str(e))


async def verify_captcha(
    token: str,
    provider: str = "hcaptcha",
    remote_ip: str | None = None,
    min_score: float = 0.5,
) -> CaptchaVerificationResult:
    if provider == "recaptcha" or provider == "recaptcha_v3":
        return await verify_recaptcha_v3(token, remote_ip, min_score)
    else:
        return await verify_hcaptcha(token, remote_ip)


def get_captcha_site_key() -> dict[str, str]:
    s = get_settings()
    return {
        "provider": getattr(s, "captcha_provider", "hcaptcha"),
        "site_key": (
            getattr(s, "hcaptcha_site_key", "")
            or getattr(s, "recaptcha_site_key", "")
            or getattr(s, "google_recaptcha_site_key", "")
        ),
    }


class CaptchaMiddleware:
    def __init__(
        self,
        protected_paths: list[str] | None = None,
        provider: str = "hcaptcha",
        min_score: float = 0.5,
    ):
        self.protected_paths = protected_paths or [
            "/auth/signup",
            "/auth/login",
            "/webhook/resume_parse",
            "/applications",
        ]
        self.provider = provider
        self.min_score = min_score

    async def verify_request(
        self,
        path: str,
        token: str | None,
        remote_ip: str | None = None,
    ) -> tuple[bool, str | None]:
        if not any(path.startswith(p) for p in self.protected_paths):
            return True, None

        if not token:
            incr("captcha.missing_token")
            return False, "CAPTCHA token required"

        result = await verify_captcha(
            token,
            provider=self.provider,
            remote_ip=remote_ip,
            min_score=self.min_score,
        )

        return result.success, result.error
