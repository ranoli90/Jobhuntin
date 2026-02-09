from __future__ import annotations

import pathlib

# Import shim: allow `import partners.*` from repo root after monorepo restructure.
# Points this package at `packages/partners`.
_pkg_partners = pathlib.Path(__file__).resolve().parent.parent / "packages" / "partners"
__path__.append(str(_pkg_partners))
