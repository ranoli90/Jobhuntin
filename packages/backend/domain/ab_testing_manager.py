"""
A/B Testing Manager for Phase 14.1 User Experience
"""

from __future__ import annotations

import asyncio
import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.ab_testing_manager")


class ExperimentStatus(Enum):
    """Experiment status."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestType(Enum):
    """Statistical test types."""

    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    WELCH_T_TEST = "welch_t_test"
    MANN_WHITNEY_U_TEST = "mann_whitney_u_test"
    ANOVA = "anova"


class MetricType(Enum):
    """Metrics for A/B testing."""

    CONVERSION_RATE = "conversion_rate"
    CLICK_THROUGH_RATE = "click_through_rate"
    ENGAGEMENT_TIME = "engagement_time"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    REVENUEUE = "revenue"


@dataclass
class ExperimentVariant:
    """A/B testing experiment variant."""

    id: str
    experiment_id: str
    name: str
    description: str
    variant_type: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    traffic_weight: float = 1.0
    traffic_allocation: Optional[float] = None
    is_control: bool = False
    is_active: bool = True
    created_at: datetime.now(timezone.utc)
    updated_at: datetime.now(timezone.utc)


@dataclass
class Experiment:
    """A/B testing experiment."""

    id: str
    name: str
    description: str
    status: ExperimentStatus
    traffic_allocation: float = 1.0
    sample_size: int
    duration_days: int
    target_metrics: List[MetricType]
    target_audience: Optional[Dict[str, Any]] = None
    ai_model_config: Optional[Dict[str, Any]] = None
    created_at: datetime.now(timezone.utc)
    updated_at: datetime.now(timezone.utc)
    variants: List[ExperimentVariant] = field(default_factory=list)


@dataclass
class ExperimentResult:
    """A/B testing experiment result."""

    id: str
    experiment_id: str
    variant_id: str
    user_id: str
    metrics: Dict[str, float]
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class StatisticalAnalysis:
    """Statistical analysis results."""

    experiment_id: str
    variant_a_id: str
    variant_b_id: str
    metric: MetricType
    variant_a_mean: float
    variant_b_mean: float
    variant_a_std: float
    variant_b_std: float
    variant_a_count: int
    variant_b_count: int
    n_a: int
    n_b: int
    p_value: float
    confidence_level: float
    confidence_interval: List[float]
    is_significant: bool
    effect_size: float
    winner: Optional[str] = None
    recommended_action: Optional[str] = None
    created_at: datetime.now(timezone.utc)


@dataclass
class ExperimentUserAssignment:
    """User assignment to experiment variant."""

    id: str
    user_id: str
    experiment_id: str
    variant_id: str
    assigned_at: datetime.now(timezone.utc)
    created_at: datetime.now(timezone.utc)


class ABTestingManager:
    """Advanced A/B testing system for user experience optimization."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._experiments: Dict[str, Experiment] = {}
        self._user_assignments: Dict[str, ExperimentUserAssignment] = {}
        self._statistical_cache: Dict[str, StatisticalAnalysis] = {}
        self._confidence_level = 0.95
        self._min_sample_size = 100

        # Initialize default experiments
        asyncio.create_task(self._initialize_default_experiments())

    async def create_experiment(
        self,
        name: str,
        description: str,
        variants_config: List[Dict[str, Any]],
        target_metrics: List[MetricType],
        sample_size: int = 1000,
        duration_days: int = 30,
        target_audience: Optional[Dict[str, Any]] = None,
        ai_model_config: Optional[Dict[str, Any]] = None,
        traffic_allocation: float = 1.0,
    ) -> Experiment:
        """Create a new A/B testing experiment."""
        try:
            # Create experiment
            experiment = Experiment(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                status=ExperimentStatus.DRAFT,
                traffic_allocation=traffic_allocation,
                sample_size=sample_size,
                duration_days=duration_days,
                target_metrics=target_metrics,
                target_audience=target_audience,
                ai_model_config=ai_model_config,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # Create variants
            variants = []
            for i, config in enumerate(variants_config):
                variant = await self._create_variant(
                    experiment.id, config, i, len(variants_config)
                )
                variants.append(variant)

            experiment.variants = variants

            # Save experiment
            await self._save_experiment(experiment)

            # Load into memory
            self._experiments[experiment.id] = experiment

            logger.info(f"Created A/B test experiment: {name}")
            return experiment

        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise

    async def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B testing experiment."""
        try:
            experiment = self._experiments.get(experiment_id)
            if not experiment:
                raise Exception(f"Experiment {experiment_id} not found")

            if experiment.status != ExperimentStatus.DRAFT:
                raise Exception(f"Experiment {experiment_id} is not in draft status")

            # Update status to running
            experiment.status = ExperimentStatus.RUNNING
            experiment.updated_at = datetime.now(timezone.utc)
            await self._save_experiment(experiment)

            logger.info(f"Started A/B test experiment: {experiment.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to start experiment: {e}")
            return False

    async def complete_experiment(
        self,
        experiment_id: str,
    ) -> StatisticalAnalysis:
        """Complete an experiment and determine winner."""
        try:
            experiment = self._experiments.get(experiment_id)
            if not experiment:
                raise Exception(f"Experiment {experiment_id} not found")

            if experiment.status != ExperimentStatus.RUNNING:
                raise Exception(f"Experiment {experiment_id} is not running")

            # Update status to completed
            experiment.status = ExperimentStatus.COMPLETED
            experiment.updated_at = datetime.now(timezone.utc)
            await self._save_experiment(experiment)

            # Perform statistical analysis
            analysis = await self._perform_statistical_analysis(experiment_id)

            # Save analysis
            await self._save_statistical_analysis(analysis)

            # Update experiment with winner
            if analysis.winner:
                await self._set_experiment_winner(experiment_id, analysis.winner)

            logger.info(
                f"Completed A/B test experiment: {experiment.name} (Winner: {analysis.winner})"
            )
            return analysis

        except Exception as e:
            logger.error(f"Failed to complete experiment: {e}")
            raise

    async def assign_user_to_variant(
        self,
        user_id: str,
        experiment_id: str,
        user_attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[ExperimentVariant]:
        """Assign user to experiment variant."""
        try:
            experiment = self._experiments.get(experiment_id)
            if not experiment:
                raise Exception(f"Experiment {experiment_id} not found")

            if experiment.status != ExperimentStatus.RUNNING:
                return None

            # Check if user is in target audience
            if experiment.target_audience and user_attributes:
                if not self._is_user_in_audience(
                    user_attributes, experiment.target_audience
                ):
                    return None

            # Get available variants
            available_variants = [v for v in experiment.variants if v.is_active]

            if not available_variants:
                return None

            # Assign variant based on traffic allocation
            variant = await self._assign_variant_to_user(
                available_variants, user_id, experiment.traffic_allocation
            )

            # Save assignment
            assignment = ExperimentUserAssignment(
                id=str(uuid.uuid4()),
                user_id=user_id,
                experiment_id=experiment_id,
                variant_id=variant.id,
                assigned_at=datetime.now(timezone.utc),
            )

            await self._save_user_assignment(assignment)

            # Update cache
            self._user_assignments[f"{user_id}:{experiment_id}"] = assignment

            logger.info(
                f"Assigned user {user_id} to variant {variant.name} in experiment {experiment_id}"
            )
            return variant

        except Exception as e:
            logger.error(f"Failed to assign user to variant: {e}")
            return None

    async def get_experiment_results(
        self,
        experiment_id: str,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ExperimentResult]:
        """Get experiment results."""
        try:
            query = """
                SELECT * FROM experiment_results
                WHERE experiment_id = $1
            """
            params = [experiment_id]

            if user_id:
                query += " AND user_id = $2"
                params.append(user_id)

            query += " ORDER BY created_at DESC LIMIT $3 OFFSET $4"
            params.extend([limit, offset])

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)

                results_list = []
                for row in results:
                    result = ExperimentResult(
                        id=row[0],
                        experiment_id=row[1],
                        variant_id=row[2],
                        user_id=row[3],
                        metrics=json.loads(row[4]) if row[4] else {},
                        created_at=row[5],
                    )
                    results_list.append(result)

                return results_list

        except Exception as e:
            logger.error(f"Failed to get experiment results: {e}")
            return []

    async def get_experiment_analytics(
        self,
        tenant_id: str,
        time_period_days: int = 30,
        experiment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive experiment analytics."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get experiment statistics
            exp_stats = await self._get_experiment_statistics(
                tenant_id, cutoff_time, experiment_id
            )

            # Get variant statistics
            variant_stats = await self._get_variant_statistics(
                tenant_id, cutoff_time, experiment_id
            )

            # Get user assignment statistics
            assignment_stats = await self._get_assignment_statistics(
                tenant_id, cutoff_time, experiment_id
            )

            # Get performance metrics
            performance_metrics = await self._get_performance_metrics(
                tenant_id, cutoff_time, experiment_id
            )

            analytics = {
                "period_days": time_period_days,
                "experiment_statistics": exp_stats,
                "variant_statistics": variant_stats,
                "assignment_statistics": assignment_stats,
                "performance_metrics": performance_metrics,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get experiment analytics: {e}")
            return {}

    async def get_user_experiments(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get experiments for a user."""
        try:
            # Get user assignments
            user_assignments = await self._get_user_assignments(user_id, tenant_id)

            experiment_ids = list(
                set([assignment.experiment_id for assignment in user_assignments])
            )

            experiments = []
            for exp_id in experiment_ids:
                experiment = self._experiments.get(exp_id)
                if experiment:
                    variant = self._get_user_variant(user_id, exp_id)

                    experiments.append(
                        {
                            "experiment_id": experiment.id,
                            "experiment_name": experiment.name,
                            "experiment_status": experiment.status.value,
                            "variant_id": variant.id if variant else None,
                            "variant_name": variant.name if variant else None,
                            "assigned_at": assignment.assigned_at.isoformat(),
                        }
                    )

            return experiments

        except Exception as e:
            logger.error(f"Failed to get user experiments: {e}")
            return []

    def _get_user_variant(
        self, user_id: str, experiment_id: str
    ) -> Optional[ExperimentVariant]:
        """Get user's assigned variant for an experiment."""
        try:
            assignment_key = f"{user_id}:{experiment_id}"
            if assignment_key in self._user_assignments:
                assignment = self._user_assignments[assignment_key]
                return self._experiments[assignment.experiment_id].variants.get(
                    assignment.variant_id
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get user variant: {e}")
            return None

    def _initialize_default_experiments(self) -> None:
        """Initialize default A/B testing experiments."""
        try:
            # Create default experiments
            default_experiments = [
                {
                    "name": "Homepage Hero Button CTA Test",
                    "description": "Test different CTA button text and colors",
                    "variants_config": [
                        {
                            "name": "Control",
                            "variant_type": "control",
                            "configuration": {
                                "button_text": "Get Started",
                                "button_color": "#3b82f6",
                                "button_size": "large",
                            },
                            "traffic_weight": 0.5,
                        },
                        {
                            "name": "Variant A",
                            "variant_type": "variant",
                            "configuration": {
                                "button_text": "Get Started Now",
                                "button_color": "#10b981",
                                "button_size": "large",
                            },
                            "traffic_weight": 0.25,
                        },
                        {
                            "name": "Variant B",
                            "variant_type": "variant",
                            "configuration": {
                                "button_text": "Start Free Trial",
                                "button_color": "#059669",
                                "button_size": "large",
                            },
                            "traffic_weight": 0.25,
                        },
                    ],
                    "target_metrics": [MetricType.CONVERSION_RATE],
                    "sample_size": 1000,
                    "duration_days": 14,
                },
                {
                    "name": "Email Subject Line Test",
                    "personalization": "Test different email subject lines",
                    "variants_config": [
                        {
                            "name": "Control",
                            "variant_type": "control",
                            "configuration": {
                                "subject_line": "Your Job Application",
                                "sender_name": "JobHuntin Team",
                            },
                            "traffic_weight": 0.5,
                        },
                        {
                            "name": "Variant A",
                            "variant_type": "variant",
                            "configuration": {
                                "subject_line": "Your Job Application at [Company]",
                                "sender_name": "JobHuntin Team",
                            },
                            "traffic_weight": 0.25,
                        },
                        {
                            "name": "Variant B",
                            "variant_type": "variant",
                            "configuration": {
                                "subject_line": "Exciting Opportunity at [Company]",
                                "sender_name": "JobHuntin Team",
                            },
                            "traffic_weight": 0.25,
                        },
                    ],
                    "target_metrics": [
                        MetricType.CLICK_THROUGH_RATE,
                        MetricType.CONVERSION_RATE,
                    ],
                    "sample_size": 500,
                    "duration_days": 7,
                },
                {
                    "name": "Page Layout Test",
                    "description": "Test different page layouts",
                    "variants_config": [
                        {
                            "name": "Control",
                            "variant_type": "control",
                            "configuration": {
                                "layout": "sidebar_left",
                                "header_style": "fixed",
                            },
                            "traffic_weight": 0.5,
                        },
                        {
                            "name": "Variant A",
                            "variant_type": "variant",
                            "configuration": {
                                "layout": "top_nav",
                                "header_style": "sticky",
                            },
                            "traffic_weight": 0.25,
                        },
                        {
                            "name": "Variant B",
                            "variant_type": "variant",
                            "configuration": {
                                "layout": "sidebar_right",
                                "header_style": "fixed",
                            },
                            "traffic_weight": 0.25,
                        },
                    ],
                    "target_metrics": [
                        MetricType.ENGAGEMENT_TIME,
                        MetricType.CONVERSION_RATE,
                    ],
                    "sample_size": 300,
                    "duration_days": 10,
                },
            ]

            for exp_config in default_experiments:
                try:
                    await self.create_experiment(**exp_config)
                except Exception as e:
                    logger.error(f"Failed to create default experiment: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize default experiments: {e}")

    async def _create_variant(
        self,
        experiment_id: str,
        config: Dict[str, Any],
        index: int,
        total_variants: int,
    ) -> ExperimentVariant:
        """Create an experiment variant."""
        try:
            variant = ExperimentVariant(
                id=str(uuid.uuid4()),
                experiment_id=experiment_id,
                name=config.get("name", f"Variant {chr(65 + index)}"),
                description=config.get("description", ""),
                variant_type=config.get("variant_type", "variant"),
                configuration=config,
                traffic_weight=config.get("traffic_weight", 1.0 / total_variants),
                is_control=config.get("variant_type") == "control",
                is_active=True,
            )

            return variant

        except Exception as e:
            logger.error(f"Failed to create variant: {e}")
            raise

    async def _assign_variant_to_user(
        self,
        variants: List[ExperimentVariant],
        user_id: str,
        traffic_allocation: float,
    ) -> ExperimentVariant:
        """Assign variant to user based on traffic allocation."""
        try:
            # Calculate cumulative weights
            cumulative_weights = []
            current_weight = 0.0

            for variant in variants:
                current_weight += variant.traffic_weight
                cumulative_weights.append(current_weight)

            # Generate random number between 0 and 1
            import random

            user_hash = hash(user_id) % 100
            random_value = random.random()

            # Find appropriate variant
            for i, weight in enumerate(cumulative_weights):
                if user_hash < weight * 100:
                    return variants[i]

            # Fallback to first variant
            return variants[0]

        except Exception as e:
            logger.error(f"Failed to assign variant to user: {e}")
            raise

    def _is_user_in_audience(
        self, user_attributes: Dict[str, Any], target_audience: Dict[str, Any]
    ) -> bool:
        """Check if user matches target audience criteria."""
        try:
            for key, value in target_audience.items():
                if key in user_attributes:
                    if isinstance(value, list):
                        if user_attributes.get(key) not in value:
                            return False
                    else:
                        if user_attributes[key] != value:
                            return False
                else:
                    if user_attributes.get(key) != value:
                        return False

            return True

        except Exception as e:
            logger.error(f"Failed to check audience membership: {e}")
            return False

    async def _perform_statistical_analysis(
        self,
        experiment_id: str,
    ) -> StatisticalAnalysis:
        """Perform statistical analysis for experiment."""
        try:
            experiment = self._experiments.get(experiment_id)
            if not experiment:
                raise Exception(f"Experiment {experiment_id} not found")

            # Get results for each variant
            variant_results = {}
            for variant in experiment.variants:
                if variant.is_active:
                    variant_results[variant.id] = await self._get_variant_results(
                        experiment_id, variant.id
                    )

            # Calculate analysis for each metric
            analyses = []
            for metric in experiment.target_metrics:
                for variant_a in experiment.variants:
                    for variant_b in experiment.variants:
                        if variant_a.is_active and variant_b.is_active:
                            analysis = await self._calculate_statistical_significance(
                                experiment_id, variant_a.id, variant_b.id, metric
                            )
                            analyses.append(analysis)

            # Get the best analysis for each metric
            best_analyses = {}
            metric_analyses = {}

            for analysis in analyses:
                metric = analysis.metric
                if metric not in metric_analyses:
                    metric_analyses[metric] = analysis

                # Keep the analysis with highest significance
                current_best = metric_analyses.get(metric)
                if analysis.is_significant and (
                    not current_best or analysis.p_value < analysis.p_value
                ):
                    metric_analyses[metric] = analysis

            # Create final analysis
            best_analysis = StatisticalAnalysis(
                id=str(uuid.uuid4()),
                experiment_id=experiment_id,
                variant_a_id=None,
                variant_b_id=None,
                metric=metric,
                variant_a_mean=0.0,
                variant_b_mean=0.0,
                variant_a_std=0.0,
                variant_b_std=0.0,
                variant_a_count=0,
                variant_b_count=0,
                n_a=0,
                n_b=0,
                p_value=0.0,
                confidence_level=self._confidence_level,
                confidence_interval=[0.0, 0.0],
                is_significant=False,
                effect_size=0.0,
                winner=None,
                recommended_action=None,
                created_at=datetime.now(timezone.utc),
            )

            # Find best analysis for each metric
            for metric in experiment.target_metrics:
                if metric in metric_analyses:
                    best_analysis = metric_analytics[metric]
                    break

            return best_analysis

        except Exception as e:
            logger.error(f"Failed to perform statistical analysis: {e}")
            raise

    async def _calculate_statistical_significance(
        self,
        experiment_id: str,
        variant_a_id: str,
        variant_b_id: str,
        metric: MetricType,
        confidence_level: float = 0.95,
    ) -> StatisticalAnalysis:
        """Calculate statistical significance between two variants."""
        try:
            # Get results for both variants
            results_a = await self._get_variant_results(experiment_id, variant_a_id)
            results_b = await self._get_variant_results(experiment_id, variant_b_id)

            if not results_a or not results_b:
                raise Exception("Insufficient data for statistical analysis")

            # Extract metric values
            values_a = [r.metrics.get(metric.value, 0.0) for r in results_a]
            values_b = [r.metrics.get(metric.value, 0.0) for r in results_b]

            n_a = len(values_a)
            n_b = len(values_b)

            if n_a < 30 or n_b < 30:
                raise Exception("Insufficient sample size for statistical analysis")

            # Calculate basic statistics
            mean_a = sum(values_a) / n_a
            mean_b = sum(values_b) / n_b

            var_a = sum((x - mean_a) ** 2 for x in values_a) / (n_a - 1)
            var_b = sum((x - mean_b) ** 2 for x in values_b) / (n_b - 1)

            # Calculate pooled standard error
            pooled_se = math.sqrt(
                ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
            )
            se_diff = pooled_se * math.sqrt(1 / n_a + 1 / n_b)

            # Calculate t-statistic
            t_stat = (mean_a - mean_b) / se_diff

            # Calculate p-value (two-tailed test)
            from scipy import stats

            p_value = 2 * (
                1 - stats.t.cdf(abs(t_stat), len(values_a) + len(values_b) - 2)
            )

            # Calculate confidence interval
            margin = se_diff * 1.96  # 95% confidence
            ci_lower = (mean_a - mean_b) - margin
            ci_upper = (mean_a - mean_b) + margin
            confidence_interval = [ci_lower, ci_upper]

            # Calculate effect size (Cohen's d)
            pooled_std = math.sqrt(
                ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
            )
            effect_size = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0.0

            # Determine significance
            is_significant = p_value < (1 - confidence_level)

            # Determine winner
            winner = (
                "A"
                if is_significant and mean_a > mean_b
                else "B"
                if is_significant
                else None
            )

            # Recommended action
            if is_significant:
                if effect_size > 0.1:
                    recommended_action = "Implement variant A"
                elif effect_size < -0.1:
                    recommended_action = "Implement variant B"
                else:
                    recommended_action = "Consider A/B testing with larger sample size"
            else:
                recommended_action = "No clear winner"

            return StatisticalAnalysis(
                id=str(uuid.uuid4()),
                experiment_id=experiment_id,
                variant_a_id=variant_a_id,
                variant_b_id=variant_b_id,
                metric=metric,
                variant_a_mean=mean_a,
                variant_b_mean=mean_b,
                variant_a_std=var_a,
                variant_b_std=var_b,
                variant_a_count=n_a,
                variant_b_count=n_b,
                n_a=n_a,
                n_b=n_b,
                p_value=p_value,
                confidence_level=confidence_level,
                confidence_interval=confidence_interval,
                is_significant=is_significant,
                effect_size=effect_size,
                winner=winner,
                recommended_action=recommended_action,
                created_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Failed to calculate statistical significance: {e}")
            raise

    async def _get_variant_results(
        self,
        experiment_id: str,
        variant_id: str,
    ) -> List[ExperimentResult]:
        """Get results for a specific variant."""
        try:
            query = """
                SELECT * FROM experiment_results
                WHERE experiment_id = $1 AND variant_id = $2
                ORDER BY created_at ASC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, experiment_id, variant_id)

                results_list = []
                for row in results:
                    result = ExperimentResult(
                        id=row[0],
                        experiment_id=row[1],
                        variant_id=row[2],
                        user_id=row[3],
                        metrics=json.loads(row[4]) if row[4] else {},
                        created_at=row[5],
                    )
                    results_list.append(result)

                return results_list

        except Exception as e:
            logger.error(f"Failed to get variant results: {e}")
            return []

    async def _get_experiment_statistics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        experiment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get experiment statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_experiments,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_experiments,
                    COUNT(CASE WHEN status = 'running' THEN 1 END) as running_experiments,
                    AVG(sample_size) as avg_sample_size,
                    AVG(duration_days) as avg_duration
                FROM experiments
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if experiment_id:
                query += " AND id = $3"
                params.append(experiment_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_experiments": result[0],
                        "completed_experiments": result[1],
                        "running_experiments": result[2],
                        "avg_sample_size": float(result[3]) if result[3] else 0,
                        "avg_duration": float(result[4]) if result[4] else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get experiment statistics: {e}")
            return {}

    async def _get_variant_statistics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        experiment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get variant statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_variants,
                    COUNT(CASE WHEN is_active THEN 1 END) as active_variants,
                    AVG(traffic_weight) as avg_traffic_weight,
                    AVG(traffic_allocation) as avg_traffic_allocation
                FROM experiment_variants
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if experiment_id:
                query += " AND experiment_id = $3"
                params.append(experiment_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_variants": result[0],
                        "active_variants": result[1],
                        "avg_traffic_weight": float(result[2]) if result[2] else 0,
                        "avg_traffic_allocation": float(result[3]) if result[3] else 0,
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get variant statistics: {e}")
            return {}

    async def _get_assignment_statistics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        experiment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get user assignment statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_assignments,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT experiment_id) as experiments_participated
                FROM user_assignments
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if experiment_id:
                query += " AND experiment_id = $3"
                params.append(experiment_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "total_assignments": result[0],
                        "unique_users": result[1],
                        "experiments_participated": result[2],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get assignment statistics: {e}")
            return {}

    async def _get_performance_metrics(
        self,
        tenant_id: str,
        cutoff_time: datetime,
        experiment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get performance metrics for experiments."""
        try:
            query = """
                SELECT
                    AVG(processing_time_ms) as avg_processing_time,
                    AVG(success_rate) as avg_success_rate,
                    COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as errors
                FROM experiment_results
                WHERE tenant_id = $1 AND created_at > $2
            """
            params = [tenant_id, cutoff_time]

            if experiment_id:
                query += " AND experiment_id = $3"
                params.append(experiment_id)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)

                if result:
                    return {
                        "avg_processing_time": float(result[0]) if result[0] else 0,
                        "avg_success_rate": float(result[1]) if result[1] else 0,
                        "total_errors": result[2],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}

    def _save_experiment(self, experiment: Experiment) -> None:
        """Save experiment to database."""
        try:
            query = """
                INSERT INTO experiments (
                    id, name, description, status, traffic_allocation, sample_size,
                    duration_days, target_metrics, target_audience,
                    ai_model_config, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    traffic_allocation = EXCLUDED.traffic_allocation,
                    sample_size = EXCLUDED.sample_size,
                    duration_days = EXCLUDED.duration_days,
                    target_metrics = EXCLUDED.target_metrics,
                    target_audience = EXCLUDED.target_audience,
                    ai_model_config = EXCLUDED.ai_model_config,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                experiment.id,
                experiment.name,
                experiment.description,
                experiment.status,
                experiment.traffic_allocation,
                experiment.sample_size,
                experiment.duration_days,
                json.dumps(experiment.target_metrics),
                json.dumps(experiment.target_audience),
                json.dumps(experiment.ai_model_config),
                experiment.created_at,
                experiment.updated_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save experiment: {e}")

    def _save_variant(self, variant: ExperimentVariant) -> None:
        """Save variant to database."""
        try:
            query = """
                INSERT INTO experiment_variants (
                    id, experiment_id, name, description, variant_type,
                    configuration, traffic_weight, is_active, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    variant_type = EXCLUDED.variant_type,
                    configuration = EXCLUDED.configuration,
                    traffic_weight = EXCLUDED.traffic_weight,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
            """

            params = [
                variant.id,
                variant.experiment_id,
                variant.name,
                variant.description,
                variant.variant_type,
                variant.configuration,
                variant.traffic_weight,
                variant.is_active,
                variant.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save variant: {e}")

    async def _save_user_assignment(self, assignment: ExperimentUserAssignment) -> None:
        """Save user assignment to database."""
        try:
            query = """
                INSERT INTO user_assignments (
                    id, user_id, experiment_id, variant_id, assigned_at
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, experiment_id) DO UPDATE SET
                    variant_id = EXCLUDED.variant_id,
                    assigned_at = EXCLUDED.assigned_at
            """

            params = [
                assignment.id,
                assignment.user_id,
                assignment.experiment_id,
                assignment.variant_id,
                assignment.assigned_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save user assignment: {e}")

    async def _save_statistical_analysis(self, analysis: StatisticalAnalysis) -> None:
        """Save statistical analysis to database."""
        try:
            query = """
                INSERT INTO statistical_analyses (
                    id, experiment_id, variant_a_id, variant_b_id, metric,
                    variant_a_mean, variant_b_mean, variant_a_std, variant_b_std,
                    variant_a_count, variant_b_count, n_a, n_b, p_value,
                    confidence_level, confidence_interval, is_significant,
                    effect_size, winner, recommended_action, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """

            params = [
                analysis.id,
                analysis.experiment_id,
                analysis.variant_a_id,
                analysis.variant_b_id,
                analysis.metric,
                analysis.variant_a_mean,
                analysis.variant_b_mean,
                analysis.variant_a_std,
                analysis.variant_b_std,
                analysis.variant_a_count,
                analysis.variant_b_count,
                analysis.n_a,
                analysis.n_b,
                analysis.p_value,
                analysis.confidence_level,
                analysis.confidence_interval,
                analysis.is_significant,
                analysis.effect_size,
                analysis.winner,
                analysis.recommended_action,
                analysis.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save statistical analysis: {e}")

    def _save_ux_score(self, ux_score: UXScore) -> None:
        """Save UX score to database."""
        try:
            query = """
                INSERT INTO ux_scores (
                    id, user_id, tenant_id, session_id, overall_score, usability_score,
                    performance_score, accessibility_score, engagement_score,
                    satisfaction_score, factors, calculated_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """

            params = [
                ux_score.id,
                ux_score.user_id,
                ux_score.tenant_id,
                ux_score.session_id,
                ux_score.overall_score,
                ux_score.usability_score,
                ux_score.performance_score,
                ux_score.accessibility_score,
                ux_score.engagement_score,
                ux_score.satisfaction_score,
                ux_score.factors,
                ux_score.calculated_at,
                ux_score.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save UX score: {e}")

    async def _save_nps_response(self, nps_response: NPSResponse) -> None:
        """Save NPS response to database."""
        try:
            query = """
                INSERT INTO nps_responses (
                    id, user_id, tenant_id, score, promoter_type, reason,
                    metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """

            params = [
                nps_response.id,
                nps_response.user_id,
                nps_response.tenant_id,
                nps_response.score,
                nps_response.promoter_type,
                nps_response.reason,
                nps_response.metadata,
                nps_response.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save NPS response: {e}")


# Factory function
def create_ab_testing_manager(db_pool) -> ABTestingManager:
    """Create A/B testing manager instance."""
    return ABTestingManager(db_pool)
