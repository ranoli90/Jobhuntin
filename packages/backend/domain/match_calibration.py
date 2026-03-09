"""Match Score Calibration System - Data-driven optimization of matching algorithms.

This module provides tools for analyzing match outcomes and automatically calibrating
match weights based on real-world performance data to improve matching accuracy.
"""

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import asyncpg

from backend.domain.match_weights import (
    TenantMatchConfig,
    WeightCategory,
    get_match_weights_manager,
)
from shared.logging_config import get_logger

logger = get_logger("sorce.match_calibration")


class CalibrationOutcome(Enum):
    """Types of calibration outcomes."""

    SUCCESS = "success"  # User got the job or positive response
    APPLICATION = "application"  # User applied (positive engagement)
    REJECTION = "rejection"  # User rejected or no response
    WITHDRAWN = "withdrawn"  # User withdrew application
    PENDING = "pending"  # Still in progress
    UNKNOWN = "unknown"  # Unknown outcome


@dataclass
class CalibrationDataPoint:
    """Single data point for calibration analysis."""

    tenant_id: str
    user_id: str
    job_id: str
    match_score: float
    category_scores: Dict[str, float]
    config_version: int
    user_action: str
    outcome: CalibrationOutcome
    applied_at: datetime
    outcome_timestamp: Optional[datetime] = None
    days_to_outcome: Optional[int] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None


@dataclass
class CalibrationMetrics:
    """Metrics for calibration analysis."""

    total_matches: int
    successful_matches: int
    application_rate: float
    success_rate: float
    avg_match_score: float
    avg_successful_score: float
    avg_unsuccessful_score: float
    score_correlation: float  # Correlation between score and success
    category_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    score_distribution: Dict[str, int] = field(default_factory=dict)
    outcome_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class CalibrationRecommendation:
    """Recommendation for weight adjustment."""

    category: WeightCategory
    current_weight: float
    recommended_weight: float
    confidence: float  # 0.0 to 1.0
    reasoning: str
    expected_impact: float
    sample_size: int


class MatchScoreCalibrator:
    """System for calibrating match scores based on real outcome data."""

    def __init__(self):
        """Initialize the calibrator."""
        self._outcome_weights = {
            CalibrationOutcome.SUCCESS: 1.0,
            CalibrationOutcome.APPLICATION: 0.7,
            CalibrationOutcome.PENDING: 0.5,
            CalibrationOutcome.REJECTION: 0.2,
            CalibrationOutcome.WITHDRAWN: 0.1,
            CalibrationOutcome.UNKNOWN: 0.0,
        }

    async def collect_calibration_data(
        self, db_pool: asyncpg.Pool, tenant_id: str, days_back: int = 90
    ) -> List[CalibrationDataPoint]:
        """Collect calibration data from match history.

        Args:
            db_pool: Database connection pool
            tenant_id: Tenant identifier
            days_back: Number of days to look back

        Returns:
            List of calibration data points
        """
        try:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT 
                        tenant_id,
                        user_id,
                        job_id,
                        match_score,
                        category_scores,
                        config_version,
                        user_action,
                        outcome,
                        applied_at,
                        updated_at as outcome_timestamp,
                        job_title,
                        company_name,
                        salary_min,
                        salary_max
                    FROM match_score_history
                    WHERE tenant_id = $1 
                        AND applied_at >= NOW() - INTERVAL '%s days'
                    ORDER BY applied_at DESC
                """,
                    tenant_id,
                    days_back,
                )

                data_points = []
                for row in rows:
                    # Calculate days to outcome
                    days_to_outcome = None
                    if row["outcome_timestamp"] and row["applied_at"]:
                        days_to_outcome = (
                            row["outcome_timestamp"] - row["applied_at"]
                        ).days

                    # Parse category scores
                    category_scores = {}
                    if row["category_scores"]:
                        category_scores = json.loads(row["category_scores"])

                    # Parse outcome
                    try:
                        outcome = CalibrationOutcome(row["outcome"])
                    except ValueError:
                        outcome = CalibrationOutcome.UNKNOWN

                    data_point = CalibrationDataPoint(
                        tenant_id=row["tenant_id"],
                        user_id=row["user_id"],
                        job_id=row["job_id"],
                        match_score=float(row["match_score"]),
                        category_scores=category_scores,
                        config_version=row["config_version"],
                        user_action=row["user_action"],
                        outcome=outcome,
                        applied_at=row["applied_at"],
                        outcome_timestamp=row["outcome_timestamp"],
                        days_to_outcome=days_to_outcome,
                        job_title=row["job_title"],
                        company_name=row["company_name"],
                        salary_min=float(row["salary_min"])
                        if row["salary_min"]
                        else None,
                        salary_max=float(row["salary_max"])
                        if row["salary_max"]
                        else None,
                    )

                    data_points.append(data_point)

                logger.info(
                    f"Collected {len(data_points)} calibration data points for tenant {tenant_id}"
                )
                return data_points

        except Exception as e:
            logger.error(
                f"Failed to collect calibration data for tenant {tenant_id}: {e}"
            )
            return []

    def calculate_metrics(
        self, data_points: List[CalibrationDataPoint]
    ) -> CalibrationMetrics:
        """Calculate calibration metrics from data points.

        Args:
            data_points: List of calibration data points

        Returns:
            Calibration metrics
        """
        if not data_points:
            return CalibrationMetrics(
                total_matches=0,
                successful_matches=0,
                application_rate=0.0,
                success_rate=0.0,
                avg_match_score=0.0,
                avg_successful_score=0.0,
                avg_unsuccessful_score=0.0,
                score_correlation=0.0,
            )

        # Basic metrics
        total_matches = len(data_points)
        successful_matches = len(
            [dp for dp in data_points if dp.outcome == CalibrationOutcome.SUCCESS]
        )
        applications = len([dp for dp in data_points if dp.user_action == "applied"])

        application_rate = applications / total_matches if total_matches > 0 else 0.0
        success_rate = successful_matches / applications if applications > 0 else 0.0

        # Score metrics
        all_scores = [dp.match_score for dp in data_points]
        successful_scores = [
            dp.match_score
            for dp in data_points
            if dp.outcome == CalibrationOutcome.SUCCESS
        ]
        unsuccessful_scores = [
            dp.match_score
            for dp in data_points
            if dp.outcome
            in [CalibrationOutcome.REJECTION, CalibrationOutcome.WITHDRAWN]
        ]

        avg_match_score = statistics.mean(all_scores) if all_scores else 0.0
        avg_successful_score = (
            statistics.mean(successful_scores) if successful_scores else 0.0
        )
        avg_unsuccessful_score = (
            statistics.mean(unsuccessful_scores) if unsuccessful_scores else 0.0
        )

        # Score correlation
        score_correlation = self._calculate_score_correlation(data_points)

        # Category performance
        category_performance = self._calculate_category_performance(data_points)

        # Score distribution
        score_distribution = self._calculate_score_distribution(all_scores)

        # Outcome distribution
        outcome_distribution = {}
        for dp in data_points:
            outcome_name = dp.outcome.value
            outcome_distribution[outcome_name] = (
                outcome_distribution.get(outcome_name, 0) + 1
            )

        return CalibrationMetrics(
            total_matches=total_matches,
            successful_matches=successful_matches,
            application_rate=application_rate,
            success_rate=success_rate,
            avg_match_score=avg_match_score,
            avg_successful_score=avg_successful_score,
            avg_unsuccessful_score=avg_unsuccessful_score,
            score_correlation=score_correlation,
            category_performance=category_performance,
            score_distribution=score_distribution,
            outcome_distribution=outcome_distribution,
        )

    def _calculate_score_correlation(
        self, data_points: List[CalibrationDataPoint]
    ) -> float:
        """Calculate correlation between match score and success."""
        if len(data_points) < 10:
            return 0.0

        # Create binary success indicator
        scores = []
        success_indicators = []

        for dp in data_points:
            scores.append(dp.match_score)
            # Weight outcomes: success=1.0, application=0.7, rejection=0.2, etc.
            success_indicator = self._outcome_weights.get(dp.outcome, 0.0)
            success_indicators.append(success_indicator)

        try:
            correlation = statistics.correlation(scores, success_indicators)
            return (
                correlation
                if not (correlation is None or correlation != correlation)
                else 0.0
            )
        except (ValueError, statistics.StatisticsError):
            return 0.0

    def _calculate_category_performance(
        self, data_points: List[CalibrationDataPoint]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics for each category."""
        category_performance = {}

        # Get all category names
        all_categories = set()
        for dp in data_points:
            all_categories.update(dp.category_scores.keys())

        for category in all_categories:
            category_scores = []
            category_success = []

            for dp in data_points:
                if category in dp.category_scores:
                    category_scores.append(dp.category_scores[category])
                    category_success.append(self._outcome_weights.get(dp.outcome, 0.0))

            if category_scores:
                avg_score = statistics.mean(category_scores)
                avg_success = statistics.mean(category_success)

                # Calculate correlation for this category
                try:
                    correlation = statistics.correlation(
                        category_scores, category_success
                    )
                    correlation = (
                        correlation
                        if not (correlation is None or correlation != correlation)
                        else 0.0
                    )
                except (ValueError, statistics.StatisticsError):
                    correlation = 0.0

                category_performance[category] = {
                    "avg_score": avg_score,
                    "avg_success": avg_success,
                    "correlation": correlation,
                    "sample_size": len(category_scores),
                }

        return category_performance

    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution in buckets."""
        if not scores:
            return {}

        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        }

        for score in scores:
            if score < 0.2:
                distribution["0.0-0.2"] += 1
            elif score < 0.4:
                distribution["0.2-0.4"] += 1
            elif score < 0.6:
                distribution["0.4-0.6"] += 1
            elif score < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1

        return distribution

    def generate_recommendations(
        self, metrics: CalibrationMetrics, config: TenantMatchConfig
    ) -> List[CalibrationRecommendation]:
        """Generate weight adjustment recommendations based on metrics.

        Args:
            metrics: Calibration metrics
            config: Current tenant configuration

        Returns:
            List of calibration recommendations
        """
        recommendations = []

        # Analyze each category
        for category, weight_config in config.weights.items():
            if not weight_config.enabled:
                continue

            category_name = category.value
            if category_name not in metrics.category_performance:
                continue

            perf = metrics.category_performance[category_name]

            # Calculate recommended weight based on performance
            current_weight = weight_config.weight
            recommended_weight = self._calculate_recommended_weight(
                current_weight, perf, metrics
            )

            # Calculate confidence based on sample size
            confidence = min(
                1.0, perf["sample_size"] / 50.0
            )  # More data = higher confidence

            # Generate reasoning
            reasoning = self._generate_reasoning(
                category_name, current_weight, recommended_weight, perf, metrics
            )

            # Calculate expected impact
            expected_impact = self._calculate_expected_impact(
                current_weight, recommended_weight, perf
            )

            # Only recommend significant changes
            if abs(recommended_weight - current_weight) > 0.1 and confidence > 0.3:
                recommendations.append(
                    CalibrationRecommendation(
                        category=category,
                        current_weight=current_weight,
                        recommended_weight=recommended_weight,
                        confidence=confidence,
                        reasoning=reasoning,
                        expected_impact=expected_impact,
                        sample_size=perf["sample_size"],
                    )
                )

        # Sort by expected impact
        recommendations.sort(key=lambda r: r.expected_impact, reverse=True)

        return recommendations[:5]  # Return top 5 recommendations

    def _calculate_recommended_weight(
        self,
        current_weight: float,
        performance: Dict[str, float],
        metrics: CalibrationMetrics,
    ) -> float:
        """Calculate recommended weight based on performance metrics."""
        correlation = performance["correlation"]
        avg_success = performance["avg_success"]

        # Base adjustment on correlation
        if correlation > 0.3:  # Strong positive correlation
            # Increase weight if correlation is strong and positive
            adjustment = 0.2 * (correlation - 0.3) / 0.7
        elif correlation < -0.3:  # Strong negative correlation
            # Decrease weight if correlation is negative
            adjustment = -0.2 * (-correlation - 0.3) / 0.7
        else:
            adjustment = 0.0

        # Adjust based on success rate
        if avg_success > 0.7:  # High success rate
            adjustment += 0.1
        elif avg_success < 0.3:  # Low success rate
            adjustment -= 0.1

        # Apply adjustment with bounds
        recommended_weight = current_weight + adjustment
        return max(0.1, min(2.0, recommended_weight))

    def _generate_reasoning(
        self,
        category: str,
        current_weight: float,
        recommended_weight: float,
        performance: Dict[str, float],
        metrics: CalibrationMetrics,
    ) -> str:
        """Generate reasoning for weight adjustment."""
        correlation = performance["correlation"]
        avg_success = performance["avg_success"]
        sample_size = performance["sample_size"]

        reasoning_parts = []

        if correlation > 0.3:
            reasoning_parts.append(
                f"Strong positive correlation ({correlation:.2f}) indicates this category is predictive of success"
            )
        elif correlation < -0.3:
            reasoning_parts.append(
                f"Negative correlation ({correlation:.2f}) suggests current weight may be misaligned"
            )
        else:
            reasoning_parts.append(
                f"Weak correlation ({correlation:.2f}) indicates limited predictive value"
            )

        if avg_success > 0.7:
            reasoning_parts.append(
                f"High success rate ({avg_success:.1%}) suggests good matching"
            )
        elif avg_success < 0.3:
            reasoning_parts.append(
                f"Low success rate ({avg_success:.1%}) indicates poor matching"
            )

        if abs(recommended_weight - current_weight) > 0.1:
            if recommended_weight > current_weight:
                reasoning_parts.append(
                    f"Increasing weight from {current_weight:.2f} to {recommended_weight:.2f}"
                )
            else:
                reasoning_parts.append(
                    f"Decreasing weight from {current_weight:.2f} to {recommended_weight:.2f}"
                )

        reasoning_parts.append(f"Based on {sample_size} data points")

        return ". ".join(reasoning_parts)

    def _calculate_expected_impact(
        self,
        current_weight: float,
        recommended_weight: float,
        performance: Dict[str, float],
    ) -> float:
        """Calculate expected impact of weight adjustment."""
        correlation = performance["correlation"]
        weight_change = abs(recommended_weight - current_weight)

        # Impact is proportional to correlation and weight change
        impact = abs(correlation) * weight_change * 0.5
        return min(1.0, impact)

    async def apply_recommendations(
        self,
        db_pool: asyncpg.Pool,
        tenant_id: str,
        recommendations: List[CalibrationRecommendation],
        updated_by: str,
    ) -> bool:
        """Apply calibration recommendations to tenant configuration.

        Args:
            db_pool: Database connection pool
            tenant_id: Tenant identifier
            recommendations: List of recommendations to apply
            updated_by: User making the changes

        Returns:
            True if applied successfully, False otherwise
        """
        try:
            manager = get_match_weights_manager()
            weight_config = await manager.get_tenant_config(db_pool, tenant_id)

            # Apply recommendations
            for rec in recommendations:
                if rec.confidence > 0.5:  # Only apply high-confidence recommendations
                    success = await manager.update_weight(
                        db_pool,
                        tenant_id,
                        rec.category,
                        rec.recommended_weight,
                        weight_config.enabled,
                        weight_config.priority,
                        weight_config.custom_rules,
                        updated_by,
                    )

                    if not success:
                        logger.warning(
                            f"Failed to apply recommendation for {rec.category.value}"
                        )
                        return False

            logger.info(
                f"Applied {len([r for r in recommendations if r.confidence > 0.5])} high-confidence recommendations for tenant {tenant_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to apply recommendations for tenant {tenant_id}: {e}")
            return False

    async def run_calibration_cycle(
        self,
        db_pool: asyncpg.Pool,
        tenant_id: str,
        days_back: int = 90,
        auto_apply: bool = False,
        updated_by: str = "system",
    ) -> Dict[str, Any]:
        """Run a complete calibration cycle.

        Args:
            db_pool: Database connection pool
            tenant_id: Tenant identifier
            days_back: Number of days to analyze
            auto_apply: Whether to automatically apply recommendations
            updated_by: User making the changes

        Returns:
            Calibration results
        """
        try:
            # Collect data
            data_points = await self.collect_calibration_data(
                db_pool, tenant_id, days_back
            )

            if len(data_points) < 50:
                return {
                    "tenant_id": tenant_id,
                    "status": "insufficient_data",
                    "message": f"Insufficient data points ({len(data_points)} for calibration. Minimum 50 required.",
                    "recommendations": [],
                }

            # Calculate metrics
            metrics = self.calculate_metrics(data_points)

            # Get current config
            manager = get_match_weights_manager()
            config = await manager.get_tenant_config(db_pool, tenant_id)

            # Generate recommendations
            recommendations = self.generate_recommendations(metrics, config)

            # Apply recommendations if requested
            applied_count = 0
            if auto_apply and recommendations:
                success = await self.apply_recommendations(
                    db_pool, tenant_id, recommendations, updated_by
                )
                if success:
                    applied_count = len(
                        [r for r in recommendations if r.confidence > 0.5]
                    )

            return {
                "tenant_id": tenant_id,
                "status": "completed",
                "data_points": len(data_points),
                "metrics": {
                    "total_matches": metrics.total_matches,
                    "success_rate": metrics.success_rate,
                    "application_rate": metrics.application_rate,
                    "avg_match_score": metrics.avg_match_score,
                    "score_correlation": metrics.score_correlation,
                },
                "recommendations": [
                    {
                        "category": rec.category.value,
                        "current_weight": rec.current_weight,
                        "recommended_weight": rec.recommended_weight,
                        "confidence": rec.confidence,
                        "reasoning": rec.reasoning,
                        "expected_impact": rec.expected_impact,
                        "sample_size": rec.sample_size,
                    }
                    for rec in recommendations
                ],
                "applied_count": applied_count,
                "calibrated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Calibration cycle failed for tenant {tenant_id}: {e}")
            return {
                "tenant_id": tenant_id,
                "status": "error",
                "message": str(e),
                "recommendations": [],
            }


# Global instance
_match_calibrator = None


def get_match_calibrator() -> MatchScoreCalibrator:
    """Get the global match calibrator instance."""
    global _match_calibrator
    if _match_calibrator is None:
        _match_calibrator = MatchScoreCalibrator()
    return _match_calibrator
