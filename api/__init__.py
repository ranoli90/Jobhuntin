from __future__ import annotations

import pathlib

# Import shim: allow `import api.*` from repo root after monorepo restructure.
# Points this package at `apps/api`.
_apps_api = pathlib.Path(__file__).resolve().parent.parent / "apps" / "api"
__path__.append(str(_apps_api))
