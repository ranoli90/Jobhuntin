"""
Multi-resume support system for targeted job applications.

Provides:
  - Manage multiple resume versions for different job types
  - Resume versioning and comparison
  - Targeted resume recommendations
  - Resume performance tracking and analytics
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel

from shared.logging_config import get_logger

logger = get_logger("sorce.multi_resume")

# Resume types
RESUME_TYPES = [
    "general",
    "technical",
    "management",
    "executive",
    "creative",
    "academic",
    "entry_level",
    "career_change",
]


class ResumeVersion(BaseModel):
    """Resume version with metadata."""

    id: str
    user_id: str
    tenant_id: str
    name: str
    resume_type: str
    description: Optional[str] = None
    file_path: str
    file_size: int
    file_format: str  # pdf, docx, etc.
    is_primary: bool = False
    is_active: bool = True
    target_industries: List[str] = []
    target_roles: List[str] = []
    skills_emphasized: List[str] = []
    ats_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    success_rate: float = 0.0


class ResumeComparison(BaseModel):
    """Comparison between two resume versions."""

    version1_id: str
    version2_id: str
    similarities: List[str] = []
    differences: List[str] = []
    ats_score_diff: float = 0.0
    recommendation: str = ""


class ResumeAnalytics(BaseModel):
    """Resume performance analytics."""

    resume_id: str
    total_applications: int
    interview_rate: float
    offer_rate: float
    average_response_time: float  # days
    success_by_industry: Dict[str, float] = {}
    success_by_role: str = ""
    feedback_summary: List[str] = []


class MultiResumeManager:
    """Manages multiple resume versions and analytics."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def create_resume_version(
        self,
        tenant_id: str,
        user_id: str,
        name: str,
        resume_type: str,
        file_path: str,
        file_size: int,
        file_format: str,
        description: Optional[str] = None,
        target_industries: List[str] = None,
        target_roles: List[str] = None,
        skills_emphasized: List[str] = None,
        is_primary: bool = False,
    ) -> ResumeVersion:
        """Create a new resume version."""

        resume_id = str(uuid.uuid4())

        async with self.db_pool.acquire() as conn:
            # If setting as primary, unset other primary resumes
            if is_primary:
                await conn.execute(
                    """
                    UPDATE resume_versions 
                    SET is_primary = false, updated_at = NOW()
                    WHERE user_id = $1 AND tenant_id = $2
                    """,
                    user_id,
                    tenant_id,
                )

            await conn.execute(
                """
                INSERT INTO resume_versions (
                    id, user_id, tenant_id, name, resume_type, description,
                    file_path, file_size, file_format, is_primary, is_active,
                    target_industries, target_roles, skills_emphasized,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), NOW())
                """,
                resume_id,
                user_id,
                tenant_id,
                name,
                resume_type,
                description,
                file_path,
                file_size,
                file_format,
                is_primary,
                True,
                target_industries or [],
                target_roles or [],
                skills_emphasized or [],
            )

            resume = ResumeVersion(
                id=resume_id,
                user_id=user_id,
                tenant_id=tenant_id,
                name=name,
                resume_type=resume_type,
                description=description,
                file_path=file_path,
                file_size=file_size,
                file_format=file_format,
                is_primary=is_primary,
                is_active=True,
                target_industries=target_industries or [],
                target_roles=target_roles or [],
                skills_emphasized=skills_emphasized or [],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            logger.info(
                "Created resume version %s for user %s",
                resume_id,
                user_id,
            )

            return resume

    async def get_user_resumes(
        self,
        tenant_id: str,
        user_id: str,
        resume_type: Optional[str] = None,
        is_active: bool = True,
    ) -> List[ResumeVersion]:
        """Get user's resume versions."""

        async with self.db_pool.acquire() as conn:
            query = """
            SELECT * FROM resume_versions
            WHERE user_id = $1 AND tenant_id = $2 AND is_active = $3
            """
            params = [user_id, tenant_id, is_active]

            if resume_type:
                query += " AND resume_type = $4"
                params.append(resume_type)

            query += " ORDER BY is_primary DESC, updated_at DESC"

            rows = await conn.fetch(query, *params)

            resumes = []
            for row in rows:
                resume = ResumeVersion(
                    id=row["id"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    name=row["name"],
                    resume_type=row["resume_type"],
                    description=row.get("description"),
                    file_path=row["file_path"],
                    file_size=row["file_size"],
                    file_format=row["file_format"],
                    is_primary=row["is_primary"],
                    is_active=row["is_active"],
                    target_industries=row.get("target_industries", []),
                    target_roles=row.get("target_roles", []),
                    skills_emphasized=row.get("skills_emphasized", []),
                    ats_score=row.get("ats_score"),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    usage_count=row.get("usage_count", 0),
                    success_rate=row.get("success_rate", 0.0),
                )
                resumes.append(resume)

            return resumes

    async def recommend_resume_for_job(
        self,
        tenant_id: str,
        user_id: str,
        job_title: str,
        company_industry: str,
        job_description: str = "",
        required_skills: List[str] = None,
    ) -> Optional[ResumeVersion]:
        """Recommend the best resume for a specific job."""

        user_resumes = await self.get_user_resumes(tenant_id, user_id)

        if not user_resumes:
            return None

        # Score each resume for this job
        scored_resumes = []

        for resume in user_resumes:
            score = await self._calculate_resume_score(
                resume,
                job_title,
                company_industry,
                job_description,
                required_skills or [],
            )
            scored_resumes.append((resume, score))

        # Sort by score and return the best
        scored_resumes.sort(key=lambda x: x[1], reverse=True)

        if scored_resumes:
            best_resume, score = scored_resumes[0]
            logger.info(
                "Recommended resume %s for job %s (score: %.2f)",
                best_resume.id,
                job_title,
                score,
            )
            return best_resume

        return None

    async def compare_resumes(
        self,
        tenant_id: str,
        user_id: str,
        resume1_id: str,
        resume2_id: str,
    ) -> Optional[ResumeComparison]:
        """Compare two resume versions."""

        user_resumes = await self.get_user_resumes(tenant_id, user_id)

        resume1 = next((r for r in user_resumes if r.id == resume1_id), None)
        resume2 = next((r for r in user_resumes if r.id == resume2_id), None)

        if not resume1 or not resume2:
            return None

        # Analyze similarities and differences
        similarities = []
        differences = []

        # Compare types
        if resume1.resume_type == resume2.resume_type:
            similarities.append(f"Both are {resume1.resume_type} resumes")
        else:
            differences.append(
                f"Different types: {resume1.resume_type} vs {resume2.resume_type}"
            )

        # Compare target industries
        common_industries = set(resume1.target_industries) & set(
            resume2.target_industries
        )
        if common_industries:
            similarities.append(f"Target industries: {', '.join(common_industries)}")

        unique_industries1 = set(resume1.target_industries) - set(
            resume2.target_industries
        )
        unique_industries2 = set(resume2.target_industries) - set(
            resume1.target_industries
        )

        if unique_industries1:
            differences.append(f"Resume 1 targets: {', '.join(unique_industries1)}")
        if unique_industries2:
            differences.append(f"Resume 2 targets: {', '.join(unique_industries2)}")

        # Compare skills
        common_skills = set(resume1.skills_emphasized) & set(resume2.skills_emphasized)
        if common_skills:
            similarities.append(f"Common skills: {', '.join(common_skills)}")

        # ATS score difference
        ats_diff = (resume1.ats_score or 0) - (resume2.ats_score or 0)

        # Generate recommendation
        recommendation = self._generate_comparison_recommendation(
            resume1, resume2, ats_diff
        )

        return ResumeComparison(
            version1_id=resume1_id,
            version2_id=resume2_id,
            similarities=similarities,
            differences=differences,
            ats_score_diff=ats_diff,
            recommendation=recommendation,
        )

    async def update_resume_analytics(
        self,
        tenant_id: str,
        user_id: str,
        resume_id: str,
    ) -> ResumeAnalytics:
        """Update and return analytics for a resume."""

        async with self.db_pool.acquire() as conn:
            # Get application data for this resume
            app_data = await conn.fetch(
                """
                SELECT 
                    a.status,
                    a.created_at,
                    a.last_activity,
                    j.title as job_title,
                    c.industry as company_industry
                FROM applications a
                LEFT JOIN jobs j ON a.job_id = j.id
                LEFT JOIN companies c ON j.company_id = c.id
                WHERE a.user_id = $1 AND a.tenant_id = $2 AND a.resume_id = $3
                ORDER BY a.created_at DESC
                """,
                user_id,
                tenant_id,
                resume_id,
            )

            if not app_data:
                return ResumeAnalytics(
                    resume_id=resume_id,
                    total_applications=0,
                    interview_rate=0.0,
                    offer_rate=0.0,
                    average_response_time=0.0,
                )

            total_apps = len(app_data)

            # Calculate interview rate (SUCCESS status)
            interviews = sum(1 for row in app_data if row["status"] == "SUCCESS")
            interview_rate = interviews / total_apps if total_apps > 0 else 0.0

            # Calculate offer rate (simplified - would need offer tracking)
            offer_rate = interview_rate * 0.3  # Placeholder

            # Calculate average response time
            response_times = []
            for row in app_data:
                if row["last_activity"] and row["created_at"]:
                    response_time = (row["last_activity"] - row["created_at"]).days
                    response_times.append(response_time)

            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0.0
            )

            # Success by industry
            industry_success = {}
            for row in app_data:
                industry = row.get("company_industry", "Unknown")
                if industry not in industry_success:
                    industry_success[industry] = {"total": 0, "interviews": 0}

                industry_success[industry]["total"] += 1
                if row["status"] == "SUCCESS":
                    industry_success[industry]["interviews"] += 1

            success_by_industry = {}
            for industry, data in industry_success.items():
                rate = data["interviews"] / data["total"] if data["total"] > 0 else 0.0
                success_by_industry[industry] = rate

            # Update resume with new analytics
            await conn.execute(
                """
                UPDATE resume_versions
                SET usage_count = $1, success_rate = $2, updated_at = NOW()
                WHERE id = $3
                """,
                total_apps,
                interview_rate,
                resume_id,
            )

            return ResumeAnalytics(
                resume_id=resume_id,
                total_applications=total_apps,
                interview_rate=interview_rate,
                offer_rate=offer_rate,
                average_response_time=avg_response_time,
                success_by_industry=success_by_industry,
                feedback_summary=[],  # Would need feedback tracking
            )

    async def set_primary_resume(
        self,
        tenant_id: str,
        user_id: str,
        resume_id: str,
    ) -> bool:
        """Set a resume as the primary resume."""

        async with self.db_pool.acquire() as conn:
            # Unset all primary resumes
            await conn.execute(
                """
                UPDATE resume_versions
                SET is_primary = false, updated_at = NOW()
                WHERE user_id = $1 AND tenant_id = $2
                """,
                user_id,
                tenant_id,
            )

            # Set new primary
            result = await conn.execute(
                """
                UPDATE resume_versions
                SET is_primary = true, updated_at = NOW()
                WHERE id = $1 AND user_id = $2 AND tenant_id = $3
                """,
                resume_id,
                user_id,
                tenant_id,
            )

            return result == "UPDATE 1"

    async def delete_resume_version(
        self,
        tenant_id: str,
        user_id: str,
        resume_id: str,
    ) -> bool:
        """Soft delete a resume version."""

        async with self.db_pool.acquire() as conn:
            # Check if it's primary
            resume_data = await conn.fetchrow(
                """
                SELECT is_primary FROM resume_versions
                WHERE id = $1 AND user_id = $2 AND tenant_id = $3
                """,
                resume_id,
                user_id,
                tenant_id,
            )

            if not resume_data:
                return False

            # Don't allow deletion of primary resume
            if resume_data["is_primary"]:
                return False

            # Soft delete
            result = await conn.execute(
                """
                UPDATE resume_versions
                SET is_active = false, updated_at = NOW()
                WHERE id = $1 AND user_id = $2 AND tenant_id = $3
                """,
                resume_id,
                user_id,
                tenant_id,
            )

            return result == "UPDATE 1"

    async def _calculate_resume_score(
        self,
        resume: ResumeVersion,
        job_title: str,
        company_industry: str,
        job_description: str,
        required_skills: List[str],
    ) -> float:
        """Calculate relevance score for resume vs job."""

        score = 0.0

        # Resume type matching
        job_title_lower = job_title.lower()

        if resume.resume_type == "general":
            score += 0.3
        elif "manager" in job_title_lower and resume.resume_type == "management":
            score += 0.8
        elif (
            "director" in job_title_lower
            or "vp" in job_title_lower
            and resume.resume_type == "executive"
        ):
            score += 0.8
        elif (
            "engineer" in job_title_lower
            or "developer" in job_title_lower
            and resume.resume_type == "technical"
        ):
            score += 0.8
        elif (
            "designer" in job_title_lower
            or "creative" in job_title_lower
            and resume.resume_type == "creative"
        ):
            score += 0.8

        # Industry matching
        if company_industry.lower() in [
            ind.lower() for ind in resume.target_industries
        ]:
            score += 0.3

        # Role matching
        if any(role.lower() in job_title_lower for role in resume.target_roles):
            score += 0.3

        # Skills matching
        if required_skills:
            matching_skills = set(resume.skills_emphasized) & set(required_skills)
            skill_match_rate = len(matching_skills) / len(required_skills)
            score += skill_match_rate * 0.4

        # ATS score bonus
        if resume.ats_score:
            score += resume.ats_score * 0.2

        # Success rate bonus
        if resume.success_rate > 0:
            score += resume.success_rate * 0.1

        return min(score, 1.0)

    def _generate_comparison_recommendation(
        self,
        resume1: ResumeVersion,
        resume2: ResumeVersion,
        ats_diff: float,
    ) -> str:
        """Generate recommendation based on resume comparison."""

        recommendations = []

        # ATS score recommendation
        if abs(ats_diff) > 0.1:
            if ats_diff > 0:
                recommendations.append(
                    f"Resume 1 has a better ATS score (+{ats_diff:.2f})"
                )
            else:
                recommendations.append(
                    f"Resume 2 has a better ATS score (+{abs(ats_diff):.2f})"
                )

        # Success rate recommendation
        if resume1.success_rate > resume2.success_rate + 0.1:
            recommendations.append(
                f"Resume 1 has a higher success rate ({resume1.success_rate:.1%} vs {resume2.success_rate:.1%})"
            )
        elif resume2.success_rate > resume1.success_rate + 0.1:
            recommendations.append(
                f"Resume 2 has a higher success rate ({resume2.success_rate:.1%} vs {resume1.success_rate:.1%})"
            )

        # Usage recommendation
        if resume1.usage_count > resume2.usage_count * 2:
            recommendations.append(
                "Resume 1 is more proven (used in more applications)"
            )
        elif resume2.usage_count > resume1.usage_count * 2:
            recommendations.append(
                "Resume 2 is more proven (used in more applications)"
            )

        # Primary status
        if resume1.is_primary:
            recommendations.append("Resume 1 is currently set as primary")
        elif resume2.is_primary:
            recommendations.append("Resume 2 is currently set as primary")

        if not recommendations:
            return "Both resumes have similar performance. Choose based on specific job requirements."

        return " | ".join(recommendations)


# Factory function
def create_multi_resume_manager(db_pool) -> MultiResumeManager:
    """Create multi-resume manager instance."""
    return MultiResumeManager(db_pool)
