"""AI-Powered User Onboarding System.

Implements intelligent onboarding with adaptive question flow:
- Personalized question generation based on user profile
- Adaptive question sequencing based on responses
- AI-powered question recommendations
- Context-aware onboarding experience
- Intelligent completion detection
- Personalized next steps suggestions

Key features:
1. AI-generated onboarding questions
2. Adaptive question flow based on user responses
3. Contextual question recommendations
4. Intelligent completion detection
5. Personalized onboarding experience
6. Integration with existing AI systems
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

logger = get_logger("sorce.ai_onboarding")


class QuestionType(StrEnum):
    """Types of onboarding questions."""

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


class QuestionComplexity(StrEnum):
    """Complexity levels for onboarding questions."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class OnboardingQuestion(BaseModel):
    """AI-generated onboarding question."""

    id: str = Field(..., description="Question unique identifier")
    question_text: str = Field(..., description="Question text")
    question_type: QuestionType = Field(..., description="Type of question")
    complexity: QuestionComplexity = Field(..., description="Question complexity")
    category: str = Field(..., description="Question category")
    description: Optional[str] = Field(
        default=None, description="Additional description"
    )
    placeholder: Optional[str] = Field(default=None, description="Input placeholder")
    options: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Question options"
    )
    required: bool = Field(default=True, description="Whether question is required")
    validation_rules: Optional[Dict[str, Any]] = Field(
        default=None, description="Validation rules"
    )
    conditional_logic: Optional[Dict[str, Any]] = Field(
        default=None, description="Conditional logic"
    )
    ai_generated: bool = Field(
        default=True, description="Whether question was AI-generated"
    )
    context_data: Optional[Dict[str, Any]] = Field(
        default=None, description="AI context data"
    )
    priority: int = Field(default=5, description="Question priority (1-10)")
    estimated_time_seconds: int = Field(
        default=30, description="Estimated time to answer"
    )
    help_text: Optional[str] = Field(default=None, description="Help text for user")


class OnboardingSession(BaseModel):
    """User onboarding session."""

    session_id: str = Field(..., description="Session unique identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    current_step: int = Field(default=0, description="Current step in onboarding")
    total_steps: int = Field(default=10, description="Total estimated steps")
    questions: List[OnboardingQuestion] = Field(
        default_factory=list, description="Generated questions"
    )
    responses: Dict[str, Any] = Field(
        default_factory=dict, description="User responses"
    )
    user_profile: Dict[str, Any] = Field(
        default_factory=dict, description="Built user profile"
    )
    completion_percentage: float = Field(
        default=0.0, description="Completion percentage"
    )
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp"
    )
    adaptive_mode: bool = Field(
        default=True, description="Whether adaptive mode is enabled"
    )
    ai_confidence: float = Field(
        default=0.8, description="AI confidence in question generation"
    )
    next_suggestions: List[str] = Field(
        default_factory=list, description="AI-generated next steps"
    )


class AIOnboardingFlow(BaseModel):
    """AI-powered onboarding flow configuration."""

    flow_id: str = Field(..., description="Flow unique identifier")
    flow_name: str = Field(..., description="Flow name")
    target_audience: str = Field(..., description="Target audience")
    question_categories: List[str] = Field(..., description="Question categories")
    complexity_progression: List[QuestionComplexity] = Field(
        ..., description="Complexity progression"
    )
    adaptive_rules: Dict[str, Any] = Field(..., description="Adaptive flow rules")
    completion_criteria: Dict[str, Any] = Field(..., description="Completion criteria")
    ai_prompts: Dict[str, str] = Field(..., description="AI generation prompts")
    integration_points: List[str] = Field(
        ..., description="Integration points with other systems"
    )


class AIOboardingManager:
    """AI-powered onboarding manager with adaptive question flow.

    Uses AI to generate personalized onboarding experiences:
    - Adaptive question generation based on user context
    - Intelligent question sequencing
    - Context-aware completion detection
    - Personalized next steps recommendations
    - Integration with existing AI systems
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm_client = llm_client
        self._settings = get_settings()

        # Onboarding flow configurations
        self._onboarding_flows = self._initialize_onboarding_flows()

        # Question templates and patterns
        self._question_templates = self._initialize_question_templates()

        # AI prompt templates
        self._ai_prompts = self._initialize_ai_prompts()

        # Adaptive rules engine
        self._adaptive_rules = self._initialize_adaptive_rules()

    @property
    def llm(self) -> LLMClient:
        """Get LLM client instance."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self._settings)
        return self._llm_client

    async def create_onboarding_session(
        self,
        user_id: str,
        tenant_id: str,
        flow_type: str = "professional",
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> OnboardingSession:
        """Create a new AI-powered onboarding session.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            flow_type: Type of onboarding flow
            initial_context: Initial user context

        Returns:
            Created onboarding session
        """
        try:
            import uuid

            session_id = str(uuid.uuid4())

            # Get onboarding flow configuration
            flow_config = self._get_flow_config(flow_type)

            # Generate initial questions using AI
            questions = await self._generate_initial_questions(
                user_id=user_id,
                tenant_id=tenant_id,
                flow_config=flow_config,
                initial_context=initial_context,
            )

            # Create session
            session = OnboardingSession(
                session_id=session_id,
                user_id=user_id,
                tenant_id=tenant_id,
                questions=questions,
                total_steps=len(questions),
                adaptive_mode=flow_config.adaptive_rules.get("enabled", True),
                ai_confidence=0.8,
            )

            return session

        except Exception as e:
            logger.error(f"Failed to create onboarding session: {e}")
            raise

    async def get_next_question(
        self,
        session: OnboardingSession,
        current_responses: Optional[Dict[str, Any]] = None,
    ) -> Optional[OnboardingQuestion]:
        """Get the next question in the onboarding flow.

        Args:
            session: Current onboarding session
            current_responses: Updated user responses

        Returns:
            Next question or None if complete
        """
        try:
            # Update responses if provided
            if current_responses:
                session.responses.update(current_responses)
                session.last_activity = datetime.now(timezone.utc)

            # Check if onboarding is complete
            if await self._is_onboarding_complete(session):
                session.completed_at = datetime.now(timezone.utc)
                session.completion_percentage = 100.0
                return None

            # Get next question based on adaptive logic
            if session.adaptive_mode:
                next_question = await self._get_adaptive_next_question(session)
            else:
                next_question = await self._get_sequential_next_question(session)

            return next_question

        except Exception as e:
            logger.error(f"Failed to get next question: {e}")
            return None

    async def process_response(
        self,
        session: OnboardingSession,
        question_id: str,
        response: Any,
    ) -> Dict[str, Any]:
        """Process user response and update session.

        Args:
            session: Current onboarding session
            question_id: Question identifier
            response: User response

        Returns:
            Processing results with next steps
        """
        try:
            # Store response
            session.responses[question_id] = response
            session.last_activity = datetime.now(timezone.utc)

            # Update user profile based on response
            profile_update = await self._extract_profile_data(question_id, response)
            session.user_profile.update(profile_update)

            # Generate adaptive follow-up questions if needed
            follow_up_questions = []
            if session.adaptive_mode:
                follow_up_questions = await self._generate_follow_up_questions(
                    session, question_id, response
                )
                if follow_up_questions:
                    session.questions.extend(follow_up_questions)
                    session.total_steps = len(session.questions)

            # Update completion percentage
            session.completion_percentage = await self._calculate_completion_percentage(
                session
            )

            # Generate next step suggestions
            session.next_suggestions = await self._generate_next_suggestions(session)

            return {
                "success": True,
                "profile_update": profile_update,
                "follow_up_questions": len(follow_up_questions),
                "completion_percentage": session.completion_percentage,
                "next_suggestions": session.next_suggestions,
            }

        except Exception as e:
            logger.error(f"Failed to process response: {e}")
            return {"success": False, "error": str(e)}

    async def complete_onboarding(
        self,
        session: OnboardingSession,
    ) -> Dict[str, Any]:
        """Complete onboarding and generate final recommendations.

        Args:
            session: Onboarding session to complete

        Returns:
            Completion results with recommendations
        """
        try:
            session.completed_at = datetime.now(timezone.utc)
            session.completion_percentage = 100.0

            # Generate comprehensive user profile
            final_profile = await self._generate_final_profile(session)

            # Generate personalized recommendations
            recommendations = await self._generate_final_recommendations(session)

            # Generate next steps
            next_steps = await self._generate_comprehensive_next_steps(session)

            return {
                "success": True,
                "final_profile": final_profile,
                "recommendations": recommendations,
                "next_steps": next_steps,
                "session_duration": (
                    session.completed_at - session.started_at
                ).total_seconds(),
                "questions_answered": len(session.responses),
                "ai_confidence": session.ai_confidence,
            }

        except Exception as e:
            logger.error(f"Failed to complete onboarding: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_initial_questions(
        self,
        user_id: str,
        tenant_id: str,
        flow_config: AIOnboardingFlow,
        initial_context: Optional[Dict[str, Any]],
    ) -> List[OnboardingQuestion]:
        """Generate initial onboarding questions using AI."""
        try:
            # Build LLM prompt for question generation
            prompt = self._build_question_generation_prompt(
                flow_config=flow_config,
                initial_context=initial_context,
                question_count=10,
            )

            # Generate questions using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response into questions
                questions = await self._parse_llm_questions_response(result)

                # Add AI-generated metadata
                for i, question in enumerate(questions):
                    question.ai_generated = True
                    question.priority = i + 1
                    question.context_data = {
                        "flow_type": flow_config.flow_name,
                        "target_audience": flow_config.target_audience,
                        "generation_context": initial_context,
                    }

                return questions
            else:
                logger.error(f"Unexpected LLM response type: {type(result)}")
                return []

        except Exception as e:
            logger.error(f"Failed to generate initial questions: {e}")
            return []

    async def _get_adaptive_next_question(
        self,
        session: OnboardingSession,
    ) -> Optional[OnboardingQuestion]:
        """Get next question using adaptive logic."""
        try:
            # Find next unanswered question
            for i, question in enumerate(session.questions):
                if question.id not in session.responses:
                    # Check conditional logic
                    if await self._should_show_question(session, question):
                        return question

            return None

        except Exception as e:
            logger.error(f"Failed to get adaptive next question: {e}")
            return None

    async def _get_sequential_next_question(
        self,
        session: OnboardingSession,
    ) -> Optional[OnboardingQuestion]:
        """Get next question using sequential logic."""
        try:
            if session.current_step < len(session.questions):
                return session.questions[session.current_step]
            return None

        except Exception as e:
            logger.error(f"Failed to get sequential next question: {e}")
            return None

    async def _should_show_question(
        self,
        session: OnboardingSession,
        question: OnboardingQuestion,
    ) -> bool:
        """Check if question should be shown based on conditional logic."""
        try:
            if not question.conditional_logic:
                return True

            # Evaluate conditional logic
            logic = question.conditional_logic
            condition_type = logic.get("type", "always")

            if condition_type == "always":
                return True
            elif condition_type == "response_equals":
                field = logic.get("field")
                expected_value = logic.get("value")
                actual_value = session.responses.get(field)
                return actual_value == expected_value
            elif condition_type == "response_in":
                field = logic.get("field")
                expected_values = logic.get("values", [])
                actual_value = session.responses.get(field)
                return actual_value in expected_values
            elif condition_type == "profile_condition":
                # Complex profile-based conditions
                return await self._evaluate_profile_condition(session, logic)

            return True

        except Exception as e:
            logger.error(f"Failed to evaluate conditional logic: {e}")
            return True

    async def _generate_follow_up_questions(
        self,
        session: OnboardingSession,
        question_id: str,
        response: Any,
    ) -> List[OnboardingQuestion]:
        """Generate follow-up questions based on response."""
        try:
            # Check if follow-up is needed
            question = next((q for q in session.questions if q.id == question_id), None)
            if not question or not question.conditional_logic:
                return []

            # Build LLM prompt for follow-up questions
            prompt = self._build_follow_up_prompt(
                original_question=question,
                response=response,
                user_context=session.user_profile,
            )

            # Generate follow-up questions using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response into questions
                follow_ups = await self._parse_llm_questions_response(result)

                # Add metadata to follow-up questions
                for follow_up in follow_ups:
                    follow_up.conditional_logic = {
                        "type": "response_in",
                        "field": question_id,
                        "values": [response],
                    }
                    follow_up.ai_generated = True
                    follow_up.priority = 9  # High priority for follow-ups

                return follow_ups

            return []

        except Exception as e:
            logger.error(f"Failed to generate follow-up questions: {e}")
            return []

    async def _is_onboarding_complete(self, session: OnboardingSession) -> bool:
        """Check if onboarding is complete."""
        try:
            # Check if all required questions are answered
            required_questions = [q for q in session.questions if q.required]
            answered_required = [
                q for q in required_questions if q.id in session.responses
            ]

            # Check completion criteria
            completion_rate = (
                len(answered_required) / len(required_questions)
                if required_questions
                else 1.0
            )

            # Check AI confidence in completion
            ai_completion_score = await self._calculate_ai_completion_score(session)

            return completion_rate >= 0.8 and ai_completion_score >= 0.7

        except Exception as e:
            logger.error(f"Failed to check onboarding completion: {e}")
            return False

    async def _calculate_completion_percentage(
        self, session: OnboardingSession
    ) -> float:
        """Calculate onboarding completion percentage."""
        try:
            if not session.questions:
                return 0.0

            answered_questions = len(session.responses)
            total_questions = len(session.questions)

            base_completion = (answered_questions / total_questions) * 100

            # Adjust for adaptive questions
            if session.adaptive_mode:
                # Consider quality of responses
                response_quality = await self._calculate_response_quality(session)
                base_completion *= 0.7 + 0.3 * response_quality

            return min(base_completion, 100.0)

        except Exception as e:
            logger.error(f"Failed to calculate completion percentage: {e}")
            return 0.0

    async def _extract_profile_data(
        self,
        question_id: str,
        response: Any,
    ) -> Dict[str, Any]:
        """Extract profile data from question response."""
        try:
            # This would be enhanced with AI-based extraction
            profile_mapping = {
                "name": "full_name",
                "email": "email",
                "experience_years": "experience_years",
                "job_title": "current_job_title",
                "industry": "industry",
                "skills": "skills",
                "career_goals": "career_goals",
                "education": "education",
                "location": "location",
                "remote_preference": "remote_work_preference",
                "salary_expectation": "salary_expectation",
            }

            # Basic mapping - would be enhanced with AI
            if question_id in profile_mapping:
                return {profile_mapping[question_id]: response}

            return {}

        except Exception as e:
            logger.error(f"Failed to extract profile data: {e}")
            return {}

    async def _generate_next_suggestions(
        self,
        session: OnboardingSession,
    ) -> List[str]:
        """Generate AI-powered next step suggestions."""
        try:
            # Build LLM prompt for suggestions
            prompt = self._build_suggestions_prompt(
                user_profile=session.user_profile,
                responses=session.responses,
                completion_percentage=session.completion_percentage,
            )

            # Generate suggestions using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response
                suggestions = await self._parse_llm_suggestions_response(result)
                return suggestions

            return []

        except Exception as e:
            logger.error(f"Failed to generate next suggestions: {e}")
            return []

    def _build_question_generation_prompt(
        self,
        flow_config: AIOnboardingFlow,
        initial_context: Optional[Dict[str, Any]],
        question_count: int,
    ) -> str:
        """Build LLM prompt for question generation."""

        context_info = ""
        if initial_context:
            context_info = f"""
            Initial User Context:
            - Industry: {initial_context.get("industry", "Unknown")}
            - Experience Level: {initial_context.get("experience_level", "Unknown")}
            - Goals: {initial_context.get("goals", "Not specified")}
            """

        prompt = f"""
        Generate {question_count} personalized onboarding questions for {flow_config.target_audience}.

        Flow Configuration:
        - Target Audience: {flow_config.target_audience}
        - Question Categories: {", ".join(flow_config.question_categories)}
        - Complexity Progression: {", ".join(flow_config.complexity_progression)}

        {context_info}

        For each question, provide:
        1. Question text (clear and engaging)
        2. Question type (multiple_choice, text_input, textarea, select, checkboxes, radio, rating, boolean)
        3. Complexity level (basic, intermediate, advanced, expert)
        4. Category (from the specified categories)
        5. Required status (true/false)
        6. Options (for multiple choice, select, radio, checkboxes)
        7. Validation rules (if any)
        8. Estimated time to answer (seconds)
        9. Help text (if needed)

        Format as JSON array with objects containing all fields.
        Focus on questions that will help build a comprehensive user profile for job matching and career guidance.
        Make questions engaging and user-friendly.
        """

        return prompt

    def _build_follow_up_prompt(
        self,
        original_question: OnboardingQuestion,
        response: Any,
        user_context: Dict[str, Any],
    ) -> str:
        """Build LLM prompt for follow-up questions."""

        prompt = f"""
        Generate 1-3 follow-up questions based on the user's response.

        Original Question: {original_question.question_text}
        User Response: {response}
        User Context: {user_context}

        Generate follow-up questions that:
        1. Are directly relevant to the user's response
        2. Help gather more specific information
        3. Are not repetitive
        4. Maintain a conversational tone

        For each follow-up question, provide:
        1. Question text
        2. Question type
        3. Complexity level
        4. Category
        5. Required status
        6. Options (if applicable)
        7. Estimated time to answer

        Format as JSON array of objects.
        """

        return prompt

    def _build_suggestions_prompt(
        self,
        user_profile: Dict[str, Any],
        responses: Dict[str, Any],
        completion_percentage: float,
    ) -> str:
        """Build LLM prompt for next step suggestions."""

        prompt = f"""
        Generate 3-5 personalized next step suggestions based on user's onboarding progress.

        User Profile: {user_profile}
        Responses: {responses}
        Completion Percentage: {completion_percentage}%

        Generate suggestions that:
        1. Are relevant to the user's profile and goals
        2. Help them get the most value from the platform
        3. Are actionable and specific
        4. Consider their current completion status

        Format as JSON array of suggestion strings.
        """

        return prompt

    async def _parse_llm_questions_response(
        self, response: str
    ) -> List[OnboardingQuestion]:
        """Parse LLM response into onboarding questions."""
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON array found in LLM response")
                return []

            json_str = response[json_start:json_end]
            questions_data = json.loads(json_str)

            questions = []
            for i, question_data in enumerate(questions_data):
                try:
                    import uuid

                    question = OnboardingQuestion(
                        id=str(uuid.uuid4()),
                        question_text=question_data.get("question_text", ""),
                        question_type=QuestionType(
                            question_data.get("question_type", "text_input")
                        ),
                        complexity=QuestionComplexity(
                            question_data.get("complexity", "basic")
                        ),
                        category=question_data.get("category", "general"),
                        description=question_data.get("description"),
                        placeholder=question_data.get("placeholder"),
                        options=question_data.get("options"),
                        required=question_data.get("required", True),
                        validation_rules=question_data.get("validation_rules"),
                        estimated_time_seconds=question_data.get(
                            "estimated_time_to_answer", 30
                        ),
                        help_text=question_data.get("help_text"),
                    )
                    questions.append(question)
                except Exception as e:
                    logger.error(f"Failed to parse question data: {e}")
                    continue

            return questions

        except Exception as e:
            logger.error(f"Failed to parse LLM questions response: {e}")
            return []

    async def _parse_llm_suggestions_response(self, response: str) -> List[str]:
        """Parse LLM response into suggestions."""
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start == -1 or json_end == 0:
                # Fallback: extract lines that look like suggestions
                lines = response.split("\n")
                suggestions = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("[") and not line.startswith("]"):
                        # Remove numbering and quotes
                        clean_line = line
                        if clean_line[0].isdigit():
                            clean_line = ".".join(clean_line.split(".")[1:])
                        clean_line = clean_line.strip().strip("\"'")
                        if clean_line:
                            suggestions.append(clean_line)
                return suggestions[:5]

            json_str = response[json_start:json_end]
            suggestions = json.loads(json_str)

            return suggestions if isinstance(suggestions, list) else []

        except Exception as e:
            logger.error(f"Failed to parse LLM suggestions response: {e}")
            return []

    def _get_flow_config(self, flow_type: str) -> AIOnboardingFlow:
        """Get onboarding flow configuration."""
        return self._onboarding_flows.get(
            flow_type, self._onboarding_flows["professional"]
        )

    def _initialize_onboarding_flows(self) -> Dict[str, AIOnboardingFlow]:
        """Initialize onboarding flow configurations."""
        return {
            "professional": AIOnboardingFlow(
                flow_id="professional_onboarding",
                flow_name="Professional Career Onboarding",
                target_audience="Professionals seeking career advancement",
                question_categories=[
                    "personal_info",
                    "experience",
                    "skills",
                    "career_goals",
                    "preferences",
                    "education",
                    "industry",
                    "location",
                ],
                complexity_progression=[
                    QuestionComplexity.BASIC,
                    QuestionComplexity.INTERMEDIATE,
                    QuestionComplexity.ADVANCED,
                ],
                adaptive_rules={
                    "enabled": True,
                    "follow_up_threshold": 0.7,
                    "complexity_adjustment": True,
                },
                completion_criteria={
                    "min_required_answers": 8,
                    "profile_completeness": 0.8,
                    "ai_confidence_threshold": 0.7,
                },
                ai_prompts={
                    "question_generation": "professional_onboarding_questions",
                    "follow_up": "professional_follow_up",
                    "suggestions": "professional_suggestions",
                },
                integration_points=[
                    "skills_taxonomy",
                    "career_path",
                    "job_matching",
                    "resume_analysis",
                ],
            ),
            "student": AIOnboardingFlow(
                flow_id="student_onboarding",
                flow_name="Student Career Onboarding",
                target_audience="Students and recent graduates",
                question_categories=[
                    "education",
                    "skills",
                    "career_interests",
                    "internships",
                    "projects",
                    "goals",
                    "preferences",
                ],
                complexity_progression=[
                    QuestionComplexity.BASIC,
                    QuestionComplexity.INTERMEDIATE,
                ],
                adaptive_rules={
                    "enabled": True,
                    "follow_up_threshold": 0.6,
                    "complexity_adjustment": False,
                },
                completion_criteria={
                    "min_required_answers": 6,
                    "profile_completeness": 0.7,
                    "ai_confidence_threshold": 0.6,
                },
                ai_prompts={
                    "question_generation": "student_onboarding_questions",
                    "follow_up": "student_follow_up",
                    "suggestions": "student_suggestions",
                },
                integration_points=[
                    "skills_taxonomy",
                    "career_path",
                    "internship_matching",
                    "education_analysis",
                ],
            ),
            "career_changer": AIOnboardingFlow(
                flow_id="career_changer_onboarding",
                flow_name="Career Changer Onboarding",
                target_audience="Professionals changing careers",
                question_categories=[
                    "background",
                    "transferable_skills",
                    "target_industry",
                    "career_goals",
                    "education",
                    "timeline",
                    "preferences",
                ],
                complexity_progression=[
                    QuestionComplexity.BASIC,
                    QuestionComplexity.INTERMEDIATE,
                    QuestionComplexity.ADVANCED,
                    QuestionComplexity.EXPERT,
                ],
                adaptive_rules={
                    "enabled": True,
                    "follow_up_threshold": 0.8,
                    "complexity_adjustment": True,
                },
                completion_criteria={
                    "min_required_answers": 10,
                    "profile_completeness": 0.85,
                    "ai_confidence_threshold": 0.75,
                },
                ai_prompts={
                    "question_generation": "career_changer_questions",
                    "follow_up": "career_changer_follow_up",
                    "suggestions": "career_changer_suggestions",
                },
                integration_points=[
                    "skills_taxonomy",
                    "career_path",
                    "transition_analysis",
                    "skill_gap_analysis",
                ],
            ),
        }

    def _initialize_question_templates(self) -> Dict[str, Any]:
        """Initialize question templates."""
        return {
            "personal_info": {
                "name": {
                    "type": "text_input",
                    "complexity": "basic",
                    "required": True,
                    "validation": {"min_length": 2, "max_length": 100},
                },
                "email": {
                    "type": "text_input",
                    "complexity": "basic",
                    "required": True,
                    "validation": {"format": "email"},
                },
            },
            "experience": {
                "years_experience": {
                    "type": "select",
                    "complexity": "basic",
                    "required": True,
                    "options": ["0-1", "2-3", "4-6", "7-10", "11-15", "15+"],
                },
                "current_role": {
                    "type": "text_input",
                    "complexity": "basic",
                    "required": True,
                },
            },
            "skills": {
                "technical_skills": {
                    "type": "skills_assessment",
                    "complexity": "intermediate",
                    "required": True,
                },
                "soft_skills": {
                    "type": "checkboxes",
                    "complexity": "intermediate",
                    "required": False,
                },
            },
        }

    def _initialize_ai_prompts(self) -> Dict[str, str]:
        """Initialize AI prompt templates."""
        return {
            "question_generation": "Generate personalized onboarding questions based on user context and flow configuration.",
            "follow_up": "Generate relevant follow-up questions based on user responses.",
            "suggestions": "Generate personalized next step suggestions based on user profile and progress.",
            "profile_extraction": "Extract structured profile data from user responses.",
            "completion_analysis": "Analyze if onboarding is complete based on responses and profile quality.",
        }

    def _initialize_adaptive_rules(self) -> Dict[str, Any]:
        """Initialize adaptive rules engine."""
        return {
            "response_analysis": {
                "complexity_adjustment": True,
                "follow_up_threshold": 0.7,
                "skip_irrelevant": True,
            },
            "flow_optimization": {
                "dynamic_question_order": True,
                "conditional_branching": True,
                "early_completion": True,
            },
            "personalization": {
                "tone_adjustment": True,
                "context_awareness": True,
                "preference_learning": True,
            },
        }

    async def _calculate_response_quality(self, session: OnboardingSession) -> float:
        """Calculate quality of user responses."""
        try:
            if not session.responses:
                return 0.0

            quality_score = 0.0
            for question_id, response in session.responses.items():
                # Basic quality assessment
                if isinstance(response, str):
                    if len(response.strip()) > 0:
                        quality_score += 0.5
                    if len(response.strip()) > 10:
                        quality_score += 0.3
                    if len(response.strip()) > 50:
                        quality_score += 0.2
                elif response is not None:
                    quality_score += 0.8

            return min(quality_score / len(session.responses), 1.0)

        except Exception as e:
            logger.error(f"Failed to calculate response quality: {e}")
            return 0.5

    async def _calculate_ai_completion_score(self, session: OnboardingSession) -> float:
        """Calculate AI confidence in onboarding completion."""
        try:
            # Base score from completion percentage
            base_score = session.completion_percentage / 100.0

            # Adjust for profile completeness
            profile_completeness = await self._calculate_profile_completeness(
                session.user_profile
            )
            base_score *= 0.6 + 0.4 * profile_completeness

            # Adjust for response quality
            response_quality = await self._calculate_response_quality(session)
            base_score *= 0.7 + 0.3 * response_quality

            return min(base_score, 1.0)

        except Exception as e:
            logger.error(f"Failed to calculate AI completion score: {e}")
            return 0.5

    async def _calculate_profile_completeness(self, profile: Dict[str, Any]) -> float:
        """Calculate profile completeness score."""
        try:
            required_fields = [
                "full_name",
                "email",
                "experience_years",
                "industry",
                "skills",
                "career_goals",
            ]

            filled_fields = sum(1 for field in required_fields if profile.get(field))

            return filled_fields / len(required_fields)

        except Exception as e:
            logger.error(f"Failed to calculate profile completeness: {e}")
            return 0.0

    async def _generate_final_profile(
        self, session: OnboardingSession
    ) -> Dict[str, Any]:
        """Generate comprehensive final user profile."""
        try:
            # Combine all collected data
            final_profile = session.user_profile.copy()
            final_profile.update(session.responses)

            # Add AI-enhanced insights
            final_profile["ai_insights"] = {
                "completion_confidence": session.ai_confidence,
                "profile_completeness": await self._calculate_profile_completeness(
                    final_profile
                ),
                "response_quality": await self._calculate_response_quality(session),
                "onboarding_duration": (
                    session.completed_at - session.started_at
                ).total_seconds()
                if session.completed_at
                else 0,
            }

            return final_profile

        except Exception as e:
            logger.error(f"Failed to generate final profile: {e}")
            return session.user_profile

    async def _generate_final_recommendations(
        self, session: OnboardingSession
    ) -> List[Dict[str, Any]]:
        """Generate final recommendations based on onboarding."""
        try:
            # Build LLM prompt for recommendations
            prompt = f"""
            Generate personalized recommendations based on completed onboarding.

            User Profile: {session.user_profile}
            Responses: {session.responses}
            AI Insights: {session.ai_confidence} confidence

            Generate 3-5 recommendations that:
            1. Are specific and actionable
            2. Help user achieve their career goals
            3. Leverage platform features
            4. Are personalized to their profile

            Format as JSON array of objects with:
            - title: Recommendation title
            - description: Detailed description
            - priority: high/medium/low
            - action_items: List of specific actions
            """

            # Generate recommendations using LLM
            result = await self.llm.call(prompt=prompt, response_format=None)

            if isinstance(result, str):
                # Parse LLM response
                recommendations = await self._parse_llm_recommendations_response(result)
                return recommendations

            return []

        except Exception as e:
            logger.error(f"Failed to generate final recommendations: {e}")
            return []

    async def _generate_comprehensive_next_steps(
        self, session: OnboardingSession
    ) -> List[str]:
        """Generate comprehensive next steps."""
        try:
            # Combine existing suggestions with AI-generated ones
            base_steps = [
                "Complete your profile setup",
                "Upload your resume for AI analysis",
                "Explore personalized job recommendations",
                "Set up job alerts",
                "Try the interview simulator",
            ]

            # Add AI-generated suggestions
            ai_suggestions = await self._generate_next_suggestions(session)

            # Combine and deduplicate
            all_steps = base_steps + ai_suggestions
            unique_steps = list(
                dict.fromkeys(all_steps)
            )  # Preserve order, remove duplicates

            return unique_steps[:8]  # Limit to 8 steps

        except Exception as e:
            logger.error(f"Failed to generate comprehensive next steps: {e}")
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

            return recommendations if isinstance(recommendations, list) else []

        except Exception as e:
            logger.error(f"Failed to parse LLM recommendations response: {e}")
            return []

    async def _evaluate_profile_condition(
        self, session: OnboardingSession, logic: Dict[str, Any]
    ) -> bool:
        """Evaluate complex profile-based conditions."""
        try:
            condition_type = logic.get("condition")
            field = logic.get("field")
            operator = logic.get("operator", "equals")
            value = logic.get("value")

            actual_value = session.user_profile.get(field)

            if condition_type == "experience_level":
                if operator == "greater_than":
                    return actual_value > value
                elif operator == "less_than":
                    return actual_value < value
                elif operator == "equals":
                    return actual_value == value

            return True

        except Exception as e:
            logger.error(f"Failed to evaluate profile condition: {e}")
            return True


_ai_onboarding_manager: Optional[AIOboardingManager] = None


def get_ai_onboarding_manager() -> AIOboardingManager:
    """Get or create singleton AI onboarding manager."""
    global _ai_onboarding_manager
    if _ai_onboarding_manager is None:
        _ai_onboarding_manager = AIOboardingManager()
    return _ai_onboarding_manager
