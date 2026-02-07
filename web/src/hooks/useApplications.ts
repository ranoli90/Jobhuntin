import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { supabase } from "../lib/supabase";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

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
  const resp = await fetch(`${API_BASE}/applications`, { credentials: "include" });
  if (!resp.ok) throw new Error("Unable to load applications");
  const json = (await resp.json()) as { applications: ApplicationRecord[] } | ApplicationRecord[];
  return Array.isArray(json) ? json : json.applications ?? [];
}

export function useApplications() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["applications"],
    queryFn: fetchApplications,
  });

  useEffect(() => {
    const channel = supabase
      .channel("applications-feed")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "applications" },
        () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
      )
      .subscribe();

    return () => {
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
    const resp = await fetch(`${API_BASE}/applications/${applicationId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    if (!resp.ok) throw new Error("Unable to answer HOLD");
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
  } as const;
}
