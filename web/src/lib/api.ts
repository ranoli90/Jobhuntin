/**
 * API client for backend. Sends Supabase JWT on every request so the API can
 * resolve user and tenant. Use this for all VITE_API_URL requests.
 */

import { supabase } from "./supabase";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

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
}

function handleApiError(resp: Response, body: string): never {
  if (resp.status === 401) {
    const returnTo = typeof window !== "undefined" ? encodeURIComponent(window.location.pathname + window.location.search) : "";
    window.location.href = `/login?returnTo=${returnTo}`;
    throw new Error("Session expired. Please sign in again.");
  }
  throw new Error(body || `HTTP ${resp.status}`);
}

/**
 * Fetch with base URL, credentials, and Supabase JWT. Use for all backend calls.
 */
export async function apiFetch(
  path: string,
  options: ApiRequestOptions = {}
): Promise<Response> {
  const url = path.startsWith("http") ? path : `${API_BASE.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const authHeaders = await getAuthHeaders();
  const { skipJsonContentType, headers: customHeaders, ...rest } = options;
  const headers: HeadersInit = {
    ...authHeaders,
    ...(skipJsonContentType ? {} : { "Content-Type": "application/json" }),
    ...customHeaders,
  };
  return fetch(url, {
    ...rest,
    credentials: "include",
    headers,
  });
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

/** POST FormData (e.g. file upload). On 401 redirects to login. */
export async function apiPostFormData<T = unknown>(path: string, body: FormData): Promise<T> {
  const authHeaders = await getAuthHeaders();
  const h = { ...(authHeaders as Record<string, string>) };
  delete h["Content-Type"];
  const url = `${API_BASE.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const resp = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: h,
    body,
  });
  const text = await resp.text();
  if (!resp.ok) handleApiError(resp, text);
  return JSON.parse(text) as T;
}
