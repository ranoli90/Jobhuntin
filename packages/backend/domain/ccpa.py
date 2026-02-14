"""
CCPA Compliance — California Consumer Privacy Act rights.

Features:
  - Right to Know: What data is collected and sold
  - Right to Delete: Delete personal information
  - Right to Opt-Out: Do Not Sell My Personal Information
  - Right to Non-Discrimination: Equal service regardless of privacy choices
  - Data inventory and categorization
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.ccpa")


class CCPARequestType(str, Enum):
    KNOW = "know"
    DELETE = "delete"
    OPT_OUT = "opt_out"
    CORRECT = "correct"
    APPEAL = "appeal"
    PORTABILITY = "portability"


class CCPARequestStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    PROCESSING = "processing"
    COMPLETED = "completed"
    DENIED = "denied"
    EXPIRED = "expired"


@dataclass
class CCPARequest:
    id: str
    request_type: CCPARequestType
    user_id: str | None
    email: str
    phone: str | None
    status: CCPARequestStatus
    created_at: datetime
    verified_at: datetime | None
    completed_at: datetime | None
    details: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataCategory:
    category: str
    description: str
    sources: list[str]
    purposes: list[str]
    disclosed_to: list[str]
    retention_days: int
    is_sold: bool = False


DATA_INVENTORY: list[DataCategory] = [
    DataCategory(
        category="Identifiers",
        description="Name, email, phone, IP address, device identifiers",
        sources=["User provided", "Automatically collected"],
        purposes=["Account management", "Communication", "Security"],
        disclosed_to=["Service providers", "Third-party integrations"],
        retention_days=730,
        is_sold=False,
    ),
    DataCategory(
        category="Commercial Information",
        description="Transaction history, application records, billing info",
        sources=["User activity", "Payment processor"],
        purposes=["Service delivery", "Billing", "Support"],
        disclosed_to=["Payment processors", "Employers"],
        retention_days=730,
        is_sold=False,
    ),
    DataCategory(
        category="Internet Activity",
        description="Browsing history, search queries, interactions",
        sources=["Automatically collected"],
        purposes=["Personalization", "Analytics", "Improvement"],
        disclosed_to=["Analytics providers"],
        retention_days=365,
        is_sold=False,
    ),
    DataCategory(
        category="Professional Information",
        description="Resume, work history, skills, job preferences",
        sources=["User provided", "Parsed from resumes"],
        purposes=["Job matching", "Application submission"],
        disclosed_to=["Employers", "Job boards"],
        retention_days=730,
        is_sold=False,
    ),
    DataCategory(
        category="Inferences",
        description="Job match scores, preferences, behavioral predictions",
        sources=["Derived from other data"],
        purposes=["Service improvement", "Personalization"],
        disclosed_to=[],
        retention_days=365,
        is_sold=False,
    ),
]


class CCPAComplianceManager:
    REQUEST_EXPIRY_DAYS = 45
    VERIFICATION_WINDOW_HOURS = 24

    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    async def submit_request(
        self,
        request_type: CCPARequestType,
        email: str,
        phone: str | None = None,
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> CCPARequest:
        async with self._pool.acquire() as conn:
            request_id = await conn.fetchval(
                """
                INSERT INTO public.ccpa_requests
                    (request_type, user_id, email, phone, status, details)
                VALUES ($1, $2, $3, $4, 'pending', $5::jsonb)
                RETURNING id
                """,
                request_type.value,
                user_id,
                email.lower(),
                phone,
                json.dumps(details or {}),
            )

            await self._record_audit(
                conn,
                None,
                user_id,
                "CCPA_REQUEST_SUBMITTED",
                "ccpa_request",
                str(request_id),
                {"type": request_type.value, "email": email},
            )

        incr("ccpa.request_submitted", {"type": request_type.value})
        logger.info(
            "CCPA request submitted: id=%s type=%s email=%s",
            request_id,
            request_type.value,
            email,
        )

        return CCPARequest(
            id=str(request_id),
            request_type=request_type,
            user_id=user_id,
            email=email,
            phone=phone,
            status=CCPARequestStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            verified_at=None,
            completed_at=None,
            details=details or {},
        )

    async def verify_request(
        self,
        request_id: str,
        verification_code: str,
    ) -> tuple[bool, CCPARequest | None]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, request_type, user_id, email, phone, status,
                       created_at, verified_at, completed_at, details, response
                FROM public.ccpa_requests
                WHERE id = $1 AND verification_code = $2
                """,
                request_id,
                verification_code,
            )

            if not row:
                return False, None

            if row["status"] != "pending":
                return False, None

            await conn.execute(
                """
                UPDATE public.ccpa_requests
                SET status = 'verified', verified_at = now()
                WHERE id = $1
                """,
                request_id,
            )

            await self._record_audit(
                conn,
                None,
                row["user_id"],
                "CCPA_REQUEST_VERIFIED",
                "ccpa_request",
                request_id,
                {},
            )

        incr("ccpa.request_verified", {"type": row["request_type"]})

        return True, CCPARequest(
            id=str(row["id"]),
            request_type=CCPARequestType(row["request_type"]),
            user_id=str(row["user_id"]) if row["user_id"] else None,
            email=row["email"],
            phone=row["phone"],
            status=CCPARequestStatus.VERIFIED,
            created_at=row["created_at"],
            verified_at=datetime.now(timezone.utc),
            completed_at=row["completed_at"],
            details=row["details"]
            if isinstance(row["details"], dict)
            else json.loads(row["details"] or "{}"),
            response=row["response"]
            if isinstance(row["response"], dict)
            else json.loads(row["response"] or "{}"),
        )

    async def process_request(self, request_id: str) -> CCPARequest | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, request_type, user_id, email, phone, status,
                       created_at, verified_at, completed_at, details
                FROM public.ccpa_requests
                WHERE id = $1 AND status = 'verified'
                """,
                request_id,
            )

            if not row:
                return None

            await conn.execute(
                """
                UPDATE public.ccpa_requests
                SET status = 'processing'
                WHERE id = $1
                """,
                request_id,
            )

        request = CCPARequest(
            id=str(row["id"]),
            request_type=CCPARequestType(row["request_type"]),
            user_id=str(row["user_id"]) if row["user_id"] else None,
            email=row["email"],
            phone=row["phone"],
            status=CCPARequestStatus.PROCESSING,
            created_at=row["created_at"],
            verified_at=row["verified_at"],
            completed_at=None,
            details=row["details"]
            if isinstance(row["details"], dict)
            else json.loads(row["details"] or "{}"),
        )

        if request.request_type == CCPARequestType.KNOW:
            response = await self._handle_know_request(request)
        elif request.request_type == CCPARequestType.DELETE:
            response = await self._handle_delete_request(request)
        elif request.request_type == CCPARequestType.OPT_OUT:
            response = await self._handle_opt_out_request(request)
        elif request.request_type == CCPARequestType.PORTABILITY:
            response = await self._handle_portability_request(request)
        else:
            response = {"error": "Request type not implemented"}

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.ccpa_requests
                SET status = 'completed', completed_at = now(), response = $1::jsonb
                WHERE id = $2
                """,
                json.dumps(response),
                request_id,
            )

            await self._record_audit(
                conn,
                None,
                request.user_id,
                "CCPA_REQUEST_COMPLETED",
                "ccpa_request",
                request_id,
                {"type": request.request_type.value},
            )

        incr("ccpa.request_completed", {"type": request.request_type.value})
        request.status = CCPARequestStatus.COMPLETED
        request.completed_at = datetime.now(timezone.utc)
        request.response = response

        return request

    async def _handle_know_request(self, request: CCPARequest) -> dict[str, Any]:
        user_id = request.user_id
        if not user_id:
            user_id = await self._find_user_by_email(request.email)

        if not user_id:
            return {"error": "No user found with this email"}

        data_collected = await self._get_user_data_inventory(user_id)

        return {
            "categories_collected": [
                {
                    "category": cat.category,
                    "description": cat.description,
                    "sources": cat.sources,
                    "purposes": cat.purposes,
                    "disclosed_to": cat.disclosed_to,
                    "retention_days": cat.retention_days,
                    "is_sold": cat.is_sold,
                }
                for cat in DATA_INVENTORY
            ],
            "data_collected": data_collected,
            "third_parties": self._get_third_party_disclosures(),
        }

    async def _handle_delete_request(self, request: CCPARequest) -> dict[str, Any]:
        user_id = request.user_id
        if not user_id:
            user_id = await self._find_user_by_email(request.email)

        if not user_id:
            return {"error": "No user found with this email"}

        deleted = []

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM public.profiles WHERE user_id = $1", user_id
            )
            deleted.append(f"profiles: {result}")

            result = await conn.execute(
                "DELETE FROM public.user_preferences WHERE user_id = $1", user_id
            )
            deleted.append(f"user_preferences: {result}")

            result = await conn.execute(
                "DELETE FROM public.answer_memory WHERE user_id = $1", user_id
            )
            deleted.append(f"answer_memory: {result}")

            result = await conn.execute(
                """
                UPDATE public.users
                SET email = 'deleted_' || id::text || '@deleted',
                    full_name = '[DELETED]',
                    avatar_url = NULL,
                    linkedin_url = NULL,
                    resume_url = NULL
                WHERE id = $1
                """,
                user_id,
            )
            deleted.append(f"users: {result}")

        return {"deleted": deleted, "user_id": user_id}

    async def _handle_opt_out_request(self, request: CCPARequest) -> dict[str, Any]:
        user_id = request.user_id
        if not user_id:
            user_id = await self._find_user_by_email(request.email)

        if not user_id:
            return {"error": "No user found with this email"}

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.user_privacy_settings (user_id, do_not_sell, opted_out_at)
                VALUES ($1, true, now())
                ON CONFLICT (user_id) DO UPDATE SET do_not_sell = true, opted_out_at = now()
                """,
                user_id,
            )

        return {"opted_out": True, "user_id": user_id}

    async def _handle_portability_request(self, request: CCPARequest) -> dict[str, Any]:
        user_id = request.user_id
        if not user_id:
            user_id = await self._find_user_by_email(request.email)

        if not user_id:
            return {"error": "No user found with this email"}

        data = await self._get_user_data_inventory(user_id)
        return {"data": data, "format": "JSON"}

    async def _find_user_by_email(self, email: str) -> str | None:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT id::text FROM public.users WHERE LOWER(email) = LOWER($1)",
                email,
            )

    async def _get_user_data_inventory(self, user_id: str) -> dict[str, Any]:
        async with self._pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, created_at FROM public.users WHERE id = $1",
                user_id,
            )
            profile = await conn.fetchrow(
                "SELECT profile_data, resume_url FROM public.profiles WHERE user_id = $1",
                user_id,
            )
            applications = await conn.fetch(
                """
                SELECT id, status, created_at
                FROM public.applications WHERE user_id = $1 LIMIT 100
                """,
                user_id,
            )

        return {
            "account": dict(user) if user else None,
            "profile": dict(profile) if profile else None,
            "applications": [dict(a) for a in applications],
        }

    def _get_third_party_disclosures(self) -> list[dict[str, str]]:
        return [
            {"name": "Stripe", "purpose": "Payment processing", "data": "Billing info"},
            {"name": "Resend", "purpose": "Email delivery", "data": "Email address"},
            {"name": "OpenAI", "purpose": "AI matching", "data": "Job preferences"},
            {
                "name": "Job Boards",
                "purpose": "Job sourcing",
                "data": "Resume (with consent)",
            },
        ]

    async def get_user_opt_out_status(self, user_id: str) -> bool:
        async with self._pool.acquire() as conn:
            return (
                await conn.fetchval(
                    """
                SELECT do_not_sell FROM public.user_privacy_settings
                WHERE user_id = $1
                """,
                    user_id,
                )
                or False
            )

    async def set_opt_out_preference(
        self,
        user_id: str,
        do_not_sell: bool,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.user_privacy_settings (user_id, do_not_sell, opted_out_at)
                VALUES ($1, $2, CASE WHEN $2 THEN now() ELSE NULL END)
                ON CONFLICT (user_id) DO UPDATE SET
                    do_not_sell = $2,
                    opted_out_at = CASE WHEN $2 THEN now() ELSE NULL END
                """,
                user_id,
                do_not_sell,
            )

            await self._record_audit(
                conn,
                None,
                user_id,
                "DO_NOT_SELL_CHANGED",
                "user",
                user_id,
                {"do_not_sell": do_not_sell},
            )

        incr("ccpa.opt_out_changed", {"do_not_sell": str(do_not_sell).lower()})

    async def get_request_status(self, request_id: str) -> CCPARequest | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, request_type, user_id, email, phone, status,
                       created_at, verified_at, completed_at, details, response
                FROM public.ccpa_requests
                WHERE id = $1
                """,
                request_id,
            )

            if not row:
                return None

            return CCPARequest(
                id=str(row["id"]),
                request_type=CCPARequestType(row["request_type"]),
                user_id=str(row["user_id"]) if row["user_id"] else None,
                email=row["email"],
                phone=row["phone"],
                status=CCPARequestStatus(row["status"]),
                created_at=row["created_at"],
                verified_at=row["verified_at"],
                completed_at=row["completed_at"],
                details=row["details"]
                if isinstance(row["details"], dict)
                else json.loads(row["details"] or "{}"),
                response=row["response"]
                if isinstance(row["response"], dict)
                else json.loads(row["response"] or "{}"),
            )

    async def cleanup_expired_requests(self) -> int:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE public.ccpa_requests
                SET status = 'expired'
                WHERE status = 'pending'
                  AND created_at < now() - ($1 || ' days')::interval
                """,
                str(self.REQUEST_EXPIRY_DAYS),
            )
            count = int(result.split()[-1])

        incr("ccpa.requests_expired", None, count)
        return count

    async def _record_audit(
        self,
        conn: asyncpg.Connection,
        tenant_id: str | None,
        user_id: str | None,
        action: str,
        resource: str,
        resource_id: str,
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
            logger.warning("Failed to record audit: %s", e)


async def init_ccpa_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.ccpa_requests (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            request_type TEXT NOT NULL CHECK (request_type IN ('know', 'delete', 'opt_out', 'correct', 'appeal', 'portability')),
            user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
            email TEXT NOT NULL,
            phone TEXT,
            verification_code TEXT,
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'processing', 'completed', 'denied', 'expired')),
            details JSONB DEFAULT '{}',
            response JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            verified_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS public.user_privacy_settings (
            user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
            do_not_sell BOOLEAN NOT NULL DEFAULT false,
            opted_out_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_ccpa_requests_email ON public.ccpa_requests(email);
        CREATE INDEX IF NOT EXISTS idx_ccpa_requests_status ON public.ccpa_requests(status);
        CREATE INDEX IF NOT EXISTS idx_user_privacy_user_id ON public.user_privacy_settings(user_id);
        """
    )
    logger.info("CCPA tables initialized")
