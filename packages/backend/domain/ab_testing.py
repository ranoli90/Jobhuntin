"""A/B Testing System for AI Content Quality Measurement.

Implements comprehensive A/B testing framework for AI-generated content:
- Experiment management and configuration
- Variant generation and distribution
- Performance metrics and analytics
- Statistical significance testing
- AI content quality measurement
- Automated winner determination

Key features:
1. AI content variant generation
2. User segmentation and targeting
3. Performance metrics tracking
4. Statistical analysis and significance testing
5. Automated experiment management
6. Quality scoring and measurement
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from packages.backend.llm.client import LLMClient
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.ab_testing")


class ExperimentStatus(StrEnum):
    """Status of A/B testing experiments."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantType(StrEnum):
    """Types of A/B test variants."""

    AI_GENERATED = "ai_generated"
    TEMPLATE_BASED = "template_based"
    HYBRID = "hybrid"
    CONTROL = "control"


class MetricType(StrEnum):
    """Types of metrics to measure."""

    CONVERSION_RATE = "conversion_rate"
    ENGAGEMENT_TIME = "engagement_time"
    USER_SATISFACTION = "user_satisfaction"
    CONTENT_QUALITY = "content_quality"
    TASK_COMPLETION = "task_completion"
    ERROR_RATE = "error_rate"
    CLICK_THROUGH_RATE = "click_through_rate"


class Experiment(BaseModel):
    """A/B testing experiment configuration."""

    id: str = Field(..., description="Experiment unique identifier")
    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description")
    status: ExperimentStatus = Field(..., description="Experiment status")
    traffic_allocation: float = Field(
        default=0.5, description="Traffic allocation (0.0-1.0)"
    )
    variants: List[Dict[str, Any]] = Field(..., description="Test variants")
    target_metrics: List[MetricType] = Field(..., description="Metrics to track")
    sample_size: int = Field(default=1000, description="Required sample size")
    confidence_level: float = Field(
        default=0.95, description="Statistical confidence level"
    )
    minimum_detectable_effect: float = Field(
        default=0.05, description="Minimum detectable effect"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = Field(
        default=None, description="Experiment start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Experiment completion time"
    )
    duration_days: Optional[int] = Field(
        default=None, description="Planned duration in days"
    )
    target_audience: Optional[Dict[str, Any]] = Field(
        default=None, description="Target audience criteria"
    )
    ai_model_config: Optional[Dict[str, Any]] = Field(
        default=None, description="AI model configuration"
    )


class Variant(BaseModel):
    """A/B test variant configuration."""

    id: str = Field(..., description="Variant unique identifier")
    experiment_id: str = Field(..., description="Parent experiment ID")
    name: str = Field(..., description="Variant name")
    type: VariantType = Field(..., description="Variant type")
    traffic_weight: float = Field(default=0.5, description="Traffic weight")
    configuration: Dict[str, Any] = Field(..., description="Variant configuration")
    ai_prompt: Optional[str] = Field(default=None, description="AI prompt for variant")
    template_id: Optional[str] = Field(
        default=None, description="Template ID for variant"
    )
    is_control: bool = Field(
        default=False, description="Whether this is control variant"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExperimentResult(BaseModel):
    """A/B test experiment results."""

    experiment_id: str = Field(..., description="Experiment ID")
    variant_id: str = Field(..., description="Variant ID")
    user_id: str = Field(..., description="User ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    user_feedback: Optional[Dict[str, Any]] = Field(
        default=None, description="User feedback"
    )
    quality_score: Optional[float] = Field(
        default=None, description="AI content quality score"
    )
    conversion: bool = Field(default=False, description="Whether conversion occurred")
    engagement_time_seconds: Optional[float] = Field(
        default=None, description="Engagement time"
    )
    error_occurred: bool = Field(default=False, description="Whether error occurred")


class StatisticalAnalysis(BaseModel):
    """Statistical analysis of A/B test results."""

    experiment_id: str = Field(..., description="Experiment ID")
    variant_a_id: str = Field(..., description="Variant A ID")
    variant_b_id: str = Field(..., description="Variant B ID")
    metric: MetricType = Field(..., description="Analyzed metric")
    variant_a_mean: float = Field(..., description="Variant A mean")
    variant_b_mean: float = Field(..., description="Variant B mean")
    variant_a_std: float = Field(..., description="Variant A standard deviation")
    variant_b_std: float = Field(..., description="Variant B standard deviation")
    sample_size_a: int = Field(..., description="Variant A sample size")
    sample_size_b: int = Field(..., description="Variant B sample size")
    p_value: float = Field(..., description="Statistical p-value")
    confidence_interval: List[float] = Field(..., description="Confidence interval")
    is_significant: bool = Field(
        ..., description="Whether result is statistically significant"
    )
    effect_size: float = Field(..., description="Effect size (Cohen's d)")
    winner: Optional[str] = Field(default=None, description="Winning variant")
    analysis_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ABTestingManager:
    """A/B testing manager for AI content quality measurement.

    Manages A/B testing experiments for AI-generated content:
    - Experiment creation and configuration
    - Variant generation using AI
    - User assignment and tracking
    - Performance metrics collection
    - Statistical analysis and significance testing
    - Automated winner determination
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm_client = llm_client
        self._settings = get_settings()

        # Experiment storage (would be database in production)
        self._experiments: Dict[str, Experiment] = {}
        self._variants: Dict[str, Variant] = {}
        self._results: List[ExperimentResult] = []

        # AI content generation templates
        self._ai_templates = self._initialize_ai_templates()

        # Statistical analysis methods
        self._statistical_methods = self._initialize_statistical_methods()

        # Quality measurement metrics
        self._quality_metrics = self._initialize_quality_metrics()

    @property
    def llm(self) -> LLMClient:
        """Get LLM client instance."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self._settings)
        return self._llm_client

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
    ) -> Experiment:
        """Create a new A/B testing experiment.

        Args:
            name: Experiment name
            description: Experiment description
            variants_config: Configuration for test variants
            target_metrics: Metrics to track
            sample_size: Required sample size
            duration_days: Planned duration
            target_audience: Target audience criteria
            ai_model_config: AI model configuration

        Returns:
            Created experiment
        """
        try:
            import uuid

            experiment_id = str(uuid.uuid4())

            # Generate variants
            variants = []
            for i, config in enumerate(variants_config):
                variant = await self._create_variant(
                    experiment_id=experiment_id,
                    config=config,
                    index=i,
                )
                variants.append(variant.model_dump())
                self._variants[variant.id] = variant

            # Create experiment
            experiment = Experiment(
                id=experiment_id,
                name=name,
                description=description,
                status=ExperimentStatus.DRAFT,
                traffic_allocation=1.0 / len(variants),
                variants=variants,
                target_metrics=target_metrics,
                sample_size=sample_size,
                duration_days=duration_days,
                target_audience=target_audience,
                ai_model_config=ai_model_config,
            )

            self._experiments[experiment_id] = experiment

            return experiment

        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise

    async def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B testing experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            Whether experiment was started successfully
        """
        try:
            if experiment_id not in self._experiments:
                return False

            experiment = self._experiments[experiment_id]
            experiment.status = ExperimentStatus.RUNNING
            experiment.started_at = datetime.now(timezone.utc)

            logger.info(f"Started experiment: {experiment.name} ({experiment_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to start experiment {experiment_id}: {e}")
            return False

    async def assign_user_to_variant(
        self,
        user_id: str,
        experiment_id: str,
        user_attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[Variant]:
        """Assign user to experiment variant.

        Args:
            user_id: User ID
            experiment_id: Experiment ID
            user_attributes: User attributes for targeting

        Returns:
            Assigned variant or None
        """
        try:
            if experiment_id not in self._experiments:
                return None

            experiment = self._experiments[experiment_id]

            # Check if user is in target audience
            if experiment.target_audience and not self._is_user_in_audience(
                user_attributes, experiment.target_audience
            ):
                return None

            # Check if experiment is running
            if experiment.status != ExperimentStatus.RUNNING:
                return None

            # Assign variant based on traffic allocation

            variants = self._get_experiment_variants(experiment_id)
            if not variants:
                return None

            # Simple hash-based assignment for consistency
            user_hash = hash(user_id) % 100
            cumulative_weight = 0

            for variant in variants:
                cumulative_weight += int(variant.traffic_weight * 100)
                if user_hash < cumulative_weight:
                    return variant

            return variants[0]  # Fallback

        except Exception as e:
            logger.error(f"Failed to assign user to variant: {e}")
            return None

    async def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        metrics: Dict[str, float],
        user_feedback: Optional[Dict[str, Any]] = None,
        quality_score: Optional[float] = None,
    ) -> bool:
        """Record experiment result.

        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID
            user_id: User ID
            metrics: Performance metrics
            user_feedback: User feedback
            quality_score: AI content quality score

        Returns:
            Whether result was recorded successfully
        """
        try:
            result = ExperimentResult(
                experiment_id=experiment_id,
                variant_id=variant_id,
                user_id=user_id,
                metrics=metrics,
                user_feedback=user_feedback,
                quality_score=quality_score,
                conversion=metrics.get("conversion", False),
                engagement_time_seconds=metrics.get("engagement_time_seconds"),
                error_occurred=metrics.get("error_occurred", False),
            )

            self._results.append(result)

            # Check if experiment should be completed
            await self._check_experiment_completion(experiment_id)

            return True

        except Exception as e:
            logger.error(f"Failed to record result: {e}")
            return False

    async def analyze_results(
        self,
        experiment_id: str,
        metric: MetricType,
    ) -> List[StatisticalAnalysis]:
        """Analyze experiment results for statistical significance.

        Args:
            experiment_id: Experiment ID
            metric: Metric to analyze

        Returns:
            Statistical analysis results
        """
        try:
            if experiment_id not in self._experiments:
                return []

            experiment = self._experiments[experiment_id]
            variants = self._get_experiment_variants(experiment_id)

            if len(variants) < 2:
                return []

            analyses = []

            # Compare each variant pair
            for i in range(len(variants)):
                for j in range(i + 1, len(variants)):
                    variant_a = variants[i]
                    variant_b = variants[j]

                    # Get results for each variant
                    results_a = [
                        r
                        for r in self._results
                        if r.experiment_id == experiment_id
                        and r.variant_id == variant_a.id
                    ]
                    results_b = [
                        r
                        for r in self._results
                        if r.experiment_id == experiment_id
                        and r.variant_id == variant_b.id
                    ]

                    if not results_a or not results_b:
                        continue

                    # Calculate statistics
                    analysis = await self._calculate_statistical_significance(
                        results_a=results_a,
                        results_b=results_b,
                        metric=metric,
                        confidence_level=experiment.confidence_level,
                    )

                    analyses.append(analysis)

            return analyses

        except Exception as e:
            logger.error(f"Failed to analyze results: {e}")
            return []

    async def generate_ai_variant(
        self,
        base_prompt: str,
        variant_type: str,
        optimization_goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate AI variant for A/B testing.

        Args:
            base_prompt: Base AI prompt
            variant_type: Type of variant to generate
            optimization_goal: Goal for optimization
            context: Additional context

        Returns:
            AI variant configuration
        """
        try:
            # Build LLM prompt for variant generation
            prompt = self._build_variant_generation_prompt(
                base_prompt=base_prompt,
                variant_type=variant_type,
                optimization_goal=optimization_goal,
                context=context,
            )

            # Generate variant using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response
                variant_config = await self._parse_llm_variant_response(result)

                return {
                    "type": "ai_generated",
                    "prompt": variant_config.get("prompt", base_prompt),
                    "parameters": variant_config.get("parameters", {}),
                    "expected_improvement": variant_config.get(
                        "expected_improvement", 0.0
                    ),
                    "rationale": variant_config.get("rationale", ""),
                }

            return {"type": "ai_generated", "prompt": base_prompt}

        except Exception as e:
            logger.error(f"Failed to generate AI variant: {e}")
            return {"type": "ai_generated", "prompt": base_prompt}

    async def get_experiment_results(
        self,
        experiment_id: str,
        variant_id: Optional[str] = None,
    ) -> List[ExperimentResult]:
        """Get experiment results.

        Args:
            experiment_id: Experiment ID
            variant_id: Optional variant ID filter

        Returns:
            Experiment results
        """
        try:
            results = [r for r in self._results if r.experiment_id == experiment_id]

            if variant_id:
                results = [r for r in results if r.variant_id == variant_id]

            return results

        except Exception as e:
            logger.error(f"Failed to get experiment results: {e}")
            return []

    async def get_experiment_summary(
        self,
        experiment_id: str,
    ) -> Dict[str, Any]:
        """Get experiment summary with key metrics.

        Args:
            experiment_id: Experiment ID

        Returns:
            Experiment summary
        """
        try:
            if experiment_id not in self._experiments:
                return {}

            experiment = self._experiments[experiment_id]
            variants = self._get_experiment_variants(experiment_id)

            summary = {
                "experiment": experiment.model_dump(),
                "variants": [v.model_dump() for v in variants],
                "total_participants": 0,
                "variant_metrics": {},
                "status": experiment.status,
            }

            # Calculate metrics for each variant
            for variant in variants:
                variant_results = await self.get_experiment_results(
                    experiment_id, variant.id
                )
                summary["variant_metrics"][variant.id] = {
                    "participants": len(variant_results),
                    "conversion_rate": 0.0,
                    "avg_engagement_time": 0.0,
                    "error_rate": 0.0,
                    "avg_quality_score": 0.0,
                }

                if variant_results:
                    conversions = sum(1 for r in variant_results if r.conversion)
                    summary["variant_metrics"][variant.id]["conversion_rate"] = (
                        conversions / len(variant_results)
                    )

                    engagement_times = [
                        r.engagement_time_seconds
                        for r in variant_results
                        if r.engagement_time_seconds is not None
                    ]
                    if engagement_times:
                        summary["variant_metrics"][variant.id][
                            "avg_engagement_time"
                        ] = sum(engagement_times) / len(engagement_times)

                    errors = sum(1 for r in variant_results if r.error_occurred)
                    summary["variant_metrics"][variant.id]["error_rate"] = errors / len(
                        variant_results
                    )

                    quality_scores = [
                        r.quality_score
                        for r in variant_results
                        if r.quality_score is not None
                    ]
                    if quality_scores:
                        summary["variant_metrics"][variant.id]["avg_quality_score"] = (
                            sum(quality_scores) / len(quality_scores)
                        )

                summary["total_participants"] += len(variant_results)

            return summary

        except Exception as e:
            logger.error(f"Failed to get experiment summary: {e}")
            return {}

    async def complete_experiment(
        self,
        experiment_id: str,
        winner_variant_id: Optional[str] = None,
    ) -> bool:
        """Complete experiment and determine winner.

        Args:
            experiment_id: Experiment ID
            winner_variant_id: Optional winner variant ID

        Returns:
            Whether experiment was completed successfully
        """
        try:
            if experiment_id not in self._experiments:
                return False

            experiment = self._experiments[experiment_id]
            experiment.status = ExperimentStatus.COMPLETED
            experiment.completed_at = datetime.now(timezone.utc)

            # If no winner specified, determine automatically
            if not winner_variant_id:
                winner_variant_id = await self._determine_winner(experiment_id)

            logger.info(
                f"Completed experiment {experiment.name} with winner: {winner_variant_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to complete experiment {experiment_id}: {e}")
            return False

    async def _create_variant(
        self,
        experiment_id: str,
        config: Dict[str, Any],
        index: int,
    ) -> Variant:
        """Create a variant for experiment."""
        try:
            import uuid

            variant_id = str(uuid.uuid4())

            variant = Variant(
                id=variant_id,
                experiment_id=experiment_id,
                name=config.get("name", f"Variant {index + 1}"),
                type=VariantType(config.get("type", "ai_generated")),
                traffic_weight=config.get("traffic_weight", 0.5),
                configuration=config,
                ai_prompt=config.get("ai_prompt"),
                template_id=config.get("template_id"),
                is_control=config.get("is_control", False),
            )

            return variant

        except Exception as e:
            logger.error(f"Failed to create variant: {e}")
            raise

    async def _calculate_statistical_significance(
        self,
        results_a: List[ExperimentResult],
        results_b: List[ExperimentResult],
        metric: MetricType,
        confidence_level: float = 0.95,
    ) -> StatisticalAnalysis:
        """Calculate statistical significance between two variants."""
        try:
            import math

            # Extract metric values
            values_a = [r.metrics.get(metric.value, 0.0) for r in results_a]
            values_b = [r.metrics.get(metric.value, 0.0) for r in results_b]

            if not values_a or not values_b:
                raise ValueError("No data for statistical analysis")

            # Calculate basic statistics
            mean_a = sum(values_a) / len(values_a)
            mean_b = sum(values_b) / len(values_b)

            var_a = sum((x - mean_a) ** 2 for x in values_a) / len(values_a)
            var_b = sum((x - mean_b) ** 2 for x in values_b) / len(values_b)

            std_a = math.sqrt(var_a)
            std_b = math.sqrt(var_b)

            # Calculate pooled standard error
            n_a, n_b = len(values_a), len(values_b)
            pooled_se = math.sqrt(
                ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
            )
            se_diff = pooled_se * math.sqrt(1 / n_a + 1 / n_b)

            # Calculate t-statistic
            t_stat = (mean_a - mean_b) / se_diff

            # Calculate degrees of freedom
            n_a + n_b - 2

            # Calculate p-value (simplified - would use scipy in production)
            # This is a simplified approximation
            p_value = 2 * (1 - self._normal_cdf(abs(t_stat)))

            # Calculate confidence interval
            margin = se_diff * 1.96  # For 95% confidence
            ci_lower = (mean_a - mean_b) - margin
            ci_upper = (mean_a - mean_b) + margin
            confidence_interval = [ci_lower, ci_upper]

            # Calculate effect size (Cohen's d)
            pooled_std = math.sqrt(
                ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b)
            )
            effect_size = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0.0

            # Determine significance
            is_significant = p_value < (1 - confidence_level)

            # Determine winner
            winner = None
            if is_significant:
                winner = "A" if mean_a > mean_b else "B"

            return StatisticalAnalysis(
                experiment_id=results_a[0].experiment_id,
                variant_a_id=results_a[0].variant_id,
                variant_b_id=results_b[0].variant_id,
                metric=metric,
                variant_a_mean=mean_a,
                variant_b_mean=mean_b,
                variant_a_std=std_a,
                variant_b_std=std_b,
                sample_size_a=n_a,
                sample_size_b=n_b,
                p_value=p_value,
                confidence_interval=confidence_interval,
                is_significant=is_significant,
                effect_size=effect_size,
                winner=winner,
            )

        except Exception as e:
            logger.error(f"Failed to calculate statistical significance: {e}")
            raise

    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF function."""
        # Simplified approximation of normal CDF
        import math

        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    async def _determine_winner(self, experiment_id: str) -> Optional[str]:
        """Determine winning variant based on results."""
        try:
            variants = self._get_experiment_variants(experiment_id)

            if len(variants) < 2:
                return None

            best_variant = None
            best_score = -float("inf")

            for variant in variants:
                variant_results = await self.get_experiment_results(
                    experiment_id, variant.id
                )

                if not variant_results:
                    continue

                # Calculate composite score
                conversion_rate = sum(1 for r in variant_results if r.conversion) / len(
                    variant_results
                )
                error_rate = sum(1 for r in variant_results if r.error_occurred) / len(
                    variant_results
                )

                # Weighted score (can be customized)
                score = conversion_rate * 0.7 - error_rate * 0.3

                if score > best_score:
                    best_score = score
                    best_variant = variant.id

            return best_variant

        except Exception as e:
            logger.error(f"Failed to determine winner: {e}")
            return None

    async def _check_experiment_completion(self, experiment_id: str) -> None:
        """Check if experiment should be completed."""
        try:
            if experiment_id not in self._experiments:
                return

            experiment = self._experiments[experiment_id]

            if experiment.status != ExperimentStatus.RUNNING:
                return

            # Check sample size
            total_results = len(
                [r for r in self._results if r.experiment_id == experiment_id]
            )

            if total_results >= experiment.sample_size:
                await self.complete_experiment(experiment_id)
                return

            # Check duration
            if experiment.started_at and experiment.duration_days:
                elapsed_days = (datetime.now(timezone.utc) - experiment.started_at).days
                if elapsed_days >= experiment.duration_days:
                    await self.complete_experiment(experiment_id)
                    return

        except Exception as e:
            logger.error(f"Failed to check experiment completion: {e}")

    def _is_user_in_audience(
        self,
        user_attributes: Optional[Dict[str, Any]],
        target_audience: Dict[str, Any],
    ) -> bool:
        """Check if user matches target audience criteria."""
        if not user_attributes or not target_audience:
            return True

        # Simple audience matching (can be enhanced)
        for key, value in target_audience.items():
            user_value = user_attributes.get(key)

            if isinstance(value, list):
                if user_value not in value:
                    return False
            elif isinstance(value, dict):
                if value.get("min") and user_value < value.get("min"):
                    return False
                if value.get("max") and user_value > value.get("max"):
                    return False
            elif user_value != value:
                return False

        return True

    def _get_experiment_variants(self, experiment_id: str) -> List[Variant]:
        """Get all variants for an experiment."""
        return [v for v in self._variants.values() if v.experiment_id == experiment_id]

    def _build_variant_generation_prompt(
        self,
        base_prompt: str,
        variant_type: str,
        optimization_goal: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build LLM prompt for variant generation."""

        context_info = ""
        if context:
            context_info = f"""
            Context:
            - User attributes: {context.get("user_attributes", {})}
            - Previous performance: {context.get("previous_performance", {})}
            - Optimization history: {context.get("optimization_history", {})}
            """

        prompt = f"""
        Generate an optimized variant for A/B testing AI content.

        Base Prompt: {base_prompt}
        Variant Type: {variant_type}
        Optimization Goal: {optimization_goal}

        {context_info}

        Generate a variant that:
        1. Is optimized for {optimization_goal}
        2. Maintains the core functionality of the base prompt
        3. Uses different wording, structure, or approach
        4. Is likely to improve the target metric
        5. Is appropriate for the target audience

        Provide the response as JSON with:
        - prompt: The optimized prompt
        - parameters: Key parameters changed
        - expected_improvement: Expected improvement percentage (0.0-1.0)
        - rationale: Explanation of changes

        Focus on measurable improvements while maintaining content quality.
        """

        return prompt

    async def _parse_llm_variant_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for variant generation."""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON object found in LLM response")
                return {}

            json_str = response[json_start:json_end]
            variant_config = json.loads(json_str)

            return variant_config

        except Exception as e:
            logger.error(f"Failed to parse LLM variant response: {e}")
            return {}

    def _initialize_ai_templates(self) -> Dict[str, Any]:
        """Initialize AI content generation templates."""
        return {
            "cover_letter": {
                "professional": "Generate a professional cover letter for {job_title} at {company}",
                "creative": "Create a creative cover letter that stands out for {job_title} role",
                "technical": "Write a technical cover letter highlighting skills for {job_title}",
            },
            "resume_summary": {
                "concise": "Generate a concise resume summary for {experience_level} professional",
                "detailed": "Create a detailed resume summary showcasing achievements for {industry}",
                "executive": "Write an executive resume summary for {leadership_level} position",
            },
            "interview_questions": {
                "behavioral": "Generate behavioral interview questions for {job_title}",
                "technical": "Create technical interview questions for {technical_role}",
                "situational": "Develop situational interview questions for {industry}",
            },
            "career_path": {
                "growth": "Generate career growth path for {current_role} to {target_role}",
                "transition": "Create career transition plan from {industry} to {target_industry}",
                "skill_development": "Design skill development plan for {skill_category}",
            },
        }

    def _initialize_statistical_methods(self) -> Dict[str, Any]:
        """Initialize statistical analysis methods."""
        return {
            "significance_tests": {
                "t_test": "Two-sample t-test for means",
                "chi_square": "Chi-square test for proportions",
                "mann_whitney": "Mann-Whitney U test for non-parametric data",
            },
            "effect_sizes": {
                "cohens_d": "Cohen's d for standardized effect size",
                "pearson_r": "Pearson correlation coefficient",
                "odds_ratio": "Odds ratio for binary outcomes",
            },
            "confidence_intervals": {
                "wald": "Wald confidence interval",
                "wilson": "Wilson score interval",
                "bootstrap": "Bootstrap confidence interval",
            },
        }

    def _initialize_quality_metrics(self) -> Dict[str, Any]:
        """Initialize AI content quality metrics."""
        return {
            "readability": {
                "flesch_kincaid": "Flesch-Kincaid readability score",
                "gunning_fog": "Gunning fog index",
                "smog": "SMOG grading",
            },
            "engagement": {
                "time_on_page": "Average time spent on content",
                "scroll_depth": "Average scroll depth",
                "interaction_rate": "Rate of user interactions",
            },
            "conversion": {
                "click_through_rate": "Click-through rate",
                "conversion_rate": "Conversion rate",
                "bounce_rate": "Bounce rate",
            },
            "satisfaction": {
                "user_ratings": "Average user ratings",
                "feedback_sentiment": "Sentiment analysis of feedback",
                "nps_score": "Net Promoter Score",
            },
            "ai_quality": {
                "coherence": "Content coherence score",
                "relevance": "Content relevance score",
                "completeness": "Content completeness score",
            },
        }


_ab_testing_manager: Optional[ABTestingManager] = None


def get_ab_testing_manager() -> ABTestingManager:
    """Get or create singleton A/B testing manager."""
    global _ab_testing_manager
    if _ab_testing_manager is None:
        _ab_testing_manager = ABTestingManager()
    return _ab_testing_manager
