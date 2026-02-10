/**
 * useAISuggestions - Hook for fetching AI-powered suggestions during onboarding
 * 
 * Provides role suggestions, salary estimates, and location recommendations
 * based on the user's parsed resume profile.
 */

import { useState, useCallback } from "react";
import { apiPost } from "../lib/api";

// Response types matching backend contracts
export interface RoleSuggestion {
    suggested_roles: string[];
    primary_role: string;
    experience_level: string;
    confidence: number;
    reasoning: string;
}

export interface SalarySuggestion {
    min_salary: number;
    max_salary: number;
    market_median: number;
    currency: string;
    confidence: number;
    factors: string[];
    reasoning: string;
}

export interface LocationSuggestion {
    suggested_locations: string[];
    remote_friendly_score: number;
    top_markets: string[];
    reasoning: string;
}

export interface JobMatchScore {
    score: number;
    skill_match: number;
    experience_match: number;
    location_match: number;
    culture_signals: string[];
    red_flags: string[];
    summary: string;
}

interface AIState<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
}

export function useAISuggestions() {
    const [roles, setRoles] = useState<AIState<RoleSuggestion>>({
        data: null,
        loading: false,
        error: null,
    });

    const [salary, setSalary] = useState<AIState<SalarySuggestion>>({
        data: null,
        loading: false,
        error: null,
    });

    const [locations, setLocations] = useState<AIState<LocationSuggestion>>({
        data: null,
        loading: false,
        error: null,
    });

    /**
     * Fetch role suggestions based on parsed profile
     */
    const suggestRoles = useCallback(async (profile: Record<string, unknown>) => {
        setRoles({ data: null, loading: true, error: null });
        try {
            const result = await apiPost<RoleSuggestion>("ai/suggest-roles", { profile });
            setRoles({ data: result, loading: false, error: null });
            return result;
        } catch (err) {
            const message = err instanceof Error ? err.message : "Failed to get role suggestions";
            setRoles({ data: null, loading: false, error: message });
            return null;
        }
    }, []);

    /**
     * Fetch salary estimate based on profile, role, and location
     */
    const suggestSalary = useCallback(async (
        profile: Record<string, unknown>,
        targetRole: string,
        location = "Remote"
    ) => {
        setSalary({ data: null, loading: true, error: null });
        try {
            const result = await apiPost<SalarySuggestion>("ai/suggest-salary", {
                profile,
                target_role: targetRole,
                location,
            });
            setSalary({ data: result, loading: false, error: null });
            return result;
        } catch (err) {
            const message = err instanceof Error ? err.message : "Failed to get salary suggestion";
            setSalary({ data: null, loading: false, error: message });
            return null;
        }
    }, []);

    /**
     * Fetch location recommendations based on profile
     */
    const suggestLocations = useCallback(async (
        profile: Record<string, unknown>,
        currentLocation = ""
    ) => {
        setLocations({ data: null, loading: true, error: null });
        try {
            const result = await apiPost<LocationSuggestion>("ai/suggest-locations", {
                profile,
                current_location: currentLocation,
            });
            setLocations({ data: result, loading: false, error: null });
            return result;
        } catch (err) {
            const message = err instanceof Error ? err.message : "Failed to get location suggestions";
            setLocations({ data: null, loading: false, error: message });
            return null;
        }
    }, []);

    /**
     * Score a single job against the user's profile
     */
    const scoreJob = useCallback(async (
        profile: Record<string, unknown>,
        job: Record<string, unknown>
    ): Promise<JobMatchScore | null> => {
        try {
            return await apiPost<JobMatchScore>("ai/match-job", { profile, job });
        } catch {
            return null;
        }
    }, []);

    /**
     * Score multiple jobs in batch (max 20)
     */
    const scoreJobsBatch = useCallback(async (
        profile: Record<string, unknown>,
        jobs: Record<string, unknown>[]
    ): Promise<{ matches: JobMatchScore[]; errors: string[] }> => {
        try {
            return await apiPost<{ matches: JobMatchScore[]; errors: string[] }>(
                "ai/match-jobs-batch",
                { profile, jobs }
            );
        } catch {
            return { matches: [], errors: ["Batch scoring failed"] };
        }
    }, []);

    /**
     * Fetch all suggestions at once after resume upload
     */
    const fetchAllSuggestions = useCallback(async (
        profile: Record<string, unknown>,
        currentLocation = ""
    ) => {
        // Fetch in parallel for speed
        const [rolesResult, locationsResult] = await Promise.all([
            suggestRoles(profile),
            suggestLocations(profile, currentLocation),
        ]);

        // Fetch salary after we have a role suggestion
        let salaryResult = null;
        if (rolesResult?.primary_role) {
            salaryResult = await suggestSalary(
                profile,
                rolesResult.primary_role,
                locationsResult?.suggested_locations?.[0] || currentLocation || "Remote"
            );
        }

        return {
            roles: rolesResult,
            locations: locationsResult,
            salary: salaryResult,
        };
    }, [suggestRoles, suggestLocations, suggestSalary]);

    const isLoading = roles.loading || salary.loading || locations.loading;
    const hasAnyData = roles.data || salary.data || locations.data;

    return {
        // Role suggestions
        roles,
        suggestRoles,

        // Salary suggestions
        salary,
        suggestSalary,

        // Location suggestions
        locations,
        suggestLocations,

        // Job matching
        scoreJob,
        scoreJobsBatch,

        // Convenience methods
        fetchAllSuggestions,
        isLoading,
        hasAnyData,

        // Reset all states
        reset: useCallback(() => {
            setRoles({ data: null, loading: false, error: null });
            setSalary({ data: null, loading: false, error: null });
            setLocations({ data: null, loading: false, error: null });
        }, []),
    };
}
