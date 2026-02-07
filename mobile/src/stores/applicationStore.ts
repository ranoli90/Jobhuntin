/**
 * Part 4: Frontend State Management – Application Status, Real-time & Hold Logic (Zustand)
 */

import { create } from "zustand";
import { supabase } from "../lib/supabase";
import type {
  Application,
  ApplicationInput,
  ApplicationStatus,
  AnswerItem,
} from "../types";
import { submitApplicationInputs as apiSubmitInputs, getApplication } from "../api/client";
import { getStatusLabel } from "../lib/blueprintConfig";
import { track } from "../lib/analytics";

// ---------------------------------------------------------------------------
// Store shape
// ---------------------------------------------------------------------------
interface ApplicationStoreState {
  /** Map of application.id → Application */
  applications: Record<string, Application>;

  /** Map of application_id → ApplicationInput[] */
  inputs: Record<string, ApplicationInput[]>;

  /** Transient per-application processing indicator */
  processingFlags: Record<string, boolean>;

  // Actions
  initRealtimeSubscriptions: (userId: string) => void;
  disposeSubscriptions: () => void;
  submitApplicationInputs: (
    applicationId: string,
    answers: AnswerItem[]
  ) => Promise<void>;
  refreshApplication: (applicationId: string) => Promise<void>;
}

// ---------------------------------------------------------------------------
// Subscription handles (module-level so we can tear them down)
// ---------------------------------------------------------------------------
let appChannel: ReturnType<typeof supabase.channel> | null = null;
let inputChannel: ReturnType<typeof supabase.channel> | null = null;

// ---------------------------------------------------------------------------
// Zustand store
// ---------------------------------------------------------------------------
export const useApplicationStore = create<ApplicationStoreState>((set, get) => ({
  applications: {},
  inputs: {},
  processingFlags: {},

  // ----- Real-time subscriptions ------------------------------------------
  initRealtimeSubscriptions: (userId: string) => {
    // 1. Subscribe to applications changes for this user
    appChannel = supabase
      .channel("app-status")
      .on<Application>(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "applications",
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          const updated = payload.new as Application;
          track("application_status_changed", {
            application_id: updated.id,
            status: updated.status,
          });
          set((state) => ({
            applications: { ...state.applications, [updated.id]: updated },
            processingFlags: {
              ...state.processingFlags,
              [updated.id]: updated.status === "PROCESSING",
            },
          }));
        }
      )
      .subscribe();

    // 2. Subscribe to application_inputs for this user's applications
    //    Supabase Realtime doesn't support JOINs, so we listen to all
    //    inserts/updates and filter client-side.
    inputChannel = supabase
      .channel("app-inputs")
      .on<ApplicationInput>(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "application_inputs",
        },
        (payload) => {
          const input = payload.new as ApplicationInput;
          // Only process if the application belongs to this user
          const apps = get().applications;
          if (!apps[input.application_id]) return;

          set((state) => {
            const existing = state.inputs[input.application_id] ?? [];
            const idx = existing.findIndex((i) => i.id === input.id);
            const updated =
              idx >= 0
                ? existing.map((i) => (i.id === input.id ? input : i))
                : [...existing, input];
            return {
              inputs: { ...state.inputs, [input.application_id]: updated },
            };
          });
        }
      )
      .subscribe();
  },

  disposeSubscriptions: () => {
    if (appChannel) {
      supabase.removeChannel(appChannel);
      appChannel = null;
    }
    if (inputChannel) {
      supabase.removeChannel(inputChannel);
      inputChannel = null;
    }
  },

  // ----- Submit answers for hold questions --------------------------------
  submitApplicationInputs: async (
    applicationId: string,
    answers: AnswerItem[]
  ) => {
    track("hold_questions_answered", {
      application_id: applicationId,
      answer_count: answers.length,
    });

    // Optimistic update: mark inputs as answered locally
    set((state) => {
      const current = state.inputs[applicationId] ?? [];
      const answerMap = new Map(answers.map((a) => [a.input_id, a.answer]));
      const updated = current.map((inp) =>
        answerMap.has(inp.id)
          ? { ...inp, answer: answerMap.get(inp.id)!, answered_at: new Date().toISOString(), resolved: true }
          : inp
      );
      return { inputs: { ...state.inputs, [applicationId]: updated } };
    });

    // Call backend via typed API client
    await apiSubmitInputs(applicationId, answers);
    // Real-time subscription will reconcile final status
  },

  // ----- Refresh application from backend --------------------------------
  refreshApplication: async (applicationId: string) => {
    try {
      const detail = await getApplication(applicationId);
      const app = detail.application as unknown as Application;
      const inputs = detail.inputs as ApplicationInput[];
      set((state) => ({
        applications: { ...state.applications, [app.id]: app },
        inputs: { ...state.inputs, [applicationId]: inputs },
      }));
    } catch (err) {
      console.error("Failed to refresh application:", err);
    }
  },
}));

// ---------------------------------------------------------------------------
// Derived selector hooks (plain functions consuming the store)
// ---------------------------------------------------------------------------

/** Pending (unanswered) inputs for a given application */
export function usePendingInputs(applicationId: string): ApplicationInput[] {
  return useApplicationStore(
    (s) => (s.inputs[applicationId] ?? []).filter((i) => i.answer === null)
  );
}

/** Human-friendly status label for a given application (blueprint-aware) */
export function useApplicationStatusLabel(
  applicationId: string
): string {
  return useApplicationStore((s) => {
    const app = s.applications[applicationId];
    if (!app) return "";
    // Delegate to blueprint config for blueprint-aware status labels
    return getStatusLabel(app.status, app.blueprint_key);
  });
}

/** Whether the agent is actively processing a given application */
export function useIsProcessing(applicationId: string): boolean {
  return useApplicationStore((s) => !!s.processingFlags[applicationId]);
}
