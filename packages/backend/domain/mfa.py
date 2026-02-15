"""
Multi-Factor Authentication (MFA) — TOTP and WebAuthn support.

Features:
  - TOTP (Time-based One-Time Password) via authenticator apps
  - WebAuthn (FIDO2) for hardware keys and biometrics
  - Recovery codes for account recovery
  - MFA enforcement for admin accounts
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import asyncpg
from shared.logging_config import get_logger

from shared.metrics import incr

logger = get_logger("sorce.mfa")


class MFAType(str, Enum):
    TOTP = "totp"
    WEBAUTHN = "webauthn"
    RECOVERY = "recovery"


@dataclass
class TOTPConfig:
    secret: str
    issuer: str = "JobHuntin"
    digits: int = 6
    period: int = 30
    algorithm: str = "SHA1"

    def get_provisioning_uri(self, email: str) -> str:
        label = f"{self.issuer}:{email}"
        params = [
            f"secret={self.secret}",
            f"issuer={self.issuer}",
            f"algorithm={self.algorithm}",
            f"digits={self.digits}",
            f"period={self.period}",
        ]
        return f"otpauth://totp/{label}?{'&'.join(params)}"


@dataclass
class WebAuthnCredential:
    credential_id: str
    public_key: str
    sign_count: int
    transports: list[str] = field(default_factory=list)
    aaguid: str | None = None


@dataclass
class MFAEnrollment:
    id: str
    user_id: str
    mfa_type: MFAType
    is_verified: bool
    is_primary: bool
    created_at: datetime
    last_used_at: datetime | None
    config: dict[str, Any] = field(default_factory=dict)


class TOTPManager:
    ISSUER = "JobHuntin"
    DIGITS = 6
    PERIOD = 30

    @staticmethod
    def generate_secret() -> str:
        return secrets.token_hex(20).upper()

    @staticmethod
    def generate_recovery_codes(count: int = 8) -> list[str]:
        return [secrets.token_hex(4).upper() for _ in range(count)]

    @classmethod
    def verify_totp(
        cls,
        secret: str,
        code: str,
        window: int = 1,
    ) -> bool:
        if not code or len(code) != cls.DIGITS or not code.isdigit():
            return False

        secret_bytes = base64.b32decode(secret, case_insensitive=True)
        current_time = int(time.time())

        for offset in range(-window, window + 1):
            counter = (current_time + (offset * cls.PERIOD)) // cls.PERIOD
            expected = cls._generate_totp(secret_bytes, counter)
            if hmac.compare_digest(code, expected):
                return True

        return False

    @classmethod
    def _generate_totp(cls, secret: bytes, counter: int) -> str:
        counter_bytes = struct.pack(">Q", counter)
        hmac_hash = hmac.new(secret, counter_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code = struct.unpack(">I", hmac_hash[offset : offset + 4])[0]
        code = code & 0x7FFFFFFF
        code = code % (10**cls.DIGITS)
        return str(code).zfill(cls.DIGITS)

    @classmethod
    def create_totp_config(cls, email: str) -> tuple[str, str]:
        secret = cls.generate_secret()
        config = TOTPConfig(secret=secret, issuer=cls.ISSUER)
        uri = config.get_provisioning_uri(email)
        return secret, uri


class WebAuthnManager:
    CHALLENGE_LENGTH = 32

    @staticmethod
    def generate_challenge() -> str:
        return secrets.token_urlsafe(WebAuthnManager.CHALLENGE_LENGTH)

    @staticmethod
    def verify_webauthn_response(
        credential_id: str,
        client_data_json: str,
        authenticator_data: str,
        signature: str,
        expected_challenge: str,
        expected_origin: str,
        stored_public_key: str,
        stored_sign_count: int,
    ) -> tuple[bool, int]:
        try:
            client_data = json.loads(base64.urlsafe_b64decode(client_data_json + "=="))

            if client_data.get("type") != "webauthn.get":
                logger.warning("Invalid WebAuthn type: %s", client_data.get("type"))
                return False, stored_sign_count

            if client_data.get("challenge") != expected_challenge:
                logger.warning("Challenge mismatch")
                return False, stored_sign_count

            origin = client_data.get("origin", "")
            if expected_origin not in origin:
                logger.warning("Origin mismatch: %s vs %s", origin, expected_origin)
                return False, stored_sign_count

            auth_data = base64.urlsafe_b64decode(authenticator_data + "==")

            if len(auth_data) < 37:
                logger.warning("Authenticator data too short")
                return False, stored_sign_count

            sign_count = struct.unpack(">I", auth_data[33:37])[0]

            if sign_count <= stored_sign_count and stored_sign_count != 0:
                logger.warning("Possible cloned authenticator")
                return False, stored_sign_count

            public_key_bytes = base64.urlsafe_b64decode(stored_public_key + "==")
            sig_bytes = base64.urlsafe_b64decode(signature + "==")

            client_data_hash = hashlib.sha256(
                base64.urlsafe_b64decode(client_data_json + "==")
            ).digest()

            verification_data = auth_data + client_data_hash

            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import ec

            public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(), public_key_bytes
            )
            public_key.verify(
                sig_bytes,
                verification_data,
                ec.ECDSA(hashes.SHA256()),
            )

            return True, sign_count

        except Exception as e:
            logger.warning("WebAuthn verification failed: %s", e)
            return False, stored_sign_count


class MFAManager:
    MAX_RECOVERY_CODES = 8
    MFA_REQUIRE_FOR_ROLES = {"OWNER", "ADMIN", "COMPLIANCE_OFFICER"}

    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    async def enroll_totp(
        self,
        user_id: str,
        email: str,
    ) -> tuple[str, str]:
        secret, uri = TOTPManager.create_totp_config(email)

        async with self._pool.acquire() as conn:
            enrollment_id = await conn.fetchval(
                """
                INSERT INTO public.user_mfa_enrollments
                    (user_id, mfa_type, is_verified, is_primary, config)
                VALUES ($1, 'totp', false, false, $2::jsonb)
                RETURNING id
                """,
                user_id,
                json.dumps({"secret": secret, "issuer": TOTPManager.ISSUER}),
            )

        incr("mfa.totp_enrollment_started")
        return str(enrollment_id), uri

    async def verify_totp_enrollment(
        self,
        enrollment_id: str,
        code: str,
    ) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT config, user_id FROM public.user_mfa_enrollments
                WHERE id = $1 AND mfa_type = 'totp' AND is_verified = false
                """,
                enrollment_id,
            )

            if not row:
                return False

            config = row["config"]
            if isinstance(config, str):
                config = json.loads(config)

            secret = config.get("secret", "")
            if not TOTPManager.verify_totp(secret, code):
                return False

            recovery_codes = TOTPManager.generate_recovery_codes()
            hashed_codes = [
                hashlib.sha256(c.encode()).hexdigest() for c in recovery_codes
            ]

            await conn.execute(
                """
                UPDATE public.user_mfa_enrollments
                SET is_verified = true, is_primary = true, verified_at = now()
                WHERE id = $1
                """,
                enrollment_id,
            )

            await conn.execute(
                """
                UPDATE public.user_mfa_enrollments
                SET is_primary = false
                WHERE user_id = $1 AND id != $2 AND mfa_type = 'totp'
                """,
                row["user_id"],
                enrollment_id,
            )

            for hashed_code in hashed_codes:
                await conn.execute(
                    """
                    INSERT INTO public.mfa_recovery_codes
                        (user_id, code_hash, used)
                    VALUES ($1, $2, false)
                    """,
                    row["user_id"],
                    hashed_code,
                )

        incr("mfa.totp_enrollment_verified")
        return True, recovery_codes

    async def verify_totp(
        self,
        user_id: str,
        code: str,
    ) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, config FROM public.user_mfa_enrollments
                WHERE user_id = $1 AND mfa_type = 'totp'
                  AND is_verified = true AND is_primary = true
                """,
                user_id,
            )

            if not row:
                return False

            config = row["config"]
            if isinstance(config, str):
                config = json.loads(config)

            secret = config.get("secret", "")
            if not TOTPManager.verify_totp(secret, code):
                return False

            await conn.execute(
                """
                UPDATE public.user_mfa_enrollments
                SET last_used_at = now()
                WHERE id = $1
                """,
                row["id"],
            )

        incr("mfa.totp_verified")
        return True

    async def verify_recovery_code(
        self,
        user_id: str,
        code: str,
    ) -> bool:
        code_hash = hashlib.sha256(code.upper().encode()).hexdigest()

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE public.mfa_recovery_codes
                SET used = true, used_at = now()
                WHERE user_id = $1 AND code_hash = $2 AND used = false
                """,
                user_id,
                code_hash,
            )

            if result == "UPDATE 0":
                return False

        incr("mfa.recovery_code_used")
        return True

    async def get_remaining_recovery_codes(self, user_id: str) -> int:
        async with self._pool.acquire() as conn:
            return (
                await conn.fetchval(
                    """
                SELECT COUNT(*)::int FROM public.mfa_recovery_codes
                WHERE user_id = $1 AND used = false
                """,
                    user_id,
                )
                or 0
            )

    async def regenerate_recovery_codes(self, user_id: str) -> list[str]:
        new_codes = TOTPManager.generate_recovery_codes()
        hashed_codes = [hashlib.sha256(c.encode()).hexdigest() for c in new_codes]

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.mfa_recovery_codes
                SET used = true, used_at = now()
                WHERE user_id = $1 AND used = false
                """,
                user_id,
            )

            for hashed_code in hashed_codes:
                await conn.execute(
                    """
                    INSERT INTO public.mfa_recovery_codes
                        (user_id, code_hash, used)
                    VALUES ($1, $2, false)
                    """,
                    user_id,
                    hashed_code,
                )

        incr("mfa.recovery_codes_regenerated")
        return new_codes

    async def is_mfa_enabled(self, user_id: str) -> bool:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM public.user_mfa_enrollments
                    WHERE user_id = $1 AND is_verified = true
                )
                """,
                user_id,
            )

    async def require_mfa_for_role(self, user_id: str, role: str) -> bool:
        if role not in self.MFA_REQUIRE_FOR_ROLES:
            return False

        async with self._pool.acquire() as conn:
            has_mfa = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM public.user_mfa_enrollments
                    WHERE user_id = $1 AND is_verified = true
                )
                """,
                user_id,
            )

            if not has_mfa:
                return True

            return False

    async def list_user_mfa_methods(self, user_id: str) -> list[MFAEnrollment]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, mfa_type, is_verified, is_primary,
                       created_at, last_used_at, config
                FROM public.user_mfa_enrollments
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id,
            )

            return [
                MFAEnrollment(
                    id=str(r["id"]),
                    user_id=str(r["user_id"]),
                    mfa_type=MFAType(r["mfa_type"]),
                    is_verified=r["is_verified"],
                    is_primary=r["is_primary"],
                    created_at=r["created_at"],
                    last_used_at=r["last_used_at"],
                    config=r["config"]
                    if isinstance(r["config"], dict)
                    else json.loads(r["config"] or "{}"),
                )
                for r in rows
            ]

    async def disable_mfa(
        self,
        user_id: str,
        enrollment_id: str | None = None,
    ) -> bool:
        async with self._pool.acquire() as conn:
            if enrollment_id:
                result = await conn.execute(
                    """
                    DELETE FROM public.user_mfa_enrollments
                    WHERE id = $1 AND user_id = $2
                    """,
                    enrollment_id,
                    user_id,
                )
            else:
                result = await conn.execute(
                    """
                    DELETE FROM public.user_mfa_enrollments
                    WHERE user_id = $1
                    """,
                    user_id,
                )
                await conn.execute(
                    """
                    UPDATE public.mfa_recovery_codes
                    SET used = true, used_at = now()
                    WHERE user_id = $1 AND used = false
                    """,
                    user_id,
                )

        incr("mfa.disabled")
        return result != "DELETE 0"


async def init_mfa_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.user_mfa_enrollments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            mfa_type TEXT NOT NULL CHECK (mfa_type IN ('totp', 'webauthn')),
            is_verified BOOLEAN NOT NULL DEFAULT false,
            is_primary BOOLEAN NOT NULL DEFAULT false,
            config JSONB NOT NULL DEFAULT '{}',
            verified_at TIMESTAMPTZ,
            last_used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(user_id, mfa_type, is_primary)
        );

        CREATE TABLE IF NOT EXISTS public.mfa_recovery_codes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            code_hash TEXT NOT NULL,
            used BOOLEAN NOT NULL DEFAULT false,
            used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_mfa_enrollments_user_id
            ON public.user_mfa_enrollments(user_id);

        CREATE INDEX IF NOT EXISTS idx_mfa_recovery_codes_user_id
            ON public.mfa_recovery_codes(user_id);
        """
    )
    logger.info("MFA tables initialized")
