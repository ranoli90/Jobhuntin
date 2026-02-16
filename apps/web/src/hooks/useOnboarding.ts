import { useState, useCallback, useEffect, useMemo } from "react";

import { OnboardingStep, OnboardingState, OnboardingFormData } from "../types/onboarding";
import { telemetry } from "../lib/logger";

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
  const [currentStep, setCurrentStep] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const state: OnboardingState = JSON.parse(stored);
        return state.currentStep || 0;
      }
    } catch {
      // ignore
    }
    return 0;
  });

  const [completedSteps, setCompletedSteps] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const state: OnboardingState = JSON.parse(stored);
        return state.completedSteps || [];
      }
    } catch {
      // ignore
    }
    return [];
  });

  const [formData, setFormData] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const state: OnboardingState = JSON.parse(stored);
        return state.formData || {};
      }
    } catch {
      // ignore
    }
    return {};
  });

  const saveState = useCallback(() => {
    try {
      const state: OnboardingState = {
        currentStep,
        completedSteps,
        formData,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.warn("Failed to save onboarding state:", error);
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

  const currentStepData = currentSteps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === currentSteps.length - 1;
  const progress = ((currentStep + 1) / currentSteps.length) * 100;

  const nextStep = useCallback(() => {
    const totalSteps = currentSteps.length;
    setCurrentStep((prev) => {
      // Basic Telemetry
      telemetry.track("Onboarding Step Completed", { 
        step: currentSteps[prev].id, 
        index: prev 
      });
      // Mark current step as completed
      setCompletedSteps((prevCompleted) => {
        const newCompleted = new Set(prevCompleted);
        newCompleted.add(currentSteps[prev].id); // Add the ID of the completed step
        return Array.from(newCompleted); // Convert Set back to Array
      });

      if (prev < totalSteps - 1) { // Check if not the last step
        return prev + 1;
      }
      return prev; // Stay on the last step if already there
    });
  }, [currentSteps, setCompletedSteps]);

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

  // Offline Queue Processing
  useEffect(() => {
    const processQueue = async () => {
      if (navigator.onLine) {
        const queue = JSON.parse(localStorage.getItem("offline_queue") || "[]");
        if (queue.length > 0) {
          // We would iterate and retry here, but since our API is not fully set up for generic replay
          // we will just log for now or clear it if it's too old. 
          // In a real implementation, we'd map these to api calls.
          console.log("Processing offline queue:", queue);
          // For this demo, let's just clear it after 'processing'
          localStorage.removeItem("offline_queue");
        }
      }
    };

    window.addEventListener('online', processQueue);
    return () => window.removeEventListener('online', processQueue);
  }, []);

  const queueOfflineAction = useCallback((action: any) => {
    const queue = JSON.parse(localStorage.getItem("offline_queue") || "[]");
    queue.push({ ...action, timestamp: Date.now() });
    localStorage.setItem("offline_queue", JSON.stringify(queue));
  }, []);

  return {
    steps: STEPS,
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
