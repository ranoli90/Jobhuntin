import * as React from "react";
import { MapPin, Briefcase, DollarSign, FileText, Upload } from "lucide-react";
import { useProfile } from "../hooks/useProfile";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { pushToast } from "../lib/toast";

export default function Settings() {
  const { profile, loading, updateProfile, uploadResume } = useProfile();
  const [preferences, setPreferences] = React.useState({
    location: "",
    role_type: "",
    salary_min: "",
    remote_only: false,
  });
  const [isSaving, setIsSaving] = React.useState(false);
  const [isUploading, setIsUploading] = React.useState(false);

  React.useEffect(() => {
    if (profile?.preferences) {
      const p = profile.preferences;
      setPreferences({
        location: p.location ?? "",
        role_type: p.role_type ?? "",
        salary_min: p.salary_min ? String(p.salary_min) : "",
        remote_only: p.remote_only ?? false,
      });
    }
  }, [profile?.preferences]);

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await updateProfile({
        preferences: {
          location: preferences.location || undefined,
          role_type: preferences.role_type || undefined,
          salary_min: preferences.salary_min ? Number(preferences.salary_min) : undefined,
          remote_only: preferences.remote_only,
        },
      });
      pushToast({ title: "Preferences saved", tone: "success" });
    } catch (err) {
      pushToast({ title: "Could not save", description: (err as Error).message, tone: "error" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.match(/\.(pdf|doc|docx)$/i)) {
      pushToast({ title: "Please upload a PDF or Word document", tone: "error" });
      return;
    }
    setIsUploading(true);
    try {
      await uploadResume(file);
      pushToast({ title: "Resume updated", tone: "success" });
    } catch (err) {
      pushToast({ title: "Upload failed", description: (err as Error).message, tone: "error" });
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner label="Loading settings…" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">Settings</p>
        <h1 className="font-display text-4xl">Profile & preferences</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card tone="shell" shadow="lift" className="p-6">
          <div className="flex items-center gap-2 mb-6">
            <FileText className="h-5 w-5 text-brand-ink" />
            <h2 className="font-display text-xl">Resume</h2>
          </div>
          {profile?.resume_url ? (
            <p className="text-sm text-brand-ink/70 mb-4">
              You have a resume on file. Upload a new one to replace it.
            </p>
          ) : (
            <p className="text-sm text-brand-ink/70 mb-4">
              Upload your resume so we can tailor applications for you.
            </p>
          )}
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-2xl border border-brand-ink/20 bg-white px-4 py-3 text-sm font-medium text-brand-ink hover:bg-brand-shell/50">
            <Upload className="h-4 w-4" />
            {isUploading ? "Uploading…" : "Upload new resume"}
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              className="hidden"
              onChange={handleResumeUpload}
              disabled={isUploading}
            />
          </label>
        </Card>

        <Card tone="shell" shadow="lift" className="p-6">
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
                value={preferences.salary_min}
                onChange={(e) => setPreferences((p) => ({ ...p, salary_min: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
            </div>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={preferences.remote_only}
                onChange={(e) => setPreferences((p) => ({ ...p, remote_only: e.target.checked }))}
                className="h-5 w-5 rounded border-brand-ink/20"
              />
              <span className="text-brand-ink">Remote only</span>
            </label>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? "Saving…" : "Save preferences"}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
