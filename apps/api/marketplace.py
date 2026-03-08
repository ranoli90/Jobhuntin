"""Blueprint Marketplace API — browse, install, submit, review, and author payouts.

Mounted at /marketplace prefix by api/main.py.
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.domain.audit import record_audit_event
from backend.domain.tenant import TenantContext, TenantScopeError, require_system_admin
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.api.marketplace")

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


def _get_pool() -> asyncpg.Pool:
    return (_ for _ in ()).throw(NotImplementedError("Pool not injected"))


def _get_tenant_ctx() -> TenantContext:
    return (_ for _ in ()).throw(NotImplementedError("Tenant ctx not injected"))


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class SubmitBlueprintRequest(BaseModel):
    name: str
    slug: str
    description: str
    long_description: str = ""
    category: str = "general"
    version: str = "1.0.0"
    source_code: dict[str, Any] = {}
    config_schema: dict[str, Any] = {}
    price_cents: int = 0


class InstallBlueprintRequest(BaseModel):
    config: dict[str, Any] = {}


class ReviewRequest(BaseModel):
    rating: int
    review_text: str = ""


class BlueprintResponse(BaseModel):
    """Blueprint details response."""

    id: str
    slug: str
    name: str
    description: str
    category: str
    author_name: str
    version: str
    install_count: int
    rating_avg: float
    rating_count: int
    price_cents: int
    is_featured: bool


# ---------------------------------------------------------------------------
# Browse
# ---------------------------------------------------------------------------


@router.get("/blueprints")
async def list_blueprints(
    category: str | None = None,
    search: str | None = None,
    featured: bool = False,
    sort: str = "popular",
    limit: int = Query(default=20, le=50),
    offset: int = 0,
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Browse marketplace blueprints (public — no auth required)."""
    # nosemgrep: python.lang.security.audit.sqli.asyncpg-sqli.asyncpg-sqli - order from whitelist, values in params
    base = """
        SELECT id, slug, name, description, category, author_name, version,
               install_count, rating_avg, rating_count, price_cents, is_featured,
               icon_url, published_at
        FROM public.marketplace_blueprints
        WHERE approval_status = 'approved' AND is_active = true
    """
    params: list[Any] = []
    idx = 0

    if category:
        idx += 1
        base += f" AND category = ${idx}"
        params.append(category)
    if search:
        idx += 1
        base += f" AND (name ILIKE ${idx} OR description ILIKE ${idx})"
        params.append(f"%{search}%")
    if featured:
        base += " AND is_featured = true"

    # Secure sort parameter with whitelist validation
    allowed_sort_options = {
        "popular": "install_count DESC",
        "rating": "rating_avg DESC",
        "newest": "published_at DESC",
        "name": "name ASC",
        "install_count": "install_count DESC",
        "rating_avg": "rating_avg DESC",
        "published_at": "published_at DESC",
    }

    # Validate and get safe sort clause
    if sort not in allowed_sort_options:
        logger.warning(f"Invalid sort parameter: {sort}")
        order = allowed_sort_options["install_count"]  # Default fallback
    else:
        order = allowed_sort_options[sort]

    # Use parameterized queries to prevent SQL injection
    base += f" ORDER BY {order}"

    idx += 1
    base += f" LIMIT ${idx}"
    params.append(limit)
    idx += 1
    base += f" OFFSET ${idx}"
    params.append(offset)

    async with db.acquire() as conn:
        rows = await conn.fetch(base, *params)
        total = await conn.fetchval(
            "SELECT COUNT(*)::int FROM public.marketplace_blueprints WHERE approval_status = 'approved' AND is_active = true"
        )

    return {"blueprints": [dict(r) for r in rows], "total": total or 0}


@router.get("/blueprints/{slug}")
async def get_blueprint(
    slug: str,
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get blueprint details by slug."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT *, (SELECT COUNT(*)::int FROM public.blueprint_installations WHERE blueprint_id = mb.id) AS installs
               FROM public.marketplace_blueprints mb WHERE slug = $1 AND is_active = true""",
            slug,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return dict(row)


@router.get("/categories")
async def list_categories(
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """List available blueprint categories with counts."""
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT category, COUNT(*)::int AS count
            FROM public.marketplace_blueprints
            WHERE approval_status = 'approved' AND is_active = true
            GROUP BY category ORDER BY count DESC
        """
        )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Install / Uninstall
# ---------------------------------------------------------------------------


@router.post("/blueprints/{blueprint_id}/install")
async def install_blueprint(
    blueprint_id: str,
    body: InstallBlueprintRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Install a marketplace blueprint for the current tenant."""
    from shared.validators import validate_uuid

    validate_uuid(blueprint_id, "blueprint_id")
    async with db.acquire() as conn:
        bp = await conn.fetchrow(
            "SELECT * FROM public.marketplace_blueprints WHERE id = $1 AND approval_status = 'approved'",
            blueprint_id,
        )
        if not bp:
            raise HTTPException(
                status_code=404, detail="Blueprint not found or not approved"
            )

        row = await conn.fetchrow(
            """
            INSERT INTO public.blueprint_installations (blueprint_id, tenant_id, installed_by, version, config)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            ON CONFLICT (blueprint_id, tenant_id) DO UPDATE
                SET version = $4, config = $5::jsonb, is_active = true, installed_at = now()
            RETURNING *
            """,
            blueprint_id,
            ctx.tenant_id,
            ctx.user_id,
            bp["version"],
            json.dumps(body.config),
        )

        await conn.execute(
            "UPDATE public.marketplace_blueprints SET install_count = install_count + 1 WHERE id = $1",
            blueprint_id,
        )

        await record_audit_event(
            conn,
            ctx.tenant_id,
            ctx.user_id,
            action="marketplace.blueprint_installed",
            resource="blueprint",
            resource_id=blueprint_id,
            details={"name": bp["name"], "version": bp["version"]},
        )

    incr("marketplace.install")
    return {"status": "installed", "installation": dict(row)}


@router.delete("/blueprints/{blueprint_id}/install")
async def uninstall_blueprint(
    blueprint_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Uninstall a blueprint from the current tenant."""
    from shared.validators import validate_uuid

    validate_uuid(blueprint_id, "blueprint_id")
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE public.blueprint_installations SET is_active = false WHERE blueprint_id = $1 AND tenant_id = $2",
            blueprint_id,
            ctx.tenant_id,
        )
    return {"status": "uninstalled"}


# ---------------------------------------------------------------------------
# Submit (Authors)
# ---------------------------------------------------------------------------


@router.post("/blueprints/submit")
async def submit_blueprint(
    body: SubmitBlueprintRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Submit a new blueprint to the marketplace for review."""
    if ctx.plan not in ("PRO", "TEAM", "ENTERPRISE"):
        raise HTTPException(
            status_code=403, detail="Blueprint submission requires a paid plan"
        )

    async with db.acquire() as conn:
        existing = await conn.fetchval(
            "SELECT id FROM public.marketplace_blueprints WHERE slug = $1",
            body.slug,
        )
        if existing:
            raise HTTPException(
                status_code=409, detail=f"Slug '{body.slug}' already taken"
            )

        tenant = await conn.fetchrow(
            "SELECT name FROM public.tenants WHERE id = $1", ctx.tenant_id
        )
        author_name = tenant["name"] if tenant else "Unknown"

        row = await conn.fetchrow(
            """
            INSERT INTO public.marketplace_blueprints
                (slug, name, description, long_description, category, author_tenant_id,
                 author_name, version, source_code, config_schema, price_cents, approval_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb, $11, 'pending')
            RETURNING id, slug, name, approval_status
            """,
            body.slug,
            body.name,
            body.description,
            body.long_description,
            body.category,
            ctx.tenant_id,
            author_name,
            body.version,
            json.dumps(body.source_code),
            json.dumps(body.config_schema),
            body.price_cents,
        )

        await record_audit_event(
            conn,
            ctx.tenant_id,
            ctx.user_id,
            action="marketplace.blueprint_submitted",
            resource="blueprint",
            resource_id=str(row["id"]),
            details={"name": body.name, "slug": body.slug},
        )

    incr("marketplace.submit")
    return {"status": "submitted_for_review", "blueprint": dict(row)}


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


@router.post("/blueprints/{blueprint_id}/review")
async def review_blueprint(
    blueprint_id: str,
    body: ReviewRequest,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Submit a review for an installed blueprint."""
    from shared.validators import validate_uuid

    validate_uuid(blueprint_id, "blueprint_id")
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.blueprint_reviews (blueprint_id, tenant_id, user_id, rating, review_text)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (blueprint_id, user_id) DO UPDATE SET rating = $4, review_text = $5
            """,
            blueprint_id,
            ctx.tenant_id,
            ctx.user_id,
            body.rating,
            body.review_text,
        )
        # Update aggregate rating
        await conn.execute(
            """
            UPDATE public.marketplace_blueprints SET
                rating_avg = (SELECT COALESCE(AVG(rating), 0) FROM public.blueprint_reviews WHERE blueprint_id = $1),
                rating_count = (SELECT COUNT(*) FROM public.blueprint_reviews WHERE blueprint_id = $1)
            WHERE id = $1
        """,
            blueprint_id,
        )

    return {"status": "reviewed"}


# ---------------------------------------------------------------------------
# Author dashboard
# ---------------------------------------------------------------------------


@router.get("/author/blueprints")
async def author_blueprints(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> list[dict[str, Any]]:
    """List blueprints submitted by the current tenant."""
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, slug, name, version, approval_status, install_count,
                      rating_avg, price_cents, created_at
               FROM public.marketplace_blueprints WHERE author_tenant_id = $1
               ORDER BY created_at DESC""",
            ctx.tenant_id,
        )
    return [dict(r) for r in rows]


@router.get("/author/earnings")
async def author_earnings(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, Any]:
    """Get earnings summary for blueprint author."""
    async with db.acquire() as conn:
        total = await conn.fetchrow(
            """SELECT COALESCE(SUM(amount_cents), 0)::int AS total_earned,
                      COALESCE(SUM(CASE WHEN status = 'pending' THEN amount_cents ELSE 0 END), 0)::int AS pending,
                      COALESCE(SUM(CASE WHEN status = 'paid' THEN amount_cents ELSE 0 END), 0)::int AS paid_out,
                      COUNT(*)::int AS total_payouts
               FROM public.author_payouts WHERE author_tenant_id = $1""",
            ctx.tenant_id,
        )
        installs = await conn.fetchval(
            """SELECT COALESCE(SUM(install_count), 0)::int
               FROM public.marketplace_blueprints WHERE author_tenant_id = $1""",
            ctx.tenant_id,
        )
    return {
        "total_earned_cents": total["total_earned"],
        "pending_cents": total["pending"],
        "paid_out_cents": total["paid_out"],
        "total_payouts": total["total_payouts"],
        "total_installs": installs or 0,
    }


# ---------------------------------------------------------------------------
# Admin: approve/reject blueprints
# ---------------------------------------------------------------------------


@router.post("/admin/blueprints/{blueprint_id}/approve")
async def approve_blueprint(
    blueprint_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Approve a pending blueprint (system admin only)."""
    from shared.validators import validate_uuid

    validate_uuid(blueprint_id, "blueprint_id")
    async with db.acquire() as conn:
        try:
            await require_system_admin(conn, ctx.user_id)
        except TenantScopeError:
            raise HTTPException(status_code=403, detail="System admin required")
        await conn.execute(
            "UPDATE public.marketplace_blueprints SET approval_status = 'approved', published_at = now() WHERE id = $1",
            blueprint_id,
        )
    return {"status": "approved"}


@router.post("/admin/blueprints/{blueprint_id}/reject")
async def reject_blueprint(
    blueprint_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    db: asyncpg.Pool = Depends(_get_pool),
) -> dict[str, str]:
    """Reject a pending blueprint (system admin only)."""
    from shared.validators import validate_uuid

    validate_uuid(blueprint_id, "blueprint_id")
    async with db.acquire() as conn:
        try:
            await require_system_admin(conn, ctx.user_id)
        except TenantScopeError:
            raise HTTPException(status_code=403, detail="System admin required")
        await conn.execute(
            "UPDATE public.marketplace_blueprints SET approval_status = 'rejected' WHERE id = $1",
            blueprint_id,
        )
    return {"status": "rejected"}
