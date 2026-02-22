#!/usr/bin/env python3
"""
Fetch issues from SonarCloud API for ranoli90_sorce project.
Usage: python scripts/sonarcloud-fetch-issues.py [--output issues.json]
Requires: SONAR_TOKEN in .env or environment
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

# Load .env if present
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

TOKEN = os.environ.get("SONAR_TOKEN")
BASE = "https://sonarcloud.io/api"
PROJECT = "ranoli90_sorce"


def fetch_issues(types="BUG,VULNERABILITY,CODE_SMELL", ps=500):
    if not TOKEN:
        print("Set SONAR_TOKEN in .env or environment", file=sys.stderr)
        sys.exit(1)
    url = f"{BASE}/issues/search?componentKeys={PROJECT}&types={types}&resolved=false&ps={ps}"
    req = urllib.request.Request(url)
    import base64
    auth = base64.b64encode(f"{TOKEN}:".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


def main():
    out_path = "issues.json"
    if "--output" in sys.argv:
        i = sys.argv.index("--output")
        out_path = sys.argv[i + 1] if i + 1 < len(sys.argv) else "issues.json"
    data = fetch_issues()
    total = data.get("total", 0)
    issues = data.get("issues", [])
    print(f"Fetched {len(issues)} issues (total: {total})", file=sys.stderr)
    Path(out_path).write_text(json.dumps(data, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
