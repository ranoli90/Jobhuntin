"""
Match feedback service for collecting and processing user feedback on match results.

Implements the feedback loop for ML improvement:
- Thumbs up/down on match results
- Feedback tags for categorical analysis
- Score adjustment based on historical feedback
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg
from pydantic import BaseModel, Field
from shared.logging_config import get_logger

logger = get_logger("sorce.match_feedback")


class MatchFeedbackCreate(BaseModel):
    """Request to submit match feedback."""

    job_id: str
    rating: int = Field(..., ge=-1, le=1, description="1 = thumbs up, -1 = thumbs down")
    match_score: float = Field(..., ge=0.0, le=1.0)
    semantic_similarity: float | None = None
    skill_match_ratio: float | None = None
    feedback_text: str | None = None
    feedback_tags: list[str] = Field(default_factory=list)
    match_type: str = "semantic"
    job_title: str | None = None
    company: str | None = None


class MatchFeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    id: str
    job_id: str
    rating: int
    created_at: datetime


class MatchFeedbackStats(BaseModel):
    """Aggregate feedback statistics for a job."""

    job_id: str
    total_feedback: int
    thumbs_up: int
    thumbs_down: int
    avg_match_score: float
    avg_score_positive: float | None
    avg_score_negative: float | None
    common_tags: list[str] = Field(default_factory=list)


class MatchFeedbackRepo:
    """Repository for match feedback operations."""

    @staticmethod
    async def submit(
        conn: asyncpg.Connection,
        user_id: str,
        tenant_id: str | None,
        feedback: MatchFeedbackCreate,
    ) -> MatchFeedbackResponse:
        """Submit match feedback, upserting if already exists."""
        row = await conn.fetchrow(
            """
            INSERT INTO public.match_feedback (
                user_id, job_id, tenant_id, rating, match_score,
                semantic_similarity, skill_match_ratio,
                feedback_text, feedback_tags, match_type,
                job_title, company
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (user_id, job_id) DO UPDATE SET
                rating = EXCLUDED.rating,
                match_score = EXCLUDED.match_score,
                semantic_similarity = EXCLUDED.semantic_similarity,
                skill_match_ratio = EXCLUDED.skill_match_ratio,
                feedback_text = EXCLUDED.feedback_text,
                feedback_tags = EXCLUDED.feedback_tags,
                created_at = now()
            RETURNING id, job_id, rating, created_at
            """,
            user_id,
            feedback.job_id,
            tenant_id,
            feedback.rating,
            feedback.match_score,
            feedback.semantic_similarity,
            feedback.skill_match_ratio,
            feedback.feedback_text,
            feedback.feedback_tags,
            feedback.match_type,
            feedback.job_title,
            feedback.company,
        )
        return MatchFeedbackResponse(
            id=str(row["id"]),
            job_id=str(row["job_id"]),
            rating=row["rating"],
            created_at=row["created_at"],
        )

    @staticmethod
    async def get_user_feedback(
        conn: asyncpg.Connection,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get all feedback submitted by a user."""
        rows = await conn.fetch(
            """
            SELECT 
                mf.id, mf.job_id, mf.rating, mf.match_score,
                mf.feedback_text, mf.feedback_tags, mf.created_at,
                mf.job_title, mf.company,
                j.title as actual_job_title,
                j.company as actual_company
            FROM public.match_feedback mf
            LEFT JOIN public.jobs j ON j.id = mf.job_id
            WHERE mf.user_id = $1
            ORDER BY mf.created_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_id,
            limit,
            offset,
        )
        return [dict(row) for row in rows]

    @staticmethod
    async def get_job_stats(
        conn: asyncpg.Connection,
        job_id: str,
    ) -> MatchFeedbackStats | None:
        """Get aggregate feedback statistics for a job."""
        row = await conn.fetchrow(
            """
            SELECT 
                job_id,
                COUNT(*) AS total_feedback,
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS thumbs_up,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) AS thumbs_down,
                AVG(match_score) AS avg_match_score,
                AVG(CASE WHEN rating = 1 THEN match_score ELSE NULL END) AS avg_score_positive,
                AVG(CASE WHEN rating = -1 THEN match_score ELSE NULL END) AS avg_score_negative,
                ARRAY_AGG(DISTINCT tag) FILTER (WHERE tag IS NOT NULL) AS common_tags
            FROM public.match_feedback
            CROSS JOIN LATERAL unnest(feedback_tags) AS tag
            WHERE job_id = $1
            GROUP BY job_id
            """,
            job_id,
        )
        if not row or row["total_feedback"] == 0:
            return None
        return MatchFeedbackStats(
            job_id=str(row["job_id"]),
            total_feedback=row["total_feedback"],
            thumbs_up=row["thumbs_up"],
            thumbs_down=row["thumbs_down"],
            avg_match_score=float(row["avg_match_score"] or 0),
            avg_score_positive=float(row["avg_score_positive"])
            if row["avg_score_positive"]
            else None,
            avg_score_negative=float(row["avg_score_negative"])
            if row["avg_score_negative"]
            else None,
            common_tags=list(row["common_tags"] or []),
        )

    @staticmethod
    async def get_adjusted_score(
        conn: asyncpg.Connection,
        job_id: str,
        base_score: float,
    ) -> float:
        """Get feedback-adjusted match score for a job."""
        try:
            result = await conn.fetchval(
                "SELECT public.compute_adjusted_match_score($1, $2)",
                job_id,
                base_score,
            )
            return float(result)
        except Exception:
            return base_score

    @staticmethod
    async def get_feedback_summary(
        conn: asyncpg.Connection,
        tenant_id: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get overall feedback summary for analytics."""
        if tenant_id:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) AS total_feedback,
                    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS total_thumbs_up,
                    SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) AS total_thumbs_down,
                    COUNT(DISTINCT user_id) AS unique_users,
                    COUNT(DISTINCT job_id) AS unique_jobs,
                    AVG(match_score) AS avg_match_score
                FROM public.match_feedback
                WHERE tenant_id = $1
                  AND created_at > now() - ($2 * interval '1 day')
                """,
                tenant_id,
                days,
            )
        else:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) AS total_feedback,
                    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS total_thumbs_up,
                    SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) AS total_thumbs_down,
                    COUNT(DISTINCT user_id) AS unique_users,
                    COUNT(DISTINCT job_id) AS unique_jobs,
                    AVG(match_score) AS avg_match_score
                FROM public.match_feedback
                WHERE created_at > now() - ($1 * interval '1 day')
                """,
                days,
            )

        if not row:
            return {"total_feedback": 0, "satisfaction_rate": None}

        total = row["total_feedback"] or 0
        thumbs_up = row["total_thumbs_up"] or 0
        satisfaction_rate = (thumbs_up / total * 100) if total > 0 else None

        return {
            "total_feedback": total,
            "total_thumbs_up": thumbs_up,
            "total_thumbs_down": row["total_thumbs_down"] or 0,
            "unique_users": row["unique_users"] or 0,
            "unique_jobs": row["unique_jobs"] or 0,
            "avg_match_score": float(row["avg_match_score"])
            if row["avg_match_score"]
            else None,
            "satisfaction_rate": round(satisfaction_rate, 1)
            if satisfaction_rate is not None
            else None,
        }


VALID_FEEDBACK_TAGS = [
    "good_skills_match",
    "bad_skills_match",
    "good_location",
    "bad_location",
    "salary_too_low",
    "salary_good",
    "good_company",
    "bad_company",
    "interesting_role",
    "not_interested",
    "remote_friendly",
    "not_remote",
    "visa_sponsored",
    "no_visa",
    "good_experience_match",
    "overqualified",
    "underqualified",
    "other",
]


def validate_feedback_tags(tags: list[str]) -> list[str]:
    """Filter tags to only include valid ones."""
    return [tag for tag in tags if tag in VALID_FEEDBACK_TAGS]
