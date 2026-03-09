"""Database capacity planning and resource management system.

Provides:
- Growth trend analysis
- Resource utilization forecasting
- Capacity planning recommendations
- Storage optimization suggestions
- Scaling recommendations

Usage:
    from shared.db_capacity_planner import CapacityPlanner

    planner = CapacityPlanner(db_pool)
    await planner.analyze_capacity_trends()
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

from shared.alerting import AlertSeverity, get_alert_manager
from shared.logging_config import get_logger

logger = get_logger("sorce.db_capacity")


class ResourceType(Enum):
    """Resource types for capacity planning."""

    STORAGE = "storage"
    MEMORY = "memory"
    CPU = "cpu"
    CONNECTIONS = "connections"
    IOPS = "iops"
    NETWORK = "network"


class AlertLevel(Enum):
    """Capacity alert levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CapacityMetric:
    """Capacity metric data point."""

    resource_type: ResourceType
    metric_name: str
    current_value: float
    max_capacity: float
    utilization_pct: float
    unit: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class GrowthTrend:
    """Growth trend analysis."""

    resource_type: ResourceType
    metric_name: str
    growth_rate_pct_per_day: float
    projected_value_30d: float
    projected_value_90d: float
    projected_value_1y: float
    days_until_capacity: Optional[float]
    trend_direction: str  # "increasing", "decreasing", "stable"
    confidence_score: float
    data_points: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class ScalingRecommendation:
    """Scaling recommendation."""

    recommendation_id: str
    resource_type: ResourceType
    current_capacity: float
    recommended_capacity: float
    scaling_factor: float
    urgency: AlertLevel
    estimated_cost: Optional[str] = None
    implementation_time: Optional[str] = None
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class CapacityPlan:
    """Comprehensive capacity plan."""

    plan_id: str
    generated_at: float
    planning_horizon_days: int
    current_metrics: Dict[str, CapacityMetric]
    growth_trends: Dict[str, GrowthTrend]
    scaling_recommendations: List[ScalingRecommendation]
    cost_projections: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    action_items: List[str]
    summary: str


class CapacityPlanner:
    """Advanced database capacity planning system."""

    def __init__(self, db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None):
        self.db_pool = db_pool
        self.alert_manager = alert_manager or get_alert_manager()

        # Capacity thresholds
        self.thresholds = {
            "storage_warning_pct": 75,
            "storage_critical_pct": 90,
            "memory_warning_pct": 80,
            "memory_critical_pct": 95,
            "connections_warning_pct": 80,
            "connections_critical_pct": 95,
            "cpu_warning_pct": 70,
            "cpu_critical_pct": 90,
            "growth_rate_warning_pct": 5.0,  # 5% daily growth
            "growth_rate_critical_pct": 10.0,  # 10% daily growth
        }

        # Historical data storage
        self.capacity_history: deque[Dict[str, Any]] = deque(maxlen=1000)
        self.growth_trends: Dict[str, GrowthTrend] = {}
        self.scaling_recommendations: deque[ScalingRecommendation] = deque(maxlen=100)

        # Planning configuration
        self.planning_config = {
            "historical_days": 30,
            "forecast_horizon_days": 365,
            "min_data_points": 7,
            "trend_confidence_threshold": 0.7,
            "auto_scaling_enabled": False,
        }

        # Background tasks
        self._planning_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def analyze_capacity_trends(self) -> CapacityPlan:
        """Perform comprehensive capacity analysis and planning."""
        try:
            # Collect current metrics
            current_metrics = await self._collect_current_metrics()

            # Analyze growth trends
            growth_trends = await self._analyze_growth_trends(current_metrics)

            # Generate scaling recommendations
            scaling_recommendations = await self._generate_scaling_recommendations(
                current_metrics, growth_trends
            )

            # Project costs
            cost_projections = await self._project_costs(scaling_recommendations)

            # Assess risks
            risk_assessment = await self._assess_risks(current_metrics, growth_trends)

            # Generate action items
            action_items = await self._generate_action_items(
                current_metrics, growth_trends, scaling_recommendations
            )

            # Create summary
            summary = self._generate_summary(
                current_metrics, growth_trends, scaling_recommendations
            )

            # Create capacity plan
            plan = CapacityPlan(
                plan_id=self._generate_plan_id(),
                generated_at=time.time(),
                planning_horizon_days=self.planning_config["forecast_horizon_days"],
                current_metrics=current_metrics,
                growth_trends=growth_trends,
                scaling_recommendations=scaling_recommendations,
                cost_projections=cost_projections,
                risk_assessment=risk_assessment,
                action_items=action_items,
                summary=summary,
            )

            # Store historical snapshot
            await self._store_historical_snapshot(plan)

            # Check for capacity alerts
            await self._check_capacity_alerts(current_metrics, growth_trends)

            return plan

        except Exception as e:
            logger.error(f"Capacity analysis failed: {e}")
            raise

    async def _collect_current_metrics(self) -> Dict[str, CapacityMetric]:
        """Collect current capacity metrics."""
        metrics = {}

        try:
            async with self.db_pool.acquire() as conn:
                # Storage metrics
                db_size = await conn.fetchval(
                    "SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb"
                )
                metrics["database_size_mb"] = CapacityMetric(
                    resource_type=ResourceType.STORAGE,
                    metric_name="database_size_mb",
                    current_value=db_size,
                    max_capacity=100000,  # 100GB default, should be configurable
                    utilization_pct=(db_size / 100000) * 100,
                    unit="MB",
                )

                # Table-specific storage
                table_sizes = await conn.fetch("""
                    SELECT
                        schemaname || '.' || tablename as table_name,
                        pg_total_relation_size(schemaname||'.'||tablename) / 1024 / 1024 as size_mb
                    FROM pg_tables
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY size_mb DESC
                    LIMIT 10
                """)

                for table in table_sizes:
                    metrics[f"table_{table['table_name']}_mb"] = CapacityMetric(
                        resource_type=ResourceType.STORAGE,
                        metric_name=f"table_{table['table_name']}_mb",
                        current_value=table["size_mb"],
                        max_capacity=10000,  # 10GB per table default
                        utilization_pct=(table["size_mb"] / 10000) * 100,
                        unit="MB",
                    )

                # Connection metrics
                conn_stats = await conn.fetchrow("""
                    SELECT
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)

                metrics["active_connections"] = CapacityMetric(
                    resource_type=ResourceType.CONNECTIONS,
                    metric_name="active_connections",
                    current_value=conn_stats["active_connections"],
                    max_capacity=conn_stats["max_connections"],
                    utilization_pct=(
                        conn_stats["active_connections"] / conn_stats["max_connections"]
                    )
                    * 100,
                    unit="count",
                )

                # Memory usage estimates (simplified)
                shared_buffers = await conn.fetchval(
                    "SELECT setting::int * 8192 / 1024 / 1024 FROM pg_settings WHERE name = 'shared_buffers'"
                )
                work_mem = await conn.fetchval(
                    "SELECT setting::int / 1024 FROM pg_settings WHERE name = 'work_mem'"
                )

                total_memory_mb = shared_buffers + (
                    work_mem * conn_stats["max_connections"]
                )

                metrics["memory_usage_mb"] = CapacityMetric(
                    resource_type=ResourceType.MEMORY,
                    metric_name="memory_usage_mb",
                    current_value=total_memory_mb,
                    max_capacity=8192,  # 8GB default
                    utilization_pct=(total_memory_mb / 8192) * 100,
                    unit="MB",
                )

                # Transaction volume (proxy for CPU/IOPS)
                tx_stats = await conn.fetchrow("""
                    SELECT
                        xact_commit + xact_rollback as total_transactions,
                        tup_inserted + tup_updated + tup_deleted as total_changes
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)

                metrics["daily_transactions"] = CapacityMetric(
                    resource_type=ResourceType.CPU,
                    metric_name="daily_transactions",
                    current_value=tx_stats["total_transactions"],
                    max_capacity=1000000,  # 1M transactions per day
                    utilization_pct=(tx_stats["total_transactions"] / 1000000) * 100,
                    unit="count",
                )

                metrics["daily_data_changes"] = CapacityMetric(
                    resource_type=ResourceType.IOPS,
                    metric_name="daily_data_changes",
                    current_value=tx_stats["total_changes"],
                    max_capacity=500000,  # 500K changes per day
                    utilization_pct=(tx_stats["total_changes"] / 500000) * 100,
                    unit="count",
                )

        except Exception as e:
            logger.error(f"Failed to collect capacity metrics: {e}")

        return metrics

    async def _analyze_growth_trends(
        self, current_metrics: Dict[str, CapacityMetric]
    ) -> Dict[str, GrowthTrend]:
        """Analyze growth trends based on historical data."""
        trends = {}

        for metric_name, current_metric in current_metrics.items():
            # Get historical data for this metric
            historical_values = self._get_historical_values(metric_name)

            if len(historical_values) < self.planning_config["min_data_points"]:
                continue

            # Calculate growth trend
            trend = self._calculate_growth_trend(
                metric_name, historical_values, current_metric
            )
            trends[metric_name] = trend
            self.growth_trends[metric_name] = trend

        return trends

    def _get_historical_values(self, metric_name: str) -> List[Tuple[float, float]]:
        """Get historical values for a metric."""
        values = []

        for snapshot in self.capacity_history:
            if metric_name in snapshot["metrics"]:
                metric_data = snapshot["metrics"][metric_name]
                values.append((snapshot["timestamp"], metric_data.current_value))

        # Sort by timestamp
        values.sort(key=lambda x: x[0])
        return values

    def _calculate_growth_trend(
        self,
        metric_name: str,
        historical_values: List[Tuple[float, float]],
        current_metric: CapacityMetric,
    ) -> GrowthTrend:
        """Calculate growth trend for a metric."""
        if len(historical_values) < 2:
            return GrowthTrend(
                resource_type=current_metric.resource_type,
                metric_name=metric_name,
                growth_rate_pct_per_day=0.0,
                projected_value_30d=current_metric.current_value,
                projected_value_90d=current_metric.current_value,
                projected_value_1y=current_metric.current_value,
                days_until_capacity=None,
                trend_direction="stable",
                confidence_score=0.0,
                data_points=len(historical_values),
            )

        # Calculate daily growth rate
        start_time, start_value = historical_values[0]
        end_time, end_value = historical_values[-1]

        days_elapsed = (end_time - start_time) / (24 * 60 * 60)

        if days_elapsed > 0 and start_value > 0:
            growth_factor = end_value / start_value
            daily_growth_rate = (growth_factor ** (1 / days_elapsed)) - 1
            growth_rate_pct = daily_growth_rate * 100
        else:
            growth_rate_pct = 0.0

        # Calculate confidence based on data consistency
        confidence_score = self._calculate_trend_confidence(historical_values)

        # Determine trend direction
        if growth_rate_pct > 1.0:  # More than 1% daily growth
            trend_direction = "increasing"
        elif growth_rate_pct < -1.0:  # More than 1% daily decline
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"

        # Calculate projected values
        current_value = current_metric.current_value
        projected_30d = current_value * ((1 + daily_growth_rate) ** 30)
        projected_90d = current_value * ((1 + daily_growth_rate) ** 90)
        projected_1y = current_value * ((1 + daily_growth_rate) ** 365)

        # Calculate days until capacity (if growing)
        days_until_capacity = None
        if (
            growth_rate_pct > 0
            and current_metric.max_capacity > 0
            and projected_1y > current_metric.max_capacity
        ):
            # Solve for days when current_value * (1 + daily_growth_rate)^days = max_capacity
            if daily_growth_rate > 0:
                days_until_capacity = math.log(
                    current_metric.max_capacity / current_value
                ) / math.log(1 + daily_growth_rate)

        return GrowthTrend(
            resource_type=current_metric.resource_type,
            metric_name=metric_name,
            growth_rate_pct_per_day=growth_rate_pct,
            projected_value_30d=projected_30d,
            projected_value_90d=projected_90d,
            projected_value_1y=projected_1y,
            days_until_capacity=days_until_capacity,
            trend_direction=trend_direction,
            confidence_score=confidence_score,
            data_points=len(historical_values),
        )

    def _calculate_trend_confidence(
        self, historical_values: List[Tuple[float, float]]
    ) -> float:
        """Calculate confidence score for trend analysis."""
        if len(historical_values) < 3:
            return 0.0

        # Simple confidence calculation based on R-squared

        n = len(historical_values)
        x_values = list(range(n))
        y_values = [value for _, value in historical_values]

        # Calculate linear regression
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum(
            (x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n)
        )
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Calculate R-squared
        ss_tot = sum((y_values[i] - y_mean) ** 2 for i in range(n))
        ss_res = sum(
            (y_values[i] - (slope * x_values[i] + intercept)) ** 2 for i in range(n)
        )

        if ss_tot == 0:
            return 1.0

        r_squared = 1 - (ss_res / ss_tot)
        return max(0, min(1, r_squared))

    async def _generate_scaling_recommendations(
        self,
        current_metrics: Dict[str, CapacityMetric],
        growth_trends: Dict[str, GrowthTrend],
    ) -> List[ScalingRecommendation]:
        """Generate scaling recommendations based on current state and trends."""
        recommendations = []

        for metric_name, metric in current_metrics.items():
            trend = growth_trends.get(metric_name)

            # Check current utilization
            if (
                metric.utilization_pct
                > self.thresholds[f"{metric.resource_type.value}_critical_pct"]
            ):
                urgency = AlertLevel.CRITICAL
            elif (
                metric.utilization_pct
                > self.thresholds[f"{metric.resource_type.value}_warning_pct"]
            ):
                urgency = AlertLevel.WARNING
            else:
                urgency = AlertLevel.INFO

            # Check growth rate
            if (
                trend
                and trend.growth_rate_pct_per_day
                > self.thresholds["growth_rate_critical_pct"]
            ):
                if urgency != AlertLevel.CRITICAL:
                    urgency = AlertLevel.CRITICAL
            elif (
                trend
                and trend.growth_rate_pct_per_day
                > self.thresholds["growth_rate_warning_pct"]
            ):
                if urgency == AlertLevel.INFO:
                    urgency = AlertLevel.WARNING

            # Generate recommendation if urgent or high growth
            if urgency in [AlertLevel.CRITICAL, AlertLevel.WARNING] or (
                trend and trend.days_until_capacity and trend.days_until_capacity < 90
            ):
                recommendation = await self._create_scaling_recommendation(
                    metric, trend, urgency
                )
                recommendations.append(recommendation)

        # Sort by urgency and impact
        urgency_order = {
            AlertLevel.CRITICAL: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.INFO: 2,
        }
        recommendations.sort(key=lambda r: urgency_order[r.urgency])

        # Store recommendations
        for rec in recommendations:
            self.scaling_recommendations.append(rec)

        return recommendations

    async def _create_scaling_recommendation(
        self, metric: CapacityMetric, trend: Optional[GrowthTrend], urgency: AlertLevel
    ) -> ScalingRecommendation:
        """Create a specific scaling recommendation."""
        resource_type = metric.resource_type
        current_capacity = metric.current_value

        # Calculate recommended capacity
        if trend and trend.growth_rate_pct_per_day > 0:
            # Scale based on 6-month projection
            projected_6m = current_capacity * (
                (1 + (trend.growth_rate_pct_per_day / 100)) ** 180
            )
            recommended_capacity = projected_6m * 1.2  # 20% buffer
        else:
            # Scale based on current utilization
            if metric.utilization_pct > 80:
                recommended_capacity = current_capacity * 2  # Double capacity
            else:
                recommended_capacity = current_capacity * 1.5  # 50% increase

        scaling_factor = recommended_capacity / current_capacity

        # Generate resource-specific recommendations
        if resource_type == ResourceType.STORAGE:
            return self._create_storage_recommendation(
                metric, trend, urgency, recommended_capacity, scaling_factor
            )
        elif resource_type == ResourceType.CONNECTIONS:
            return self._create_connection_recommendation(
                metric, trend, urgency, recommended_capacity, scaling_factor
            )
        elif resource_type == ResourceType.MEMORY:
            return self._create_memory_recommendation(
                metric, trend, urgency, recommended_capacity, scaling_factor
            )
        else:
            return self._create_general_recommendation(
                metric, trend, urgency, recommended_capacity, scaling_factor
            )

    def _create_storage_recommendation(
        self,
        metric: CapacityMetric,
        trend: Optional[GrowthTrend],
        urgency: AlertLevel,
        recommended_capacity: float,
        scaling_factor: float,
    ) -> ScalingRecommendation:
        """Create storage scaling recommendation."""
        benefits = [
            "Prevent storage exhaustion",
            "Maintain database performance",
            "Allow for continued growth",
        ]

        risks = [
            "Storage upgrade costs",
            "Potential downtime during upgrade",
            "Need for backup storage",
        ]

        alternatives = [
            "Implement data archiving",
            "Add read replicas for reporting",
            "Use compression for old data",
        ]

        return ScalingRecommendation(
            recommendation_id=f"storage_{int(time.time())}",
            resource_type=ResourceType.STORAGE,
            current_capacity=metric.current_value,
            recommended_capacity=recommended_capacity,
            scaling_factor=scaling_factor,
            urgency=urgency,
            estimated_cost=f"${int(recommended_capacity * 0.1)}",  # $0.10 per MB
            implementation_time="2-4 hours",
            benefits=benefits,
            risks=risks,
            alternatives=alternatives,
        )

    def _create_connection_recommendation(
        self,
        metric: CapacityMetric,
        trend: Optional[GrowthTrend],
        urgency: AlertLevel,
        recommended_capacity: float,
        scaling_factor: float,
    ) -> ScalingRecommendation:
        """Create connection scaling recommendation."""
        benefits = [
            "Handle increased concurrent users",
            "Reduce connection timeouts",
            "Improve application responsiveness",
        ]

        risks = [
            "Increased memory usage",
            "Potential CPU overhead",
            "Need for connection pooling",
        ]

        alternatives = [
            "Implement connection pooling",
            "Add read replicas",
            "Optimize application connection usage",
        ]

        return ScalingRecommendation(
            recommendation_id=f"connections_{int(time.time())}",
            resource_type=ResourceType.CONNECTIONS,
            current_capacity=metric.current_value,
            recommended_capacity=recommended_capacity,
            scaling_factor=scaling_factor,
            urgency=urgency,
            estimated_cost=f"${int(recommended_capacity * 0.5)}",  # $0.50 per connection
            implementation_time="1-2 hours",
            benefits=benefits,
            risks=risks,
            alternatives=alternatives,
        )

    def _create_memory_recommendation(
        self,
        metric: CapacityMetric,
        trend: Optional[GrowthTrend],
        urgency: AlertLevel,
        recommended_capacity: float,
        scaling_factor: float,
    ) -> ScalingRecommendation:
        """Create memory scaling recommendation."""
        benefits = [
            "Improved query performance",
            "Better cache hit ratios",
            "Reduced disk I/O",
        ]

        risks = [
            "Increased server costs",
            "Need for server restart",
            "Memory allocation complexity",
        ]

        alternatives = [
            "Optimize query efficiency",
            "Add database indexes",
            "Implement result caching",
        ]

        return ScalingRecommendation(
            recommendation_id=f"memory_{int(time.time())}",
            resource_type=ResourceType.MEMORY,
            current_capacity=metric.current_value,
            recommended_capacity=recommended_capacity,
            scaling_factor=scaling_factor,
            urgency=urgency,
            estimated_cost=f"${int(recommended_capacity * 0.02)}",  # $0.02 per MB
            implementation_time="2-6 hours",
            benefits=benefits,
            risks=risks,
            alternatives=alternatives,
        )

    def _create_general_recommendation(
        self,
        metric: CapacityMetric,
        trend: Optional[GrowthTrend],
        urgency: AlertLevel,
        recommended_capacity: float,
        scaling_factor: float,
    ) -> ScalingRecommendation:
        """Create general scaling recommendation."""
        benefits = [
            "Improve system performance",
            "Handle increased load",
            "Ensure system stability",
        ]

        risks = [
            "Increased operational costs",
            "Complexity in management",
            "Potential service disruption",
        ]

        alternatives = [
            "Optimize application code",
            "Implement caching strategies",
            "Use load balancing",
        ]

        return ScalingRecommendation(
            recommendation_id=f"general_{int(time.time())}",
            resource_type=metric.resource_type,
            current_capacity=metric.current_value,
            recommended_capacity=recommended_capacity,
            scaling_factor=scaling_factor,
            urgency=urgency,
            estimated_cost="Varies by resource type",
            implementation_time="4-8 hours",
            benefits=benefits,
            risks=risks,
            alternatives=alternatives,
        )

    async def _project_costs(
        self, recommendations: List[ScalingRecommendation]
    ) -> Dict[str, Any]:
        """Project costs for scaling recommendations."""
        total_cost = 0
        cost_breakdown = defaultdict(float)

        for rec in recommendations:
            if rec.estimated_cost and rec.estimated_cost.startswith("$"):
                try:
                    cost = float(rec.estimated_cost[1:])
                    total_cost += cost
                    cost_breakdown[rec.resource_type.value] += cost
                except ValueError:
                    pass

        return {
            "total_estimated_cost": total_cost,
            "cost_breakdown": dict(cost_breakdown),
            "currency": "USD",
            "cost_per_month": total_cost,  # Simplified
            "implementation_costs": total_cost * 0.2,  # 20% implementation cost
        }

    async def _assess_risks(
        self,
        current_metrics: Dict[str, CapacityMetric],
        growth_trends: Dict[str, GrowthTrend],
    ) -> Dict[str, Any]:
        """Assess capacity-related risks."""
        risks = {
            "immediate_risks": [],
            "near_term_risks": [],
            "long_term_risks": [],
            "risk_score": 0.0,
        }

        # Check for immediate risks
        for metric_name, metric in current_metrics.items():
            if (
                metric.utilization_pct
                > self.thresholds[f"{metric.resource_type.value}_critical_pct"]
            ):
                risks["immediate_risks"].append(
                    {
                        "resource": metric_name,
                        "type": "capacity_exhaustion",
                        "severity": "critical",
                        "description": f"{metric_name} at {metric.utilization_pct:.1f}% capacity",
                    }
                )
                risks["risk_score"] += 3

        # Check for near-term risks (30 days)
        for metric_name, trend in growth_trends.items():
            if trend.days_until_capacity and trend.days_until_capacity < 30:
                risks["near_term_risks"].append(
                    {
                        "resource": metric_name,
                        "type": "projected_exhaustion",
                        "severity": "high",
                        "description": f"{metric_name} projected to exhaust in {trend.days_until_capacity:.0f} days",
                        "days_until_exhaustion": trend.days_until_capacity,
                    }
                )
                risks["risk_score"] += 2

        # Check for long-term risks (90 days)
        for metric_name, trend in growth_trends.items():
            if trend.days_until_capacity and trend.days_until_capacity < 90:
                risks["long_term_risks"].append(
                    {
                        "resource": metric_name,
                        "type": "projected_exhaustion",
                        "severity": "medium",
                        "description": f"{metric_name} projected to exhaust in {trend.days_until_capacity:.0f} days",
                        "days_until_exhaustion": trend.days_until_capacity,
                    }
                )
                risks["risk_score"] += 1

        # Normalize risk score
        max_possible_score = 10  # Arbitrary max score
        risks["risk_score"] = min(risks["risk_score"] / max_possible_score, 1.0)

        return risks

    async def _generate_action_items(
        self,
        current_metrics: Dict[str, CapacityMetric],
        growth_trends: Dict[str, GrowthTrend],
        recommendations: List[ScalingRecommendation],
    ) -> List[str]:
        """Generate prioritized action items."""
        actions = []

        # Critical actions (immediate)
        critical_recs = [r for r in recommendations if r.urgency == AlertLevel.CRITICAL]
        if critical_recs:
            actions.append(
                "URGENT: Implement critical scaling recommendations to prevent service disruption"
            )

        # High utilization metrics
        high_util_metrics = [
            name
            for name, metric in current_metrics.items()
            if metric.utilization_pct > 80
        ]
        if high_util_metrics:
            actions.append(
                f"Monitor high-utilization resources: {', '.join(high_util_metrics)}"
            )

        # Fast-growing resources
        fast_growing = [
            name
            for name, trend in growth_trends.items()
            if trend.growth_rate_pct_per_day > 5.0
        ]
        if fast_growing:
            actions.append(
                f"Plan for fast-growing resources: {', '.join(fast_growing)}"
            )

        # Regular maintenance
        actions.extend(
            [
                "Review and update capacity planning quarterly",
                "Implement automated monitoring and alerting",
                "Document scaling procedures and runbooks",
                "Test scaling procedures in staging environment",
            ]
        )

        return actions

    def _generate_summary(
        self,
        current_metrics: Dict[str, CapacityMetric],
        growth_trends: Dict[str, GrowthTrend],
        recommendations: List[ScalingRecommendation],
    ) -> str:
        """Generate capacity planning summary."""
        critical_count = len(
            [r for r in recommendations if r.urgency == AlertLevel.CRITICAL]
        )
        warning_count = len(
            [r for r in recommendations if r.urgency == AlertLevel.WARNING]
        )

        high_util_count = len(
            [m for m in current_metrics.values() if m.utilization_pct > 80]
        )

        fast_growth_count = len(
            [t for t in growth_trends.values() if t.growth_rate_pct_per_day > 5.0]
        )

        summary = f"Capacity analysis reveals {critical_count} critical and {warning_count} warning recommendations. "
        summary += (
            f"Currently {high_util_count} resources are operating above 80% capacity. "
        )
        summary += (
            f"{fast_growth_count} resources are showing high growth rates (>5% daily). "
        )

        if critical_count > 0:
            summary += "Immediate action required to prevent service disruption."
        elif warning_count > 0:
            summary += "Proactive scaling recommended within 30-60 days."
        else:
            summary += "Current capacity is adequate with normal growth patterns."

        return summary

    async def _store_historical_snapshot(self, plan: CapacityPlan) -> None:
        """Store capacity planning snapshot."""
        snapshot = {
            "timestamp": plan.generated_at,
            "metrics": {name: metric for name, metric in plan.current_metrics.items()},
            "trends": {name: trend for name, trend in plan.growth_trends.items()},
            "recommendations_count": len(plan.scaling_recommendations),
            "risk_score": plan.risk_assessment.get("risk_score", 0.0),
        }

        self.capacity_history.append(snapshot)

    async def _check_capacity_alerts(
        self,
        current_metrics: Dict[str, CapacityMetric],
        growth_trends: Dict[str, GrowthTrend],
    ) -> None:
        """Check for capacity-related alerts."""
        # Check critical utilization
        for metric_name, metric in current_metrics.items():
            threshold_key = f"{metric.resource_type.value}_critical_pct"
            if metric.utilization_pct > self.thresholds[threshold_key]:
                await self.alert_manager.trigger_alert(
                    name=f"capacity_{metric.resource_type.value}_critical",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Critical capacity utilization: {metric_name} at {metric.utilization_pct:.1f}%",
                    metric_value=metric.utilization_pct,
                    threshold=self.thresholds[threshold_key],
                )

        # Check for imminent capacity exhaustion
        for trend_name, trend in growth_trends.items():
            if trend.days_until_capacity and trend.days_until_capacity < 7:
                await self.alert_manager.trigger_alert(
                    name="capacity_imminent_exhaustion",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Resource {trend_name} projected to exhaust in {trend.days_until_capacity:.0f} days",
                    metric_value=trend.days_until_capacity,
                    threshold=7,
                )

    def _generate_plan_id(self) -> str:
        """Generate unique plan ID."""
        import uuid

        return f"cap_plan_{int(time.time())}_{str(uuid.uuid4())[:8]}"

    def get_capacity_summary(self) -> Dict[str, Any]:
        """Get comprehensive capacity summary."""
        if not self.capacity_history:
            return {"status": "no_data"}

        latest_snapshot = self.capacity_history[-1]

        summary = {
            "last_analysis": latest_snapshot["timestamp"],
            "metrics_tracked": len(latest_snapshot["metrics"]),
            "trends_analyzed": len(latest_snapshot["trends"]),
            "current_recommendations": len(self.scaling_recommendations),
            "risk_score": latest_snapshot["risk_score"],
        }

        # Count recommendations by urgency
        urgency_counts = defaultdict(int)
        for rec in self.scaling_recommendations:
            urgency_counts[rec.urgency.value] += 1
        summary["recommendations_by_urgency"] = dict(urgency_counts)

        # Get top critical recommendations
        critical_recs = [
            {
                "id": rec.recommendation_id,
                "resource": rec.resource_type.value,
                "urgency": rec.urgency.value,
            }
            for rec in self.scaling_recommendations
            if rec.urgency == AlertLevel.CRITICAL
        ][:5]
        summary["critical_recommendations"] = critical_recs

        return summary

    async def start_monitoring(self, interval_seconds: int = 3600) -> asyncio.Task:
        """Start continuous capacity monitoring."""

        async def monitor():
            while True:
                try:
                    await self.analyze_capacity_trends()
                    await asyncio.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Capacity monitoring error: {e}")
                    await asyncio.sleep(interval_seconds)

        self._planning_task = asyncio.create_task(monitor)
        return self._planning_task

    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        if self._planning_task:
            self._planning_task.cancel()
            self._planning_task = None


# Add missing import
import math

# Global capacity planner instance
_capacity_planner: CapacityPlanner | None = None


def get_capacity_planner() -> CapacityPlanner:
    """Get global capacity planner instance."""
    global _capacity_planner
    if _capacity_planner is None:
        raise RuntimeError(
            "Capacity planner not initialized. Call init_capacity_planner() first."
        )
    return _capacity_planner


async def init_capacity_planner(
    db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None
) -> CapacityPlanner:
    """Initialize global capacity planner."""
    global _capacity_planner
    _capacity_planner = CapacityPlanner(db_pool, alert_manager)
    return _capacity_planner
