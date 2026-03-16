"""Pluggable Agent Blueprints.

Each blueprint defines vertical-specific logic (prompts, profile schema,
submit selectors, completion hooks) while the core engine handles the
generic form-filling workflow.
"""

from packages.backend.blueprints.registry import (
    BLUEPRINTS,
    get_blueprint,
    register_blueprint,
)

__all__ = ["get_blueprint", "register_blueprint", "BLUEPRINTS"]
