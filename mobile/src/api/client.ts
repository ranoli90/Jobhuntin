/**
 * Typed API client for the Sorce backend.
 *
 * Centralizes all HTTP calls with:
 *   - Environment-aware base URL (from config.ts)
 *   - Auth token injection via Supabase session
 *   - Standard error handling (ErrorResponse envelope)
 *   - Typed request/response wrappers
 */

import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";
import { track } from "../lib/analytics";
import { getUsage } from "./billing";
import type { Application, AnswerItem } from "../types";
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
 * Checks quota before inserting. Throws QuotaExceededError if limit hit.
 */
export async function createApplication(jobId: string): Promise<Application> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new ApiError(401, "UNAUTHENTICATED", "Not authenticated");

  // Pre-flight quota check
  try {
    const usage = await getUsage();
    if (usage.monthly_remaining <= 0) {
      throw new QuotaExceededError(usage.plan, usage.monthly_used, usage.monthly_limit);
    }
  } catch (err) {
    if (err instanceof QuotaExceededError) throw err;
    // If usage endpoint fails, allow the insert (server-side RLS/triggers will catch)
    console.warn("Quota pre-check failed, proceeding:", err);
  }

  const { data, error } = await supabase
    .from("applications")
    .insert({ user_id: user.id, job_id: jobId, status: "QUEUED" })
    .select()
    .single();

  if (error) throw new ApiError(500, "CREATE_APPLICATION_FAILED", error.message);
  return data as Application;
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
