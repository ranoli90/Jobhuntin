/**
 * Upgrade funnel — logic for when/how to show upgrade prompts.
 *
 * Triggers:
 *   1. Quota usage ≥80% → soft nudge banner
 *   2. Quota exhausted → hard paywall
 *   3. After 3rd successful application → "Go PRO" prompt
 *   4. After 7 days on FREE → retention nudge
 *
 * Also handles in-app review prompts after successful applications.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { track } from "./analytics";

// ---------------------------------------------------------------------------
// Storage keys
// ---------------------------------------------------------------------------

const KEYS = {
  APPS_COMPLETED: "sorce_apps_completed_count",
  LAST_UPGRADE_SHOWN: "sorce_last_upgrade_shown",
  LAST_REVIEW_SHOWN: "sorce_last_review_shown",
  SIGNUP_DATE: "sorce_signup_date",
} as const;

// ---------------------------------------------------------------------------
// Upgrade prompt logic
// ---------------------------------------------------------------------------

export type UpgradeReason =
  | "quota_80_pct"
  | "quota_exhausted"
  | "third_app_completed"
  | "retention_day_7";

export interface UpgradePromptDecision {
  shouldShow: boolean;
  reason: UpgradeReason | null;
  message: string;
}

/**
 * Decide whether to show an upgrade prompt.
 * Call after key user actions (swipe, app completed, app open).
 */
export async function shouldShowUpgradePrompt(
  plan: string,
  usagePct: number,
  monthlyRemaining: number,
): Promise<UpgradePromptDecision> {
  const noShow: UpgradePromptDecision = { shouldShow: false, reason: null, message: "" };

  // Already on PRO — never show
  if (plan !== "FREE") return noShow;

  // Rate-limit: don't show more than once per 24h
  const lastShown = await AsyncStorage.getItem(KEYS.LAST_UPGRADE_SHOWN);
  if (lastShown) {
    const elapsed = Date.now() - parseInt(lastShown, 10);
    if (elapsed < 24 * 60 * 60 * 1000) return noShow;
  }

  // 1. Hard paywall
  if (monthlyRemaining <= 0) {
    await markUpgradeShown("quota_exhausted");
    return {
      shouldShow: true,
      reason: "quota_exhausted",
      message: "You've used all your free applications this month. Upgrade to PRO for 200 apps/month.",
    };
  }

  // 2. Soft nudge at 80%
  if (usagePct >= 80) {
    await markUpgradeShown("quota_80_pct");
    return {
      shouldShow: true,
      reason: "quota_80_pct",
      message: `You've used ${Math.round(usagePct)}% of your free applications. Upgrade to keep your momentum.`,
    };
  }

  // 3. After 3rd completed app
  const completedStr = await AsyncStorage.getItem(KEYS.APPS_COMPLETED);
  const completed = parseInt(completedStr || "0", 10);
  if (completed === 3) {
    await markUpgradeShown("third_app_completed");
    return {
      shouldShow: true,
      reason: "third_app_completed",
      message: "3 applications submitted! Imagine 200/month with PRO.",
    };
  }

  // 4. Day 7 retention nudge
  const signupStr = await AsyncStorage.getItem(KEYS.SIGNUP_DATE);
  if (signupStr) {
    const daysSince = (Date.now() - parseInt(signupStr, 10)) / (1000 * 60 * 60 * 24);
    if (daysSince >= 7 && daysSince < 8) {
      await markUpgradeShown("retention_day_7");
      return {
        shouldShow: true,
        reason: "retention_day_7",
        message: "You've been using Sorce for a week! Upgrade for unlimited power.",
      };
    }
  }

  return noShow;
}

async function markUpgradeShown(reason: UpgradeReason): Promise<void> {
  await AsyncStorage.setItem(KEYS.LAST_UPGRADE_SHOWN, Date.now().toString());
  track("upgrade_prompt_shown", { reason });
}

/**
 * Call when a user completes signup to start the retention timer.
 */
export async function recordSignupDate(): Promise<void> {
  const existing = await AsyncStorage.getItem(KEYS.SIGNUP_DATE);
  if (!existing) {
    await AsyncStorage.setItem(KEYS.SIGNUP_DATE, Date.now().toString());
  }
}

/**
 * Increment the completed applications counter (used for upgrade triggers).
 */
export async function incrementCompletedApps(): Promise<number> {
  const current = parseInt((await AsyncStorage.getItem(KEYS.APPS_COMPLETED)) || "0", 10);
  const next = current + 1;
  await AsyncStorage.setItem(KEYS.APPS_COMPLETED, next.toString());
  return next;
}

// ---------------------------------------------------------------------------
// In-app review prompt logic
// ---------------------------------------------------------------------------

/**
 * Decide whether to show in-app review prompt (App Store / Play Store rating).
 *
 * Triggers after 5th successful application, max once per 90 days.
 */
export async function shouldShowReviewPrompt(): Promise<boolean> {
  const completedStr = await AsyncStorage.getItem(KEYS.APPS_COMPLETED);
  const completed = parseInt(completedStr || "0", 10);

  if (completed < 5) return false;

  const lastShown = await AsyncStorage.getItem(KEYS.LAST_REVIEW_SHOWN);
  if (lastShown) {
    const elapsed = Date.now() - parseInt(lastShown, 10);
    if (elapsed < 90 * 24 * 60 * 60 * 1000) return false;
  }

  await AsyncStorage.setItem(KEYS.LAST_REVIEW_SHOWN, Date.now().toString());
  track("review_prompt_shown", { completed_apps: completed });
  return true;
}

/**
 * Actually request the in-app review dialog.
 * Call this after shouldShowReviewPrompt() returns true.
 */
export async function requestInAppReview(): Promise<void> {
  try {
    const StoreReview = await import("expo-store-review");
    const isAvailable = await StoreReview.isAvailableAsync();
    if (isAvailable) {
      await StoreReview.requestReview();
    }
  } catch (err) {
    console.warn("In-app review not available:", err);
  }
}
