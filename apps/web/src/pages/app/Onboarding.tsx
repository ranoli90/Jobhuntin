import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Check, Upload, MapPin, Briefcase, DollarSign, Rocket, ArrowRight, ArrowLeft, FileText, CheckCircle2, Sparkles, User, Zap, Mail, Phone, Shield, X } from "lucide-react";
import { Logo }

/* Safari CSS compatibility fix */
@supports (-webkit-backdrop-filter: none) {
  .backdrop-blur-xl {
    -webkit-backdrop-filter: blur(20px);
    backdrop-filter: blur(20px);
  }
}

/* Firefox compatibility fix */
@supports (not (-webkit-backdrop-filter: none)) {
  .backdrop-blur-xl {
    backdrop-filter: blur(20px);
  }
} from '../../components/brand/Logo';
import { useOnboarding } from "../../hooks/useOnboarding";
import { useProfile } from "../../hooks/useProfile";
import { useAISuggestions } from "../../hooks/useAISuggestions";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { AISuggestionCard, SalarySuggestionCard } from "../../components/ui/AISuggestionCard";
import { pushToast } from "../../lib/toast";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

export default function Onboarding() {
  const navigate = useNavigate();
  const { steps, currentStep, currentStepData, progress, isFirstStep, isLastStep, nextStep, prevStep, resetOnboarding } = useOnboarding();
  const { profile, loading, uploadResume, savePreferences, completeOnboarding, updateProfile } = useProfile();
  const aiSuggestions = useAISuggestions();
  const shouldReduceMotion = useReducedMotion();

  const [resumeFile, setResumeFile] = React.useState<File | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [resumeError, setResumeError] = React.useState<string | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const [preferences, setPreferences] = React.useState({
    location: "",
    role_type: "",
    salary_min: "",
    remote_only: false,
    work_authorized: true,
  });

  const [formErrors, setFormErrors] = React.useState<Record<string, string>>({});

  const [contactInfo, setContactInfo] = React.useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
  });
  const [isSavingContact, setIsSavingContact] = React.useState(false);

  const [linkedinUrl, setLinkedinUrl] = React.useState("");
  const [parsedResume, setParsedResume] = React.useState<{ title?: string; skills?: string[]; years?: number; summary?: string; headline?: string } | null>(null);
  const [showParsingPreview, setShowParsingPreview] = React.useState(false);
  const [isSavingPreferences, setIsSavingPreferences] = React.useState(false);
  const [isCompleting, setIsCompleting] = React.useState(false);
  const [parsedProfile, setParsedProfile] = React.useState<Record<string, unknown> | null>(null);

  React.useEffect(() => {
    if (profile?.preferences) {
      const p = profile.preferences;
      setPreferences({
        location: p.location ?? "",
        role_type: p.role_type ?? "",
        salary_min: p.salary_min ? String(p.salary_min) : "",
        remote_only: p.remote_only ?? false,
        work_authorized: p.work_authorized ?? true,
      });
    }
  }, [profile?.preferences]);

  // Pre-fill contact info from profile
  React.useEffect(() => {
    if (profile?.contact) {
      const c = profile.contact;
      setContactInfo(prev => ({
        first_name: prev.first_name || c.first_name || "",
        last_name: prev.last_name || c.last_name || "",
        email: prev.email || c.email || profile.email || "",
        phone: prev.phone || c.phone || "",
      }));
    }
  }, [profile?.contact, profile?.email]);

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

        // Store the full parsed profile for AI suggestions
        setParsedProfile(data.parsed_profile);

        // Fetch AI suggestions in background (don't block)
        aiSuggestions.fetchAllSuggestions(
          data.parsed_profile,
          data.preferences?.location || data.contact?.location || ""
        ).catch(() => {
          // Non-critical failure, just log
          console.log("AI suggestions fetch failed, will continue without");
        });
      }
    } catch (err) {
      const message = (err as Error).message;
      setResumeError(message);
      pushToast({
        title: "Upload stalled",
        description: message.includes("size") || message.includes("type")
          ? "Use PDF/DOC under 5MB, or try our sample resume to continue."
          : "Check your connection and retry. PDF/DOC under 5MB works best.",
        tone: "error"
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirmParsing = () => {
    setShowParsingPreview(false);
    nextStep();
  };

  const handleSaveContact = async () => {
    try {
      const errors: Record<string, string> = {};
      if (!contactInfo.first_name?.trim()) errors.first_name = "First name is required";
      if (!contactInfo.last_name?.trim()) errors.last_name = "Last name is required";
      const emailToUse = contactInfo.email || profile?.email;
      if (!emailToUse?.trim()) errors.email = "Email is required";
      setFormErrors(errors);
      if (Object.keys(errors).length) {
        throw new Error("Please fill required fields.");
      }

      setIsSavingContact(true);
      await updateProfile({
        contact: {
          ...profile?.contact,
          first_name: contactInfo.first_name,
          last_name: contactInfo.last_name,
          full_name: `${contactInfo.first_name} ${contactInfo.last_name}`.trim(),
          email: contactInfo.email,
          phone: contactInfo.phone,
          linkedin_url: linkedinUrl || profile?.contact?.linkedin_url || undefined,
        },
      });
      nextStep();
    } catch (err) {
      pushToast({ title: "Failed to save contact info", description: "Please try again.", tone: "error" });
    } finally {
      setIsSavingContact(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setResumeFile(e.dataTransfer.files[0]);
    }
  };

  const calculateCompleteness = () => {
    let score = 0;
    if (profile?.resume_url || resumeFile) score += 25;
    if (contactInfo.first_name && contactInfo.email) score += 25;
    if (preferences.location) score += 10;
    if (preferences.role_type) score += 15;
    if (preferences.salary_min) score += 15;
    if (preferences.work_authorized !== undefined) score += 10;
    return score;
  };

  const completeness = calculateCompleteness();

  const handleSavePreferences = async () => {
    try {
      const errors: Record<string, string> = {};
      if (!preferences.location?.trim()) errors.location = "Location is required";
      if (!preferences.role_type?.trim()) errors.role_type = "Role type is required";
      setFormErrors(errors);
      if (Object.keys(errors).length) {
        throw new Error("Please fill required fields.");
      }

      setIsSavingPreferences(true);
      await savePreferences({
        location: preferences.location || undefined,
        role_type: preferences.role_type || undefined,
        salary_min: preferences.salary_min ? Number(preferences.salary_min) : undefined,
        remote_only: preferences.remote_only,
        work_authorized: preferences.work_authorized,
      });

      // Update contact info separately if LinkedIn URL is provided
      if (linkedinUrl) {
        await updateProfile({
          contact: {
            linkedin_url: linkedinUrl,
            location: preferences.location || undefined,
          }
        });
      }
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
    <div className="h-[100dvh] w-full overflow-hidden bg-slate-50 flex flex-col relative">
      {/* Minimal Header */}
      <header className="px-3 md:px-6 h-11 md:h-12 shrink-0 flex items-center justify-between bg-white/80 backdrop-blur-xl border-b border-slate-200 z-50">
        <Logo to="/app/onboarding" size="sm" />
        <div className="flex items-center gap-2 md:gap-4">
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-50 border border-primary-100">
            <div className="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
            <span className="text-[10px] font-black text-primary-700 uppercase tracking-widest">AI Calibration Active</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => resetOnboarding()} className="text-slate-500 text-[10px] md:text-xs font-bold uppercase hover:bg-slate-100">
            Restart
          </Button>
        </div>
      </header>

      <main className="flex-1 w-full flex flex-col items-center justify-center p-1.5 md:p-4 overflow-hidden bg-grid-premium opacity-100 relative min-h-0">
        <div className="w-full max-w-xl lg:max-w-3xl h-full max-h-full flex flex-col relative justify-center min-h-0">
          {/* Subtle background glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary-500/5 rounded-full blur-[100px] pointer-events-none" />

          {/* Progress bar - Condensed */}
          <div className="mb-2 md:mb-6 shrink-0 z-10">
            <div className="flex items-center justify-between mb-1.5 md:mb-3 px-1">
              <span className="text-[10px] md:text-xs font-black text-slate-400 uppercase tracking-[0.15em] md:tracking-[0.2em]">
                Calibration Progress — {(progress).toFixed(0)}%
              </span>
              <span className="text-[10px] md:text-xs font-black text-primary-600 uppercase tracking-[0.15em] md:tracking-[0.2em]">{currentStepData.title}</span>
            </div>
            <div className="h-1 md:h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
              <motion.div
                initial={shouldReduceMotion ? { width: `${progress}%` } : { width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-primary-600 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
                transition={shouldReduceMotion ? undefined : { type: "spring", stiffness: 50, damping: 15 }}
              />
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              className="flex-1 min-h-0 flex flex-col"
              initial={shouldReduceMotion ? undefined : { opacity: 0, scale: 0.98, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={shouldReduceMotion ? undefined : { opacity: 0, scale: 0.98, y: -10 }}
              transition={shouldReduceMotion ? undefined : { duration: 0.3, ease: "easeOut" }}
            >
              <Card tone="glass" shadow="lift" className="flex flex-col flex-1 p-3 md:p-8 border-slate-200/60 overflow-hidden relative max-h-full min-h-0">
                {/* Decorative background elements inside card */}
                <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary-500/5 rounded-full blur-3xl pointer-events-none" />

                {/* Profile completeness indicator - Compact for mobile */}
                <div className="mb-2 md:mb-6 shrink-0 rounded-xl md:rounded-2xl bg-slate-900 border border-slate-800 p-2.5 md:p-4 shadow-xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl group-hover:bg-emerald-500/20 transition-colors" />
                  <div className="flex items-center justify-between mb-1.5 md:mb-3">
                    <div className="flex items-center gap-1.5 md:gap-2">
                      <div className="w-5 h-5 md:w-8 md:h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                        <Sparkles className="h-2.5 w-2.5 md:h-4 md:w-4 text-emerald-400" />
                      </div>
                      <div>
                        <span className="block text-[7px] md:text-[10px] font-black text-emerald-500/70 uppercase tracking-widest">Intelligence Profile</span>
                        <span className="text-[9px] md:text-xs font-bold text-white">System Confidence</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-base md:text-2xl font-black text-white italic">{completeness}%</span>
                    </div>
                  </div>
                  <div className="h-1 md:h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${completeness}%` }}
                      className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                      transition={{ type: "spring", stiffness: 40, damping: 12 }}
                    />
                  </div>
                  <div className="mt-1.5 md:mt-4 flex-wrap gap-1 md:gap-2 hidden md:flex">
                    {(profile?.resume_url || resumeFile) && (
                      <Badge className="text-[8px] md:text-[9px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-1.5 py-0.5 md:px-2 md:py-1">
                        <CheckCircle2 className="mr-1 h-2.5 w-2.5 md:h-3 md:w-3" />
                        Experience Mapped
                      </Badge>
                    )}
                    {preferences.location && (
                      <Badge className="text-[8px] md:text-[9px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-1.5 py-0.5 md:px-2 md:py-1">
                        <CheckCircle2 className="mr-1 h-2.5 w-2.5 md:h-3 md:w-3" />
                        Geospatial Set
                      </Badge>
                    )}
                    {preferences.role_type && (
                      <Badge className="text-[8px] md:text-[9px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-1.5 py-0.5 md:px-2 md:py-1">
                        <CheckCircle2 className="mr-1 h-2.5 w-2.5 md:h-3 md:w-3" />
                        Role Target Lock
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Step 1: Welcome - Scrollable Content */}
                {currentStep === 0 && (
                  <div className="flex flex-col h-full overflow-hidden">
                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                      <div className="text-center py-1 md:py-4">
                        <div className="mx-auto mb-3 md:mb-6 relative">
                          <motion.div
                            animate={shouldReduceMotion ? undefined : { rotate: 360 }}
                            transition={shouldReduceMotion ? undefined : { duration: 20, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-0 rounded-[2rem] border-2 border-dashed border-primary-500/20 hidden md:block"
                          />
                          <div className="relative mx-auto flex h-12 w-12 md:h-20 md:w-20 items-center justify-center rounded-[1.5rem] md:rounded-[2rem] bg-slate-900 shadow-2xl shadow-primary-500/20 scale-100">
                            <Rocket className="h-6 w-6 md:h-10 md:w-10 text-primary-400" />
                          </div>
                        </div>
                        <h1 className="mb-1 md:mb-3 font-display text-xl md:text-3xl font-black text-slate-900 tracking-tight leading-tight">
                          Initiate <span className="text-primary-600 italic">Hyper-Hunt.</span>
                        </h1>
                        <p className="mb-3 md:mb-8 text-slate-500 font-medium leading-relaxed max-w-sm mx-auto text-xs md:text-base">
                          We're about to build your digital autonomous twin. Calibration takes 90 seconds.
                        </p>
                        <div className="grid gap-1.5 md:gap-3 mb-3 md:mb-8 text-left">
                          {[
                            { title: "Skill Mapping", desc: "AI-driven resume vectorization", icon: Sparkles },
                            { title: "Radar Tuning", desc: "Location & salary baseline profiling", icon: MapPin },
                            { title: "Autonomous Launch", desc: "1-Click application engine activation", icon: Rocket },
                          ].map((item, i) => (
                            <motion.div
                              key={i}
                              initial={shouldReduceMotion ? undefined : { opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={shouldReduceMotion ? undefined : { delay: 0.2 + i * 0.1 }}
                              className="flex items-center gap-2.5 md:gap-4 p-2 md:p-4 rounded-xl md:rounded-2xl bg-slate-50 border border-slate-100/50 hover:bg-white hover:shadow-md transition-all group"
                            >
                              <div className="flex h-7 w-7 md:h-10 md:w-10 shrink-0 items-center justify-center rounded-lg md:rounded-xl bg-primary-100 text-primary-600 group-hover:bg-primary-600 group-hover:text-white transition-colors">
                                <item.icon className="h-3.5 w-3.5 md:h-5 md:w-5" />
                              </div>
                              <div className="text-left min-w-0">
                                <p className="text-[11px] md:text-sm font-black text-slate-900 uppercase tracking-tight truncate">{item.title}</p>
                                <p className="text-[9px] md:text-xs text-slate-500 font-medium truncate">{item.desc}</p>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="sticky bottom-0 pt-2 md:pt-4 shrink-0 mt-auto bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                      <Button size="lg" onClick={nextStep} className="w-full h-10 md:h-12 rounded-[1.25rem] text-base md:text-xl font-black shadow-xl md:shadow-2xl shadow-primary-500/30 bg-primary-600 hover:bg-primary-500 hover:scale-[1.02] transition-all group">
                        BEGIN CALIBRATION
                        <ArrowRight className="ml-3 h-5 w-5 md:h-6 md:w-6 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </div>
                  </div>
                )}

                {/* Step 2: Resume Upload */}
                {/* Step 2: Resume Upload */}
                {currentStep === 1 && (
                  <div className="flex flex-col h-full overflow-hidden">
                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                      <div className="mb-3 md:mb-8 flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6">
                        <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-primary-50 border border-primary-100 text-primary-600 shadow-inner">
                          <Upload className="h-4 w-4 md:h-8 md:w-8" />
                        </div>
                        <div className="min-w-0">
                          <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">Experience Input</h2>
                          <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">Feed the AI your career history for optimization.</p>
                        </div>
                      </div>

                      <div
                        className="mb-3 md:mb-8 relative group"
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                      >
                        <input
                          type="file"
                          accept=".pdf,.doc,.docx"
                          onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                          className="hidden"
                          id="resume-upload"
                          disabled={isUploading}
                        />
                        <label
                          htmlFor="resume-upload"
                          className={`flex cursor-pointer flex-col items-center gap-2 md:gap-6 rounded-[1.25rem] md:rounded-[2.5rem] border-3 border-dashed p-3 md:p-10 text-center transition-all duration-300 ${isDragging
                            ? "bg-primary-50 border-primary-500 scale-[1.02] shadow-xl"
                            : resumeFile
                              ? "bg-primary-50/50 border-primary-300"
                              : "bg-slate-50/50 border-slate-200 hover:bg-slate-50 hover:border-primary-300"
                            }`}
                        >
                          <div className={`flex h-10 w-10 md:h-20 md:w-20 items-center justify-center rounded-[0.75rem] md:rounded-[2rem] bg-white shadow-xl transition-all ${isUploading ? 'animate-pulse scale-90' : isDragging ? 'scale-110 rotate-12' : 'group-hover:scale-110 group-hover:rotate-3'}`}>
                            {isUploading ? (
                              <div className="relative">
                                <Sparkles className="h-5 w-5 md:h-10 md:w-10 text-primary-400 animate-spin-slow" />
                                <div className="absolute inset-0 flex items-center justify-center">
                                  <div className="w-2.5 h-2.5 md:w-5 md:h-5 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
                                </div>
                              </div>
                            ) : (
                              <FileText className={`h-5 w-5 md:h-10 md:w-10 ${resumeFile || isDragging ? 'text-primary-600' : 'text-slate-300'}`} />
                            )}
                          </div>
                          <div className="space-y-0.5 md:space-y-2">
                            <p className={`text-xs md:text-xl font-black ${resumeFile || isDragging ? 'text-primary-700' : 'text-slate-900'}`}>
                              {resumeFile ? resumeFile.name : isDragging ? "Drop to Analyze" : "Tap to Upload Resume"}
                            </p>
                            <p className="text-[9px] md:text-xs text-slate-400 font-bold uppercase tracking-widest leading-tight">PDF, DOCX — AI Optimization Ready</p>
                          </div>
                        </label>
                        {/* Clear file button */}
                        {resumeFile && !isUploading && (
                          <button
                            onClick={(e) => { e.preventDefault(); setResumeFile(null); setResumeError(null); setShowParsingPreview(false); }}
                            className="absolute top-2 right-2 md:top-3 md:right-3 w-6 h-6 md:w-7 md:h-7 rounded-full bg-slate-200 hover:bg-red-100 flex items-center justify-center transition-colors z-20"
                            title="Remove file"
                          >
                            <X className="h-3 w-3 md:h-4 md:w-4 text-slate-500 hover:text-red-500" />
                          </button>
                        )}
                        {isUploading && (
                          <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] rounded-[1.25rem] md:rounded-[2.5rem] flex flex-col items-center justify-center gap-3 z-10">
                            <div className="w-40 md:w-64 h-1.5 bg-slate-200 rounded-full overflow-hidden border border-slate-100 shadow-inner">
                              <motion.div
                                className="h-full bg-primary-500"
                                initial={shouldReduceMotion ? { width: "100%" } : { width: "0%" }}
                                animate={{ width: "100%" }}
                                transition={shouldReduceMotion ? undefined : { duration: 4, repeat: Infinity }}
                              />
                            </div>
                            <p className="text-[9px] md:text-xs font-black text-primary-600 uppercase tracking-widest animate-pulse">Scanning Vector Space...</p>
                          </div>
                        )}
                      </div>

                      <div className="mb-3 md:mb-10">
                        <div className="flex items-center gap-2 mb-1.5 md:mb-4 px-1">
                          <div className="h-[1px] flex-1 bg-slate-100" />
                          <span className="text-[9px] md:text-[10px] font-black text-slate-300 uppercase tracking-widest">or social reference</span>
                          <div className="h-[1px] flex-1 bg-slate-100" />
                        </div>
                        <div className="relative">
                          <Input
                            icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                            type="url"
                            placeholder="LinkedIn URL (optional)"
                            value={linkedinUrl}
                            onChange={(e) => setLinkedinUrl(e.target.value)}
                            className="bg-white shadow-sm text-sm"
                          />
                        </div>
                      </div>

                      {resumeError && (
                        <motion.div
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="mb-3 md:mb-8 rounded-xl md:rounded-2xl border border-red-200 bg-red-50 p-3 md:p-5 text-xs md:text-sm text-red-600 font-bold flex items-center gap-2 md:gap-3"
                        >
                          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0" />
                          <span className="flex-1 min-w-0 truncate">{resumeError}</span>
                        </motion.div>
                      )}
                    </div>

                    <div className="flex gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                      <Button variant="ghost" onClick={prevStep} className="h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4">
                        <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                        PREV
                      </Button>
                      {resumeFile && !resumeError ? (
                        <Button
                          onClick={handleResumeUpload}
                          disabled={isUploading}
                          className="flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black bg-primary-600 hover:bg-primary-500 shadow-2xl shadow-primary-500/30 text-xs md:text-lg group overflow-hidden relative"
                        >
                          <span className="relative z-10 flex items-center justify-center">
                            {isUploading ? <LoadingSpinner size="sm" /> : showParsingPreview ? "SYNC NEW SOURCE" : "EXTRACT EXPERIENCE"}
                            <ArrowRight className="ml-1.5 md:ml-3 h-4 w-4 md:h-6 md:w-6 group-hover:translate-x-1 transition-transform" />
                          </span>
                        </Button>
                      ) : (
                        <Button
                          variant={resumeError ? "primary" : "outline"}
                          onClick={nextStep}
                          className={`flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black transition-all text-xs md:text-lg truncate ${resumeError
                            ? "bg-primary-600 hover:bg-primary-500 shadow-xl shadow-primary-500/30 text-white"
                            : "text-slate-500 hover:border-slate-900 hover:text-slate-900 border-2 border-slate-200"
                            }`}
                        >
                          {resumeError ? "CONTINUE ANYWAY" : "SKIP TO MANUAL"}
                        </Button>
                      )}
                    </div>

                    {/* Resume Parsing Preview */}
                    <AnimatePresence>
                      {showParsingPreview && parsedResume && (
                        <motion.div
                          initial={{ opacity: 0, height: 0, y: 20 }}
                          animate={{ opacity: 1, height: 'auto', y: 0 }}
                          exit={{ opacity: 0, height: 0, y: 20 }}
                          className="overflow-hidden"
                        >
                          <Card className="mt-10 p-8 rounded-[2.5rem] border-primary-100 bg-primary-50/40 relative shadow-xl">
                            <div className="absolute top-4 right-4 bg-emerald-500 text-white text-[9px] font-black px-2 py-0.5 rounded uppercase tracking-widest">
                              98% Accuracy
                            </div>
                            <div className="flex items-center gap-3 mb-8">
                              <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center text-white shadow-lg shadow-primary-500/20">
                                <Sparkles className="h-6 w-6" />
                              </div>
                              <h3 className="font-black text-slate-900 text-xl tracking-tight">System Extraction Result:</h3>
                            </div>
                            <div className="grid gap-6">
                              <div className="flex items-start gap-4 p-4 rounded-2xl bg-white/80 border border-white shadow-sm">
                                <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-primary-500 shadow-inner">
                                  <User className="h-5 w-5" />
                                </div>
                                <div>
                                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Inferred Professional Title</p>
                                  <p className="font-black text-slate-900 text-lg">{parsedResume.title}</p>
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-start gap-4 p-4 rounded-2xl bg-white/80 border border-white shadow-sm">
                                  <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-primary-500 shadow-inner">
                                    <Briefcase className="h-5 w-5" />
                                  </div>
                                  <div>
                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Depth</p>
                                    <p className="font-black text-slate-900 text-lg">{parsedResume.years} Years</p>
                                  </div>
                                </div>
                                <div className="flex items-start gap-4 p-4 rounded-2xl bg-white/80 border border-white shadow-sm">
                                  <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-primary-500 shadow-inner">
                                    <Sparkles className="h-5 w-5" />
                                  </div>
                                  <div>
                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Core Stack</p>
                                    <p className="font-black text-slate-900 text-lg">{parsedResume.skills?.length || 0} Skills</p>
                                  </div>
                                </div>
                              </div>
                              <div className="p-4 rounded-2xl bg-white/80 border border-white shadow-sm">
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Extracted Competencies</p>
                                <div className="flex flex-wrap gap-2">
                                  {parsedResume.skills?.map((skill, i) => (
                                    <motion.div
                                      initial={{ opacity: 0, scale: 0.8 }}
                                      animate={{ opacity: 1, scale: 1 }}
                                      transition={{ delay: i * 0.05 }}
                                      key={skill}
                                    >
                                      <Badge variant="outline" className="text-[10px] font-black bg-white border-slate-100 text-slate-700 px-3 py-1 uppercase tracking-wider">{skill}</Badge>
                                    </motion.div>
                                  ))}
                                  {(!parsedResume.skills || parsedResume.skills.length === 0) && (
                                    <span className="text-xs text-slate-400 font-medium">Automatic extraction pending manual review...</span>
                                  )}
                                </div>
                              </div>
                            </div>
                            <Button
                              variant="primary"
                              className="w-full mt-10 h-12 rounded-[1.25rem] font-black text-lg bg-emerald-600 hover:bg-emerald-500 shadow-xl shadow-emerald-500/20"
                              onClick={handleConfirmParsing}
                            >
                              LOCK IN & PROCEED
                            </Button>
                          </Card>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Step 3: Confirm Contact */}
                {currentStep === 2 && (
                  <div className="flex flex-col h-full overflow-hidden">
                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                      <div className="mb-3 md:mb-8 flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6">
                        <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-emerald-50 border border-emerald-100 text-emerald-600 shadow-inner">
                          <User className="h-4 w-4 md:h-8 md:w-8" />
                        </div>
                        <div className="min-w-0">
                          <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">Verify Identity</h2>
                          <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">Confirm the details we extracted.</p>
                        </div>
                      </div>

                      <div className="grid gap-3 md:gap-6">
                        <div className="grid grid-cols-2 gap-2.5 md:gap-6">
                          <div>
                            <label className="mb-2 md:mb-3 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                              <div className="w-1 h-1 rounded-full bg-emerald-500" />
                              First Name <span className="text-red-400">*</span>
                            </label>
                            <div className="relative">
                              <Input
                                icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                                type="text"
                                placeholder="John"
                                value={contactInfo.first_name}
                                onChange={(e) => setContactInfo(c => ({ ...c, first_name: e.target.value }))}
                                className="bg-white shadow-sm text-sm"
                              />
                            </div>
                          </div>
                          <div>
                            <label className="mb-2 md:mb-3 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                              <div className="w-1 h-1 rounded-full bg-emerald-500" />
                              Last Name <span className="text-red-400">*</span>
                            </label>
                            <div className="relative">
                              <Input
                                icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                                type="text"
                                placeholder="Doe"
                                value={contactInfo.last_name}
                                onChange={(e) => setContactInfo(c => ({ ...c, last_name: e.target.value }))}
                                className="bg-white shadow-sm text-sm"
                              />
                            </div>
                          </div>
                        </div>

                        <div>
                          <label className="mb-2 md:mb-3 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                            <div className="w-1 h-1 rounded-full bg-emerald-500" />
                            Email Address <span className="text-red-400">*</span>
                          </label>
                          <div className="relative">
                            <Input
                              icon={<Mail className="h-4 w-4 md:h-5 md:w-5" />}
                              type="email"
                              placeholder="john@example.com"
                              value={contactInfo.email}
                              onChange={(e) => setContactInfo(c => ({ ...c, email: e.target.value }))}
                              className="bg-white shadow-sm text-sm"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="mb-2 md:mb-3 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                            <div className="w-1 h-1 rounded-full bg-emerald-500" />
                            Phone Number
                          </label>
                          <div className="relative">
                            <Input
                              icon={<Phone className="h-4 w-4 md:h-5 md:w-5" />}
                              type="tel"
                              placeholder="+1 (555) 123-4567"
                              value={contactInfo.phone}
                              onChange={(e) => setContactInfo(c => ({ ...c, phone: e.target.value }))}
                              className="bg-white shadow-sm text-sm"
                            />
                          </div>
                        </div>
                      </div>

                      {parsedResume && (
                        <div className="mt-3 md:mt-8 p-2.5 md:p-5 rounded-xl md:rounded-2xl bg-emerald-50 border border-emerald-100">
                          <div className="flex items-center gap-2 mb-1 md:mb-2">
                            <Sparkles className="h-3 w-3 md:h-4 md:w-4 text-emerald-600" />
                            <p className="text-[7px] md:text-[10px] font-black text-emerald-700 uppercase tracking-widest">AI-Extracted From Resume</p>
                          </div>
                          <p className="text-[10px] md:text-sm text-emerald-800 font-medium">We pre-filled these from your resume. Please verify details.</p>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                      <Button variant="ghost" onClick={prevStep} className="h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4">
                        <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                        PREV
                      </Button>
                      <Button
                        onClick={handleSaveContact}
                        disabled={!contactInfo.first_name || !contactInfo.email || isSavingContact}
                        className="flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black bg-emerald-600 hover:bg-emerald-500 shadow-2xl shadow-emerald-500/30 text-xs md:text-lg disabled:opacity-50 disabled:cursor-not-allowed group"
                      >
                        {isSavingContact ? <LoadingSpinner size="sm" /> : "CONFIRM IDENTITY"}
                        <ArrowRight className="ml-1.5 md:ml-3 h-4 w-4 md:h-6 md:w-6 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </div>
                  </div>
                )}

                {/* Step 4: Preferences */}
                {currentStep === 3 && (
                  <div className="flex flex-col h-full overflow-hidden">
                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                      <div className="flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6 mb-3 md:mb-8">
                        <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-amber-50 border border-amber-100 text-amber-600 shadow-inner">
                          <MapPin className="h-4 w-4 md:h-8 md:w-8" />
                        </div>
                        <div className="min-w-0">
                          <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">Active Parameters</h2>
                          <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">Define the geospatial and fiscal bounds.</p>
                        </div>
                      </div>

                      {/* AI Suggestions Section */}
                      {(aiSuggestions.roles.data || aiSuggestions.roles.loading || aiSuggestions.locations.data || aiSuggestions.locations.loading) && (
                        <div className="grid md:grid-cols-2 gap-2.5 md:gap-6 mb-3 md:mb-8">
                          {/* Role Suggestions */}
                          <AISuggestionCard
                            title="Suggested Roles"
                            subtitle="Based on your experience"
                            suggestions={aiSuggestions.roles.data?.suggested_roles || []}
                            confidence={aiSuggestions.roles.data?.confidence}
                            reasoning={aiSuggestions.roles.data?.reasoning}
                            loading={aiSuggestions.roles.loading}
                            error={aiSuggestions.roles.error}
                            onAccept={(role) => setPreferences(p => ({ ...p, role_type: role }))}
                            onReject={() => { }}
                          />

                          {/* Location Suggestions */}
                          <AISuggestionCard
                            title="Recommended Locations"
                            subtitle={aiSuggestions.locations.data?.remote_friendly_score
                              ? `${Math.round(aiSuggestions.locations.data.remote_friendly_score * 100)}% remote`
                              : "Based on your skills"
                            }
                            suggestions={aiSuggestions.locations.data?.suggested_locations || []}
                            confidence={aiSuggestions.locations.data?.remote_friendly_score}
                            reasoning={aiSuggestions.locations.data?.reasoning}
                            loading={aiSuggestions.locations.loading}
                            error={aiSuggestions.locations.error}
                            onAccept={(location) => setPreferences(p => ({ ...p, location }))}
                            onReject={() => { }}
                          />
                        </div>
                      )}

                      {/* Salary Suggestion */}
                      {(aiSuggestions.salary.data || aiSuggestions.salary.loading) && (
                        <div className="mb-3 md:mb-8">
                          <SalarySuggestionCard
                            minSalary={aiSuggestions.salary.data?.min_salary || 0}
                            maxSalary={aiSuggestions.salary.data?.max_salary || 0}
                            marketMedian={aiSuggestions.salary.data?.market_median || 0}
                            currency={aiSuggestions.salary.data?.currency}
                            confidence={aiSuggestions.salary.data?.confidence}
                            factors={aiSuggestions.salary.data?.factors}
                            reasoning={aiSuggestions.salary.data?.reasoning}
                            loading={aiSuggestions.salary.loading}
                            error={aiSuggestions.salary.error}
                            onAccept={(min) => setPreferences(p => ({ ...p, salary_min: String(min) }))}
                            onReject={() => { }}
                          />
                        </div>
                      )}

                      <div className="space-y-3 md:space-y-8">
                        <div className="grid gap-3 md:gap-8">
                          <div>
                            <label className="mb-2 md:mb-4 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                              <div className="w-1 h-1 rounded-full bg-primary-500" />
                              Primary Operation Hub
                            </label>
                            <div className="relative">
                              <Input
                                icon={<MapPin className="h-4 w-4 md:h-5 md:w-5" />}
                                type="text"
                                placeholder="e.g., Remote, Austin TX, London"
                                value={preferences.location}
                                onChange={(e) => setPreferences((p) => ({ ...p, location: e.target.value }))}
                                className="bg-white shadow-sm text-sm"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="mb-2 md:mb-4 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                              <div className="w-1 h-1 rounded-full bg-primary-500" />
                              Target Role Classification
                            </label>
                            <div className="relative">
                              <Input
                                icon={<Briefcase className="h-4 w-4 md:h-5 md:w-5" />}
                                type="text"
                                placeholder="e.g., Staff AI Engineer"
                                value={preferences.role_type}
                                onChange={(e) => setPreferences((p) => ({ ...p, role_type: e.target.value }))}
                                className="bg-white shadow-sm text-sm"
                              />
                            </div>
                          </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-3 md:gap-8">
                          <div>
                            <label className="mb-2 md:mb-4 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                              <div className="w-1 h-1 rounded-full bg-primary-500" />
                              Min Multiplier (Salary)
                            </label>
                            <div className="relative">
                              <Input
                                icon={<DollarSign className="h-4 w-4 md:h-5 md:w-5" />}
                                type="number"
                                placeholder="150000"
                                value={preferences.salary_min}
                                onChange={(e) => setPreferences((p) => ({ ...p, salary_min: e.target.value }))}
                                className="bg-white shadow-sm text-sm"
                              />
                            </div>
                          </div>
                          <div className="flex flex-col justify-end">
                            <label className={`flex items-center gap-3 md:gap-4 p-3 md:p-5 rounded-2xl cursor-pointer border-2 transition-all ${preferences.remote_only ? 'bg-primary-50 border-primary-200 shadow-sm' : 'bg-slate-50 border-slate-100'}`}>
                              <div className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center transition-all ${preferences.remote_only ? 'bg-primary-600 text-white' : 'bg-white text-slate-300 shadow-sm'}`}>
                                <Zap className="h-4 w-4 md:h-5 md:w-5" />
                              </div>
                              <div className="flex-1">
                                <p className="text-xs font-black text-slate-900 uppercase tracking-tight">Geo-Agnostic Only</p>
                                <p className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-widest">100% Remote Filter</p>
                              </div>
                              <input
                                type="checkbox"
                                checked={preferences.remote_only}
                                onChange={(e) => setPreferences((p) => ({ ...p, remote_only: e.target.checked }))}
                                className="h-5 w-5 md:h-6 md:w-6 rounded-lg border-slate-300 text-primary-600 focus:ring-primary-500"
                              />
                            </label>
                          </div>
                        </div>
                      </div>

                      {/* Work Authorization */}
                      <div className="pt-3 md:pt-6 border-t border-slate-100 mt-3 md:mt-8">
                        <label className="mb-2 md:mb-4 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                          <div className="w-1 h-1 rounded-full bg-emerald-500" />
                          Work Authorization
                        </label>
                        <label className={`flex items-center gap-3 md:gap-4 p-3 md:p-5 rounded-2xl cursor-pointer border-2 transition-all ${preferences.work_authorized ? 'bg-emerald-50 border-emerald-200 shadow-sm' : 'bg-slate-50 border-slate-100'}`}>
                          <div className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center transition-all ${preferences.work_authorized ? 'bg-emerald-600 text-white' : 'bg-white text-slate-300 shadow-sm'}`}>
                            <Shield className="h-4 w-4 md:h-5 md:w-5" />
                          </div>
                          <div className="flex-1">
                            <p className="text-xs font-black text-slate-900 uppercase tracking-tight">Authorized to Work</p>
                            <p className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-widest">No visa sponsorship needed</p>
                          </div>
                          <input
                            type="checkbox"
                            checked={preferences.work_authorized}
                            onChange={(e) => setPreferences((p) => ({ ...p, work_authorized: e.target.checked }))}
                            className="h-5 w-5 md:h-6 md:w-6 rounded-lg border-slate-300 text-emerald-600 focus:ring-emerald-500"
                          />
                        </label>
                      </div>
                    </div>

                    <div className="flex gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                      <Button variant="ghost" onClick={prevStep} className="h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4">
                        <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                        PREV
                      </Button>
                      <Button onClick={handleSavePreferences} className="flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black bg-primary-600 hover:bg-primary-500 shadow-2xl shadow-primary-500/30 text-xs md:text-xl group" disabled={isSavingPreferences}>
                        {isSavingPreferences ? <LoadingSpinner size="sm" /> : "DEPLOY HUNTER ENGINE"}
                        <ArrowRight className="ml-1.5 md:ml-3 h-4 w-4 md:h-6 md:w-6 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </div>
                  </div>
                )}

                {/* Step 5: Review & Ready! */}
                {currentStep === 4 && (
                  <div className="flex flex-col h-full overflow-hidden">
                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                      <div className="text-center py-2 md:py-6">
                        <div className="mx-auto mb-3 md:mb-10 relative">
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: [1, 1.2, 1] }}
                            transition={{ duration: 0.5, times: [0, 0.5, 1] }}
                            className="absolute inset-0 bg-emerald-500/20 rounded-full blur-2xl"
                          />
                          <div className="relative mx-auto flex h-14 w-14 md:h-28 md:w-28 items-center justify-center rounded-[1.5rem] md:rounded-[3rem] bg-emerald-500 shadow-2xl shadow-emerald-200">
                            <CheckCircle2 className="h-7 w-7 md:h-12 md:w-16 text-white" />
                          </div>
                        </div>

                        <h1 className="mb-1 md:mb-4 font-display text-2xl md:text-5xl font-black text-slate-900 tracking-tight">
                          System <span className="text-emerald-500 italic">Online.</span>
                        </h1>
                        <p className="mb-4 md:mb-12 text-slate-500 font-medium max-w-sm mx-auto text-sm md:text-lg leading-relaxed">
                          Calibration successful. Your digital twin is initialized.
                        </p>

                        {/* Preferences Summary Table */}
                        <div className="mb-4 md:mb-12 relative">
                          <div className="absolute -inset-4 bg-gradient-to-b from-slate-900/5 to-transparent rounded-[3rem] -z-10 hidden md:block" />
                          <Card className="bg-slate-950 text-white p-3 md:p-8 rounded-[1.25rem] md:rounded-[2.5rem] shadow-2xl text-left relative overflow-hidden border-white/5 border-t-white/10">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 rounded-full blur-[80px]" />
                            <div className="relative z-10">
                              <div className="flex items-center gap-3 mb-4 md:mb-8 border-b border-white/5 pb-2 md:pb-4">
                                <div className="w-6 h-6 md:w-8 md:h-8 rounded-lg bg-primary-500/20 flex items-center justify-center text-primary-400">
                                  <Rocket className="h-3 w-3 md:h-4 md:w-4" />
                                </div>
                                <h3 className="font-black text-white/50 text-[8px] md:text-[10px] uppercase tracking-[0.3em]">Operational Directives</h3>
                              </div>
                              <div className="space-y-4 md:space-y-6">
                                <div className="flex items-start justify-between group">
                                  <div>
                                    <p className="text-[8px] md:text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">CONFIRMED IDENTITY</p>
                                    <p className="font-black text-sm md:text-lg text-white group-hover:text-emerald-400 transition-colors uppercase">{contactInfo.first_name} {contactInfo.last_name}</p>
                                    <p className="text-[10px] md:text-xs text-white/40 font-medium mt-0.5 max-w-[150px] truncate">{contactInfo.email}</p>
                                  </div>
                                  <User className="h-4 w-4 md:h-5 md:w-5 text-white/10 group-hover:text-emerald-500 transition-colors" />
                                </div>
                                <div className="flex items-start justify-between group">
                                  <div>
                                    <p className="text-[8px] md:text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">AOI GEOLOCATION</p>
                                    <p className="font-black text-sm md:text-lg text-white group-hover:text-primary-400 transition-colors uppercase">{preferences.location || "Global Priority"}</p>
                                  </div>
                                  <MapPin className="h-4 w-4 md:h-5 md:w-5 text-white/10 group-hover:text-primary-500 transition-colors" />
                                </div>
                                <div className="flex items-start justify-between group">
                                  <div>
                                    <p className="text-[8px] md:text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">TARGET CLASSIFICATION</p>
                                    <p className="font-black text-sm md:text-lg text-white group-hover:text-primary-400 transition-colors uppercase">{preferences.role_type || "Senior Impact Role"}</p>
                                  </div>
                                  <Briefcase className="h-4 w-4 md:h-5 md:w-5 text-white/10 group-hover:text-primary-500 transition-colors" />
                                </div>
                              </div>
                              <div className="mt-6 md:mt-10 pt-4 md:pt-8 border-t border-white/5 grid grid-cols-2 gap-3 md:gap-6">
                                <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-emerald-500/10 border border-emerald-500/20 group">
                                  <p className="text-[8px] md:text-[9px] uppercase font-black text-emerald-500/70 mb-1 tracking-widest">Match Strength</p>
                                  <p className="text-xl md:text-2xl font-black text-emerald-400 italic">{completeness}%</p>
                                </div>
                                <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-primary-500/10 border border-primary-500/20 group">
                                  <p className="text-[8px] md:text-[9px] uppercase font-black text-primary-500/70 mb-1 tracking-widest">Data Points</p>
                                  <p className="text-xl md:text-2xl font-black text-primary-400 italic">{[contactInfo.first_name, contactInfo.email, preferences.location, preferences.role_type, preferences.salary_min, (profile?.resume_url || resumeFile)].filter(Boolean).length}/6</p>
                                </div>
                              </div>
                            </div>
                          </Card>
                        </div>
                      </div>
                    </div>

                    <div className="pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                      <Button size="lg" variant="primary" onClick={handleComplete} className="w-full h-10 md:h-16 rounded-[1.25rem] md:rounded-[2rem] text-base md:text-2xl font-black shadow-[0_20px_50px_-12px_rgba(59,130,246,0.5)] bg-primary-600 hover:bg-primary-500 hover:scale-[1.03] active:scale-95 transition-all group overflow-hidden relative" disabled={isCompleting}>
                        <span className="relative z-10 flex items-center justify-center gap-2 md:gap-4">
                          {isCompleting ? <LoadingSpinner size="sm" /> : "LAUNCH COMMAND CENTER"}
                          <Rocket className="h-5 w-5 md:h-8 md:w-8 group-hover:translate-x-2 group-hover:-translate-y-2 transition-transform" />
                        </span>
                        <motion.div
                          animate={{ x: ['-100%', '200%'] }}
                          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12"
                        />
                      </Button>
                      <p className="mt-2 md:mt-8 text-[8px] md:text-[10px] text-slate-400 font-black uppercase tracking-[0.4em] hidden md:block">Full system authority granted.</p>
                    </div>
                  </div>
                )}
              </Card>
            </motion.div>
          </AnimatePresence>

          {/* Helper text - hidden on mobile */}
          <p className="mt-3 md:mt-8 text-center text-[10px] md:text-xs text-slate-400 font-medium hidden md:block">
            Step recorded at {new Date().toLocaleTimeString()} • Secured by 256-bit encryption
          </p>
        </div>
      </main>

      {/* Footer - desktop only */}
      <footer className="hidden md:block px-6 py-4 lg:py-6 border-t border-slate-200 bg-white shrink-0">
        <div className="max-w-2xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-400 font-medium font-bold">© {new Date().getFullYear()} JobHuntin AI. Intelligence for Career Acceleration.</p>
          <div className="flex gap-6">
            <a href="/privacy" className="text-xs text-slate-400 hover:text-slate-900 font-bold uppercase transition-colors">Privacy</a>
            <a href="/terms" className="text-xs text-slate-400 hover:text-slate-900 font-bold uppercase transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
