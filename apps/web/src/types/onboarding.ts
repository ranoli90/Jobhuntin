export interface OnboardingStep {
    id: string;
    title: string;
    description: string;
}

export interface RichSkill {
    skill: string;
    confidence: number;
    years_actual: number | null;
    context: string;
    last_used: string | null;
    verified: boolean;
    related_to: string[];
    source: string;
    project_count: number;
}

export interface WorkStyleProfile {
    autonomy_preference: 'high' | 'medium' | 'low';
    learning_style: 'docs' | 'building' | 'pairing' | 'courses';
    company_stage_preference: 'early_startup' | 'growth' | 'enterprise' | 'flexible';
    communication_style: 'async' | 'sync' | 'mixed' | 'flexible';
    pace_preference: 'fast' | 'steady' | 'methodical' | 'flexible';
    ownership_preference: 'solo' | 'team' | 'lead' | 'flexible';
    career_trajectory: 'ic' | 'tech_lead' | 'manager' | 'founder' | 'open';
}

export interface OnboardingFormData {
    linkedinUrl?: string;
    preferences?: any;
    resumeFile?: any;
    parsedResume?: any;
    parsedProfile?: any;
    richSkills?: RichSkill[];
    workStyleAnswers?: Record<string, string>;
    workStyle?: WorkStyleProfile;
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

export interface BehavioralQuestion {
    id: string;
    question: string;
    options: string[];
    maps_to: string;
}

export interface TrajectoryOption {
    value: string;
    label: string;
}
