import { useMemo, useEffect } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import { pushToast } from "../lib/toast";

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
  requirements?: string[];
  match_score?: number;
}

interface JobsResponse {
  jobs?: JobPosting[];
  next_offset?: number | null;
}

async function fetchJobs(filters: JobFilters, offset = 0, limit = 25): Promise<JobsResponse> {
  const params = new URLSearchParams();
  if (filters.location) params.set("location", filters.location);
  if (filters.minSalary) params.set("min_salary", String(filters.minSalary));
  if (filters.keywords) params.set("keywords", filters.keywords);
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  const query = params.toString();
  const path = query ? `jobs?${query}` : "jobs";
  const json = await apiGet<JobsResponse | JobPosting[]>(path);
  if (Array.isArray(json)) return { jobs: json, next_offset: null };
  return { jobs: json.jobs ?? [], next_offset: json.next_offset ?? null };
}

export function useJobs(filters: JobFilters) {
  const memoFilters = useMemo(() => ({
    location: filters.location,
    minSalary: filters.minSalary,
    keywords: filters.keywords,
  }), [filters.location, filters.minSalary, filters.keywords]);

  const query = useInfiniteQuery({
    queryKey: ["jobs", memoFilters],
    queryFn: ({ pageParam = 0 }) => fetchJobs(memoFilters, pageParam as number),
    getNextPageParam: (lastPage) => lastPage.next_offset ?? undefined,
    initialPageParam: 0,
  });

  useEffect(() => {
    if (query.error) {
      pushToast({
        title: "Failed to load jobs",
        description: (query.error as Error).message || "Please check your connection and try again.",
        tone: "error",
      });
    }
  }, [query.error]);

  return {
    jobs: (query.data?.pages.flatMap((p) => p.jobs ?? []) ?? []),
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    refetch: query.refetch,
  };
}
