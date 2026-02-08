import { useState, useCallback } from "react";

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
}

const STEPS: OnboardingStep[] = [
  { id: "welcome", title: "Welcome to JobHuntin", description: "Let's get you set up in 2 minutes" },
  { id: "resume", title: "Upload your resume", description: "We'll use this to find perfect matches" },
  { id: "preferences", title: "Job preferences", description: "Tell us what you're looking for" },
  { id: "ready", title: "You're ready!", description: "Time to start job hunting" },
];

export function useOnboarding() {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);

  const currentStepData = STEPS[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === STEPS.length - 1;
  const progress = ((currentStep + 1) / STEPS.length) * 100;

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

  return {
    steps: STEPS,
    currentStep,
    currentStepData,
    completedSteps,
    progress,
    isFirstStep,
    isLastStep,
    nextStep,
    prevStep,
    goToStep,
  };
}
