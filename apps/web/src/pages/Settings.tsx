import * as React from "react";
import { MapPin, Briefcase, DollarSign, FileText, Upload, Camera, Loader2, Download } from "lucide-react";
import { useProfile } from "../hooks/useProfile";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { pushToast } from "../lib/toast";
import { getApiBase, getAuthHeaders } from "../lib/api";
import { telemetry } from "../lib/telemetry";

export default function Settings() {
  const { profile, loading, updateProfile, uploadResume, uploadAvatar } = useProfile();
  const [preferences, setPreferences] = React.useState({
    location: "",
    role_type: "",
    salary_min: "",
    salary_max: "",
    remote_only: false,
    work_authorized: true,
    visa_sponsorship: false,
  });
  const [contactForm, setContactForm] = React.useState({
    full_name: "",
    headline: "",
    bio: "",
  });
  const [isSaving, setIsSaving] = React.useState(false);
  const [isUploading, setIsUploading] = React.useState(false);
  const [isProfileSaving, setIsProfileSaving] = React.useState(false);
  const [isAvatarUploading, setIsAvatarUploading] = React.useState(false);
  const [resumeError, setResumeError] = React.useState<string | null>(null);
  const [resumeSuccess, setResumeSuccess] = React.useState<string | null>(null);
  const [isExporting, setIsExporting] = React.useState(false);

  React.useEffect(() => {
    if (profile?.preferences) {
      const p = profile.preferences;
      setPreferences({
        location: p.location ?? "",
        role_type: p.role_type ?? "",
        salary_min: p.salary_min ? String(p.salary_min) : "",
        salary_max: p.salary_max ? String(p.salary_max) : "",
        remote_only: p.remote_only ?? false,
        work_authorized: p.work_authorized ?? true,
        visa_sponsorship: p.visa_sponsorship ?? false,
      });
    }
  }, [profile?.preferences]);

  React.useEffect(() => {
    setContactForm({
      full_name: profile?.contact?.full_name ?? "",
      headline: profile?.headline ?? "",
      bio: profile?.bio ?? "",
    });
  }, [profile?.contact?.full_name, profile?.headline, profile?.bio]);

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await updateProfile({
        preferences: {
          location: preferences.location || undefined,
          role_type: preferences.role_type || undefined,
          salary_min: preferences.salary_min ? Number(preferences.salary_min) : undefined,
          salary_max: preferences.salary_max ? Number(preferences.salary_max) : undefined,
          remote_only: preferences.remote_only,
          work_authorized: preferences.work_authorized,
          visa_sponsorship: preferences.visa_sponsorship,
        },
      });
      pushToast({ title: "Preferences saved", tone: "success" });
    } catch (err) {
      pushToast({ title: "Could not save", description: (err as Error).message, tone: "error" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProfileSaving(true);
    try {
      await updateProfile({
        full_name: contactForm.full_name || undefined,
        headline: contactForm.headline || undefined,
        bio: contactForm.bio || undefined,
      });
      pushToast({ title: "Profile updated", tone: "success" });
    } catch (err) {
      pushToast({ title: "Could not update profile", description: (err as Error).message, tone: "error" });
    } finally {
      setIsProfileSaving(false);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      pushToast({ title: "Please upload an image", tone: "error" });
      return;
    }
    const MAX_AVATAR_SIZE_MB = 5;
    if (file.size > MAX_AVATAR_SIZE_MB * 1024 * 1024) {
      pushToast({ title: `Image must be under ${MAX_AVATAR_SIZE_MB}MB`, tone: "error" });
      return;
    }
    setIsAvatarUploading(true);
    try {
      await uploadAvatar(file);
      pushToast({ title: "Photo updated", tone: "success" });
    } catch (err) {
      pushToast({ title: "Avatar upload failed", description: (err as Error).message, tone: "error" });
    } finally {
      setIsAvatarUploading(false);
      e.target.value = "";
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.match(/\.pdf$/i)) {
      pushToast({ title: "Please upload a PDF document", tone: "error" });
      return;
    }
    setIsUploading(true);
    setResumeError(null);
    setResumeSuccess(null);
    try {
      await uploadResume(file);
      pushToast({ title: "Resume updated", tone: "success" });
      setResumeSuccess("Resume uploaded successfully");
    } catch (err) {
      const message = (err as Error).message;
      const status = (err as any).status;
      console.error("Resume upload failed:", err);
      pushToast({ title: "Upload failed", description: status ? `[${status}] ${message}` : message, tone: "error" });
      setResumeError(status ? `[${status}] ${message}` : message);
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  const handleExportData = async () => {
    setIsExporting(true);
    try {
      const base = getApiBase();
      const headers = await getAuthHeaders();
      const res = await fetch(`${base.replace(/\/$/, "")}/me/export`, { headers, credentials: "include" });
      if (!res.ok) throw new Error(res.statusText || "Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `jobhuntin-data-export-${new Date().toISOString().slice(0, 10)}.ndjson`;
      a.click();
      URL.revokeObjectURL(url);
      telemetry.track("data_exported", {});
      pushToast({ title: "Data exported", tone: "success" });
    } catch (err) {
      pushToast({ title: "Export failed", description: (err as Error).message, tone: "error" });
    } finally {
      setIsExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-8 px-4 lg:px-0 pb-8" aria-busy="true" aria-label="Loading settings">
        <div className="space-y-2">
          <div className="h-4 w-24 bg-slate-200 rounded animate-pulse" />
          <div className="h-10 w-64 bg-slate-200 rounded animate-pulse" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-6">
            <div className="p-6 rounded-2xl border border-slate-200 bg-white animate-pulse">
              <div className="flex items-center justify-between mb-4">
                <div className="h-5 w-32 bg-slate-200 rounded" />
                <div className="h-4 w-40 bg-slate-100 rounded" />
              </div>
              <div className="flex items-center gap-4 mb-6">
                <div className="h-20 w-20 rounded-full bg-slate-200" />
                <div className="space-y-2 flex-1">
                  <div className="h-5 w-32 bg-slate-200 rounded" />
                  <div className="h-4 w-48 bg-slate-100 rounded" />
                </div>
              </div>
              <div className="space-y-4">
                <div className="h-12 w-full bg-slate-100 rounded-2xl" />
                <div className="h-12 w-full bg-slate-100 rounded-2xl" />
                <div className="h-24 w-full bg-slate-100 rounded-2xl" />
              </div>
            </div>
          </div>
          <div className="space-y-6">
            <div className="p-6 rounded-2xl border border-slate-200 bg-white animate-pulse">
              <div className="h-5 w-40 bg-slate-200 rounded mb-4" />
              <div className="space-y-4">
                <div className="h-12 w-full bg-slate-100 rounded-2xl" />
                <div className="h-12 w-full bg-slate-100 rounded-2xl" />
                <div className="h-12 w-1/2 bg-slate-100 rounded-2xl" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const avatarUrl = profile?.contact?.avatar_url;
  const initials = (profile?.contact?.full_name || profile?.email || "JH").slice(0, 2).toUpperCase();

  return (
    <div className="space-y-8 px-4 lg:px-0 pb-8">
      <div>
        <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">Settings</p>
        <h1 className="font-display text-4xl">Profile & preferences</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card tone="shell" shadow="lift" className="p-6 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-brand-ink" />
                <h2 className="font-display text-xl">Profile details</h2>
              </div>
              <span className="text-sm text-brand-ink/60">{profile?.email}</span>
            </div>
            <div className="flex items-center gap-4 mb-6">
              <div className="relative h-20 w-20">
                {avatarUrl ? (
                  <img src={avatarUrl} alt="User avatar" className="h-20 w-20 rounded-full object-cover" loading="lazy" />
                ) : (
                  <div className="h-20 w-20 rounded-full bg-brand-ink/10 text-brand-ink flex items-center justify-center text-xl font-semibold">
                    {initials}
                  </div>
                )}
                <label className="absolute -bottom-2 -right-2 inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-brand-ink text-white shadow">
                  {isAvatarUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
                  <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={handleAvatarUpload} disabled={isAvatarUploading} />
                </label>
              </div>
              <div>
                <p className="text-lg font-semibold text-brand-ink">{profile?.contact?.full_name || "Add your name"}</p>
                <p className="text-sm text-brand-ink/60">Make it easier for recruiters to recognize you.</p>
              </div>
            </div>

            <form onSubmit={handleProfileSave} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-brand-ink">Full name</label>
                <input
                  type="text"
                  value={contactForm.full_name}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, full_name: e.target.value }))}
                  className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-brand-ink">Headline</label>
                <input
                  type="text"
                  placeholder="e.g., Product Designer @ Stripe"
                  value={contactForm.headline}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, headline: e.target.value }))}
                  className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-brand-ink">Bio</label>
                <textarea
                  rows={4}
                  value={contactForm.bio}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, bio: e.target.value }))}
                  className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                  placeholder="Tell companies what makes you a standout candidate"
                />
              </div>
              <Button type="submit" disabled={isProfileSaving} className="w-full">
                {isProfileSaving ? "Saving…" : "Save profile"}
              </Button>
            </form>
          </Card>

          <Card tone="shell" shadow="lift" className="p-6">
            <div className="flex items-center gap-2 mb-6">
              <FileText className="h-5 w-5 text-brand-ink" />
              <h2 className="font-display text-xl">Resume</h2>
            </div>
            {profile?.resume_url ? (
              <p className="text-sm text-brand-ink/70 mb-4">
                You have a resume on file. Upload a new one to replace it or keep building your profile.
              </p>
            ) : (
              <p className="text-sm text-brand-ink/70 mb-4">
                Upload your resume so we can personalize applications.
              </p>
            )}
            <div className="flex flex-col gap-3">
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-2xl border border-brand-ink/20 bg-white px-4 py-3 text-sm font-medium text-brand-ink hover:bg-brand-shell/50">
                <Upload className="h-4 w-4" />
                {isUploading ? "Uploading…" : "Upload new resume"}
                <input
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleResumeUpload}
                  disabled={isUploading}
                />
              </label>
              {resumeSuccess && <p className="text-sm text-emerald-600">{resumeSuccess}</p>}
              {resumeError && <p className="text-sm text-red-500">{resumeError}</p>}
            </div>
          </Card>
        </div>

        <Card tone="shell" shadow="lift" className="p-6 space-y-4">
          <div className="flex items-center gap-2 mb-6">
            <Briefcase className="h-5 w-5 text-brand-ink" />
            <h2 className="font-display text-xl">Job preferences</h2>
          </div>
          <form onSubmit={handleSavePreferences} className="space-y-4">
            <div>
              <label className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <MapPin className="h-4 w-4" /> Location
              </label>
              <input
                type="text"
                placeholder="e.g. Remote, San Francisco"
                value={preferences.location}
                onChange={(e) => setPreferences((p) => ({ ...p, location: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
            </div>
            <div>
              <label className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <Briefcase className="h-4 w-4" /> Role type
              </label>
              <input
                type="text"
                placeholder="e.g. Product Designer, Software Engineer"
                value={preferences.role_type}
                onChange={(e) => setPreferences((p) => ({ ...p, role_type: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
            </div>
            <div>
              <label className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <DollarSign className="h-4 w-4" /> Min salary (optional)
              </label>
              <input
                type="number"
                placeholder="e.g. 100000"
                min="0"
                max="10000000"
                inputMode="numeric"
                value={preferences.salary_min}
                onChange={(e) => setPreferences((p) => ({ ...p, salary_min: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
              <p className="text-xs text-brand-ink/50 mt-1">Annual salary in USD</p>
            </div>
            <div>
              <label className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <DollarSign className="h-4 w-4" /> Max salary (optional)
              </label>
              <input
                type="number"
                placeholder="e.g. 200000"
                min="0"
                max="10000000"
                inputMode="numeric"
                value={preferences.salary_max}
                onChange={(e) => setPreferences((p) => ({ ...p, salary_max: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
              <p className="text-xs text-brand-ink/50 mt-1">Annual salary in USD</p>
            </div>
            <div className="space-y-3">
              {[
                { key: 'remote_only' as const, label: 'Remote only', desc: 'Prioritize remote-first roles' },
                { key: 'work_authorized' as const, label: 'Work authorized', desc: 'I am authorized to work in my target location' },
                { key: 'visa_sponsorship' as const, label: 'Need visa sponsorship', desc: 'Only show roles offering visa sponsorship' },
              ].map(({ key, label, desc }) => (
                <div key={key} className="space-y-1">
                  <button
                    type="button"
                    role="switch"
                    aria-checked={preferences[key]}
                    onClick={() => setPreferences((p) => ({ ...p, [key]: !p[key] }))}
                    className={`flex items-center justify-between w-full rounded-2xl border px-4 py-3 transition-all ${preferences[key]
                      ? "bg-primary-50 border-primary-200 text-primary-700"
                      : "bg-white border-brand-ink/10 text-brand-ink"
                      }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold">{label}</span>
                      <span className="text-xs text-brand-ink/60">{desc}</span>
                    </div>
                    <span
                      className={`inline-flex h-6 w-11 items-center rounded-full p-0.5 transition-all ${preferences[key] ? "bg-primary-500" : "bg-slate-200"
                        }`}
                    >
                      <span
                        className={`h-5 w-5 rounded-full bg-white shadow transition-transform ${preferences[key] ? "translate-x-5" : "translate-x-0"
                          }`}
                      />
                    </span>
                  </button>
                </div>
              ))}
            </div>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? "Saving…" : "Save preferences"}
            </Button>
          </form>
        </Card>

        <Card tone="shell" shadow="lift" className="p-6">
          <h2 className="font-display text-xl mb-2">Data & privacy</h2>
          <p className="text-sm text-brand-ink/60 mb-4">
            Export your data (profile, applications, events) for portability. See our{" "}
            <a href="/privacy" className="underline hover:text-brand-ink">Privacy Policy</a> for details.
          </p>
          <Button variant="outline" onClick={handleExportData} disabled={isExporting}>
            {isExporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {isExporting ? "Exporting…" : "Export my data"}
          </Button>
        </Card>
      </div>
    </div>
  );
}
