import { useState, useCallback, useEffect, useMemo } from "react";
import { telemetry } from "../lib/telemetry";

import { OnboardingStep, OnboardingState, OnboardingFormData } from "../types/onboarding";

const STORAGE_KEY = "onboarding_state";

const STEPS: OnboardingStep[] = [
  { id: "welcome", title: "Welcome to JobHuntin", description: "Let's get you set up in 2 minutes" },
  { id: "resume", title: "Upload your resume", description: "We'll use this to find perfect matches" },
  { id: "skill-review", title: "Review your skills", description: "Verify the skills we detected" },
  { id: "confirm-contact", title: "Confirm your details", description: "Verify the info we extracted" },
  { id: "preferences", title: "Job preferences", description: "Tell us what you're looking for" },
  { id: "work-style", title: "Work style", description: "Help us find your ideal environment" },
  { id: "ready", title: "You're ready!", description: "Time to start job hunting" },
];

export function useOnboarding() {
  // Parse localStorage once on mount for all state initializers
  const _initialState = (() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const state: OnboardingState = JSON.parse(stored);
        return state;
      }
    } catch (e) {
      console.warn('[useOnboarding] Corrupted storage, resetting:', e);
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch { }
    }
    return null;
  })();

  const [currentStep, setCurrentStep] = useState(() => {
    const step = _initialState?.currentStep;
    return typeof step === 'number' && step >= 0 ? step : 0;
  });

  const [completedSteps, setCompletedSteps] = useState<string[]>(() => {
    return Array.isArray(_initialState?.completedSteps) ? _initialState!.completedSteps : [];
  });

  const [formData, setFormData] = useState(() => {
    return _initialState?.formData && typeof _initialState.formData === 'object' ? _initialState.formData : {};
  });

  const saveState = useCallback(() => {
    try {
      const state: OnboardingState = {
        currentStep,
        completedSteps,
        formData,
      };
      if (import.meta.env.DEV) console.log('[useOnboarding] Saving state:', state);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error('[useOnboarding] Failed to save state:', error);
      // Attempt to clear corrupted data and save minimal state
      try {
        localStorage.removeItem(STORAGE_KEY);
        const minimalState = { currentStep: 0, completedSteps: [], formData: {} };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(minimalState));
        if (import.meta.env.DEV) console.log('[useOnboarding] Recovered with minimal state');
      } catch (recoveryError) {
        console.error('[useOnboarding] Failed to recover state:', recoveryError);
      }
    }
  }, [currentStep, completedSteps, formData]);

  const updateFormData = useCallback((updates: Partial<OnboardingState['formData']>) => {
    setFormData(prev => ({ ...prev, ...updates }));
  }, []);

  // A/B Test: Variant Assignment
  const [abVariant, setAbVariant] = useState<"resume_first" | "role_first">("resume_first");

  useEffect(() => {
    const storedVariant = localStorage.getItem("onboarding_ab_variant");
    if (storedVariant) {
      setAbVariant(storedVariant as any);
    } else {
      // 50/50 split
      const newVariant = Math.random() > 0.5 ? "resume_first" : "role_first";
      localStorage.setItem("onboarding_ab_variant", newVariant);
      setAbVariant(newVariant);
      // Log exposure
      telemetry.track("A/B Test Assignment", { onboarding_flow: newVariant });
    }
  }, []);

  // Dynamic Steps based on Variant
  const currentSteps = useMemo(() => {
    if (abVariant === "role_first") {
      // Swap Resume and Preferences to test "Intent vs Payload"
      // New STEPS order: Welcome, Preferences, Resume, SkillReview, Contact, WorkStyle, Ready
      return [
        STEPS[0], // Welcome (index 0)
        STEPS[4], // Preferences (index 4 in original)
        STEPS[1], // Resume (index 1)
        STEPS[2], // SkillReview (index 2)
        STEPS[3], // ConfirmContact (index 3)
        STEPS[5], // WorkStyle (index 5)
        STEPS[6]  // Ready (index 6)
      ];
    }
    return STEPS;
  }, [abVariant]);

  const currentStepData = currentSteps[currentStep] ?? currentSteps[0];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === currentSteps.length - 1;
  const progress = currentSteps.length > 0 ? ((currentStep + 1) / currentSteps.length) * 100 : 0;

  const nextStep = useCallback(() => {
    const totalSteps = currentSteps.length;
    if (import.meta.env.DEV) console.log('[useOnboarding] nextStep called, totalSteps:', totalSteps);

    setCurrentStep((prev) => {
      if (prev < totalSteps - 1) {
        if (import.meta.env.DEV) console.log('[useOnboarding] Advancing from step', prev, 'to', prev + 1);

        const completedStepId = currentSteps[prev]?.id;
        if (completedStepId) {
          telemetry.track("Onboarding Step Completed", {
            step: completedStepId,
            index: prev
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
    if (!isFirstStep) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [isFirstStep]);

  const goToStep = useCallback((index: number) => {
    if (index >= 0 && index < currentSteps.length) {
      setCurrentStep(index);
    }
  }, [currentSteps.length]);

  useEffect(() => {
    saveState();
  }, [currentStep, completedSteps, formData, saveState]);

  const resetOnboarding = useCallback(() => {
    setCurrentStep(0);
    setCompletedSteps([]);
    setFormData({});
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem("offline_queue");
    } catch {
      /* ignore */
    }
  }, []);

  // Offline Queue Processing: retry on reconnect
  useEffect(() => {
    const processQueue = async () => {
      if (!navigator.onLine) return;
      try {
        const raw = localStorage.getItem("offline_queue");
        if (!raw) return;
        const queue = JSON.parse(raw);
        if (queue.length === 0) return;

        const MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24h
        const valid = queue.filter((a: { timestamp?: number }) => !a.timestamp || Date.now() - a.timestamp < MAX_AGE_MS);
        if (valid.length === 0) {
          localStorage.removeItem("offline_queue");
          return;
        }

        // Retry: dispatch custom event so onboarding steps can re-submit; clear queue after attempt
        window.dispatchEvent(new CustomEvent("offline_queue:retry", { detail: valid }));
        localStorage.removeItem("offline_queue");
      } catch (error) {
        console.error("[useOnboarding] Failed to process offline queue:", error);
        try {
          localStorage.removeItem("offline_queue");
        } catch {
          /* ignore */
        }
      }
    };

    window.addEventListener("online", processQueue);
    processQueue(); // Run once if already online (e.g. page load after reconnect)
    return () => window.removeEventListener("online", processQueue);
  }, []);

  const queueOfflineAction = useCallback((action: any) => {
    try {
      const queue = JSON.parse(localStorage.getItem("offline_queue") || "[]");
      queue.push({ ...action, timestamp: Date.now() });
      localStorage.setItem("offline_queue", JSON.stringify(queue));
    } catch (error) {
      console.error('[useOnboarding] Failed to queue offline action:', error);
      // Try to clear and retry
      try {
        localStorage.removeItem("offline_queue");
        const newQueue = [{ ...action, timestamp: Date.now() }];
        localStorage.setItem("offline_queue", JSON.stringify(newQueue));
      } catch (retryError) {
        console.error('[useOnboarding] Failed to retry offline action queue:', retryError);
      }
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
  };
}
