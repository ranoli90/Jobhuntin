"""
Cold start handling for new users.

Provides:
- Default preferences based on user profile
- Initial job recommendations using popularity
- Onboarding questionnaire analysis
- Progressive profile enrichment
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OnboardingProfile:
    """Profile data collected during onboarding."""
    job_titles: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    experience_years: Optional[int] = None
    salary_expectation: Optional[int] = None
    job_types: list[str] = field(default_factory=list)  # full-time, part-time, contract, remote
    industries: list[str] = field(default_factory=list)
    willing_to_relocate: bool = False
    remote_preference: str = "hybrid"  # remote, hybrid, onsite


@dataclass
class ColdStartRecommendation:
    """A recommendation for a new user."""
    job_id: str
    title: str
    company: str
    location: str
    match_score: float
    reason: str
    source: str  # popularity, trending, similar_users, profile_match


class ColdStartHandler:
    """
    Handles cold start problem for new users.
    
    Strategies:
    1. Popularity-based: Recommend popular jobs in user's area
    2. Trending: Recommend trending jobs in user's industry
    3. Similar users: Recommend jobs liked by similar profiles
    4. Profile match: Match based on onboarding questionnaire
    """

    def __init__(
        self,
        db_conn: "asyncpg.Connection",
        min_recommendations: int = 20,
        max_recommendations: int = 50,
    ):
        self.db = db_conn
        self.min_recommendations = min_recommendations
        self.max_recommendations = max_recommendations

    async def get_initial_recommendations(
        self,
        user_id: str,
        onboarding: OnboardingProfile,
    ) -> list[ColdStartRecommendation]:
        """
        Get initial job recommendations for a new user.
        
        Combines multiple strategies to provide diverse recommendations.
        """
        recommendations: list[ColdStartRecommendation] = []
        seen_job_ids: set[str] = set()

        # Strategy 1: Profile-based matching
        profile_matches = await self._get_profile_matches(onboarding)
        for match in profile_matches:
            if match.job_id not in seen_job_ids:
                recommendations.append(match)
                seen_job_ids.add(match.job_id)

        # Strategy 2: Popular jobs in user's locations
        if len(recommendations) < self.min_recommendations:
            popular = await self._get_popular_jobs(onboarding.locations)
            for job in popular:
                if job.job_id not in seen_job_ids:
                    recommendations.append(job)
                    seen_job_ids.add(job.job_id)

        # Strategy 3: Trending jobs in user's industry
        if len(recommendations) < self.min_recommendations:
            trending = await self._get_trending_jobs(onboarding.industries)
            for job in trending:
                if job.job_id not in seen_job_ids:
                    recommendations.append(job)
                    seen_job_ids.add(job.job_id)

        # Strategy 4: Similar user recommendations
        if len(recommendations) < self.min_recommendations:
            similar = await self._get_similar_user_jobs(onboarding)
            for job in similar:
                if job.job_id not in seen_job_ids:
                    recommendations.append(job)
                    seen_job_ids.add(job.job_id)

        # Strategy 5: Fallback to general popular jobs
        if len(recommendations) < self.min_recommendations:
            general = await self._get_general_popular()
            for job in general:
                if job.job_id not in seen_job_ids:
                    recommendations.append(job)
                    seen_job_ids.add(job.job_id)

        # Sort by match score and limit
        recommendations.sort(key=lambda r: r.match_score, reverse=True)
        return recommendations[:self.max_recommendations]

    async def _get_profile_matches(
        self,
        onboarding: OnboardingProfile,
    ) -> list[ColdStartRecommendation]:
        """Get jobs matching the onboarding profile."""
        matches: list[ColdStartRecommendation] = []

        try:
            # Build query based on profile
            conditions = []
            params = []
            param_idx = 1

            # Match by job titles
            if onboarding.job_titles:
                conditions.append(f"""
                    j.title ILIKE ANY(${param_idx})
                """)
                params.append([f"%{title}%" for title in onboarding.job_titles])
                param_idx += 1

            # Match by skills
            if onboarding.skills:
                conditions.append(f"""
                    j.description ILIKE ANY(${param_idx})
                    OR EXISTS (
                        SELECT 1 FROM unnest(j.required_skills) skill
                        WHERE skill ILIKE ANY(${param_idx})
                    )
                """)
                params.append([f"%{skill}%" for skill in onboarding.skills])
                param_idx += 1

            # Match by locations
            if onboarding.locations:
                conditions.append(f"""
                    j.location ILIKE ANY(${param_idx})
                """)
                params.append([f"%{loc}%" for loc in onboarding.locations])
                param_idx += 1

            # Match by job types
            if onboarding.job_types:
                conditions.append(f"""
                    j.job_type = ANY(${param_idx})
                """)
                params.append(onboarding.job_types)
                param_idx += 1

            if not conditions:
                return matches

            query = f"""
                SELECT
                    j.id, j.title, j.company, j.location,
                    j.required_skills, j.description
                FROM public.jobs j
                WHERE j.status = 'ACTIVE'
                AND ({" OR ".join(conditions)})
                ORDER BY j.created_at DESC
                LIMIT 30
            """

            rows = await self.db.fetch(query, *params)

            for row in rows:
                # Calculate match score based on profile overlap
                score = self._calculate_profile_match_score(row, onboarding)

                matches.append(ColdStartRecommendation(
                    job_id=str(row["id"]),
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    match_score=score,
                    reason="Matches your profile preferences",
                    source="profile_match",
                ))

        except Exception as e:
            logger.error(f"Error getting profile matches: {e}")

        return matches

    async def _get_popular_jobs(
        self,
        locations: list[str],
    ) -> list[ColdStartRecommendation]:
        """Get popular jobs based on application count."""
        matches: list[ColdStartRecommendation] = []

        try:
            query = """
                SELECT
                    j.id, j.title, j.company, j.location,
                    COUNT(a.id) AS application_count
                FROM public.jobs j
                LEFT JOIN public.applications a ON a.job_id = j.id
                WHERE j.status = 'ACTIVE'
                AND ($1::text[] IS NULL OR array_length($1, 1) IS NULL
                    OR j.location ILIKE ANY($1))
                GROUP BY j.id
                ORDER BY application_count DESC, j.created_at DESC
                LIMIT 20
            """

            location_patterns = [f"%{loc}%" for loc in locations] if locations else None
            rows = await self.db.fetch(query, location_patterns)

            max_count = max((r["application_count"] or 0 for r in rows), default=1)

            for row in rows:
                # Normalize score by popularity
                score = min((row["application_count"] or 0) / max_count, 1.0) * 0.8

                matches.append(ColdStartRecommendation(
                    job_id=str(row["id"]),
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    match_score=score,
                    reason="Popular job in your area",
                    source="popularity",
                ))

        except Exception as e:
            logger.error(f"Error getting popular jobs: {e}")

        return matches

    async def _get_trending_jobs(
        self,
        industries: list[str],
    ) -> list[ColdStartRecommendation]:
        """Get trending jobs based on recent activity."""
        matches: list[ColdStartRecommendation] = []

        try:
            query = """
                SELECT
                    j.id, j.title, j.company, j.location,
                    COUNT(a.id) FILTER (WHERE a.created_at > now() - interval '7 days') AS recent_apps
                FROM public.jobs j
                LEFT JOIN public.applications a ON a.job_id = j.id
                WHERE j.status = 'ACTIVE'
                AND ($1::text[] IS NULL OR array_length($1, 1) IS NULL
                    OR j.industry ILIKE ANY($1))
                GROUP BY j.id
                HAVING COUNT(a.id) FILTER (WHERE a.created_at > now() - interval '7 days') > 0
                ORDER BY recent_apps DESC
                LIMIT 15
            """

            industry_patterns = [f"%{ind}%" for ind in industries] if industries else None
            rows = await self.db.fetch(query, industry_patterns)

            max_recent = max((r["recent_apps"] or 0 for r in rows), default=1)

            for row in rows:
                score = min((row["recent_apps"] or 0) / max_recent, 1.0) * 0.75

                matches.append(ColdStartRecommendation(
                    job_id=str(row["id"]),
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    match_score=score,
                    reason="Trending job in your industry",
                    source="trending",
                ))

        except Exception as e:
            logger.error(f"Error getting trending jobs: {e}")

        return matches

    async def _get_similar_user_jobs(
        self,
        onboarding: OnboardingProfile,
    ) -> list[ColdStartRecommendation]:
        """Get jobs that similar users have applied to."""
        matches: list[ColdStartRecommendation] = []

        try:
            # Find users with similar profiles
            query = """
                WITH similar_users AS (
                    SELECT DISTINCT p.user_id
                    FROM public.profiles p
                    WHERE p.skills && $1::text[]
                    OR p.desired_titles && $2::text[]
                    LIMIT 100
                ),
                similar_applications AS (
                    SELECT
                        a.job_id,
                        COUNT(*) AS similar_user_count
                    FROM public.applications a
                    JOIN similar_users su ON su.user_id = a.user_id
                    GROUP BY a.job_id
                    ORDER BY similar_user_count DESC
                    LIMIT 20
                )
                SELECT
                    j.id, j.title, j.company, j.location,
                    sa.similar_user_count
                FROM similar_applications sa
                JOIN public.jobs j ON j.id = sa.job_id
                WHERE j.status = 'ACTIVE'
            """

            rows = await self.db.fetch(
                query,
                onboarding.skills,
                onboarding.job_titles,
            )

            max_count = max((r["similar_user_count"] or 0 for r in rows), default=1)

            for row in rows:
                score = min((row["similar_user_count"] or 0) / max_count, 1.0) * 0.7

                matches.append(ColdStartRecommendation(
                    job_id=str(row["id"]),
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    match_score=score,
                    reason="Users with similar profiles applied",
                    source="similar_users",
                ))

        except Exception as e:
            logger.error(f"Error getting similar user jobs: {e}")

        return matches

    async def _get_general_popular(self) -> list[ColdStartRecommendation]:
        """Get generally popular jobs as fallback."""
        matches: list[ColdStartRecommendation] = []

        try:
            query = """
                SELECT
                    j.id, j.title, j.company, j.location,
                    COUNT(a.id) AS application_count
                FROM public.jobs j
                LEFT JOIN public.applications a ON a.job_id = j.id
                WHERE j.status = 'ACTIVE'
                AND j.created_at > now() - interval '30 days'
                GROUP BY j.id
                ORDER BY application_count DESC, j.created_at DESC
                LIMIT 15
            """

            rows = await self.db.fetch(query)

            max_count = max((r["application_count"] or 0 for r in rows), default=1)

            for row in rows:
                score = min((row["application_count"] or 0) / max_count, 1.0) * 0.6

                matches.append(ColdStartRecommendation(
                    job_id=str(row["id"]),
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    match_score=score,
                    reason="Popular recent job",
                    source="popularity",
                ))

        except Exception as e:
            logger.error(f"Error getting general popular jobs: {e}")

        return matches

    def _calculate_profile_match_score(
        self,
        job_row: dict,
        onboarding: OnboardingProfile,
    ) -> float:
        """Calculate match score between job and profile."""
        score = 0.0
        max_score = 0.0

        # Title match (weight: 30%)
        max_score += 0.3
        if onboarding.job_titles:
            title = (job_row.get("title") or "").lower()
            if any(t.lower() in title for t in onboarding.job_titles):
                score += 0.3

        # Skills match (weight: 25%)
        max_score += 0.25
        if onboarding.skills:
            job_skills = job_row.get("required_skills") or []
            description = (job_row.get("description") or "").lower()

            matched_skills = sum(
                1 for skill in onboarding.skills
                if skill.lower() in description or
                   any(skill.lower() in (s or "").lower() for s in job_skills)
            )
            skill_score = matched_skills / max(len(onboarding.skills), 1)
            score += 0.25 * skill_score

        # Location match (weight: 25%)
        max_score += 0.25
        if onboarding.locations:
            location = (job_row.get("location") or "").lower()
            if any(loc.lower() in location for loc in onboarding.locations):
                score += 0.25

        # Experience match (weight: 10%)
        max_score += 0.1
        if onboarding.experience_years is not None:
            # Assume job requires some experience based on title
            title = (job_row.get("title") or "").lower()
            if "senior" in title or "lead" in title:
                if onboarding.experience_years >= 5:
                    score += 0.1
            elif "junior" in title or "entry" in title:
                if onboarding.experience_years <= 3:
                    score += 0.1
            else:
                score += 0.05  # Partial credit for mid-level

        # Remote preference (weight: 10%)
        max_score += 0.1
        location = (job_row.get("location") or "").lower()
        if onboarding.remote_preference == "remote" and "remote" in location:
            score += 0.1
        elif onboarding.remote_preference == "onsite" and "remote" not in location:
            score += 0.1
        elif onboarding.remote_preference == "hybrid":
            score += 0.05

        return score / max_score if max_score > 0 else 0.5


async def get_cold_start_recommendations(
    db_conn: "asyncpg.Connection",
    user_id: str,
    onboarding: OnboardingProfile,
) -> list[ColdStartRecommendation]:
    """Convenience function to get cold start recommendations."""
    handler = ColdStartHandler(db_conn)
    return await handler.get_initial_recommendations(user_id, onboarding)
