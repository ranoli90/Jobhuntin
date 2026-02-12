export interface OnboardingStep {
    id: string;
    title: string;
    description: string;
}

export interface OnboardingFormData {
    linkedinUrl?: string;
    preferences?: any;
    resumeFile?: any;
    parsedResume?: any;
    calibrationQuestions?: any[];
    calibrationAnswers?: Record<string, any>;
    contactInfo?: {
        first_name: string;
        last_name: string;
        email: string;
        phone: string;
    };
}

export interface OnboardingState {
    currentStep: number;
    completedSteps: string[];
    formData: OnboardingFormData;
}

export interface ParsedResume {
    title?: string;
    skills?: string[];
    years?: number;
    summary?: string;
    headline?: string;
}
