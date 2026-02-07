"""
Enterprise contract management — self-serve onboarding, annual billing,
contract lifecycle, churn risk scoring.
"""

from __future__ import annotations

from typing import Any

import asyncpg

from backend.domain.audit import record_audit_event
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.contracts")


# ---------------------------------------------------------------------------
# Self-serve enterprise onboarding
# ---------------------------------------------------------------------------

async def start_enterprise_onboarding(
    conn: asyncpg.Connection,
    tenant_id: str,
    custom_domain: str | None = None,
) -> dict[str, Any]:
    """Initialize self-serve enterprise onboarding."""
    row = await conn.fetchrow(
        """
        INSERT INTO public.enterprise_onboarding (tenant_id, step, custom_domain)
        VALUES ($1, 'domain', $2)
        ON CONFLICT (tenant_id) DO UPDATE SET custom_domain = COALESCE($2, enterprise_onboarding.custom_domain), updated_at = now()
        RETURNING *
        """,
        tenant_id, custom_domain,
    )
    return dict(row)


async def advance_onboarding(
    conn: asyncpg.Connection,
    tenant_id: str,
    step: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Advance onboarding to next step."""
    STEPS = ["domain", "sso", "contract", "billing", "complete"]
    row = await conn.fetchrow(
        "SELECT * FROM public.enterprise_onboarding WHERE tenant_id = $1", tenant_id,
    )
    if not row:
        raise ValueError("Onboarding not started")

    current_idx = STEPS.index(row["step"]) if row["step"] in STEPS else 0
    next_idx = STEPS.index(step) if step in STEPS else current_idx + 1
    next_step = STEPS[min(next_idx, len(STEPS) - 1)]

    update_fields: dict[str, Any] = {"step": next_step}
    if details:
        if "contract_signed" in details:
            update_fields["contract_signed"] = details["contract_signed"]
        if "contract_pdf" in details:
            update_fields["contract_pdf"] = details["contract_pdf"]
        if "custom_domain" in details:
            update_fields["custom_domain"] = details["custom_domain"]

    updated = await conn.fetchrow(
        """
        UPDATE public.enterprise_onboarding
        SET step = $2, contract_signed = COALESCE($3, contract_signed),
            custom_domain = COALESCE($4, custom_domain), updated_at = now()
        WHERE tenant_id = $1
        RETURNING *
        """,
        tenant_id, next_step,
        update_fields.get("contract_signed"),
        update_fields.get("custom_domain"),
    )
    return dict(updated)


async def get_onboarding_status(
    conn: asyncpg.Connection, tenant_id: str,
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT * FROM public.enterprise_onboarding WHERE tenant_id = $1", tenant_id,
    )
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Contract lifecycle
# ---------------------------------------------------------------------------

async def set_contract(
    conn: asyncpg.Connection,
    tenant_id: str,
    value_cents: int,
    billing_interval: str = "monthly",
    contract_months: int = 12,
) -> None:
    """Set contract value and dates on a tenant."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=contract_months * 30)

    discount = get_settings().annual_discount_pct if billing_interval == "annual" else 0

    await conn.execute(
        """
        UPDATE public.tenants
        SET contract_value_cents = $2, contract_start = $3, contract_end = $4,
            billing_interval = $5, annual_discount_pct = $6, updated_at = now()
        WHERE id = $1
        """,
        tenant_id, value_cents, now, end, billing_interval, discount,
    )


async def get_contracts_expiring(
    conn: asyncpg.Connection, within_days: int = 30,
) -> list[dict[str, Any]]:
    """Get contracts expiring within N days."""
    rows = await conn.fetch(
        """
        SELECT t.id, t.name, t.plan::text, t.contract_end, t.contract_value_cents,
               t.seat_count, t.churn_risk_score
        FROM public.tenants t
        WHERE t.contract_end IS NOT NULL
          AND t.contract_end <= now() + ($1 || ' days')::interval
          AND t.plan IN ('TEAM', 'ENTERPRISE')
        ORDER BY t.contract_end ASC
        """,
        str(within_days),
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Churn risk scoring (simple heuristic — ML v2 in future)
# ---------------------------------------------------------------------------

async def update_churn_risk_scores(conn: asyncpg.Connection) -> int:
    """
    Recompute churn_risk_score for all paying tenants.

    Score 0-100 based on:
    - Days since last activity (0-40 pts)
    - Usage decline trend (0-30 pts)
    - Contract expiry proximity (0-20 pts)
    - Support ticket sentiment (0-10 pts, placeholder)
    """
    result = await conn.execute("""
        WITH scored AS (
            SELECT
                t.id,
                -- Activity recency: 0 pts (active today) → 40 pts (inactive 30+ days)
                LEAST(40, COALESCE(
                    EXTRACT(DAY FROM now() - (
                        SELECT MAX(a.created_at) FROM public.applications a
                        JOIN public.tenant_members tm ON tm.user_id = a.user_id AND tm.tenant_id = t.id
                    ))::int * 40 / 30,
                    40
                )) AS recency_score,
                -- Contract expiry: 0 pts (>90 days) → 20 pts (<30 days)
                CASE
                    WHEN t.contract_end IS NULL THEN 5
                    WHEN t.contract_end < now() + interval '30 days' THEN 20
                    WHEN t.contract_end < now() + interval '60 days' THEN 12
                    WHEN t.contract_end < now() + interval '90 days' THEN 5
                    ELSE 0
                END AS contract_score
            FROM public.tenants t
            WHERE t.plan IN ('PRO', 'TEAM', 'ENTERPRISE')
        )
        UPDATE public.tenants
        SET churn_risk_score = LEAST(100, scored.recency_score + scored.contract_score)
        FROM scored
        WHERE tenants.id = scored.id
    """)
    count = int(result.split()[-1]) if result else 0
    logger.info("Updated churn risk for %d tenants", count)
    return count


# ---------------------------------------------------------------------------
# Annual billing helpers
# ---------------------------------------------------------------------------

def get_annual_price_id(plan: str) -> str | None:
    """Return the Stripe annual price ID for a plan."""
    s = get_settings()
    return {
        "PRO": s.stripe_pro_annual_price_id,
        "TEAM": s.stripe_team_annual_price_id,
        "ENTERPRISE": s.stripe_enterprise_annual_price_id,
    }.get(plan)
