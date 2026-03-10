/**
 * Part 4: Frontend State Management – Job Feed & Swipe Store (Zustand)
 *
 * Uses REST API (GET /me/jobs, POST /me/applications) - Render backend, no Supabase.
 */

import { create } from "zustand";
import type { Job, Application } from "../types";
import {
  createApplication as apiCreateApplication,
  getJobs,
  QuotaExceededError,
} from "../api/client";
import { track } from "../lib/analytics";

// ---------------------------------------------------------------------------
// Store shape
// ---------------------------------------------------------------------------
interface JobStoreState {
  jobs: Job[];
  currentIndex: number;
  isLoadingJobs: boolean;

  /** Map of job_id → local Application record (optimistic + server) */
  swipedApplications: Record<string, Application>;

  /** Set when a swipe-right fails due to quota limit */
  quotaExceeded: { plan: string; used: number; limit: number } | null;
  clearQuotaExceeded: () => void;

  loadJobs: () => Promise<void>;
  swipeRight: (job: Job) => Promise<void>;
  swipeLeft: (job: Job) => void;
}

// ---------------------------------------------------------------------------
// Backend helpers
// ---------------------------------------------------------------------------

async function fetchJobsFromBackend(): Promise<Job[]> {
  const { jobs } = await getJobs({ limit: 50, offset: 0 });
  return jobs;
}

// ---------------------------------------------------------------------------
// Zustand store
// ---------------------------------------------------------------------------
export const useJobStore = create<JobStoreState>((set, get) => ({
  jobs: [],
  currentIndex: 0,
  isLoadingJobs: false,
  swipedApplications: {},
  quotaExceeded: null,
  clearQuotaExceeded: () => set({ quotaExceeded: null }),

  loadJobs: async () => {
    set({ isLoadingJobs: true });
    try {
      const jobs = await fetchJobsFromBackend();
      set({ jobs, currentIndex: 0, isLoadingJobs: false });
    } catch (err) {
      console.error("Failed to load jobs:", err);
      set({ isLoadingJobs: false });
    }
  },

  swipeRight: async (job: Job) => {
    track("job_swipe_right", { job_id: job.id, job_title: job.title });
    const { currentIndex, swipedApplications } = get();

    // Optimistic local entry
    const optimistic: Application = {
      id: `temp-${job.id}`,
      user_id: "",
      job_id: job.id,
      tenant_id: null,
      blueprint_key: "job-app",
      status: "QUEUED",
      error_message: null,
      locked_at: null,
      submitted_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    set({
      currentIndex: currentIndex + 1,
      swipedApplications: { ...swipedApplications, [job.id]: optimistic },
    });

    try {
      const serverApp = await apiCreateApplication(job.id);
      track("application_created", { job_id: job.id, application_id: serverApp.id });
      set((state) => ({
        swipedApplications: {
          ...state.swipedApplications,
          [job.id]: serverApp,
        },
      }));
    } catch (err) {
      // Remove optimistic entry on failure
      set((state) => {
        const copy = { ...state.swipedApplications };
        delete copy[job.id];
        return { swipedApplications: copy };
      });

      if (err instanceof QuotaExceededError) {
        set({ quotaExceeded: { plan: err.plan, used: err.used, limit: err.limit } });
      } else {
        console.error("Failed to create application:", err);
      }
    }
  },

  swipeLeft: (_job: Job) => {
    track("job_swipe_left", { job_id: _job.id, job_title: _job.title });
    set((state) => ({ currentIndex: state.currentIndex + 1 }));
  },
}));
