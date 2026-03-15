"""
Voice Interview Simulator - Voice-enabled interview preparation system
Provides speech-to-text, text-to-speech, and voice analytics capabilities
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.logging_config import get_logger

logger = get_logger("sorce.voice_interviews")


class QuestionType(str, Enum):
    """Types of interview questions."""

    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOXES = "checkboxes"
    RADIO = "radio"
    RATING = "rating"
    BOOLEAN = "boolean"
    FILE_UPLOAD = "file_upload"
    SKILLS_ASSESSMENT = "skills_assessment"
    CAREER_GOALS = "career_goals"
    EXPERIENCE_LEVEL = "experience_level"


class QuestionComplexity(str, Enum):
    """Complexity levels for interview questions."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class InterviewType(str, Enum):
    """Types of interview sessions."""

    GENERAL = "general"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    CODING = "coding"
    CASE_STUDY = "case_study"
    PHONE_SCREEN = "phone_screen"
    FINAL_ROUND = "final_round"


class InterviewPhase(str, Enum):
    """Phases of an interview."""

    INTRODUCTION = "introduction"
    CORE_QUESTIONS = "core_questions"
    TECHNICAL_QUESTIONS = "technical_questions"
    DEEP_DIVE = "deep_dive"
    BEHAVIORAL_QUESTIONS = "behavioral_questions"
    PROBLEM_SOLVING = "problem_solving"
    CLOSING = "closing"


class VoiceAnalytics(BaseModel):
    """Voice analytics data."""

    clarity_score: float = Field(ge=0.0, le=1.0, description="Speech clarity score")
    pace_score: float = Field(ge=0.0, le=1.0, description="Speaking pace score")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score")
    filler_words_count: int = Field(ge=0, description="Number of filler words")
    total_duration_seconds: float = Field(
        ge=0.0, description="Total duration in seconds"
    )
    word_count: int = Field(ge=0, description="Total word count")
    average_words_per_minute: float = Field(
        ge=0.0, description="Average words per minute"
    )
    voice_quality_score: float = Field(
        ge=0.0, le=1.0, description="Voice quality score"
    )
    emotional_tone: str = Field(description="Detected emotional tone")
    speaking_rate: str = Field(description="Speaking rate category")


class VoiceSettings(BaseModel):
    """Voice settings for interview sessions."""

    speech_to_text: Dict[str, Any] = Field(default_factory=dict)
    text_to_speech: Dict[str, Any] = Field(default_factory=dict)
    voice_analytics: Dict[str, Any] = Field(default_factory=dict)
    language: str = Field(default="en-US")
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    voice_pitch: float = Field(default=0.0, ge=-20.0, le=20.0)


class InterviewQuestion(BaseModel):
    """Interview question model."""

    id: str
    question: str
    question_type: QuestionType
    difficulty: QuestionComplexity
    phase: InterviewPhase
    expected_keywords: List[str] = Field(default_factory=list)
    time_limit_seconds: int = Field(default=300)
    context: Dict[str, Any] = Field(default_factory=dict)


class UserResponse(BaseModel):
    """User response to interview question."""

    question_id: str
    response_text: str
    response_time_seconds: float
    keywords_hit: List[str] = Field(default_factory=list)
    missed_keywords: List[str] = Field(default_factory=list)


class FeedbackScore(BaseModel):
    """Feedback score for a response."""

    clarity: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    depth: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    structure: float = Field(ge=0.0, le=1.0)
    overall: float = Field(ge=0.0, le=1.0)


class QuestionFeedback(BaseModel):
    """Feedback for a question response."""

    question_id: str
    score: FeedbackScore
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    sample_answer: Optional[str] = None
    tips: List[str] = Field(default_factory=list)


class InterviewSession(BaseModel):
    """Interview session model."""

    session_id: str
    user_id: str
    job_id: Optional[str] = None
    company: str
    job_title: str
    interview_type: InterviewType
    difficulty: QuestionComplexity
    questions: List[InterviewQuestion]
    responses: List[UserResponse] = Field(default_factory=list)
    feedback: List[QuestionFeedback] = Field(default_factory=list)
    current_question_index: int = 0
    status: str = "active"
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_score: Optional[float] = None


class VoiceInterviewSession(BaseModel):
    """Voice interview session model."""

    interview_session_id: str
    user_id: str
    voice_settings: VoiceSettings
    audio_files: List[Dict[str, Any]] = Field(default_factory=list)
    transcriptions: List[Dict[str, Any]] = Field(default_factory=list)
    voice_analytics: List[VoiceAnalytics] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class VoiceInterviewSimulator:
    """Voice-enabled interview simulator with speech recognition and synthesis."""

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
        user_profile: Dict[str, Any],
        interview_type: InterviewType = InterviewType.GENERAL,
        difficulty: QuestionComplexity = QuestionComplexity.MEDIUM,
        question_count: int = 10,
        voice_settings: Optional[Dict[str, Any]] = None,
    ) -> InterviewSession:
        """Create a new interview session with voice support."""
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

        session = InterviewSession(
            session_id=session_id,
            user_id=user_id,
            job_id=job_id,
            company=company,
            job_title=job_title,
            interview_type=interview_type,
            difficulty=difficulty,
            questions=questions,
            started_at=datetime.now(timezone.utc),
        )

        # Create voice session
        VoiceInterviewSession(
            interview_session_id=session_id,
            user_id=user_id,
            voice_settings=VoiceSettings(**(voice_settings or {})),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return session

    async def _generate_questions(
        self,
        job_title: str,
        company: str,
        job_description: str,
        user_profile: Dict[str, Any],
        interview_type: InterviewType,
        difficulty: QuestionComplexity,
        count: int,
    ) -> List[InterviewQuestion]:
        """Generate interview questions based on context."""
        questions: List[InterviewQuestion] = []

        job_lower = job_title.lower()

        # Introduction question
        intro_question = InterviewQuestion(
            id=str(uuid.uuid4()),
            question=(
                f"Welcome! Let's start with: Tell me about yourself and why you're "
                f"interested in the {job_title} role at {company}."
            ),
            question_type=InterviewType.BEHAVIORAL,
            difficulty=QuestionComplexity.BASIC,
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

        # Behavioral questions
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

        # Technical questions based on job type
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
                            phase=InterviewPhase.TECHNICAL_QUESTIONS,
                            expected_keywords=self._extract_keywords(question),
                            time_limit_seconds=300,
                        )
                    )
                break

        # Closing question
        closing_question = InterviewQuestion(
            id=str(uuid.uuid4()),
            question="Do you have any questions for us about the role or the company?",
            question_type=InterviewType.GENERAL,
            difficulty=QuestionComplexity.BASIC,
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

    def _extract_keywords(self, question: str) -> List[str]:
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
        audio_data: Optional[bytes] = None,
    ) -> QuestionFeedback:
        """Submit a response with voice analysis and get feedback."""
        current_question = session.questions[session.current_question_index]

        # Analyze keywords
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

        # Generate feedback
        feedback = await self._generate_feedback(
            question=current_question,
            response=response,
            session=session,
        )
        session.feedback.append(feedback)

        # Voice analytics if audio provided
        if audio_data:
            voice_analytics = await self._analyze_voice_characteristics(
                audio_data=audio_data,
                transcription_text=response_text,
            )
            # Store voice analytics (in real implementation, would save to database)
            logger.info(
                f"Voice analytics generated: clarity={voice_analytics.clarity_score:.2f}"
            )

        session.current_question_index += 1

        if session.current_question_index >= len(session.questions):
            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            session.total_score = self._calculate_total_score(session)

        return feedback

    async def _generate_feedback(
        self,
        question: InterviewQuestion,
        response: UserResponse,
        session: InterviewSession,
    ) -> QuestionFeedback:
        """Generate detailed feedback for a response."""
        # Calculate basic scores
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

        # Generate sample answer if needed
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
        self, question: InterviewQuestion, session: InterviewSession
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
                "For technical questions, structure your answer to show your thought process: "
                "1) Clarify the requirements, 2) Discuss your approach, "
                "3) Mention trade-offs, 4) Provide concrete examples from your experience."
            )
        return (
            "Practice answering this question concisely while covering the key topics."
        )

    def _generate_tips(self, question_type: QuestionType) -> List[str]:
        """Generate tips for the question type."""
        tips_map = {
            InterviewType.BEHAVIORAL: [
                "Use the STAR method: Situation, Task, Action, Result",
                "Be specific with examples and quantify outcomes",
                "Connect your experience to the role requirements",
                "Practice with a mock interviewer",
            ],
            InterviewType.TECHNICAL: [
                "Explain your thought process out loud",
                "Ask clarifying questions before diving in",
                "Discuss trade-offs and alternatives",
                "Consider edge cases and error handling",
            ],
            InterviewType.CODING: [
                "Talk through your approach before coding",
                "Consider edge cases and error handling",
                "Optimize after getting a working solution",
                "Test your code with examples",
            ],
            InterviewType.SYSTEM_DESIGN: [
                "Start with requirements clarification",
                "Draw diagrams to illustrate your design",
                "Consider scalability, reliability, and cost",
                "Discuss monitoring and security aspects",
            ],
        }
        return tips_map.get(question_type, ["Stay calm and take your time"])

    def _calculate_total_score(self, session: InterviewSession) -> float:
        """Calculate overall session score."""
        if not session.feedback:
            return 0.0

        scores = [f.score.overall for f in session.feedback]
        return sum(scores) / len(scores)

    async def _analyze_voice_characteristics(
        self, audio_data: bytes, transcription_text: str
    ) -> VoiceAnalytics:
        """Analyze voice characteristics from audio data."""
        # In a real implementation, this would use speech-to-text services
        # For now, we'll simulate basic analysis

        words = transcription_text.split()
        word_count = len(words)

        # Simulate duration (would get from actual audio processing)
        duration_seconds = len(audio_data) / 16000  # Assuming 16kHz sample rate

        # Calculate metrics
        average_words_per_minute = (
            (word_count / duration_seconds) * 60 if duration_seconds > 0 else 0
        )

        # Simulate clarity based on word count and structure
        clarity_score = min(1.0, word_count / 100) if word_count > 0 else 0.5

        # Simulate pace score
        pace_score = 0.8 if 100 <= average_words_per_minute <= 150 else 0.6

        # Simulate confidence score
        confidence_score = 0.7 if clarity_score > 0.6 else 0.5

        # Count filler words (simplified)
        filler_words = [
            "um",
            "uh",
            "er",
            "like",
            "you know",
            "basically",
            "actually",
            "so",
            "well",
            "but",
        ]
        filler_count = sum(1 for word in words if word.lower() in filler_words)

        # Determine speaking rate
        if average_words_per_minute < 100:
            speaking_rate = "slow"
        elif average_words_per_minute <= 150:
            speaking_rate = "normal"
        elif average_words_per_minute <= 200:
            speaking_rate = "fast"
        else:
            speaking_rate = "very fast"

        # Determine emotional tone (simplified)
        emotional_tone = (
            "neutral"  # Would use sentiment analysis in real implementation
        )

        return VoiceAnalytics(
            clarity_score=clarity_score,
            pace_score=pace_score,
            confidence_score=confidence_score,
            filler_words_count=filler_count,
            total_duration_seconds=duration_seconds,
            word_count=word_count,
            average_words_per_minute=average_words_per_minute,
            voice_quality_score=0.8,  # Simulated
            emotional_tone=emotional_tone,
            speaking_rate=speaking_rate,
        )

    def get_session_summary(self, session: InterviewSession) -> Dict[str, Any]:
        """Get a comprehensive summary of the interview session."""
        if session.status != "completed":
            return {
                "status": "in_progress",
                "current_question": session.current_question_index + 1,
                "total_questions": len(session.questions),
            }

        category_scores: Dict[str, List[float]] = {}
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

    async def generate_voice_question(
        self, question: InterviewQuestion, voice_settings: VoiceSettings
    ) -> Dict[str, Any]:
        """Generate voice version of a question using text-to-speech."""
        # In a real implementation, this would call TTS service
        # For now, return metadata

        return {
            "question_id": question.id,
            "question_text": question.question,
            "audio_url": f"/api/voice-interviews/audio/{question.id}.mp3",
            "duration_seconds": len(question.question.split()) * 0.5,  # Estimated
            "voice_settings": voice_settings.dict(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def transcribe_audio(
        self, audio_data: bytes, voice_settings: VoiceSettings
    ) -> Dict[str, Any]:
        """Transcribe audio data using speech-to-text."""
        # In a real implementation, this would call STT service
        # For now, return simulated transcription

        # Simulate basic transcription
        simulated_text = "This is a simulated transcription of the audio response."

        return {
            "transcription": simulated_text,
            "confidence": 0.85,
            "duration_seconds": len(audio_data) / 16000,
            "language": voice_settings.language,
            "transcribed_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for voice features."""
        return [
            "en-US",
            "en-GB",
            "en-AU",
            "en-CA",
            "en-IN",
            "en-IE",
            "es-ES",
            "fr-FR",
            "de-DE",
            "it-IT",
            "pt-BR",
            "zh-CN",
            "ja-JP",
            "ko-KR",
        ]

    def get_voice_capabilities(self) -> Dict[str, Any]:
        """Get voice system capabilities."""
        return {
            "speech_to_text": {
                "supported": True,
                "providers": ["openai_whisper", "azure_speech", "google_speech"],
                "languages": self.get_supported_languages(),
                "formats": ["mp3", "wav", "m4a", "flac"],
                "real_time": True,
            },
            "text_to_speech": {
                "supported": True,
                "providers": ["openai_tts", "azure_tts", "google_tts"],
                "voices": ["alloy", "nova", "echo", "onyx"],
                "languages": self.get_supported_languages(),
                "formats": ["mp3"],
                "real_time": True,
            },
            "voice_analytics": {
                "supported": True,
                "features": [
                    "clarity_detection",
                    "pace_analysis",
                    "confidence_scoring",
                    "emotional_tone",
                    "speaking_rate",
                    "filler_word_detection",
                    "pause_detection",
                    "voice_quality_scoring",
                ],
                "accuracy": "high",
                "real_time": True,
            },
        }
