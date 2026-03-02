"""Lightweight experimentation framework.

Provides deterministic, sticky variant assignment for A/B and canary
experiments. Assignments are persisted in `experiment_assignments` for
stability and auditability.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import asyncpg

logger = logging.getLogger("sorce.experiments")


async def get_variant(
    conn: asyncpg.Connection,
    experiment_key: str,
    subject_id: str,
    subject_type: str = "TENANT",
) -> str | None:
    """Return the variant name for a subject in an active experiment.

    1. If the experiment doesn't exist or is inactive → return None.
    2. If an assignment already exists → return it (sticky).
    3. Otherwise, compute a deterministic assignment via hash, persist it,
       and return the variant name.
    """
    # Fetch experiment
    exp = await conn.fetchrow(
        "SELECT id, variants, is_active FROM public.experiments WHERE key = $1",
        experiment_key,
    )
    if exp is None or not exp["is_active"]:
        return None

    experiment_id = exp["id"]
    variants: list[dict[str, Any]] = json.loads(exp["variants"]) if isinstance(exp["variants"], str) else exp["variants"]

    # Check for existing sticky assignment
    existing = await conn.fetchval(
        """
        SELECT variant FROM public.experiment_assignments
        WHERE experiment_id = $1 AND subject_type = $2 AND subject_id = $3
        """,
        experiment_id,
        subject_type,
        subject_id,
    )
    if existing is not None:
        return existing

    # Deterministic hash-based assignment
    hash_input = f"{experiment_key}:{subject_id}"
    hash_val = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16) % 100

    cumulative = 0
    assigned_variant = variants[-1]["name"]  # fallback to last
    for v in variants:
        cumulative += v.get("traffic_pct", 0)
        if hash_val < cumulative:
            assigned_variant = v["name"]
            break

    # Persist assignment
    await conn.execute(
        """
        INSERT INTO public.experiment_assignments
            (experiment_id, subject_type, subject_id, variant)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (experiment_id, subject_type, subject_id) DO NOTHING
        """,
        experiment_id,
        subject_type,
        subject_id,
        assigned_variant,
    )

    logger.info(
        "Assigned %s/%s to variant '%s' for experiment '%s'",
        subject_type, subject_id, assigned_variant, experiment_key,
    )
    return assigned_variant


async def get_variant_for_tenant(
    conn: asyncpg.Connection,
    experiment_key: str,
    tenant_id: str,
) -> str | None:
    """Convenience wrapper: get variant for a tenant subject."""
    return await get_variant(conn, experiment_key, tenant_id, subject_type="TENANT")


async def get_variant_for_user(
    conn: asyncpg.Connection,
    experiment_key: str,
    user_id: str,
) -> str | None:
    """Convenience wrapper: get variant for a user subject."""
    return await get_variant(conn, experiment_key, user_id, subject_type="USER")
