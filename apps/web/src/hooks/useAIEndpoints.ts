import { useState, useCallback } from "react";
import { apiPost, apiPostFormData, apiGet } from "../lib/api";

export interface SemanticMatchRequest {
  profile: Record<string, unknown>;
  job: Record<string, unknown>;
  min_salary?: number;
  max_salary?: number;
  preferred_locations?: string[];
  remote_only?: boolean;
}

export interface SemanticMatchResponse {
  job_id: string;
  score: number;
  semantic_similarity: number;
  skill_match_ratio: number;
  experience_alignment: number;
  matched_skills: string[];
  missing_skills: string[];
  reasoning: string;
  confidence: "low" | "medium" | "high";
  passed_dealbreakers: boolean;
  dealbreaker_reasons: string[];
}

export interface BatchSemanticMatchRequest {
  profile: Record<string, unknown>;
  jobs: Record<string, unknown>[];
  dealbreakers?: {
    min_salary?: number;
    max_salary?: number;
    locations?: string[];
    remote_only?: boolean;
    onsite_only?: boolean;
    visa_sponsorship_required?: boolean;
    excluded_companies?: string[];
    excluded_keywords?: string[];
  };
}

export interface BatchSemanticMatchResult {
  job_id: string;
  score: number;
  explanation: {
    score: number;
    semantic_similarity: number;
    skill_match_ratio: number;
    experience_alignment: number;
    location_compatible: boolean;
    salary_in_range: boolean;
    matched_skills: string[];
    missing_skills: string[];
    reasoning: string;
    confidence: "low" | "medium" | "high";
  };
  passed_dealbreakers: boolean;
  dealbreaker_reasons: string[];
}

export interface BatchSemanticMatchResponse {
  results: BatchSemanticMatchResult[];
}

export interface TailorResumeRequest {
  profile: Record<string, unknown>;
  job: Record<string, unknown>;
  match_explanation?: Record<string, unknown>;
}

export interface TailorResumeResponse {
  original_summary: string;
  tailored_summary: string;
  highlighted_skills: string[];
  emphasized_experiences: Record<string, unknown>[];
  added_keywords: string[];
  ats_optimization_score: number;
  tailoring_confidence: string;
}

export interface ATSScoreRequest {
  resume_text: string;
  job_description: string;
}

export interface ATSScoreResponse {
  overall_score: number;
  metrics: Record<string, number>;
  recommendations: string[];
}

export interface CoverLetterGenerateRequest {
  job_id: string;
  template_id?: string;
  tone?: string;
  length?: string;
  focus_areas?: string[];
  custom_instructions?: string;
}

export interface CoverLetterGenerateResponse {
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

interface AIEndpointState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useSemanticMatch() {
  const [state, setState] = useState<AIEndpointState<SemanticMatchResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const match = useCallback(async (request: SemanticMatchRequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const result = await apiPost<SemanticMatchResponse>(
        "ai/semantic-match",
        request,
      );
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Semantic matching failed";
      setState({ data: null, loading: false, error: message });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    match,
    reset,
  };
}

export function useBatchSemanticMatch() {
  const [state, setState] = useState<
    AIEndpointState<BatchSemanticMatchResponse>
  >({
    data: null,
    loading: false,
    error: null,
  });

  const matchBatch = useCallback(async (request: BatchSemanticMatchRequest) => {
    if (request.jobs.length > 20) {
      const error = "Maximum 20 jobs per batch";
      setState({ data: null, loading: false, error });
      return null;
    }

    setState({ data: null, loading: true, error: null });
    try {
      const result = await apiPost<BatchSemanticMatchResponse>(
        "ai/semantic-match/batch",
        request,
      );
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Batch matching failed";
      setState({ data: null, loading: false, error: message });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    matchBatch,
    reset,
  };
}

export function useResumeTailor() {
  const [state, setState] = useState<AIEndpointState<TailorResumeResponse>>({
    data: null,
    loading: false,
    error: null,
  });
  const [progress, setProgress] = useState(0);

  const tailor = useCallback(async (request: TailorResumeRequest) => {
    setState({ data: null, loading: true, error: null });
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress((previous) => Math.min(previous + 10, 90));
    }, 200);

    try {
      const result = await apiPost<TailorResumeResponse>(
        "ai/tailor-resume",
        request,
      );
      clearInterval(progressInterval);
      setProgress(100);
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      clearInterval(progressInterval);
      setProgress(0);
      const message =
        error instanceof Error ? error.message : "Resume tailoring failed";
      setState({ data: null, loading: false, error: message });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
    setProgress(0);
  }, []);

  return {
    ...state,
    progress,
    tailor,
    reset,
  };
}

export function useATSScore() {
  const [state, setState] = useState<AIEndpointState<ATSScoreResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const score = useCallback(async (request: ATSScoreRequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const result = await apiPost<ATSScoreResponse>("ai/ats-score", request);
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "ATS scoring failed";
      setState({ data: null, loading: false, error: message });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    score,
    reset,
  };
}

export function useCoverLetterGenerate() {
  const [state, setState] = useState<
    AIEndpointState<CoverLetterGenerateResponse>
  >({
    data: null,
    loading: false,
    error: null,
  });

  const generate = useCallback(async (request: CoverLetterGenerateRequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const result = await apiPost<CoverLetterGenerateResponse>(
        "ai/cover-letters/generate",
        request,
      );
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Cover letter generation failed";
      setState({ data: null, loading: false, error: message });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    generate,
    reset,
  };
}

export function useAIEndpoints() {
  const semanticMatch = useSemanticMatch();
  const batchSemanticMatch = useBatchSemanticMatch();
  const resumeTailor = useResumeTailor();
  const atsScore = useATSScore();
  const coverLetterGenerate = useCoverLetterGenerate();

  const isLoading =
    semanticMatch.loading ||
    batchSemanticMatch.loading ||
    resumeTailor.loading ||
    atsScore.loading ||
    coverLetterGenerate.loading;

  return {
    semanticMatch,
    batchSemanticMatch,
    resumeTailor,
    atsScore,
    coverLetterGenerate,
    isLoading,
  };
}
