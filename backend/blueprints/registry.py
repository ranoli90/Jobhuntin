"""
Blueprint registry — stores and retrieves AgentBlueprint instances by slug.

Usage:
    from backend.blueprints.registry import get_blueprint, register_blueprint

    register_blueprint(JobApplicationBlueprint())
    bp = get_blueprint("job-app")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.blueprints.protocol import AgentBlueprint

from shared.logging_config import get_logger

logger = get_logger("sorce.blueprints")

BLUEPRINTS: dict[str, "AgentBlueprint"] = {}


def register_blueprint(bp: "AgentBlueprint") -> None:
    """Register a blueprint instance by its slug."""
    BLUEPRINTS[bp.slug] = bp
    logger.info("Registered blueprint: %s (v%s) as '%s'", bp.name, bp.version, bp.slug)


def get_blueprint(key: str) -> "AgentBlueprint":
    """
    Look up a blueprint by key (tenants.blueprint_key or tasks.blueprint_key).
    Raises KeyError if not found.
    """
    if key not in BLUEPRINTS:
        available = ", ".join(BLUEPRINTS.keys()) or "(none)"
        raise KeyError(
            f"Blueprint '{key}' not registered. Available: {available}"
        )
    return BLUEPRINTS[key]


def load_default_blueprints() -> None:
    """Import and register all built-in blueprints. Called at startup."""
    from backend.blueprints.job_app import JobApplicationBlueprint
    register_blueprint(JobApplicationBlueprint())

    from backend.blueprints.grant import GrantApplicationBlueprint
    register_blueprint(GrantApplicationBlueprint())
