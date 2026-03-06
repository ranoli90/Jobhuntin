"""Cost monitoring service for cloud spend.

Provides:
- Cloud cost tracking
- Budget alerts
- Cost anomaly detection
- Resource optimization recommendations
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger(__name__)


class CloudProvider(StrEnum):
    """Supported cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    RENDER = "render"
    VERCEL = "vercel"
    SUPABASE = "supabase"


class CostCategory(StrEnum):
    """Categories of cloud costs."""

    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORK = "network"
    AI_LLM = "ai_llm"
    MONITORING = "monitoring"
    OTHER = "other"


@dataclass
class CostEntry:
    """A single cost entry."""

    provider: CloudProvider
    category: CostCategory
    amount_usd: float
    date: datetime
    resource_id: str | None = None
    resource_name: str | None = None
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class BudgetAlert:
    """A budget alert configuration."""

    name: str
    monthly_budget_usd: float
    alert_thresholds: list[float] = field(default_factory=lambda: [0.5, 0.75, 0.9, 1.0])
    notify_emails: list[str] = field(default_factory=list)
    notify_slack: bool = True


@dataclass
class CostAnomaly:
    """A detected cost anomaly."""

    provider: CloudProvider
    category: CostCategory
    expected_usd: float
    actual_usd: float
    deviation_pct: float
    detected_at: datetime
    resource_id: str | None = None

    @property
    def severity(self) -> str:
        """Determine anomaly severity."""
        if self.deviation_pct > 100:
            return "critical"
        elif self.deviation_pct > 50:
            return "warning"
        else:
            return "info"


@dataclass
class CostSummary:
    """Summary of cloud costs."""

    period_start: datetime
    period_end: datetime
    total_usd: float
    by_provider: dict[CloudProvider, float] = field(default_factory=dict)
    by_category: dict[CostCategory, float] = field(default_factory=dict)
    daily_average: float = 0.0
    projected_monthly: float = 0.0

    def to_dict(self) -> dict:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_usd": round(self.total_usd, 2),
            "by_provider": {p.value: round(v, 2) for p, v in self.by_provider.items()},
            "by_category": {c.value: round(v, 2) for c, v in self.by_category.items()},
            "daily_average": round(self.daily_average, 2),
            "projected_monthly": round(self.projected_monthly, 2),
        }


class CostMonitor:
    """Cloud cost monitoring service.

    Features:
    - Multi-provider cost aggregation
    - Budget alerts and notifications
    - Anomaly detection
    - Optimization recommendations
    """

    def __init__(
        self,
        db_conn: "asyncpg.Connection",
        budget_alerts: list[BudgetAlert] | None = None,
        anomaly_threshold_pct: float = 30.0,
    ):
        self.db = db_conn
        self.budget_alerts = budget_alerts or []
        self.anomaly_threshold_pct = anomaly_threshold_pct

    async def record_cost(self, entry: CostEntry) -> None:
        """Record a cost entry."""
        await self.db.execute(
            """
            INSERT INTO public.cloud_costs
            (provider, category, amount_usd, date, resource_id, resource_name, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            entry.provider.value,
            entry.category.value,
            entry.amount_usd,
            entry.date,
            entry.resource_id,
            entry.resource_name,
            entry.tags,
        )

    async def get_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        provider: CloudProvider | None = None,
        category: CostCategory | None = None,
    ) -> list[CostEntry]:
        """Get cost entries for a period."""
        conditions = ["date >= $1", "date <= $2"]
        params: list = [start_date, end_date]

        if provider:
            conditions.append(f"provider = ${len(params) + 1}")
            params.append(provider.value)

        if category:
            conditions.append(f"category = ${len(params) + 1}")
            params.append(category.value)

        query = f"""  # nosec
            SELECT * FROM public.cloud_costs
            WHERE {" AND ".join(conditions)}
            ORDER BY date DESC
        """

        rows = await self.db.fetch(query, *params)

        return [
            CostEntry(
                provider=CloudProvider(r["provider"]),
                category=CostCategory(r["category"]),
                amount_usd=r["amount_usd"],
                date=r["date"],
                resource_id=r["resource_id"],
                resource_name=r["resource_name"],
                tags=r["tags"] or {},
            )
            for r in rows
        ]

    async def get_summary(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> CostSummary:
        """Get cost summary for a period."""
        rows = await self.db.fetch(
            """
            SELECT
                provider,
                category,
                SUM(amount_usd) as total
            FROM public.cloud_costs
            WHERE date >= $1 AND date <= $2
            GROUP BY provider, category
            """,
            start_date,
            end_date,
        )

        by_provider: dict[CloudProvider, float] = {}
        by_category: dict[CostCategory, float] = {}
        total = 0.0

        for row in rows:
            provider = CloudProvider(row["provider"])
            category = CostCategory(row["category"])
            amount = float(row["total"] or 0)

            by_provider[provider] = by_provider.get(provider, 0) + amount
            by_category[category] = by_category.get(category, 0) + amount
            total += amount

        days = (end_date - start_date).days or 1
        daily_average = total / days

        # Project monthly cost
        now = datetime.utcnow()
        days_in_month = 30  # Approximate
        days_elapsed = min(now.day, days_in_month)
        projected_monthly = (daily_average * days_in_month) if days_elapsed > 0 else 0

        return CostSummary(
            period_start=start_date,
            period_end=end_date,
            total_usd=total,
            by_provider=by_provider,
            by_category=by_category,
            daily_average=daily_average,
            projected_monthly=projected_monthly,
        )

    async def check_budget_alerts(self) -> list[dict]:
        """Check budget alerts and return triggered alerts."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        summary = await self.get_summary(month_start, now)
        triggered_alerts = []

        for alert in self.budget_alerts:
            usage_pct = summary.total_usd / alert.monthly_budget_usd

            for threshold in alert.alert_thresholds:
                if usage_pct >= threshold:
                    # Check if we already sent this alert
                    existing = await self.db.fetchrow(
                        """
                        SELECT id FROM public.budget_alerts_log
                        WHERE alert_name = $1 AND threshold = $2
                        AND created_at >= $3
                        """,
                        alert.name,
                        threshold,
                        month_start,
                    )

                    if not existing:
                        triggered_alerts.append(
                            {
                                "alert_name": alert.name,
                                "threshold": threshold,
                                "usage_pct": round(usage_pct * 100, 1),
                                "current_spend": round(summary.total_usd, 2),
                                "budget": alert.monthly_budget_usd,
                                "notify_emails": alert.notify_emails,
                                "notify_slack": alert.notify_slack,
                            }
                        )

        return triggered_alerts

    async def detect_anomalies(
        self,
        lookback_days: int = 30,
        comparison_days: int = 30,
    ) -> list[CostAnomaly]:
        """Detect cost anomalies by comparing periods."""
        now = datetime.utcnow()

        # Current period
        current_start = now - timedelta(days=lookback_days)
        current_end = now

        # Comparison period
        comparison_start = current_start - timedelta(days=comparison_days)
        comparison_end = current_start

        # Get costs by category for both periods
        current_costs = await self._get_costs_by_category(current_start, current_end)
        comparison_costs = await self._get_costs_by_category(
            comparison_start, comparison_end
        )

        anomalies = []

        for category, current_amount in current_costs.items():
            comparison_amount = comparison_costs.get(category, 0)

            if comparison_amount == 0:
                if current_amount > 10:  # New significant cost
                    anomalies.append(
                        CostAnomaly(
                            provider=CloudProvider.RENDER,  # Default
                            category=category,
                            expected_usd=0,
                            actual_usd=current_amount,
                            deviation_pct=100,
                            detected_at=now,
                        )
                    )
                continue

            deviation = ((current_amount - comparison_amount) / comparison_amount) * 100

            if deviation > self.anomaly_threshold_pct:
                anomalies.append(
                    CostAnomaly(
                        provider=CloudProvider.RENDER,  # Default
                        category=category,
                        expected_usd=comparison_amount,
                        actual_usd=current_amount,
                        deviation_pct=deviation,
                        detected_at=now,
                    )
                )

        return anomalies

    async def _get_costs_by_category(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[CostCategory, float]:
        """Get costs grouped by category."""
        rows = await self.db.fetch(
            """
            SELECT category, SUM(amount_usd) as total
            FROM public.cloud_costs
            WHERE date >= $1 AND date <= $2
            GROUP BY category
            """,
            start_date,
            end_date,
        )

        return {CostCategory(r["category"]): float(r["total"] or 0) for r in rows}

    async def get_optimization_recommendations(self) -> list[dict]:
        """Get cost optimization recommendations."""
        recommendations = []

        # Get current costs
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        summary = await self.get_summary(month_start, now)

        # Check for high database costs
        db_cost = summary.by_category.get(CostCategory.DATABASE, 0)
        if db_cost > 100:
            recommendations.append(
                {
                    "category": "database",
                    "title": "Review database tier",
                    "description": f"Database costs are ${db_cost:.2f}/month. Consider optimizing queries or downgrading tier.",
                    "potential_savings": db_cost * 0.2,
                }
            )

        # Check for high AI/LLM costs
        ai_cost = summary.by_category.get(CostCategory.AI_LLM, 0)
        if ai_cost > 50:
            recommendations.append(
                {
                    "category": "ai_llm",
                    "title": "Optimize LLM usage",
                    "description": f"AI costs are ${ai_cost:.2f}/month. Consider caching responses or using smaller models.",
                    "potential_savings": ai_cost * 0.3,
                }
            )

        # Check for high storage costs
        storage_cost = summary.by_category.get(CostCategory.STORAGE, 0)
        if storage_cost > 50:
            recommendations.append(
                {
                    "category": "storage",
                    "title": "Review storage usage",
                    "description": f"Storage costs are ${storage_cost:.2f}/month. Consider cleaning up old files or using lifecycle policies.",
                    "potential_savings": storage_cost * 0.25,
                }
            )

        return recommendations


async def setup_cost_monitoring(
    db_conn: "asyncpg.Connection",
    monthly_budget_usd: float = 500.0,
    notify_emails: list[str] | None = None,
) -> CostMonitor:
    """Set up cost monitoring with default budget alert."""
    budget_alert = BudgetAlert(
        name="Monthly Budget",
        monthly_budget_usd=monthly_budget_usd,
        notify_emails=notify_emails or [],
    )

    return CostMonitor(db_conn, budget_alerts=[budget_alert])
