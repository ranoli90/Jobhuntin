from __future__ import annotations

import pathlib

# Import shim: allow `import worker.*` from repo root after monorepo restructure.
# Points this package at `apps/worker`.
_apps_worker = pathlib.Path(__file__).resolve().parent.parent / "apps" / "worker"
__path__.append(str(_apps_worker))
