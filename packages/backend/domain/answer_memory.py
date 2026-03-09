"""
Answer memory system for interview preparation and question tracking.

Provides:
  - Store and retrieve interview questions and answers
  - Personalized answer suggestions based on profile
  - Question categorization and difficulty tracking
  - Performance analytics and improvement recommendations
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from shared.logging_config import get_logger

logger = get_logger("sorce.answer_memory")

# Question categories
QUESTION_CATEGORIES = [
    "behavioral",
    "technical",
    "situational",
    "leadership",
    "problem_solving",
    "cultural_fit",
    "salary_negotiation",
    "company_specific",
    "role_specific",
    "general",
]

# Difficulty levels
DIFFICULTY_LEVELS = ["easy", "medium", "hard", "expert"]


class InterviewQuestion(BaseModel):
    """Interview question with metadata."""

    id: str
    question: str
    category: str
    difficulty: str
    context: Optional[str] = None
    tags: List[str] = []
    company_specific: bool = False
    role_specific: bool = False
    created_at: datetime
    usage_count: int = 0


class AnswerAttempt(BaseModel):
    """Record of an answer attempt."""

    id: str
    question_id: str
    user_id: str
    tenant_id: str
    answer: str
    confidence_score: float = 0.0  # 0-1
    feedback: Optional[str] = None
    ai_score: Optional[float] = None
    created_at: datetime
    reviewed: bool = False
    notes: Optional[str] = None


class AnswerMemory(BaseModel):
    """User's answer memory entry."""

    id: str
    user_id: str
    tenant_id: str
    question_id: str
    memorized_answer: str
    key_points: List[str] = []
    examples: List[str] = []
    follow_up_questions: List[str] = []
    last_reviewed: Optional[datetime] = None
    review_count: int = 0
    mastery_level: float = 0.0  # 0-1
    created_at: datetime
    updated_at: datetime


class QuestionAnalytics(BaseModel):
    """Question performance analytics."""

    question_id: str
    total_attempts: int
    average_confidence: float
    average_ai_score: float
    mastery_rate: float
    improvement_suggestions: List[str] = []


class AnswerMemoryManager:
    """Manages interview answer memory and analytics."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.questions = self._initialize_questions()

    async def get_recommended_questions(
        self,
        tenant_id: str,
        user_id: str,
        job_title: str,
        company_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[InterviewQuestion]:
        """Get recommended questions based on user profile and job."""

        async with self.db_pool.acquire() as conn:
            # Get user profile and experience
            profile_data = await conn.fetchrow(
                """
                SELECT experience_years, skills, industry, job_level
                FROM user_profiles 
                WHERE user_id = $1 AND tenant_id = $2
                """,
                user_id,
                tenant_id,
            )

            # Get user's question history
            history_data = await conn.fetch(
                """
                SELECT question_id, confidence_score, ai_score, created_at
                FROM answer_attempts
                WHERE user_id = $1 AND tenant_id = $2
                ORDER BY created_at DESC
                LIMIT 50
                """,
                user_id,
                tenant_id,
            )

            # Get questions user has already memorized
            memorized_questions = await conn.fetch(
                """
                SELECT question_id, mastery_level
                FROM answer_memory
                WHERE user_id = $1 AND tenant_id = $2
                """,
                user_id,
                tenant_id,
            )

            memorized_ids = {row["question_id"] for row in memorized_questions}

            # Filter and recommend questions
            recommended = []

            for question in self.questions:
                # Skip if already memorized with high mastery
                if question.id in memorized_ids:
                    mastery = next(
                        (
                            row["mastery_level"]
                            for row in memorized_questions
                            if row["question_id"] == question.id
                        ),
                        0,
                    )
                    if mastery > 0.8:
                        continue

                # Score based on relevance
                relevance_score = self._calculate_question_relevance(
                    question,
                    job_title,
                    company_name,
                    profile_data,
                    history_data,
                )

                if relevance_score > 0.3:  # Threshold for recommendation
                    question_copy = question.model_copy()
                    question_copy.usage_count = int(
                        relevance_score * 100
                    )  # Store as usage for sorting
                    recommended.append(question_copy)

            # Sort by relevance and limit
            recommended.sort(key=lambda q: q.usage_count, reverse=True)
            return recommended[:limit]

    async def save_answer_attempt(
        self,
        tenant_id: str,
        user_id: str,
        question_id: str,
        answer: str,
        confidence_score: float = 0.0,
    ) -> AnswerAttempt:
        """Save an answer attempt with optional AI scoring."""

        attempt_id = str(uuid.uuid4())

        # Generate AI feedback and score (placeholder)
        ai_score, feedback = await self._generate_ai_feedback(question_id, answer)

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO answer_attempts (
                    id, question_id, user_id, tenant_id, answer,
                    confidence_score, ai_score, feedback, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                """,
                attempt_id,
                question_id,
                user_id,
                tenant_id,
                answer,
                confidence_score,
                ai_score,
                feedback,
            )

            # Update question usage count
            await conn.execute(
                """
                UPDATE interview_questions 
                SET usage_count = usage_count + 1 
                WHERE id = $1
                """,
                question_id,
            )

            attempt = AnswerAttempt(
                id=attempt_id,
                question_id=question_id,
                user_id=user_id,
                tenant_id=tenant_id,
                answer=answer,
                confidence_score=confidence_score,
                ai_score=ai_score,
                feedback=feedback,
                created_at=datetime.now(timezone.utc),
            )

            logger.info(
                "Saved answer attempt %s for question %s by user %s",
                attempt_id,
                question_id,
                user_id,
            )

            return attempt

    async def create_answer_memory(
        self,
        tenant_id: str,
        user_id: str,
        question_id: str,
        memorized_answer: str,
        key_points: List[str] = None,
        examples: List[str] = None,
    ) -> AnswerMemory:
        """Create or update answer memory entry."""

        async with self.db_pool.acquire() as conn:
            # Check if memory entry already exists
            existing = await conn.fetchrow(
                """
                SELECT id FROM answer_memory
                WHERE user_id = $1 AND tenant_id = $2 AND question_id = $3
                """,
                user_id,
                tenant_id,
                question_id,
            )

            if existing:
                # Update existing
                await conn.execute(
                    """
                    UPDATE answer_memory
                    SET memorized_answer = $4, key_points = $5, examples = $6,
                        updated_at = NOW(), review_count = review_count + 1
                    WHERE id = $1
                    """,
                    existing["id"],
                    question_id,
                    memorized_answer,
                    key_points or [],
                    examples or [],
                )

                memory_id = existing["id"]
            else:
                # Create new
                memory_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO answer_memory (
                        id, user_id, tenant_id, question_id, memorized_answer,
                        key_points, examples, mastery_level, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, 0.5, NOW(), NOW())
                    """,
                    memory_id,
                    user_id,
                    tenant_id,
                    question_id,
                    memorized_answer,
                    key_points or [],
                    examples or [],
                )

            # Get the memory entry
            memory_data = await conn.fetchrow(
                """
                SELECT * FROM answer_memory WHERE id = $1
                """,
                memory_id,
            )

            memory = AnswerMemory(
                id=memory_data["id"],
                user_id=memory_data["user_id"],
                tenant_id=memory_data["tenant_id"],
                question_id=memory_data["question_id"],
                memorized_answer=memory_data["memorized_answer"],
                key_points=memory_data.get("key_points", []),
                examples=memory_data.get("examples", []),
                follow_up_questions=memory_data.get("follow_up_questions", []),
                last_reviewed=memory_data.get("last_reviewed"),
                review_count=memory_data.get("review_count", 0),
                mastery_level=memory_data.get("mastery_level", 0.0),
                created_at=memory_data["created_at"],
                updated_at=memory_data["updated_at"],
            )

            return memory

    async def get_user_memories(
        self,
        tenant_id: str,
        user_id: str,
        category: Optional[str] = None,
        mastery_threshold: float = 0.0,
        limit: int = 50,
    ) -> List[AnswerMemory]:
        """Get user's answer memories with optional filtering."""

        async with self.db_pool.acquire() as conn:
            query = """
            SELECT am.*, iq.category, iq.question, iq.difficulty
            FROM answer_memory am
            JOIN interview_questions iq ON am.question_id = iq.id
            WHERE am.user_id = $1 AND am.tenant_id = $2
            """
            params = [user_id, tenant_id]
            param_idx = 3

            if category:
                query += f" AND iq.category = ${param_idx}"
                params.append(category)
                param_idx += 1

            if mastery_threshold > 0:
                query += f" AND am.mastery_level >= ${param_idx}"
                params.append(mastery_threshold)
                param_idx += 1

            query += " ORDER BY am.updated_at DESC LIMIT $" + str(param_idx)
            params.append(limit)

            rows = await conn.fetch(query, *params)

            memories = []
            for row in rows:
                memory = AnswerMemory(
                    id=row["id"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    question_id=row["question_id"],
                    memorized_answer=row["memorized_answer"],
                    key_points=row.get("key_points", []),
                    examples=row.get("examples", []),
                    follow_up_questions=row.get("follow_up_questions", []),
                    last_reviewed=row.get("last_reviewed"),
                    review_count=row.get("review_count", 0),
                    mastery_level=row.get("mastery_level", 0.0),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                memories.append(memory)

            return memories

    async def get_question_analytics(
        self,
        tenant_id: str,
        user_id: str,
        question_id: str,
    ) -> Optional[QuestionAnalytics]:
        """Get analytics for a specific question."""

        async with self.db_pool.acquire() as conn:
            # Get answer attempts
            attempts = await conn.fetch(
                """
                SELECT confidence_score, ai_score, created_at
                FROM answer_attempts
                WHERE question_id = $1 AND user_id = $2 AND tenant_id = $3
                ORDER BY created_at ASC
                """,
                question_id,
                user_id,
                tenant_id,
            )

            if not attempts:
                return None

            # Calculate metrics
            total_attempts = len(attempts)
            avg_confidence = (
                sum(row["confidence_score"] for row in attempts) / total_attempts
            )
            avg_ai_score = (
                sum(row["ai_score"] or 0 for row in attempts) / total_attempts
            )

            # Calculate mastery rate (attempts with ai_score > 0.7)
            mastery_attempts = sum(
                1 for row in attempts if (row["ai_score"] or 0) > 0.7
            )
            mastery_rate = mastery_attempts / total_attempts

            # Generate improvement suggestions
            suggestions = self._generate_improvement_suggestions(
                attempts,
                avg_confidence,
                avg_ai_score,
            )

            return QuestionAnalytics(
                question_id=question_id,
                total_attempts=total_attempts,
                average_confidence=avg_confidence,
                average_ai_score=avg_ai_score,
                mastery_rate=mastery_rate,
                improvement_suggestions=suggestions,
            )

    async def update_mastery_level(
        self,
        tenant_id: str,
        user_id: str,
        question_id: str,
    ) -> float:
        """Update and return mastery level for a question."""

        async with self.db_pool.acquire() as conn:
            # Get recent attempts
            recent_attempts = await conn.fetch(
                """
                SELECT confidence_score, ai_score
                FROM answer_attempts
                WHERE question_id = $1 AND user_id = $2 AND tenant_id = $3
                AND created_at > NOW() - INTERVAL '30 days'
                ORDER BY created_at DESC
                LIMIT 10
                """,
                question_id,
                user_id,
                tenant_id,
            )

            if not recent_attempts:
                return 0.0

            # Calculate mastery based on recent performance
            avg_confidence = sum(
                row["confidence_score"] for row in recent_attempts
            ) / len(recent_attempts)
            avg_ai_score = sum(row["ai_score"] or 0 for row in recent_attempts) / len(
                recent_attempts
            )

            # Weight recent performance more heavily
            mastery = avg_confidence * 0.3 + avg_ai_score * 0.7

            # Update in database
            await conn.execute(
                """
                UPDATE answer_memory
                SET mastery_level = $1, last_reviewed = NOW(), updated_at = NOW()
                WHERE question_id = $2 AND user_id = $3 AND tenant_id = $4
                """,
                mastery,
                question_id,
                user_id,
                tenant_id,
            )

            return mastery

    def _initialize_questions(self) -> List[InterviewQuestion]:
        """Initialize default interview questions."""

        questions = []

        # Behavioral questions
        questions.append(
            InterviewQuestion(
                id="tell_me_about_yourself",
                question="Tell me about yourself.",
                category="behavioral",
                difficulty="easy",
                context="Icebreaker question",
                tags=["introduction", "personal"],
                created_at=datetime.now(timezone.utc),
            )
        )

        questions.append(
            InterviewQuestion(
                id="strengths_weaknesses",
                question="What are your greatest strengths and weaknesses?",
                category="behavioral",
                difficulty="medium",
                context="Self-assessment",
                tags=["self-awareness", "improvement"],
                created_at=datetime.now(timezone.utc),
            )
        )

        # Technical questions
        questions.append(
            InterviewQuestion(
                id="technical_challenge",
                question="Describe a challenging technical problem you've solved.",
                category="technical",
                difficulty="hard",
                context="Problem-solving",
                tags=["technical", "problem-solving"],
                created_at=datetime.now(timezone.utc),
            )
        )

        # Situational questions
        questions.append(
            InterviewQuestion(
                id="handle_conflict",
                question="How do you handle conflicts with team members?",
                category="situational",
                difficulty="medium",
                context="Team dynamics",
                tags=["conflict", "teamwork"],
                created_at=datetime.now(timezone.utc),
            )
        )

        # Leadership questions
        questions.append(
            InterviewQuestion(
                id="leadership_experience",
                question="Describe your leadership experience.",
                category="leadership",
                difficulty="medium",
                context="Leadership assessment",
                tags=["leadership", "management"],
                created_at=datetime.now(timezone.utc),
            )
        )

        return questions

    def _calculate_question_relevance(
        self,
        question: InterviewQuestion,
        job_title: str,
        company_name: Optional[str],
        profile_data: Optional[Dict[str, Any]],
        history_data: List[Dict[str, Any]],
    ) -> float:
        """Calculate relevance score for a question."""

        score = 0.5  # Base score

        # Job title relevance
        job_title_lower = job_title.lower()
        if "manager" in job_title_lower and question.category == "leadership":
            score += 0.3
        elif "technical" in job_title_lower or "engineer" in job_title_lower:
            if question.category == "technical":
                score += 0.3
            elif question.category == "problem_solving":
                score += 0.2

        # Experience level
        if profile_data:
            experience = profile_data.get("experience_years", 0)
            if experience < 2 and question.difficulty == "easy":
                score += 0.2
            elif experience >= 5 and question.difficulty in ["hard", "expert"]:
                score += 0.2

        # Historical performance
        if history_data:
            # Boost questions user hasn't seen recently
            recent_question_ids = {row["question_id"] for row in history_data[:10]}
            if question.id not in recent_question_ids:
                score += 0.2

            # Consider confidence levels
            avg_confidence = sum(
                row.get("confidence_score", 0) for row in history_data[:5]
            ) / min(5, len(history_data))
            if avg_confidence < 0.6 and question.difficulty == "easy":
                score += 0.1

        return min(score, 1.0)

    async def _generate_ai_feedback(
        self,
        question_id: str,
        answer: str,
    ) -> tuple[float, str]:
        """Generate AI feedback and score for an answer."""

        # Placeholder implementation
        # In production, integrate with LLM for real feedback

        # Simple scoring based on answer length and content
        answer_length = len(answer)

        if answer_length < 50:
            score = 0.3
            feedback = "Your answer is quite brief. Consider providing more specific examples and details."
        elif answer_length < 150:
            score = 0.6
            feedback = "Good answer. Try to include specific examples that demonstrate your skills."
        else:
            score = 0.8
            feedback = (
                "Excellent detailed answer. You've provided good context and examples."
            )

        # Check for common good answer patterns
        if any(
            keyword in answer.lower()
            for keyword in ["example", "specifically", "result", "achieved"]
        ):
            score += 0.1
            feedback += " Great use of specific examples!"

        return min(score, 1.0), feedback

    def _generate_improvement_suggestions(
        self,
        attempts: List[Dict[str, Any]],
        avg_confidence: float,
        avg_ai_score: float,
    ) -> List[str]:
        """Generate improvement suggestions based on performance."""

        suggestions = []

        if avg_confidence < 0.5:
            suggestions.append(
                "Practice your answer to build confidence. Try recording yourself."
            )

        if avg_ai_score < 0.6:
            suggestions.append(
                "Add more specific examples and measurable results to your answers."
            )

        if len(attempts) < 3:
            suggestions.append(
                "Practice this question more frequently to improve your response."
            )

        # Check for improvement trend
        if len(attempts) >= 3:
            recent_scores = [row.get("ai_score", 0) for row in attempts[-3:]]
            if recent_scores[-1] < recent_scores[0]:
                suggestions.append(
                    "Your recent performance has declined. Review and refine your approach."
                )

        return suggestions


# Factory function
def create_answer_memory_manager(db_pool) -> AnswerMemoryManager:
    """Create answer memory manager instance."""
    return AnswerMemoryManager(db_pool)
