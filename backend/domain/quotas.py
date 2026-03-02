"""Quota enforcement for tenant plan limits.

Provides check functions that raise QuotaExceededError when a tenant
has exhausted their plan allowance.
"""

from __future__ import annotations

import asyncpg
from shared.logging_config import get_logger

from packages.backend.domain.plans import plan_config_for
from packages.backend.domain.repositories import TenantRepo

logger = get_logger("sorce.quotas")


class QuotaExceededError(Exception):
    """Raised when a tenant exceeds a plan limit."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


async def check_can_create_application(
    conn: asyncpg.Connection,
    tenant_id: str,
    plan: str,
    plan_metadata: dict | None = None,
) -> None:
    """Raise QuotaExceededError if the tenant has exceeded their monthly
    application creation limit.

    Call this before inserting a new application row.
    """
    config = plan_config_for(plan, plan_metadata)
    current = await TenantRepo.count_monthly_applications(conn, tenant_id)

    if current >= config["max_monthly_applications"]:
        logger.warning(
            "Tenant %s quota exceeded: %d/%d monthly applications",
            tenant_id, current, config["max_monthly_applications"],
        )
        raise QuotaExceededError(
            code="QUOTA_EXCEEDED",
            message=(
                f"Monthly application quota reached ({current}/{config['max_monthly_applications']}). "
                f"Upgrade your plan for more applications."
            ),
        )


async def check_concurrent_limit(
    conn: asyncpg.Connection,
    tenant_id: str,
    plan: str,
    plan_metadata: dict | None = None,
) -> bool:
    """Check if the tenant has room for another concurrent PROCESSING application.

    Returns True if under limit, False if at/over limit.
    Used by the worker to skip tenants that are at their concurrent cap.
    """
    config = plan_config_for(plan, plan_metadata)
    processing = await TenantRepo.count_concurrent_processing(conn, tenant_id)

    if processing >= config["max_concurrent_applications"]:
        logger.info(
            "Tenant %s at concurrent limit: %d/%d PROCESSING",
            tenant_id, processing, config["max_concurrent_applications"],
        )
        return False
    return True
