/**
 * API response types mirroring backend Pydantic models.
 * Single source of truth for frontend ↔ backend contract.
 */

import type {
  ApplicationStatus,
  ApplicationInput,
  AnswerItem,
} from "../types";

// ---------------------------------------------------------------------------
// Standard error envelope (mirrors backend ErrorResponse)
// ---------------------------------------------------------------------------

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

// ---------------------------------------------------------------------------
// Resume parse
// ---------------------------------------------------------------------------

export interface CanonicalContact {
  full_name: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  location: string;
  linkedin_url: string;
  portfolio_url: string;
}

export interface CanonicalEducation {
  institution: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date: string;
  gpa: string;
}

export interface CanonicalExperience {
  company: string;
  title: string;
  start_date: string;
  end_date: string;
  location: string;
  responsibilities: string[];
}

export interface CanonicalSkills {
  technical: string[];
  soft: string[];
}

export interface CanonicalProfile {
  contact: CanonicalContact;
  education: CanonicalEducation[];
  experience: CanonicalExperience[];
  skills: CanonicalSkills;
  certifications: string[];
  languages: string[];
  summary: string;
  current_title: string;
  current_company: string;
  years_experience: number | null;
}

export interface ResumeParseResponse {
  user_id: string;
  profile: CanonicalProfile;
  resume_url: string | null;
}

// ---------------------------------------------------------------------------
// Application detail (debug endpoint)
// ---------------------------------------------------------------------------

export interface ApplicationEvent {
  id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface ApplicationWithDetail {
  application: Record<string, unknown>;
  inputs: ApplicationInput[];
  events: ApplicationEvent[];
}

// ---------------------------------------------------------------------------
// Resume task (answer hold questions)
// ---------------------------------------------------------------------------

export interface ApplicationInputOut {
  id: string;
  selector: string;
  question: string;
  field_type: string;
  answer: string | null;
  resolved: boolean;
  meta: Record<string, unknown> | null;
}

export interface ResumeTaskResponse {
  application_id: string;
  status: ApplicationStatus;
  message: string;
  unresolved_inputs: ApplicationInputOut[];
}

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: "ok" | "degraded";
  env: string;
  db: "ok" | "unreachable";
  metrics: Record<string, unknown>;
}
