import { useMemo, useEffect, useRef } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import { pushToast } from "../lib/toast";

export type JobSwipeDecision = "ACCEPT" | "REJECT";

export interface JobFilters {
  location?: string;
  minSalary?: number;
  keywords?: string;
  source?: string;
  isRemote?: boolean;
  jobType?: string;
  sortBy?: "match_score" | "recently_matched" | "salary";
  minMatchScore?: number;
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
  source?: string;
  is_remote?: boolean;
  job_type?: string;
  date_posted?: string;
  job_level?: string;
  company_industry?: string;
}

export interface JobSource {
  source: string;
  total_jobs: number;
  remote_jobs: number;
  jobs_with_salary: number;
  last_synced_at?: string;
}

interface JobsResponse {
  jobs?: JobPosting[];
  next_offset?: number | null;
}

async function fetchJobs(
  filters: JobFilters,
  offset = 0,
  limit = 25,
): Promise<JobsResponse> {
  const parameters = new URLSearchParams();
  if (filters.location) parameters.set("location", filters.location);
  if (filters.minSalary)
    parameters.set("min_salary", String(filters.minSalary));
  if (filters.keywords) parameters.set("keywords", filters.keywords);
  if (filters.source) parameters.set("source", filters.source);
  if (filters.isRemote !== undefined)
    parameters.set("is_remote", String(filters.isRemote));
  if (filters.jobType) parameters.set("job_type", filters.jobType);
  if (filters.sortBy) parameters.set("sort_by", filters.sortBy);
  if (filters.minMatchScore != undefined)
    parameters.set("min_match_score", String(filters.minMatchScore));
  parameters.set("limit", String(limit));
  parameters.set("offset", String(offset));
  const query = parameters.toString();
  const path = query ? `me/jobs?${query}` : "me/jobs";
  const json = await apiGet<JobsResponse | JobPosting[]>(path);
  if (Array.isArray(json)) return { jobs: json, next_offset: null };
  return { jobs: json.jobs ?? [], next_offset: json.next_offset ?? null };
}

async function fetchJobSources(): Promise<JobSource[]> {
  return apiGet<JobSource[]>("me/jobs/sources");
}

export function useJobs(filters: JobFilters) {
  const memoFilters = useMemo(
    () => ({
      location: filters.location,
      minSalary: filters.minSalary,
      keywords: filters.keywords,
      source: filters.source,
      isRemote: filters.isRemote,
      jobType: filters.jobType,
      sortBy: filters.sortBy,
      minMatchScore: filters.minMatchScore,
    }),
    [
      filters.location,
      filters.minSalary,
      filters.keywords,
      filters.source,
      filters.isRemote,
      filters.jobType,
      filters.sortBy,
      filters.minMatchScore,
    ],
  );

  const query = useInfiniteQuery({
    queryKey: ["jobs", memoFilters],
    queryFn: ({ pageParam: pageParameter = 0 }) =>
      fetchJobs(memoFilters, pageParameter),
    getNextPageParam: (lastPage) => lastPage.next_offset ?? undefined,
    initialPageParam: 0,
    staleTime: 2 * 60 * 1000, // #63: 2 min - swiped jobs removed on invalidate; shorter stale for fresher feed
  });

  const hasShownErrorReference = useRef(false);
  useEffect(() => {
    if (query.error) {
      if (!hasShownErrorReference.current) {
        hasShownErrorReference.current = true;
        pushToast({
          title: "Failed to load jobs",
          description:
            query.error.message ||
            "Please check your connection and try again.",
          tone: "error",
        });
      }
    } else {
      hasShownErrorReference.current = false;
    }
  }, [query.error]);

  return {
    jobs: query.data?.pages.flatMap((p) => p.jobs ?? []) ?? [],
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    refetch: query.refetch,
    error: query.error,
  };
}

export function useJobSources() {
  return useInfiniteQuery({
    queryKey: ["jobSources"],
    queryFn: () => fetchJobSources(),
    initialPageParam: 0,
    getNextPageParam: () => undefined,
  });
}

export const JOB_SOURCES = [
  { id: "indeed", label: "Indeed", color: "bg-blue-100 text-blue-700" },
  { id: "linkedin", label: "LinkedIn", color: "bg-sky-100 text-sky-700" },
  {
    id: "zip_recruiter",
    label: "ZipRecruiter",
    color: "bg-purple-100 text-purple-700",
  },
  { id: "glassdoor", label: "Glassdoor", color: "bg-green-100 text-green-700" },
] as const;

export const JOB_TYPES = [
  { id: "fulltime", label: "Full-time" },
  { id: "parttime", label: "Part-time" },
  { id: "contract", label: "Contract" },
  { id: "internship", label: "Internship" },
] as const;

export function formatTimeAgo(dateString: string | undefined): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "Unknown";
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return `${Math.floor(diffDays / 30)} months ago`;
}
