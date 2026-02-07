#!/usr/bin/env python3
"""
Series A Metrics Export CLI — fetches investor metrics from the API
and saves as JSON + CSV for pitch deck preparation.

Usage:
    python investor-metrics/export.py --api-url https://api.sorce.app --token $ADMIN_TOKEN
    python investor-metrics/export.py --api-url http://localhost:8000 --token dev-token --output ./exports
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Sorce Series A metrics")
    parser.add_argument("--api-url", default=os.getenv("API_URL", "http://localhost:8000"))
    parser.add_argument("--token", default=os.getenv("ADMIN_TOKEN", ""))
    parser.add_argument("--output", default="./investor-metrics/exports")
    args = parser.parse_args()

    if not args.token:
        print("ERROR: --token or ADMIN_TOKEN env var required")
        sys.exit(1)

    try:
        import httpx
    except ImportError:
        print("ERROR: httpx required — pip install httpx")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {args.token}"}
    base = args.api_url.rstrip("/")

    # 1. Refresh views
    print("Refreshing materialized views...")
    resp = httpx.post(f"{base}/admin/m5-dashboard/refresh", headers=headers, timeout=30)
    if resp.status_code == 200:
        print("  ✓ Views refreshed")
    else:
        print(f"  ⚠ Refresh returned {resp.status_code}: {resp.text[:200]}")

    # 2. Fetch JSON metrics
    print("Fetching investor metrics (JSON)...")
    resp = httpx.get(f"{base}/investors/metrics", headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"ERROR: API returned {resp.status_code}: {resp.text[:200]}")
        sys.exit(1)
    metrics = resp.json()

    # 3. Fetch CSV
    print("Fetching investor metrics (CSV)...")
    csv_resp = httpx.get(f"{base}/investors/metrics.csv", headers=headers, timeout=30)
    csv_data = csv_resp.text if csv_resp.status_code == 200 else ""

    # 4. Save outputs
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    json_path = out_dir / f"metrics_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"  ✓ JSON saved: {json_path}")

    csv_path = out_dir / f"metrics_{timestamp}.csv"
    with open(csv_path, "w") as f:
        f.write(csv_data)
    print(f"  ✓ CSV saved:  {csv_path}")

    # Also save a "latest" symlink/copy
    latest_json = out_dir / "latest.json"
    with open(latest_json, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    latest_csv = out_dir / "latest.csv"
    with open(latest_csv, "w") as f:
        f.write(csv_data)

    # 5. Print summary
    fin = metrics.get("financials", {})
    cust = metrics.get("customers", {})
    ue = metrics.get("unit_economics", {})

    print("\n" + "=" * 50)
    print("  SORCE — Series A Metrics Summary")
    print("=" * 50)
    print(f"  MRR:              ${fin.get('mrr', 0):,.0f}")
    print(f"  ARR:              ${fin.get('arr', 0):,.0f}")
    print(f"  MRR Growth:       {fin.get('mrr_growth_mom_pct', 0):.1f}% MoM")
    print(f"  Gross Margin:     {fin.get('gross_margin_pct', 0):.1f}%")
    print(f"  Paying Subs:      {cust.get('paying_subscribers', 0):,}")
    print(f"  Enterprise:       {cust.get('enterprise', 0)}")
    print(f"  LTV:CAC:          {ue.get('ltv_cac_ratio', 0):.1f}:1")
    print(f"  Monthly Churn:    {ue.get('monthly_churn_pct', 0):.1f}%")
    print(f"  Payback:          {ue.get('payback_months', 0):.1f} months")
    print("=" * 50)


if __name__ == "__main__":
    main()
