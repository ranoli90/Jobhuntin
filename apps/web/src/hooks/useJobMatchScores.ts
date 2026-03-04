/**
 * useJobMatchScores - Hook for fetching AI-powered job match scores
 * 
 * Scores jobs against the user's profile using semantic matching.
 * Uses batch API for efficiency.
 * 
 * Features:
 * - Vector-based semantic similarity
 * - Skill match analysis
 * - Dealbreaker filtering
 * - Explainable match reasoning
 */

import { useState, useCallback, useRef } from "react";
import { apiPost } from "../lib/api";
import { pushToast } from "../lib/toast";
import type { JobPosting } from "./useJobs";

export interface MatchExplanation {
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
}

export interface JobMatchScore {
    job_id: string;
    score: number;
    explanation: MatchExplanation;
    passed_dealbreakers: boolean;
    dealbreaker_reasons: string[];
}

export interface DealbreakerPreferences {
    min_salary?: number;
    max_salary?: number;
    locations?: string[];
    remote_only?: boolean;
    onsite_only?: boolean;
    visa_sponsorship_required?: boolean;
    excluded_companies?: string[];
    excluded_keywords?: string[];
}

interface ScoreCache {
    [jobId: string]: JobMatchScore;
}

export function useJobMatchScores() {
    const [scores, setScores] = useState<ScoreCache>({});
    const [loading, setLoading] = useState<Set<string>>(new Set());
    const [error, setError] = useState<string | null>(null);
    const profileRef = useRef<Record<string, unknown> | null>(null);
    const dealbreakersRef = useRef<DealbreakerPreferences | null>(null);
    const scoresRef = useRef<ScoreCache>({});
    const loadingRef = useRef<Set<string>>(new Set());

    scoresRef.current = scores;
    loadingRef.current = loading;

    const setProfile = useCallback((profile: Record<string, unknown>) => {
        profileRef.current = profile;
    }, []);

    const setDealbreakers = useCallback((dealbreakers: DealbreakerPreferences) => {
        dealbreakersRef.current = dealbreakers;
    }, []);

    const scoreJobs = useCallback(async (jobs: JobPosting[]) => {
        if (!profileRef.current) {
            if (import.meta.env.DEV) console.warn("No profile set for job scoring");
            return;
        }

        const currentScores = scoresRef.current;
        const currentLoading = loadingRef.current;

        const unscored = jobs.filter(job => !currentScores[job.id] && !currentLoading.has(job.id));
        if (unscored.length === 0) return;

        setLoading(prev => {
            const next = new Set(prev);
            unscored.forEach(job => next.add(job.id));
            return next;
        });

        try {
            const jobsPayload = unscored.slice(0, 20).map(job => ({
                id: job.id,
                title: job.title,
                company: job.company,
                description: job.description,
                location: job.location,
                salary_min: job.salary_min,
                salary_max: job.salary_max,
                requirements: job.requirements,
            }));

            const response = await apiPost<{ results: JobMatchScore[] }>(
                "ai/semantic-match/batch",
                {
                    profile: profileRef.current,
                    jobs: jobsPayload,
                    dealbreakers: dealbreakersRef.current || {},
                }
            );

            setScores(prev => {
                const next = { ...prev };
                response.results.forEach((result) => {
                    next[result.job_id] = result;
                });
                return next;
            });

            setError(null);
        } catch (err) {
            const message = err instanceof Error ? err.message : "Failed to score jobs";
            setError(message);
            pushToast({
                title: "AI Scoring Failed",
                description: message,
                tone: "error",
            });
        } finally {
            setLoading(prev => {
                const next = new Set(prev);
                unscored.forEach(job => next.delete(job.id));
                return next;
            });
        }
    }, []);

    const scoreSingleJob = useCallback(async (
        job: JobPosting,
        profile: Record<string, unknown>,
        dealbreakers?: DealbreakerPreferences
    ): Promise<JobMatchScore | null> => {
        try {
            const response = await apiPost<JobMatchScore>(
                "ai/semantic-match",
                {
                    profile,
                    jobs: [{
                        id: job.id,
                        title: job.title,
                        company: job.company,
                        description: job.description,
                        location: job.location,
                        salary_min: job.salary_min,
                        salary_max: job.salary_max,
                    }],
                    dealbreakers: dealbreakers || {},
                }
            );
            return response;
        } catch {
            return null;
        }
    }, []);

    const getScore = useCallback((jobId: string): JobMatchScore | undefined => {
        return scores[jobId];
    }, [scores]);

    const isScoring = useCallback((jobId: string): boolean => {
        return loading.has(jobId);
    }, [loading]);

    const clearScores = useCallback(() => {
        setScores({});
        setLoading(new Set());
        setError(null);
    }, []);

    return {
        scores,
        scoreJobs,
        scoreSingleJob,
        getScore,
        isScoring,
        setProfile,
        setDealbreakers,
        clearScores,
        error,
        hasScores: Object.keys(scores).length > 0,
    };
}

export function getScoreColor(score: number): string {
    if (score >= 80) return "text-emerald-600 bg-emerald-50 border-emerald-200";
    if (score >= 60) return "text-amber-600 bg-amber-50 border-amber-200";
    return "text-slate-600 bg-slate-50 border-slate-200";
}

export function getScoreLabel(score: number): string {
    if (score >= 90) return "Excellent Match";
    if (score >= 80) return "Great Match";
    if (score >= 70) return "Good Match";
    if (score >= 60) return "Fair Match";
    return "Low Match";
}

export function getConfidenceColor(confidence: "low" | "medium" | "high"): string {
    switch (confidence) {
        case "high": return "text-emerald-600";
        case "medium": return "text-amber-600";
        case "low": return "text-slate-500";
    }
}
