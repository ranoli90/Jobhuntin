"""Interview Simulator API endpoints — AI-powered interview preparation."""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from packages.backend.domain.interview_simulator import (
    InterviewPhase,
    InterviewQuestion,
    InterviewSession,
    InterviewType,
    QuestionDifficulty,
    UserResponse,
    get_interview_simulator,
)
from shared.logging_config import get_logger
from shared.metrics import incr

from api.deps import get_pool, get_current_user_id

logger = get_logger("sorce.api.interviews")

router = APIRouter(prefix="/interviews", tags=["interviews"])


class CreateSessionRequest(BaseModel):
    job_id: str
    company: str
    job_title: str
    job_description: str
    interview_type: str = "general"
    difficulty: str = "medium"
    question_count: int = 10


class CreateSessionResponse(BaseModel):
    session_id: str
    job_id: str
    company: str
    job_title: str
    interview_type: str
    difficulty: str
    total_questions: int
    first_question: dict[str, Any] | None = None


class SubmitAnswerRequest(BaseModel):
    response_text: str
    response_time_seconds: float


class SubmitAnswerResponse(BaseModel):
    feedback: dict[str, Any]
    next_question: dict[str, Any] | None
    is_complete: bool
    current_question: int
    total_questions: int


class SessionSummaryResponse(BaseModel):
    session_id: str
    company: str
    job_title: str
    total_score: float
    questions_answered: int
    category_scores: dict[str, float]
    top_strengths: list[str]
    top_improvements: list[str]
    duration_minutes: float
    difficulty: str
    status: str


class SessionDetailResponse(BaseModel):
    session: dict[str, Any]
    questions: list[dict[str, Any]]
    responses: list[dict[str, Any]]
    feedback: list[dict[str, Any]]


async def _session_from_row(row: dict) -> InterviewSession:
    questions_data = (
        row["questions"]
        if isinstance(row["questions"], list)
        else json.loads(row["questions"] or "[]")
    )
    responses_data = (
        row["responses"]
        if isinstance(row["responses"], list)
        else json.loads(row["responses"] or "[]")
    )

    questions = [
        InterviewQuestion(
            id=q["id"],
            question=q["question"],
            question_type=InterviewType(q.get("question_type", "general")),
            difficulty=QuestionDifficulty(q.get("difficulty", "medium")),
            phase=InterviewPhase(q.get("phase", "core_questions")),
            expected_keywords=q.get("expected_keywords", []),
            follow_up_prompts=q.get("follow_up_prompts", []),
            time_limit_seconds=q.get("time_limit_seconds", 180),
            hints=q.get("hints", []),
        )
        for q in questions_data
    ]

    responses = [
        UserResponse(
            question_id=r["question_id"],
            response_text=r["response_text"],
            response_time_seconds=r.get("response_time_seconds", 0),
            confidence_level=r.get("confidence_level", 0.5),
            keywords_hit=r.get("keywords_hit", []),
            missed_keywords=r.get("missed_keywords", []),
        )
        for r in responses_data
    ]

    return InterviewSession(
        session_id=row["session_id"],
        user_id=str(row["user_id"]),
        job_id=str(row["job_id"]) if row["job_id"] else "",
        company=row["company"],
        job_title=row["job_title"],
        interview_type=InterviewType(row.get("interview_type", "general")),
        difficulty=QuestionDifficulty(row.get("difficulty", "medium")),
        questions=questions,
        responses=responses,
        feedback=[],
        current_phase=InterviewPhase.CORE_QUESTIONS,
        current_question_index=row.get("current_question_index", 0),
        total_score=row.get("total_score", 0.0),
        started_at=row["started_at"],
        completed_at=row.get("completed_at"),
        status=row.get("status", "in_progress"),
    )


async def _save_session(db: asyncpg.Pool, session: InterviewSession) -> None:
    questions_json = [
        {
            "id": q.id,
            "question": q.question,
            "question_type": q.question_type.value,
            "difficulty": q.difficulty.value,
            "phase": q.phase.value,
            "expected_keywords": q.expected_keywords,
            "follow_up_prompts": q.follow_up_prompts,
            "time_limit_seconds": q.time_limit_seconds,
            "hints": q.hints,
        }
        for q in session.questions
    ]

    responses_json = [
        {
            "question_id": r.question_id,
            "response_text": r.response_text,
            "response_time_seconds": r.response_time_seconds,
            "confidence_level": r.confidence_level,
            "keywords_hit": r.keywords_hit,
            "missed_keywords": r.missed_keywords,
        }
        for r in session.responses
    ]

    feedback_json = [
        {
            "question_id": f.question_id,
            "score": f.score.model_dump(),
            "strengths": f.strengths,
            "improvements": f.improvements,
            "sample_answer": f.sample_answer,
            "tips": f.tips,
        }
        for f in session.feedback
    ]

    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.interview_sessions
                (session_id, user_id, job_id, company, job_title, interview_type,
                 difficulty, questions, responses, feedback, current_question_index,
                 total_score, status, started_at, completed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10::jsonb, $11, $12, $13, $14, $15)
            ON CONFLICT (session_id) DO UPDATE SET
                responses = $9::jsonb,
                feedback = $10::jsonb,
                current_question_index = $11,
                total_score = $12,
                status = $13,
                completed_at = $15
            """,
            session.session_id,
            session.user_id,
            session.job_id if session.job_id else None,
            session.company,
            session.job_title,
            session.interview_type.value,
            session.difficulty.value,
            json.dumps(questions_json),
            json.dumps(responses_json),
            json.dumps(feedback_json),
            session.current_question_index,
            session.total_score,
            session.status,
            session.started_at,
            session.completed_at,
        )


async def _load_session(db: asyncpg.Pool, session_id: str) -> InterviewSession | None:
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM public.interview_sessions WHERE session_id = $1",
            session_id,
        )

        if not row:
            return None

        return await _session_from_row(dict(row))


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_interview_session(
    body: CreateSessionRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> CreateSessionResponse:
    simulator = get_interview_simulator()

    async with db.acquire() as conn:
        profile_row = await conn.fetchrow(
            """
            SELECT p.profile_data, u.email, u.full_name
            FROM public.profiles p
            JOIN public.users u ON u.id = p.user_id
            WHERE p.user_id = $1
            """,
            user_id,
        )

    user_profile = {}
    if profile_row:
        profile_data = profile_row["profile_data"]
        if isinstance(profile_data, str):
            profile_data = json.loads(profile_data or "{}")
        user_profile = {
            "email": profile_row["email"],
            "full_name": profile_row["full_name"],
            **profile_data,
        }

    try:
        interview_type = InterviewType(body.interview_type.lower())
    except ValueError:
        interview_type = InterviewType.GENERAL

    try:
        difficulty = QuestionDifficulty(body.difficulty.lower())
    except ValueError:
        difficulty = QuestionDifficulty.MEDIUM

    session = await simulator.create_session(
        user_id=user_id,
        job_id=body.job_id,
        company=body.company,
        job_title=body.job_title,
        job_description=body.job_description,
        user_profile=user_profile,
        interview_type=interview_type,
        difficulty=difficulty,
        question_count=body.question_count,
    )

    await _save_session(db, session)
    incr("interview.session_created")

    first_question = session.questions[0] if session.questions else None

    return CreateSessionResponse(
        session_id=session.session_id,
        job_id=session.job_id,
        company=session.company,
        job_title=session.job_title,
        interview_type=session.interview_type.value,
        difficulty=session.difficulty.value,
        total_questions=len(session.questions),
        first_question=(
            {
                "id": first_question.id,
                "question": first_question.question,
                "question_type": first_question.question_type.value,
                "difficulty": first_question.difficulty.value,
                "phase": first_question.phase.value,
                "time_limit_seconds": first_question.time_limit_seconds,
            }
            if first_question
            else None
        ),
    )


@router.post("/sessions/{session_id}/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    session_id: str,
    body: SubmitAnswerRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> SubmitAnswerResponse:
    simulator = get_interview_simulator()

    session = await _load_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")

    feedback = await simulator.submit_response(
        session=session,
        response_text=body.response_text,
        response_time_seconds=body.response_time_seconds,
    )

    await _save_session(db, session)
    incr("interview.answer_submitted")

    is_complete = session.status == "completed"

    next_question = None
    if not is_complete and session.current_question_index < len(session.questions):
        q = session.questions[session.current_question_index]
        next_question = {
            "id": q.id,
            "question": q.question,
            "question_type": q.question_type.value,
            "difficulty": q.difficulty.value,
            "phase": q.phase.value,
            "time_limit_seconds": q.time_limit_seconds,
        }

    return SubmitAnswerResponse(
        feedback={
            "question_id": feedback.question_id,
            "score": feedback.score.model_dump(),
            "strengths": feedback.strengths,
            "improvements": feedback.improvements,
            "sample_answer": feedback.sample_answer,
            "tips": feedback.tips,
        },
        next_question=next_question,
        is_complete=is_complete,
        current_question=session.current_question_index,
        total_questions=len(session.questions),
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> SessionDetailResponse:
    session = await _load_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return SessionDetailResponse(
        session={
            "session_id": session.session_id,
            "user_id": session.user_id,
            "job_id": session.job_id,
            "company": session.company,
            "job_title": session.job_title,
            "interview_type": session.interview_type.value,
            "difficulty": session.difficulty.value,
            "current_phase": session.current_phase.value,
            "current_question_index": session.current_question_index,
            "total_score": session.total_score,
            "started_at": session.started_at.isoformat(),
            "completed_at": (
                session.completed_at.isoformat() if session.completed_at else None
            ),
            "status": session.status,
        },
        questions=[
            {
                "id": q.id,
                "question": q.question,
                "question_type": q.question_type.value,
                "difficulty": q.difficulty.value,
                "phase": q.phase.value,
                "time_limit_seconds": q.time_limit_seconds,
                "expected_keywords": q.expected_keywords,
            }
            for q in session.questions
        ],
        responses=[
            {
                "question_id": r.question_id,
                "response_text": r.response_text,
                "response_time_seconds": r.response_time_seconds,
                "keywords_hit": r.keywords_hit,
                "missed_keywords": r.missed_keywords,
            }
            for r in session.responses
        ],
        feedback=[
            {
                "question_id": f.question_id,
                "score": f.score.model_dump(),
                "strengths": f.strengths,
                "improvements": f.improvements,
                "tips": f.tips,
            }
            for f in session.feedback
        ],
    )


@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(
    session_id: str,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> SessionSummaryResponse:
    session = await _load_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    simulator = get_interview_simulator()
    summary = simulator.get_session_summary(session)

    return SessionSummaryResponse(
        session_id=session.session_id,
        company=session.company,
        job_title=session.job_title,
        total_score=session.total_score,
        questions_answered=len(session.responses),
        category_scores=summary.get("category_scores", {}),
        top_strengths=summary.get("top_strengths", [])[:5],
        top_improvements=summary.get("top_improvements", [])[:5],
        duration_minutes=summary.get("duration_minutes", 0),
        difficulty=session.difficulty.value,
        status=session.status,
    )


@router.get("/sessions")
async def list_user_sessions(
    limit: int = 10,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> list[dict[str, Any]]:
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT session_id, company, job_title, interview_type, difficulty,
                   total_score, status, started_at, completed_at,
                   json_array_length(responses) as questions_answered
            FROM public.interview_sessions
            WHERE user_id = $1
            ORDER BY started_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )

        return [
            {
                "session_id": r["session_id"],
                "company": r["company"],
                "job_title": r["job_title"],
                "interview_type": r["interview_type"],
                "difficulty": r["difficulty"],
                "total_score": r["total_score"],
                "questions_answered": r["questions_answered"],
                "status": r["status"],
                "started_at": r["started_at"].isoformat(),
                "completed_at": (
                    r["completed_at"].isoformat() if r["completed_at"] else None
                ),
            }
            for r in rows
        ]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
) -> dict[str, str]:
    session = await _load_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    async with db.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.interview_sessions WHERE session_id = $1",
            session_id,
        )

    incr("interview.session_deleted")
    return {"status": "deleted"}
