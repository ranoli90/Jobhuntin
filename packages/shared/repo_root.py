from __future__ import annotations

import pathlib
from typing import Iterable


def find_repo_root(start: pathlib.Path, markers: Iterable[str] | None = None) -> pathlib.Path:
    """Find the repository root by walking parents until a marker file/dir is found.

    This is used to make runtime file lookups resilient to repo restructures.
    """

    if markers is None:
        markers = ("pyproject.toml", "render.yaml", ".git")

    p = start.resolve()
    if p.is_file():
        p = p.parent

    for candidate in (p, *p.parents):
        for m in markers:
            if (candidate / m).exists():
                return candidate

    return p
