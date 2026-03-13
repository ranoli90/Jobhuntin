import { useQuery, useMutation } from "@tanstack/react-query";
import { apiPost, apiGet } from "../lib/api";
import { pushToast } from "../lib/toast";

// ===================================================================
// Types
// ===================================================================

export interface SkillGapItem {
  skill_name: string;
  category: string;
  skill_type: string;
  demand_score: number;
  priority: "high" | "medium" | "low";
  missing: boolean;
  proficiency_gap: number;
  estimated_learning_weeks: number;
  related_skills: string[];
  description: string;
  resources: Array<{
    type: string;
    name: string;
    provider: string;
  }>;
}

export interface SkillGapAnalysis {
  target_role: string;
  current_skills: string[];
  required_skills: string[];
  matched_skills: string[];
  missing_skills: string[];
  gap_score: number;
  skill_gaps: SkillGapItem[];
  category_breakdown: Record<
    string,
    {
      matched: string[];
      missing: string[];
      total: number;
      match_rate: number;
    }
  >;
  recommendations: SkillRecommendation[];
  market_insights: {
    role_demand_growth: number;
    experience_level: string;
    total_job_postings_estimate: number;
    competition_level: string;
  };
}

export interface SkillRecommendation {
  skill: string;
  category: string;
  skill_type: string;
  priority: string;
  priority_weight: number;
  demand_score: number;
  estimated_learning_weeks: number;
  description: string;
  related_skills: string[];
  resources: Array<{
    type: string;
    name: string;
    provider: string;
  }>;
  reason: string;
}

export interface TargetRole {
  id: string;
  name: string;
  required_skills_count: number;
  preferred_skills_count: number;
  experience_level: string;
  demand_growth: number;
}

export interface SkillGapRequest {
  current_skills: string[];
  target_role: string;
  user_proficiency_levels?: Record<string, string>;
}

export interface SkillRecommendationRequest {
  current_skills: string[];
  target_role: string;
  limit?: number;
}

export interface SkillRecommendationResponse {
  target_role: string;
  recommendations: SkillRecommendation[];
  total_missing: number;
  estimated_total_learning_weeks: number;
}

export interface TargetRolesResponse {
  roles: TargetRole[];
}

// ===================================================================
// API Functions
// ===================================================================

async function fetchSkillGapAnalysis(
  request: SkillGapRequest
): Promise<SkillGapAnalysis> {
  return apiPost<SkillGapAnalysis>("/skill-gap/analyze", request);
}

async function fetchSkillRecommendations(
  request: SkillRecommendationRequest
): Promise<SkillRecommendationResponse> {
  return apiPost<SkillRecommendationResponse>("/skill-gap/recommendations", request);
}

async function fetchTargetRoles(): Promise<TargetRolesResponse> {
  return apiGet<TargetRolesResponse>("/skill-gap/roles");
}

// ===================================================================
// Hooks
// ===================================================================

/**
 * Hook for analyzing skill gaps between user skills and target role requirements.
 */
export function useSkillGapAnalysis(request: SkillGapRequest) {
  return useQuery({
    queryKey: ["skillGapAnalysis", request.target_role, request.current_skills],
    queryFn: () => fetchSkillGapAnalysis(request),
    enabled: request.current_skills.length > 0 && !!request.target_role,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook for getting personalized skill recommendations.
 */
export function useSkillRecommendations(request: SkillRecommendationRequest) {
  return useQuery({
    queryKey: [
      "skillRecommendations",
      request.target_role,
      request.current_skills,
      request.limit,
    ],
    queryFn: () => fetchSkillRecommendations(request),
    enabled: request.current_skills.length > 0 && !!request.target_role,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook for getting available target roles.
 */
export function useTargetRoles() {
  return useQuery({
    queryKey: ["targetRoles"],
    queryFn: fetchTargetRoles,
    staleTime: 30 * 60 * 1000, // 30 minutes - roles don't change often
  });
}

/**
 * Hook for analyzing skill gaps with mutation support (for when you want to trigger analysis manually).
 */
export function useSkillGapAnalysisMutation() {
  return useMutation({
    mutationFn: fetchSkillGapAnalysis,
    onSuccess: () => {
      pushToast({
        title: "Analysis complete",
        description: "Your skill gap analysis is ready",
        tone: "success",
      });
    },
    onError: (error: Error) => {
      pushToast({
        title: "Analysis failed",
        description: error.message || "Please try again",
        tone: "error",
      });
    },
  });
}

/**
 * Hook for getting skill recommendations with mutation support.
 */
export function useSkillRecommendationsMutation() {
  return useMutation({
    mutationFn: fetchSkillRecommendations,
    onSuccess: () => {
      pushToast({
        title: "Recommendations ready",
        description: "Here are your personalized skill recommendations",
        tone: "success",
      });
    },
    onError: (error: Error) => {
      pushToast({
        title: "Failed to get recommendations",
        description: error.message || "Please try again",
        tone: "error",
      });
    },
  });
}

// ===================================================================
// Utility Functions
// ===================================================================

/**
 * Calculate the overall readiness score based on gap analysis.
 */
export function calculateReadinessScore(analysis: SkillGapAnalysis): number {
  return Math.round(analysis.gap_score * 100);
}

/**
 * Get a human-readable readiness level.
 */
export function getReadinessLevel(gapScore: number): string {
  if (gapScore >= 0.8) return "Highly Ready";
  if (gapScore >= 0.6) return "Mostly Ready";
  if (gapScore >= 0.4) return "Partially Ready";
  if (gapScore >= 0.2) return "Needs Development";
  return "Significant Gap";
}

/**
 * Get color class based on priority.
 */
export function getPriorityColor(priority: string): string {
  switch (priority) {
    case "high":
      return "text-red-600 bg-red-50 border-red-200";
    case "medium":
      return "text-yellow-600 bg-yellow-50 border-yellow-200";
    case "low":
      return "text-green-600 bg-green-50 border-green-200";
    default:
      return "text-gray-600 bg-gray-50 border-gray-200";
  }
}

/**
 * Format estimated learning time.
 */
export function formatLearningTime(weeks: number): string {
  if (weeks < 1) {
    return "Less than a week";
  }
  if (weeks === 1) {
    return "1 week";
  }
  if (weeks < 4) {
    return `${Math.round(weeks)} weeks`;
  }
  const months = Math.round(weeks / 4);
  if (months === 1) {
    return "1 month";
  }
  return `${months} months`;
}

/**
 * Group recommendations by category.
 */
export function groupRecommendationsByCategory(
  recommendations: SkillRecommendation[]
): Record<string, SkillRecommendation[]> {
  return recommendations.reduce(
    (acc, rec) => {
      const category = rec.category;
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(rec);
      return acc;
    },
    {} as Record<string, SkillRecommendation[]>
  );
}
