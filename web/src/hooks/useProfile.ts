import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

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
        const resp = await fetch(`${API_BASE}/profile`, { credentials: "include" });
        if (!resp.ok) throw new Error("Failed to load profile");
        const data = (await resp.json()) as UserProfile;
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
    const resp = await fetch(`${API_BASE}/profile`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(updates),
    });
    if (!resp.ok) throw new Error("Failed to update profile");
    const updated = (await resp.json()) as UserProfile;
    setProfile(updated);
    return updated;
  };

  const uploadResume = async (file: File) => {
    const formData = new FormData();
    formData.append("resume", file);
    
    const resp = await fetch(`${API_BASE}/profile/resume`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!resp.ok) throw new Error("Failed to upload resume");
    const data = (await resp.json()) as { resume_url: string };
    setProfile((prev) => (prev ? { ...prev, resume_url: data.resume_url } : null));
    return data.resume_url;
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
