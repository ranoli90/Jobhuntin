from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg
import pyotp


class MFAManager:
    """MFA Manager for TOTP and recovery code management."""

    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self.db_pool = db_pool

    @staticmethod
    def generate_secret() -> str:
        """Generate a TOTP secret."""
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(secret: str, username: str, issuer_name: str) -> str:
        """Get TOTP provisioning URI."""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username, issuer_name=issuer_name
        )

    @staticmethod
    def verify(secret: str, otp: str) -> bool:
        """Verify a TOTP code."""
        totp_obj = pyotp.TOTP(secret)
        return totp_obj.verify(otp)

    async def enroll_totp(self, user_id: str, email: str) -> tuple[str, str]:
        """Enroll a user in TOTP MFA."""
        secret = self.generate_secret()
        uri = self.get_provisioning_uri(secret, email, "JobHuntin")

        enrollment_id = str(uuid.uuid4())
        config = {"secret": secret}

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.user_mfa_enrollments
                (id, user_id, mfa_type, config, is_verified, created_at)
                VALUES ($1, $2, 'totp', $3, false, $4)
                """,
                enrollment_id,
                user_id,
                json.dumps(config),
                datetime.now(timezone.utc),
            )

        return (enrollment_id, uri)

    async def verify_totp_enrollment(
        self, enrollment_id: str, code: str, user_id: str
    ) -> tuple[bool, list[str] | None] | bool:
        """Verify TOTP enrollment with a code."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT config, user_id FROM public.user_mfa_enrollments
                WHERE id = $1 AND user_id = $2
                """,
                enrollment_id,
                user_id,
            )

            if not row:
                return False

            config = (
                row["config"]
                if isinstance(row["config"], dict)
                else json.loads(row["config"] or "{}")
            )
            secret = config.get("secret", "")

            if not self.verify(secret, code):
                return False

            # Mark as verified and generate recovery codes
            recovery_codes = [str(uuid.uuid4()).replace("-", "")[:8] for _ in range(10)]
            recovery_config = {"codes": recovery_codes, "used": []}

            await conn.execute(
                """
                UPDATE public.user_mfa_enrollments
                SET is_verified = true,
                    config = jsonb_set(config, '{recovery_codes}', $1::jsonb),
                    updated_at = $2
                WHERE id = $3
                """,
                json.dumps(recovery_config),
                datetime.now(timezone.utc),
                enrollment_id,
            )

            return (True, recovery_codes)

    async def verify_totp(self, user_id: str, code: str) -> bool:
        """Verify a TOTP code for authentication."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT config FROM public.user_mfa_enrollments
                WHERE user_id = $1 AND mfa_type = 'totp' AND is_verified = true
                """,
                user_id,
            )

            for row in rows:
                config = (
                    row["config"]
                    if isinstance(row["config"], dict)
                    else json.loads(row["config"] or "{}")
                )
                secret = config.get("secret", "")
                if self.verify(secret, code):
                    # Update last_used_at
                    await conn.execute(
                        """
                        UPDATE public.user_mfa_enrollments
                        SET last_used_at = $1
                        WHERE user_id = $2 AND mfa_type = 'totp' AND is_verified = true
                        """,
                        datetime.now(timezone.utc),
                        user_id,
                    )
                    return True

        return False

    async def verify_recovery_code(self, user_id: str, code: str) -> bool:
        """Verify a recovery code."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, config FROM public.user_mfa_enrollments
                WHERE user_id = $1 AND mfa_type = 'totp' AND is_verified = true
                """,
                user_id,
            )

            for row in rows:
                config = (
                    row["config"]
                    if isinstance(row["config"], dict)
                    else json.loads(row["config"] or "{}")
                )
                recovery_config = config.get("recovery_codes", {})
                codes = recovery_config.get("codes", [])
                used = recovery_config.get("used", [])

                if code in codes and code not in used:
                    # Mark as used
                    used.append(code)
                    recovery_config["used"] = used
                    config["recovery_codes"] = recovery_config

                    await conn.execute(
                        """
                        UPDATE public.user_mfa_enrollments
                        SET config = $1, last_used_at = $2
                        WHERE id = $3
                        """,
                        json.dumps(config),
                        datetime.now(timezone.utc),
                        row["id"],
                    )
                    return True

        return False

    async def regenerate_recovery_codes(self, user_id: str) -> list[str]:
        """Regenerate recovery codes for a user."""
        new_codes = [str(uuid.uuid4()).replace("-", "")[:8] for _ in range(10)]

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT config FROM public.user_mfa_enrollments
                WHERE user_id = $1 AND mfa_type = 'totp' AND is_verified = true
                ORDER BY created_at DESC LIMIT 1
                """,
                user_id,
            )

            if row:
                config = (
                    row["config"]
                    if isinstance(row["config"], dict)
                    else json.loads(row["config"] or "{}")
                )
                config["recovery_codes"] = {"codes": new_codes, "used": []}

                await conn.execute(
                    """
                    UPDATE public.user_mfa_enrollments
                    SET config = $1, updated_at = $2
                    WHERE user_id = $3 AND mfa_type = 'totp' AND is_verified = true
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    json.dumps(config),
                    datetime.now(timezone.utc),
                    user_id,
                )

        return new_codes

    async def get_remaining_recovery_codes(self, user_id: str) -> int:
        """Get count of remaining recovery codes."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT config FROM public.user_mfa_enrollments
                WHERE user_id = $1 AND mfa_type = 'totp' AND is_verified = true
                ORDER BY created_at DESC LIMIT 1
                """,
                user_id,
            )

            if row:
                config = (
                    row["config"]
                    if isinstance(row["config"], dict)
                    else json.loads(row["config"] or "{}")
                )
                recovery_config = config.get("recovery_codes", {})
                codes = recovery_config.get("codes", [])
                used = recovery_config.get("used", [])
                return len([c for c in codes if c not in used])

        return 0

    async def is_mfa_enabled(self, user_id: str) -> bool:
        """Check if MFA is enabled for a user."""
        async with self.db_pool.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM public.user_mfa_enrollments
                WHERE user_id = $1 AND mfa_type = 'totp' AND is_verified = true
                """,
                user_id,
            )
            return count > 0 if count else False

    async def list_user_mfa_methods(self, user_id: str) -> list[Any]:
        """List all MFA methods for a user."""
        from enum import Enum

        class MFAType(Enum):
            TOTP = "totp"

        class MFAMethod:
            def __init__(
                self,
                id: str,
                mfa_type: MFAType,
                is_verified: bool,
                is_primary: bool,
                created_at: datetime,
                last_used_at: datetime | None,
            ):
                self.id = id
                self.mfa_type = mfa_type
                self.is_verified = is_verified
                self.is_primary = is_primary
                self.created_at = created_at
                self.last_used_at = last_used_at

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, mfa_type, is_verified, created_at, last_used_at
                FROM public.user_mfa_enrollments
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id,
            )

            methods = []
            for i, row in enumerate(rows):
                methods.append(
                    MFAMethod(
                        id=str(row["id"]),
                        mfa_type=MFAType(row["mfa_type"]),
                        is_verified=bool(row["is_verified"]),
                        is_primary=i == 0,  # First is primary
                        created_at=row["created_at"],
                        last_used_at=row.get("last_used_at"),
                    )
                )

            return methods

    async def disable_mfa(self, user_id: str, enrollment_id: str | None) -> bool:
        """Disable MFA for a user."""
        async with self.db_pool.acquire() as conn:
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

            result_str = str(result)  # type: ignore[arg-type]
            return result_str == "DELETE 1" or result_str.startswith("DELETE")
