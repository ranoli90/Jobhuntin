from __future__ import annotations

import pathlib

# Import shim: allow `import shared.*` from repo root after monorepo restructure.
# Points this package at `packages/shared`.
_pkg_shared = pathlib.Path(__file__).resolve().parent.parent / "packages" / "shared"
__path__.append(str(_pkg_shared))
