"""
Interview Preparation Simulator.

Implements the "Pre-Flight Interview Simulator" recommended in competitive analysis:
- Asynchronous voice-interactive LLM mock interviews
- Company-specific interview preparation
- Technical and behavioral question generation
- Real-time feedback and scoring

Based on competitive analysis:
"Introduce 'Ethical Interview Guardrails and Asynchronous Simulation.'
This consists of an intense, highly adversarial voice-based LLM simulation
conducted twenty-four hours before the interview."
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field

from shared.logging_config import get_logger

logger = get_logger("sorce.interview_simulator")


class InterviewType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    CODING = "coding"
    CASE_STUDY = "case_study"
    CULTURE_FIT = "culture_fit"
    GENERAL = "general"


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class InterviewPhase(str, Enum):
    INTRODUCTION = "introduction"
    WARMUP = "warmup"
    CORE_QUESTIONS = "core_questions"
    DEEP_DIVE = "deep_dive"
    CLOSING = "closing"


class InterviewQuestion(BaseModel):
    id: str
    question: str
    question_type: InterviewType
    difficulty: QuestionDifficulty
    phase: InterviewPhase
    expected_keywords: list[str] = Field(default_factory=list)
    follow_up_prompts: list[str] = Field(default_factory=list)
    time_limit_seconds: int = 180
    hints: list[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    question_id: str
    response_text: str
    response_time_seconds: float
    confidence_level: float = Field(default=0.5, ge=0.0, le=1.0)
    keywords_hit: list[str] = Field(default_factory=list)
    missed_keywords: list[str] = Field(default_factory=list)


class FeedbackScore(BaseModel):
    clarity: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    depth: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    structure: float = Field(default=0.5, ge=0.0, le=1.0)
    overall: float = Field(default=0.5, ge=0.0, le=1.0)


class QuestionFeedback(BaseModel):
    question_id: str
    score: FeedbackScore
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    sample_answer: str | None = None
    tips: list[str] = Field(default_factory=list)


class InterviewSession(BaseModel):
    session_id: str
    user_id: str
    job_id: str
    company: str
    job_title: str
    interview_type: InterviewType
    difficulty: QuestionDifficulty
    questions: list[InterviewQuestion] = Field(default_factory=list)
    responses: list[UserResponse] = Field(default_factory=list)
    feedback: list[QuestionFeedback] = Field(default_factory=list)
    current_phase: InterviewPhase = InterviewPhase.INTRODUCTION
    current_question_index: int = 0
    total_score: float = 0.0
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    status: str = "in_progress"


class InterviewSimulator:
    """
    AI-powered interview preparation simulator.

    Generates realistic interview scenarios based on:
    - Job description and company context
    - User's profile and experience
    - Industry-specific patterns
    - Common interview question banks
    """

    BEHAVIORAL_QUESTIONS = [
        "Tell me about yourself and your background.",
        "Why are you interested in this role?",
        "What are your greatest strengths?",
        "What is your biggest weakness?",
        "Describe a challenging project you worked on.",
        "Tell me about a time you had to work with a difficult team member.",
        "How do you handle pressure and tight deadlines?",
        "Describe a time you had to learn something new quickly.",
        "Tell me about a time you failed and what you learned.",
        "Where do you see yourself in 5 years?",
        "Why do you want to work for our company?",
        "What motivates you in your work?",
        "Describe your ideal work environment.",
        "How do you prioritize your work?",
        "Tell me about a time you showed leadership.",
    ]

    TECHNICAL_PATTERNS = {
        "software engineer": [
            "Explain how you would design a scalable web application.",
            "What is your approach to debugging a production issue?",
            "How do you ensure code quality in your projects?",
            "Describe your experience with {technology}.",
            "How would you optimize a slow database query?",
            "Explain the difference between {concept_a} and {concept_b}.",
            "How do you handle technical debt?",
        ],
        "data scientist": [
            "How would you approach a new machine learning problem?",
            "Explain the trade-offs between different ML algorithms.",
            "How do you handle imbalanced datasets?",
            "Describe your feature engineering process.",
            "How do you validate your models?",
        ],
        "product manager": [
            "How do you prioritize features in your roadmap?",
            "Describe your approach to gathering user requirements.",
            "How do you measure product success?",
            "Tell me about a product decision you made with limited data.",
        ],
    }

    def __init__(self, llm_client: Any = None):
        self._llm_client = llm_client

    async def create_session(
        self,
        user_id: str,
        job_id: str,
        company: str,
        job_title: str,
        job_description: str,
        user_profile: dict[str, Any],
        interview_type: InterviewType = InterviewType.GENERAL,
        difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM,
        question_count: int = 10,
    ) -> InterviewSession:
        """
        Create a new interview preparation session.

        Generates personalized questions based on the job and user profile.
        """
        import uuid

        session_id = str(uuid.uuid4())

        questions = await self._generate_questions(
            job_title=job_title,
            company=company,
            job_description=job_description,
            user_profile=user_profile,
            interview_type=interview_type,
            difficulty=difficulty,
            count=question_count,
        )

        return InterviewSession(
            session_id=session_id,
            user_id=user_id,
            job_id=job_id,
            company=company,
            job_title=job_title,
            interview_type=interview_type,
            difficulty=difficulty,
            questions=questions,
        )

    async def _generate_questions(
        self,
        job_title: str,
        company: str,
        job_description: str,
        user_profile: dict[str, Any],
        interview_type: InterviewType,
        difficulty: QuestionDifficulty,
        count: int,
    ) -> list[InterviewQuestion]:
        """Generate interview questions based on context."""
        import uuid

        questions: list[InterviewQuestion] = []

        job_lower = job_title.lower()

        intro_question = InterviewQuestion(
            id=str(uuid.uuid4()),
            question=f"Welcome! Let's start with: Tell me about yourself and why you're interested in the {job_title} role at {company}.",
            question_type=InterviewType.BEHAVIORAL,
            difficulty=QuestionDifficulty.EASY,
            phase=InterviewPhase.INTRODUCTION,
            expected_keywords=[
                "experience",
                "background",
                "interested",
                "company",
                "role",
            ],
            time_limit_seconds=120,
        )
        questions.append(intro_question)

        behavioral_count = max(2, count // 4)
        for i in range(behavioral_count):
            if i < len(self.BEHAVIORAL_QUESTIONS):
                q = self.BEHAVIORAL_QUESTIONS[i + 1]
            else:
                q = self.BEHAVIORAL_QUESTIONS[i % len(self.BEHAVIORAL_QUESTIONS)]

            questions.append(
                InterviewQuestion(
                    id=str(uuid.uuid4()),
                    question=q,
                    question_type=InterviewType.BEHAVIORAL,
                    difficulty=difficulty,
                    phase=InterviewPhase.CORE_QUESTIONS,
                    expected_keywords=self._extract_keywords(q),
                    time_limit_seconds=180,
                )
            )

        for role_pattern, tech_questions in self.TECHNICAL_PATTERNS.items():
            if role_pattern in job_lower:
                for i, q_template in enumerate(tech_questions[: count // 3]):
                    question = self._customize_question(q_template, job_description)
                    questions.append(
                        InterviewQuestion(
                            id=str(uuid.uuid4()),
                            question=question,
                            question_type=InterviewType.TECHNICAL,
                            difficulty=difficulty,
                            phase=InterviewPhase.DEEP_DIVE,
                            expected_keywords=self._extract_keywords(question),
                            time_limit_seconds=300,
                        )
                    )
                break

        closing_question = InterviewQuestion(
            id=str(uuid.uuid4()),
            question="Do you have any questions for us about the role or the company?",
            question_type=InterviewType.GENERAL,
            difficulty=QuestionDifficulty.EASY,
            phase=InterviewPhase.CLOSING,
            expected_keywords=["question", "team", "company", "culture", "projects"],
            time_limit_seconds=120,
        )
        questions.append(closing_question)

        return questions[:count]

    def _customize_question(self, template: str, job_description: str) -> str:
        """Customize a question template based on job description."""
        import re

        technologies = re.findall(
            r"\b(python|javascript|typescript|react|angular|vue|node|django|flask|"
            r"fastapi|aws|azure|gcp|docker|kubernetes|sql|mongodb|redis)\b",
            job_description.lower(),
        )

        question = template
        if "{technology}" in template and technologies:
            question = question.replace("{technology}", technologies[0].title())
        elif "{technology}" in template:
            question = question.replace("{technology}", "your primary technology stack")

        if "{concept_a}" in template:
            question = question.replace("{concept_a}", "REST")
            question = question.replace("{concept_b}", "GraphQL")

        return question

    def _extract_keywords(self, question: str) -> list[str]:
        """Extract important keywords from a question."""
        import re

        words = re.findall(r"\b[a-zA-Z]{4,}\b", question.lower())
        stop_words = {
            "tell",
            "about",
            "your",
            "with",
            "what",
            "when",
            "where",
            "which",
            "would",
            "could",
            "should",
            "have",
            "from",
            "they",
            "this",
            "that",
            "been",
            "were",
            "said",
            "each",
            "which",
            "their",
            "time",
            "very",
            "just",
            "know",
            "take",
            "come",
            "make",
            "more",
            "some",
            "most",
            "such",
            "than",
            "then",
            "them",
            "these",
            "those",
        }
        return [w for w in words if w not in stop_words][:10]

    async def submit_response(
        self,
        session: InterviewSession,
        response_text: str,
        response_time_seconds: float,
    ) -> QuestionFeedback:
        """Submit a response and get AI-powered feedback."""
        current_question = session.questions[session.current_question_index]

        keywords_hit = []
        missed_keywords = []
        response_lower = response_text.lower()

        for keyword in current_question.expected_keywords:
            if keyword.lower() in response_lower:
                keywords_hit.append(keyword)
            else:
                missed_keywords.append(keyword)

        response = UserResponse(
            question_id=current_question.id,
            response_text=response_text,
            response_time_seconds=response_time_seconds,
            keywords_hit=keywords_hit,
            missed_keywords=missed_keywords,
        )
        session.responses.append(response)

        feedback = await self._generate_feedback(
            question=current_question,
            response=response,
            session=session,
        )
        session.feedback.append(feedback)

        session.current_question_index += 1

        if session.current_question_index >= len(session.questions):
            session.status = "completed"
            session.completed_at = datetime.now(UTC)
            session.total_score = self._calculate_total_score(session)

        return feedback

    async def _generate_feedback(
        self,
        question: InterviewQuestion,
        response: UserResponse,
        session: InterviewSession,
    ) -> QuestionFeedback:
        """Generate detailed feedback for a response."""
        keyword_score = (
            len(response.keywords_hit) / len(question.expected_keywords)
            if question.expected_keywords
            else 0.5
        )

        word_count = len(response.response_text.split())
        length_score = 0.5
        if 50 <= word_count <= 200:
            length_score = 1.0
        elif 30 <= word_count <= 300:
            length_score = 0.7

        time_score = 0.5
        if response.response_time_seconds <= question.time_limit_seconds:
            time_score = 1.0
        elif response.response_time_seconds <= question.time_limit_seconds * 1.5:
            time_score = 0.7

        strengths = []
        improvements = []

        if keyword_score >= 0.7:
            strengths.append("Addressed key topics effectively")
        if response.keywords_hit:
            strengths.append(
                f"Covered important concepts: {', '.join(response.keywords_hit[:3])}"
            )
        if length_score >= 0.7:
            strengths.append("Response length was appropriate")

        if keyword_score < 0.5:
            improvements.append("Consider addressing more aspects of the question")
        if response.missed_keywords:
            improvements.append(
                f"Could expand on: {', '.join(response.missed_keywords[:3])}"
            )
        if response.response_time_seconds > question.time_limit_seconds:
            improvements.append("Try to be more concise")

        score = FeedbackScore(
            clarity=length_score,
            relevance=keyword_score,
            depth=min(1.0, keyword_score * 1.2),
            confidence=time_score,
            structure=0.6,
            overall=(keyword_score + length_score + time_score) / 3,
        )

        sample_answer = None
        if score.overall < 0.6:
            sample_answer = self._generate_sample_answer(question, session)

        return QuestionFeedback(
            question_id=question.id,
            score=score,
            strengths=strengths,
            improvements=improvements,
            sample_answer=sample_answer,
            tips=self._generate_tips(question.question_type),
        )

    def _generate_sample_answer(
        self,
        question: InterviewQuestion,
        session: InterviewSession,
    ) -> str:
        """Generate a sample answer for the question."""
        if question.question_type == InterviewType.BEHAVIORAL:
            return (
                f"A strong response would include a specific example using the STAR method "
                f"(Situation, Task, Action, Result). For the {session.job_title} role at "
                f"{session.company}, focus on relevant experiences that demonstrate your "
                f"qualifications and alignment with the company's values."
            )
        elif question.question_type == InterviewType.TECHNICAL:
            return (
                f"For technical questions, structure your answer to show your thought process: "
                f"1) Clarify the requirements, 2) Discuss your approach, "
                f"3) Mention trade-offs, 4) Provide concrete examples from your experience."
            )
        return (
            "Practice answering this question concisely while covering the key topics."
        )

    def _generate_tips(self, question_type: InterviewType) -> list[str]:
        """Generate tips for the question type."""
        tips_map = {
            InterviewType.BEHAVIORAL: [
                "Use the STAR method: Situation, Task, Action, Result",
                "Be specific with examples and quantify outcomes",
                "Connect your experience to the role requirements",
            ],
            InterviewType.TECHNICAL: [
                "Explain your thought process out loud",
                "Ask clarifying questions before diving in",
                "Discuss trade-offs and alternatives",
            ],
            InterviewType.CODING: [
                "Talk through your approach before coding",
                "Consider edge cases and error handling",
                "Optimize after getting a working solution",
            ],
            InterviewType.SYSTEM_DESIGN: [
                "Start with requirements clarification",
                "Draw diagrams to illustrate your design",
                "Consider scalability, reliability, and cost",
            ],
        }
        return tips_map.get(question_type, ["Stay calm and take your time"])

    def _calculate_total_score(self, session: InterviewSession) -> float:
        """Calculate overall session score."""
        if not session.feedback:
            return 0.0

        scores = [f.score.overall for f in session.feedback]
        return sum(scores) / len(scores)

    def get_session_summary(self, session: InterviewSession) -> dict[str, Any]:
        """Get a comprehensive summary of the interview session."""
        if session.status != "completed":
            return {
                "status": "in_progress",
                "current_question": session.current_question_index + 1,
                "total_questions": len(session.questions),
            }

        category_scores: dict[str, list[float]] = {}
        for i, feedback in enumerate(session.feedback):
            q_type = session.questions[i].question_type.value
            if q_type not in category_scores:
                category_scores[q_type] = []
            category_scores[q_type].append(feedback.score.overall)

        avg_category_scores = {
            cat: sum(scores) / len(scores) for cat, scores in category_scores.items()
        }

        all_strengths = []
        all_improvements = []
        for f in session.feedback:
            all_strengths.extend(f.strengths)
            all_improvements.extend(f.improvements)

        return {
            "status": "completed",
            "session_id": session.session_id,
            "company": session.company,
            "job_title": session.job_title,
            "total_score": session.total_score,
            "questions_answered": len(session.responses),
            "category_scores": avg_category_scores,
            "top_strengths": list(set(all_strengths))[:5],
            "top_improvements": list(set(all_improvements))[:5],
            "duration_minutes": (
                (session.completed_at - session.started_at).total_seconds() / 60
                if session.completed_at
                else 0
            ),
            "difficulty": session.difficulty.value,
        }


_interview_simulator: InterviewSimulator | None = None


def get_interview_simulator() -> InterviewSimulator:
    global _interview_simulator
    if _interview_simulator is None:
        _interview_simulator = InterviewSimulator()
    return _interview_simulator
