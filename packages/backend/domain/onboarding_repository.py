"""Repository for onboarding session persistence."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import asyncpg

from packages.backend.domain.ai_onboarding import OnboardingSession
from shared.logging_config import get_logger

logger = get_logger("sorce.onboarding_repo")


class OnboardingSessionRepo:
    """Repository for onboarding session persistence."""

    @staticmethod
    async def save_session(
        conn: asyncpg.Connection,
        session: OnboardingSession,
        expires_in_hours: int = 24,
    ) -> None:
        """Save onboarding session to database.

        Args:
            conn: Database connection
            session: Onboarding session to save
            expires_in_hours: Hours until session expires (default 24)
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        await conn.execute(
            """
            INSERT INTO public.onboarding_sessions
                (session_id, user_id, tenant_id, flow_type, state, current_step,
                 completion_percentage, created_at, updated_at, expires_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10)
            ON CONFLICT (session_id) DO UPDATE SET
                state = $5::jsonb,
                current_step = $6,
                completion_percentage = $7,
                updated_at = $9,
                expires_at = $10
            """,
            session.session_id,
            session.user_id,
            session.tenant_id,
            getattr(session, "flow_type", "professional"),
            json.dumps(
                {
                    "questions": [
                        q.model_dump() if hasattr(q, "model_dump") else q
                        for q in session.questions
                    ],
                    "responses": session.responses,
                    "user_profile": session.user_profile,
                    "total_steps": session.total_steps,
                    "adaptive_mode": session.adaptive_mode,
                    "ai_confidence": session.ai_confidence,
                    "next_suggestions": session.next_suggestions,
                }
            ),
            session.current_step,
            session.completion_percentage,
            session.started_at,
            datetime.now(timezone.utc),
            expires_at,
        )

    @staticmethod
    async def load_session(
        conn: asyncpg.Connection,
        session_id: str,
    ) -> OnboardingSession | None:
        """Load onboarding session from database.

        Args:
            conn: Database connection
            session_id: Session identifier

        Returns:
            OnboardingSession if found, None otherwise
        """
        row = await conn.fetchrow(
            """
            SELECT session_id, user_id, tenant_id, flow_type, state, current_step,
                   completion_percentage, created_at, updated_at, expires_at, completed_at
            FROM public.onboarding_sessions
            WHERE session_id = $1
            """,
            session_id,
        )

        if not row:
            return None

        # Check expiration
        if row.get("expires_at") and row["expires_at"] < datetime.now(timezone.utc):
            logger.warning(f"Session {session_id} has expired")
            return None

        # Parse state
        state = (
            row["state"]
            if isinstance(row["state"], dict)
            else json.loads(row["state"] or "{}")
        )

        # Reconstruct session
        from packages.backend.domain.ai_onboarding import OnboardingQuestion

        questions = []
        for q_data in state.get("questions", []):
            try:
                if isinstance(q_data, dict):
                    questions.append(OnboardingQuestion(**q_data))
                else:
                    questions.append(q_data)
            except Exception as e:
                logger.warning(f"Failed to parse question: {e}")

        session = OnboardingSession(
            session_id=str(row["session_id"]),
            user_id=str(row["user_id"]),
            tenant_id=str(row["tenant_id"]),
            current_step=int(row["current_step"]),
            total_steps=state.get("total_steps", int(row.get("total_steps", 10))),
            questions=questions,
            responses=state.get("responses", {}),
            user_profile=state.get("user_profile", {}),
            completion_percentage=float(row["completion_percentage"]),
            started_at=row["created_at"],
            last_activity=row["updated_at"],
            completed_at=row.get("completed_at"),
            adaptive_mode=state.get("adaptive_mode", True),
            ai_confidence=state.get("ai_confidence", 0.8),
            next_suggestions=state.get("next_suggestions", []),
        )

        return session

    @staticmethod
    async def mark_completed(
        conn: asyncpg.Connection,
        session_id: str,
    ) -> None:
        """Mark session as completed.

        Args:
            conn: Database connection
            session_id: Session identifier
        """
        # MEDIUM: Verify session exists before updating
        existing = await conn.fetchrow(
            "SELECT id FROM public.onboarding_sessions WHERE session_id = $1",
            session_id,
        )
        if not existing:
            raise ValueError(f"Session {session_id} not found")

        await conn.execute(
            """
            UPDATE public.onboarding_sessions
            SET completed_at = now(), updated_at = now()
            WHERE session_id = $1
            """,
            session_id,
        )

    @staticmethod
    async def delete_session(
        conn: asyncpg.Connection,
        session_id: str,
    ) -> bool:
        """Delete onboarding session.

        Args:
            conn: Database connection
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        # MEDIUM: Check if session exists and return status
        result = await conn.execute(
            "DELETE FROM public.onboarding_sessions WHERE session_id = $1",
            session_id,
        )
        # asyncpg execute returns "DELETE N" - check if any rows were deleted
        return result.split()[-1] != "0"
