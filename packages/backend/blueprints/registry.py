"""Blueprint registry — stores and retrieves AgentBlueprint instances by slug.

Usage:
    from packages.backend.blueprints.registry import get_blueprint, register_blueprint

    register_blueprint(JobApplicationBlueprint())
    bp = get_blueprint("job-app")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from packages.backend.blueprints.protocol import AgentBlueprint

from shared.logging_config import get_logger

logger = get_logger("sorce.blueprints")

BLUEPRINTS: dict[str, AgentBlueprint] = {}


def register_blueprint(bp: AgentBlueprint) -> None:
    """Register a blueprint instance by its slug."""
    if bp.slug in BLUEPRINTS:
        logger.warning("Blueprint '%s' already registered; skipping duplicate", bp.slug)
        return
    BLUEPRINTS[bp.slug] = bp
    logger.info("Registered blueprint: %s (v%s) as '%s'", bp.name, bp.version, bp.slug)


def get_blueprint(key: str) -> AgentBlueprint:
    """Look up a blueprint by key (tenants.blueprint_key or tasks.blueprint_key).
    Raises KeyError if not found.
    """
    if key not in BLUEPRINTS:
        available = ", ".join(BLUEPRINTS.keys()) or "(none)"
        raise KeyError(f"Blueprint '{key}' not registered. Available: {available}")
    return BLUEPRINTS[key]


def load_default_blueprints(enabled_slugs: list[str] | None = None) -> None:
    """Import and register built-in blueprints, optionally filtered by slug."""
    from packages.backend.blueprints.grant import GrantApplicationBlueprint
    from packages.backend.blueprints.job_app import JobApplicationBlueprint

    registry: dict[str, Callable[[], Any]] = {
        "job-app": JobApplicationBlueprint,
        "grant": GrantApplicationBlueprint,
    }

    targets = (
        list(registry.keys())
        if enabled_slugs is None
        else [s for s in enabled_slugs if s in registry]
    )

    for slug in targets:
        try:
            register_blueprint(registry[slug]())
        except Exception as exc:
            logger.error("Failed to register blueprint '%s': %s", slug, exc)
