/**
 * Typed API client for the Sorce backend (Render).
 *
 * Centralizes all HTTP calls with:
 *   - Environment-aware base URL (from config.ts)
 *   - Auth token injection via session
 *   - Standard error handling (ErrorResponse envelope)
 *   - Typed request/response wrappers
 */

import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";
import { track } from "../lib/analytics";
import { getUsage } from "./billing";
import type { Application, AnswerItem, Job } from "../types";
import type {
  ResumeParseResponse,
  ResumeTaskResponse,
  ApplicationWithDetail,
  HealthResponse,
  ErrorResponse,
} from "./types";

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown> | null;

  constructor(status: number, code: string, message: string, details?: Record<string, unknown> | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details ?? null;
  }
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

async function getAuthToken(): Promise<string> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new ApiError(401, "UNAUTHENTICATED", "Not authenticated");
  return session.access_token;
}

async function handleResponse<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    let code = `HTTP_${resp.status}`;
    let message = `Request failed with status ${resp.status}`;
    try {
      const body = (await resp.json()) as ErrorResponse;
      if (body.error) {
        code = body.error.code;
        message = body.error.message;
      }
    } catch {
      // Response body wasn't JSON; use defaults
    }
    throw new ApiError(resp.status, code, message);
  }
  return (await resp.json()) as T;
}

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Upload a PDF resume and get back a parsed canonical profile.
 */
export async function parseResume(file: { uri: string; name: string; type: string }): Promise<ResumeParseResponse> {
  const token = await getAuthToken();

  const formData = new FormData();
  formData.append("file", {
    uri: file.uri,
    name: file.name,
    type: file.type,
  } as unknown as Blob);

  track("resume_uploaded", { file_name: file.name });

  const resp = await fetch(`${API_BASE_URL}/webhook/resume_parse`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  try {
    const result = await handleResponse<ResumeParseResponse>(resp);
    track("resume_parsed_success", { user_id: result.user_id });
    return result;
  } catch (err) {
    track("resume_parsed_failed", { error: String(err) });
    throw err;
  }
}

export class QuotaExceededError extends Error {
  plan: string;
  used: number;
  limit: number;
  constructor(plan: string, used: number, limit: number) {
    super(`Monthly quota reached (${used}/${limit}). Upgrade for more applications.`);
    this.name = "QuotaExceededError";
    this.plan = plan;
    this.used = used;
    this.limit = limit;
  }
}

/**
 * Create a new application for a job (swipe right).
 * Uses REST API (POST /me/applications) - same as web. Throws QuotaExceededError if limit hit.
 */
export async function createApplication(jobId: string): Promise<Application> {
  const token = await getAuthToken();
  if (!token) throw new ApiError(401, "UNAUTHENTICATED", "Not authenticated");

  const resp = await fetch(`${API_BASE_URL}/me/applications`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ job_id: jobId, decision: "ACCEPT" }),
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({})) as { detail?: string | { message?: string } };
    const detail = typeof body.detail === "string" ? body.detail : body.detail?.message;
    if (resp.status === 402 && detail?.toLowerCase().includes("quota")) {
      const usage = await getUsage();
      throw new QuotaExceededError(usage.plan, usage.monthly_used, usage.monthly_limit);
    }
    throw new ApiError(resp.status, "CREATE_APPLICATION_FAILED", detail || "Failed to create application");
  }

  const data = await handleResponse<{ id: string; job_id: string; status: string }>(resp);
  return {
    id: data.id,
    user_id: "",
    job_id: data.job_id,
    tenant_id: null,
    blueprint_key: "job-app",
    status: data.status as Application["status"],
    error_message: null,
    locked_at: null,
    submitted_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  } as Application;
}

/**
 * Get full application detail (app + inputs + events).
 */
export async function getApplication(applicationId: string): Promise<ApplicationWithDetail> {
  const token = await getAuthToken();

  const resp = await fetch(`${API_BASE_URL}/applications/${applicationId}`, {
    method: "GET",
    headers: authHeaders(token),
  });

  return handleResponse<ApplicationWithDetail>(resp);
}

/**
 * Submit answers to hold questions and re-queue the application.
 */
export async function submitApplicationInputs(
  applicationId: string,
  answers: AnswerItem[],
): Promise<ResumeTaskResponse> {
  const token = await getAuthToken();

  const resp = await fetch(`${API_BASE_URL}/agent/resume_task`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({
      application_id: applicationId,
      answers,
    }),
  });

  return handleResponse<ResumeTaskResponse>(resp);
}

/**
 * Fetch job listings (for job feed / swipe). Uses REST API GET /me/jobs.
 */
export async function getJobs(params?: { limit?: number; offset?: number }): Promise<{ jobs: Job[] }> {
  const token = await getAuthToken();
  if (!token) throw new ApiError(401, "UNAUTHENTICATED", "Not authenticated");

  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  const query = searchParams.toString();
  const url = `${API_BASE_URL}/me/jobs${query ? `?${query}` : ""}`;

  const resp = await fetch(url, { headers: authHeaders(token) });
  const data = await handleResponse<{ jobs?: Job[] } | Job[]>(resp);
  const jobs = Array.isArray(data) ? data : (data.jobs ?? []);
  return { jobs };
}

/**
 * Health check endpoint.
 */
export async function healthCheck(): Promise<HealthResponse> {
  const resp = await fetch(`${API_BASE_URL}/healthz`);
  return handleResponse<HealthResponse>(resp);
}

// ---------------------------------------------------------------------------
// AI Endpoints
// ---------------------------------------------------------------------------

export interface SemanticMatchResponse {
  job_id: string;
  score: number;
  semantic_similarity: number;
  skill_match_ratio: number;
  experience_alignment: number;
  matched_skills: string[];
  missing_skills: string[];
  reasoning: string;
  confidence: "low" | "medium" | "high";
  passed_dealbreakers: boolean;
  dealbreaker_reasons: string[];
}

export interface BatchSemanticMatchResult {
  job_id: string;
  score: number;
  explanation: {
    score: number;
    semantic_similarity: number;
    skill_match_ratio: number;
    experience_alignment: number;
    location_compatible: boolean;
    salary_in_range: boolean;
    matched_skills: string[];
    missing_skills: string[];
    reasoning: string;
    confidence: "low" | "medium" | "high";
  };
  passed_dealbreakers: boolean;
  dealbreaker_reasons: string[];
}

export interface BatchSemanticMatchResponse {
  results: BatchSemanticMatchResult[];
}

export interface TailorResumeResponse {
  original_summary: string;
  tailored_summary: string;
  highlighted_skills: string[];
  emphasized_experiences: Record<string, unknown>[];
  added_keywords: string[];
  ats_optimization_score: number;
  tailoring_confidence: string;
}

export interface ATSScoreResponse {
  overall_score: number;
  metrics: Record<string, number>;
  recommendations: string[];
}

export async function semanticMatch(token: string, jobId: string): Promise<SemanticMatchResponse> {
  const resp = await fetch(`${API_BASE_URL}/ai/semantic-match`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ job_id: jobId }),
  });
  return handleResponse<SemanticMatchResponse>(resp);
}

export async function batchSemanticMatch(
  token: string,
  profile: Record<string, unknown>,
  jobs: Record<string, unknown>[],
  dealbreakers?: Record<string, unknown>
): Promise<BatchSemanticMatchResponse> {
  const resp = await fetch(`${API_BASE_URL}/ai/semantic-match/batch`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ profile, jobs, dealbreakers }),
  });
  return handleResponse<BatchSemanticMatchResponse>(resp);
}

export async function tailorResume(
  token: string,
  profile: Record<string, unknown>,
  job: Record<string, unknown>
): Promise<TailorResumeResponse> {
  const resp = await fetch(`${API_BASE_URL}/ai/tailor-resume`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ profile, job }),
  });
  return handleResponse<TailorResumeResponse>(resp);
}

export async function atsScore(
  token: string,
  resumeText: string,
  jobDescription: string
): Promise<ATSScoreResponse> {
  const resp = await fetch(`${API_BASE_URL}/ai/ats-score`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription }),
  });
  return handleResponse<ATSScoreResponse>(resp);
}
