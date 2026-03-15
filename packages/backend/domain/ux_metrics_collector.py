"""
UX Metrics Collector for Phase 14.1 User Experience
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.ux_metrics_collector")


class MetricType(Enum):
    """Types of UX metrics."""

    PERFORMANCE = "performance"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"
    ENGAGEMENT = "engagement"
    SATISFACTION = "satisfaction"
    CONVERSION = "conversion"
    RETENTION = "retention"
    ERROR_RATE = "error_rate"


class MetricCategory(Enum):
    """Categories of UX metrics."""

    PAGE_PERFORMANCE = "page_performance"
    USER_INTERACTION = "user_interaction"
    NAVIGATION = "navigation"
    FORM_COMPLETION = "form_completion"
    SEARCH_EFFICIENCY = "search_efficiency"
    CONTENT_ENGAGEMENT = "content_engagement"
    TASK_COMPLETION = "task_completion"
    ERROR_HANDLING = "error_handling"


@dataclass
class UXMetric:
    """UX metric data point."""

    id: str
    user_id: str
    tenant_id: str
    session_id: str
    metric_type: MetricType
    metric_category: MetricCategory
    metric_name: str
    value: float
    unit: str
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = datetime.now(timezone.utc)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class UXMetricDefinition:
    """UX metric definition."""

    id: str
    name: str
    description: str
    metric_type: MetricType
    metric_category: MetricCategory
    unit: str
    calculation_method: str
    thresholds: Dict[str, float] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


@dataclass
class UXMetricAggregation:
    """Aggregated UX metrics."""

    id: str
    tenant_id: str
    metric_type: MetricType
    metric_category: MetricCategory
    metric_name: str
    aggregation_type: str  # avg, min, max, sum, count
    period_hours: int
    value: float
    sample_size: int
    threshold_compliance: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class UXMetricAlert:
    """UX metric alert."""

    id: str
    tenant_id: str
    metric_name: str
    alert_type: str  # threshold_breach, trend_anomaly, significant_change
    severity: str  # low, medium, high, critical
    message: str
    current_value: float
    threshold_value: Optional[float]
    trend_data: Optional[Dict[str, Any]] = None
    is_resolved: bool = False
    created_at: datetime = datetime.now(timezone.utc)
    resolved_at: Optional[datetime] = None


class UXMetricsCollector:
    """Advanced UX metrics collection and analysis system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._metric_definitions: Dict[str, UXMetricDefinition] = {}
        self._metrics_cache: Dict[str, List[UXMetric]] = {}
        self._aggregation_cache: Dict[str, UXMetricAggregation] = {}
        self._alerts_cache: Dict[str, List[UXMetricAlert]] = {}
        self._collection_thresholds = self._initialize_thresholds()
        self._aggregation_intervals = {
            "hourly": 1,
            "daily": 24,
            "weekly": 168,
            "monthly": 720,
        }

        # Initialize default metric definitions
        asyncio.create_task(self._initialize_metric_definitions())

        # Start background collection and analysis
        asyncio.create_task(self._start_background_tasks())

    async def collect_metric(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        metric_type: MetricType,
        metric_category: MetricCategory,
        metric_name: str,
        value: float,
        unit: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UXMetric:
        """Collect a UX metric."""
        try:
            # Validate metric definition
            metric_def = self._get_metric_definition(metric_name)
            if not metric_def or not metric_def.is_active:
                logger.warning(f"Metric {metric_name} not found or inactive")
                return None  # type: ignore[return-value]

            # Create metric
            metric = UXMetric(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                metric_type=metric_type,
                metric_category=metric_category,
                metric_name=metric_name,
                value=value,
                unit=unit,
                context=context or {},
                metadata=metadata or {},
            )

            # Save metric
            await self._save_metric(metric)

            # Update cache
            cache_key = f"{tenant_id}:{metric_name}"
            if cache_key not in self._metrics_cache:
                self._metrics_cache[cache_key] = []
            self._metrics_cache[cache_key].append(metric)

            # Check for alerts
            await self._check_metric_alerts(metric)

            logger.info(f"Collected UX metric: {metric_name} = {value} {unit}")
            return metric

        except Exception as e:
            logger.error(f"Failed to collect UX metric: {e}")
            raise

    async def get_metrics_summary(
        self,
        tenant_id: str,
        time_period_hours: int = 24,
        metric_type: Optional[MetricType] = None,
        metric_category: Optional[MetricCategory] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive UX metrics summary."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Get metric statistics
            stats = await self._get_metric_statistics(
                tenant_id, cutoff_time, metric_type, metric_category, user_id
            )

            # Get aggregations
            aggregations = await self._get_metric_aggregations(
                tenant_id, time_period_hours, metric_type, metric_category
            )

            # Get alerts
            alerts = await self._get_active_alerts(
                tenant_id, metric_type, metric_category
            )

            # Get trends
            trends = await self._get_metric_trends(
                tenant_id, time_period_hours, metric_type, metric_category
            )

            # Get performance benchmarks
            benchmarks = await self._get_performance_benchmarks(
                tenant_id, metric_type, metric_category
            )

            summary = {
                "period_hours": time_period_hours,
                "metric_statistics": stats,
                "aggregations": aggregations,
                "active_alerts": alerts,
                "trends": trends,
                "benchmarks": benchmarks,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}

    async def get_metric_details(
        self,
        tenant_id: str,
        metric_name: str,
        time_period_hours: int = 24,
        aggregation_type: str = "avg",
    ) -> Dict[str, Any]:
        """Get detailed information for a specific metric."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Get metric definition
            metric_def = self._get_metric_definition(metric_name)
            if not metric_def:
                return {}

            # Get raw metrics
            raw_metrics = await self._get_raw_metrics(
                tenant_id, metric_name, cutoff_time
            )

            # Calculate aggregations
            aggregations = await self._calculate_metric_aggregations(
                raw_metrics, aggregation_type
            )

            # Get threshold compliance
            threshold_compliance = await self._calculate_threshold_compliance(
                raw_metrics, metric_def
            )

            # Get trend analysis
            trend_analysis = await self._analyze_metric_trend(
                raw_metrics, time_period_hours
            )

            # Get user breakdown
            user_breakdown = await self._get_user_breakdown(raw_metrics)

            # Get context analysis
            context_analysis = await self._analyze_context_data(raw_metrics)

            details = {
                "metric_definition": {
                    "name": metric_def.name,
                    "description": metric_def.description,
                    "type": metric_def.metric_type.value,
                    "category": metric_def.metric_category.value,
                    "unit": metric_def.unit,
                    "thresholds": metric_def.thresholds,
                },
                "period_hours": time_period_hours,
                "sample_size": len(raw_metrics),
                "aggregations": aggregations,
                "threshold_compliance": threshold_compliance,
                "trend_analysis": trend_analysis,
                "user_breakdown": user_breakdown,
                "context_analysis": context_analysis,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return details

        except Exception as e:
            logger.error(f"Failed to get metric details: {e}")
            return {}

    async def create_metric_definition(
        self,
        name: str,
        description: str,
        metric_type: MetricType,
        metric_category: MetricCategory,
        unit: str,
        calculation_method: str,
        thresholds: Optional[Dict[str, float]] = None,
        is_active: bool = True,
    ) -> UXMetricDefinition:
        """Create a new UX metric definition."""
        try:
            definition = UXMetricDefinition(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                metric_type=metric_type,
                metric_category=metric_category,
                unit=unit,
                calculation_method=calculation_method,
                thresholds=thresholds or {},
                is_active=is_active,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # Save definition
            await self._save_metric_definition(definition)

            # Update cache
            self._metric_definitions[name] = definition

            logger.info(f"Created UX metric definition: {name}")
            return definition

        except Exception as e:
            logger.error(f"Failed to create metric definition: {e}")
            raise

    async def update_metric_thresholds(
        self,
        metric_name: str,
        thresholds: Dict[str, float],
    ) -> bool:
        """Update metric thresholds."""
        try:
            definition = self._get_metric_definition(metric_name)
            if not definition:
                return False

            definition.thresholds = thresholds
            definition.updated_at = datetime.now(timezone.utc)

            # Save updated definition
            await self._save_metric_definition(definition)

            # Update cache
            self._metric_definitions[metric_name] = definition

            logger.info(f"Updated thresholds for metric: {metric_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update metric thresholds: {e}")
            return False

    async def get_performance_benchmarks(
        self,
        tenant_id: str,
        metric_type: Optional[MetricType] = None,
        metric_category: Optional[MetricCategory] = None,
    ) -> Dict[str, Any]:
        """Get performance benchmarks."""
        try:
            # Get all benchmarks using the existing method
            all_benchmarks = await self._get_performance_benchmarks(
                tenant_id, metric_type, metric_category
            )

            # Extract components (stub methods for now - implement as needed)
            industry_benchmarks = all_benchmarks.get("industry", {})
            tenant_benchmarks = all_benchmarks.get("tenant", {})
            peer_benchmarks = all_benchmarks.get("peer", {})
            performance_percentiles = all_benchmarks.get("percentiles", {})

            benchmarks = {
                "industry_benchmarks": industry_benchmarks,
                "tenant_benchmarks": tenant_benchmarks,
                "peer_benchmarks": peer_benchmarks,
                "performance_percentiles": performance_percentiles,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return benchmarks

        except Exception as e:
            logger.error(f"Failed to get performance benchmarks: {e}")
            return {}

    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize default metric thresholds."""
        return {
            "page_load_time": {
                "excellent": 1.0,
                "good": 2.0,
                "acceptable": 3.0,
                "poor": 5.0,
            },
            "time_to_interactive": {
                "excellent": 2.0,
                "good": 3.0,
                "acceptable": 5.0,
                "poor": 8.0,
            },
            "click_through_rate": {
                "excellent": 0.1,
                "good": 0.05,
                "acceptable": 0.02,
                "poor": 0.01,
            },
            "form_completion_rate": {
                "excellent": 0.9,
                "good": 0.8,
                "acceptable": 0.6,
                "poor": 0.4,
            },
            "search_success_rate": {
                "excellent": 0.9,
                "good": 0.8,
                "acceptable": 0.6,
                "poor": 0.4,
            },
            "error_rate": {
                "excellent": 0.01,
                "good": 0.02,
                "acceptable": 0.05,
                "poor": 0.1,
            },
            "user_satisfaction": {
                "excellent": 4.5,
                "good": 4.0,
                "acceptable": 3.5,
                "poor": 3.0,
            },
            "task_completion_time": {
                "excellent": 30.0,
                "good": 60.0,
                "acceptable": 120.0,
                "poor": 300.0,
            },
        }

    async def _initialize_metric_definitions(self) -> None:
        """Initialize default metric definitions."""
        try:
            default_metrics = [
                {
                    "name": "page_load_time",
                    "description": "Time taken to load a page completely",
                    "metric_type": MetricType.PERFORMANCE,
                    "metric_category": MetricCategory.PAGE_PERFORMANCE,
                    "unit": "seconds",
                    "calculation_method": "navigation_timing",
                    "thresholds": self._collection_thresholds["page_load_time"],
                },
                {
                    "name": "time_to_interactive",
                    "description": "Time until page becomes interactive",
                    "metric_type": MetricType.PERFORMANCE,
                    "metric_category": MetricCategory.PAGE_PERFORMANCE,
                    "unit": "seconds",
                    "calculation_method": "performance_timing",
                    "thresholds": self._collection_thresholds["time_to_interactive"],
                },
                {
                    "name": "click_through_rate",
                    "description": "Percentage of users who click on elements",
                    "metric_type": MetricType.ENGAGEMENT,
                    "metric_category": MetricCategory.USER_INTERACTION,
                    "unit": "percentage",
                    "calculation_method": "event_tracking",
                    "thresholds": self._collection_thresholds["click_through_rate"],
                },
                {
                    "name": "form_completion_rate",
                    "description": "Percentage of forms successfully completed",
                    "metric_type": MetricType.CONVERSION,
                    "metric_category": MetricCategory.FORM_COMPLETION,
                    "unit": "percentage",
                    "calculation_method": "form_tracking",
                    "thresholds": self._collection_thresholds["form_completion_rate"],
                },
                {
                    "name": "search_success_rate",
                    "description": "Percentage of successful search queries",
                    "metric_type": MetricType.USABILITY,
                    "metric_category": MetricCategory.SEARCH_EFFICIENCY,
                    "unit": "percentage",
                    "calculation_method": "search_tracking",
                    "thresholds": self._collection_thresholds["search_success_rate"],
                },
                {
                    "name": "error_rate",
                    "description": "Percentage of user actions resulting in errors",
                    "metric_type": MetricType.ERROR_RATE,
                    "metric_category": MetricCategory.ERROR_HANDLING,
                    "unit": "percentage",
                    "calculation_method": "error_tracking",
                    "thresholds": self._collection_thresholds["error_rate"],
                },
                {
                    "name": "user_satisfaction",
                    "description": "User satisfaction score",
                    "metric_type": MetricType.SATISFACTION,
                    "metric_category": MetricCategory.TASK_COMPLETION,
                    "unit": "score",
                    "calculation_method": "survey_tracking",
                    "thresholds": self._collection_thresholds["user_satisfaction"],
                },
                {
                    "name": "task_completion_time",
                    "description": "Time taken to complete primary tasks",
                    "metric_type": MetricType.USABILITY,
                    "metric_category": MetricCategory.TASK_COMPLETION,
                    "unit": "seconds",
                    "calculation_method": "task_tracking",
                    "thresholds": self._collection_thresholds["task_completion_time"],
                },
            ]

            for metric_config in default_metrics:
                try:
                    await self.create_metric_definition(**metric_config)
                except Exception as e:
                    logger.error(
                        f"Failed to create default metric {metric_config['name']}: {e}"
                    )

        except Exception as e:
            logger.error(f"Failed to initialize metric definitions: {e}")

    async def _start_background_tasks(self) -> None:
        """Start background collection and analysis tasks."""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour

                # Perform aggregations
                await self._perform_metric_aggregations()

                # Check for anomalies
                await self._check_metric_anomalies()

                # Update benchmarks (stub - implement as needed)
                pass  # await self._update_benchmarks()

        except Exception as e:
            logger.error(f"Background task failed: {e}")

    async def _perform_metric_aggregations(self) -> None:
        """Perform metric aggregations."""
        try:
            # Get active tenants
            tenants = await self._get_active_tenants()

            for tenant_id in tenants:
                try:
                    # Perform hourly aggregations
                    await self._aggregate_metrics(tenant_id, 1, "hourly")

                    # Perform daily aggregations
                    await self._aggregate_metrics(tenant_id, 24, "daily")

                except Exception as e:
                    logger.error(
                        f"Failed to aggregate metrics for tenant {tenant_id}: {e}"
                    )

        except Exception as e:
            logger.error(f"Failed to perform metric aggregations: {e}")

    async def _check_metric_anomalies(self) -> None:
        """Check for metric anomalies."""
        try:
            # Get active tenants
            tenants = await self._get_active_tenants()

            for tenant_id in tenants:
                try:
                    # Check for threshold breaches (using existing method)
                    # await self._check_threshold_breaches(tenant_id)  # Stub - use _check_metric_alerts instead

                    # Check for trend anomalies (using existing method)
                    await self._check_metric_anomalies()  # Use existing method

                except Exception as e:
                    logger.error(
                        f"Failed to check anomalies for tenant {tenant_id}: {e}"
                    )

        except Exception as e:
            logger.error(f"Failed to check metric anomalies: {e}")

    async def _check_metric_alerts(self, metric: UXMetric) -> None:
        """Check for metric alerts."""
        try:
            definition = self._get_metric_definition(metric.metric_name)
            if not definition or not definition.thresholds:
                return

            # Check threshold breaches
            for threshold_level, threshold_value in definition.thresholds.items():
                if self._is_threshold_breached(
                    metric.value, threshold_value, metric.metric_name
                ):
                    await self._create_threshold_alert(
                        metric, threshold_level, threshold_value
                    )
                    break

        except Exception as e:
            logger.error(f"Failed to check metric alerts: {e}")

    def _is_threshold_breached(
        self, value: float, threshold: float, metric_name: str
    ) -> bool:
        """Check if threshold is breached."""
        try:
            # Different metrics have different threshold directions
            lower_is_better = [
                "page_load_time",
                "time_to_interactive",
                "error_rate",
                "task_completion_time",
            ]

            if metric_name in lower_is_better:
                return value > threshold
            else:
                return value < threshold

        except Exception as e:
            logger.error(f"Failed to check threshold breach: {e}")
            return False

    async def _create_threshold_alert(
        self,
        metric: UXMetric,
        threshold_level: str,
        threshold_value: float,
    ) -> None:
        """Create threshold breach alert."""
        try:
            # Check if alert already exists and is unresolved (stub - implement as needed)
            existing_alert = (
                None  # await self._get_existing_alert(...)  # type: ignore[assignment]
            )
            if existing_alert and not existing_alert.is_resolved:  # type: ignore[union-attr]
                return  # Alert already exists

            # Determine severity
            severity_mapping = {
                "excellent": "low",
                "good": "low",
                "acceptable": "medium",
                "poor": "high",
            }
            severity = severity_mapping.get(threshold_level, "medium")

            # Create alert
            alert = UXMetricAlert(
                id=str(uuid.uuid4()),
                tenant_id=metric.tenant_id,
                metric_name=metric.metric_name,
                alert_type="threshold_breach",
                severity=severity,
                message =
    f"Metric {metric.metric_name} breached {threshold_level} threshold: {metric.value} {metric.unit} > {threshold_value}
    {metric.unit}",
                current_value=metric.value,
                threshold_value=threshold_value,
                created_at=datetime.now(timezone.utc),
            )

            # Save alert
            await self._save_alert(alert)

            # Update cache
            if metric.tenant_id not in self._alerts_cache:
                self._alerts_cache[metric.tenant_id] = []
            self._alerts_cache[metric.tenant_id].append(alert)

            logger.warning(f"Created threshold alert: {alert.message}")

        except Exception as e:
            logger.error(f"Failed to create threshold alert: {e}")

    def _get_metric_definition(self, metric_name: str) -> Optional[UXMetricDefinition]:
        """Get metric definition by name."""
        return self._metric_definitions.get(metric_name)

    async def _save_metric(self, metric: UXMetric) -> None:
        """Save metric to database."""
        try:
            query = """
                INSERT INTO ux_metrics (
                    id, user_id, tenant_id, session_id, metric_type, metric_category,
                    metric_name, value, unit, context, metadata, timestamp, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """

            params = [
                metric.id,
                metric.user_id,
                metric.tenant_id,
                metric.session_id,
                metric.metric_type.value,
                metric.metric_category.value,
                metric.metric_name,
                metric.value,
                metric.unit,
                json.dumps(metric.context),
                json.dumps(metric.metadata),
                metric.timestamp,
                metric.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save metric: {e}")

    async def _save_metric_definition(self, definition: UXMetricDefinition) -> None:
        """Save metric definition to database."""
        try:
            query = """
                INSERT INTO ux_metric_definitions (
                    id, name, description, metric_type, metric_category, unit,
                    calculation_method, thresholds, is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (name) DO UPDATE SET
                    description = EXCLUDED.description,
                    metric_type = EXCLUDED.metric_type,
                    metric_category = EXCLUDED.metric_category,
                    unit = EXCLUDED.unit,
                    calculation_method = EXCLUDED.calculation_method,
                    thresholds = EXCLUDED.thresholds,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                definition.id,
                definition.name,
                definition.description,
                definition.metric_type.value,
                definition.metric_category.value,
                definition.unit,
                definition.calculation_method,
                json.dumps(definition.thresholds),
                definition.is_active,
                definition.created_at,
                definition.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save metric definition: {e}")

    async def _save_alert(self, alert: UXMetricAlert) -> None:
        """Save alert to database."""
        try:
            query = """
                INSERT INTO ux_metric_alerts (
                    id, tenant_id, metric_name, alert_type, severity, message,
                    current_value, threshold_value, trend_data, is_resolved,
                    created_at, resolved_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """

            params = [
                alert.id,
                alert.tenant_id,
                alert.metric_name,
                alert.alert_type,
                alert.severity,
                alert.message,
                alert.current_value,
                alert.threshold_value,
                json.dumps(alert.trend_data),
                alert.is_resolved,
                alert.created_at,
                alert.resolved_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save alert: {e}")

    async def _get_metric_statistics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        metric_type: Optional[MetricType] = None,
        metric_category: Optional[MetricCategory] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get metric statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_metrics,
                    COUNT(DISTINCT metric_name) as unique_metrics,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    STDDEV(value) as std_value
                FROM ux_metrics
                WHERE tenant_id = $1 AND timestamp > $2
            """
            params = [tenant_id, cutoff_time]

            if metric_type:
                query += " AND metric_type = $3"
                params.append(metric_type.value)

            if metric_category:
                query += " AND metric_category = $4"
                params.append(metric_category.value)

            if user_id:
                query += " AND user_id = $5"
                params.append(user_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_metrics": result[0],
                        "unique_metrics": result[1],
                        "unique_users": result[2],
                        "unique_sessions": result[3],
                        "avg_value": float(result[4]) if result[4] else 0,
                        "min_value": float(result[5]) if result[5] else 0,
                        "max_value": float(result[6]) if result[6] else 0,
                        "std_value": float(result[7]) if result[7] else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get metric statistics: {e}")
            return {}

    async def _get_metric_aggregations(
        self,
        tenant_id: str,
        time_period_hours: int,
        metric_type: Optional[MetricType] = None,
        metric_category: Optional[MetricCategory] = None,
    ) -> List[UXMetricAggregation]:
        """Get metric aggregations."""
        try:
            query = """
                SELECT * FROM ux_metric_aggregations
                WHERE tenant_id = $1 AND period_hours = $2
            """
            params = [tenant_id, time_period_hours]

            if metric_type:
                query += " AND metric_type = $3"
                params.append(metric_type.value)

            if metric_category:
                query += " AND metric_category = $4"
                params.append(metric_category.value)

            query += " ORDER BY created_at DESC"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                aggregations = []
                for row in results:
                    aggregation = UXMetricAggregation(
                        id=row[0],
                        tenant_id=row[1],
                        metric_type=MetricType(row[2]),
                        metric_category=MetricCategory(row[3]),
                        metric_name=row[4],
                        aggregation_type=row[5],
                        period_hours=row[6],
                        value=row[7],
                        sample_size=row[8],
                        threshold_compliance=json.loads(row[9]) if row[9] else {},
                        created_at=row[10],
                    )
                    aggregations.append(aggregation)

                return aggregations

        except Exception as e:
            logger.error(f"Failed to get metric aggregations: {e}")
            return []

    async def _get_active_alerts(
        self,
        tenant_id: str,
        metric_type: Optional[MetricType] = None,
        metric_category: Optional[MetricCategory] = None,
    ) -> List[UXMetricAlert]:
        """Get active alerts."""
        try:
            query = """
                SELECT * FROM ux_metric_alerts
                WHERE tenant_id = $1 AND is_resolved = false
            """
            params = [tenant_id]

            if metric_type:
                query += " AND metric_name IN (SELECT name FROM ux_metric_definitions WHERE metric_type = $2)"
                params.append(metric_type.value)

            if metric_category:
                query += " AND metric_name IN (SELECT name FROM ux_metric_definitions WHERE metric_category = $3)"
                params.append(metric_category.value)

            query += " ORDER BY created_at DESC"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                alerts = []
                for row in results:
                    alert = UXMetricAlert(
                        id=row[0],
                        tenant_id=row[1],
                        metric_name=row[2],
                        alert_type=row[3],
                        severity=row[4],
                        message=row[5],
                        current_value=row[6],
                        threshold_value=row[7],
                        trend_data=json.loads(row[8]) if row[8] else None,
                        is_resolved=row[9],
                        created_at=row[10],
                        resolved_at=row[11],
                    )
                    alerts.append(alert)

                return alerts

        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []

    async def _get_metric_trends(
        self,
        tenant_id: str,
        time_period_hours: int,
        metric_type: Optional[MetricType] = None,
        metric_category: Optional[MetricCategory] = None,
    ) -> Dict[str, Any]:
        """Get metric trends."""
        try:
            # Get hourly data for trend analysis (stub - implement proper hourly aggregation)
            # For now, return empty trends - implement proper hourly aggregation as needed
            trends: Dict[str, Any] = {}
            return trends

        except Exception as e:
            logger.error(f"Failed to get metric trends: {e}")
            return {}

    async def _get_performance_benchmarks(
        self,
        tenant_id: str,
        metric_type: Optional[MetricType] = None,
        metric_category: Optional[MetricCategory] = None,
    ) -> Dict[str, Any]:
        """Get performance benchmarks."""
        try:
            # Get tenant's current performance (stub - implement as needed)
            current_performance: Dict[str, Any] = {}  # type: ignore[assignment]

            # Get industry averages (stub - implement as needed)
            industry_averages: Dict[str, Any] = {}  # type: ignore[assignment]

            # Calculate percentile rankings (stub - implement as needed)
            percentile_rankings: Dict[str, Any] = {}  # type: ignore[assignment]

            benchmarks = {
                "current_performance": current_performance,
                "industry_averages": industry_averages,
                "percentile_rankings": percentile_rankings,
            }

            return benchmarks

        except Exception as e:
            logger.error(f"Failed to get performance benchmarks: {e}")
            return {}

    async def _get_raw_metrics(
        self,
        tenant_id: str,
        metric_name: str,
        cutoff_time: datetime,
    ) -> List[UXMetric]:
        """Get raw metrics for analysis."""
        try:
            query = """
                SELECT * FROM ux_metrics
                WHERE tenant_id = $1 AND metric_name = $2 AND timestamp > $3
                ORDER BY timestamp ASC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id, metric_name, cutoff_time)

                metrics = []
                for row in results:
                    metric = UXMetric(
                        id=row[0],
                        user_id=row[1],
                        tenant_id=row[2],
                        session_id=row[3],
                        metric_type=MetricType(row[4]),
                        metric_category=MetricCategory(row[5]),
                        metric_name=row[6],
                        value=row[7],
                        unit=row[8],
                        context=json.loads(row[9]) if row[9] else {},
                        metadata=json.loads(row[10]) if row[10] else {},
                        timestamp=row[11],
                        created_at=row[12],
                    )
                    metrics.append(metric)

                return metrics

        except Exception as e:
            logger.error(f"Failed to get raw metrics: {e}")
            return []

    async def _calculate_metric_aggregations(
        self,
        metrics: List[UXMetric],
        aggregation_type: str,
    ) -> Dict[str, float]:
        """Calculate metric aggregations."""
        try:
            if not metrics:
                return {}

            values = [metric.value for metric in metrics]

            aggregations = {}
            if aggregation_type == "avg":
                aggregations["average"] = sum(values) / len(values)
            elif aggregation_type == "min":
                aggregations["minimum"] = min(values)
            elif aggregation_type == "max":
                aggregations["maximum"] = max(values)
            elif aggregation_type == "sum":
                aggregations["total"] = sum(values)
            elif aggregation_type == "count":
                aggregations["count"] = len(values)

            # Always calculate standard deviation
            if len(values) > 1:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                aggregations["std_dev"] = variance**0.5

            return aggregations

        except Exception as e:
            logger.error(f"Failed to calculate metric aggregations: {e}")
            return {}

    async def _calculate_threshold_compliance(
        self,
        metrics: List[UXMetric],
        definition: UXMetricDefinition,
    ) -> Dict[str, float]:
        """Calculate threshold compliance."""
        try:
            if not metrics or not definition.thresholds:
                return {}

            values = [metric.value for metric in metrics]

            compliance = {}
            for threshold_level, threshold_value in definition.thresholds.items():
                if self._is_threshold_breached(
                    sum(values) / len(values), threshold_value, definition.name
                ):
                    compliance[threshold_level] = 0.0  # Not compliant
                else:
                    compliance[threshold_level] = 1.0  # Compliant

            return compliance

        except Exception as e:
            logger.error(f"Failed to calculate threshold compliance: {e}")
            return {}

    async def _analyze_metric_trend(
        self,
        metrics: List[UXMetric],
        time_period_hours: int,
    ) -> Dict[str, Any]:
        """Analyze metric trend."""
        try:
            if len(metrics) < 2:
                return {"trend": "insufficient_data"}

            # Sort by timestamp
            sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)

            # Calculate trend
            first_half = sorted_metrics[: len(sorted_metrics) // 2]
            second_half = sorted_metrics[len(sorted_metrics) // 2 :]

            first_avg = sum(m.value for m in first_half) / len(first_half)
            second_avg = sum(m.value for m in second_half) / len(second_half)

            change_percent = (
                ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            )

            # Determine trend
            if change_percent > 10:
                trend = "improving"
            elif change_percent < -10:
                trend = "declining"
            else:
                trend = "stable"

            return {
                "trend": trend,
                "change_percent": change_percent,
                "first_period_avg": first_avg,
                "second_period_avg": second_avg,
                "data_points": len(metrics),
            }

        except Exception as e:
            logger.error(f"Failed to analyze metric trend: {e}")
            return {"trend": "error"}

    async def _get_user_breakdown(self, metrics: List[UXMetric]) -> Dict[str, Any]:
        """Get user breakdown analysis."""
        try:
            if not metrics:
                return {}

            # Group by user
            user_metrics = defaultdict(list)
            for metric in metrics:
                user_metrics[metric.user_id].append(metric)

            # Calculate user statistics
            user_stats = {}
            for user_id, user_metric_list in user_metrics.items():
                values = [m.value for m in user_metric_list]
                user_stats[user_id] = {
                    "count": len(user_metric_list),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }

            # Calculate overall statistics
            all_values = [m.value for m in metrics]

            breakdown = {
                "unique_users": len(user_metrics),
                "user_statistics": user_stats,
                "overall_average": sum(all_values) / len(all_values),
                "overall_min": min(all_values),
                "overall_max": max(all_values),
            }

            return breakdown

        except Exception as e:
            logger.error(f"Failed to get user breakdown: {e}")
            return {}

    async def _analyze_context_data(self, metrics: List[UXMetric]) -> Dict[str, Any]:
        """Analyze context data."""
        try:
            if not metrics:
                return {}

            # Aggregate context data
            context_aggregates: Dict[str, Dict[str, int]] = defaultdict(
                lambda: defaultdict(int)
            )  # type: ignore[assignment]
            for metric in metrics:
                for key, value in metric.context.items():
                    if isinstance(value, str):
                        context_aggregates[key][value] += 1

            # Analyze top context values
            context_analysis: Dict[str, Any] = {}
            for key, value_counts in context_aggregates.items():
                top_values = sorted(
                    value_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]
                context_analysis[key] = {
                    "top_values": top_values,
                    "unique_values": len(value_counts),
                    "total_occurrences": sum(value_counts.values()),
                }

            return context_analysis

        except Exception as e:
            logger.error(f"Failed to analyze context data: {e}")
            return {}

    async def _get_active_tenants(self) -> List[str]:
        """Get list of active tenants."""
        try:
            query = """
                SELECT DISTINCT tenant_id FROM ux_metrics
                WHERE timestamp > NOW() - INTERVAL '7 days'
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query)
                return [row[0] for row in results]

        except Exception as e:
            logger.error(f"Failed to get active tenants: {e}")
            return []

    async def _aggregate_metrics(
        self,
        tenant_id: str,
        period_hours: int,
        _aggregation_name: str,
    ) -> None:
        """Aggregate metrics for a specific period."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=period_hours)

            # Get all metric definitions
            definitions = list(self._metric_definitions.values())

            for definition in definitions:
                if not definition.is_active:
                    continue

                # Get metrics for this definition
                metrics = await self._get_raw_metrics(
                    tenant_id, definition.name, cutoff_time
                )

                if not metrics:
                    continue

                # Calculate aggregations
                aggregations = await self._calculate_metric_aggregations(metrics, "avg")

                # Create aggregation record
                aggregation = UXMetricAggregation(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    metric_type=definition.metric_type,
                    metric_category=definition.metric_category,
                    metric_name=definition.name,
                    aggregation_type="avg",
                    period_hours=period_hours,
                    value=aggregations.get("average", 0),
                    sample_size=len(metrics),
                    threshold_compliance=await self._calculate_threshold_compliance(
                        metrics, definition
                    ),
                    created_at=datetime.now(timezone.utc),
                )

                # Save aggregation
                await self._save_aggregation(aggregation)

        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")

    async def _save_aggregation(self, aggregation: UXMetricAggregation) -> None:
        """Save aggregation to database."""
        try:
            query = """
                INSERT INTO ux_metric_aggregations (
                    id, tenant_id, metric_type, metric_category, metric_name,
                    aggregation_type, period_hours, value, sample_size,
                    threshold_compliance, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (tenant_id, metric_name, period_hours, aggregation_type)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    sample_size = EXCLUDED.sample_size,
                    threshold_compliance = EXCLUDED.threshold_compliance
            """

            params = [
                aggregation.id,
                aggregation.tenant_id,
                aggregation.metric_type.value,
                aggregation.metric_category.value,
                aggregation.metric_name,
                aggregation.aggregation_type,
                aggregation.period_hours,
                aggregation.value,
                aggregation.sample_size,
                json.dumps(aggregation.threshold_compliance),
                aggregation.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save aggregation: {e}")


# Factory function
def create_ux_metrics_collector(db_pool) -> UXMetricsCollector:
    """Create UX metrics collector instance."""
    return UXMetricsCollector(db_pool)
