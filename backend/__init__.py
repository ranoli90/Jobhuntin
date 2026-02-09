from __future__ import annotations

import pathlib

# Import shim: allow `import backend.*` from repo root after monorepo restructure.
# Points this package at `packages/backend`.
_pkg_backend = pathlib.Path(__file__).resolve().parent.parent / "packages" / "backend"
__path__.append(str(_pkg_backend))
