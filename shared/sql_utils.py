"""SQL safety utilities for parameterized queries."""


def escape_ilike(s: str) -> str:
    """Escape %, _, and \\ for safe use in ILIKE/LIKE patterns. Prevents wildcard injection."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
