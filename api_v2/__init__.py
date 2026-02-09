from __future__ import annotations

import pathlib

# Import shim: allow `import api_v2.*` from repo root after monorepo restructure.
# Points this package at `apps/api_v2`.
_apps_api_v2 = pathlib.Path(__file__).resolve().parent.parent / "apps" / "api_v2"
__path__.append(str(_apps_api_v2))
