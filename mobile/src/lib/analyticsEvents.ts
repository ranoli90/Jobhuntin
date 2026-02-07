/**
 * Product analytics event taxonomy — TypeScript types.
 *
 * Mirrors backend/domain/analytics_events.py.
 */

// ---------------------------------------------------------------------------
// Canonical event type union
// ---------------------------------------------------------------------------

export type AnalyticsEventType =
  // Job feed
  | "job_swipe_right"
  | "job_swipe_left"
  // Application lifecycle
  | "application_created"
  | "application_status_changed"
  // Hold / input
  | "hold_questions_shown"
  | "hold_questions_answered"
  // Resume
  | "resume_uploaded"
  | "resume_parsed_success"
  | "resume_parsed_failed"
  // Session
  | "app_opened"
  | "session_started"
  | "session_ended"
  // Agent feedback
  | "agent_feedback_submitted"
  // M2: Growth / onboarding / conversion
  | "onboarding_started"
  | "onboarding_resume_uploaded"
  | "onboarding_completed"
  | "referral_shared"
  | "referral_redeemed"
  | "upgrade_prompt_shown"
  | "upgrade_started"
  | "upgrade_completed"
  | "push_token_registered"
  | "review_prompt_shown";
