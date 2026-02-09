import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";

export type JobSwipeDecision = "ACCEPT" | "REJECT";

export interface JobFilters {
  location?: string;
  minSalary?: number;
  keywords?: string;
}

export interface JobPosting {
  id: string;
  title: string;
  company: string;
  salary_min?: number;
  salary_max?: number;
  location?: string;
  description?: string;
  url?: string;
  logo_url?: string;
}

async function fetchJobs(filters: JobFilters): Promise<JobPosting[]> {
  const params = new URLSearchParams();
  if (filters.location) params.set("location", filters.location);
  if (filters.minSalary) params.set("min_salary", String(filters.minSalary));
  if (filters.keywords) params.set("keywords", filters.keywords);
  const query = params.toString();
  const path = query ? `jobs?${query}` : "jobs";
  const json = await apiGet<{ jobs?: JobPosting[] } | JobPosting[]>(path);
  if (Array.isArray(json)) return json;
  return json.jobs ?? [];
}

export function useJobs(filters: JobFilters) {
  const memoFilters = useMemo(() => filters, [filters.location, filters.minSalary, filters.keywords]);

  const query = useQuery({
    queryKey: ["jobs", memoFilters],
    queryFn: () => fetchJobs(memoFilters),
  });

  return {
    jobs: query.data ?? [],
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    refetch: query.refetch,
  };
}
