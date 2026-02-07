import { useState, useEffect } from "react";
import { apiGet, apiPatch, apiPostFormData } from "../lib/api";

export interface UserProfile {
  id: string;
  email: string;
  has_completed_onboarding: boolean;
  resume_url?: string;
  preferences?: {
    location?: string;
    role_type?: string;
    salary_min?: number;
    remote_only?: boolean;
  };
}

export function useProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiGet<UserProfile>("profile");
        setProfile(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const updateProfile = async (updates: Partial<UserProfile>) => {
    const updated = await apiPatch<UserProfile>("profile", updates);
    setProfile(updated);
    return updated;
  };

  const uploadResume = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file); // Backend expects "file" from UploadFile = File(...)
    const data = await apiPostFormData<{ resume_url: string; parsed_profile?: any }>("profile/resume", formData);
    setProfile((prev) => (prev ? { ...prev, resume_url: data.resume_url } : null));
    return data;
  };

  const savePreferences = async (preferences: UserProfile["preferences"]) => {
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
    savePreferences,
    completeOnboarding,
    needsOnboarding: !profile?.has_completed_onboarding && !loading,
  };
}
