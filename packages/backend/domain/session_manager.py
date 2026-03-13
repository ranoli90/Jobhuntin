"""Session management — track and revoke user sessions.

Provides session tracking with device fingerprinting, session invalidation
on password change or security events, and integration with the audit log.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.sessions")


@dataclass
class SessionInfo:
    session_id: str
    user_id: str
    tenant_id: str | None
    device_fingerprint: str
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_revoked: bool = False
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "device_fingerprint": self.device_fingerprint,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_revoked": self.is_revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_reason": self.revoked_reason,
            "metadata": self.metadata,
        }


class SessionManager:
    DEFAULT_SESSION_DURATION_HOURS = 24 * 7
    MAX_SESSIONS_PER_USER = 10
    CLEANUP_EXPIRED_SESSIONS_DAYS = 30

    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    @staticmethod
    def generate_device_fingerprint(
        user_agent: str | None,
        ip_address: str | None,
        additional_data: dict[str, Any] | None = None,
    ) -> str:
        components = [
            user_agent or "",
            ip_address or "",
        ]
        if additional_data:
            for k in sorted(additional_data.keys()):
                components.append(f"{k}={additional_data[k]}")
        combined = "|".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    @staticmethod
    def generate_session_id() -> str:
        return secrets.token_urlsafe(32)

    async def create_session(
        self,
        user_id: str,
        tenant_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
        duration_hours: int | None = None,
    ) -> SessionInfo:
        duration = duration_hours or self.DEFAULT_SESSION_DURATION_HOURS
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=duration)
        session_id = self.generate_session_id()
        device_fp = self.generate_device_fingerprint(user_agent, ip_address)

        async with self._pool.acquire() as conn:
            await self._enforce_session_limit(conn, user_id)

            await conn.execute(
                """
                INSERT INTO public.user_sessions
                    (session_id, user_id, tenant_id, device_fingerprint,
                     ip_address, user_agent, created_at, last_activity_at,
                     expires_at, metadata, is_revoked)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, false)
                """,
                session_id,
                user_id,
                tenant_id,
                device_fp,
                ip_address,
                user_agent,
                now,
                now,
                expires_at,
                json.dumps(metadata or {}),
            )

            await self._record_audit(
                conn,
                tenant_id,
                user_id,
                "SESSION_CREATED",
                "session",
                session_id,
                {
                    "device_fingerprint": device_fp,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                },
            )

        incr("sessions.created")
        logger.info(
            "Session created: user=%s session=%s",
            user_id,
            session_id[:8],
        )

        return SessionInfo(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            device_fingerprint=device_fp,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_activity_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )

    async def validate_session(
        self,
        session_id: str,
        user_id: str,
        update_activity: bool = True,
    ) -> SessionInfo | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT session_id, user_id, tenant_id, device_fingerprint,
                       ip_address, user_agent, created_at, last_activity_at,
                       expires_at, is_revoked, revoked_at, revoked_reason, metadata
                FROM public.user_sessions
                WHERE session_id = $1 AND user_id = $2
                """,
                session_id,
                user_id,
            )

            if not row:
                incr("sessions.validation_failed", {"reason": "not_found"})
                return None

            session = self._row_to_session(row)

            if session.is_revoked:
                incr("sessions.validation_failed", {"reason": "revoked"})
                logger.warning(
                    "Attempt to use revoked session: user=%s session=%s reason=%s",
                    user_id,
                    session_id[:8],
                    session.revoked_reason,
                )
                return None

            if session.is_expired():
                incr("sessions.validation_failed", {"reason": "expired"})
                return None

            if update_activity:
                await conn.execute(
                    """
                    UPDATE public.user_sessions
                    SET last_activity_at = now()
                    WHERE session_id = $1
                    """,
                    session_id,
                )

            incr("sessions.validated")
            return session

    async def revoke_session(
        self,
        session_id: str,
        reason: str,
        revoked_by_user_id: str | None = None,
        user_id: str | None = None,
    ) -> dict | None:
        """Revoke a session. If user_id is provided, only revoke if session belongs to that user (prevents cross-user revocation)."""
        now = datetime.now(timezone.utc)

        async with self._pool.acquire() as conn:
            if user_id:
                row = await conn.fetchrow(
                    """
                    UPDATE public.user_sessions
                    SET is_revoked = true,
                        revoked_at = $1,
                        revoked_reason = $2
                    WHERE session_id = $3 AND user_id = $4 AND is_revoked = false
                    RETURNING user_id, tenant_id, metadata
                    """,
                    now,
                    reason,
                    session_id,
                    user_id,
                )
            else:
                row = await conn.fetchrow(
                    """
                    UPDATE public.user_sessions
                    SET is_revoked = true,
                        revoked_at = $1,
                        revoked_reason = $2
                    WHERE session_id = $3 AND is_revoked = false
                    RETURNING user_id, tenant_id, metadata
                    """,
                    now,
                    reason,
                    session_id,
                )

            if not row:
                return None

            await self._record_audit(
                conn,
                row["tenant_id"],
                revoked_by_user_id or row["user_id"],
                "SESSION_REVOKED",
                "session",
                session_id,
                {"reason": reason},
            )

        incr("sessions.revoked", {"reason": reason.replace(" ", "_")})
        logger.info(
            "Session revoked: session=%s reason=%s",
            session_id[:8],
            reason,
        )
        return row

    async def update_session_jti(self, session_id: str, jti: str) -> None:
        """Store jti in session metadata for Redis revocation on revoke."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.user_sessions
                SET metadata = jsonb_set(COALESCE(metadata, '{}'), '{jti}', to_jsonb($2::text))
                WHERE session_id = $1
                """,
                session_id,
                jti,
            )

    async def revoke_all_user_sessions(
        self,
        user_id: str,
        reason: str,
        except_session_id: str | None = None,
    ) -> tuple[int, list[str]]:
        """Revoke all user sessions. Returns (count, list of jtis for Redis revocation)."""
        now = datetime.now(timezone.utc)

        async with self._pool.acquire() as conn:
            if except_session_id:
                rows = await conn.fetch(
                    """
                    SELECT session_id, metadata
                    FROM public.user_sessions
                    WHERE user_id = $1 AND is_revoked = false AND session_id != $2
                    """,
                    user_id,
                    except_session_id,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT session_id, metadata
                    FROM public.user_sessions
                    WHERE user_id = $1 AND is_revoked = false
                    """,
                    user_id,
                )

            jtis: list[str] = []
            for row in rows:
                meta = row.get("metadata")
                if isinstance(meta, dict) and meta.get("jti"):
                    jtis.append(str(meta["jti"]))

            if except_session_id:
                result = await conn.execute(
                    """
                    UPDATE public.user_sessions
                    SET is_revoked = true,
                        revoked_at = $1,
                        revoked_reason = $2
                    WHERE user_id = $3
                      AND is_revoked = false
                      AND session_id != $4
                    """,
                    now,
                    reason,
                    user_id,
                    except_session_id,
                )
            else:
                result = await conn.execute(
                    """
                    UPDATE public.user_sessions
                    SET is_revoked = true,
                        revoked_at = $1,
                        revoked_reason = $2
                    WHERE user_id = $3 AND is_revoked = false
                    """,
                    now,
                    reason,
                    user_id,
                )

            count = int(result.split()[-1]) if result else 0

            await self._record_audit(
                conn,
                None,
                user_id,
                "ALL_SESSIONS_REVOKED",
                "user",
                user_id,
                {"reason": reason, "count": count},
            )

        incr("sessions.bulk_revoked", {"reason": reason.replace(" ", "_")}, count)
        logger.info(
            "All sessions revoked for user=%s count=%d reason=%s",
            user_id,
            count,
            reason,
        )
        return count, jtis

    async def revoke_sessions_on_password_change(self, user_id: str) -> int:
        count, _ = await self.revoke_all_user_sessions(
            user_id,
            reason="PASSWORD_CHANGED",
        )
        incr("sessions.revoked_on_password_change")
        return count

    async def revoke_sessions_on_security_event(
        self,
        user_id: str,
        event: str,
    ) -> int:
        count, _ = await self.revoke_all_user_sessions(
            user_id,
            reason=f"SECURITY_EVENT:{event}",
        )
        incr("sessions.revoked_on_security_event", {"event": event})
        return count

    async def list_user_sessions(
        self,
        user_id: str,
        include_revoked: bool = False,
        include_expired: bool = False,
    ) -> list[SessionInfo]:
        async with self._pool.acquire() as conn:
            conditions = ["user_id = $1"]
            if not include_revoked:
                conditions.append("is_revoked = false")
            if not include_expired:
                conditions.append("expires_at > now()")

            rows = await conn.fetch(
                """
                SELECT session_id, user_id, tenant_id, device_fingerprint,
                       ip_address, user_agent, created_at, last_activity_at,
                       expires_at, is_revoked, revoked_at, revoked_reason, metadata
                FROM public.user_sessions
                WHERE {" AND ".join(conditions)}
                ORDER BY last_activity_at DESC
                """,
                user_id,
            )

            return [self._row_to_session(row) for row in rows]

    async def get_active_session_count(self, user_id: str) -> int:
        async with self._pool.acquire() as conn:
            return (
                await conn.fetchval(
                    """
                SELECT COUNT(*)::int
                FROM public.user_sessions
                WHERE user_id = $1
                  AND is_revoked = false
                  AND expires_at > now()
                """,
                    user_id,
                )
                or 0
            )

    async def cleanup_expired_sessions(self, days_old: int | None = None) -> int:
        threshold_days = days_old or self.CLEANUP_EXPIRED_SESSIONS_DAYS
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM public.user_sessions
                WHERE (expires_at < now() - ($1 || ' days')::interval)
                   OR (is_revoked = true AND revoked_at < now() - ($1 || ' days')::interval)
                """,
                str(threshold_days),
            )
            count = int(result.split()[-1]) if result else 0

        incr("sessions.cleanup_deleted", None, count)
        logger.info("Cleaned up %d expired/revoked sessions", count)
        return count

    async def detect_suspicious_activity(
        self,
        user_id: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> dict[str, Any]:
        async with self._pool.acquire() as conn:
            sessions = await conn.fetch(
                """
                SELECT DISTINCT ip_address, user_agent, device_fingerprint
                FROM public.user_sessions
                WHERE user_id = $1
                  AND is_revoked = false
                  AND expires_at > now()
                """,
                user_id,
            )

            if not sessions:
                return {"suspicious": False, "reasons": []}

            existing_ips = {s["ip_address"] for s in sessions if s["ip_address"]}
            existing_devices = {s["device_fingerprint"] for s in sessions}
            current_device = self.generate_device_fingerprint(user_agent, ip_address)

            reasons = []

            if ip_address and ip_address not in existing_ips and len(existing_ips) > 0:
                reasons.append("NEW_IP_ADDRESS")

            if current_device not in existing_devices and len(existing_devices) > 0:
                reasons.append("NEW_DEVICE")

            active_count = len(sessions)
            if active_count >= self.MAX_SESSIONS_PER_USER:
                reasons.append("MAX_SESSIONS_APPROACHED")

            return {
                "suspicious": len(reasons) > 0,
                "reasons": reasons,
                "active_sessions": active_count,
                "known_ips": list(existing_ips),
            }

    async def _enforce_session_limit(
        self,
        conn: asyncpg.Connection,
        user_id: str,
    ) -> None:
        count = await conn.fetchval(
            """
            SELECT COUNT(*)::int
            FROM public.user_sessions
            WHERE user_id = $1 AND is_revoked = false AND expires_at > now()
            """,
            user_id,
        )

        if count >= self.MAX_SESSIONS_PER_USER:
            oldest_row = await conn.fetchrow(
                """
                SELECT session_id, metadata FROM public.user_sessions
                WHERE user_id = $1 AND is_revoked = false AND expires_at > now()
                ORDER BY last_activity_at ASC
                LIMIT 1
                """,
                user_id,
            )
            if oldest_row:
                oldest = oldest_row["session_id"]
                await conn.execute(
                    """
                    UPDATE public.user_sessions
                    SET is_revoked = true,
                        revoked_at = now(),
                        revoked_reason = 'SESSION_LIMIT_EXCEEDED'
                    WHERE session_id = $1
                    """,
                    oldest,
                )
                logger.info(
                    "Evicted oldest session for user=%s session=%s",
                    user_id,
                    oldest[:8],
                )
                # Revoke JTI in Redis so evicted session token is invalid
                meta = oldest_row.get("metadata")
                jti = meta.get("jti") if isinstance(meta, dict) else None
                if jti:
                    try:
                        from shared.config import get_settings
                        from shared.session_revocation import revoke_jti_in_redis

                        s = get_settings()
                        await revoke_jti_in_redis(jti, s.redis_url, s.env.value)
                    except Exception as e:
                        logger.warning("Failed to revoke evicted session JTI in Redis: %s", e)

    async def _record_audit(
        self,
        conn: asyncpg.Connection,
        tenant_id: str | None,
        user_id: str | None,
        action: str,
        resource: str,
        resource_id: str | None,
        details: dict[str, Any],
    ) -> None:
        try:
            await conn.execute(
                """
                INSERT INTO public.audit_log
                    (tenant_id, user_id, action, resource, resource_id, details)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                """,
                tenant_id,
                user_id,
                action,
                resource,
                resource_id,
                json.dumps(details),
            )
        except Exception as e:
            logger.warning("Failed to record audit event: %s", e)

    def _row_to_session(self, row: asyncpg.Record) -> SessionInfo:
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        return SessionInfo(
            session_id=row["session_id"],
            user_id=str(row["user_id"]),
            tenant_id=str(row["tenant_id"]) if row["tenant_id"] else None,
            device_fingerprint=row["device_fingerprint"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=row["created_at"],
            last_activity_at=row["last_activity_at"],
            expires_at=row["expires_at"],
            is_revoked=row["is_revoked"],
            revoked_at=row["revoked_at"],
            revoked_reason=row["revoked_reason"],
            metadata=metadata or {},
        )


async def init_session_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            tenant_id UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
            device_fingerprint TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            is_revoked BOOLEAN NOT NULL DEFAULT false,
            revoked_at TIMESTAMPTZ,
            revoked_reason TEXT,
            metadata JSONB DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id
            ON public.user_sessions(user_id);

        CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at
            ON public.user_sessions(expires_at);

        CREATE INDEX IF NOT EXISTS idx_user_sessions_device_fp
            ON public.user_sessions(device_fingerprint);
        """
    )
    logger.info("Session table initialized")
