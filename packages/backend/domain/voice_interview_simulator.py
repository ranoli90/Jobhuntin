"""Voice-Enhanced Interview Simulator.

Implements voice interaction capabilities for the interview simulator:
- Speech-to-text for user responses
- Text-to-speech for AI questions
- Real-time voice feedback
- Voice analytics and scoring
- Natural conversation flow
- Voice-based question generation

Key features:
1. Speech recognition and synthesis
2. Voice analytics (pace, clarity, confidence)
3. Real-time voice feedback
4. Natural conversation interface
5. Voice-based question generation
6. Performance metrics tracking
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.domain.interview_simulator import (
    InterviewPhase,
    InterviewQuestion,
    InterviewType,
    QuestionDifficulty,
    QuestionFeedback,
    UserResponse,
    get_interview_simulator,
)
from backend.llm.client import LLMClient
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.voice_interview_simulator")


class VoiceAnalytics(BaseModel):
    """Voice analytics data for user responses."""

    clarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    pace_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    filler_words_count: int = Field(default=0)
    pause_count: int = Field(default=0)
    total_duration_seconds: float = Field(default=0.0)
    word_count: int = Field(default=0)
    average_words_per_minute: float = Field(default=0.0)
    voice_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    emotional_tone: str = Field(default="neutral")
    speaking_rate: str = Field(default="normal")


class VoiceInterviewSession(BaseModel):
    """Enhanced interview session with voice capabilities."""

    session_id: str
    user_id: str
    job_id: str
    company: str
    job_title: str
    interview_type: InterviewType
    difficulty: QuestionDifficulty
    questions: list[InterviewQuestion]
    responses: list[UserResponse]
    feedback: list[QuestionFeedback]
    voice_responses: list[Dict[str, Any]] = Field(default_factory=list)
    voice_analytics: list[VoiceAnalytics] = Field(default_factory=list)
    current_phase: InterviewPhase = InterviewPhase.INTRODUCTION
    current_question_index: int = 0
    total_score: float = 0.0
    voice_enabled: bool = True
    voice_settings: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = "in_progress"

    class Config:
        arbitrary_types_allowed = True


class VoiceInterviewSimulator:
    """Voice-enhanced interview simulator.

    Provides natural voice interaction for interview preparation:
    - Speech-to-text for user responses
    - Text-to-speech for AI questions
    - Voice analytics and feedback
    - Natural conversation flow
    - Real-time voice scoring
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm_client = llm_client
        self._settings = get_settings()
        self._base_simulator = get_interview_simulator()

        # Voice service configuration
        self._voice_service_config = {
            "speech_to_text": {
                "provider": "openai_whisper",  # or "azure_speech", "google_speech"
                "language": "en-US",
                "model": "whisper-1",
                "timeout": 30,
            },
            "text_to_speech": {
                "provider": "openai_tts",  # or "azure_tts", "google_tts"
                "voice": "alloy",  # Professional, clear voice
                "speed": 1.0,  # Normal speaking pace
                "pitch": 0.0,  # Natural pitch
                "language": "en-US",
            },
            "voice_analytics": {
                "enable_clarity_detection": True,
                "enable_pace_analysis": True,
                "enable_confidence_scoring": True,
                "enable_emotional_tone": True,
                "enable_speaking_rate": True,
            },
        }

        # Voice analytics thresholds
        self._analytics_thresholds = {
            "clarity": {
                "excellent": 0.8,
                "good": 0.6,
                "fair": 0.4,
                "poor": 0.2,
            },
            "pace": {
                "slow": 100,  # words per minute
                "normal": 150,
                "fast": 200,
                "very_fast": 250,
            },
            "confidence": {
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4,
                "very_low": 0.2,
            },
        }

    @property
    def llm(self) -> LLMClient:
        """Get LLM client instance."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self._settings)
        return self._llm_client

    async def create_voice_session(
        self,
        user_id: str,
        job_id: str,
        company: str,
        job_title: str,
        job_description: str,
        user_profile: Dict[str, Any],
        interview_type: InterviewType = InterviewType.GENERAL,
        difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM,
        question_count: int = 10,
        voice_settings: Optional[Dict[str, Any]] = None,
    ) -> VoiceInterviewSession:
        """Create a new voice-enabled interview session.

        Args:
            user_id: User identifier
            job_id: Job identifier
            company: Company name
            job_title: Job title
            job_description: Job description
            user_profile: User profile data
            interview_type: Type of interview
            difficulty: Question difficulty level
            question_count: Number of questions
            voice_settings: Voice configuration settings

        Returns:
            Voice-enabled interview session
        """
        # Create base session
        base_session = await self._base_simulator.create_session(
            user_id=user_id,
            job_id=job_id,
            company=company,
            job_title=job_title,
            job_description=job_description,
            user_profile=user_profile,
            interview_type=interview_type,
            difficulty=difficulty,
            question_count=question_count,
        )

        # Create voice-enhanced session
        voice_session = VoiceInterviewSession(
            session_id=base_session.session_id,
            user_id=base_session.user_id,
            job_id=base_session.job_id,
            company=base_session.company,
            job_title=base_session.job_title,
            interview_type=base_session.interview_type,
            difficulty=base_session.difficulty,
            questions=base_session.questions,
            responses=base_session.responses,
            feedback=base_session.feedback,
            voice_enabled=True,
            voice_settings=voice_settings or self._voice_service_config,
        )

        return voice_session

    async def start_voice_question(
        self,
        session: VoiceInterviewSession,
        question_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Start a voice question with text-to-speech.

        Args:
            session: Voice interview session
            question_index: Optional question index (defaults to current)

        Returns:
            Voice question start response
        """
        if question_index is None:
            question_index = session.current_question_index

        if question_index >= len(session.questions):
            return {
                "success": False,
                "error": "No more questions available",
                "session_status": session.status,
            }

        question = session.questions[question_index]

        try:
            # Generate voice audio for the question
            audio_data = await self._text_to_speech(
                text=question.question,
                voice_settings=session.voice_settings.get("text_to_speech", {}),
            )

            # Update session state
            session.current_question_index = question_index
            session.current_phase = question.phase

            return {
                "success": True,
                "question_id": question.id,
                "question_text": question.question,
                "question_type": question.question_type.value,
                "difficulty": question.difficulty.value,
                "phase": question.phase.value,
                "time_limit_seconds": question.time_limit_seconds,
                "audio_data": audio_data,
                "audio_format": "mp3",
                "session_status": session.status,
                "voice_enabled": session.voice_enabled,
            }

        except Exception as e:
            logger.error(f"Failed to generate voice for question {question.id}: {e}")
            return {
                "success": False,
                "error": f"Voice generation failed: {str(e)}",
                "question_id": question.id,
                "session_status": session.status,
            }

    async def transcribe_voice_response(
        self,
        session: VoiceInterviewSession,
        audio_data: bytes,
        audio_format: str = "mp3",
    ) -> Dict[str, Any]:
        """Transcribe voice response to text.

        Args:
            session: Voice interview session
            audio_data: Audio data bytes
            audio_format: Audio format (mp3, wav, etc.)

        Returns:
            Transcription result with analytics
        """
        try:
            # Transcribe audio to text
            transcription_result = await self._speech_to_text(
                audio_data=audio_data,
                audio_format=audio_format,
                voice_settings=session.voice_settings.get("speech_to_text", {}),
            )

            # Analyze voice characteristics
            voice_analytics = await self._analyze_voice_characteristics(
                audio_data=audio_data,
                transcription_text=transcription_result.get("text", ""),
                voice_settings=session.voice_settings.get("voice_analytics", {}),
            )

            # Create response object
            response = UserResponse(
                question_id=session.questions[session.current_question_index].id,
                response_text=transcription_result.get("text", ""),
                response_time_seconds=transcription_result.get("duration", 0.0),
                keywords_hit=[],  # Will be filled by base simulator
                missed_keywords=[],  # Will be filled by base simulator
            )

            # Add voice response to session
            voice_response = {
                "question_id": response.question_id,
                "transcribed_text": response.response_text,
                "confidence": transcription_result.get("confidence", 0.0),
                "duration_seconds": transcription_result.get("duration", 0.0),
                "voice_analytics": voice_analytics.model_dump(),
                "audio_format": audio_format,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            session.voice_responses.append(voice_response)
            session.voice_analytics.append(voice_analytics)

            # Submit to base simulator for feedback
            feedback = await self._base_simulator.submit_response(
                session=session,
                response_text=response.response_text,
                response_time_seconds=response.response_time_seconds,
            )

            session.feedback.append(feedback)
            session.responses.append(response)

            # Update session state
            session.current_question_index += 1
            if session.current_question_index >= len(session.questions):
                session.status = "completed"
                session.completed_at = datetime.now(timezone.utc)
                session.total_score = self._base_simulator._calculate_total_score(
                    session
                )

            return {
                "success": True,
                "transcribed_text": response.response_text,
                "confidence": transcription_result.get("confidence", 0.0),
                "duration_seconds": transcription_result.get("duration", 0.0),
                "voice_analytics": voice_analytics.model_dump(),
                "feedback": feedback.model_dump(),
                "session_status": session.status,
                "current_question_index": session.current_question_index,
                "total_questions": len(session.questions),
            }

        except Exception as e:
            logger.error(f"Voice transcription failed: {e}")
            return {
                "success": False,
                "error": f"Voice transcription failed: {str(e)}",
                "session_status": session.status,
            }

    async def _text_to_speech(
        self,
        text: str,
        voice_settings: Dict[str, Any],
    ) -> bytes:
        """Convert text to speech using TTS service.

        Args:
            text: Text to convert
            voice_settings: Voice configuration

        Returns:
            Audio data bytes
        """
        # TODO: Implement actual TTS service integration
        # For now, return placeholder audio data

        # In production, this would integrate with:
        # - OpenAI TTS API
        # - Azure Speech Service
        # - Google Cloud Text-to-Speech
        # - AWS Polly

        # Placeholder implementation
        logger.info(f"Converting text to speech: {text[:50]}...")

        # Return empty bytes for now
        return b""

    async def _speech_to_text(
        self,
        audio_data: bytes,
        audio_format: str,
        voice_settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Convert speech to text using STT service.

        Args:
            audio_data: Audio data bytes
            audio_format: Audio format
            voice_settings: Voice configuration

        Returns:
            Transcription result
        """
        # TODO: Implement actual STT service integration
        # For now, return placeholder result

        # In production, this would integrate with:
        # - OpenAI Whisper API
        # - Azure Speech Service
        # - Google Cloud Speech-to-Text
        # - AssemblyAI

        # Placeholder implementation
        logger.info(f"Transcribing audio ({len(audio_data)} bytes, {audio_format})")

        return {
            "text": "This is a placeholder transcription of the voice response.",
            "confidence": 0.9,
            "duration": 15.0,
            "language": voice_settings.get("language", "en-US"),
            "provider": "placeholder",
        }

    async def _analyze_voice_characteristics(
        self,
        audio_data: bytes,
        transcription_text: str,
        voice_settings: Dict[str, Any],
    ) -> VoiceAnalytics:
        """Analyze voice characteristics from audio and transcription.

        Args:
            audio_data: Audio data bytes
            transcription_text: Transcribed text
            voice_settings: Voice configuration

        Returns:
            Voice analytics results
        """
        # Calculate word count and speaking rate
        words = transcription_text.split()
        word_count = len(words)
        duration_seconds = (
            len(audio_data) / 16000
        )  # Approximate: 16KB per second for mp3

        average_words_per_minute = (
            (word_count / duration_seconds) * 60 if duration_seconds > 0 else 0
        )

        # Analyze speaking pace
        pace_score = self._calculate_pace_score(average_words_per_minute)

        # Detect filler words
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

        # Estimate clarity (placeholder - would use audio analysis in production)
        clarity_score = 0.8 if filler_count < 3 else 0.6 if filler_count < 6 else 0.4

        # Estimate confidence (placeholder - would use audio analysis in production)
        confidence_score = 0.8 if clarity_score > 0.7 else 0.6

        # Estimate voice quality (placeholder)
        voice_quality_score = 0.8

        # Detect emotional tone (placeholder - would use audio analysis in production)
        emotional_tone = "neutral"
        if any(word in ["excited", "happy", "great", "amazing"] for word in words):
            emotional_tone = "positive"
        elif any(
            word in ["nervous", "anxious", "worried", "concerned"] for word in words
        ):
            emotional_tone = "anxious"

        # Determine speaking rate category
        speaking_rate = "normal"
        if average_words_per_minute < self._analytics_thresholds["pace"]["slow"]:
            speaking_rate = "slow"
        elif average_words_per_minute > self._analytics_thresholds["pace"]["fast"]:
            speaking_rate = "fast"

        return VoiceAnalytics(
            clarity_score=clarity_score,
            pace_score=pace_score,
            confidence_score=confidence_score,
            filler_words_count=filler_count,
            pause_count=0,  # Would be detected from audio analysis
            total_duration_seconds=duration_seconds,
            word_count=word_count,
            average_words_per_minute=average_words_per_minute,
            voice_quality_score=voice_quality_score,
            emotional_tone=emotional_tone,
            speaking_rate=speaking_rate,
        )

    def _calculate_pace_score(self, words_per_minute: float) -> float:
        """Calculate speaking pace score."""
        if words_per_minute >= self._analytics_thresholds["pace"]["normal"] - 20:
            return 1.0  # Ideal pace
        elif words_per_minute >= self._analytics_thresholds["pace"]["slow"] - 20:
            return 0.8  # Slightly slow
        elif words_per_minute <= self._analytics_thresholds["pace"]["slow"]:
            return 0.6  # Too slow
        elif words_per_minute >= self._analytics_thresholds["pace"]["fast"]:
            return 0.7  # Too fast
        else:
            return 0.5  # Very fast

    async def generate_voice_question(
        self,
        session: VoiceInterviewSession,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a voice question using LLM.

        Args:
            session: Voice interview session
            context: Additional context for question generation

        Returns:
            Generated voice question
        """
        try:
            # Get current question
            if session.current_question_index >= len(session.questions):
                return {
                    "success": False,
                    "error": "No more questions available",
                    "session_status": session.status,
                }

            current_question = session.questions[session.current_question_index]

            # Generate contextual question if needed
            if context and "voice_context" in context:
                prompt = f"""
                Generate a natural, conversational interview question based on the context:
                
                Current Question: {current_question.question}
                Interview Type: {current_question.question_type.value}
                Difficulty: {current_question.difficulty.value}
                Phase: {current_question.phase.value}
                
                Voice Context: {context.get("voice_context", "")}
                Previous Responses: {[r.get("transcribed_text", "") for r in session.voice_responses[-2:]]}
                
                Generate a follow-up question that:
                1. Is natural and conversational
                2. Builds on the previous response
                3. Maintains the interview flow
                4. Is appropriate for the interview type
                5. Is suitable for voice interaction
                
                Return only the question text, no additional formatting.
                """

                result = await self.llm.call(prompt=prompt, response_format=None)
                if isinstance(result, str):
                    generated_question = result.strip()
                else:
                    generated_question = current_question.question
            else:
                generated_question = current_question.question

            # Generate voice audio
            audio_data = await self._text_to_speech(
                text=generated_question,
                voice_settings=session.voice_settings.get("text_to_speech", {}),
            )

            return {
                "success": True,
                "question_id": current_question.id,
                "question_text": generated_question,
                "question_type": current_question.question_type.value,
                "difficulty": current_question.difficulty.value,
                "phase": current_question.phase.value,
                "time_limit_seconds": current_question.time_limit_seconds,
                "audio_data": audio_data,
                "audio_format": "mp3",
                "is_generated": generated_question != current_question.question,
                "session_status": session.status,
            }

        except Exception as e:
            logger.error(f"Failed to generate voice question: {e}")
            return {
                "success": False,
                "error": f"Voice question generation failed: {str(e)}",
                "session_status": session.status,
            }

    async def get_voice_session_summary(
        self,
        session: VoiceInterviewSession,
    ) -> Dict[str, Any]:
        """Get comprehensive voice session summary."""
        base_summary = self._base_simulator.get_session_summary(session)

        # Add voice-specific analytics
        if session.voice_analytics:
            avg_clarity = sum(a.clarity_score for a in session.voice_analytics) / len(
                session.voice_analytics
            )
            avg_pace = sum(a.pace_score for a in session.voice_analytics) / len(
                session.voice_analytics
            )
            avg_confidence = sum(
                a.confidence_score for a in session.voice_analytics
            ) / len(session.voice_analytics)
            avg_speaking_rate = len(
                [a for a in session.voice_analytics if a.speaking_rate == "normal"]
            ) / len(session.voice_analytics)

            total_filler_words = sum(
                a.filler_words_count for a in session.voice_analytics
            )
            total_duration = sum(
                a.total_duration_seconds for a in session.voice_analytics
            )
            avg_words_per_minute = sum(
                a.average_words_per_minute for a in session.voice_analytics
            ) / len(session.voice_analytics)

            voice_summary = {
                "average_clarity_score": avg_clarity,
                "average_pace_score": avg_pace,
                "average_confidence_score": avg_confidence,
                "average_speaking_rate": avg_speaking_rate,
                "total_filler_words": total_filler_words,
                "total_voice_duration_seconds": total_duration,
                "average_words_per_minute": avg_words_per_minute,
                "voice_quality_distribution": {
                    "excellent": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.voice_quality_score >= 0.8
                        ]
                    ),
                    "good": len(
                        [
                            a
                            for a in session.voice_analytics
                            if 0.6 <= a.voice_quality_score < 0.8
                        ]
                    ),
                    "fair": len(
                        [
                            a
                            for a in session.voice_analytics
                            if 0.4 <= a.voice_quality_score < 0.6
                        ]
                    ),
                    "poor": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.voice_quality_score < 0.4
                        ]
                    ),
                },
                "emotional_tone_distribution": {
                    "positive": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.emotional_tone == "positive"
                        ]
                    ),
                    "neutral": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.emotional_tone == "neutral"
                        ]
                    ),
                    "anxious": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.emotional_tone == "anxious"
                        ]
                    ),
                    "negative": len(
                        [
                            a
                            for a in session.session.voice_analytics
                            if a.emotional_tone == "negative"
                        ]
                    ),
                },
                "speaking_rate_distribution": {
                    "slow": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.speaking_rate == "slow"
                        ]
                    ),
                    "normal": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.speaking_rate == "normal"
                        ]
                    ),
                    "fast": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.speaking_rate == "fast"
                        ]
                    ),
                    "very_fast": len(
                        [
                            a
                            for a in session.voice_analytics
                            if a.speaking_rate == "very_fast"
                        ]
                    ),
                },
            }
        else:
            voice_summary = {
                "voice_enabled": False,
                "voice_analytics": None,
            }

        # Combine with base summary
        base_summary.update(
            {
                "voice_enabled": session.voice_enabled,
                "voice_settings": session.voice_settings,
                "voice_responses_count": len(session.voice_responses),
                "voice_summary": voice_summary,
            }
        )

        return base_summary

    async def update_voice_settings(
        self,
        session: VoiceInterviewSession,
        voice_settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update voice settings for the session.

        Args:
            session: Voice interview session
            voice_settings: New voice configuration

        Returns:
            Updated session status
        """
        session.voice_settings.update(voice_settings)

        return {
            "success": True,
            "voice_settings": session.voice_settings,
            "session_status": session.status,
        }

    async def toggle_voice_mode(
        self,
        session: VoiceInterviewSession,
    ) -> Dict[str, Any]:
        """Toggle voice mode on/off for the session.

        Args:
            session: Voice interview session

        Returns:
            Updated session status
        """
        session.voice_enabled = not session.voice_enabled

        return {
            "success": True,
            "voice_enabled": session.voice_enabled,
            "session_status": session.status,
        }

    async def get_voice_analytics_report(
        self,
        session: VoiceInterviewSession,
    ) -> Dict[str, Any]:
        """Get detailed voice analytics report.

        Args:
            session: Voice interview session

        Returns:
            Comprehensive voice analytics report
        """
        if not session.voice_analytics:
            return {
                "session_id": session.session_id,
                "voice_enabled": session.voice_enabled,
                "analytics_available": False,
            }

        # Calculate analytics trends
        clarity_trend = [a.clarity_score for a in session.voice_analytics]
        pace_trend = [a.pace_score for a in session.voice_analytics]
        confidence_trend = [a.confidence_score for a in session.voice_analytics]

        # Calculate improvements
        if len(clarity_trend) > 1:
            clarity_improvement = clarity_trend[-1] - clarity_trend[0]
        else:
            clarity_improvement = 0.0

        if len(pace_trend) > 1:
            pace_improvement = pace_trend[-1] - pace_trend[0]
        else:
            pace_improvement = 0.0

        if len(confidence_trend) > 1:
            confidence_improvement = confidence_trend[-1] - confidence_trend[0]
        else:
            confidence_improvement = 0.0

        return {
            "session_id": session.session_id,
            "voice_enabled": session.voice_enabled,
            "total_responses": len(session.voice_analytics),
            "analytics_trends": {
                "clarity": clarity_trend,
                "pace": pace_trend,
                "confidence": confidence_trend,
            },
            "improvements": {
                "clarity_improvement": clarity_improvement,
                "pace_improvement": pace_improvement,
                "confidence_improvement": confidence_improvement,
            },
            "average_scores": {
                "clarity": sum(clarity_trend) / len(clarity_trend)
                if clarity_trend
                else 0.0,
                "pace": sum(pace_trend) / len(pace_trend) if pace_trend else 0.0,
                "confidence": sum(confidence_trend) / len(confidence_trend)
                if confidence_trend
                else 0.0,
            },
            "recommendations": self._generate_voice_recommendations(session),
        }

    def _generate_voice_recommendations(
        self,
        session: VoiceInterviewSession,
    ) -> List[str]:
        """Generate voice improvement recommendations."""
        recommendations = []

        if not session.voice_analytics:
            return ["Enable voice mode to get personalized recommendations"]

        avg_clarity = sum(a.clarity_score for a in session.voice_analytics) / len(
            session.voice_analytics
        )
        avg_pace = sum(a.pace_score for a in session.voice_analytics) / len(
            session.voice_analytics
        )
        avg_confidence = sum(a.confidence_score for a in session.voice_analytics) / len(
            session.voice_analytics
        )

        if avg_clarity < 0.6:
            recommendations.append("Speak more clearly and avoid mumbling")
            recommendations.append("Practice enunciation of technical terms")
            recommendations.append("Record yourself and listen back for clarity")

        if avg_pace < 0.6:
            recommendations.append("Slow down your speaking pace")
            recommendations.append("Take brief pauses to organize thoughts")
            recommendations.append("Practice with a metronome")

        if avg_confidence < 0.6:
            recommendations.append("Practice answering common interview questions")
            recommendations.append("Record yourself and review for confidence")
            recommendations.append("Focus on your key strengths and experiences")

        if (
            sum(a.filler_words_count for a in session.voice_analytics)
            / len(session.voice_analytics)
            > 5
        ):
            recommendations.append(
                "Practice reducing filler words (um, uh, like, you know)"
            )
            recommendations.append("Take a moment to think before speaking")
            recommendations.append("Practice brief pauses instead of filler words")

        if recommendations:
            recommendations.append(
                "Consider voice coaching for professional development"
            )

        return recommendations


_voice_interview_simulator: Optional[VoiceInterviewSimulator] = None


def get_voice_interview_simulator() -> VoiceInterviewSimulator:
    """Get or create the singleton voice interview simulator."""
    global _voice_interview_simulator
    if _voice_interview_simulator is None:
        _voice_interview_simulator = VoiceInterviewSimulator()
    return _voice_interview_simulator
