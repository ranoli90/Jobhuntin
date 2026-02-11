import { useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { supabase } from "../lib/supabase";
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
  });

  useEffect(() => {
    // Debounce invalidations to avoid thrashing on noisy channels or multi-tenant updates
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const channel = supabase
      .channel("applications-feed")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "applications" },
        () => {
          if (debounceRef.current) clearTimeout(debounceRef.current);
          debounceRef.current = setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ["applications"] });
            debounceRef.current = null;
          }, 250);
        },
      )
      .subscribe();

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      supabase.removeChannel(channel);
    };
  }, [queryClient]);

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
