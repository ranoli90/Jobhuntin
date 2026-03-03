/**
 * Shared authentication utilities for mobile app.
 * Centralizes auth header generation to avoid duplication.
 */

import { getAuthToken } from "./supabase";

/**
 * Get authorization headers for API requests.
 * Centralized to avoid duplication across the app.
 */
export async function getAuthHeaders(): Promise<Record<string, string>> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }
  return {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

/**
 * Get authorization headers without content-type (for FormData).
 */
export async function getAuthHeadersForFormData(): Promise<Record<string, string>> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }
  return {
    "Authorization": `Bearer ${token}`,
  };
}
