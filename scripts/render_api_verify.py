#!/usr/bin/env python3
"""
Verify Render API connection.

Usage:
  export RENDER_API_KEY=your-key   # or RENDER_API_TOKEN
  PYTHONPATH=packages python scripts/render_api_verify.py
"""
from __future__ import annotations

import os
import sys

# Ensure packages is on path (run with PYTHONPATH=packages or from repo root)
root = os.path.join(os.path.dirname(__file__), "..")
if root not in sys.path:
    sys.path.insert(0, root)
packages_path = os.path.join(root, "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

from shared.render_api import get_render_client, RenderAPIError


def main() -> int:
    client = get_render_client()
    if not client or not client.is_configured:
        print("❌ RENDER_API_KEY or RENDER_API_TOKEN not set.")
        print("   Get a key from: dashboard.render.com → Account → API Keys")
        print("   Then: export RENDER_API_KEY=your-key")
        return 1

    try:
        services = client.list_services()
        print(f"✅ Render API connected. Found {len(services)} service(s).")
        for svc in services[:5]:
            name = svc.get("name", "?")
            sid = svc.get("id", "?")
            print(f"   - {name} ({sid})")
        if len(services) > 5:
            print(f"   ... and {len(services) - 5} more")
        return 0
    except RenderAPIError as e:
        print(f"❌ Render API error: {e}")
        if e.status_code:
            print(f"   Status: {e.status_code}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
