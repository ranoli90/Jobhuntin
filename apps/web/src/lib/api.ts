/**
 * API client for backend. Sends JWT token on every request so the API can
 * resolve user and tenant. Use this for all VITE_API_URL requests.
 *
 * Features:
 *  - Automatic 401 → redirect to /login with return path
 *  - Retry with exponential back-off for 429 and 5xx errors
 *  - User-friendly error messages mapped from HTTP status codes
 *  - Standardized API response format handling (Phase 6.1)
 */

// Token storage key
// SECURITY: JWT in localStorage is vulnerable to XSS. Production uses httpOnly cookies.
// The localStorage token is kept for backward compatibility during transition.
// All requests include credentials so httpOnly cookies are sent automatically.
const AUTH_TOKEN_KEY = "auth_token";

// #58: Prefer explicit API base; fall back to same-origin /api; never use empty string
const API_BASE = (() => {
  const environment = (
    import.meta.env.VITE_API_URL as string | undefined
  )?.trim();
  if (environment) return environment;
  if (typeof window !== "undefined") return `${window.location.origin}/api`;
  return "/api"; // SSR fallback
})();

/** Maximum number of automatic retries for retryable errors. */
const MAX_RETRIES = 2;

/** Base delay in ms for exponential back-off (doubled on each retry). */
const BASE_DELAY_MS = 1000;

/** Maximum retry delay in ms */
const MAX_DELAY_MS = 30_000;

// ---------------------------------------------------------------------------
// Standardized API Response Types (Phase 6.1)
// ---------------------------------------------------------------------------=

/** Metadata included in every API response. */
export interface ResponseMeta {
  version: string;
  timestamp: string;
  request_id?: string;
}

/** Detailed error information for a specific field. */
export interface ErrorDetail {
  field?: string;
  message: string;
}

/** Error information structure from backend. */
export interface ErrorInfo {
  code: string;
  message: string;
  details?: ErrorDetail[];
  request_id?: string;
}

/**
 * Standardized API response wrapper.
 * - Success: { success: true, data: T, meta: { version, timestamp, request_id } }
 * - Error: { success: false, error: { code, message, details, request_id } }
 */
export interface ApiResponse<T> {
  success: true;
  data: T;
  meta: ResponseMeta;
}

/** Standardized error response from backend. */
export interface ApiErrorResponse {
  success: false;
  error: ErrorInfo;
}

/** Union type for all API responses. */
export type ApiResult<T> = ApiResponse<T> | ApiErrorResponse;

/** Check if a response is a successful API response. */
export function isApiSuccess<T>(response: ApiResult<T>): response is ApiResponse<T> {
  return response.success === true;
}

/** Check if a response is an error API response. */
export function isApiError<T>(response: ApiResult<T>): response is ApiErrorResponse {
  return response.success === false;
}

// ---------------------------------------------------------------------------
// Typed Error Classes
// ---------------------------------------------------------------------------=

/** Base API Error with typed error code. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number,
    public readonly details?: ErrorDetail[],
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Authentication/Authorization error (401, 403). */
export class AuthError extends ApiError {
  constructor(message: string, code: string = "AUTH_ERROR", requestId?: string) {
    super(message, code, 401, undefined, requestId);
    this.name = "AuthError";
  }
}

/** Resource not found error (404). */
export class NotFoundError extends ApiError {
  constructor(message: string = "Resource not found", requestId?: string) {
    super(message, "NOT_FOUND", 404, undefined, requestId);
    this.name = "NotFoundError";
  }
}

/** Validation error (400, 422). */
export class ValidationError extends ApiError {
  constructor(message: string, details?: ErrorDetail[], requestId?: string) {
    super(message, "VALIDATION_ERROR", 400, details, requestId);
    this.name = "ValidationError";
  }
}

/** Rate limit error (429). */
export class RateLimitError extends ApiError {
  constructor(message: string = "Rate limit exceeded", requestId?: string) {
    super(message, "RATE_LIMIT_EXCEEDED", 429, undefined, requestId);
    this.name = "RateLimitError";
  }
}

/** Internal server error (5xx). */
export class InternalError extends ApiError {
  constructor(message: string = "Internal server error", requestId?: string) {
    super(message, "INTERNAL_ERROR", 500, undefined, requestId);
    this.name = "InternalError";
  }
}

/**
 * Create typed error from API error response.
 * Maps error codes to appropriate error types.
 */
export function createApiError(errorInfo: ErrorInfo, httpStatus: number): ApiError {
  const { code, message, details, request_id } = errorInfo;

  // Map error codes to typed errors
  switch (code) {
    case "AUTH_ERROR":
    case "INVALID_TOKEN":
    case "TOKEN_EXPIRED":
      return new AuthError(message, code, request_id);
    case "NOT_FOUND":
      return new NotFoundError(message, request_id);
    case "VALIDATION_ERROR":
    case "INVALID_INPUT":
      return new ValidationError(message, details, request_id);
    case "RATE_LIMIT_EXCEEDED":
      return new RateLimitError(message, request_id);
    case "INTERNAL_ERROR":
    case "DATABASE_ERROR":
      return new InternalError(message, request_id);
    default:
      return new ApiError(message, code, httpStatus, details, request_id);
  }
}

/**
 * Parse standardized API response.
 * Returns the data on success, throws ApiError on failure.
 * Maintains backward compatibility with non-standard responses.
 */
export function parseApiResponse<T>(json: unknown, httpStatus: number): T {
  // Check if this is a standardized response format
  if (json !== null && typeof json === "object") {
    const response = json as { success?: boolean; data?: unknown; error?: ErrorInfo };

    // Handle standardized error response
    if (response.success === false && response.error) {
      const error = createApiError(response.error, httpStatus);

      // Log request_id for debugging
      if (response.error.request_id) {
        console.debug(`[API Error] request_id: ${response.error.request_id}, code: ${response.error.code}`);
      }

      throw error;
    }

    // Handle standardized success response - extract data
    if (response.success === true && response.data !== undefined) {
      return response.data as T;
    }

    // Backward compatibility: non-standard response with success field
    if ("success" in response && response.data === undefined) {
      // Some endpoints might return { success: true, ... } without data wrapper
      // Return the entire response minus the success field
      const { success, ...rest } = response as Record<string, unknown>;
      return rest as T;
    }
  }

  // Backward compatibility: non-standard response (raw data)
  // Return as-is for endpoints that haven't been updated yet
  return json as T;
}

/**
 * Utility function to retry an async operation with exponential backoff
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  options: {
    maxRetries?: number;
    baseDelayMs?: number;
    maxDelayMs?: number;
    shouldRetry?: (error: Error, attempt: number) => boolean;
    onRetry?: (error: Error, attempt: number) => void;
  } = {},
): Promise<T> {
  const {
    maxRetries = 3,
    baseDelayMs = BASE_DELAY_MS,
    maxDelayMs = MAX_DELAY_MS,
    shouldRetry = (error: Error & { status?: number }) => {
      // Retry on network errors and 5xx status
      const status = error.status;
      return !status || status >= 500 || status === 429;
    },
    onRetry,
  } = options;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      const error_ = error as Error;
      lastError = error_;

      // Check if we should retry
      if (attempt === maxRetries || !shouldRetry(error_, attempt)) {
        throw error_;
      }

      // Calculate delay with exponential backoff and jitter
      const delay = Math.min(
        baseDelayMs * Math.pow(2, attempt) + Math.random() * 500,
        maxDelayMs,
      );

      // Notify about retry
      if (onRetry) {
        onRetry(error_, attempt);
      }

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

export function getApiBase(): string {
  return API_BASE;
}

/**
 * S1 (Audit): JWT in localStorage when api_public_url unset (legacy). When API_PUBLIC_URL is set,
 * magic link uses /auth/verify-magic → httpOnly cookie. Token from cookie is sent via credentials.
 */
export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;

  // Note: httpOnly cookies (jobhuntin_auth) cannot be read from document.cookie.
  // Session check is done by /me/profile in AuthContext; server validates on each request.
  // We always send credentials: "include" so httpOnly cookies are sent automatically.

  // SECURITY: No localStorage fallback for production - only use httpOnly cookies
  // This prevents XSS attacks from stealing auth tokens
  // VITE_ALLOW_LOCALSTORAGE_AUTH: allow localStorage token for local E2E testing (localhost only)
  const allowLocalStorage =
    import.meta.env.DEV ||
    (import.meta.env.VITE_ALLOW_LOCALSTORAGE_AUTH === "true" &&
      typeof window !== "undefined" &&
      /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/.test(window.location.origin));
  if (allowLocalStorage) {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }
  if (import.meta.env.PROD) {
    return null;
  }
  return null;
}

/** Read csrf cookie set by backend (starlette-csrf) */
function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/** Ensure CSRF cookie is set before mutations. Call before PATCH/POST/DELETE when token is missing. */
let _csrfPreparePromise: Promise<void> | null = null;
export async function ensureCsrfCookie(): Promise<void> {
  if (getCsrfToken()) return;
  if (_csrfPreparePromise) return _csrfPreparePromise;
  _csrfPreparePromise = (async () => {
    try {
      const base = getApiBase();
      if (base) await fetch(`${base.replace(/\/$/, "")}/csrf/prepare`, { credentials: "include" });
    } catch {
      // Ignore - mutations may fail with 403
    }
  })();
  await _csrfPreparePromise;
}

export function setAuthToken(token: string) {
  // SECURITY: Only store tokens in localStorage for development
  // In production, tokens should only be stored in httpOnly cookies
  if (import.meta.env.DEV) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    console.warn("Token storage in localStorage disabled in production");
  }
}

export function clearAuthToken() {
  // SECURITY: Only clear tokens from localStorage for development
  // In production, tokens should only be cleared via httpOnly cookies
  if (import.meta.env.DEV) {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  } else {
    console.warn("Token clearing from localStorage disabled in production");
  }
}

export async function getAuthHeaders(): Promise<HeadersInit> {
  const token = getAuthToken();
  const csrf = getCsrfToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (csrf) {
    headers["x-csrftoken"] = csrf;
  }
  return headers;
}

export interface ApiRequestOptions extends Omit<RequestInit, "headers"> {
  headers?: HeadersInit;
  /** If true, do not send JSON Content-Type (e.g. for FormData). */
  skipJsonContentType?: boolean;
  /** Request timeout in milliseconds. Defaults to 15000 (N1: slow 3G). */
  timeout?: number;
}

// ---------------------------------------------------------------------------
// User-friendly error messages per HTTP status
// ---------------------------------------------------------------------------
function friendlyMessage(status: number, body: string): string {
  switch (status) {
    case 400: {
      return tryParseMessage(body) || "Please check your input and try again.";
    }
    case 401: {
      return "Session expired. Please sign in again.";
    }
    case 403: {
      return "You don't have permission to perform this action.";
    }
    case 404: {
      return "The requested resource could not be found.";
    }
    case 409: {
      return (
        tryParseMessage(body) ||
        "A conflict occurred — this resource may already exist."
      );
    }
    case 422: {
      return (
        tryParseMessage(body) ||
        "Some of the provided data is invalid. Please review and try again."
      );
    }
    case 429: {
      return "You're making requests too quickly. Please wait a moment and try again.";
    }
    default: {
      if (status >= 500) {
        return "Something went wrong on our end. Please try again in a moment.";
      }
      return tryParseMessage(body) || `Unexpected error (HTTP ${status})`;
    }
  }
}

/** Try to extract a `message` or `detail` field from a JSON body. */
function tryParseMessage(body: string): string | null {
  try {
    const json = JSON.parse(body);
    if (typeof json === "object" && json !== null) {
      // Extract the first string-type field we find
      for (const key of ["message", "detail", "error"]) {
        const value = json[key];
        if (typeof value === "string" && value.length > 0) return value;
        // FastAPI can return detail as array: [{"msg":"...","type":"..."}]
        if (Array.isArray(value) && value.length > 0) {
          const first = value[0];
          if (typeof first === "string") return first;
          if (typeof first === "object" && first?.msg) return String(first.msg);
        }
        // detail can be an object like {"msg": "..."}
        if (
          typeof value === "object" &&
          value !== null &&
          !Array.isArray(value)
        ) {
          if (typeof value.msg === "string") return value.msg;
          if (typeof value.message === "string") return value.message;
        }
      }
      // Last resort: stringify, but only if it's small enough to be useful
      const string_ = JSON.stringify(json);
      if (string_.length < 200) return string_;
    }
    if (typeof json === "string") return json;
    return null;
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
    const seconds = Number.parseInt(retryAfter, 10);
    if (!isNaN(seconds)) return seconds * 1000;
  }
  // Exponential back-off with jitter
  const delay = BASE_DELAY_MS * Math.pow(2, attempt);
  return delay + Math.random() * 500;
}

let _redirecting = false;

/** Handle API error (401 redirect, throw with message). Exported for custom fetch flows (e.g. blob download). */
export function handleApiError(resp: Response, body: string): never {
  if (resp.status === 401 && !_redirecting) {
    const isLoginPage =
      typeof window !== "undefined" && window.location.pathname === "/login";
    if (!isLoginPage) {
      _redirecting = true;
      const returnTo =
        typeof window === "undefined"
          ? ""
          : encodeURIComponent(
              window.location.pathname + window.location.search,
            );
      const isOnboarding =
        typeof window !== "undefined" &&
        window.location.pathname.startsWith("/app/onboarding");
      if (isOnboarding) {
        import("../hooks/useOnboarding")
          .then((m) => m.flushOnboardingBeforeRedirect())
          .catch(() => {});
      }
      const event_ = new CustomEvent("auth:unauthorized", {
        detail: { returnTo },
      });
      window.dispatchEvent(event_);
      // AuthContext handles redirect; avoid double redirect by not redirecting here
    }
  }

  // Try to parse as standardized API error response first
  let requestId: string | undefined;
  let errorCode = "UNKNOWN_ERROR";
  let errorMessage = "";

  try {
    const json = JSON.parse(body);
    if (json && typeof json === "object") {
      const response = json as { success?: boolean; error?: ErrorInfo };

      // Check for standardized error format
      if (response.success === false && response.error) {
        requestId = response.error.request_id;
        errorCode = response.error.code;
        errorMessage = response.error.message;

        // Log request_id for debugging
        if (requestId) {
          console.debug(`[API Error] request_id: ${requestId}, code: ${errorCode}`);
        }

        // Create typed error
        const error = createApiError(response.error, resp.status);
        throw error;
      }
    }
  } catch (e) {
    // If it's already an ApiError, re-throw it
    if (e instanceof ApiError) {
      throw e;
    }
    // Otherwise continue with fallback message parsing
  }

  // Fallback: try legacy message parsing
  const parsedMessage = tryParseMessage(body);
  const message = parsedMessage
    ? `${parsedMessage} (HTTP ${resp.status})`
    : friendlyMessage(resp.status, body);

  // Create error with sanitized information for production
  const error = new Error(message) as Error & {
    status: number;
    code: string;
    rawBody: string;
    sanitized: boolean;
    requestId?: string;
  };
  error.status = resp.status;
  error.code = errorCode;
  error.requestId = requestId;

  // In production, sanitize sensitive information
  if (import.meta.env.PROD) {
    error.sanitized = true;
    // Only include raw body in development for debugging
    error.rawBody = "[Sanitized in production]";
  } else {
    error.sanitized = false;
    error.rawBody = body;
  }

  throw error;
}

/** Call after successful re-authentication to allow future 401 redirects. */
export function resetAuthRedirectGuard() {
  _redirecting = false;
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
  options: ApiRequestOptions = {},
): Promise<Response> {
  const {
    skipJsonContentType,
    headers: customHeaders,
    timeout = 15_000,
    ...rest
  } = options;

  const url = path.startsWith("http")
    ? path
    : `${API_BASE.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const method = (options.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
    await ensureCsrfCookie();
  }
  const authHeaders = await getAuthHeaders();
  const headers: HeadersInit = {
    ...authHeaders,
    ...(skipJsonContentType ? {} : { "Content-Type": "application/json" }),
    ...customHeaders,
  };

  let lastResp: Response | undefined;
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    // If user provided a signal, listen to it
    const onUserAbort = () => controller.abort();
    if (options.signal) {
      options.signal.addEventListener("abort", onUserAbort);
    }

    try {
      const resp = await fetch(url, {
        ...rest,
        credentials: "include",
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      if (options.signal) {
        options.signal.removeEventListener("abort", onUserAbort);
      }

      if (resp.ok) return resp;

      // Don't retry non-retryable errors
      if (
        !isRetryable(resp.status, options.method) ||
        attempt === MAX_RETRIES
      ) {
        return resp;
      }

      lastResp = resp;
    } catch (error) {
      const error_ = error as Error;
      clearTimeout(timeoutId);
      if (options.signal) {
        options.signal.removeEventListener("abort", onUserAbort);
      }
      lastError = error_;

      // Retry on network errors/timeouts if it's an idempotent method
      if (!isRetryable(503, options.method) || attempt === MAX_RETRIES) {
        throw error_;
      }
    }

    const delay = retryDelay(attempt, lastResp);
    await new Promise((r) => setTimeout(r, delay));
  }

  if (lastResp) return lastResp;
  throw lastError || new Error("Request failed");
}

/** GET and parse JSON. Throws if !resp.ok; on 401 redirects to login.
 * Handles standardized API response format.
 */
export async function apiGet<T = unknown>(path: string): Promise<T> {
  const resp = await apiFetch(path, { method: "GET" });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  if (!text) return {} as T;
  const json = JSON.parse(text);
  // Parse standardized response format
  return parseApiResponse<T>(json, resp.status);
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
  document.body.append(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
}

/** POST JSON and parse JSON. Throws if !resp.ok; on 401 redirects to login.
 * Handles standardized API response format.
 */
export async function apiPost<T = unknown>(
  path: string,
  body?: unknown,
  options?: Pick<ApiRequestOptions, "headers">,
): Promise<T> {
  const resp = await apiFetch(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
    ...options,
  });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  if (!text) return {} as T;
  const json = JSON.parse(text);
  // Parse standardized response format
  return parseApiResponse<T>(json, resp.status);
}

/** PATCH JSON and parse JSON. Throws if !resp.ok; on 401 redirects to login.
 * Handles standardized API response format.
 */
export async function apiPatch<T = unknown>(
  path: string,
  body: unknown,
): Promise<T> {
  const resp = await apiFetch(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  if (!text) return {} as T;
  const json = JSON.parse(text);
  // Parse standardized response format
  return parseApiResponse<T>(json, resp.status);
}

/** PUT JSON and parse JSON. Throws if !resp.ok; on 401 redirects to login.
 * Handles standardized API response format.
 */
export async function apiPut<T = unknown>(
  path: string,
  body?: unknown,
): Promise<T> {
  const resp = await apiFetch(path, {
    method: "PUT",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  if (!text) return {} as T;
  const json = JSON.parse(text);
  // Parse standardized response format
  return parseApiResponse<T>(json, resp.status);
}

/** DELETE and parse JSON. Throws if !resp.ok; on 401 redirects to login.
 * Handles standardized API response format.
 */
export async function apiDelete<T = unknown>(path: string): Promise<T> {
  const resp = await apiFetch(path, { method: "DELETE" });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  if (!text) return {} as T;
  const json = JSON.parse(text);
  // Parse standardized response format
  return parseApiResponse<T>(json, resp.status);
}

/** POST FormData (e.g. file upload). On 401 redirects to login.
 * Handles standardized API response format.
 */
export async function apiPostFormData<T = unknown>(
  path: string,
  body: FormData,
  options: ApiRequestOptions = {},
): Promise<T> {
  const authHeaders = await getAuthHeaders();
  const h = { ...(authHeaders as Record<string, string>) };
  delete h["Content-Type"];
  const url = `${API_BASE.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;

  let lastResp: Response | undefined;
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60_000); // 60s for uploads

    // Forward user-provided signal
    const onUserAbort = () => controller.abort();
    if (options.signal) {
      options.signal.addEventListener("abort", onUserAbort);
    }

    try {
      const resp = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: h,
        body,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      if (options.signal) {
        options.signal.removeEventListener("abort", onUserAbort);
      }

      if (resp.ok) {
        const text = await resp.text();
        if (!text) return {} as T;
        const json = JSON.parse(text);
        // Parse standardized response format
        return parseApiResponse<T>(json, resp.status);
      }

      if (!isRetryable(resp.status, "POST") || attempt === MAX_RETRIES) {
        const text = await resp.text();
        handleApiError(resp, text);
      }

      lastResp = resp;
    } catch (error) {
      clearTimeout(timeoutId);
      if (options.signal) {
        options.signal.removeEventListener("abort", onUserAbort);
      }
      throw error;
    }

    const delay = retryDelay(attempt, lastResp);
    await new Promise((r) => setTimeout(r, delay));
  }

  // Shouldn't reach here, but satisfy TypeScript
  const text = await lastResp!.text();
  handleApiError(lastResp!, text);
}

/** Unified API object for legacy/convenience usage. */
export const api = {
  get: apiGet,
  post: apiPost,
  patch: apiPatch,
  delete: apiDelete,
  postFormData: apiPostFormData,
};
