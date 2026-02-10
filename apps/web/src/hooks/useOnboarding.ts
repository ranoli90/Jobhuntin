import { useState, useCallback, useEffect } from "react";

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
}

interface OnboardingState {
  currentStep: number;
  completedSteps: string[];
  formData: {
    linkedinUrl?: string;
    preferences?: any;
    resumeFile?: any;
    parsedResume?: any;
  };
}

const STORAGE_KEY = "onboarding_state";

const STEPS: OnboardingStep[] = [
  { id: "welcome", title: "Welcome to JobHuntin", description: "Let's get you set up in 2 minutes" },
  { id: "resume", title: "Upload your resume", description: "We'll use this to find perfect matches" },
  { id: "confirm-contact", title: "Confirm your details", description: "Verify the info we extracted" },
  { id: "preferences", title: "Job preferences", description: "Tell us what you're looking for" },
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

  const currentStepData = STEPS[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === STEPS.length - 1;
  const progress = ((currentStep + 1) / STEPS.length) * 100;

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

  const nextStep = useCallback(() => {
    if (!isLastStep) {
      setCompletedSteps((prev) => [...prev, STEPS[currentStep].id]);
      setCurrentStep((prev) => prev + 1);
    }
  }, [currentStep, isLastStep]);

  const prevStep = useCallback(() => {
    if (!isFirstStep) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [isFirstStep]);

  const goToStep = useCallback((index: number) => {
    if (index >= 0 && index < STEPS.length) {
      setCurrentStep(index);
    }
  }, []);

  useEffect(() => {
    saveState();
  }, [currentStep, completedSteps, formData, saveState]);

  const resetOnboarding = useCallback(() => {
    setCurrentStep(0);
    setCompletedSteps([]);
    setFormData({});
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
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
