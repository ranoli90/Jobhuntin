import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Check, Upload, MapPin, Briefcase, DollarSign, Rocket, ArrowRight, ArrowLeft, FileText, CheckCircle2, Sparkles, User } from "lucide-react";
import { useOnboarding } from "../../hooks/useOnboarding";
import { useProfile } from "../../hooks/useProfile";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { pushToast } from "../../lib/toast";

export default function Onboarding() {
  const navigate = useNavigate();
  const { steps, currentStep, currentStepData, progress, isFirstStep, isLastStep, nextStep, prevStep, resetOnboarding } = useOnboarding();
  const { profile, loading, uploadResume, savePreferences, completeOnboarding } = useProfile();

  const [resumeFile, setResumeFile] = React.useState<File | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [resumeError, setResumeError] = React.useState<string | null>(null);
  const [preferences, setPreferences] = React.useState({
    location: "",
    role_type: "",
    salary_min: "",
    remote_only: false,
  });

  const [linkedinUrl, setLinkedinUrl] = React.useState("");
  const [parsedResume, setParsedResume] = React.useState<{ title?: string; skills?: string[]; years?: number; summary?: string; headline?: string } | null>(null);
  const [showParsingPreview, setShowParsingPreview] = React.useState(false);
  const [isSavingPreferences, setIsSavingPreferences] = React.useState(false);
  const [isCompleting, setIsCompleting] = React.useState(false);

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

  React.useEffect(() => {
    if (profile?.has_completed_onboarding) {
      resetOnboarding();
      navigate("/app/jobs");
    }
  }, [profile, navigate, resetOnboarding]);

  const handleResumeUpload = async () => {
    if (!resumeFile) return;
    setIsUploading(true);
    setResumeError(null);
    try {
      const data = await uploadResume(resumeFile);
      pushToast({ title: "Resume uploaded!", tone: "success" });

      if (data.parsed_profile) {
        const p = data.parsed_profile;
        setParsedResume({
          title: p.headline || (p.experience?.[0]?.title),
          skills: p.skills?.technical?.slice(0, 5) || [],
          years: p.experience?.length || 0,
          summary: p.summary,
          headline: p.headline,
        });
        setShowParsingPreview(true);
      }
    } catch (err) {
      const message = (err as Error).message;
      setResumeError(message);
      pushToast({ title: "Upload failed", description: message, tone: "error" });
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirmParsing = () => {
    setShowParsingPreview(false);
    nextStep();
  };

  const calculateCompleteness = () => {
    let score = 0;
    if (profile?.resume_url || resumeFile) score += 40;
    if (preferences.location) score += 20;
    if (preferences.role_type) score += 20;
    if (preferences.salary_min) score += 20;
    return score;
  };

  const completeness = calculateCompleteness();

  const handleSavePreferences = async () => {
    try {
      setIsSavingPreferences(true);
      await savePreferences({
        location: preferences.location || undefined,
        role_type: preferences.role_type || undefined,
        salary_min: preferences.salary_min ? Number(preferences.salary_min) : undefined,
        remote_only: preferences.remote_only,
      });
      nextStep();
    } catch (err) {
      pushToast({ title: "Something went sideways", description: "Your data is safe. Please try again.", tone: "error" });
    } finally {
      setIsSavingPreferences(false);
    }
  };

  const handleComplete = async () => {
    try {
      setIsCompleting(true);
      await completeOnboarding();
      resetOnboarding();
      pushToast({ title: "You're all set! Let's job hunt! 🚀", tone: "success" });
      navigate("/app/jobs");
    } catch (err) {
      pushToast({ title: "Almost there!", description: "Please try again.", tone: "error" });
    } finally {
      setIsCompleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Loading your profile..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Minimal Header */}
      <header className="px-6 h-20 flex items-center justify-between bg-white/80 backdrop-blur-xl border-b border-slate-200 sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-tr from-primary-500 to-primary-600 p-2 rounded-xl rotate-3 shadow-lg shadow-primary-500/20">
            <Bot className="text-white w-5 h-5" />
          </div>
          <span className="text-xl font-bold font-display text-slate-900 tracking-tight">JobHuntin</span>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="hidden sm:flex text-slate-500 border-slate-200">
            Secure Setup
          </Badge>
          <Button variant="ghost" size="sm" onClick={() => resetOnboarding()} className="text-slate-500 text-xs font-bold uppercase">
            Reset
          </Button>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12 md:py-20 bg-grid-premium opacity-100">
        <div className="w-full max-w-2xl relative">
          {/* Subtle background glow */}
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-primary-500/10 rounded-full blur-[100px] pointer-events-none" />
          <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-amber-500/10 rounded-full blur-[100px] pointer-events-none" />
          {/* Progress bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-900">
                Step {currentStep + 1} of {steps.length}
              </span>
              <span className="text-sm text-slate-500 font-medium">{currentStepData.title}</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-200">
              <div
                className="h-full rounded-full bg-primary-600 transition-all duration-500 shadow-sm"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <Card tone="glass" shadow="lift" className="p-8 border-slate-200/60">
            {/* Profile completeness indicator */}
            <div className="mb-8 rounded-2xl bg-emerald-50 border border-emerald-100 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-emerald-600" />
                  <span className="text-sm font-bold text-slate-900">Intelligence Profile</span>
                </div>
                <span className="text-sm font-black text-emerald-600">{completeness}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-white border border-emerald-100/50">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                  style={{ width: `${completeness}%` }}
                />
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {(profile?.resume_url || resumeFile) && (
                  <Badge className="text-[10px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-700 border-none">
                    <CheckCircle2 className="mr-1 h-3 w-3" />
                    Resume
                  </Badge>
                )}
                {preferences.location && (
                  <Badge className="text-[10px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-700 border-none">
                    <CheckCircle2 className="mr-1 h-3 w-3" />
                    Location
                  </Badge>
                )}
                {preferences.role_type && (
                  <Badge className="text-[10px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-700 border-none">
                    <CheckCircle2 className="mr-1 h-3 w-3" />
                    Role
                  </Badge>
                )}
                {preferences.salary_min && (
                  <Badge className="text-[10px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-700 border-none">
                    <CheckCircle2 className="mr-1 h-3 w-3" />
                    Salary
                  </Badge>
                )}
              </div>
            </div>

            {/* Step 1: Welcome */}
            {currentStep === 0 && (
              <div className="text-center">
                <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-[2rem] bg-slate-900 shadow-xl shadow-slate-200">
                  <Rocket className="h-10 w-10 text-primary-400" />
                </div>
                <h1 className="mb-4 font-display text-4xl font-black text-slate-900">
                  Welcome to Command.
                </h1>
                <p className="mb-8 text-slate-500 font-medium leading-relaxed">
                  We're going to calibrate your AI agent in just 2 minutes. Let's build your digital hunting twin.
                </p>
                <ul className="mb-8 space-y-4 text-left">
                  {[
                    "Upload resume for skill matching",
                    "Define your target salary & location",
                    "Activate autonomous job hunting",
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-4 text-slate-700 font-medium">
                      <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary-100 shadow-sm flex-shrink-0">
                        <Check className="h-3.5 w-3.5 text-primary-600 stroke-[3]" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>
                <Button size="lg" onClick={nextStep} className="w-full h-14 rounded-2xl text-lg font-bold shadow-xl shadow-primary-500/20 bg-primary-600 hover:bg-primary-500">
                  Begin Calibration
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            )}

            {/* Step 2: Resume Upload */}
            {currentStep === 1 && (
              <div>
                <div className="mb-8 flex items-center gap-4 border-b border-slate-100 pb-6">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-50 border border-primary-100 text-primary-600">
                    <Upload className="h-7 w-7" />
                  </div>
                  <div>
                    <h2 className="font-display text-2xl font-black text-slate-900">Input Data Source</h2>
                    <p className="text-sm text-slate-500 font-medium italic">We'll parse and map your experience in milliseconds.</p>
                  </div>
                </div>

                <div className="mb-8 rounded-[2rem] border-2 border-dashed border-slate-200 bg-slate-50/50 p-10 text-center hover:bg-slate-50 hover:border-primary-300 transition-all cursor-pointer group">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="resume-upload"
                  />
                  <label
                    htmlFor="resume-upload"
                    className="flex cursor-pointer flex-col items-center gap-4"
                  >
                    <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white shadow-md group-hover:scale-110 transition-transform">
                      <FileText className="h-10 w-10 text-primary-500" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-slate-900">
                        {resumeFile ? resumeFile.name : "Drop Resume Here"}
                      </p>
                      <p className="text-sm text-slate-400 font-medium">PDF or DOCX (max 5MB)</p>
                    </div>
                  </label>
                </div>

                <div className="mb-8">
                  <p className="mb-3 text-xs font-black text-slate-400 uppercase tracking-widest">Or Social Reference Filter</p>
                  <input
                    type="url"
                    placeholder="https://linkedin.com/in/yourname"
                    value={linkedinUrl}
                    onChange={(e) => setLinkedinUrl(e.target.value)}
                    className="w-full rounded-2xl border border-slate-200 bg-white px-5 py-4 text-slate-900 font-medium outline-none focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 transition-all shadow-sm"
                  />
                </div>

                {resumeError && (
                  <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-600 font-medium">
                    {resumeError}
                  </div>
                )}

                <div className="flex gap-4">
                  <Button variant="ghost" onClick={prevStep} className="flex-1 h-14 rounded-2xl font-bold text-slate-400 hover:text-slate-900 border border-slate-200">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back
                  </Button>
                  {resumeFile ? (
                    <Button
                      onClick={handleResumeUpload}
                      disabled={isUploading}
                      className="flex-[1.5] h-14 rounded-2xl font-bold bg-primary-600 hover:bg-primary-500 shadow-xl shadow-primary-500/20"
                    >
                      {isUploading ? <LoadingSpinner size="sm" /> : showParsingPreview ? "Update Source" : "Extract Experience"}
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      onClick={nextStep}
                      className="flex-[1.5] h-14 rounded-2xl font-bold text-slate-500 hover:border-slate-900 hover:text-slate-900"
                    >
                      Skip to manual entry
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  )}
                </div>

                {/* Resume Parsing Preview */}
                {showParsingPreview && parsedResume && (
                  <Card tone="lagoon" className="mt-8 p-6 rounded-[2rem] border-primary-100 bg-primary-50/30">
                    <div className="flex items-center gap-2 mb-4">
                      <Sparkles className="h-5 w-5 text-primary-600" />
                      <h3 className="font-black text-slate-900 text-lg">Parsed Intelligence:</h3>
                    </div>
                    <div className="space-y-4">
                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-sm">
                          <User className="h-4 w-4 text-primary-500" />
                        </div>
                        <div>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Inferred Title</p>
                          <p className="font-bold text-slate-900">{parsedResume.title}</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-sm">
                          <Briefcase className="h-4 w-4 text-primary-500" />
                        </div>
                        <div>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Experience Depth</p>
                          <p className="font-bold text-slate-900">{parsedResume.years} years</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-sm">
                          <CheckCircle2 className="h-4 w-4 text-primary-500" />
                        </div>
                        <div>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Extracted Stack</p>
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {parsedResume.skills?.map((skill) => (
                              <Badge key={skill} variant="outline" className="text-[10px] font-bold bg-white">{skill}</Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="primary"
                      className="w-full mt-6 h-12 rounded-xl font-bold"
                      onClick={handleConfirmParsing}
                    >
                      Confirm & Proceed
                    </Button>
                  </Card>
                )}
              </div>
            )}

            {/* Step 3: Preferences */}
            {currentStep === 2 && (
              <div className="space-y-8">
                <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-50 border border-amber-100 text-amber-600">
                    <MapPin className="h-7 w-7" />
                  </div>
                  <div>
                    <h2 className="font-display text-2xl font-black text-slate-900">Targeting Parameters</h2>
                    <p className="text-sm text-slate-500 font-medium italic">Define where the AI should hunt.</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="mb-3 flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-widest">
                      <MapPin className="h-3.5 w-3.5" />
                      Preferred Hub
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., San Francisco, Remote, London"
                      value={preferences.location}
                      onChange={(e) => setPreferences((p) => ({ ...p, location: e.target.value }))}
                      className="w-full rounded-2xl border border-slate-200 bg-white px-5 py-4 text-slate-900 font-medium outline-none focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 transition-all shadow-sm"
                    />
                  </div>

                  <div>
                    <label className="mb-3 flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-widest">
                      <Briefcase className="h-3.5 w-3.5" />
                      Role Classification
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Senior Fullstack Engineer"
                      value={preferences.role_type}
                      onChange={(e) => setPreferences((p) => ({ ...p, role_type: e.target.value }))}
                      className="w-full rounded-2xl border border-slate-200 bg-white px-5 py-4 text-slate-900 font-medium outline-none focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 transition-all shadow-sm"
                    />
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="mb-3 flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-widest">
                        <DollarSign className="h-3.5 w-3.5" />
                        Min Baseline Salary
                      </label>
                      <input
                        type="number"
                        placeholder="e.g., 140000"
                        value={preferences.salary_min}
                        onChange={(e) => setPreferences((p) => ({ ...p, salary_min: e.target.value }))}
                        className="w-full rounded-2xl border border-slate-200 bg-white px-5 py-4 text-slate-900 font-medium outline-none focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 transition-all shadow-sm"
                      />
                    </div>
                    <div className="flex flex-col justify-end">
                      <label className="flex items-center gap-3 p-4 rounded-2xl bg-slate-50 cursor-pointer border border-slate-100 hover:border-slate-200 transition-colors">
                        <input
                          type="checkbox"
                          checked={preferences.remote_only}
                          onChange={(e) => setPreferences((p) => ({ ...p, remote_only: e.target.checked }))}
                          className="h-5 w-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="text-sm font-bold text-slate-700 uppercase tracking-tight">Socially Remote Only</span>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4 pt-4">
                  <Button variant="ghost" onClick={prevStep} className="flex-1 h-14 rounded-2xl font-bold text-slate-400 hover:text-slate-900 border border-slate-200">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back
                  </Button>
                  <Button onClick={handleSavePreferences} className="flex-1 h-14 rounded-2xl font-bold bg-primary-600 hover:bg-primary-500 shadow-xl shadow-primary-500/20" disabled={isSavingPreferences}>
                    {isSavingPreferences ? <LoadingSpinner size="sm" /> : "Deploy Parameters"}
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </div>
              </div>
            )}

            {/* Step 4: Review & Ready! */}
            {currentStep === 3 && (
              <div className="text-center">
                <div className="mx-auto mb-8 flex h-24 w-24 items-center justify-center rounded-[2.5rem] bg-emerald-500 shadow-2xl shadow-emerald-200 animate-bounce">
                  <CheckCircle2 className="h-12 w-12 text-white" />
                </div>
                <h1 className="mb-4 font-display text-4xl font-black text-slate-900">
                  System Ready.
                </h1>
                <p className="mb-10 text-slate-500 font-medium max-w-sm mx-auto">
                  Calibration complete. Your digital double is primed for the market.
                </p>

                {/* Preferences Summary */}
                <div className="mb-10 grid gap-4 text-left">
                  <div className="p-6 rounded-[2rem] bg-slate-900 text-white relative overflow-hidden shadow-2xl">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-primary-500/20 rounded-full blur-3xl" />
                    <h3 className="mb-6 font-black text-primary-400 text-sm uppercase tracking-widest">Active Objectives:</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between border-b border-white/5 pb-3">
                        <span className="text-white/50 text-xs font-bold uppercase">AOI Location</span>
                        <span className="font-bold text-sm">{preferences.location || "Global"}</span>
                      </div>
                      <div className="flex items-center justify-between border-b border-white/5 pb-3">
                        <span className="text-white/50 text-xs font-bold uppercase">Role Target</span>
                        <span className="font-bold text-sm">{preferences.role_type || "Any High-Value"}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-white/50 text-xs font-bold uppercase">Comp Baseline</span>
                        <span className="font-bold text-sm">
                          {preferences.salary_min ? `$${(Number(preferences.salary_min) / 1000).toFixed(0)}k+` : "Premium Only"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="flex-1 p-4 rounded-2xl bg-emerald-50 border border-emerald-100 text-center">
                      <p className="text-[10px] uppercase font-black text-emerald-600 mb-1">Success Match</p>
                      <p className="text-2xl font-black text-emerald-700">98%</p>
                    </div>
                    <div className="flex-1 p-4 rounded-2xl bg-primary-50 border border-primary-100 text-center">
                      <p className="text-[10px] uppercase font-black text-primary-600 mb-1">Time to Deploy</p>
                      <p className="text-2xl font-black text-primary-700">&lt;2s</p>
                    </div>
                  </div>
                </div>

                <Button size="lg" variant="primary" onClick={handleComplete} className="w-full h-16 rounded-[1.5rem] text-xl font-black shadow-2xl shadow-primary-500/30 bg-primary-600 hover:bg-primary-500 group transition-all" disabled={isCompleting}>
                  {isCompleting ? <LoadingSpinner size="sm" /> : "LAUNCH COMMAND CENTER"}
                  <Rocket className="ml-3 h-6 w-6 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </Button>
              </div>
            )}
          </Card>

          {/* Helper text */}
          <p className="mt-8 text-center text-xs text-slate-400 font-medium">
            Step recorded at {new Date().toLocaleTimeString()} • Secured by 256-bit encryption
          </p>
        </div>
      </main>

      {/* Minimal Footer */}
      <footer className="px-6 py-8 border-t border-slate-200 bg-white">
        <div className="max-w-2xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-400 font-medium font-bold">© 2024 JobHuntin AI. Intelligence for Career Acceleration.</p>
          <div className="flex gap-6">
            <a href="/privacy" className="text-xs text-slate-400 hover:text-slate-900 font-bold uppercase transition-colors">Privacy</a>
            <a href="/terms" className="text-xs text-slate-400 hover:text-slate-900 font-bold uppercase transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
