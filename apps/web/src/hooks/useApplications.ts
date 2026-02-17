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
  const json = await apiGet<{ applications?: ApplicationRecord[] } | ApplicationRecord[]>("applications");
  return Array.isArray(json) ? json : json.applications ?? [];
}

export function useApplications() {
  const queryClient = useQueryClient();
  // L-10: Track per-application submission state for answerHold and snooze
  const [submittingIds, setSubmittingIds] = useState<Set<string>>(new Set());

  const query = useQuery({
    queryKey: ["applications"],
    queryFn: fetchApplications,
    // M-2: Reduced from 5s to 15s to lower server load; don't poll when tab is hidden
    refetchInterval: 15_000,
    refetchIntervalInBackground: false,
  });

  const applications = query.data ?? [];
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
      await apiPost(`applications/${applicationId}/answer`, { answer });
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
    setSubmittingIds(prev => new Set(prev).add(`snooze-${applicationId}`));
    try {
      await apiPost(`applications/${applicationId}/snooze`, { hours });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      pushToast({ title: "Snoozed for 24h", description: "This hold will reappear tomorrow.", tone: "info" });
    } catch (err) {
      pushToast({ title: "Snooze failed", description: (err as Error).message, tone: "error" });
      throw err;
    } finally {
      setSubmittingIds(prev => {
        const next = new Set(prev);
        next.delete(`snooze-${applicationId}`);
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
    isLoading: query.isLoading,
    // M-5: Expose error state so Dashboard can show an error banner
    error: query.error ? (query.error as Error).message : null,
    isSubmitting: (id: string) => submittingIds.has(id),
    refetch: query.refetch,
    answerHold,
    snoozeApplication,
  } as const;
}
