import { useState, useCallback, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "../lib/api";
import { pushToast } from "../lib/toast";
import {
  ApplicationErrorCode,
  getErrorDetail,
  formatApplicationError,
  type ApplicationErrorDetail,
} from "../lib/applicationErrors";

export type ApplicationStatus = "APPLYING" | "APPLIED" | "HOLD" | "FAILED";

export interface ApplicationRecord {
  id: string;
  job_title: string;
  company: string;
  status: ApplicationStatus;
  summary?: string;
  hold_question?: string;
  last_activity?: string;
  error_code?: ApplicationErrorCode;
  error_message?: string;
}

interface ApplicationsResponse {
  items?: ApplicationRecord[];
  applications?: ApplicationRecord[];
  pagination?: { total: number; limit: number; offset: number };
}

async function fetchApplications(): Promise<{
  items: ApplicationRecord[];
  total: number;
}> {
  const json = await apiGet<ApplicationsResponse | ApplicationRecord[]>(
    "me/applications?limit=100",
  );
  if (Array.isArray(json)) {
    return { items: json, total: json.length };
  }
  const items = json.items ?? json.applications ?? [];
  const total =
    json.pagination?.total ?? items.length;
  return { items, total };
}

export interface QueueStats {
  applications: { id: string; priority_score: number }[];
  queue_ahead: number;
  eta_minutes: number;
}

async function fetchQueueStats(): Promise<QueueStats> {
  return apiGet<QueueStats>("me/applications/queue-stats");
}

export function useApplications() {
  const queryClient = useQueryClient();
  // L-10: Track per-application submission state for answerHold and snooze
  const [submittingIds, setSubmittingIds] = useState<Set<string>>(new Set());

  const query = useQuery({
    queryKey: ["applications"],
    queryFn: fetchApplications,
    // #23: Dynamic polling - 10s when APPLYING, 30s otherwise; don't poll when tab hidden
    refetchInterval: (q) => {
      const data = q.state.data;
      const hasApplying = data?.items?.some((a) => a.status === "APPLYING") ?? false;
      return hasApplying ? 10_000 : 30_000;
    },
    refetchIntervalInBackground: false,
  });

  const { items: applications = [], total: totalApps = 0 } = query.data ?? {};
  const hasApplying = applications.some((a) => a.status === "APPLYING");

  const queueStatsQuery = useQuery({
    queryKey: ["applications", "queue-stats"],
    queryFn: fetchQueueStats,
    enabled: hasApplying,
    refetchInterval: hasApplying ? 15_000 : false,
  });
  const queueStats = queueStatsQuery.data;
  const holdApplications = applications.filter((app) => app.status === "HOLD");
  const successCount = applications.filter(
    (app) => app.status === "APPLIED",
  ).length;
  const displayTotal = totalApps > 0 ? totalApps : applications.length;
  const successRate =
    applications.length > 0
      ? Math.round((successCount / applications.length) * 100)
      : 0;

  const byStatus = {
    APPLYING: applications.filter((app) => app.status === "APPLYING").length,
    APPLIED: successCount,
    HOLD: holdApplications.length,
    FAILED: applications.filter((app) => app.status === "FAILED").length,
  } as const;

  // L-10: answerHold now tracks loading state per-application
  const answerHold = useCallback(
    async (applicationId: string, answer: string) => {
      setSubmittingIds((previous) => new Set(previous).add(applicationId));
      try {
        await apiPost(`me/applications/${applicationId}/answer`, { answer });
        queryClient.invalidateQueries({ queryKey: ["applications"] });
        pushToast({
          title: "Response sent",
          description: "Your AI agent will resume this application.",
          tone: "success",
        });
      } catch (error) {
        pushToast({
          title: "Could not send response",
          description: (error as Error).message || "Please try again.",
          tone: "error",
        });
        throw error;
      } finally {
        setSubmittingIds((previous) => {
          const next = new Set(previous);
          next.delete(applicationId);
          return next;
        });
      }
    },
    [queryClient],
  );

  // L-7: snoozeApplication now shows toast feedback
  const snoozeApplication = useCallback(
    async (applicationId: string, hours: number = 24) => {
      setSubmittingIds((previous) => new Set(previous).add(applicationId));
      try {
        await apiPost(`me/applications/${applicationId}/snooze`, { hours });
        queryClient.invalidateQueries({ queryKey: ["applications"] });
        pushToast({
          title: "Snoozed for 24h",
          description: "This hold will reappear tomorrow.",
          tone: "info",
        });
      } catch (error) {
        pushToast({
          title: "Could not snooze",
          description: (error as Error).message || "Please try again.",
          tone: "error",
        });
        throw error;
      } finally {
        setSubmittingIds((previous) => {
          const next = new Set(previous);
          next.delete(applicationId);
          return next;
        });
      }
    },
    [queryClient],
  );

  // #62: Shared review/withdraw actions for Dashboard and ApplicationsView
  const reviewApplication = useCallback(
    async (applicationId: string) => {
      setSubmittingIds((previous) => new Set(previous).add(applicationId));
      try {
        await apiPost(`me/applications/${applicationId}/review`, {});
        queryClient.invalidateQueries({ queryKey: ["applications"] });
        pushToast({
          title: "Marked as reviewed",
          description: "Application has been marked as reviewed.",
          tone: "success",
        });
      } catch (error) {
        pushToast({
          title: "Could not mark as reviewed",
          description: (error as Error).message || "Please try again.",
          tone: "error",
        });
        throw error;
      } finally {
        setSubmittingIds((previous) => {
          const next = new Set(previous);
          next.delete(applicationId);
          return next;
        });
      }
    },
    [queryClient],
  );

  const withdrawApplication = useCallback(
    async (applicationId: string) => {
      setSubmittingIds((previous) => new Set(previous).add(applicationId));
      try {
        await apiPost(`me/applications/${applicationId}/withdraw`, {});
        queryClient.invalidateQueries({ queryKey: ["applications"] });
        pushToast({
          title: "Application withdrawn",
          description: "The application has been withdrawn.",
          tone: "info",
        });
      } catch (error) {
        pushToast({
          title: "Could not withdraw application",
          description: (error as Error).message || "Please try again.",
          tone: "error",
        });
        throw error;
      } finally {
        setSubmittingIds((previous) => {
          const next = new Set(previous);
          next.delete(applicationId);
          return next;
        });
      }
    },
    [queryClient],
  );

  // Get detailed error information for a failed application
  const getApplicationError = useCallback(
    (application: ApplicationRecord): ApplicationErrorDetail | null => {
      if (application.status !== "FAILED") {
        return null;
      }
      // If we have an error code, use the detailed error system
      if (application.error_code) {
        return getErrorDetail(application.error_code as ApplicationErrorCode);
      }
      // Fallback: parse from error_message if available
      if (application.error_message) {
        return formatApplicationError(application.error_message);
      }
      // Default to unknown error
      return getErrorDetail(ApplicationErrorCode.UNKNOWN_ERROR);
    },
    [],
  );

  // Get failed applications with error details
  const failedApplications = useMemo(() => {
    return applications
      .filter((app) => app.status === "FAILED")
      .map((app) => ({
        ...app,
        errorDetail: getApplicationError(app),
      }));
  }, [applications, getApplicationError]);

  return {
    applications,
    holdApplications,
    failedApplications,
    byStatus,
    stats: {
      successRate,
      totalApps: displayTotal,
      monthlyApps: displayTotal,
    },
    queueStats: queueStats ?? null,
    isLoading: query.isLoading,
    error: query.error ? String(query.error) : null,
    isSubmitting: (id: string) => submittingIds.has(id),
    refetch: query.refetch,
    answerHold,
    snoozeApplication,
    reviewApplication,
    withdrawApplication,
    getApplicationError,
  } as const;
}
