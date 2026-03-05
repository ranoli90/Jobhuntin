"""Cost Monitoring — track and alert on cloud infrastructure costs.

Provides:
- Multi-provider cost aggregation (Render, AWS, etc.)
- Budget thresholds with alerts
- Cost anomaly detection
- Usage-based cost attribution
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.cost_monitoring")


class CostCategory(StrEnum):
    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    LLM_API = "llm_api"
    THIRD_PARTY = "third_party"


class BudgetAlert(BaseModel):
    budget_id: str
    category: CostCategory
    current_spend: float
    budget_limit: float
    threshold_pct: float
    timestamp: str


class CostSnapshot(BaseModel):
    timestamp: str
    category: CostCategory
    amount: float
    currency: str = "USD"
    provider: str
    resource_id: str | None = None
    resource_name: str | None = None


class RenderCostClient:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.render.com/v1"

    async def get_current_spend(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/billing",
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Accept": "application/json",
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "current_month_spend": data.get("currentMonthSpend", 0),
                        "projected_month_spend": data.get("projectedMonthSpend", 0),
                        "services": data.get("services", []),
                    }
                return {"error": f"Status {resp.status_code}"}

        except Exception as e:
            logger.error("Failed to fetch Render costs: %s", e)
            return {"error": str(e)}

    async def get_service_costs(self, service_id: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/services/{service_id}/metrics",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )

                if resp.status_code == 200:
                    return resp.json()
                return {"error": f"Status {resp.status_code}"}

        except Exception as e:
            return {"error": str(e)}


class CostMonitor:
    def __init__(
        self,
        budgets: dict[CostCategory, float],
        alert_thresholds: list[float] | None = None,
    ):
        self.budgets = budgets
        self.alert_thresholds = alert_thresholds or [0.5, 0.75, 0.9, 1.0]
        self._notified_thresholds: dict[str, set[float]] = {}

    async def check_budgets(
        self,
        current_costs: dict[CostCategory, float],
    ) -> list[BudgetAlert]:
        alerts = []

        for category, budget_limit in self.budgets.items():
            current_spend = current_costs.get(category, 0)
            usage_pct = current_spend / budget_limit if budget_limit > 0 else 0

            for threshold in self.alert_thresholds:
                if usage_pct >= threshold:
                    key = f"{category.value}_{threshold}"
                    if key not in self._notified_thresholds:
                        self._notified_thresholds[key] = set()
                    if threshold not in self._notified_thresholds[key]:
                        self._notified_thresholds[key].add(threshold)

                        alert = BudgetAlert(
                            budget_id=f"{category.value}-monthly",
                            category=category,
                            current_spend=current_spend,
                            budget_limit=budget_limit,
                            threshold_pct=threshold * 100,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                        alerts.append(alert)

                        incr(
                            "cost.budget_alert",
                            {
                                "category": category.value,
                                "threshold": str(int(threshold * 100)),
                            },
                        )

            if usage_pct < min(self.alert_thresholds):
                for threshold in list(
                    self._notified_thresholds.get(
                        f"{category.value}_{min(self.alert_thresholds)}", []
                    )
                ):
                    if threshold > usage_pct:
                        self._notified_thresholds[
                            f"{category.value}_{threshold}"
                        ].discard(threshold)

        return alerts

    def reset_monthly_notifications(self):
        self._notified_thresholds.clear()


async def get_llm_costs(
    days: int = 30,
) -> dict[str, Any]:
    from shared.config import get_settings

    s = get_settings()

    try:
        import httpx

        base_url = s.llm_api_base or "https://openrouter.ai/api/v1"

        if "openrouter" in base_url:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{base_url}/auth/key",
                    headers={"Authorization": f"Bearer {s.llm_api_key}"},
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "provider": "openrouter",
                        "credits_remaining": data.get("data", {}).get(
                            "limit_remaining", 0
                        ),
                        "usage_limit": data.get("data", {}).get("limit", 0),
                        "period": f"{days} days",
                    }

        return {"provider": "unknown", "error": "Could not fetch LLM costs"}

    except Exception as e:
        return {"provider": "error", "error": str(e)}


async def get_cost_dashboard() -> dict[str, Any]:
    s = get_settings()

    costs: dict[CostCategory, float] = {}

    if s.pagerduty_api_key:
        pass

    llm_costs = await get_llm_costs()
    if "credits_remaining" in llm_costs:
        costs[CostCategory.LLM_API] = float(
            llm_costs.get("usage_limit", 0) - llm_costs.get("credits_remaining", 0)
        )

    observe("cost.llm_api_usd", costs.get(CostCategory.LLM_API, 0))

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "costs_by_category": {c.value: v for c, v in costs.items()},
        "total_monthly_spend": sum(costs.values()),
        "llm_details": llm_costs,
    }


async def check_cost_anomalies(
    historical_costs: list[float],
    current_cost: float,
    sensitivity: float = 2.0,
) -> dict[str, Any]:
    if len(historical_costs) < 3:
        return {"anomaly": False, "reason": "insufficient_data"}

    mean = sum(historical_costs) / len(historical_costs)
    variance = sum((x - mean) ** 2 for x in historical_costs) / len(historical_costs)
    std_dev = variance**0.5

    if std_dev == 0:
        return {"anomaly": False, "reason": "no_variance"}

    z_score = (current_cost - mean) / std_dev

    is_anomaly = abs(z_score) > sensitivity

    if is_anomaly:
        incr("cost.anomaly_detected", {"direction": "high" if z_score > 0 else "low"})

    return {
        "anomaly": is_anomaly,
        "z_score": round(z_score, 2),
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2),
        "current": current_cost,
        "threshold": sensitivity,
    }
