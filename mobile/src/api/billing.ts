/**
 * Billing API client — Stripe checkout, portal, usage, and status.
 *
 * Used by the upgrade prompt and settings screens.
 */

import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BillingStatus {
  tenant_id: string;
  plan: string;
  provider: string | null;
  provider_customer_id: string | null;
  subscription_status: string;
  current_period_end: string | null;
}

export interface UsageInfo {
  tenant_id: string;
  plan: string;
  monthly_limit: number;
  monthly_used: number;
  monthly_remaining: number;
  concurrent_limit: number;
  concurrent_used: number;
  percentage_used: number;
}

export interface CheckoutResult {
  checkout_url: string;
  session_id: string;
}

export interface PortalResult {
  portal_url: string;
}

// ---------------------------------------------------------------------------
// Auth helper
// ---------------------------------------------------------------------------

async function getAuthHeaders(): Promise<Record<string, string>> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const token = session?.access_token;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`Billing API error ${resp.status}: ${body}`);
  }
  return resp.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

/** Fetch current billing status for the tenant. */
export async function getBillingStatus(): Promise<BillingStatus> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_BASE_URL}/billing/status`, { headers });
  return handleResponse<BillingStatus>(resp);
}

/** Fetch current quota usage for the tenant. */
export async function getUsage(): Promise<UsageInfo> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_BASE_URL}/billing/usage`, { headers });
  return handleResponse<UsageInfo>(resp);
}

/** Create a Stripe Checkout Session for FREE → PRO upgrade. */
export async function createCheckout(
  successUrl = "sorce://billing/success",
  cancelUrl = "sorce://billing/cancel",
): Promise<CheckoutResult> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_BASE_URL}/billing/checkout`, {
    method: "POST",
    headers,
    body: JSON.stringify({ success_url: successUrl, cancel_url: cancelUrl }),
  });
  return handleResponse<CheckoutResult>(resp);
}

/** Create a Stripe Customer Portal session for managing subscription. */
export async function createPortalSession(): Promise<PortalResult> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_BASE_URL}/billing/portal`, {
    method: "POST",
    headers,
  });
  return handleResponse<PortalResult>(resp);
}
