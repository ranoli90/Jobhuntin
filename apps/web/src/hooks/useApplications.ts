import { useState, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "../lib/api";
import { pushToast } from "../lib/toast";

export type ApplicationStatus = "APPLYING" | "APPLIED" | "HOLD" | "FAILED";

export interface ApplicationRecord {
  id: string;
  job_title: string;
  company: string;
  status: ApplicationStatus;
  summary?: string;
  hold_question?: string;
  last_activity?: string;
}

async function fetchApplications(): Promise<ApplicationRecord[]> {
  const json = await apiGet<{ items?: ApplicationRecord[]; applications?: ApplicationRecord[] } | ApplicationRecord[]>("me/applications");
  if (Array.isArray(json)) return json;
  return json.items ?? json.applications ?? [];
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
      const data = q.state.data as ApplicationRecord[] | undefined;
      const hasApplying = data?.some((a) => a.status === "APPLYING") ?? false;
      return hasApplying ? 10_000 : 30_000;
    },
    refetchIntervalInBackground: false,
  });

  const applications = query.data ?? [];
  const hasApplying = applications.some((a) => a.status === "APPLYING");

  const queueStatsQuery = useQuery({
    queryKey: ["applications", "queue-stats"],
    queryFn: fetchQueueStats,
    enabled: hasApplying,
    refetchInterval: hasApplying ? 15_000 : false,
  });
  const queueStats = queueStatsQuery.data;
  const holdApplications = applications.filter((app) => app.status === "HOLD");
  const successCount = applications.filter((app) => app.status === "APPLIED").length;
  const successRate = applications.length ? Math.round((successCount / applications.length) * 100) : 0;

  const byStatus = {
    APPLYING: applications.filter((app) => app.status === "APPLYING").length,
    APPLIED: successCount,
    HOLD: holdApplications.length,
    FAILED: applications.filter((app) => app.status === "FAILED").length,
  } as const;

  // L-10: answerHold now tracks loading state per-application
  const answerHold = useCallback(async (applicationId: string, answer: string) => {
    setSubmittingIds(prev => new Set(prev).add(applicationId));
    try {
      await apiPost(`me/applications/${applicationId}/answer`, { answer });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      pushToast({ title: "Response sent", description: "Your AI agent will resume this application.", tone: "success" });
    } catch (err) {
      pushToast({ title: "Failed to send response", description: (err as Error).message, tone: "error" });
      throw err;
    } finally {
      setSubmittingIds(prev => {
        const next = new Set(prev);
        next.delete(applicationId);
        return next;
      });
    }
  }, [queryClient]);

  // L-7: snoozeApplication now shows toast feedback
  const snoozeApplication = useCallback(async (applicationId: string, hours: number = 24) => {
    setSubmittingIds(prev => new Set(prev).add(applicationId));
    try {
      await apiPost(`me/applications/${applicationId}/snooze`, { hours });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      pushToast({ title: "Snoozed for 24h", description: "This hold will reappear tomorrow.", tone: "info" });
    } catch (err) {
      pushToast({ title: "Snooze failed", description: (err as Error).message, tone: "error" });
      throw err;
    } finally {
      setSubmittingIds(prev => {
        const next = new Set(prev);
        next.delete(applicationId);
        return next;
      });
    }
  }, [queryClient]);

  // #62: Shared review/withdraw actions for Dashboard and ApplicationsView
  const reviewApplication = useCallback(async (applicationId: string) => {
    setSubmittingIds(prev => new Set(prev).add(applicationId));
    try {
      await apiPost(`me/applications/${applicationId}/review`, {});
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      pushToast({ title: "Marked as reviewed", description: "Application has been marked as reviewed.", tone: "success" });
    } catch (err) {
      pushToast({ title: "Failed to mark as reviewed", description: (err as Error).message, tone: "error" });
      throw err;
    } finally {
      setSubmittingIds(prev => {
        const next = new Set(prev);
        next.delete(applicationId);
        return next;
      });
    }
  }, [queryClient]);

  const withdrawApplication = useCallback(async (applicationId: string) => {
    setSubmittingIds(prev => new Set(prev).add(applicationId));
    try {
      await apiPost(`me/applications/${applicationId}/withdraw`, {});
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      pushToast({ title: "Application withdrawn", description: "The application has been withdrawn.", tone: "info" });
    } catch (err) {
      pushToast({ title: "Withdraw failed", description: (err as Error).message, tone: "error" });
      throw err;
    } finally {
      setSubmittingIds(prev => {
        const next = new Set(prev);
        next.delete(applicationId);
        return next;
      });
    }
  }, [queryClient]);

  return {
    applications,
    holdApplications,
    byStatus,
    stats: {
      successRate,
      monthlyApps: applications.length,
    },
    queueStats: queueStats ?? null,
    isLoading: query.isLoading,
    error: query.error ? (query.error as Error).message : null,
    isSubmitting: (id: string) => submittingIds.has(id),
    refetch: query.refetch,
    answerHold,
    snoozeApplication,
    reviewApplication,
    withdrawApplication,
  } as const;
}
