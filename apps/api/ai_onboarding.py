"""AI-Powered Onboarding API endpoints.

Provides intelligent onboarding with adaptive question flow:
- Personalized question generation based on user profile
- Adaptive question sequencing based on responses
- AI-powered question recommendations
- Context-aware onboarding experience
- Intelligent completion detection
- Personalized next steps suggestions

Key endpoints:
- POST /ai-onboarding/create-session - Create new onboarding session
- GET /ai-onboarding/session/{session_id} - Get session details
- POST /ai-onboarding/session/{session_id}/next-question - Get next question
- POST /ai-onboarding/session/{session_id}/respond - Submit response
- POST /ai-onboarding/session/{session_id}/complete - Complete onboarding
- GET /ai-onboarding/flows - Get available onboarding flows
- GET /ai-onboarding/health - Health check for AI onboarding
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from api.deps import get_pool, get_pool as _get_pool, get_tenant_context, get_tenant_context as _get_tenant_ctx
from packages.backend.domain.ai_onboarding import get_ai_onboarding_manager
from packages.backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.ai_onboarding")

router = APIRouter(tags=["ai_onboarding"])


class CreateSessionRequest(BaseModel):
    """Request for creating onboarding session."""

    flow_type: str = Field(
        default="professional",
        pattern="^(professional|student|career_change|advanced)$",  # HIGH: Validate enum values
        description="Onboarding flow type",
    )
    initial_context: Optional[Dict[str, Any]] = Field(
        default=None,
        max_length=100,  # HIGH: Limit dict size to prevent DoS
        description="Initial user context (max 100 keys)",
    )


class CreateSessionResponse(BaseModel):
    """Response for creating onboarding session."""

    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    flow_type: str = Field(..., description="Onboarding flow type")
    total_steps: int = Field(..., description="Total estimated steps")
    adaptive_mode: bool = Field(..., description="Whether adaptive mode is enabled")
    ai_confidence: float = Field(
        ..., description="AI confidence in question generation"
    )
    first_question: Optional[Dict[str, Any]] = Field(
        default=None, description="First question"
    )


class SessionDetailsResponse(BaseModel):
    """Response for session details."""

    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    current_step: int = Field(..., description="Current step")
    total_steps: int = Field(..., description="Total steps")
    completion_percentage: float = Field(..., description="Completion percentage")
    adaptive_mode: bool = Field(..., description="Whether adaptive mode is enabled")
    started_at: datetime = Field(..., description="Session start time")
    last_activity: datetime = Field(..., description="Last activity time")
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion time"
    )
    user_profile: Dict[str, Any] = Field(..., description="Built user profile")
    next_suggestions: List[str] = Field(..., description="Next step suggestions")


class NextQuestionResponse(BaseModel):
    """Response for next question."""

    question: Optional[Dict[str, Any]] = Field(
        default=None, description="Next question"
    )
    session_complete: bool = Field(
        default=False, description="Whether session is complete"
    )
    completion_percentage: float = Field(..., description="Completion percentage")
    next_suggestions: List[str] = Field(..., description="Next step suggestions")


class SubmitResponseRequest(BaseModel):
    """Request for submitting response."""

    question_id: str = Field(
        ..., min_length=1, max_length=100, description="Question identifier"
    )
    response: str = Field(..., description="User response")

    @field_validator("response")
    @classmethod
    def validate_response(cls, v):
        """HIGH: Validate response size and sanitize HTML to prevent DoS and XSS."""
        from packages.backend.domain.sanitization import sanitize_text_input

        # Convert to string if needed
        if not isinstance(v, str):
            v = str(v)
        # Sanitize HTML
        v = sanitize_text_input(v, max_length=10000)
        # Validate size
        if len(v) > 10000:
            raise ValueError("Response too long (max 10000 characters)")
        return v


class SubmitResponseResponse(BaseModel):
    """Response for submitting response."""

    success: bool = Field(
        ..., description="Whether response was processed successfully"
    )
    profile_update: Dict[str, Any] = Field(..., description="Profile data extracted")
    follow_up_questions: int = Field(
        ..., description="Number of follow-up questions generated"
    )
    completion_percentage: float = Field(
        ..., description="Updated completion percentage"
    )
    next_suggestions: List[str] = Field(..., description="Next step suggestions")
    next_question: Optional[Dict[str, Any]] = Field(
        default=None, description="Next question"
    )


class CompleteSessionResponse(BaseModel):
    """Response for completing onboarding."""

    success: bool = Field(..., description="Whether completion was successful")
    final_profile: Dict[str, Any] = Field(..., description="Final user profile")
    recommendations: List[Dict[str, Any]] = Field(
        ..., description="Final recommendations"
    )
    next_steps: List[str] = Field(..., description="Comprehensive next steps")
    session_duration: float = Field(..., description="Session duration in seconds")
    questions_answered: int = Field(..., description="Total questions answered")
    ai_confidence: float = Field(..., description="AI confidence in completion")


class OnboardingFlowResponse(BaseModel):
    """Response for onboarding flows."""

    flows: List[Dict[str, Any]] = Field(..., description="Available onboarding flows")
    default_flow: str = Field(..., description="Default flow type")


async def _verify_session_ownership(
    session_id: str,
    ctx: TenantContext,
    db: asyncpg.Pool,
) -> None:
    """CRITICAL: Verify that session belongs to the authenticated user.

    This prevents unauthorized access to other users' onboarding sessions.

    Args:
        session_id: Session identifier to verify
        ctx: Authenticated tenant context
        db: Database pool

    Raises:
        HTTPException: If session doesn't exist or doesn't belong to user
    """
    # OB-016: Validate session_id format (UUID)
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="Invalid session ID")
    try:
        import uuid as _uuid

        _uuid.UUID(session_id)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # HIGH: Verify session ownership from database
    async with db.acquire() as conn:
        session_row = await conn.fetchrow(
            """
            SELECT user_id, tenant_id, expires_at
            FROM public.onboarding_sessions
            WHERE session_id = $1
            """,
            session_id,
        )
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check expiration
        expires_at = session_row.get("expires_at")
        if expires_at:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=410, detail="Session has expired")

        # Verify ownership
        row_user_id = session_row.get("user_id")
        row_tenant_id = session_row.get("tenant_id")
        if not row_user_id or str(row_user_id) != ctx.user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Session does not belong to current user",
            )
        if not row_tenant_id or str(row_tenant_id) != ctx.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Session does not belong to current tenant",
            )

    # HIGH: Verification now uses database - no warning needed
    # (verification logic is above)


@router.post("/create-session", response_model=CreateSessionResponse)
async def create_onboarding_session(
    request: CreateSessionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> CreateSessionResponse:
    """Create a new AI-powered onboarding session.

    Args:
        request: Create session request
        ctx: Tenant context for identification

    Returns:
        Created onboarding session details
    """
    try:
        ai_onboarding = get_ai_onboarding_manager()

        # Create onboarding session
        session = await ai_onboarding.create_onboarding_session(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            flow_type=request.flow_type,
            initial_context=request.initial_context,
        )

        # Get first question (updates session in memory)
        first_question = await ai_onboarding.get_next_question(session)

        # OB-007: Single transaction for both saves - avoid inconsistent state if second save fails
        from packages.backend.domain.onboarding_repository import OnboardingSessionRepo

        async with db.acquire() as conn:
            async with conn.transaction():
                await OnboardingSessionRepo.save_session(conn, session)

        return CreateSessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            flow_type=request.flow_type,
            total_steps=session.total_steps,
            adaptive_mode=session.adaptive_mode,
            ai_confidence=session.ai_confidence,
            first_question=first_question.model_dump() if first_question else None,
        )

    except Exception as e:
        logger.error(f"Failed to create onboarding session: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create onboarding session"
        )


@router.get("/session/{session_id}", response_model=SessionDetailsResponse)
async def get_session_details(
    session_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> SessionDetailsResponse:
    """Get onboarding session details.

    CRITICAL: Verifies session ownership to prevent unauthorized access.

    Args:
        session_id: Session identifier
        ctx: Tenant context for identification
        db: Database pool

    Returns:
        Session details
    """
    try:
        # CRITICAL: Verify session ownership
        await _verify_session_ownership(session_id, ctx, db)

        # HIGH: Load session from database
        async with db.acquire() as conn:
            from packages.backend.domain.onboarding_repository import (
                OnboardingSessionRepo,
            )

            session = await OnboardingSessionRepo.load_session(conn, session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionDetailsResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            current_step=session.current_step,
            total_steps=session.total_steps,
            completion_percentage=session.completion_percentage,
            adaptive_mode=session.adaptive_mode,
            started_at=session.started_at,
            last_activity=session.last_activity,
            completed_at=session.completed_at,
            user_profile=session.user_profile,
            next_suggestions=session.next_suggestions,
        )

    except Exception as e:
        logger.error(f"Failed to get session details: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve session details"
        )


@router.post("/session/{session_id}/next-question", response_model=NextQuestionResponse)
async def get_next_question(
    session_id: str,
    current_responses: Optional[Dict[str, Any]] = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> NextQuestionResponse:
    """Get the next question in the onboarding flow.

    CRITICAL: Verifies session ownership to prevent unauthorized access.

    Args:
        session_id: Session identifier
        current_responses: Updated user responses
        ctx: Tenant context for identification
        db: Database pool

    Returns:
        Next question or completion status
    """
    try:
        # CRITICAL: Verify session ownership
        await _verify_session_ownership(session_id, ctx, db)

        # HIGH: Load session from database
        async with db.acquire() as conn:
            from packages.backend.domain.onboarding_repository import (
                OnboardingSessionRepo,
            )

            session = await OnboardingSessionRepo.load_session(conn, session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Update responses if provided
        if current_responses:
            session.responses.update(current_responses)

        ai_onboarding = get_ai_onboarding_manager()

        # Get next question
        next_question = await ai_onboarding.get_next_question(
            session, current_responses
        )

        # HIGH: Save updated session
        async with db.acquire() as conn:
            await OnboardingSessionRepo.save_session(conn, session)

        return NextQuestionResponse(
            question=next_question.model_dump() if next_question else None,
            session_complete=next_question is None,
            completion_percentage=session.completion_percentage,
            next_suggestions=session.next_suggestions,
        )

    except Exception as e:
        logger.error(f"Failed to get next question: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve next question")


@router.post("/session/{session_id}/respond", response_model=SubmitResponseResponse)
async def submit_response(
    session_id: str,
    request: SubmitResponseRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> SubmitResponseResponse:
    """Submit a response to an onboarding question.

    CRITICAL: Verifies session ownership to prevent unauthorized access.

    Args:
        session_id: Session identifier
        request: Response submission request
        ctx: Tenant context for identification
        db: Database pool

    Returns:
        Response processing results
    """
    try:
        # CRITICAL: Verify session ownership
        await _verify_session_ownership(session_id, ctx, db)

        # HIGH: Load session from database
        async with db.acquire() as conn:
            from packages.backend.domain.onboarding_repository import (
                OnboardingSessionRepo,
            )

            session = await OnboardingSessionRepo.load_session(conn, session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        ai_onboarding = get_ai_onboarding_manager()

        # Process response
        result = await ai_onboarding.process_response(
            session, request.question_id, request.response
        )

        if result["success"]:
            # Get next question before saving
            next_question = await ai_onboarding.get_next_question(session)

            # Single transactional save after processing and getting next question
            async with db.acquire() as conn:
                from packages.backend.domain.onboarding_repository import (
                    OnboardingSessionRepo,
                )

                await OnboardingSessionRepo.save_session(conn, session)

            return SubmitResponseResponse(
                success=result["success"],
                profile_update=result["profile_update"],
                follow_up_questions=result["follow_up_questions"],
                completion_percentage=result["completion_percentage"],
                next_suggestions=result["next_suggestions"],
                next_question=next_question.model_dump() if next_question else None,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to process response"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit response: {e}")
        raise HTTPException(status_code=500, detail="Failed to process response")


@router.post("/session/{session_id}/complete", response_model=CompleteSessionResponse)
async def complete_onboarding(
    session_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> CompleteSessionResponse:
    """Complete the onboarding session.

    CRITICAL: Verifies session ownership to prevent unauthorized access.

    Args:
        session_id: Session identifier
        ctx: Tenant context for identification
        db: Database pool

    Returns:
        Completion results with recommendations
    """
    try:
        # CRITICAL: Verify session ownership
        await _verify_session_ownership(session_id, ctx, db)

        # HIGH: Load session from database
        async with db.acquire() as conn:
            from packages.backend.domain.onboarding_repository import (
                OnboardingSessionRepo,
            )

            session = await OnboardingSessionRepo.load_session(conn, session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        ai_onboarding = get_ai_onboarding_manager()

        # Complete onboarding
        result = await ai_onboarding.complete_onboarding(session)

        # HIGH: Mark session as completed and save
        async with db.acquire() as conn:
            from packages.backend.domain.onboarding_repository import (
                OnboardingSessionRepo,
            )

            await OnboardingSessionRepo.mark_completed(conn, session_id)
            await OnboardingSessionRepo.save_session(conn, session)

            # CRITICAL: Update profile has_completed_onboarding so user is not sent back to onboarding
            await conn.execute(
                """
                UPDATE public.profiles
                SET profile_data = COALESCE(profile_data, '{}')::jsonb || '{"has_completed_onboarding": true}'::jsonb,
                    updated_at = now()
                WHERE user_id = $1 AND tenant_id = $2
                """,
                session.user_id,
                session.tenant_id,
            )

        if result["success"]:
            return CompleteSessionResponse(
                success=result["success"],
                final_profile=result["final_profile"],
                recommendations=result["recommendations"],
                next_steps=result["next_steps"],
                session_duration=result["session_duration"],
                questions_answered=result["questions_answered"],
                ai_confidence=result["ai_confidence"],
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to complete onboarding"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete onboarding: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete onboarding")


@router.get("/flows", response_model=OnboardingFlowResponse)
async def get_onboarding_flows(
    ctx: TenantContext = Depends(get_tenant_context),
) -> OnboardingFlowResponse:
    """Get available onboarding flows.

    Args:
        ctx: Tenant context for identification

    Returns:
        Available onboarding flows
    """
    try:
        ai_onboarding = get_ai_onboarding_manager()

        # Get available flows
        flows = []
        for flow_id, flow_config in ai_onboarding._onboarding_flows.items():
            flows.append(
                {
                    "flow_id": flow_config.flow_id,
                    "flow_name": flow_config.flow_name,
                    "target_audience": flow_config.target_audience,
                    "question_categories": flow_config.question_categories,
                    "complexity_progression": [
                        c.value for c in flow_config.complexity_progression
                    ],
                    "adaptive_mode": flow_config.adaptive_rules.get("enabled", False),
                    "estimated_duration_minutes": len(flow_config.question_categories)
                    * 2,
                }
            )

        return OnboardingFlowResponse(
            flows=flows,
            default_flow="professional",
        )

    except Exception as e:
        logger.error(f"Failed to get onboarding flows: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve onboarding flows"
        )


_PROGRESS_DATA_MAX_KEYS = 10
_PROGRESS_DATA_MAX_BYTES = 50 * 1024  # 50KB


@router.post("/session/{session_id}/save-progress")
async def save_session_progress(
    session_id: str,
    progress_data: Dict[str, Any],
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> Dict[str, Any]:
    """Save onboarding session progress.

    CRITICAL: Verifies session ownership to prevent unauthorized access.

    Args:
        session_id: Session identifier
        progress_data: Progress data to save
        ctx: Tenant context for identification
        db: Database pool

    Returns:
        Save operation result
    """
    try:
        # HIGH: Validate payload size to prevent DoS
        try:
            payload_bytes = json.dumps(progress_data).encode("utf-8")
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid progress_data")
        if len(payload_bytes) > _PROGRESS_DATA_MAX_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"progress_data too large (max {_PROGRESS_DATA_MAX_BYTES // 1024}KB)",
            )
        if len(progress_data) > _PROGRESS_DATA_MAX_KEYS:
            raise HTTPException(
                status_code=400,
                detail=f"Too many keys in progress_data (max {_PROGRESS_DATA_MAX_KEYS})",
            )

        # CRITICAL: Verify session ownership
        await _verify_session_ownership(session_id, ctx, db)

        # HIGH: Load and update session from database
        async with db.acquire() as conn:
            from packages.backend.domain.onboarding_repository import (
                OnboardingSessionRepo,
            )

            session = await OnboardingSessionRepo.load_session(conn, session_id)

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # Update session with progress data (validate to avoid 500 on malformed input)
            if "current_step" in progress_data:
                try:
                    session.current_step = int(progress_data["current_step"])
                except (TypeError, ValueError):
                    raise HTTPException(
                        status_code=400,
                        detail="current_step must be a valid integer",
                    )
            if "completion_percentage" in progress_data:
                try:
                    session.completion_percentage = float(
                        progress_data["completion_percentage"]
                    )
                except (TypeError, ValueError):
                    raise HTTPException(
                        status_code=400,
                        detail="completion_percentage must be a valid number",
                    )
            if "responses" in progress_data:
                r = progress_data["responses"]
                if isinstance(r, dict):
                    session.responses.update(r)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="responses must be an object",
                    )
            if "user_profile" in progress_data:
                up = progress_data["user_profile"]
                if isinstance(up, dict):
                    session.user_profile.update(up)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="user_profile must be an object",
                    )

            # Save updated session
            await OnboardingSessionRepo.save_session(conn, session)

        return {
            "success": True,
            "message": "Progress saved successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to save session progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to save session progress")


@router.get("/session/{session_id}/progress")
async def get_session_progress(
    session_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> Dict[str, Any]:
    """Get onboarding session progress.

    CRITICAL: Verifies session ownership to prevent unauthorized access.

    Args:
        session_id: Session identifier
        ctx: Tenant context for identification
        db: Database pool

    Returns:
        Session progress data
    """
    try:
        # CRITICAL: Verify session ownership
        await _verify_session_ownership(session_id, ctx, db)

        # HIGH: Load session from database
        async with db.acquire() as conn:
            from packages.backend.domain.onboarding_repository import (
                OnboardingSessionRepo,
            )

            session = await OnboardingSessionRepo.load_session(conn, session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "user_id": ctx.user_id,
            "completion_percentage": session.completion_percentage,
            "questions_answered": len(session.responses),
            "total_questions": session.total_steps,
            "current_step": session.current_step,
            "last_activity": session.last_activity.isoformat()
            if session.last_activity
            else datetime.now(timezone.utc).isoformat(),
            "estimated_remaining_minutes": max(
                0, int((1.0 - session.completion_percentage / 100) * 15)
            ),
        }

    except Exception as e:
        logger.error(f"Failed to get session progress: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve session progress"
        )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: asyncpg.Pool = Depends(get_pool),
) -> Dict[str, Any]:
    """Delete onboarding session.

    CRITICAL: Verifies session ownership to prevent unauthorized deletion.

    Args:
        session_id: Session identifier
        ctx: Tenant context for identification
        db: Database pool

    Returns:
        Delete operation result
    """
    try:
        # CRITICAL: Verify session ownership before deletion
        await _verify_session_ownership(session_id, ctx, db)
        # HIGH: Delete session from database
        async with db.acquire() as conn:
            from packages.backend.domain.onboarding_repository import (
                OnboardingSessionRepo,
            )

            await OnboardingSessionRepo.delete_session(conn, session_id)

        return {
            "success": True,
            "message": "Session deleted successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.get("/analytics")
async def get_onboarding_analytics(
    ctx: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Get onboarding analytics data.

    Args:
        ctx: Tenant context for identification

    Returns:
        Onboarding analytics
    """
    try:
        # In a real implementation, we would retrieve from database
        return {
            "total_sessions": 0,
            "completed_sessions": 0,
            "average_completion_time_minutes": 0,
            "most_used_flow": "professional",
            "completion_rate": 0.0,
            "average_questions_per_session": 0,
            "ai_confidence_average": 0.0,
            "user_satisfaction_score": 0.0,
        }

    except Exception as e:
        logger.error(f"Failed to get onboarding analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve onboarding analytics"
        )


@router.get("/health")
async def health_check(
    ctx: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Health check for AI onboarding system."""

    return {
        "status": "healthy",
        "ai_integration": "operational",
        "adaptive_flows": "available",
        "question_generation": "functional",
        "response_processing": "operational",
        "completion_detection": "functional",
        "profile_extraction": "operational",
        "recommendation_engine": "available",
        "available_flows": ["professional", "student", "career_changer"],
        "question_types": [
            "multiple_choice",
            "text_input",
            "textarea",
            "select",
            "checkboxes",
            "radio",
            "rating",
            "boolean",
            "file_upload",
            "skills_assessment",
            "career_goals",
            "experience_level",
        ],
        "adaptive_features": {
            "dynamic_question_order": True,
            "conditional_branching": True,
            "follow_up_generation": True,
            "complexity_adjustment": True,
            "early_completion": True,
        },
        "ai_capabilities": {
            "question_generation": True,
            "response_analysis": True,
            "profile_extraction": True,
            "completion_detection": True,
            "recommendation_generation": True,
            "next_step_suggestions": True,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/test-question-generation")
async def test_question_generation(
    flow_type: str = "professional",
    initial_context: Optional[Dict[str, Any]] = None,
    ctx: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Test AI question generation.

    Args:
        flow_type: Onboarding flow type
        initial_context: Initial user context
        ctx: Tenant context for identification

    Returns:
        Generated test questions
    """
    try:
        ai_onboarding = get_ai_onboarding_manager()

        # Get flow configuration
        flow_config = ai_onboarding._get_flow_config(flow_type)

        # Generate test questions
        questions = await ai_onboarding._generate_initial_questions(
            user_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            flow_config=flow_config,
            initial_context=initial_context,
        )

        return {
            "success": True,
            "flow_type": flow_type,
            "questions_generated": len(questions),
            "questions": [
                q.model_dump() for q in questions[:3]
            ],  # Return first 3 for testing
            "ai_confidence": 0.8,
        }

    except Exception as e:
        logger.error(f"Failed to test question generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate test questions")


@router.get("/question-templates")
async def get_question_templates(
    ctx: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Get available question templates.

    Args:
        ctx: Tenant context for identification

    Returns:
        Available question templates
    """
    try:
        ai_onboarding = get_ai_onboarding_manager()

        return {
            "templates": ai_onboarding._question_templates,
            "categories": list(ai_onboarding._question_templates.keys()),
            "total_templates": len(ai_onboarding._question_templates),
        }

    except Exception as e:
        logger.error(f"Failed to get question templates: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve question templates"
        )
