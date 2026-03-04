import { useState, useEffect, useCallback } from "react";
import { apiGet, apiPatch, apiPostFormData } from "../lib/api";

export interface Preferences {
  location?: string;
  role_type?: string;
  salary_min?: number;
  salary_max?: number;
  remote_only?: boolean;
  hybrid_acceptable?: boolean;
  onsite_only?: boolean;
  work_authorized?: boolean;
  visa_sponsorship?: boolean;
  excluded_companies?: string[];
  excluded_keywords?: string[];
}

export interface ContactInfo {
  full_name?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  location?: string;
  avatar_url?: string;
  linkedin_url?: string;
  portfolio_url?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  has_completed_onboarding: boolean;
  resume_url?: string;
  preferences?: Preferences;
  contact?: ContactInfo;
  headline?: string;
  bio?: string;
}

export interface ProfileUpdatePayload {
  full_name?: string;
  headline?: string;
  bio?: string;
  has_completed_onboarding?: boolean;
  preferences?: Preferences;
  contact?: ContactInfo;
  avatar_url?: string;
  resume_url?: string;
}

interface ParsedProfile {
  title?: string;
  headline?: string;
  // V2 parser returns nested skills object; V1 returns flat string[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  skills?: any; // { technical?: (string | RichSkill)[], soft?: string[] } | string[]
  experience?: Array<{
    title: string;
    company: string;
    duration: string;
    highlights: string[];
  }>;
  education?: Array<{
    degree: string;
    institution: string;
    year?: string;
  }>;
  summary?: string;
  years_experience?: number;
  // Allow additional fields from API
  [key: string]: unknown;
}

interface UploadResumeResponse {
  resume_url: string;
  parsed_profile?: ParsedProfile;
  contact?: ContactInfo;
  preferences?: Preferences;
}

export function useProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshProfile = useCallback(async () => {
    try {
      const data = await apiGet<UserProfile>("profile");
      setProfile(data);
      setError(null);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      // Don't throw here, just set error/profile to null so UI can decide what to do
      setProfile(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;

    const initProfile = async () => {
      try {
        await refreshProfile();
      } catch (err) {
        if (mounted) {
          console.error("Failed to load profile:", err);
        }
      }
    };

    initProfile();

    return () => {
      mounted = false;
    };
  }, [refreshProfile]);

  const updateProfile = async (updates: ProfileUpdatePayload) => {
    const updated = await apiPatch<UserProfile>("profile", updates);
    setProfile(updated);
    return updated;
  };

  const uploadResume = async (file: File): Promise<UploadResumeResponse> => {
    if (!file) {
      throw new Error("Please select a file to upload.");
    }

    const maxBytes = 15_728_640; // 15 MB to match backend
    const isPdf = (file.type || "").toLowerCase() === "application/pdf";

    if (file.size === 0) {
      throw new Error("File appears empty or corrupted.");
    }
    if (file.size > maxBytes) {
      throw new Error("File too large. Maximum size is 15 MB.");
    }
    if (!isPdf) {
      throw new Error("Only PDF files are accepted.");
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // Increased timeout to 2 minutes for parsing

    try {
      const formData = new FormData();
      formData.append("file", file); // Backend expects "file" from UploadFile = File(...)
      const data = await apiPostFormData<UploadResumeResponse>("profile/resume", formData, {
        signal: controller.signal
      });
      setProfile((prev: UserProfile | null) => {
        // If prev is null, we can't fully reconstruct it without ID/email, 
        // but we can start building it if the backend returned enough info.
        // However, usually uploadResume is called when we are already authenticated.
        // We'll rely on refreshProfile if prev is null.
        if (!prev) return prev;
        return {
          ...prev,
          resume_url: data.resume_url,
          preferences: data.preferences ?? prev.preferences,
          contact: {
            ...prev.contact,
            ...(data.contact ?? {}),
          },
        };
      });
      // If we didn't have a profile before, refresh to get the full object
      if (!profile) {
        await refreshProfile();
      }
      return data;
    } catch (error) {
      const err = error as Error & { status?: number };
      if (err.name === "AbortError") {
        throw new Error("Upload timed out. Please check your connection and try again.");
      }

      // Provide more specific error messages based on status
      if (err.status) {
        switch (err.status) {
          case 413:
            throw new Error("File too large. Maximum size is 15 MB.");
          case 429:
            throw new Error("Too many upload attempts. Please wait a moment and try again.");
          case 500:
            throw new Error("Server error during upload. Please try again.");
          case 502:
            throw new Error("Resume parsing service unavailable. Please try again in a few minutes.");
          case 503:
            throw new Error("Service temporarily unavailable. Please try again.");
          default:
            throw err;
        }
      }

      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  };

  const uploadAvatar = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const data = await apiPostFormData<{ avatar_url: string }>("profile/avatar", formData);
    setProfile((prev: UserProfile | null) =>
      prev ? { ...prev, contact: { ...prev.contact, avatar_url: data.avatar_url } } : prev
    );
    return data.avatar_url;
  };

  const savePreferences = async (preferences: Preferences | undefined) => {
    return updateProfile({ preferences });
  };

  const completeOnboarding = async () => {
    const c = profile?.contact;
    const hasFirstName = c?.first_name?.trim();
    const hasLastName = c?.last_name?.trim();
    const hasEmail = c?.email?.trim() || profile?.email?.trim();

    if (!hasFirstName || !hasLastName) {
      throw new Error("Please provide your first and last name.");
    }
    if (!hasEmail) {
      throw new Error("Please provide your email address.");
    }
    return updateProfile({ has_completed_onboarding: true });
  };

  return {
    profile,
    loading,
    error,
    updateProfile,
    uploadResume,
    uploadAvatar,
    savePreferences,
    completeOnboarding,
    refreshProfile,
    // Force onboarding if profile is missing (new user) or explicitly not completed
    // Only force onboarding when we have a valid profile result (no error) and it is incomplete
    needsOnboarding: !loading && !error && (!profile || !profile.has_completed_onboarding),
  };
}
