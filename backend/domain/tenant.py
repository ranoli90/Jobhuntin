"""Tenant context resolution, guards, and auto-provisioning.

Provides:
  - TenantContext: the per-request identity envelope
  - resolve_tenant_context(): JWT user_id → tenant lookup (auto-creates FREE tenant if none)
  - assert_tenant_owns(): guard that a resource belongs to the expected tenant
  - TenantScopeError: raised on tenant mismatch
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.tenant")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TenantContext:
    """Per-request identity: who is acting, under which tenant, with what roles."""

    tenant_id: str
    user_id: str
    roles: list[str]
    plan: str  # FREE, PRO, ENTERPRISE

    @property
    def is_owner(self) -> bool:
        return "OWNER" in self.roles

    @property
    def is_admin(self) -> bool:
        return "ADMIN" in self.roles or "OWNER" in self.roles

    @property
    def is_member(self) -> bool:
        return len(self.roles) > 0


class TenantScopeError(Exception):
    """Raised when a resource does not belong to the expected tenant."""

    pass


# ---------------------------------------------------------------------------
# Resolution: user_id → TenantContext (with auto-provisioning)
# ---------------------------------------------------------------------------


async def resolve_tenant_context(
    conn: asyncpg.Connection,
    user_id: str,
) -> TenantContext:
    """Look up the user's tenant membership.

    If the user has no tenant_members rows, auto-create a personal FREE tenant
    and make them OWNER. Returns the resolved TenantContext.
    """
    # 1. Look up existing membership (take first tenant — default)
    row = await conn.fetchrow(
        """
        SELECT tm.tenant_id, tm.role, t.plan
        FROM   public.tenant_members tm
        JOIN   public.tenants t ON t.id = tm.tenant_id
        WHERE  tm.user_id = $1
        ORDER  BY tm.created_at ASC
        LIMIT  1
        """,
        user_id,
    )

    if row is not None:
        # Fetch all roles for this user in this tenant
        roles_rows = await conn.fetch(
            """
            SELECT role FROM public.tenant_members
            WHERE  tenant_id = $1 AND user_id = $2
            """,
            str(row["tenant_id"]),
            user_id,
        )
        roles = [str(r["role"]) for r in roles_rows]
        return TenantContext(
            tenant_id=str(row["tenant_id"]),
            user_id=user_id,
            roles=roles,
            plan=str(row["plan"]),
        )

    # 2. Auto-provision: create personal tenant + OWNER membership
    logger.info("Auto-provisioning FREE tenant for user %s", user_id)
    tenant_id = str(uuid.uuid4())
    slug = f"user-{user_id[:8]}-{uuid.uuid4().hex[:6]}"

    # nosemgrep: python.lang.security.audit.sqli.asyncpg-sqli.asyncpg-sqli - parameterized $1..$3
    await conn.execute(
        """
        INSERT INTO public.tenants (id, name, slug, plan)
        VALUES ($1, $2, $3, 'FREE')
        """,
        tenant_id,
        "Personal",
        slug,
    )
    await conn.execute(
        """
        INSERT INTO public.tenant_members (tenant_id, user_id, role)
        VALUES ($1, $2, 'OWNER')
        """,
        tenant_id,
        user_id,
    )

    return TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=["OWNER"],
        plan="FREE",
    )


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def assert_tenant_owns(
    resource: dict,
    tenant_id: str,
    resource_name: str = "resource",
) -> None:
    """Raise TenantScopeError if the resource's tenant_id does not match.
    Callers should catch this and return 403.
    """
    res_tenant = str(resource.get("tenant_id", ""))
    if res_tenant != tenant_id:
        raise TenantScopeError(f"{resource_name} does not belong to tenant {tenant_id}")


def require_role(ctx: TenantContext, *allowed_roles: str) -> None:
    """Raise TenantScopeError if the user doesn't have any of the allowed roles."""
    if not any(r in ctx.roles for r in allowed_roles):
        raise TenantScopeError(
            f"User {ctx.user_id} lacks required role(s): {allowed_roles}"
        )


async def require_system_admin(conn: asyncpg.Connection, user_id: str) -> None:
    """Raise TenantScopeError if the user is not a system admin.
    System admin is indicated by users.is_system_admin = true.
    """
    row = await conn.fetchrow(
        "SELECT is_system_admin FROM public.users WHERE id = $1",
        user_id,
    )
    if row is None or not row["is_system_admin"]:
        raise TenantScopeError(f"User {user_id} is not a system admin")


async def require_tenant_admin_or_system(
    conn: asyncpg.Connection,
    ctx: TenantContext,
) -> None:
    """Require ADMIN/OWNER on the tenant, or system admin."""
    if ctx.is_admin:
        return
    await require_system_admin(conn, ctx.user_id)
