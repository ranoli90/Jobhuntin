/**
 * Saved Jobs Hook - Job Bookmarking Functionality
 * Microsoft-level implementation with optimistic updates and caching
 */

import { useState, useCallback, useEffect } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { apiPost, apiGet, apiDelete } from "../lib/api";

export interface SavedJob {
  id: string;
  job_id: string;
  user_id: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  job_data: {
    id: string;
    title: string;
    company: string;
    location: string;
    salary_min?: number;
    salary_max?: number;
    description?: string;
  };
}

export interface SaveJobRequest {
  job_id: string;
}

interface SavedJobsState {
  savedJobs: SavedJob[];
  isLoading: boolean;
  error: string | null;
  savedJobIds: Set<string>;
}

export function useSavedJobs() {
  const queryClient = useQueryClient();
  const [state, setState] = useState<SavedJobsState>({
    savedJobs: [],
    isLoading: false,
    error: null,
    savedJobIds: new Set(),
  });

  // Fetch saved jobs
  const {
    data: savedJobs = [],
    isLoading: savedJobsLoading,
    error: savedJobsError,
    refetch: refetchSavedJobs,
  } = useQuery({
    queryKey: ["saved-jobs"],
    queryFn: async () => {
      return await apiGet<SavedJob[]>("saved-jobs");
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Update state when data changes
  useEffect(() => {
    const savedIds = new Set(savedJobs.map((job) => job.job_id));
    setState((previous) => ({
      ...previous,
      savedJobs,
      isLoading: savedJobsLoading,
      error:
        savedJobsError instanceof Error
          ? savedJobsError.message
          : (savedJobsError
            ? String(savedJobsError)
            : null),
      savedJobIds: savedIds,
    }));
  }, [savedJobs, savedJobsLoading, savedJobsError]);

  // Save job mutation
  const saveJobMutation = useMutation({
    mutationFn: async (request: SaveJobRequest) => {
      return await apiPost<SavedJob>("saved-jobs", request);
    },
    onMutate: async (request) => {
      // Optimistic update
      const temporaryJob: SavedJob = {
        id: `temp-${Date.now()}`,
        job_id: request.job_id,
        user_id: "",
        tenant_id: "",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        job_data: {
          id: request.job_id,
          title: "",
          company: "",
          location: "",
        },
      };

      setState((previous) => ({
        ...previous,
        savedJobs: [temporaryJob, ...previous.savedJobs],
        savedJobIds: new Set([...previous.savedJobIds, request.job_id]),
      }));

      // Update cache
      queryClient.setQueryData(["saved-jobs"], (old: SavedJob[] | undefined) =>
        old ? [temporaryJob, ...old] : [temporaryJob],
      );
    },
    onSuccess: (savedJob) => {
      // Replace optimistic update with real data
      setState((previous) => ({
        ...previous,
        savedJobs: [
          savedJob,
          ...previous.savedJobs.filter((job) => job.job_id !== savedJob.job_id),
        ],
      }));

      queryClient.setQueryData(
        ["saved-jobs"],
        (old: SavedJob[] | undefined) => {
          if (!old) return [savedJob];
          return [
            savedJob,
            ...old.filter((job) => job.job_id !== savedJob.job_id),
          ];
        },
      );
    },
    onError: (error) => {
      // Revert optimistic update
      setState((previous) => {
        const jobId = (error as any)?.config?.data?.job_id;
        if (!jobId) return previous;

        return {
          ...previous,
          savedJobs: previous.savedJobs.filter((job) => job.job_id !== jobId),
          savedJobIds: new Set(
            [...previous.savedJobIds].filter((id) => id !== jobId),
          ),
        };
      });

      queryClient.invalidateQueries({ queryKey: ["saved-jobs"] });
    },
  });

  // Unsave job mutation
  const unsaveJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      return await apiDelete(`saved-jobs/${jobId}`);
    },
    onMutate: async (jobId) => {
      // Optimistic update
      setState((previous) => ({
        ...previous,
        savedJobs: previous.savedJobs.filter((job) => job.job_id !== jobId),
        savedJobIds: new Set(
          [...previous.savedJobIds].filter((id) => id !== jobId),
        ),
      }));

      // Update cache
      queryClient.setQueryData(
        ["saved-jobs"],
        (old: SavedJob[] | undefined) =>
          old?.filter((job) => job.job_id !== jobId) || [],
      );
    },
    onSuccess: (_, jobId) => {
      // Cache is already updated by onMutate
      queryClient.invalidateQueries({ queryKey: ["saved-jobs"] });
    },
    onError: (error, jobId) => {
      // Revert optimistic update
      queryClient.invalidateQueries({ queryKey: ["saved-jobs"] });
    },
  });

  // Memoized functions
  const saveJob = useCallback(
    (jobId: string) => {
      if (state.savedJobIds.has(jobId)) {
        return; // Already saved
      }
      saveJobMutation.mutate({ job_id: jobId });
    },
    [saveJobMutation, state.savedJobIds],
  );

  const unsaveJob = useCallback(
    (jobId: string) => {
      if (!state.savedJobIds.has(jobId)) {
        return; // Not saved
      }
      unsaveJobMutation.mutate(jobId);
    },
    [unsaveJobMutation, state.savedJobIds],
  );

  const isJobSaved = useCallback(
    (jobId: string) => {
      return state.savedJobIds.has(jobId);
    },
    [state.savedJobIds],
  );

  const getSavedJob = useCallback(
    (jobId: string) => {
      return state.savedJobs.find((job) => job.job_id === jobId);
    },
    [state.savedJobs],
  );

  return {
    // State
    ...state,

    // Actions
    saveJob,
    unsaveJob,
    refetchSavedJobs,

    // Queries
    isJobSaved,
    getSavedJob,

    // Mutation states
    isSaving: saveJobMutation.isPending,
    isUnsaving: unsaveJobMutation.isPending,
    saveError: saveJobMutation.error,
    unsaveError: unsaveJobMutation.error,
  };
}
