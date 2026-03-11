import React, { useState, useCallback, useEffect, useMemo } from "react";
import { telemetry } from "../lib/telemetry";
import { securePIIStorage } from "../lib/secureStorage";
import { safeSetStorage, safeGetStorage } from "../lib/utils";

import { OnboardingStep, OnboardingState, OnboardingFormData } from "../types/onboarding";

interface OfflineAction {
  type: string;
  payload: Record<string, unknown>;
  timestamp: number;
}

const STORAGE_KEY = "onboarding_state";

/** A6: Flush onboarding state before 401 redirect - registered by useOnboarding when active */
let _onboardingFlush: (() => void) | null = null;
export function registerOnboardingFlush(fn: (() => void) | null) {
  _onboardingFlush = fn;
}
export function flushOnboardingBeforeRedirect() {
  _onboardingFlush?.();
}

// PII fields that should be stored securely
const PII_FIELDS = ['contactInfo'];

// Helper to separate PII from non-PII data
const separatePII = (formData: OnboardingFormData) => {
  const pii: Partial<OnboardingFormData> = {};
  const nonPii: Partial<OnboardingFormData> = {};

  Object.keys(formData).forEach(key => {
    if (PII_FIELDS.includes(key)) {
      (pii as Record<string, unknown>)[key] = formData[key as keyof OnboardingFormData];
    } else {
      (nonPii as Record<string, unknown>)[key] = formData[key as keyof OnboardingFormData];
    }
  });

  return { pii, nonPii };
};

const STEPS: OnboardingStep[] = [
  { id: "welcome", title: "Welcome to JobHuntin", description: "Let's get you set up in 2 minutes" },
  { id: "resume", title: "Upload your resume", description: "We'll use this to find perfect matches" },
  { id: "skill-review", title: "Review your skills", description: "Verify the skills we detected" },
  { id: "confirm-contact", title: "Confirm your details", description: "Verify the info we extracted" },
  { id: "preferences", title: "Job preferences", description: "Tell us what you're looking for" },
  { id: "work-style", title: "Work style", description: "Help us find your ideal environment" },
  { id: "career-goals", title: "Career goals", description: "Where are you headed?" },
  { id: "ready", title: "You're ready!", description: "Time to start job hunting" },
];

export interface UseOnboardingOptions {
  /** P1: Server-side progress for cross-device resume */
  serverProgress?: { step: number; completed: string[] } | null;
  /** Sync progress to server when step/completed changes */
  syncToServer?: (step: number, completed: string[]) => void | Promise<void>;
  /** N1: Deep-link to step from URL ?step=N */
  initialStepFromUrl?: number | null;
  /** OB-009: Called when syncToServer fails (e.g. to show toast) */
  onSyncError?: (err: unknown) => void;
}

export function useOnboarding(options: UseOnboardingOptions = {}) {
  const { serverProgress, syncToServer, initialStepFromUrl, onSyncError } = options;
  const [isLoading, setIsLoading] = useState(true);

  // Parse localStorage and secure storage once on mount for all state initializers
  const loadInitialState = useCallback(async () => {
    try {
      let storedState: OnboardingState | null = null;
      try {
        const stored = safeGetStorage(STORAGE_KEY);
        if (stored) storedState = JSON.parse(stored);
      } catch {
        if (import.meta.env.DEV) console.warn("[useOnboarding] Failed to parse stored state");
      }
      // Get PII data from secure storage
      let piiData: Partial<OnboardingFormData> = {};
      try {
        piiData = (await securePIIStorage.get('contact_info')) || {};
      } catch (error) {
        if (import.meta.env.DEV) console.warn('[useOnboarding] Failed to load PII from secure storage:', error);
      }

      // Merge the data
      const mergedFormData = { ...(storedState?.formData || {}), ...piiData };

      return storedState ? { ...storedState, formData: mergedFormData } : null;
    } catch (e) {
      if (import.meta.env.DEV) console.warn('[useOnboarding] Corrupted storage, resetting:', e);
      try {
        localStorage.removeItem(STORAGE_KEY);
        securePIIStorage.clear();
      } catch { }
    }
    return null;
  }, []);

  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [formData, setFormData] = useState<OnboardingFormData>({});

  // Initialize async state loading; use server progress when no localStorage (cross-device)
  // N1: URL ?step=N takes precedence for deep-linking
  useEffect(() => {
    let cancelled = false;
    loadInitialState()
      .then(initialState => {
      if (cancelled) return;
      let step = 0;
      let completed: string[] = [];
      if (initialState) {
        step = initialState.currentStep;
        completed = initialState.completedSteps || [];
      }
      if (serverProgress && serverProgress.step >= 0) {
        if (!initialState || serverProgress.step > step) {
          step = serverProgress.step;
          completed = serverProgress.completed || [];
          if (import.meta.env.DEV) console.log('[useOnboarding] Using server progress:', step, completed);
        }
      }
      if (initialStepFromUrl != null && initialStepFromUrl >= 0) {
        step = Math.min(initialStepFromUrl, 7); // Max step index (8 steps)
        if (import.meta.env.DEV) console.log('[useOnboarding] Using URL step:', step);
      }
      setCurrentStep(step);
      setCompletedSteps(completed);
      if (initialState) setFormData(initialState.formData);
      setIsLoading(false);
    })
      .catch((err) => {
        if (!cancelled && import.meta.env.DEV) console.warn("[useOnboarding] loadInitialState failed:", err);
        if (!cancelled) setIsLoading(false);
      });
    return () => { cancelled = true; };
  }, [loadInitialState, serverProgress, initialStepFromUrl]);

  const saveState = useCallback(async () => {
    const { pii, nonPii } = separatePII(formData);
    const state: OnboardingState = {
      currentStep,
      completedSteps,
      formData: nonPii,
    };

    try {
      if (import.meta.env.DEV) console.log('[useOnboarding] Saving non-PII state:', state);
      if (!safeSetStorage(STORAGE_KEY, JSON.stringify(state))) {
        if (import.meta.env.DEV) console.warn('[useOnboarding] Could not persist state; progress may be lost on refresh');
      }

      if (syncToServer) {
        try {
          await syncToServer(currentStep, completedSteps);
        } catch (e) {
          if (import.meta.env.DEV) console.warn('[useOnboarding] Server sync failed:', e);
          onSyncError?.(e);
        }
      }

      if (Object.keys(pii).length > 0) {
        try {
          await securePIIStorage.set('contact_info', pii);
          if (import.meta.env.DEV) console.log('[useOnboarding] Saved PII to secure storage');
        } catch (e) {
          if (import.meta.env.DEV) console.warn('[useOnboarding] PII save failed (storage may be full):', e);
        }
      }
    } catch (error) {
      if (import.meta.env.DEV) console.error('[useOnboarding] Failed to save state:', error);
      try {
        localStorage.removeItem(STORAGE_KEY);
        securePIIStorage.clear();
        const minimalState = { currentStep: 0, completedSteps: [], formData: {} };
        safeSetStorage(STORAGE_KEY, JSON.stringify(minimalState));
        if (import.meta.env.DEV) console.log('[useOnboarding] Recovered with minimal state');
      } catch (recoveryError) {
        if (import.meta.env.DEV) console.error('[useOnboarding] Failed to recover state:', recoveryError);
      }
    }
  }, [currentStep, completedSteps, formData, syncToServer, onSyncError]);

  const updateFormData = useCallback((updates: Partial<OnboardingState['formData']>) => {
    setFormData(prev => ({ ...prev, ...updates }));
  }, []);

  // A/B Test: Variant Assignment
  const [abVariant, setAbVariant] = useState<"resume_first" | "role_first">("resume_first");

  useEffect(() => {
    const storedVariant = safeGetStorage("onboarding_ab_variant");
    if (storedVariant) {
      setAbVariant(storedVariant as "resume_first" | "role_first");
    } else {
      const newVariant = Math.random() > 0.5 ? "resume_first" : "role_first";
      if (!safeSetStorage("onboarding_ab_variant", newVariant)) {
        if (import.meta.env.DEV) console.warn("[useOnboarding] Could not persist A/B variant (QuotaExceeded?)");
      }
      setAbVariant(newVariant);
      // Log exposure
      telemetry.track("A/B Test Assignment", { onboarding_flow: newVariant });
    }
  }, []);

  // Dynamic Steps based on Variant
  const currentSteps = useMemo(() => {
    if (abVariant === "role_first") {
      // Swap Resume and Preferences to test "Intent vs Payload"
      // New STEPS order: Welcome, Preferences, Resume, SkillReview, Contact, WorkStyle, CareerGoals, Ready
      return [
        STEPS[0], // Welcome
        STEPS[4], // Preferences
        STEPS[1], // Resume
        STEPS[2], // SkillReview
        STEPS[3], // ConfirmContact
        STEPS[5], // WorkStyle
        STEPS[6], // CareerGoals
        STEPS[7], // Ready
      ];
    }
    return STEPS;
  }, [abVariant]);

  const currentStepData = currentSteps[currentStep] ?? currentSteps[0];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === currentSteps.length - 1;
  const progress = currentSteps.length > 0 ? ((currentStep + 1) / currentSteps.length) * 100 : 0;

  // C2: Debounce rapid back/forward to avoid state thrashing
  const lastNavRef = React.useRef(0);
  const NAV_DEBOUNCE_MS = 150;

  const nextStep = useCallback(() => {
    if (Date.now() - lastNavRef.current < NAV_DEBOUNCE_MS) return;
    lastNavRef.current = Date.now();
    const totalSteps = currentSteps.length;
    if (import.meta.env.DEV) console.log('[useOnboarding] nextStep called, totalSteps:', totalSteps);

    setCurrentStep((prev) => {
      if (prev < totalSteps - 1) {
        if (import.meta.env.DEV) console.log('[useOnboarding] Advancing from step', prev, 'to', prev + 1);

        const completedStepId = currentSteps[prev]?.id;
        if (completedStepId) {
          telemetry.track("onboarding_step_completed", {
            step_id: completedStepId,
            step_number: prev + 1,
            total_steps: totalSteps,
          });
          setCompletedSteps((prevCompleted) => {
            const newCompleted = new Set(prevCompleted);
            newCompleted.add(completedStepId);
            return Array.from(newCompleted);
          });
        }

        return prev + 1;
      }
      if (import.meta.env.DEV) console.log('[useOnboarding] Already at last step, staying at', prev);
      return prev;
    });
  }, [currentSteps]);

  const prevStep = useCallback(() => {
    if (Date.now() - lastNavRef.current < NAV_DEBOUNCE_MS) return;
    lastNavRef.current = Date.now();
    if (!isFirstStep) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [isFirstStep]);

  const goToStep = useCallback((index: number) => {
    if (index < 0 || index >= currentSteps.length) return;
    // Can't skip more than one step ahead - must complete steps in order
    if (index > currentStep + 1) return;
    setCurrentStep(index);
  }, [currentSteps.length, currentStep]);

  // S1: Save immediately on step/completed; debounce on formData (rapid typing)
  useEffect(() => {
    saveState();
  }, [currentStep, completedSteps, saveState, syncToServer]);

  // OB-010: When syncToServer becomes available (profile loads), sync current progress
  const prevSyncRef = React.useRef(syncToServer);
  useEffect(() => {
    if (syncToServer && !prevSyncRef.current) {
      saveState();
    }
    prevSyncRef.current = syncToServer;
  }, [syncToServer, saveState]);
  useEffect(() => {
    const t = setTimeout(() => saveState(), 400);
    return () => clearTimeout(t);
  }, [formData, saveState]);

  // A6: Register flush for 401 redirect - persist state before navigation
  const stateRef = React.useRef({ currentStep, completedSteps, formData });
  useEffect(() => {
    stateRef.current = { currentStep, completedSteps, formData };
  }, [currentStep, completedSteps, formData]);
  useEffect(() => {
    registerOnboardingFlush(() => {
      const { currentStep: s, completedSteps: c, formData: f } = stateRef.current;
      const { nonPii } = separatePII(f);
      safeSetStorage(STORAGE_KEY, JSON.stringify({ currentStep: s, completedSteps: c, formData: nonPii }));
    });
    return () => registerOnboardingFlush(null);
  }, []);

  const resetOnboarding = useCallback(async () => {
    setCurrentStep(0);
    setCompletedSteps([]);
    setFormData({});
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem("offline_queue");
      securePIIStorage.clear();
    } catch {
      /* ignore */
    }
  }, []);

  // Offline Queue Processing: retry on reconnect
  useEffect(() => {
    const processQueue = async () => {
      if (!navigator.onLine) return;
      try {
        const raw = safeGetStorage("offline_queue");
        if (!raw) return;
        const queue = JSON.parse(raw);
        if (queue.length === 0) return;

        const MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24h
        const valid = queue.filter((a: { timestamp?: number }) => !a.timestamp || Date.now() - a.timestamp < MAX_AGE_MS);
        if (valid.length === 0) {
          try {
            localStorage.removeItem("offline_queue");
            sessionStorage.removeItem("offline_queue");
          } catch {
            /* ignore */
          }
          return;
        }

        // Retry: dispatch custom event so onboarding steps can re-submit; clear queue after attempt
        window.dispatchEvent(new CustomEvent("offline_queue:retry", { detail: valid }));
        try {
          localStorage.removeItem("offline_queue");
          sessionStorage.removeItem("offline_queue");
        } catch {
          /* ignore */
        }
      } catch (error) {
        if (import.meta.env.DEV) console.error("[useOnboarding] Failed to process offline queue:", error);
      }
    };

    window.addEventListener("online", processQueue);
    processQueue(); // Run once if already online (e.g. page load after reconnect)
    return () => window.removeEventListener("online", processQueue);
  }, []);

  const queueOfflineAction = useCallback((action: OfflineAction) => {
    try {
      const queue = JSON.parse(safeGetStorage("offline_queue") || "[]");
      queue.push({ ...action, timestamp: Date.now() });
      if (!safeSetStorage("offline_queue", JSON.stringify(queue))) {
        if (import.meta.env.DEV) console.warn("[useOnboarding] Failed to queue offline action (QuotaExceeded?)");
      }
    } catch (error) {
      if (import.meta.env.DEV) console.error("[useOnboarding] Failed to queue offline action:", error);
    }
  }, []);

  return {
    steps: currentSteps,
    currentStep,
    currentStepData,
    completedSteps,
    formData,
    progress,
    isFirstStep,
    isLastStep,
    nextStep,
    prevStep,
    goToStep,
    updateFormData,
    resetOnboarding,
    queueOfflineAction,
    isLoading,
  };
}
