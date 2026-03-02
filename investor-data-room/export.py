#!/usr/bin/env python3
"""Series A Data Room Export CLI — fetches full investor metrics and saves
as timestamped JSON + CSV for diligence preparation.

Usage:
    python investor-data-room/export.py --api-url https://api.sorce.app --token $ADMIN_TOKEN
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Sorce Series A data room")
    parser.add_argument("--api-url", default=os.getenv("API_URL", "http://localhost:8000"))
    parser.add_argument("--token", default=os.getenv("ADMIN_TOKEN", ""))
    parser.add_argument("--output", default="./investor-data-room/exports")
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

    # 1. Refresh all views
    print("Refreshing M1–M6 materialized views...")
    resp = httpx.post(f"{base}/admin/m6-platform/refresh", headers=headers, timeout=60)
    print(f"  {'✓' if resp.status_code == 200 else '⚠'} Views: {resp.status_code}")

    # 2. Full metrics JSON
    print("Fetching full investor metrics...")
    resp = httpx.get(f"{base}/investors/full-metrics", headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} — {resp.text[:200]}")
        sys.exit(1)
    metrics = resp.json()

    # 3. CSV
    csv_resp = httpx.get(f"{base}/investors/full-metrics.csv", headers=headers, timeout=30)

    # 4. Save
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    (out / f"data_room_{ts}.json").write_text(json.dumps(metrics, indent=2, default=str))
    (out / f"data_room_{ts}.csv").write_text(csv_resp.text if csv_resp.status_code == 200 else "")
    (out / "latest.json").write_text(json.dumps(metrics, indent=2, default=str))

    # 5. Summary
    fin = metrics.get("financials", {})
    cust = metrics.get("customers", {})
    ue = metrics.get("unit_economics", {})
    plat = metrics.get("platform", {})

    print("\n" + "=" * 56)
    print("  SORCE — Series A Data Room Summary")
    print("=" * 56)
    print(f"  MRR:              ${fin.get('mrr', 0):>10,.0f}")
    print(f"  ARR:              ${fin.get('arr', 0):>10,.0f}")
    print(f"  MRR Growth:       {fin.get('mrr_growth_mom_pct', 0):>9.1f}% MoM")
    print(f"  Gross Margin:     {fin.get('gross_margin_pct', 0):>9.1f}%")
    print(f"  Paying Subs:      {cust.get('paying_subscribers', 0):>10,}")
    print(f"  Enterprise:       {cust.get('enterprise', 0):>10}")
    print(f"  LTV:CAC:          {ue.get('ltv_cac_ratio', 0):>9.1f}:1")
    print(f"  Churn:            {ue.get('monthly_churn_pct', 0):>9.1f}%")
    print(f"  API Integrators:  {plat.get('integrators', 0):>10}")
    print(f"  Marketplace BPs:  {plat.get('marketplace_blueprints', 0):>10}")
    print("=" * 56)
    for v in metrics.get("verticals", []):
        print(f"  {v.get('vertical', ''):20s}  MRR=${v.get('mrr', 0):>8,}  tenants={v.get('tenant_count', 0)}")
    print("=" * 56)


if __name__ == "__main__":
    main()
