/**
 * Advanced Cover Letter Generation Hook
 * Microsoft-level implementation with AI integration and template management
 */

import { useState, useCallback, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiPost, apiGet } from "../lib/api";
import { useProfile, type UserProfile } from "./useProfile";
import type { JobPosting } from "./useJobs";

export interface CoverLetterTemplate {
  id: string;
  name: string;
  description: string;
  category: "professional" | "creative" | "technical" | "executive" | "entry";
  content: string;
  variables: string[];
  is_default: boolean;
}

export interface CoverLetterGenerationRequest {
  job_id: string;
  template_id?: string;
  tone: "professional" | "friendly" | "enthusiastic" | "formal";
  length: "concise" | "standard" | "detailed";
  focus_areas: string[];
  custom_instructions?: string;
}

export interface GeneratedCoverLetter {
  id: string;
  job_id: string;
  content: string;
  template_used: string;
  tone: string;
  word_count: number;
  quality_score: number;
  suggestions: string[];
  generated_at: string;
  is_bookmarked: boolean;
}

export interface CoverLetterAnalytics {
  total_generated: number;
  success_rate: number;
  average_quality_score: number;
  most_used_tones: Record<string, number>;
  most_used_templates: Record<string, number>;
  response_rate_by_tone: Record<string, number>;
}

// Legacy interface for backward compatibility
export interface CoverLetterResponse {
  content: string;
  subject_line: string;
}

interface GenerationState {
  isGenerating: boolean;
  currentJobId: string | null;
  progress: number;
  estimatedTime: number;
}

export function useCoverLetter() {
  const queryClient = useQueryClient();
  const { profile } = useProfile();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CoverLetterResponse | null>(null);
  const [generationState, setGenerationState] = useState<GenerationState>({
    isGenerating: false,
    currentJobId: null,
    progress: 0,
    estimatedTime: 0,
  });

  // Fetch available templates
  const {
    data: templates = [],
    isLoading: templatesLoading,
  } = useQuery({
    queryKey: ["cover-letter-templates"],
    queryFn: async () => {
      return await apiGet<CoverLetterTemplate[]>("ai/cover-letters/templates");
    },
    staleTime: 30 * 60 * 1000, // 30 minutes
  });

  // Fetch user's generated cover letters
  const {
    data: generatedLetters = [],
    isLoading: lettersLoading,
    refetch: refetchLetters,
  } = useQuery({
    queryKey: ["cover-letters"],
    queryFn: async () => {
      return await apiGet<GeneratedCoverLetter[]>("ai/cover-letters");
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Legacy generate function for backward compatibility
  const generate = async (profileData: UserProfile, job: JobPosting, tone: string = "professional") => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiPost<CoverLetterResponse>("ai/generate-cover-letter", {
        profile: profileData,
        job,
        tone,
      });
      setResult(data);
      return data;
    } catch (error) {
      const err = error as Error;
      console.error(err);
      setError(err.message || "Failed to generate cover letter");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Enhanced generation with AI
  const generateCoverLetter = useCallback(async (
    request: CoverLetterGenerationRequest
  ): Promise<GeneratedCoverLetter | null> => {
    if (!profile) {
      console.error("Cannot generate cover letter: no user profile");
      return null;
    }

    setGenerationState({
      isGenerating: true,
      currentJobId: request.job_id,
      progress: 0,
      estimatedTime: 30, // 30 seconds estimate
    });
    setError(null);

    // Start progress simulation
    const progressInterval = setInterval(() => {
      setGenerationState(prev => {
        if (prev.progress >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return { ...prev, progress: prev.progress + 10 };
      });
    }, 300);

    try {
      const enhancedRequest = {
        ...request,
        profile_context: {
          preferences: profile.preferences,
          resume_url: profile.resume_url,
          contact: profile.contact,
          headline: profile.headline,
          bio: profile.bio,
        },
        optimization_settings: {
          include_keywords: true,
          match_company_culture: true,
          highlight_relevant_experience: true,
          address_job_requirements: true,
        },
      };

      const result = await apiPost<GeneratedCoverLetter>("ai/cover-letters/generate", enhancedRequest);

      clearInterval(progressInterval);
      setGenerationState({
        isGenerating: false,
        currentJobId: null,
        progress: 100,
        estimatedTime: 0,
      });

      // Update cache
      queryClient.setQueryData(
        ["cover-letters"],
        (oldLetters: GeneratedCoverLetter[] | undefined) =>
          oldLetters ? [result, ...oldLetters] : [result]
      );

      return result;
    } catch (error) {
      clearInterval(progressInterval);
      const message = error instanceof Error ? error.message : "Failed to generate cover letter";
      console.error("Failed to generate cover letter:", error);
      setError(message);
      setGenerationState({
        isGenerating: false,
        currentJobId: null,
        progress: 0,
        estimatedTime: 0,
      });
      return null;
    }
  }, [profile, queryClient]);

  // Get best template for job category
  const getRecommendedTemplate = useCallback((
    jobTitle: string,
    jobDescription: string
  ): CoverLetterTemplate | null => {
    if (!templates.length) return null;

    // Simple keyword matching for template recommendation
    const keywords = {
      technical: ["engineer", "developer", "programmer", "technical", "software"],
      executive: ["manager", "director", "vp", "executive", "lead", "head"],
      creative: ["designer", "artist", "creative", "writer", "content"],
      professional: ["analyst", "specialist", "coordinator", "associate", "professional"],
      entry: ["junior", "entry", "intern", "trainee", "graduate"]
    };

    const text = (jobTitle + " " + jobDescription).toLowerCase();

    for (const [category, words] of Object.entries(keywords)) {
      if (words.some(word => text.includes(word))) {
        const template = templates.find(t => t.category === category && t.is_default);
        if (template) return template;
      }
    }

    // Return default professional template
    return templates.find(t => t.is_default) || templates[0] || null;
  }, [templates]);

  // Get cover letters for a specific job
  const getLettersForJob = useCallback((jobId: string): GeneratedCoverLetter[] => {
    return generatedLetters.filter(letter => letter.job_id === jobId);
  }, [generatedLetters]);

  // Get generation progress
  const getGenerationProgress = useCallback((jobId: string) => {
    if (generationState.currentJobId === jobId) {
      return {
        isGenerating: generationState.isGenerating,
        progress: generationState.progress,
        estimatedTime: generationState.estimatedTime,
      };
    }
    return {
      isGenerating: false,
      progress: 0,
      estimatedTime: 0,
    };
  }, [generationState]);

  // Reset hook state
  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setGenerationState({
      isGenerating: false,
      currentJobId: null,
      progress: 0,
      estimatedTime: 0,
    });
  }, []);

  return {
    // Legacy API
    generate,
    reset,
    loading,
    error,
    result,

    // Enhanced API
    templates,
    generatedLetters,
    generateCoverLetter,
    getRecommendedTemplate,
    getLettersForJob,
    getGenerationProgress,
    refetchLetters,
    generationState,

    // Loading states
    isLoading: {
      templates: templatesLoading,
      letters: lettersLoading,
      generation: generationState.isGenerating,
    },
  };
}
