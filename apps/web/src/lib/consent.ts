/**
 * Consent API Service
 * Handles consent management with the backend API
 */

import { api } from "./api";

export interface ConsentPreferences {
  essential: boolean;
  analytics: boolean;
  marketing: boolean;
  cookies: boolean;
  functional: boolean;
}

export interface ConsentResponse {
  preferences: ConsentPreferences;
  user_id: string | null;
  anonymous_id: string | null;
  version: string;
  last_updated: string;
}

export interface ConsentExportResponse {
  user_id: string | null;
  anonymous_id: string | null;
  consents: Array<{
    id: string;
    consent_type: string;
    granted: boolean;
    granted_at: string | null;
    revoked_at: string | null;
    ip_address: string | null;
    user_agent: string | null;
    version: string;
    source: string;
    created_at: string | null;
    updated_at: string | null;
  }>;
  audit_log: Array<{
    id: string;
    consent_type: string;
    action: string;
    previous_value: boolean | null;
    new_value: boolean | null;
    ip_address: string | null;
    user_agent: string | null;
    created_at: string;
    reason: string | null;
  }>;
  exported_at: string;
  version: string;
}

// Generate anonymous ID for tracking anonymous users
function getAnonymousId(): string {
  const ANONYMOUS_ID_KEY = "jobhuntin-anonymous-id";

  let anonymousId = localStorage.getItem(ANONYMOUS_ID_KEY);
  if (!anonymousId) {
    anonymousId = crypto.randomUUID();
    localStorage.setItem(ANONYMOUS_ID_KEY, anonymousId);
  }
  return anonymousId;
}

// Get consent preferences from backend
export async function getConsent(): Promise<ConsentResponse> {
  const anonymousId = getAnonymousId();

  try {
    const response = await api.get<ConsentResponse>("/consent", {
      headers: {
        "X-Anonymous-ID": anonymousId,
      },
    });
    return response.data;
  } catch {
    // Return default preferences if API fails
    return {
      preferences: {
        essential: true,
        analytics: false,
        marketing: false,
        cookies: false,
        functional: false,
      },
      user_id: null,
      anonymous_id: anonymousId,
      version: "2.0",
      last_updated: new Date().toISOString(),
    };
  }
}

// Save consent preferences to backend
export async function saveConsent(
  preferences: ConsentPreferences,
): Promise<ConsentResponse> {
  const anonymousId = getAnonymousId();

  const response = await api.post<ConsentResponse>(
    "/consent",
    {
      preferences,
      anonymous_id: anonymousId,
      version: "2.0",
    },
    {
      headers: {
        "X-Anonymous-ID": anonymousId,
      },
    },
  );
  return response.data;
}

// Revoke a specific consent type
export async function revokeConsent(consentType: string): Promise<ConsentResponse> {
  const anonymousId = getAnonymousId();

  const response = await api.delete<ConsentResponse>(`/consent/${consentType}`, {
    headers: {
      "X-Anonymous-ID": anonymousId,
    },
  });
  return response.data;
}

// Export all consent data for GDPR
export async function exportConsentData(): Promise<ConsentExportResponse> {
  const anonymousId = getAnonymousId();

  const response = await api.get<ConsentExportResponse>("/consent/export", {
    headers: {
      "X-Anonymous-ID": anonymousId,
    },
  });
  return response.data;
}
