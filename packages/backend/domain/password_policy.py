"""Password Policy — strength validation and enforcement.

Features:
  - Configurable password strength requirements
  - Common password blacklist checking
  - Password strength scoring
  - Breached password detection (haveibeenpwned API)
  - Per-tenant policy customization
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import timezone
from enum import StrEnum
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.password_policy")


class PasswordStrength(StrEnum):
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class PasswordPolicy:
    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special: bool = True
    min_special_chars: int = 1
    min_unique_chars: int = 6
    max_repeated_chars: int = 3
    prevent_common_passwords: bool = True
    prevent_personal_info: bool = True
    prevent_keyboard_patterns: bool = True
    prevent_sequential_chars: bool = True
    breach_check_enabled: bool = True
    password_history_count: int = 5
    max_age_days: int = 90


@dataclass
class PasswordValidationResult:
    is_valid: bool
    strength: PasswordStrength
    score: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


COMMON_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "123456",
    "12345678",
    "qwerty",
    "abc123",
    "monkey",
    "master",
    "dragon",
    "letmein",
    "login",
    "admin",
    "welcome",
    "football",
    "iloveyou",
    "trustno1",
    "sunshine",
    "princess",
    "shadow",
    "superman",
    "michael",
    "jennifer",
    "hunter",
    "hunter2",
    "baseball",
    "batman",
    "soccer",
    "charlie",
    "donald",
    "password!",
    "passw0rd",
    "p@ssword",
    "p@ssw0rd",
    "pa$$word",
    "password@1",
    "qwerty123",
    "qwer1234",
    "asdfgh",
    "zxcvbn",
    "1q2w3e4r",
    "1qaz2wsx",
    "jobhuntin",
    "jobhunting",
    "jobsearch",
    "resume",
    "career",
}

KEYBOARD_PATTERNS = {
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
    "qwerty",
    "asdfgh",
    "zxcvbn",
    "1234567890",
    "0987654321",
    "1qaz",
    "2wsx",
    "3edc",
    "4rfv",
    "5tgb",
    "6yhn",
    "7ujm",
    "8ik",
    "9ol",
    "0p",
    "qazwsx",
    "edcrfv",
    "tgbyhn",
}

SEQUENTIAL_PATTERNS = [
    "abc",
    "bcd",
    "cde",
    "def",
    "efg",
    "fgh",
    "ghi",
    "hij",
    "ijk",
    "jkl",
    "klm",
    "lmn",
    "mno",
    "nop",
    "opq",
    "pqr",
    "qrs",
    "rst",
    "stu",
    "tuv",
    "uvw",
    "vwx",
    "wxy",
    "xyz",
    "012",
    "123",
    "234",
    "345",
    "456",
    "567",
    "678",
    "789",
    "890",
]


class PasswordValidator:
    def __init__(self, policy: PasswordPolicy | None = None):
        self.policy = policy or PasswordPolicy()

    def validate(
        self,
        password: str,
        user_info: dict[str, Any] | None = None,
    ) -> PasswordValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []
        score = 0

        if len(password) < self.policy.min_length:
            errors.append(
                f"Password must be at least {self.policy.min_length} characters"
            )
        else:
            score += min(len(password) - self.policy.min_length + 1, 10)

        if len(password) > self.policy.max_length:
            errors.append(
                f"Password must not exceed {self.policy.max_length} characters"
            )

        if self.policy.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 5 if re.search(r"[A-Z]", password) else 0

        if self.policy.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 5 if re.search(r"[a-z]", password) else 0

        if self.policy.require_digits and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        else:
            score += 5 if re.search(r"\d", password) else 0

        if self.policy.require_special:
            special_count = len(
                re.findall(r'[!@#$%^&*()_+\-=\[\]{};\':"|,.<>/?`~]', password)
            )
            if special_count < self.policy.min_special_chars:
                errors.append(
                    f"Password must contain at least {self.policy.min_special_chars} special character(s)"
                )
            else:
                score += min(special_count * 3, 10)

        unique_chars = len(set(password.lower()))
        if unique_chars < self.policy.min_unique_chars:
            warnings.append(
                f"Password should contain at least {self.policy.min_unique_chars} unique characters"
            )
        else:
            score += min(unique_chars, 10)

        if self.policy.max_repeated_chars > 0:
            repeated = re.findall(
                r"(.)\1{" + str(self.policy.max_repeated_chars) + r",}", password
            )
            if repeated:
                errors.append(
                    f"Password cannot have more than {self.policy.max_repeated_chars} repeated character(s)"
                )

        if self.policy.prevent_common_passwords:
            lower_password = password.lower()
            if lower_password in COMMON_PASSWORDS:
                errors.append("Password is too common. Choose something unique")
                score = max(0, score - 20)
            for common in COMMON_PASSWORDS:
                if common in lower_password and len(common) >= 4:
                    warnings.append("Password contains a common word or pattern")
                    score = max(0, score - 5)
                    break

        if self.policy.prevent_personal_info and user_info:
            lower_password = password.lower()
            personal_fields = [
                "email",
                "name",
                "first_name",
                "last_name",
                "company",
                "phone",
            ]
            for personal_field in personal_fields:
                value = user_info.get(personal_field, "")
                if (
                    value
                    and len(str(value)) >= 3
                    and str(value).lower() in lower_password
                ):
                    errors.append(
                        f"Password should not contain your {personal_field.replace('_', ' ')}"
                    )
                    score = max(0, score - 10)
                    break

        if self.policy.prevent_keyboard_patterns:
            lower_password = password.lower()
            for pattern in KEYBOARD_PATTERNS:
                if pattern in lower_password and len(pattern) >= 4:
                    warnings.append("Password contains a keyboard pattern")
                    score = max(0, score - 5)
                    break

        if self.policy.prevent_sequential_chars:
            lower_password = password.lower()
            for pattern in SEQUENTIAL_PATTERNS:
                if pattern in lower_password:
                    warnings.append("Password contains sequential characters")
                    score = max(0, score - 5)
                    break

        strength = self._calculate_strength(score)

        if score < 30:
            suggestions.append("Try using a passphrase with multiple random words")
            suggestions.append(
                "Include a mix of uppercase, lowercase, numbers, and symbols"
            )
        elif score < 50:
            suggestions.append("Consider making your password longer")
            suggestions.append("Add more variety in character types")

        is_valid = len(errors) == 0 and score >= 30

        incr(
            "password.validated",
            {"strength": strength.value, "valid": str(is_valid).lower()},
        )

        return PasswordValidationResult(
            is_valid=is_valid,
            strength=strength,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _calculate_strength(self, score: int) -> PasswordStrength:
        if score < 20:
            return PasswordStrength.VERY_WEAK
        elif score < 35:
            return PasswordStrength.WEAK
        elif score < 50:
            return PasswordStrength.MEDIUM
        elif score < 70:
            return PasswordStrength.STRONG
        else:
            return PasswordStrength.VERY_STRONG

    async def check_password_breach(
        self,
        password: str,
        _http_client: Any = None,
    ) -> tuple[bool, int]:
        # Pwned Passwords API requires SHA1 (k-anonymity); see haveibeenpwned.com/API/v3
        sha1_hash = (
            hashlib.sha1(
                password.encode(),
                usedforsecurity=False
            ).hexdigest().upper()
        )  # nosemgrep: python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1
        )
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://api.pwnedpasswords.com/range/{prefix}"
                )
                if response.status_code != 200:
                    return False, 0

                for line in response.text.splitlines():
                    parts = line.strip().split(":")
                    if len(parts) == 2 and parts[0] == suffix:
                        count = int(parts[1])
                        incr("password.breached")
                        return True, count

                return False, 0
        except Exception as e:
            logger.warning("Breached password check failed: %s", e)
            return False, 0


class PasswordHistoryManager:
    def __init__(self, db_pool: asyncpg.Pool, policy: PasswordPolicy | None = None):
        self._pool = db_pool
        self.policy = policy or PasswordPolicy()

    async def add_to_history(
        self,
        user_id: str,
        password_hash: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.password_history
                    (user_id, password_hash)
                VALUES ($1, $2)
                """,
                user_id,
                password_hash,
            )

            await conn.execute(
                """
                DELETE FROM public.password_history
                WHERE user_id = $1 AND id NOT IN (
                    SELECT id FROM public.password_history
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                )
                """,
                user_id,
                self.policy.password_history_count,
            )

    async def is_password_in_history(
        self,
        user_id: str,
        password_hash: str,
    ) -> bool:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM public.password_history
                    WHERE user_id = $1 AND password_hash = $2
                )
                """,
                user_id,
                password_hash,
            )

    async def get_password_age_days(
        self,
        user_id: str,
    ) -> int | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT created_at FROM public.password_history
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id,
            )

            if not row:
                return None

            from datetime import datetime

            age = datetime.now(timezone.utc) - row["created_at"]
            return age.days

    async def is_password_expired(
        self,
        user_id: str,
    ) -> bool:
        if self.policy.max_age_days <= 0:
            return False

        age = await self.get_password_age_days(user_id)
        if age is None:
            return False

        return age > self.policy.max_age_days


async def init_password_history_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.password_history (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_password_history_user_id
            ON public.password_history(user_id);
        """
    )

    try:
        await conn.execute(
            """
            ALTER TABLE public.users
            ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS password_expires_at TIMESTAMPTZ
            """
        )
    except Exception:
        pass

    logger.info("Password history table initialized")
