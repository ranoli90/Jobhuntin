"""LLM-Enhanced Career Path Analysis.

Implements AI-powered career path generation using LLM:
- Dynamic role generation based on market data
- Personalized career trajectory analysis
- AI-powered skill gap identification
- Market-aware career recommendations
- Real-time industry trend integration
- Personalized learning path generation

Key features:
1. LLM-powered role analysis and generation
2. Market data integration for career trends
3. Personalized skill gap analysis
4. AI-driven career path recommendations
5. Dynamic learning path creation
6. Industry trend awareness
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.domain.career_path import CareerLevel, CareerTrack, SkillGap
from backend.llm.client import LLMClient
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.llm_career_path")


class MarketTrend(BaseModel):
    """Market trend data for career analysis."""

    trend_name: str = Field(..., description="Name of the trend")
    trend_type: str = Field(..., description="Type of trend (growth, decline, stable)")
    impact_level: str = Field(..., description="Impact level (high, medium, low)")
    affected_roles: List[str] = Field(
        default_factory=list, description="Roles affected by trend"
    )
    emerging_skills: List[str] = Field(
        default_factory=list, description="Emerging skills"
    )
    declining_skills: List[str] = Field(
        default_factory=list, description="Declining skills"
    )
    market_demand: float = Field(
        default=0.0, description="Market demand score (0.0-1.0)"
    )
    salary_impact: float = Field(default=0.0, description="Salary impact percentage")
    confidence_score: float = Field(default=0.0, description="Trend confidence score")


class DynamicCareerRole(BaseModel):
    """AI-generated career role with market intelligence."""

    title: str = Field(..., description="Role title")
    level: CareerLevel = Field(..., description="Career level")
    track: CareerTrack = Field(..., description="Career track")
    typical_years_experience: tuple[int, int] = Field(
        ..., description="Experience range"
    )
    typical_skills: List[str] = Field(
        default_factory=list, description="Required skills"
    )
    salary_range_usd: tuple[int, int] = Field(..., description="Salary range")
    growth_outlook: str = Field(default="stable", description="Growth outlook")
    market_demand: float = Field(default=0.5, description="Market demand score")
    trend_alignment: float = Field(
        default=0.5, description="Alignment with market trends"
    )
    ai_confidence: float = Field(default=0.5, description="AI generation confidence")
    emerging_skills: List[str] = Field(
        default_factory=list, description="Emerging skills"
    )
    industry_focus: List[str] = Field(
        default_factory=list, description="Industry focus areas"
    )
    remote_work_potential: str = Field(
        default="medium", description="Remote work potential"
    )


class PersonalizedCareerPath(BaseModel):
    """Personalized career path with AI insights."""

    user_profile: Dict[str, Any] = Field(..., description="User profile data")
    current_role: str = Field(..., description="Current role")
    target_role: str = Field(..., description="Target role")
    path_type: str = Field(..., description="Path type (promotion, transition, pivot)")
    steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Career path steps"
    )
    skill_gaps: List[SkillGap] = Field(default_factory=list, description="Skill gaps")
    market_opportunities: List[str] = Field(
        default_factory=list, description="Market opportunities"
    )
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    estimated_timeline_months: int = Field(default=24, description="Timeline in months")
    potential_salary_increase_pct: float = Field(
        default=0.2, description="Salary increase potential"
    )
    market_alignment_score: float = Field(
        default=0.5, description="Market alignment score"
    )
    ai_confidence: float = Field(default=0.5, description="AI confidence score")
    personalization_factors: Dict[str, Any] = Field(
        default_factory=dict, description="Personalization factors"
    )


class LLMCareerPathAnalyzer:
    """AI-powered career path analyzer with market intelligence.

    Uses LLM to generate dynamic career paths based on:
    - Market trends and industry data
    - User profile and preferences
    - Real-time job market analysis
    - Personalized skill gap analysis
    - AI-driven learning recommendations
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm_client = llm_client
        self._settings = get_settings()

        # Market trend data (would be updated from real market APIs)
        self._market_trends = self._initialize_market_trends()

        # Industry-specific career patterns
        self._industry_patterns = self._initialize_industry_patterns()

        # Emerging skills database
        self._emerging_skills = self._initialize_emerging_skills()

        # Role generation templates
        self._role_templates = self._initialize_role_templates()

    @property
    def llm(self) -> LLMClient:
        """Get LLM client instance."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self._settings)
        return self._llm_client

    async def generate_dynamic_career_roles(
        self,
        industry: str,
        experience_level: str,
        skills: List[str],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> List[DynamicCareerRole]:
        """Generate dynamic career roles using LLM and market data.

        Args:
            industry: Industry focus
            experience_level: Experience level (entry, mid, senior, executive)
            skills: Current skills
            preferences: User preferences and constraints

        Returns:
            List of AI-generated career roles
        """
        try:
            # Build LLM prompt for role generation
            prompt = self._build_role_generation_prompt(
                industry=industry,
                experience_level=experience_level,
                skills=skills,
                preferences=preferences,
                market_trends=self._get_relevant_trends(industry),
                emerging_skills=self._get_relevant_emerging_skills(industry),
            )

            # Generate roles using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response into structured roles
                roles = await self._parse_llm_roles_response(
                    result, industry, experience_level
                )

                # Enhance with market data
                for role in roles:
                    role = await self._enhance_role_with_market_data(role, industry)

                return roles
            else:
                logger.error(f"Unexpected LLM response type: {type(result)}")
                return []

        except Exception as e:
            logger.error(f"Failed to generate dynamic career roles: {e}")
            return []

    async def analyze_personalized_career_path(
        self,
        user_profile: Dict[str, Any],
        current_role: str,
        target_role: str,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> PersonalizedCareerPath:
        """Analyze personalized career path using AI.

        Args:
            user_profile: User profile data
            current_role: Current role
            target_role: Target role
            preferences: User preferences

        Returns:
            Personalized career path with AI insights
        """
        try:
            # Get market context
            industry = user_profile.get("industry", "technology")
            relevant_trends = self._get_relevant_trends(industry)

            # Build LLM prompt for personalized analysis
            prompt = self._build_personalized_path_prompt(
                user_profile=user_profile,
                current_role=current_role,
                target_role=target_role,
                preferences=preferences,
                market_trends=relevant_trends,
            )

            # Generate personalized path using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response
                path_data = await self._parse_llm_path_response(result)

                # Create personalized career path
                career_path = PersonalizedCareerPath(
                    user_profile=user_profile,
                    current_role=current_role,
                    target_role=target_role,
                    path_type=path_data.get("path_type", "transition"),
                    steps=path_data.get("steps", []),
                    skill_gaps=await self._generate_ai_skill_gaps(
                        current_role, target_role, user_profile.get("skills", [])
                    ),
                    market_opportunities=path_data.get("market_opportunities", []),
                    risk_factors=path_data.get("risk_factors", []),
                    estimated_timeline_months=path_data.get("timeline_months", 24),
                    potential_salary_increase_pct=path_data.get(
                        "salary_increase_pct", 0.2
                    ),
                    market_alignment_score=path_data.get("market_alignment", 0.5),
                    ai_confidence=0.8,
                    personalization_factors={
                        "industry": industry,
                        "experience_years": user_profile.get("experience_years", 0),
                        "skills_match": path_data.get("skills_match", 0.5),
                        "preferences_weight": len(preferences or {}),
                    },
                )

                return career_path
            else:
                logger.error(f"Unexpected LLM response type: {type(result)}")
                raise ValueError("Invalid LLM response")

        except Exception as e:
            logger.error(f"Failed to analyze personalized career path: {e}")
            raise

    async def identify_ai_skill_gaps(
        self,
        current_role: str,
        target_role: str,
        current_skills: List[str],
        industry: Optional[str] = None,
    ) -> List[SkillGap]:
        """Identify skill gaps using AI analysis.

        Args:
            current_role: Current role
            target_role: Target role
            current_skills: Current skills
            industry: Industry context

        Returns:
            List of AI-identified skill gaps
        """
        try:
            # Build LLM prompt for skill gap analysis
            prompt = self._build_skill_gap_prompt(
                current_role=current_role,
                target_role=target_role,
                current_skills=current_skills,
                industry=industry,
                emerging_skills=self._get_relevant_emerging_skills(industry),
            )

            # Generate skill gaps using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response into skill gaps
                skill_gaps = await self._parse_llm_skill_gaps_response(result)
                return skill_gaps
            else:
                logger.error(f"Unexpected LLM response type: {type(result)}")
                return []

        except Exception as e:
            logger.error(f"Failed to identify AI skill gaps: {e}")
            return []

    async def generate_market_aware_recommendations(
        self,
        user_profile: Dict[str, Any],
        career_goals: List[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate market-aware career recommendations.

        Args:
            user_profile: User profile data
            career_goals: Career goals and aspirations
            constraints: Constraints and limitations

        Returns:
            List of market-aware recommendations
        """
        try:
            industry = user_profile.get("industry", "technology")
            relevant_trends = self._get_relevant_trends(industry)

            # Build LLM prompt for recommendations
            prompt = self._build_recommendations_prompt(
                user_profile=user_profile,
                career_goals=career_goals,
                constraints=constraints,
                market_trends=relevant_trends,
            )

            # Generate recommendations using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response
                recommendations = await self._parse_llm_recommendations_response(result)
                return recommendations
            else:
                logger.error(f"Unexpected LLM response type: {type(result)}")
                return []

        except Exception as e:
            logger.error(f"Failed to generate market-aware recommendations: {e}")
            return []

    async def create_personalized_learning_path(
        self,
        skill_gaps: List[SkillGap],
        learning_style: Optional[str] = None,
        time_commitment: Optional[str] = None,
        budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create personalized learning path using AI.

        Args:
            skill_gaps: List of skill gaps to address
            learning_style: Preferred learning style
            time_commitment: Weekly time commitment
            budget: Learning budget

        Returns:
            Personalized learning path
        """
        try:
            # Build LLM prompt for learning path
            prompt = self._build_learning_path_prompt(
                skill_gaps=skill_gaps,
                learning_style=learning_style,
                time_commitment=time_commitment,
                budget=budget,
            )

            # Generate learning path using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response
                learning_path = await self._parse_llm_learning_path_response(result)
                return learning_path
            else:
                logger.error(f"Unexpected LLM response type: {type(result)}")
                return {}

        except Exception as e:
            logger.error(f"Failed to create personalized learning path: {e}")
            return {}

    def _build_role_generation_prompt(
        self,
        industry: str,
        experience_level: str,
        skills: List[str],
        preferences: Optional[Dict[str, Any]],
        market_trends: List[MarketTrend],
        emerging_skills: List[str],
    ) -> str:
        """Build LLM prompt for role generation."""

        trends_info = "\n".join(
            [
                f"- {trend.trend_name}: {trend.trend_type} trend, impact: {trend.impact_level}, "
                f"emerging skills: {', '.join(trend.emerging_skills[:3])}"
                for trend in market_trends[:5]
            ]
        )

        emerging_info = ", ".join(emerging_skills[:10])

        prompt = f"""
        Generate 5-7 realistic and modern career roles for the {industry} industry at {experience_level} level.
        
        User Context:
        - Industry: {industry}
        - Experience Level: {experience_level}
        - Current Skills: {", ".join(skills[:10])}
        - Preferences: {preferences or "None specified"}
        
        Market Trends:
        {trends_info}
        
        Emerging Skills in Industry:
        {emerging_info}
        
        For each role, provide:
        1. Role title (modern and realistic)
        2. Career level (entry, junior, mid, senior, management, staff, principal, director, vp, c_level)
        3. Career track (ic, management, hybrid, consultant, entrepreneur)
        4. Typical years experience range (min, max)
        5. Required skills (5-8 key skills)
        6. Salary range USD (realistic for current market)
        7. Growth outlook (excellent, strong, stable, declining)
        8. Market demand score (0.0-1.0)
        9. Trend alignment score (0.0-1.0)
        10. Emerging skills (3-5 future-facing skills)
        11. Industry focus areas (2-3 specific areas)
        12. Remote work potential (low, medium, high)
        
        Format as JSON array with objects containing all fields.
        Focus on roles that are in high demand and align with market trends.
        Ensure roles are realistic and reflect current job market conditions.
        """

        return prompt

    def _build_personalized_path_prompt(
        self,
        user_profile: Dict[str, Any],
        current_role: str,
        target_role: str,
        preferences: Optional[Dict[str, Any]],
        market_trends: List[MarketTrend],
    ) -> str:
        """Build LLM prompt for personalized career path."""

        user_info = f"""
        - Experience: {user_profile.get("experience_years", 0)} years
        - Education: {user_profile.get("education", "Not specified")}
        - Skills: {", ".join(user_profile.get("skills", [])[:10])}
        - Industry: {user_profile.get("industry", "Technology")}
        - Salary: {user_profile.get("current_salary", "Not specified")}
        - Location: {user_profile.get("location", "Not specified")}
        - Work Style: {user_profile.get("work_style", "Not specified")}
        """

        trends_info = "\n".join(
            [
                f"- {trend.trend_name}: {trend.impact_level} impact on career progression"
                for trend in market_trends[:3]
            ]
        )

        prompt = f"""
        Create a personalized career path from {current_role} to {target_role}.
        
        User Profile:
        {user_info}
        
        Preferences:
        {preferences or "None specified"}
        
        Market Trends Impact:
        {trends_info}
        
        Provide a detailed career path analysis including:
        1. Path type (promotion, transition, pivot, hybrid)
        2. Step-by-step progression plan (4-6 concrete steps)
        3. Skill gaps to address with priority levels
        4. Market opportunities to leverage
        5. Risk factors to consider
        6. Estimated timeline in months
        7. Potential salary increase percentage
        8. Market alignment score (0.0-1.0)
        9. Skills match score (0.0-1.0)
        
        Format as JSON object with all fields.
        Focus on practical, actionable steps that consider the user's background and current market conditions.
        """

        return prompt

    def _build_skill_gap_prompt(
        self,
        current_role: str,
        target_role: str,
        current_skills: List[str],
        industry: Optional[str],
        emerging_skills: List[str],
    ) -> str:
        """Build LLM prompt for skill gap analysis."""

        prompt = f"""
        Analyze skill gaps between {current_role} and {target_role} roles.
        
        Current Skills: {", ".join(current_skills[:15])}
        Industry: {industry or "Technology"}
        Emerging Skills: {", ".join(emerging_skills[:10])}
        
        Identify 5-8 critical skill gaps and for each provide:
        1. Skill name
        2. Importance level (critical, important, nice_to_have)
        3. Acquisition method (online_course, certification, on_the_job, mentorship, bootcamp, self_study)
        4. Estimated time to acquire (weeks)
        5. Recommended resources (2-3 specific resources)
        6. Priority level (high, medium, low)
        
        Format as JSON array of objects.
        Focus on skills that will make the transition successful and market-relevant.
        """

        return prompt

    def _build_recommendations_prompt(
        self,
        user_profile: Dict[str, Any],
        career_goals: List[str],
        constraints: Optional[Dict[str, Any]],
        market_trends: List[MarketTrend],
    ) -> str:
        """Build LLM prompt for career recommendations."""

        user_info = f"""
        - Experience: {user_profile.get("experience_years", 0)} years
        - Skills: {", ".join(user_profile.get("skills", [])[:10])}
        - Industry: {user_profile.get("industry", "Technology")}
        - Current Role: {user_profile.get("current_role", "Not specified")}
        """

        goals_info = "\n".join([f"- {goal}" for goal in career_goals[:5]])

        prompt = f"""
        Generate 3-5 personalized career recommendations based on user profile and goals.
        
        User Profile:
        {user_info}
        
        Career Goals:
        {goals_info}
        
        Constraints:
        {constraints or "None specified"}
        
        For each recommendation provide:
        1. Role/Path title
        2. Description of the opportunity
        3. Alignment with goals (0.0-1.0)
        4. Market demand score (0.0-1.0)
        5. Required actions (3-4 concrete steps)
        6. Timeline to achieve
        7. Potential outcomes
        8. Risk level (low, medium, high)
        
        Format as JSON array of objects.
        Focus on actionable recommendations that align with market trends and user goals.
        """

        return prompt

    def _build_learning_path_prompt(
        self,
        skill_gaps: List[SkillGap],
        learning_style: Optional[str],
        time_commitment: Optional[str],
        budget: Optional[int],
    ) -> str:
        """Build LLM prompt for learning path."""

        gaps_info = "\n".join(
            [
                f"- {gap.skill}: {gap.importance}, {gap.estimated_time_weeks} weeks"
                for gap in skill_gaps[:8]
            ]
        )

        prompt = f"""
        Create a personalized learning path to address skill gaps.
        
        Skill Gaps:
        {gaps_info}
        
        Learning Preferences:
        - Style: {learning_style or "Not specified"}
        - Time Commitment: {time_commitment or "Not specified"}
        - Budget: ${budget or "Not specified"}
        
        Provide a comprehensive learning plan including:
        1. Total timeline in weeks
        2. Learning phases (3-4 phases)
        3. Weekly schedule and milestones
        4. Recommended resources for each skill
        5. Assessment methods
        6. Success metrics
        7. Contingency plans
        
        Format as JSON object with all fields.
        Focus on practical, achievable learning that fits the user's preferences and constraints.
        """

        return prompt

    async def _parse_llm_roles_response(
        self,
        response: str,
        industry: str,
        experience_level: str,
    ) -> List[DynamicCareerRole]:
        """Parse LLM response into dynamic career roles."""
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON array found in LLM response")
                return []

            json_str = response[json_start:json_end]
            roles_data = json.loads(json_str)

            roles = []
            for role_data in roles_data:
                try:
                    # Convert to DynamicCareerRole
                    role = DynamicCareerRole(
                        title=role_data.get("title", ""),
                        level=CareerLevel(role_data.get("level", "mid")),
                        track=CareerTrack(role_data.get("track", "ic")),
                        typical_years_experience=tuple(
                            role_data.get("typical_years_experience", [0, 0])
                        ),
                        typical_skills=role_data.get("required_skills", []),
                        salary_range_usd=tuple(
                            role_data.get("salary_range_usd", [0, 0])
                        ),
                        growth_outlook=role_data.get("growth_outlook", "stable"),
                        market_demand=role_data.get("market_demand", 0.5),
                        trend_alignment=role_data.get("trend_alignment", 0.5),
                        ai_confidence=0.8,
                        emerging_skills=role_data.get("emerging_skills", []),
                        industry_focus=role_data.get("industry_focus", [industry]),
                        remote_work_potential=role_data.get(
                            "remote_work_potential", "medium"
                        ),
                    )
                    roles.append(role)
                except Exception as e:
                    logger.error(f"Failed to parse role data: {e}")
                    continue

            return roles

        except Exception as e:
            logger.error(f"Failed to parse LLM roles response: {e}")
            return []

    async def _parse_llm_path_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into career path data."""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON object found in LLM response")
                return {}

            json_str = response[json_start:json_end]
            path_data = json.loads(json_str)

            return path_data

        except Exception as e:
            logger.error(f"Failed to parse LLM path response: {e}")
            return {}

    async def _parse_llm_skill_gaps_response(self, response: str) -> List[SkillGap]:
        """Parse LLM response into skill gaps."""
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON array found in LLM response")
                return []

            json_str = response[json_start:json_end]
            gaps_data = json.loads(json_str)

            skill_gaps = []
            for gap_data in gaps_data:
                try:
                    gap = SkillGap(
                        skill=gap_data.get("skill", ""),
                        importance=gap_data.get("importance", "medium"),
                        acquisition_method=gap_data.get(
                            "acquisition_method", "self_study"
                        ),
                        estimated_time_weeks=gap_data.get(
                            "estimated_time_to_acquire", 4
                        ),
                        resources=gap_data.get("recommended_resources", []),
                    )
                    skill_gaps.append(gap)
                except Exception as e:
                    logger.error(f"Failed to parse skill gap data: {e}")
                    continue

            return skill_gaps

        except Exception as e:
            logger.error(f"Failed to parse LLM skill gaps response: {e}")
            return []

    async def _parse_llm_recommendations_response(
        self, response: str
    ) -> List[Dict[str, Any]]:
        """Parse LLM response into recommendations."""
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON array found in LLM response")
                return []

            json_str = response[json_start:json_end]
            recommendations = json.loads(json_str)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to parse LLM recommendations response: {e}")
            return []

    async def _parse_llm_learning_path_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into learning path."""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON object found in LLM response")
                return {}

            json_str = response[json_start:json_end]
            learning_path = json.loads(json_str)

            return learning_path

        except Exception as e:
            logger.error(f"Failed to parse LLM learning path response: {e}")
            return {}

    async def _enhance_role_with_market_data(
        self,
        role: DynamicCareerRole,
        industry: str,
    ) -> DynamicCareerRole:
        """Enhance role with real market data."""
        try:
            # Get relevant market trends
            relevant_trends = self._get_relevant_trends(industry)

            # Calculate trend alignment
            trend_alignment = 0.5
            for trend in relevant_trends:
                if any(skill in role.typical_skills for skill in trend.emerging_skills):
                    trend_alignment += 0.1

            # Update role with market insights
            role.trend_alignment = min(trend_alignment, 1.0)
            role.market_demand = self._calculate_market_demand(role, industry)

            return role

        except Exception as e:
            logger.error(f"Failed to enhance role with market data: {e}")
            return role

    async def _generate_ai_skill_gaps(
        self,
        current_role: str,
        target_role: str,
        current_skills: List[str],
    ) -> List[SkillGap]:
        """Generate AI-powered skill gaps."""
        try:
            # Use AI to identify skill gaps
            skill_gaps = await self.identify_ai_skill_gaps(
                current_role=current_role,
                target_role=target_role,
                current_skills=current_skills,
            )

            return skill_gaps

        except Exception as e:
            logger.error(f"Failed to generate AI skill gaps: {e}")
            return []

    def _get_relevant_trends(self, industry: str) -> List[MarketTrend]:
        """Get market trends relevant to industry."""
        industry_lower = industry.lower()
        relevant_trends = []

        for trend in self._market_trends:
            if (
                industry_lower in " ".join(trend.affected_roles).lower()
                or industry_lower in trend.trend_name.lower()
            ):
                relevant_trends.append(trend)

        return relevant_trends[:5]

    def _get_relevant_emerging_skills(self, industry: str) -> List[str]:
        """Get emerging skills relevant to industry."""
        industry_lower = industry.lower()
        relevant_skills = []

        for skill_data in self._emerging_skills:
            if industry_lower in skill_data.get("industries", []):
                relevant_skills.extend(skill_data.get("skills", []))

        return list(set(relevant_skills))[:15]

    def _calculate_market_demand(self, role: DynamicCareerRole, industry: str) -> float:
        """Calculate market demand score for role."""
        base_demand = 0.5

        # Adjust based on growth outlook
        outlook_multipliers = {
            "excellent": 0.3,
            "strong": 0.2,
            "stable": 0.0,
            "declining": -0.2,
        }

        demand = base_demand + outlook_multipliers.get(role.growth_outlook, 0.0)

        # Adjust based on emerging skills
        emerging_count = len(role.emerging_skills)
        demand += min(emerging_count * 0.05, 0.2)

        return max(0.0, min(demand, 1.0))

    def _initialize_market_trends(self) -> List[MarketTrend]:
        """Initialize market trend data."""
        return [
            MarketTrend(
                trend_name="AI and Machine Learning Integration",
                trend_type="growth",
                impact_level="high",
                affected_roles=[
                    "software_engineer",
                    "data_scientist",
                    "product_manager",
                ],
                emerging_skills=["machine_learning", "prompt_engineering", "ai_ethics"],
                declining_skills=["manual_testing", "basic_data_entry"],
                market_demand=0.9,
                salary_impact=0.15,
                confidence_score=0.8,
            ),
            MarketTrend(
                trend_name="Remote Work Optimization",
                trend_type="growth",
                impact_level="medium",
                affected_roles=["software_engineer", "ux_designer", "product_manager"],
                emerging_skills=[
                    "remote_collaboration",
                    "async_communication",
                    "digital_tools",
                ],
                declining_skills=["in_person_only", "office_management"],
                market_demand=0.7,
                salary_impact=0.05,
                confidence_score=0.7,
            ),
            MarketTrend(
                trend_name="Cloud Native Architecture",
                trend_type="growth",
                impact_level="high",
                affected_roles=["software_engineer", "devops_engineer", "sre"],
                emerging_skills=["kubernetes", "serverless", "microservices"],
                declining_skills=["monolithic_architecture", "on_premise"],
                market_demand=0.8,
                salary_impact=0.12,
                confidence_score=0.8,
            ),
        ]

    def _initialize_industry_patterns(self) -> Dict[str, Any]:
        """Initialize industry-specific patterns."""
        return {
            "technology": {
                "growth_rate": 0.15,
                "emerging_areas": ["ai", "cloud", "cybersecurity", "blockchain"],
                "declining_areas": ["legacy_systems", "manual_testing"],
                "key_skills": ["programming", "system_design", "cloud_computing"],
            },
            "healthcare": {
                "growth_rate": 0.12,
                "emerging_areas": ["telemedicine", "health_tech", "ai_diagnostics"],
                "declining_areas": ["paper_records", "administrative_overhead"],
                "key_skills": ["medical_knowledge", "empathy", "technology_adoption"],
            },
            "finance": {
                "growth_rate": 0.08,
                "emerging_areas": ["fintech", "blockchain", "quantitative_finance"],
                "declining_areas": ["traditional_banking", "manual_trading"],
                "key_skills": ["financial_analysis", "risk_management", "technology"],
            },
        }

    def _initialize_emerging_skills(self) -> List[Dict[str, Any]]:
        """Initialize emerging skills database."""
        return [
            {
                "skills": [
                    "machine_learning",
                    "deep_learning",
                    "nlp",
                    "computer_vision",
                ],
                "industries": ["technology", "healthcare", "finance"],
                "growth_rate": 0.25,
                "timeline_months": 12,
            },
            {
                "skills": ["cloud_computing", "kubernetes", "serverless", "devops"],
                "industries": ["technology", "finance", "healthcare"],
                "growth_rate": 0.20,
                "timeline_months": 8,
            },
            {
                "skills": ["cybersecurity", "security_engineering", "compliance"],
                "industries": ["technology", "finance", "healthcare", "government"],
                "growth_rate": 0.18,
                "timeline_months": 10,
            },
            {
                "skills": ["data_science", "analytics", "business_intelligence"],
                "industries": ["technology", "finance", "healthcare", "retail"],
                "growth_rate": 0.15,
                "timeline_months": 6,
            },
        ]

    def _initialize_role_templates(self) -> Dict[str, Any]:
        """Initialize role generation templates."""
        return {
            "technical_roles": {
                "prefixes": ["Senior", "Lead", "Principal", "Staff"],
                "core_skills": ["programming", "system_design", "problem_solving"],
                "emerging_modifiers": ["AI", "Cloud", "Security", "Data"],
            },
            "management_roles": {
                "prefixes": ["Engineering", "Technical", "Product"],
                "core_skills": ["leadership", "communication", "strategy"],
                "emerging_modifiers": ["Digital", "Remote", "Agile"],
            },
            "product_roles": {
                "prefixes": ["Senior", "Lead", "Principal"],
                "core_skills": ["user_research", "analytics", "strategy"],
                "emerging_modifiers": ["AI", "Data", "Growth"],
            },
        }


_llm_career_path_analyzer: Optional[LLMCareerPathAnalyzer] = None


def get_llm_career_path_analyzer() -> LLMCareerPathAnalyzer:
    """Get or create the singleton LLM career path analyzer."""
    global _llm_career_path_analyzer
    if _llm_career_path_analyzer is None:
        _llm_career_path_analyzer = LLMCareerPathAnalyzer()
    return _llm_career_path_analyzer
