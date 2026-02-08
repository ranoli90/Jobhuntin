import { useState, useEffect, useCallback } from "react";
import { apiGet, apiPatch, apiPostFormData } from "../lib/api";

export interface Preferences {
  location?: string;
  role_type?: string;
  salary_min?: number;
  remote_only?: boolean;
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
  avatar_url?: string;
  resume_url?: string;
}

interface UploadResumeResponse {
  resume_url: string;
  parsed_profile?: any;
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
    const formData = new FormData();
    formData.append("file", file); // Backend expects "file" from UploadFile = File(...)
    const data = await apiPostFormData<UploadResumeResponse>("profile/resume", formData);
    setProfile((prev) => {
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
  };

  const uploadAvatar = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const data = await apiPostFormData<{ avatar_url: string }>("profile/avatar", formData);
    setProfile((prev) => (prev ? { ...prev, contact: { ...prev.contact, avatar_url: data.avatar_url } } : prev));
    return data.avatar_url;
  };

  const savePreferences = async (preferences: Preferences | undefined) => {
    return updateProfile({ preferences });
  };

  const completeOnboarding = async () => {
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
    needsOnboarding: !loading && (!profile || !profile.has_completed_onboarding),
  };
}
