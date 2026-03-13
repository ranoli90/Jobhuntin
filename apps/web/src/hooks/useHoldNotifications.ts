import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut } from "../lib/api";
import { pushToast } from "../lib/toast";
import { t, getLocale } from "../lib/i18n";
import type { ApplicationRecord } from "./useApplications";

/**
 * Hold question notification types
 */
export interface HoldQuestionNotification {
  id: string;
  application_id: string;
  job_title: string;
  company: string;
  question: string;
  created_at: string;
  deadline?: string;
  snoozed_until?: string;
  is_answered: boolean;
  priority: "high" | "medium" | "low";
}

/**
 * Hold notification preferences
 */
export interface HoldNotificationPreferences {
  push_enabled: boolean;
  email_enabled: boolean;
  deadline_reminder_hours: number;
  quick_answer_enabled: boolean;
  sound_enabled: boolean;
}

/**
 * API response for hold notifications
 */
interface HoldNotificationsResponse {
  notifications: HoldQuestionNotification[];
  unread_count: number;
}

/**
 * API response for hold notification preferences
 */
interface HoldPreferencesResponse {
  preferences: HoldNotificationPreferences;
}

/**
 * Default notification preferences
 */
const DEFAULT_PREFERENCES: HoldNotificationPreferences = {
  push_enabled: true,
  email_enabled: true,
  deadline_reminder_hours: 24,
  quick_answer_enabled: true,
  sound_enabled: true,
};

/**
 * Calculate time remaining until deadline
 */
function calculateTimeRemaining(deadline?: string): {
  total: number;
  days: number;
  hours: number;
  minutes: number;
  isUrgent: boolean;
  isOverdue: boolean;
} {
  if (!deadline) {
    return { total: 0, days: 0, hours: 0, minutes: 0, isUrgent: false, isOverdue: false };
  }

  const now = new Date();
  const deadlineDate = new Date(deadline);
  const total = deadlineDate.getTime() - now.getTime();

  if (total <= 0) {
    return { total: 0, days: 0, hours: 0, minutes: 0, isUrgent: true, isOverdue: true };
  }

  const days = Math.floor(total / (1000 * 60 * 60 * 24));
  const hours = Math.floor((total % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((total % (1000 * 60 * 60)) / (1000 * 60));

  // Consider urgent if less than 4 hours remaining
  const isUrgent = total < 4 * 60 * 60 * 1000;

  return { total, days, hours, minutes, isUrgent, isOverdue: false };
}

/**
 * Format time remaining for display
 */
export function formatTimeRemaining(remaining: ReturnType<typeof calculateTimeRemaining>): string {
  if (remaining.isOverdue) {
    return "Overdue";
  }

  if (remaining.days > 0) {
    return `${remaining.days}d ${remaining.hours}h remaining`;
  }

  if (remaining.hours > 0) {
    return `${remaining.hours}h ${remaining.minutes}m remaining`;
  }

  if (remaining.minutes > 0) {
    return `${remaining.minutes}m remaining`;
  }

  return "Less than a minute";
}

/**
 * Hook for managing hold question notifications
 * - Push notifications for hold questions requiring action
 * - Email notification settings
 * - Deadline countdown for time-sensitive questions
 * - Quick answer inline form capability
 */
export function useHoldNotifications() {
  const queryClient = useQueryClient();
  const [quickAnswers, setQuickAnswers] = useState<Record<string, string>>({});
  const notifiedIds = useRef<Set<string>>(new Set());
  const locale = getLocale();

  // Fetch hold notifications from API
  const {
    data: notificationsData,
    isLoading: isLoadingNotifications,
    error: notificationsError,
    refetch: refetchNotifications,
  } = useQuery({
    queryKey: ["hold-notifications"],
    queryFn: async (): Promise<HoldNotificationsResponse> => {
      try {
        const json = await apiGet<HoldNotificationsResponse>("communications/notifications/hold");
        return json;
      } catch {
        // Fallback: return empty response if endpoint doesn't exist yet
        return { notifications: [], unread_count: 0 };
      }
    },
    refetchInterval: 30000, // Poll every 30 seconds
  });

  // Fetch hold notification preferences
  const {
    data: preferencesData,
    isLoading: isLoadingPreferences,
    error: preferencesError,
  } = useQuery({
    queryKey: ["hold-notification-preferences"],
    queryFn: async (): Promise<HoldPreferencesResponse> => {
      try {
        const json = await apiGet<HoldPreferencesResponse>(
          "communications/preferences/hold-notifications",
        );
        return json;
      } catch {
        // Return default preferences if endpoint doesn't exist
        return { preferences: DEFAULT_PREFERENCES };
      }
    },
  });

  const preferences = preferencesData?.preferences ?? DEFAULT_PREFERENCES;

  // Update notification preferences mutation
  const updatePreferencesMutation = useMutation({
    mutationFn: async (newPreferences: Partial<HoldNotificationPreferences>) => {
      const updated = { ...preferences, ...newPreferences };
      await apiPut("communications/preferences/hold-notifications", updated);
      return updated;
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(["hold-notification-preferences"], {
        preferences: updated,
      });
      pushToast({
        title: t("holdNotifications.preferencesSaved", locale) || "Preferences saved",
        description:
          t("holdNotifications.preferencesSavedDesc", locale) ||
          "Your notification preferences have been updated.",
        tone: "success",
      });
    },
    onError: () => {
      pushToast({
        title: t("holdNotifications.preferencesError", locale) || "Could not save preferences",
        description: t("holdNotifications.tryAgain", locale) || "Please try again.",
        tone: "error",
      });
    },
  });

  // Quick answer mutation
  const quickAnswerMutation = useMutation({
    mutationFn: async ({
      applicationId,
      answer,
    }: {
      applicationId: string;
      answer: string;
    }) => {
      await apiPost(`me/applications/${applicationId}/answer`, { answer });
    },
    onSuccess: (_, { applicationId }) => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["hold-notifications"] });
      pushToast({
        title: t("holdNotifications.quickAnswerSent", locale) || "Response sent",
        description:
          t("holdNotifications.quickAnswerSentDesc", locale) ||
          "Your AI agent will resume this application.",
        tone: "success",
      });
      // Clear quick answer for this application
      setQuickAnswers((prev) => {
        const next = { ...prev };
        delete next[applicationId];
        return next;
      });
    },
    onError: () => {
      pushToast({
        title: t("holdNotifications.quickAnswerError", locale) || "Could not send response",
        description: t("holdNotifications.tryAgain", locale) || "Please try again.",
        tone: "error",
      });
    },
  });

  // Snooze hold mutation
  const snoozeMutation = useMutation({
    mutationFn: async ({
      applicationId,
      hours,
    }: {
      applicationId: string;
      hours: number;
    }) => {
      await apiPost(`me/applications/${applicationId}/snooze`, { hours });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["hold-notifications"] });
      pushToast({
        title: t("holdNotifications.snoozed", locale) || "Snoozed",
        description:
          t("holdNotifications.snoozedDesc", locale) ||
          "This hold will reappear after the snooze period.",
        tone: "info",
      });
    },
    onError: () => {
      pushToast({
        title: t("holdNotifications.snoozeError", locale) || "Could not snooze",
        description: t("holdNotifications.tryAgain", locale) || "Please try again.",
        tone: "error",
      });
    },
  });

  // Extract notifications from data
  const notifications = notificationsData?.notifications ?? [];
  const unreadCount = notificationsData?.unread_count ?? 0;

  // Calculate time-sensitive notifications
  const urgentNotifications = useMemo(() => {
    return notifications
      .filter((n) => {
        if (n.is_answered || n.snoozed_until) return false;
        const remaining = calculateTimeRemaining(n.deadline);
        return remaining.isUrgent || remaining.isOverdue;
      })
      .sort((a, b) => {
        const aRemaining = calculateTimeRemaining(a.deadline).total;
        const bRemaining = calculateTimeRemaining(b.deadline).total;
        return aRemaining - bRemaining;
      });
  }, [notifications]);

  // Show push notification for new hold questions
  useEffect(() => {
    if (!preferences.push_enabled || isLoadingNotifications) return;

    for (const notification of notifications) {
      if (
        notification.is_answered ||
        notification.snoozed_until ||
        notifiedIds.current.has(notification.id)
      ) {
        continue;
      }

      // Check if deadline is approaching
      const remaining = calculateTimeRemaining(notification.deadline);
      if (remaining.isUrgent || remaining.isOverdue) {
        notifiedIds.current.add(notification.id);

        const title =
          t("holdNotifications.urgentTitle", locale) ||
          `⏰ Response needed: ${notification.company}`;
        const description =
          t("holdNotifications.urgentDesc", locale) ||
          `Question: ${notification.question.substring(0, 100)}${notification.question.length > 100 ? "..." : ""}`;

        pushToast({
          title,
          description,
          tone: remaining.isOverdue ? "error" : "warning",
        });
      }
    }
  }, [notifications, preferences.push_enabled, isLoadingNotifications, locale]);

  // Quick answer handlers
  const handleQuickAnswer = useCallback(
    (applicationId: string, answer: string) => {
      if (!answer.trim()) return;
      quickAnswerMutation.mutate({ applicationId, answer });
    },
    [quickAnswerMutation],
  );

  const handleQuickAnswerChange = useCallback(
    (applicationId: string, value: string) => {
      setQuickAnswers((prev) => ({
        ...prev,
        [applicationId]: value,
      }));
    },
    [],
  );

  const handleSnooze = useCallback(
    (applicationId: string, hours: number = 24) => {
      snoozeMutation.mutate({ applicationId, hours });
    },
    [snoozeMutation],
  );

  // Update preferences
  const updatePreferences = useCallback(
    (newPrefs: Partial<HoldNotificationPreferences>) => {
      updatePreferencesMutation.mutate(newPrefs);
    },
    [updatePreferencesMutation],
  );

  // Get notifications by priority
  const notificationsByPriority = useMemo(() => {
    const high = notifications.filter((n) => n.priority === "high" && !n.is_answered);
    const medium = notifications.filter((n) => n.priority === "medium" && !n.is_answered);
    const low = notifications.filter((n) => n.priority === "low" && !n.is_answered);
    return { high, medium, low };
  }, [notifications]);

  return {
    // Data
    notifications,
    notificationsByPriority,
    urgentNotifications,
    unreadCount,
    preferences,

    // Loading states
    isLoading: isLoadingNotifications || isLoadingPreferences,
    isLoadingPreferences,
    isSubmittingQuickAnswer: quickAnswerMutation.isPending,
    isSubmittingSnooze: snoozeMutation.isPending,
    isUpdatingPreferences: updatePreferencesMutation.isPending,

    // Errors
    error: notificationsError || preferencesError,

    // Actions
    refetch: refetchNotifications,
    handleQuickAnswer,
    handleQuickAnswerChange,
    handleSnooze,
    updatePreferences,
    getQuickAnswer: (applicationId: string) => quickAnswers[applicationId] ?? "",
    calculateTimeRemaining,

    // Utility
    formatTimeRemaining,
  };
}

export type { HoldQuestionNotification, HoldNotificationPreferences };
