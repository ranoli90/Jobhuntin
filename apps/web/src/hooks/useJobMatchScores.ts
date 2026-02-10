/**
 * useJobMatchScores - Hook for fetching AI-powered job match scores
 * 
 * Scores jobs against the user's profile and caches results.
 * Uses batch API for efficiency.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { apiPost } from "../lib/api";
import type { JobPosting } from "./useJobs";

export interface JobMatchScore {
    score: number;
    skill_match: number;
    experience_match: number;
    location_match: number;
    salary_match: number;
    culture_signals: string[];
    red_flags: string[];
    summary: string;
    confidence: number;
    reasoning: string;
}

interface ScoreCache {
    [jobId: string]: JobMatchScore;
}

export function useJobMatchScores() {
    const [scores, setScores] = useState<ScoreCache>({});
    const [loading, setLoading] = useState<Set<string>>(new Set());
    const [error, setError] = useState<string | null>(null);
    const profileRef = useRef<Record<string, unknown> | null>(null);
    const scoresRef = useRef<ScoreCache>({});
    const loadingRef = useRef<Set<string>>(new Set());

    // Keep refs in sync
    scoresRef.current = scores;
    loadingRef.current = loading;

    /**
     * Set the user profile for scoring
     */
    const setProfile = useCallback((profile: Record<string, unknown>) => {
        profileRef.current = profile;
    }, []);

    /**
     * Score a batch of jobs (max 20)
     */
    const scoreJobs = useCallback(async (jobs: JobPosting[]) => {
        if (!profileRef.current) {
            console.warn("No profile set for job scoring");
            return;
        }

        // Use refs to read current state without depending on it
        const currentScores = scoresRef.current;
        const currentLoading = loadingRef.current;

        // Filter out already scored jobs
        const unscored = jobs.filter(job => !currentScores[job.id] && !currentLoading.has(job.id));
        if (unscored.length === 0) return;

        // Mark as loading
        setLoading(prev => {
            const next = new Set(prev);
            unscored.forEach(job => next.add(job.id));
            return next;
        });

        try {
            const response = await apiPost<{ matches: JobMatchScore[]; errors: string[] }>(
                "ai/match-jobs-batch",
                {
                    profile: profileRef.current,
                    jobs: unscored.slice(0, 20).map(job => ({
                        id: job.id,
                        title: job.title,
                        company: job.company,
                        description: job.description,
                        location: job.location,
                        salary_min: job.salary_min,
                        salary_max: job.salary_max,
                        requirements: job.requirements,
                    })),
                }
            );

            // Update cache with new scores
            setScores(prev => {
                const next = { ...prev };
                response.matches.forEach((match, index) => {
                    if (unscored[index]) {
                        next[unscored[index].id] = match;
                    }
                });
                return next;
            });

            setError(null);

            if (response.errors.length > 0) {
                console.warn("Some jobs failed to score:", response.errors);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to score jobs");
        } finally {
            setLoading(prev => {
                const next = new Set(prev);
                unscored.forEach(job => next.delete(job.id));
                return next;
            });
        }
    }, []); // Stable reference — reads state through refs

    /**
     * Get the score for a specific job
     */
    const getScore = useCallback((jobId: string): JobMatchScore | undefined => {
        return scores[jobId];
    }, [scores]);

    /**
     * Check if a job is currently being scored
     */
    const isScoring = useCallback((jobId: string): boolean => {
        return loading.has(jobId);
    }, [loading]);

    /**
     * Clear all cached scores
     */
    const clearScores = useCallback(() => {
        setScores({});
        setLoading(new Set());
        setError(null);
    }, []);

    return {
        scores,
        scoreJobs,
        getScore,
        isScoring,
        setProfile,
        clearScores,
        error,
        hasScores: Object.keys(scores).length > 0,
    };
}

/**
 * Get a color class based on the match score
 */
export function getScoreColor(score: number): string {
    if (score >= 80) return "text-emerald-600 bg-emerald-50 border-emerald-200";
    if (score >= 60) return "text-amber-600 bg-amber-50 border-amber-200";
    return "text-slate-600 bg-slate-50 border-slate-200";
}

/**
 * Get a label for the score
 */
export function getScoreLabel(score: number): string {
    if (score >= 90) return "Excellent Match";
    if (score >= 80) return "Great Match";
    if (score >= 70) return "Good Match";
    if (score >= 60) return "Fair Match";
    return "Low Match";
}
