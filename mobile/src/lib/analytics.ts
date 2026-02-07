/**
 * Client-side analytics tracking layer.
 *
 * Batches events in memory and flushes to POST /analytics/events
 * every FLUSH_INTERVAL_MS or when the buffer reaches FLUSH_THRESHOLD.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { supabase } from "./supabase";
import { API_BASE_URL } from "./config";
import type { AnalyticsEventType } from "./analyticsEvents";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const FLUSH_INTERVAL_MS = 5_000;
const FLUSH_THRESHOLD = 10;
const SESSION_KEY = "analytics_session_id";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface QueuedEvent {
  event_type: AnalyticsEventType;
  properties: Record<string, unknown>;
  session_id: string;
  user_id: string | null;
  tenant_id: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let _buffer: QueuedEvent[] = [];
let _sessionId: string | null = null;
let _flushTimer: ReturnType<typeof setInterval> | null = null;

// ---------------------------------------------------------------------------
// Session management
// ---------------------------------------------------------------------------

function generateUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

async function getSessionId(): Promise<string> {
  if (_sessionId) return _sessionId;
  let stored = await AsyncStorage.getItem(SESSION_KEY);
  if (!stored) {
    stored = generateUUID();
    await AsyncStorage.setItem(SESSION_KEY, stored);
  }
  _sessionId = stored;
  return stored;
}

/**
 * Rotate the session ID (e.g., on app foreground after long background).
 */
export async function rotateSession(): Promise<void> {
  _sessionId = generateUUID();
  await AsyncStorage.setItem(SESSION_KEY, _sessionId);
}

// ---------------------------------------------------------------------------
// Auth context helpers
// ---------------------------------------------------------------------------

async function getAuthContext(): Promise<{
  user_id: string | null;
  tenant_id: string | null;
}> {
  try {
    const {
      data: { user },
    } = await supabase.auth.getUser();
    // tenant_id is stored in user metadata by the backend
    const tenant_id =
      (user?.user_metadata?.tenant_id as string) ?? null;
    return { user_id: user?.id ?? null, tenant_id };
  } catch {
    return { user_id: null, tenant_id: null };
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Track an analytics event. Automatically attaches session, user, and tenant.
 */
export async function track(
  eventType: AnalyticsEventType,
  properties: Record<string, unknown> = {},
): Promise<void> {
  const sessionId = await getSessionId();
  const { user_id, tenant_id } = await getAuthContext();

  _buffer.push({
    event_type: eventType,
    properties,
    session_id: sessionId,
    user_id,
    tenant_id,
    created_at: new Date().toISOString(),
  });

  if (_buffer.length >= FLUSH_THRESHOLD) {
    flush();
  }
}

/**
 * Flush buffered events to the backend.
 */
export async function flush(): Promise<void> {
  if (_buffer.length === 0) return;

  const batch = [..._buffer];
  _buffer = [];

  try {
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

    await fetch(`${API_BASE_URL}/analytics/events`, {
      method: "POST",
      headers,
      body: JSON.stringify({ events: batch }),
    });
  } catch (err) {
    // On failure, push events back to buffer for retry
    _buffer.unshift(...batch);
    console.warn("Analytics flush failed, will retry:", err);
  }
}

// ---------------------------------------------------------------------------
// Auto-flush timer
// ---------------------------------------------------------------------------

export function startAutoFlush(): void {
  if (_flushTimer) return;
  _flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);
}

export function stopAutoFlush(): void {
  if (_flushTimer) {
    clearInterval(_flushTimer);
    _flushTimer = null;
  }
}
