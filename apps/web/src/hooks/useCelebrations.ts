import { useCallback, useRef } from "react";
import { pushToast } from "../lib/toast";
import { fireSuccessConfetti } from "../lib/confetti";
import { t, getLocale } from "../lib/i18n";

// Estimated response times based on company size (in days)
const RESPONSE_TIME_ESTIMATES: Record<string, string> = {
  startup: "1-3 days",
  small: "3-5 days",
  medium: "5-10 days",
  large: "10-14 days",
  enterprise: "2-4 weeks",
  unknown: "1-2 weeks",
};

/**
 * Get estimated response time based on company characteristics
 * This can be enhanced with actual company data from the backend
 */
export function getEstimatedResponseTime(companySize?: string): string {
  if (!companySize) return RESPONSE_TIME_ESTIMATES.unknown;
  const size = companySize.toLowerCase();
  if (size.includes("startup") || size.includes("1-10") || size.includes("11-50")) {
    return RESPONSE_TIME_ESTIMATES.startup;
  }
  if (size.includes("small") || size.includes("51-200") || size.includes("50")) {
    return RESPONSE_TIME_ESTIMATES.small;
  }
  if (size.includes("medium") || size.includes("201-500") || size.includes("500")) {
    return RESPONSE_TIME_ESTIMATES.medium;
  }
  if (size.includes("large") || size.includes("1000") || size.includes("1001-5000")) {
    return RESPONSE_TIME_ESTIMATES.large;
  }
  if (size.includes("enterprise") || size.includes("5000")) {
    return RESPONSE_TIME_ESTIMATES.enterprise;
  }
  return RESPONSE_TIME_ESTIMATES.unknown;
}

export interface ApplicationCelebrationData {
  jobId: string;
  jobTitle: string;
  company: string;
  companySize?: string;
  salary?: string;
}

/**
 * Hook for celebrating successful job application submissions
 * - Shows confetti animation
 * - Displays "Application Sent!" notification with company name
 * - Shows estimated response time based on company data
 * - Provides option to share success
 */
export function useApplicationCelebration() {
  const toasted = useRef<Set<string>>(new Set());

  const celebrate = useCallback(
    async (data: ApplicationCelebrationData) => {
      const { jobId, jobTitle, company, companySize } = data;

      // Prevent duplicate celebrations for the same job
      if (toasted.current.has(jobId)) return;
      toasted.current.add(jobId);

      const locale = getLocale();
      const estimatedTime = getEstimatedResponseTime(companySize);

      // Get translations
      const title = t("celebrations.applicationSent", locale) || "Application Sent! 🚀";
      const description =
        t("celebrations.applicationSentDesc", locale) ||
        `Your application for ${jobTitle} at ${company} has been submitted successfully.`;
      const responseTimeLabel =
        t("celebrations.estimatedResponse", locale) || "Estimated response time";
      const shareText = t("celebrations.shareSuccess", locale) || "Share your success";

      // Fire confetti animation
      await fireSuccessConfetti();

      // Push the main success toast
      pushToast({
        title,
        description,
        tone: "success",
      });

      // Push a secondary toast with estimated response time
      setTimeout(() => {
        pushToast({
          title: `${responseTimeLabel}: ${estimatedTime}`,
          description:
            t("celebrations.responseTimeNote", locale) ||
            "This is an estimate based on company size. Actual times may vary.",
          tone: "info",
        });
      }, 1500);

      // Push share option toast
      setTimeout(() => {
        pushToast({
          title: shareText,
          description:
            t("celebrations.shareDesc", locale) ||
            "Let others know you're on the job hunt!",
          tone: "neutral",
        });
      }, 3000);
    },
    [],
  );

  const reset = useCallback(() => {
    toasted.current.clear();
  }, []);

  return { celebrate, reset };
}

export function useFirstSaveCelebration() {
  const toasted = useRef<Set<string>>(new Set());

  const celebrate = (jobId: string, jobTitle: string, company: string) => {
    if (toasted.current.has(jobId)) return;
    toasted.current.add(jobId);
    pushToast({
      title: "First job saved! 🎯",
      description: `${jobTitle} @ ${company} is now in your shortlist.`,
      tone: "success",
    });
  };

  return { celebrate };
}

export function useSessionMilestone() {
  // N-5: Session milestones use higher thresholds to avoid overlapping with
  // per-swipe milestones [1, 5, 10, 25] defined in JobsView.
  const milestones = [50, 100, 250, 500];
  const toasted = useRef<Set<number>>(new Set());

  const celebrate = (count: number) => {
    for (const m of milestones) {
      if (count >= m && !toasted.current.has(m)) {
        toasted.current.add(m);
        pushToast({
          title: `🔥 ${m} jobs viewed`,
          description: "You're building momentum—keep scouting!",
          tone: "success",
        });
      }
    }
  };

  return { celebrate };
}

/**
 * Milestone celebrations for application counts
 */
export function useApplicationMilestone() {
  const milestones = [1, 5, 10, 25, 50, 100];
  const toasted = useRef<Set<number>>(new Set());

  const celebrate = async (count: number) => {
    for (const m of milestones) {
      if (count >= m && !toasted.current.has(m)) {
        toasted.current.add(m);

        // Fire confetti for milestones
        await fireSuccessConfetti();

        const locale = getLocale();
        const titles: Record<number, string> = {
          1: t("celebrations.firstApplication", locale) || "First Application! 🎉",
          5: t("celebrations.fiveApplications", locale) || "5 Applications! 🔥",
          10: t("celebrations.tenApplications", locale) || "10 Applications! 🚀",
          25: t("celebrations.twentyFiveApplications", locale) || "25 Applications! 💪",
          50: t("celebrations.fiftyApplications", locale) || "50 Applications! ⭐",
          100: t("celebrations.hundredApplications", locale) || "100 Applications! 🏆",
        };

        pushToast({
          title: titles[m] || `${m} Applications! 🎊`,
          description:
            t("celebrations.milestoneDesc", locale) ||
            "Keep up the great work! Your AI agent is working hard for you.",
          tone: "success",
        });
      }
    }
  };

  return { celebrate };
}
