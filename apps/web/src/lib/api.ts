/**
 * API client for backend. Sends Supabase JWT on every request so the API can
 * resolve user and tenant. Use this for all VITE_API_URL requests.
 *
 * Features:
 *  - Automatic 401 → redirect to /login with return path
 *  - Retry with exponential back-off for 429 and 5xx errors
 *  - User-friendly error messages mapped from HTTP status codes
 */

import { supabase } from "./supabase";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

/** Maximum number of automatic retries for retryable errors. */
const MAX_RETRIES = 2;

/** Base delay in ms for exponential back-off (doubled on each retry). */
const BASE_DELAY_MS = 1000;

export function getApiBase(): string {
  return API_BASE;
}

export async function getAuthHeaders(): Promise<HeadersInit> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (session?.access_token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${session.access_token}`;
  }
  return headers;
}

export interface ApiRequestOptions extends Omit<RequestInit, "headers"> {
  headers?: HeadersInit;
  /** If true, do not send JSON Content-Type (e.g. for FormData). */
  skipJsonContentType?: boolean;
  /** Request timeout in milliseconds. Defaults to 10000. */
  timeout?: number;
}

// ---------------------------------------------------------------------------
// User-friendly error messages per HTTP status
// ---------------------------------------------------------------------------
function friendlyMessage(status: number, body: string): string {
  switch (status) {
    case 400:
      return tryParseMessage(body) || "The request was invalid. Please check your input.";
    case 401:
      return "Session expired. Please sign in again.";
    case 403:
      return "You don't have permission to perform this action.";
    case 404:
      return "The requested resource could not be found.";
    case 409:
      return tryParseMessage(body) || "A conflict occurred — this resource may already exist.";
    case 422:
      return tryParseMessage(body) || "Some of the provided data is invalid. Please review and try again.";
    case 429:
      return "You're making requests too quickly. Please wait a moment and try again.";
    default:
      if (status >= 500) {
        return "Something went wrong on our end. Please try again in a moment.";
      }
      return tryParseMessage(body) || `Unexpected error (HTTP ${status})`;
  }
}

/** Try to extract a `message` or `detail` field from a JSON body. */
function tryParseMessage(body: string): string | null {
  try {
    const json = JSON.parse(body);
    return json.message || json.detail || json.error || null;
  } catch {
    return null;
  }
}

/** Is this status code safe to retry? */
function isRetryable(status: number, method?: string): boolean {
  const retryableStatus = status === 429 || status >= 500;
  if (!retryableStatus) return false;

  // Only retry idempotent methods by default
  const idempotentMethods = ["GET", "PUT", "DELETE", "HEAD", "OPTIONS"];
  return idempotentMethods.includes(method?.toUpperCase() || "GET");
}

/** Wait for a duration, respecting `Retry-After` header if present. */
function retryDelay(attempt: number, resp?: Response): number {
  const retryAfter = resp?.headers?.get("Retry-After");
  if (retryAfter) {
    const seconds = parseInt(retryAfter, 10);
    if (!isNaN(seconds)) return seconds * 1000;
  }
  // Exponential back-off with jitter
  const delay = BASE_DELAY_MS * Math.pow(2, attempt);
  return delay + Math.random() * 500;
}

function handleApiError(resp: Response, body: string): never {
  if (resp.status === 401) {
    const returnTo = typeof window !== "undefined" ? encodeURIComponent(window.location.pathname + window.location.search) : "";
    window.location.href = `/login?returnTo=${returnTo}`;
  }
  const msg = friendlyMessage(resp.status, body);
  const err = new Error(msg) as Error & { status: number };
  err.status = resp.status;
  throw err;
}

// ---------------------------------------------------------------------------
// Core fetch with retry
// ---------------------------------------------------------------------------

/**
 * Fetch with base URL, credentials, Supabase JWT, and automatic retry for
 * transient server errors (429, 5xx).
 */
export async function apiFetch(
  path: string,
  options: ApiRequestOptions = {}
): Promise<Response> {
  const {
    skipJsonContentType,
    headers: customHeaders,
    timeout = 10000,
    ...rest
  } = options;

  const url = path.startsWith("http") ? path : `${API_BASE.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const authHeaders = await getAuthHeaders();
  const headers: HeadersInit = {
    ...authHeaders,
    ...(skipJsonContentType ? {} : { "Content-Type": "application/json" }),
    ...customHeaders,
  };

  let lastResp: Response | undefined;
  let lastError: any;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const resp = await fetch(url, {
        ...rest,
        credentials: "include",
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (resp.ok) return resp;

      // Don't retry non-retryable errors
      if (!isRetryable(resp.status, options.method) || attempt === MAX_RETRIES) {
        return resp;
      }

      lastResp = resp;
    } catch (err: any) {
      clearTimeout(timeoutId);
      lastError = err;

      // Retry on network errors/timeouts if it's an idempotent method
      if (!isRetryable(503, options.method) || attempt === MAX_RETRIES) {
        throw err;
      }
    }

    const delay = retryDelay(attempt, lastResp);
    await new Promise(r => setTimeout(r, delay));
  }

  if (lastResp) return lastResp;
  throw lastError || new Error("Request failed");
}

/** GET and parse JSON. Throws if !resp.ok; on 401 redirects to login. */
export async function apiGet<T = unknown>(path: string): Promise<T> {
  const resp = await apiFetch(path, { method: "GET" });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  return JSON.parse(text) as T;
}

/** Download a file from the API. */
export async function downloadFile(path: string, filename: string) {
  const resp = await apiFetch(path, { method: "GET" });
  if (!resp.ok) {
    const text = await resp.text();
    handleApiError(resp, text);
  }
  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

/** POST JSON and parse JSON. Throws if !resp.ok; on 401 redirects to login. */
export async function apiPost<T = unknown>(path: string, body?: unknown): Promise<T> {
  const resp = await apiFetch(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  return JSON.parse(text) as T;
}

/** PATCH JSON and parse JSON. Throws if !resp.ok; on 401 redirects to login. */
export async function apiPatch<T = unknown>(path: string, body: unknown): Promise<T> {
  const resp = await apiFetch(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  return JSON.parse(text) as T;
}

/** DELETE and parse JSON. Throws if !resp.ok; on 401 redirects to login. */
export async function apiDelete<T = unknown>(path: string): Promise<T> {
  const resp = await apiFetch(path, { method: "DELETE" });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  return JSON.parse(text) as T;
}

/** POST FormData (e.g. file upload). On 401 redirects to login. */
export async function apiPostFormData<T = unknown>(path: string, body: FormData): Promise<T> {
  const authHeaders = await getAuthHeaders();
  const h = { ...(authHeaders as Record<string, string>) };
  delete h["Content-Type"];
  const url = `${API_BASE.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;

  let lastResp: Response | undefined;
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const resp = await fetch(url, {
      method: "POST",
      credentials: "include",
      headers: h,
      body,
    });

    if (resp.ok) {
      const text = await resp.text();
      return JSON.parse(text) as T;
    }

    if (!isRetryable(resp.status) || attempt === MAX_RETRIES) {
      const text = await resp.text();
      handleApiError(resp, text);
    }

    lastResp = resp;
    const delay = retryDelay(attempt, resp);
    await new Promise(r => setTimeout(r, delay));
  }

  // Shouldn't reach here, but satisfy TypeScript
  const text = await lastResp!.text();
  handleApiError(lastResp!, text);
}
