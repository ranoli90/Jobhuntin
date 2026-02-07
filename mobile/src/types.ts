/**
 * Part 4: Frontend State Management – Shared TypeScript Interfaces
 */

// ---------------------------------------------------------------------------
// Application status enum (mirrors DB enum)
// ---------------------------------------------------------------------------
export type ApplicationStatus =
  | "QUEUED"
  | "PROCESSING"
  | "REQUIRES_INPUT"
  | "APPLIED"       // Sorce job-app terminal status
  | "SUBMITTED"     // Grant/vendor terminal status
  | "COMPLETED"     // Generic terminal status
  | "FAILED";

// ---------------------------------------------------------------------------
// Job (from Adzuna / public.jobs)
// ---------------------------------------------------------------------------
export interface Job {
  id: string;
  external_id: string;
  title: string;
  company: string;
  description: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  category: string | null;
  application_url: string;
  source: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Application (public.applications)
// ---------------------------------------------------------------------------
export interface Application {
  id: string;
  user_id: string;
  job_id: string;
  tenant_id: string | null;
  blueprint_key: string;
  status: ApplicationStatus;
  error_message: string | null;
  locked_at: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Tenant (public.tenants)
// ---------------------------------------------------------------------------
export type TenantPlan = "FREE" | "PRO" | "ENTERPRISE";
export type TenantRole = "OWNER" | "ADMIN" | "MEMBER" | "SUPPORT_AGENT";

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan: TenantPlan;
  plan_metadata: Record<string, unknown>;
  blueprint_key: string;
  created_at: string;
  updated_at: string;
}

export interface TenantMember {
  id: string;
  tenant_id: string;
  user_id: string;
  role: TenantRole;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// ApplicationInput – a single "hold" question (public.application_inputs)
// ---------------------------------------------------------------------------
export interface ApplicationInput {
  id: string;
  application_id: string;
  selector: string;
  question: string;
  field_type: string;
  answer: string | null;
  resolved: boolean;
  meta: Record<string, unknown> | null;
  created_at: string;
  answered_at: string | null;
}

// ---------------------------------------------------------------------------
// ApplicationEvent (public.application_events)
// ---------------------------------------------------------------------------
export interface ApplicationEvent {
  id: string;
  application_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Profile (Digital Twin – public.profiles)
// ---------------------------------------------------------------------------
export interface Profile {
  id: string;
  user_id: string;
  profile_data: ProfileData;
  resume_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProfileData {
  contact: {
    full_name: string;
    email: string;
    phone: string;
    location: string;
    linkedin_url: string;
    portfolio_url: string;
  };
  education: {
    institution: string;
    degree: string;
    field_of_study: string;
    start_date: string;
    end_date: string;
    gpa: string;
  }[];
  experience: {
    company: string;
    title: string;
    start_date: string;
    end_date: string;
    location: string;
    responsibilities: string[];
  }[];
  skills: {
    technical: string[];
    soft: string[];
  };
  certifications: string[];
  languages: string[];
  summary: string;
}

// ---------------------------------------------------------------------------
// API payloads
// ---------------------------------------------------------------------------
export interface AnswerItem {
  input_id: string;
  answer: string;
}

export interface ResumeTaskRequest {
  application_id: string;
  answers: AnswerItem[];
}

export interface ResumeTaskResponse {
  application_id: string;
  status: ApplicationStatus;
  message: string;
}
