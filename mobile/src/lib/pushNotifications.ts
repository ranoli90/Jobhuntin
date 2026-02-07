/**
 * Push notification registration and handling.
 *
 * Uses expo-notifications to:
 *   1. Request permission + get Expo push token
 *   2. Register token with backend
 *   3. Handle incoming notifications (foreground + background tap)
 */

import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { Platform } from "react-native";
import { supabase } from "./supabase";
import { API_BASE_URL } from "./config";

// ---------------------------------------------------------------------------
// Notification handler config (foreground display)
// ---------------------------------------------------------------------------

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// ---------------------------------------------------------------------------
// Token registration
// ---------------------------------------------------------------------------

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

/**
 * Request push permission, get Expo push token, register with backend.
 * Call this after login / on app startup.
 */
export async function registerForPushNotifications(): Promise<string | null> {
  if (!Device.isDevice) {
    console.log("Push notifications require a physical device");
    return null;
  }

  // Check existing permission
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    console.log("Push notification permission denied");
    return null;
  }

  // Android notification channel
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "Sorce Notifications",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#3B82F6",
    });
  }

  // Get Expo push token
  const tokenData = await Notifications.getExpoPushTokenAsync({
    projectId: "YOUR_EAS_PROJECT_ID",
  });
  const token = tokenData.data;

  // Register with backend
  try {
    const headers = await getAuthHeaders();
    await fetch(`${API_BASE_URL}/push/register`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        token,
        platform: Platform.OS === "ios" ? "apns" : "fcm",
      }),
    });
    console.log("Push token registered:", token.substring(0, 20) + "...");
  } catch (err) {
    console.error("Failed to register push token:", err);
  }

  return token;
}

/**
 * Unregister push token (call on logout).
 */
export async function unregisterPushToken(token: string): Promise<void> {
  try {
    const headers = await getAuthHeaders();
    await fetch(`${API_BASE_URL}/push/unregister`, {
      method: "POST",
      headers,
      body: JSON.stringify({ token, platform: Platform.OS === "ios" ? "apns" : "fcm" }),
    });
  } catch (err) {
    console.error("Failed to unregister push token:", err);
  }
}

// ---------------------------------------------------------------------------
// Notification listeners
// ---------------------------------------------------------------------------

export type NotificationTapHandler = (data: Record<string, unknown>) => void;

let _tapHandler: NotificationTapHandler | null = null;

/**
 * Set a handler for when the user taps a notification.
 * Typically used to navigate to the relevant screen.
 */
export function setNotificationTapHandler(handler: NotificationTapHandler): void {
  _tapHandler = handler;
}

/**
 * Start listening for notification events. Call once at app root.
 * Returns a cleanup function.
 */
export function startNotificationListeners(): () => void {
  // Foreground notification received
  const receivedSub = Notifications.addNotificationReceivedListener((notification) => {
    console.log("Notification received (foreground):", notification.request.content.title);
  });

  // User tapped notification
  const responseSub = Notifications.addNotificationResponseReceivedListener((response) => {
    const data = response.notification.request.content.data as Record<string, unknown>;
    console.log("Notification tapped, data:", data);
    if (_tapHandler) {
      _tapHandler(data);
    }
  });

  return () => {
    receivedSub.remove();
    responseSub.remove();
  };
}

/**
 * Get the notification that launched the app (cold start from notification tap).
 */
export async function getInitialNotification(): Promise<Record<string, unknown> | null> {
  const response = await Notifications.getLastNotificationResponseAsync();
  if (response) {
    return response.notification.request.content.data as Record<string, unknown>;
  }
  return null;
}
