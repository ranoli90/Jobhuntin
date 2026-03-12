"""Prompt versioning registry.

Centralizes all LLM prompt templates with version keys so that the
experimentation framework can swap between prompt variants at runtime.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("sorce.prompt_registry")


# ---------------------------------------------------------------------------
# Registry: maps (prompt_key, version) → prompt template string
# ---------------------------------------------------------------------------

_PROMPTS: dict[tuple[str, str], str] = {}

# Flat lookup: prompt_key → default version
_DEFAULTS: dict[str, str] = {}


def register_prompt(
    prompt_key: str, version: str, template: str, *, default: bool = False
) -> None:
    """Register a prompt template under a key + version."""
    _PROMPTS[(prompt_key, version)] = template
    if default or prompt_key not in _DEFAULTS:
        _DEFAULTS[prompt_key] = version
    logger.debug("Registered prompt %s/%s (default=%s)", prompt_key, version, default)


def get_prompt(prompt_key: str, version: str | None = None) -> str:
    """Retrieve a prompt template by key and optional version.

    If version is None, returns the default version.
    Raises KeyError if not found.
    """
    if version is None:
        version = _DEFAULTS.get(prompt_key)
        if version is None:
            raise KeyError(f"No default version registered for prompt '{prompt_key}'")
    key = (prompt_key, version)
    if key not in _PROMPTS:
        raise KeyError(f"Prompt '{prompt_key}' version '{version}' not found")
    return _PROMPTS[key]


def get_default_version(prompt_key: str) -> str | None:
    """Return the default version string for a prompt key, or None."""
    return _DEFAULTS.get(prompt_key)


def list_prompts() -> dict[str, list[str]]:
    """Return a dict of prompt_key → list of registered versions."""
    result: dict[str, list[str]] = {}
    for pk, ver in _PROMPTS:
        result.setdefault(pk, []).append(ver)
    return result


# ---------------------------------------------------------------------------
# Auto-register existing prompts from contracts.py
# ---------------------------------------------------------------------------


def _register_builtin_prompts() -> None:
    """Register the built-in prompt templates from contracts.py."""
    from packages.backend.llm.contracts import DOM_MAPPING_PROMPT_V1, RESUME_PARSE_PROMPT_V1

    register_prompt("resume_parse", "v1", RESUME_PARSE_PROMPT_V1, default=True)
    register_prompt("dom_mapping", "v1", DOM_MAPPING_PROMPT_V1, default=True)


# Run on import
_register_builtin_prompts()
