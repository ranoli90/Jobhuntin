/**
 * Home Screen Widget Config — exposes data for iOS/Android widgets.
 *
 * Widget shows: "3 apps in progress · 2 need your input"
 * Tapping deep-links to the HOLD screen or dashboard.
 *
 * For Expo, widget data is shared via expo-shared-preferences
 * or a native module. This module prepares the data payload.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { supabase } from "../../lib/supabase";
import { API_BASE_URL } from "../../lib/config";

const WIDGET_DATA_KEY = "sorce_widget_data";

export interface WidgetData {
  active_count: number;
  hold_count: number;
  completed_today: number;
  last_updated: string;
  deep_link: string;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {};
}

/**
 * Fetch current widget data from API and persist to shared storage
 * for native widget consumption.
 */
export async function refreshWidgetData(): Promise<WidgetData> {
  try {
    const h = await getAuthHeaders();
    const r = await fetch(`${API_BASE_URL}/me/dashboard`, { headers: h });

    let data: WidgetData;
    if (r.ok) {
      const d = await r.json();
      data = {
        active_count: d.active_count || 0,
        hold_count: d.hold_count || 0,
        completed_today: d.completed_today || 0,
        last_updated: new Date().toISOString(),
        deep_link: d.hold_count > 0
          ? "sorce://applications?filter=REQUIRES_INPUT"
          : "sorce://dashboard",
      };
    } else {
      data = {
        active_count: 0, hold_count: 0, completed_today: 0,
        last_updated: new Date().toISOString(),
        deep_link: "sorce://dashboard",
      };
    }

    // Persist for native widget layer
    await AsyncStorage.setItem(WIDGET_DATA_KEY, JSON.stringify(data));

    // If expo-shared-preferences is available, write there too
    try {
      const SharedPreferences = require("expo-shared-preferences");
      await SharedPreferences.setItemAsync("widget_active", String(data.active_count));
      await SharedPreferences.setItemAsync("widget_hold", String(data.hold_count));
      await SharedPreferences.setItemAsync("widget_today", String(data.completed_today));
      await SharedPreferences.setItemAsync("widget_link", data.deep_link);
    } catch {
      // expo-shared-preferences may not be installed
    }

    return data;
  } catch (e) {
    console.error("Widget refresh failed:", e);
    return {
      active_count: 0, hold_count: 0, completed_today: 0,
      last_updated: new Date().toISOString(),
      deep_link: "sorce://dashboard",
    };
  }
}

/**
 * Get cached widget data (for fast reads without network).
 */
export async function getCachedWidgetData(): Promise<WidgetData | null> {
  try {
    const raw = await AsyncStorage.getItem(WIDGET_DATA_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Widget display strings for native rendering.
 */
export function formatWidgetDisplay(data: WidgetData): {
  title: string;
  subtitle: string;
  badge: number;
} {
  const parts: string[] = [];
  if (data.active_count > 0) parts.push(`${data.active_count} in progress`);
  if (data.hold_count > 0) parts.push(`${data.hold_count} need input`);
  if (data.completed_today > 0) parts.push(`${data.completed_today} done today`);

  return {
    title: "Sorce",
    subtitle: parts.length > 0 ? parts.join(" · ") : "No active applications",
    badge: data.hold_count,
  };
}
