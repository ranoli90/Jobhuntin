import * as React from "react";
import { MapPin, Briefcase, DollarSign, FileText, Upload, Camera, Loader2, Download, Trash2, AlertTriangle, Ban, Tag, Moon, Sun, Shield, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useProfile } from "../hooks/useProfile";
import { t, getLocale } from "../lib/i18n";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ConfirmModal } from "../components/ui/ConfirmModal";
import { pushToast } from "../lib/toast";
import { getApiBase, getAuthHeaders } from "../lib/api";
import { telemetry } from "../lib/telemetry";
import { ThemeToggle } from "../components/ThemeToggle";

export default function Settings() {
  const navigate = useNavigate();
  const { profile, loading, updateProfile, uploadResume, uploadAvatar } = useProfile();
  const [preferences, setPreferences] = React.useState({
    location: "",
    role_type: "",
    salary_min: "",
    salary_max: "",
    remote_only: false,
    work_authorized: true,
    visa_sponsorship: false,
    excluded_companies: [] as string[],
    excluded_keywords: [] as string[],
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
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [showDeleteModal, setShowDeleteModal] = React.useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = React.useState('');
  const [showExportConfirm, setShowExportConfirm] = React.useState(false);

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
        excluded_companies: p.excluded_companies ?? [],
        excluded_keywords: p.excluded_keywords ?? [],
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
          excluded_companies: preferences.excluded_companies?.length ? preferences.excluded_companies : undefined,
          excluded_keywords: preferences.excluded_keywords?.length ? preferences.excluded_keywords : undefined,
        },
      });
      telemetry.track("preferences_saved", {});
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
      telemetry.track("profile_updated", {});
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
    const allowed =
      /\.(pdf|docx|doc)$/i.test(file.name || "") ||
      ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"].includes(file.type || "");
    if (!allowed) {
      pushToast({ title: "Please upload a PDF or Word (DOCX/DOC) document", tone: "error" });
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
      const apiErr = err as Error & { status?: number };
      const message = apiErr.message;
      const status = apiErr.status;
      if (import.meta.env.DEV) console.error("Resume upload failed:", err);
      pushToast({ title: "Upload failed", description: status ? `[${status}] ${message}` : message, tone: "error" });
      setResumeError(status ? `[${status}] ${message}` : message);
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE') {
      pushToast({ title: 'Please type "DELETE" to confirm account deletion', tone: 'error' });
      return;
    }

    setIsDeleting(true);
    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${getApiBase()}/user/delete-account`, {
        method: 'DELETE',
        headers: authHeaders,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete account');
      }

      const result = await response.json();
      
      // Track deletion event
      telemetry.track('Account Deleted', {
        success: true,
        email: profile?.email ? profile.email.replace(/(.{2}).+(@.+)/, '$1***$2') : 'unknown',
      });

      pushToast({ title: 'Account deletion initiated. You will receive a confirmation email shortly.', tone: 'success' });
      
      // Redirect to home after successful deletion request
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
      
    } catch (error) {
      const err = error as Error;
      if (import.meta.env.DEV) console.error('Account deletion failed:', err);
      
      telemetry.track('Account Deletion Failed', {
        error: err.message,
        email: profile?.email ? profile.email.replace(/(.{2}).+(@.+)/, '$1***$2') : 'unknown',
      });
      
      pushToast({ title: err.message || 'Failed to delete account. Please try again.', tone: 'error' });
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
      setDeleteConfirmation('');
    }
  };
  const handleExportData = () => {
    setShowExportConfirm(true);
  };

  const doExportData = async () => {
    setIsExporting(true);
    setShowExportConfirm(false);
    try {
      const base = getApiBase();
      const headers = await getAuthHeaders();
      const res = await fetch(`${base.replace(/\/$/, "")}/me/export`, {
        headers,
        credentials: "include",
      });
      if (!res.ok) throw new Error(res.statusText || "Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `jobhuntin-data-export-${new Date().toISOString().slice(0, 10)}.ndjson`;
      a.click();
      URL.revokeObjectURL(url);
      telemetry.track("data_exported", {});
      pushToast({ title: "Data exported successfully", tone: "success" });
    } catch (error) {
      const err = error as Error;
      if (import.meta.env.DEV) console.error("Export failed:", err);
      pushToast({ title: "Export failed", description: err.message, tone: "error" });
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

  const locale = getLocale();
  return (
    <div className="space-y-8 px-4 lg:px-0 pb-8">
      <div>
        <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">{t("settings.title", locale)}</p>
        <h1 className="font-display text-4xl">{t("settings.profilePreferences", locale)}</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card tone="shell" shadow="lift" className="p-6 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-brand-ink" />
                <h2 className="font-display text-xl">{t("settings.profileDetails", locale)}</h2>
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
                <label className="absolute -bottom-2 -right-2 inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-brand-ink text-white shadow" aria-label="Upload profile photo">
                  {isAvatarUploading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Camera className="h-4 w-4" aria-hidden />}
                  <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={handleAvatarUpload} disabled={isAvatarUploading} />
                </label>
              </div>
              <div>
                <p className="text-lg font-semibold text-brand-ink">{profile?.contact?.full_name || t("settings.addYourName", locale)}</p>
                <p className="text-sm text-brand-ink/60">{t("settings.recruiterHint", locale)}</p>
              </div>
            </div>

            <form onSubmit={handleProfileSave} className="space-y-4">
              <div>
                <label htmlFor="settings-full-name" className="mb-1 block text-sm font-medium text-brand-ink">{t("settings.fullName", locale)}</label>
                <input
                  id="settings-full-name"
                  type="text"
                  value={contactForm.full_name}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, full_name: e.target.value }))}
                  className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                />
              </div>
              <div>
                <label htmlFor="settings-headline" className="mb-1 block text-sm font-medium text-brand-ink">{t("settings.headline", locale)}</label>
                <input
                  id="settings-headline"
                  type="text"
                  placeholder={t("settings.headlinePlaceholder", locale)}
                  value={contactForm.headline}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, headline: e.target.value }))}
                  className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                />
              </div>
              <div>
                <label htmlFor="settings-bio" className="mb-1 block text-sm font-medium text-brand-ink">{t("settings.bio", locale)}</label>
                <textarea
                  id="settings-bio"
                  rows={4}
                  value={contactForm.bio}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, bio: e.target.value }))}
                  className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                  placeholder={t("settings.bioPlaceholder", locale)}
                />
              </div>
              <Button type="submit" disabled={isProfileSaving} className="w-full">
                {isProfileSaving ? t("settings.saving", locale) : t("settings.saveProfile", locale)}
              </Button>
            </form>
          </Card>

          <Card tone="shell" shadow="lift" className="p-6">
            <div className="flex items-center gap-2 mb-6">
              <FileText className="h-5 w-5 text-brand-ink" />
              <h2 className="font-display text-xl">{t("settings.resume", locale)}</h2>
            </div>
            {profile?.resume_url ? (
              <p className="text-sm text-brand-ink/70 mb-4">
                {t("settings.resumeOnFile", locale)}
              </p>
            ) : (
              <p className="text-sm text-brand-ink/70 mb-4">
                {t("settings.resumeUploadHint", locale)}
              </p>
            )}
            <div className="flex flex-col gap-3">
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-2xl border border-brand-ink/20 bg-white px-4 py-3 text-sm font-medium text-brand-ink hover:bg-brand-shell/50" aria-label={t("settings.uploadNewResume", locale) + " (PDF, max 15MB)"}>
                <Upload className="h-4 w-4" aria-hidden />
                {isUploading ? t("settings.uploading", locale) : t("settings.uploadNewResume", locale)}
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword"
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
            <h2 className="font-display text-xl">{t("settings.jobPreferences", locale)}</h2>
          </div>
          <form onSubmit={handleSavePreferences} className="space-y-4">
            <div>
              <label htmlFor="settings-location" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <MapPin className="h-4 w-4" aria-hidden /> {t("settings.location", locale)}
              </label>
              <input
                id="settings-location"
                type="text"
                placeholder={t("settings.locationPlaceholder", locale)}
                value={preferences.location}
                onChange={(e) => setPreferences((p) => ({ ...p, location: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
            </div>
            <div>
              <label htmlFor="settings-role-type" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <Briefcase className="h-4 w-4" aria-hidden /> {t("settings.roleType", locale)}
              </label>
              <input
                id="settings-role-type"
                type="text"
                placeholder={t("settings.rolePlaceholder", locale)}
                value={preferences.role_type}
                onChange={(e) => setPreferences((p) => ({ ...p, role_type: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
            </div>
            <div>
              <label htmlFor="settings-salary-min" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <DollarSign className="h-4 w-4" aria-hidden /> {t("settings.minSalary", locale)}
              </label>
              <input
                id="settings-salary-min"
                type="number"
                placeholder="e.g. 100000"
                min="0"
                max="10000000"
                inputMode="numeric"
                value={preferences.salary_min}
                onChange={(e) => setPreferences((p) => ({ ...p, salary_min: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
              <p className="text-xs text-brand-ink/50 mt-1">{t("settings.salaryHint", locale)}</p>
            </div>
            <div>
              <label htmlFor="settings-salary-max" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <DollarSign className="h-4 w-4" aria-hidden /> {t("settings.maxSalary", locale)}
              </label>
              <input
                id="settings-salary-max"
                type="number"
                placeholder="e.g. 200000"
                min="0"
                max="10000000"
                inputMode="numeric"
                value={preferences.salary_max}
                onChange={(e) => setPreferences((p) => ({ ...p, salary_max: e.target.value }))}
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
              <p className="text-xs text-brand-ink/50 mt-1">{t("settings.salaryHint", locale)}</p>
            </div>
            <div className="space-y-3">
              {[
                { key: 'remote_only' as const, labelKey: 'settings.remoteOnly' as const, descKey: 'settings.remoteOnlyDesc' as const },
                { key: 'work_authorized' as const, labelKey: 'settings.workAuthorized' as const, descKey: 'settings.workAuthorizedDesc' as const },
                { key: 'visa_sponsorship' as const, labelKey: 'settings.visaSponsorship' as const, descKey: 'settings.visaSponsorshipDesc' as const },
              ].map(({ key, labelKey, descKey }) => (
                <div key={key} className="space-y-1">
                  <button
                    type="button"
                    role="switch"
                    aria-checked={preferences[key]}
                    aria-label={`${t(labelKey, locale)}: ${t(descKey, locale)}. ${preferences[key] ? "On" : "Off"}`}
                    onClick={() => setPreferences((p) => ({ ...p, [key]: !p[key] }))}
                    className={`flex items-center justify-between w-full rounded-2xl border px-4 py-3 transition-all ${preferences[key]
                      ? "bg-brand-primary/10 border-brand-primary/20 text-brand-primary"
                      : "bg-white border-brand-ink/10 text-brand-ink"
                      }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="sr-only">, {t(preferences[key] ? "settings.toggleOn" : "settings.toggleOff", locale)}</span>
                    <span className="text-sm font-semibold">{t(labelKey, locale)}</span>
                      <span className="text-xs text-brand-ink/60">{t(descKey, locale)}</span>
                    </div>
                    <span
                      className={`inline-flex h-6 w-11 items-center rounded-full p-0.5 transition-all ${preferences[key] ? "bg-brand-primary" : "bg-brand-border"
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
            <div>
              <label htmlFor="settings-excluded-companies" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <Ban className="h-4 w-4" aria-hidden /> Excluded companies
              </label>
              <input
                id="settings-excluded-companies"
                type="text"
                placeholder="e.g. Acme Corp, Beta Inc (comma-separated)"
                value={preferences.excluded_companies?.join(", ") ?? ""}
                onChange={(e) =>
                  setPreferences((p) => ({
                    ...p,
                    excluded_companies: e.target.value.split(",").map((c) => c.trim()).filter(Boolean),
                  }))
                }
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
              <p className="text-xs text-brand-ink/50 mt-1">Companies to exclude from job matches</p>
            </div>
            <div>
              <label htmlFor="settings-excluded-keywords" className="mb-1.5 flex items-center gap-2 text-sm font-medium text-brand-ink">
                <Tag className="h-4 w-4" aria-hidden /> Excluded keywords
              </label>
              <input
                id="settings-excluded-keywords"
                type="text"
                placeholder="e.g. contract, freelance (comma-separated)"
                value={preferences.excluded_keywords?.join(", ") ?? ""}
                onChange={(e) =>
                  setPreferences((p) => ({
                    ...p,
                    excluded_keywords: e.target.value.split(",").map((k) => k.trim()).filter(Boolean),
                  }))
                }
                className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
              />
              <p className="text-xs text-brand-ink/50 mt-1">Keywords to exclude from job matches</p>
            </div>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? t("settings.saving", locale) : t("settings.savePreferences", locale)}
            </Button>
          </form>
        </Card>

        <Card tone="shell" shadow="lift" className="p-6">
          <h2 className="font-display text-xl mb-2 flex items-center gap-2">
            <Moon className="h-5 w-5" aria-hidden />
            {t("settings.appearance", locale) || "Appearance"}
          </h2>
          <p className="text-sm text-brand-ink/60 mb-4">
            {t("settings.themeDescription", locale) || "Choose light, dark, or system theme."}
          </p>
          <div className="flex items-center gap-3">
            <ThemeToggle className="text-brand-ink" />
            <span className="text-sm text-brand-ink/70">
              {t("settings.themeToggle", locale) || "Click to cycle: light → dark → system"}
            </span>
          </div>
        </Card>

        <Card tone="shell" shadow="lift" className="p-6">
          <h2 className="font-display text-xl mb-2 flex items-center gap-2">
            <Shield className="h-5 w-5" aria-hidden />
            Security
          </h2>
          <p className="text-sm text-brand-ink/60 mb-4">
            Manage your active sessions and sign out from devices you no longer use.
          </p>
          <Button variant="outline" onClick={() => navigate("/app/sessions")} className="flex items-center gap-2">
            <LogOut className="h-4 w-4" />
            Manage Sessions
          </Button>
        </Card>

        <Card tone="shell" shadow="lift" className="p-6">
          <h2 className="font-display text-xl mb-2">{t("settings.dataPrivacy", locale)}</h2>
          <p className="text-sm text-brand-ink/60 mb-4">
            {t("settings.exportDescription", locale)}{" "}
            <a href="/privacy" className="underline hover:text-brand-ink">{t("cookies.privacyPolicy", locale)}</a> {t("settings.exportForDetails", locale)}
          </p>
          <div className="space-y-3">
            <Button variant="outline" onClick={handleExportData} disabled={isExporting}>
              {isExporting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Download className="h-4 w-4" aria-hidden />}
              {isExporting ? t("settings.exporting", locale) : t("settings.exportData", locale)}
            </Button>
            
            <div className="border-t pt-4 mt-4">
              <h3 className="font-semibold text-red-900 mb-2 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Delete Account
              </h3>
              <p className="text-sm text-red-700 mb-4">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
              <Button 
                variant="outline" 
                onClick={() => setShowDeleteModal(true)}
                className="border-red-200 text-red-700 hover:bg-red-50 hover:border-red-300"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Account
              </Button>
            </div>
          </div>
        </Card>

        {/* Account Deletion Confirmation Modal */}
        <ConfirmModal
          isOpen={showDeleteModal}
          onClose={() => {
            setShowDeleteModal(false);
            setDeleteConfirmation('');
          }}
          onConfirm={handleDeleteAccount}
          title="Delete Account Permanently"
          description={
            <div className="space-y-4">
              <p>
                This action <strong>cannot be undone</strong>. Deleting your account will permanently remove:
              </p>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>Your profile information and preferences</li>
                <li>All job applications and swipe history</li>
                <li>Resume files and parsed data</li>
                <li>AI recommendations and personalization data</li>
              </ul>
              <p>
                To confirm deletion, please type <code className="bg-gray-100 px-2 py-1 rounded text-sm">DELETE</code> below:
              </p>
              <input
                type="text"
                value={deleteConfirmation}
                onChange={(e) => setDeleteConfirmation(e.target.value)}
                placeholder="Type DELETE to confirm"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                autoFocus
              />
              {deleteConfirmation && deleteConfirmation !== 'DELETE' && (
                <p className="text-sm text-red-600">
                  Please type exactly "DELETE" to confirm
                </p>
              )}
            </div>
          }
          confirmText="Delete Account Permanently"
          cancelText="Cancel"
          variant="danger"
          isLoading={isDeleting}
        />

        {/* Data Export Confirmation Modal - no password required (magic-link users don't have passwords) */}
        <ConfirmModal
          isOpen={showExportConfirm}
          onClose={() => setShowExportConfirm(false)}
          onConfirm={doExportData}
          title="Export Your Data"
          description="Are you sure you want to export your data? A file will be downloaded with your profile and application data."
          confirmText="Export"
          cancelText="Cancel"
          variant="info"
          isLoading={isExporting}
        />
      </div>
    </div>
  );
}
