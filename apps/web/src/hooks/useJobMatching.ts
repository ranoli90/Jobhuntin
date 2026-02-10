/**
 * Enhanced Job Matching Hook with AI Integration
 * Microsoft-level implementation with comprehensive error handling and caching
 */

import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiPost, apiGet } from "../lib/api";
import { useProfile } from "./useProfile";

// Simple debounce implementation to avoid external dependency
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export interface EnhancedJobPosting {
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
  benefits?: string[];
  posted_date?: string;
  remote_policy?: "remote" | "hybrid" | "onsite";
  experience_level?: "entry" | "mid" | "senior" | "executive";
  match_score?: JobMatchScore;
}

export interface JobMatchScore {
  score: number;
  skill_match: number;
  experience_match: number;
  location_match: number;
  salary_match: number;
  culture_signals: string[];
  red_flags: string[];
  summary: string;
  confidence: number;
  reasoning: string;
}

export interface MatchingFilters {
  location?: string;
  minSalary?: number;
  maxSalary?: number;
  keywords?: string;
  remoteOnly?: boolean;
  experienceLevel?: string;
  companies?: string[];
  excludeCompanies?: string[];
  minMatchScore?: number;
}

interface MatchingState {
  isScoring: boolean;
  lastScoredJob: string | null;
  batchProgress: number;
  totalBatch: number;
}

export function useJobMatching(initialFilters: MatchingFilters = {}) {
  const queryClient = useQueryClient();
  const { profile } = useProfile();
  const [filters, setFilters] = useState<MatchingFilters>(initialFilters);
  const [matchingState, setMatchingState] = useState<MatchingState>({
    isScoring: false,
    lastScoredJob: null,
    batchProgress: 0,
    totalBatch: 0,
  });

  // Fetch jobs with enhanced filtering
  const {
    data: jobs = [],
    isLoading: jobsLoading,
    error: jobsError,
    refetch: refetchJobs,
  } = useQuery({
    queryKey: ["enhanced-jobs", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v));
          } else {
            params.set(key, String(value));
          }
        }
      });

      const queryString = params.toString();
      const path = queryString ? `jobs/enhanced?${queryString}` : "jobs/enhanced";
      return await apiGet<EnhancedJobPosting[]>(path);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (replaced cacheTime)
  });

  // Score a single job against user's profile
  const scoreJob = useCallback(async (
    job: EnhancedJobPosting
  ): Promise<JobMatchScore | null> => {
    if (!profile) {
      console.warn("Cannot score job: no user profile available");
      return null;
    }

    setMatchingState(prev => ({ ...prev, isScoring: true, lastScoredJob: job.id }));

    try {
      const score = await apiPost<JobMatchScore>("ai/match-job", {
        job_id: job.id,
        profile_context: {
          preferences: profile.preferences,
          resume_url: profile.resume_url,
          contact: profile.contact,
        },
        scoring_weights: {
          skills: 0.4,
          experience: 0.25,
          location: 0.2,
          salary: 0.15,
        },
      });

      // Update job in cache with match score
      queryClient.setQueryData(
        ["enhanced-jobs", filters],
        (oldJobs: EnhancedJobPosting[] | undefined) =>
          oldJobs?.map(j =>
            j.id === job.id ? { ...j, match_score: score } : j
          )
      );

      return score;
    } catch (error) {
      console.error("Failed to score job:", error);
      return null;
    } finally {
      setMatchingState(prev => ({ ...prev, isScoring: false, lastScoredJob: null }));
    }
  }, [profile, filters, queryClient]);

  // Batch score multiple jobs (optimized for performance)
  const scoreJobsBatch = useCallback(async (
    jobIds: string[],
    onProgress?: (completed: number, total: number) => void
  ): Promise<{ scores: Record<string, JobMatchScore>; errors: string[] }> => {
    if (!profile) {
      return { scores: {}, errors: ["No user profile available"] };
    }

    setMatchingState({
      isScoring: true,
      lastScoredJob: null,
      batchProgress: 0,
      totalBatch: jobIds.length,
    });

    try {
      const results = await apiPost<{ scores: Record<string, JobMatchScore> }>("ai/score-jobs-batch", {
        job_ids: jobIds,
        profile_context: {
          preferences: profile.preferences,
          resume_url: profile.resume_url,
          contact: profile.contact,
        },
        scoring_weights: {
          skills: 0.4,
          experience: 0.25,
          location: 0.2,
          salary: 0.15,
        },
      });

      // Update all jobs in cache with their scores
      queryClient.setQueryData(
        ["enhanced-jobs", filters],
        (oldJobs: EnhancedJobPosting[] | undefined) =>
          oldJobs?.map(job =>
            results.scores[job.id]
              ? { ...job, match_score: results.scores[job.id] }
              : job
          )
      );

      setMatchingState(prev => ({ ...prev, batchProgress: jobIds.length }));
      onProgress?.(jobIds.length, jobIds.length);

      return { scores: results.scores, errors: [] };
    } catch (error) {
      console.error("Batch scoring failed:", error);
      return { scores: {}, errors: ["Batch scoring failed"] };
    } finally {
      setMatchingState(prev => ({ ...prev, isScoring: false }));
    }
  }, [profile, filters, queryClient]);

  // Auto-score jobs as they load
  const scoredJobIdsRef = useRef<Set<string>>(new Set());
  useEffect(() => {
    let cancelled = false;

    if (jobs.length > 0 && profile) {
      const unscoredJobs = jobs.filter(
        (job: EnhancedJobPosting) => !job.match_score && !scoredJobIdsRef.current.has(job.id)
      );
      if (unscoredJobs.length > 0) {
        // Mark them as being scored to prevent re-triggering
        unscoredJobs.forEach((job: EnhancedJobPosting) => scoredJobIdsRef.current.add(job.id));

        // Score first 10 jobs immediately, rest in background
        const immediateJobs = unscoredJobs.slice(0, 10);
        const backgroundJobs = unscoredJobs.slice(10);

        if (!cancelled) {
          immediateJobs.forEach((job: EnhancedJobPosting) => {
            scoreJob(job);
          });
        }

        let bgTimer: ReturnType<typeof setTimeout> | null = null;
        if (backgroundJobs.length > 0 && !cancelled) {
          bgTimer = setTimeout(() => {
            if (!cancelled) {
              scoreJobsBatch(
                backgroundJobs.map((j: EnhancedJobPosting) => j.id),
                (completed: number, total: number) => {
                  if (!cancelled) {
                    setMatchingState(prev => ({
                      ...prev,
                      batchProgress: completed,
                      totalBatch: total,
                    }));
                  }
                }
              );
            }
          }, 1000);
        }

        return () => {
          cancelled = true;
          if (bgTimer) clearTimeout(bgTimer);
        };
      }
    }

    return () => {
      cancelled = true;
    };
  }, [jobs, profile]); // eslint-disable-line react-hooks/exhaustive-deps

  // Debounced filter updates — use useMemo to create a stable debounced function
  const debouncedSetFilters = useMemo(
    () => debounce((newFilters: MatchingFilters) => {
      setFilters(newFilters);
    }, 300),
    []
  );

  // Get recommended jobs based on AI scoring
  const getRecommendedJobs = useCallback((
    limit: number = 20,
    minScore: number = 0.7
  ): EnhancedJobPosting[] => {
    return jobs
      .filter((job: EnhancedJobPosting) => job.match_score && job.match_score.score >= minScore)
      .sort((a: EnhancedJobPosting, b: EnhancedJobPosting) => (b.match_score?.score || 0) - (a.match_score?.score || 0))
      .slice(0, limit);
  }, [jobs]);

  // Get jobs with potential issues (red flags)
  const getJobsWithWarnings = useCallback((): EnhancedJobPosting[] => {
    return jobs.filter((job: EnhancedJobPosting) =>
      job.match_score && job.match_score.red_flags.length > 0
    );
  }, [jobs]);

  // Update filters with validation
  const updateFilters = useCallback((newFilters: Partial<MatchingFilters>) => {
    const validatedFilters = { ...filters, ...newFilters };

    // Validate numeric inputs
    if (validatedFilters.minSalary !== undefined) {
      validatedFilters.minSalary = Math.max(0, validatedFilters.minSalary);
    }
    if (validatedFilters.maxSalary !== undefined) {
      validatedFilters.maxSalary = Math.max(0, validatedFilters.maxSalary);
    }
    if (validatedFilters.minMatchScore !== undefined) {
      validatedFilters.minMatchScore = Math.max(0, Math.min(1, validatedFilters.minMatchScore));
    }

    debouncedSetFilters(validatedFilters);
  }, [filters, debouncedSetFilters]);

  // Clear all cached scores
  const clearScores = useCallback(() => {
    queryClient.setQueryData(
      ["enhanced-jobs", filters],
      (oldJobs: EnhancedJobPosting[] | undefined) =>
        oldJobs?.map(job => ({ ...job, match_score: undefined }))
    );
  }, [filters, queryClient]);

  return {
    // Data
    jobs,
    // Memoized derived data
    recommendedJobs: useMemo(() => getRecommendedJobs(), [getRecommendedJobs]),
    jobsWithWarnings: useMemo(() => getJobsWithWarnings(), [getJobsWithWarnings]),

    // Loading states
    isLoading: jobsLoading,
    isScoring: matchingState.isScoring,
    scoringProgress: {
      current: matchingState.batchProgress,
      total: matchingState.totalBatch,
      percentage: matchingState.totalBatch > 0
        ? (matchingState.batchProgress / matchingState.totalBatch) * 100
        : 0,
    },

    // Error handling
    error: jobsError,

    // Actions
    scoreJob,
    scoreJobsBatch,
    updateFilters,
    setFilters: debouncedSetFilters,
    clearScores,
    refetchJobs,

    // State
    filters,
    matchingState,
  };
}
