"""
Pluggable Agent Blueprints.

Each blueprint defines vertical-specific logic (prompts, profile schema,
submit selectors, completion hooks) while the core engine handles the
generic form-filling workflow.
"""

from backend.blueprints.registry import get_blueprint, register_blueprint, BLUEPRINTS

__all__ = ["get_blueprint", "register_blueprint", "BLUEPRINTS"]
