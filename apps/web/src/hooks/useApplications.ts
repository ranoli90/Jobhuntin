import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "../lib/api";

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

  const query = useQuery({
    queryKey: ["applications"],
    queryFn: fetchApplications,
    refetchInterval: 5000, // Poll every 5 seconds instead of realtime subscription
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

  const answerHold = async (applicationId: string, answer: string) => {
    await apiPost(`applications/${applicationId}/answer`, { answer });
    queryClient.invalidateQueries({ queryKey: ["applications"] });
  };

  const snoozeApplication = async (applicationId: string, hours: number = 24) => {
    await apiPost(`applications/${applicationId}/snooze`, { hours });
    queryClient.invalidateQueries({ queryKey: ["applications"] });
  };

  return {
    applications,
    holdApplications,
    byStatus,
    stats: {
      successRate,
      monthlyApps: applications.length,
    },
    isLoading: query.isLoading,
    refetch: query.refetch,
    answerHold,
    snoozeApplication,
  } as const;
}
