"""
Product analytics event taxonomy.

Defines canonical event type constants used by both the API (server-side
enrichment) and the mobile client (via the /analytics/events sink).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Job feed events
# ---------------------------------------------------------------------------
JOB_SWIPE_RIGHT = "job_swipe_right"
JOB_SWIPE_LEFT = "job_swipe_left"

# ---------------------------------------------------------------------------
# Application lifecycle events
# ---------------------------------------------------------------------------
APPLICATION_CREATED = "application_created"
APPLICATION_STATUS_CHANGED = "application_status_changed"

# ---------------------------------------------------------------------------
# Hold / input events
# ---------------------------------------------------------------------------
HOLD_QUESTIONS_SHOWN = "hold_questions_shown"
HOLD_QUESTIONS_ANSWERED = "hold_questions_answered"

# ---------------------------------------------------------------------------
# Resume events
# ---------------------------------------------------------------------------
RESUME_UPLOADED = "resume_uploaded"
RESUME_PARSED_SUCCESS = "resume_parsed_success"
RESUME_PARSED_FAILED = "resume_parsed_failed"

# ---------------------------------------------------------------------------
# Session events
# ---------------------------------------------------------------------------
APP_OPENED = "app_opened"
SESSION_STARTED = "session_started"
SESSION_ENDED = "session_ended"

# ---------------------------------------------------------------------------
# Agent feedback events
# ---------------------------------------------------------------------------
AGENT_FEEDBACK_SUBMITTED = "agent_feedback_submitted"

# ---------------------------------------------------------------------------
# M2: Growth / onboarding / conversion events
# ---------------------------------------------------------------------------
ONBOARDING_STARTED = "onboarding_started"
ONBOARDING_RESUME_UPLOADED = "onboarding_resume_uploaded"
ONBOARDING_COMPLETED = "onboarding_completed"
REFERRAL_SHARED = "referral_shared"
REFERRAL_REDEEMED = "referral_redeemed"
UPGRADE_PROMPT_SHOWN = "upgrade_prompt_shown"
UPGRADE_STARTED = "upgrade_started"
UPGRADE_COMPLETED = "upgrade_completed"
PUSH_TOKEN_REGISTERED = "push_token_registered"
REVIEW_PROMPT_SHOWN = "review_prompt_shown"

# ---------------------------------------------------------------------------
# Full catalog (for validation)
# ---------------------------------------------------------------------------
ALL_EVENT_TYPES: frozenset[str] = frozenset({
    JOB_SWIPE_RIGHT,
    JOB_SWIPE_LEFT,
    APPLICATION_CREATED,
    APPLICATION_STATUS_CHANGED,
    HOLD_QUESTIONS_SHOWN,
    HOLD_QUESTIONS_ANSWERED,
    RESUME_UPLOADED,
    RESUME_PARSED_SUCCESS,
    RESUME_PARSED_FAILED,
    APP_OPENED,
    SESSION_STARTED,
    SESSION_ENDED,
    AGENT_FEEDBACK_SUBMITTED,
    ONBOARDING_STARTED,
    ONBOARDING_RESUME_UPLOADED,
    ONBOARDING_COMPLETED,
    REFERRAL_SHARED,
    REFERRAL_REDEEMED,
    UPGRADE_PROMPT_SHOWN,
    UPGRADE_STARTED,
    UPGRADE_COMPLETED,
    PUSH_TOKEN_REGISTERED,
    REVIEW_PROMPT_SHOWN,
})
