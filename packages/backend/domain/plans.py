"""
Plan definitions and configuration.

Maps tenant plan tiers to concrete limits and feature flags.
"""

from __future__ import annotations

from typing import Any, TypedDict


class PlanConfig(TypedDict):
    """Configuration structure for a subscription plan."""
    max_monthly_tasks: int
    max_concurrent_tasks: int
    # Backward-compat aliases (same values, different keys for Sorce code)
    max_monthly_applications: int
    max_concurrent_applications: int
    priority: int  # higher = processed first (future use)
    features: dict[str, bool]


# ---------------------------------------------------------------------------
# Canonical plan configurations
# ---------------------------------------------------------------------------

PLAN_CONFIGS: dict[str, PlanConfig] = {
    "FREE": PlanConfig(
        max_monthly_tasks=25,
        max_concurrent_tasks=2,
        max_monthly_applications=25,
        max_concurrent_applications=2,
        priority=0,
        features={
            "resume_parsing": True,
            "hold_questions": True,
            "priority_processing": False,
            "team_members": False,
            "api_access": False,
            "custom_branding": False,
        },
    ),
    "PRO": PlanConfig(
        max_monthly_tasks=200,
        max_concurrent_tasks=10,
        max_monthly_applications=200,
        max_concurrent_applications=10,
        priority=10,
        features={
            "resume_parsing": True,
            "hold_questions": True,
            "priority_processing": True,
            "team_members": True,
            "api_access": True,
            "custom_branding": False,
        },
    ),
    "TEAM": PlanConfig(
        max_monthly_tasks=500,  # base; scales with seats
        max_concurrent_tasks=25,
        max_monthly_applications=500,
        max_concurrent_applications=25,
        priority=20,
        features={
            "resume_parsing": True,
            "hold_questions": True,
            "priority_processing": True,
            "team_members": True,
            "api_access": True,
            "custom_branding": False,
            "shared_job_lists": True,
            "team_analytics": True,
            "grant_blueprint": True,
        },
    ),
    "ENTERPRISE": PlanConfig(
        max_monthly_tasks=999_999,  # effectively unlimited
        max_concurrent_tasks=100,
        max_monthly_applications=999_999,
        max_concurrent_applications=100,
        priority=100,
        features={
            "resume_parsing": True,
            "hold_questions": True,
            "priority_processing": True,
            "team_members": True,
            "api_access": True,
            "custom_branding": True,
            "shared_job_lists": True,
            "team_analytics": True,
            "grant_blueprint": True,
            "sso": True,
            "audit_log": True,
            "bulk_operations": True,
            "dedicated_support": True,
            "custom_sla": True,
            "data_export": True,
            "member_impersonation": True,
        },
    ),
}


def plan_config_for(plan: str, plan_metadata: dict[str, Any] | None = None) -> PlanConfig:
    """
    Return the PlanConfig for a given plan tier.

    If plan_metadata contains overrides (e.g., custom limits negotiated for
    an enterprise tenant), those take precedence over the defaults.
    """
    base = PLAN_CONFIGS.get(plan, PLAN_CONFIGS["FREE"]).copy()
    if plan_metadata:
        for key in ("max_monthly_tasks", "max_concurrent_tasks",
                    "max_monthly_applications", "max_concurrent_applications", "priority"):
            if key in plan_metadata:
                base[key] = plan_metadata[key]  # type: ignore[literal-required]
        if "features" in plan_metadata and isinstance(plan_metadata["features"], dict):
            base["features"] = {**base["features"], **plan_metadata["features"]}
    return base
