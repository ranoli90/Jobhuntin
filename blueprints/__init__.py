from __future__ import annotations

import pathlib

# Import shim: allow `import blueprints.*` from repo root after monorepo restructure.
# Points this package at `packages/blueprints`.
_pkg_blueprints = (
    pathlib.Path(__file__).resolve().parent.parent / "packages" / "blueprints"
)
__path__.append(str(_pkg_blueprints))
