import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Check, Upload, MapPin, Briefcase, DollarSign, Rocket, ArrowRight, ArrowLeft, FileText, CheckCircle2, Sparkles, User, Zap, Mail, Phone, Shield } from "lucide-react";
import { Logo } from '../../components/brand/Logo';
import { useOnboarding } from "../../hooks/useOnboarding";
import { useProfile } from "../../hooks/useProfile";
import { useAISuggestions } from "../../hooks/useAISuggestions";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { AISuggestionCard, SalarySuggestionCard } from "../../components/ui/AISuggestionCard";
import { pushToast } from "../../lib/toast";
import { motion, AnimatePresence } from "framer-motion";

export default function Onboarding() {
  const navigate = useNavigate();
  const { steps, currentStep, currentStepData, progress, isFirstStep, isLastStep, nextStep, prevStep, resetOnboarding } = useOnboarding();
  const { profile, loading, uploadResume, savePreferences, completeOnboarding, updateProfile } = useProfile();
  const aiSuggestions = useAISuggestions();

  const [resumeFile, setResumeFile] = React.useState<File | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [resumeError, setResumeError] = React.useState<string | null>(null);
  const [preferences, setPreferences] = React.useState({
    location: "",
    role_type: "",
    salary_min: "",
    remote_only: false,
    work_authorized: true,
  });

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
      pushToast({ title: "Upload failed", description: message, tone: "error" });
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
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Minimal Header */}
      <header className="px-6 h-12 flex items-center justify-between bg-white/80 backdrop-blur-xl border-b border-slate-200 sticky top-0 z-50">
        <Logo to="/app/onboarding" size="sm" />
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-50 border border-primary-100">
            <div className="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
            <span className="text-[10px] font-black text-primary-700 uppercase tracking-widest">AI Calibration Active</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => resetOnboarding()} className="text-slate-500 text-xs font-bold uppercase hover:bg-slate-100">
            Restart
          </Button>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8 md:py-12 bg-grid-premium opacity-100">
        <div className="w-full max-w-2xl relative">
          {/* Subtle background glow */}
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-primary-500/10 rounded-full blur-[100px] pointer-events-none" />
          <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-amber-500/10 rounded-full blur-[100px] pointer-events-none" />
          {/* Progress bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3 px-1">
              <span className="text-xs font-black text-slate-400 uppercase tracking-[0.2em]">
                Calibration Progress — {(progress).toFixed(0)}%
              </span>
              <span className="text-xs font-black text-primary-600 uppercase tracking-[0.2em]">{currentStepData.title}</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-primary-600 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
                transition={{ type: "spring", stiffness: 50, damping: 15 }}
              />
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, scale: 0.98, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98, y: -10 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <Card tone="glass" shadow="lift" className="p-8 border-slate-200/60 overflow-hidden relative">
                {/* Decorative background elements inside card */}
                <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary-500/5 rounded-full blur-3xl pointer-events-none" />

                {/* Profile completeness indicator */}
                <div className="mb-6 rounded-2xl bg-slate-900 border border-slate-800 p-4 shadow-xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl group-hover:bg-emerald-500/20 transition-colors" />
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                        <Sparkles className="h-4 w-4 text-emerald-400" />
                      </div>
                      <div>
                        <span className="block text-[10px] font-black text-emerald-500/70 uppercase tracking-widest">Intelligence Profile</span>
                        <span className="text-xs font-bold text-white">System Confidence</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-black text-white italic">{completeness}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${completeness}%` }}
                      className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                      transition={{ type: "spring", stiffness: 40, damping: 12 }}
                    />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {(profile?.resume_url || resumeFile) && (
                      <Badge className="text-[9px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-1">
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                        Experience Mapped
                      </Badge>
                    )}
                    {preferences.location && (
                      <Badge className="text-[9px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-1">
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                        Geospatial Set
                      </Badge>
                    )}
                    {preferences.role_type && (
                      <Badge className="text-[9px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-1">
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                        Role Target Lock
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Step 1: Welcome */}
                {currentStep === 0 && (
                  <div className="text-center py-4">
                    <div className="mx-auto mb-6 relative">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 rounded-[2rem] border-2 border-dashed border-primary-500/20"
                      />
                      <div className="relative mx-auto flex h-20 w-20 items-center justify-center rounded-[2rem] bg-slate-900 shadow-2xl shadow-primary-500/20 scale-100">
                        <Rocket className="h-10 w-10 text-primary-400" />
                      </div>
                    </div>
                    <h1 className="mb-3 font-display text-3xl font-black text-slate-900 tracking-tight leading-tight">
                      Initiate <span className="text-primary-600 italic">Hyper-Hunt.</span>
                    </h1>
                    <p className="mb-8 text-slate-500 font-medium leading-relaxed max-w-sm mx-auto text-base">
                      We're about to build your digital autonomous twin. Calibration takes 90 seconds.
                    </p>
                    <div className="grid gap-3 mb-8">
                      {[
                        { title: "Skill Mapping", desc: "AI-driven resume vectorization", icon: Sparkles },
                        { title: "Radar Tuning", desc: "Location & salary baseline profiling", icon: MapPin },
                        { title: "Autonomous Launch", desc: "1-Click application engine activation", icon: Rocket },
                      ].map((item, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.2 + i * 0.1 }}
                          className="flex items-center gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-100/50 hover:bg-white hover:shadow-md transition-all group"
                        >
                          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-100 text-primary-600 group-hover:bg-primary-600 group-hover:text-white transition-colors">
                            <item.icon className="h-5 w-5" />
                          </div>
                          <div className="text-left">
                            <p className="text-sm font-black text-slate-900 uppercase tracking-tight">{item.title}</p>
                            <p className="text-xs text-slate-500 font-medium">{item.desc}</p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                    <Button size="lg" onClick={nextStep} className="w-full h-12 rounded-[1.5rem] text-xl font-black shadow-2xl shadow-primary-500/30 bg-primary-600 hover:bg-primary-500 hover:scale-[1.02] transition-all group">
                      BEGIN CALIBRATION
                      <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </div>
                )}

                {/* Step 2: Resume Upload */}
                {currentStep === 1 && (
                  <div className="py-2">
                    <div className="mb-10 flex items-center gap-5 border-b border-slate-100 pb-8">
                      <div className="flex h-12 w-16 items-center justify-center rounded-[1.5rem] bg-primary-50 border border-primary-100 text-primary-600 shadow-inner">
                        <Upload className="h-8 w-8" />
                      </div>
                      <div>
                        <h2 className="font-display text-3xl font-black text-slate-900 tracking-tight">Experience Input</h2>
                        <p className="text-sm text-slate-500 font-medium italic">Feed the AI your career history for optimization.</p>
                      </div>
                    </div>

                    <div className="mb-8 relative group">
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
                        className={`flex cursor-pointer flex-col items-center gap-6 rounded-[2.5rem] border-3 border-dashed p-14 text-center transition-all ${resumeFile
                          ? "bg-primary-50/50 border-primary-300"
                          : "bg-slate-50/50 border-slate-200 hover:bg-slate-50 hover:border-primary-300"
                          }`}
                      >
                        <div className={`flex h-24 w-24 items-center justify-center rounded-[2rem] bg-white shadow-xl transition-all ${isUploading ? 'animate-pulse scale-90' : 'group-hover:scale-110 group-hover:rotate-3'}`}>
                          {isUploading ? (
                            <div className="relative">
                              <Sparkles className="h-12 w-12 text-primary-400 animate-spin-slow" />
                              <div className="absolute inset-0 flex items-center justify-center">
                                <div className="w-6 h-6 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
                              </div>
                            </div>
                          ) : (
                            <FileText className={`h-12 w-12 ${resumeFile ? 'text-primary-600' : 'text-slate-300'}`} />
                          )}
                        </div>
                        <div className="space-y-2">
                          <p className={`text-xl font-black ${resumeFile ? 'text-primary-700' : 'text-slate-900'}`}>
                            {resumeFile ? resumeFile.name : "Drop Intelligence File"}
                          </p>
                          <p className="text-sm text-slate-400 font-bold uppercase tracking-widest">PDF, DOCX — AI Optimization Ready</p>
                        </div>
                      </label>
                      {isUploading && (
                        <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] rounded-[2.5rem] flex flex-col items-center justify-center gap-4 z-10">
                          <div className="w-64 h-2 bg-slate-200 rounded-full overflow-hidden border border-slate-100 shadow-inner">
                            <motion.div
                              className="h-full bg-primary-500"
                              initial={{ width: "0%" }}
                              animate={{ width: "100%" }}
                              transition={{ duration: 4, repeat: Infinity }}
                            />
                          </div>
                          <p className="text-xs font-black text-primary-600 uppercase tracking-widest animate-pulse">Scanning Vector Space...</p>
                        </div>
                      )}
                    </div>

                    <div className="mb-10">
                      <div className="flex items-center gap-2 mb-4 px-1">
                        <div className="h-[1px] flex-1 bg-slate-100" />
                        <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">or social reference</span>
                        <div className="h-[1px] flex-1 bg-slate-100" />
                      </div>
                      <div className="relative">
                        <User className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                        <input
                          type="url"
                          placeholder="LinkedIn URL (optional context)"
                          value={linkedinUrl}
                          onChange={(e) => setLinkedinUrl(e.target.value)}
                          className="w-full rounded-[1.25rem] border border-slate-200 bg-white pl-14 pr-5 py-5 text-slate-900 font-bold outline-none focus:ring-8 focus:ring-primary-500/5 focus:border-primary-500 transition-all shadow-sm text-lg placeholder:text-slate-300 placeholder:font-medium"
                        />
                      </div>
                    </div>

                    {resumeError && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8 rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-600 font-bold flex items-center gap-3"
                      >
                        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        {resumeError}
                      </motion.div>
                    )}

                    <div className="flex gap-4">
                      <Button variant="ghost" onClick={prevStep} className="flex-1 h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all">
                        <ArrowLeft className="mr-2 h-5 w-5" />
                        PREV
                      </Button>
                      {resumeFile ? (
                        <Button
                          onClick={handleResumeUpload}
                          disabled={isUploading}
                          className="flex-[2] h-12 rounded-[1.25rem] font-black bg-primary-600 hover:bg-primary-500 shadow-2xl shadow-primary-500/30 text-lg group overflow-hidden relative"
                        >
                          <span className="relative z-10 flex items-center justify-center">
                            {isUploading ? <LoadingSpinner size="sm" /> : showParsingPreview ? "SYNC NEW SOURCE" : "EXTRACT EXPERIENCE"}
                            <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                          </span>
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          onClick={nextStep}
                          className="flex-[2] h-12 rounded-[1.25rem] font-black text-slate-500 hover:border-slate-900 hover:text-slate-900 border-2 border-slate-200 transition-all text-lg"
                        >
                          SKIP TO MANUAL ENTRY
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
                  <div className="py-2">
                    <div className="mb-10 flex items-center gap-5 border-b border-slate-100 pb-8">
                      <div className="flex h-12 w-16 items-center justify-center rounded-[1.5rem] bg-emerald-50 border border-emerald-100 text-emerald-600 shadow-inner">
                        <User className="h-8 w-8" />
                      </div>
                      <div>
                        <h2 className="font-display text-3xl font-black text-slate-900 tracking-tight">Verify Identity</h2>
                        <p className="text-sm text-slate-500 font-medium italic">Confirm the details we extracted. The AI uses these to apply on your behalf.</p>
                      </div>
                    </div>

                    <div className="grid gap-8">
                      <div className="grid md:grid-cols-2 gap-6">
                        <div>
                          <label className="mb-3 flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                            <div className="w-1 h-1 rounded-full bg-emerald-500" />
                            First Name <span className="text-red-400">*</span>
                          </label>
                          <div className="relative">
                            <User className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                            <input
                              type="text"
                              placeholder="John"
                              value={contactInfo.first_name}
                              onChange={(e) => setContactInfo(c => ({ ...c, first_name: e.target.value }))}
                              className="w-full rounded-[1.25rem] border border-slate-200 bg-white pl-14 pr-5 py-5 text-slate-900 font-bold outline-none focus:ring-8 focus:ring-emerald-500/5 focus:border-emerald-500 transition-all shadow-sm text-lg placeholder:text-slate-200"
                            />
                          </div>
                        </div>
                        <div>
                          <label className="mb-3 flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                            <div className="w-1 h-1 rounded-full bg-emerald-500" />
                            Last Name <span className="text-red-400">*</span>
                          </label>
                          <div className="relative">
                            <User className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                            <input
                              type="text"
                              placeholder="Doe"
                              value={contactInfo.last_name}
                              onChange={(e) => setContactInfo(c => ({ ...c, last_name: e.target.value }))}
                              className="w-full rounded-[1.25rem] border border-slate-200 bg-white pl-14 pr-5 py-5 text-slate-900 font-bold outline-none focus:ring-8 focus:ring-emerald-500/5 focus:border-emerald-500 transition-all shadow-sm text-lg placeholder:text-slate-200"
                            />
                          </div>
                        </div>
                      </div>

                      <div>
                        <label className="mb-3 flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                          <div className="w-1 h-1 rounded-full bg-emerald-500" />
                          Email Address <span className="text-red-400">*</span>
                        </label>
                        <div className="relative">
                          <Mail className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                          <input
                            type="email"
                            placeholder="john@example.com"
                            value={contactInfo.email}
                            onChange={(e) => setContactInfo(c => ({ ...c, email: e.target.value }))}
                            className="w-full rounded-[1.25rem] border border-slate-200 bg-white pl-14 pr-5 py-5 text-slate-900 font-bold outline-none focus:ring-8 focus:ring-emerald-500/5 focus:border-emerald-500 transition-all shadow-sm text-lg placeholder:text-slate-200"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="mb-3 flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                          <div className="w-1 h-1 rounded-full bg-emerald-500" />
                          Phone Number
                        </label>
                        <div className="relative">
                          <Phone className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                          <input
                            type="tel"
                            placeholder="+1 (555) 123-4567"
                            value={contactInfo.phone}
                            onChange={(e) => setContactInfo(c => ({ ...c, phone: e.target.value }))}
                            className="w-full rounded-[1.25rem] border border-slate-200 bg-white pl-14 pr-5 py-5 text-slate-900 font-bold outline-none focus:ring-8 focus:ring-emerald-500/5 focus:border-emerald-500 transition-all shadow-sm text-lg placeholder:text-slate-200"
                          />
                        </div>
                      </div>
                    </div>

                    {parsedResume && (
                      <div className="mt-8 p-5 rounded-2xl bg-emerald-50 border border-emerald-100">
                        <div className="flex items-center gap-2 mb-2">
                          <Sparkles className="h-4 w-4 text-emerald-600" />
                          <p className="text-[10px] font-black text-emerald-700 uppercase tracking-widest">AI-Extracted From Resume</p>
                        </div>
                        <p className="text-sm text-emerald-800 font-medium">We pre-filled these from your resume. Please verify and correct anything that looks off.</p>
                      </div>
                    )}

                    <div className="flex gap-4 pt-10">
                      <Button variant="ghost" onClick={prevStep} className="flex-1 h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all">
                        <ArrowLeft className="mr-2 h-5 w-5" />
                        PREV
                      </Button>
                      <Button
                        onClick={handleSaveContact}
                        disabled={!contactInfo.first_name || !contactInfo.email || isSavingContact}
                        className="flex-[2] h-12 rounded-[1.25rem] font-black bg-emerald-600 hover:bg-emerald-500 shadow-2xl shadow-emerald-500/30 text-lg disabled:opacity-50 disabled:cursor-not-allowed group"
                      >
                        {isSavingContact ? <LoadingSpinner size="sm" /> : "CONFIRM IDENTITY"}
                        <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </div>
                  </div>
                )}

                {/* Step 4: Preferences */}
                {currentStep === 3 && (
                  <div className="space-y-10 py-2">
                    <div className="flex items-center gap-5 border-b border-slate-100 pb-8">
                      <div className="flex h-12 w-16 items-center justify-center rounded-[1.5rem] bg-amber-50 border border-amber-100 text-amber-600 shadow-inner">
                        <MapPin className="h-8 w-8" />
                      </div>
                      <div>
                        <h2 className="font-display text-3xl font-black text-slate-900 tracking-tight">Active Parameters</h2>
                        <p className="text-sm text-slate-500 font-medium italic">Define the geospatial and fiscal bounds for the AI.</p>
                      </div>
                    </div>

                    {/* AI Suggestions Section */}
                    {(aiSuggestions.roles.data || aiSuggestions.roles.loading || aiSuggestions.locations.data || aiSuggestions.locations.loading) && (
                      <div className="grid md:grid-cols-2 gap-6 mb-8">
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
                            ? `${Math.round(aiSuggestions.locations.data.remote_friendly_score * 100)}% remote-friendly role`
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
                      <div className="mb-8">
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

                    <div className="space-y-8">
                      <div className="grid gap-8">
                        <div>
                          <label className="mb-4 flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                            <div className="w-1 h-1 rounded-full bg-primary-500" />
                            Primary Operation Hub
                          </label>
                          <div className="relative">
                            <MapPin className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                            <input
                              type="text"
                              placeholder="e.g., Remote, Austin TX, London"
                              value={preferences.location}
                              onChange={(e) => setPreferences((p) => ({ ...p, location: e.target.value }))}
                              className="w-full rounded-[1.25rem] border border-slate-200 bg-white pl-14 pr-5 py-5 text-slate-900 font-bold outline-none focus:ring-8 focus:ring-primary-500/5 focus:border-primary-500 transition-all shadow-sm text-lg placeholder:text-slate-200"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="mb-4 flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                            <div className="w-1 h-1 rounded-full bg-primary-500" />
                            Target Role Classification
                          </label>
                          <div className="relative">
                            <Briefcase className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                            <input
                              type="text"
                              placeholder="e.g., Staff AI Engineer"
                              value={preferences.role_type}
                              onChange={(e) => setPreferences((p) => ({ ...p, role_type: e.target.value }))}
                              className="w-full rounded-[1.25rem] border border-slate-200 bg-white pl-14 pr-5 py-5 text-slate-900 font-bold outline-none focus:ring-8 focus:ring-primary-500/5 focus:border-primary-500 transition-all shadow-sm text-lg placeholder:text-slate-200"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-8">
                        <div>
                          <label className="mb-4 flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                            <div className="w-1 h-1 rounded-full bg-primary-500" />
                            Min Multiplier (Salary)
                          </label>
                          <div className="relative">
                            <DollarSign className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                            <input
                              type="number"
                              placeholder="150000"
                              value={preferences.salary_min}
                              onChange={(e) => setPreferences((p) => ({ ...p, salary_min: e.target.value }))}
                              className="w-full rounded-[1.25rem] border border-slate-200 bg-white pl-14 pr-5 py-5 text-slate-900 font-bold outline-none focus:ring-8 focus:ring-primary-500/5 focus:border-primary-500 transition-all shadow-sm text-lg placeholder:text-slate-200"
                            />
                          </div>
                        </div>
                        <div className="flex flex-col justify-end">
                          <label className={`flex items-center gap-4 p-5 rounded-[1.25rem] cursor-pointer border-2 transition-all ${preferences.remote_only ? 'bg-primary-50 border-primary-200 shadow-sm' : 'bg-slate-50 border-slate-100'}`}>
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${preferences.remote_only ? 'bg-primary-600 text-white' : 'bg-white text-slate-300 shadow-sm'}`}>
                              <Zap className="h-5 w-5" />
                            </div>
                            <div className="flex-1">
                              <p className="text-xs font-black text-slate-900 uppercase tracking-tight">Geo-Agnostic Only</p>
                              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">100% Remote Filter</p>
                            </div>
                            <input
                              type="checkbox"
                              checked={preferences.remote_only}
                              onChange={(e) => setPreferences((p) => ({ ...p, remote_only: e.target.checked }))}
                              className="h-6 w-6 rounded-lg border-slate-300 text-primary-600 focus:ring-primary-500"
                            />
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* Work Authorization */}
                    <div className="pt-6 border-t border-slate-100">
                      <label className="mb-4 flex items-center gap-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                        <div className="w-1 h-1 rounded-full bg-emerald-500" />
                        Work Authorization
                      </label>
                      <label className={`flex items-center gap-4 p-5 rounded-[1.25rem] cursor-pointer border-2 transition-all ${preferences.work_authorized ? 'bg-emerald-50 border-emerald-200 shadow-sm' : 'bg-slate-50 border-slate-100'}`}>
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${preferences.work_authorized ? 'bg-emerald-600 text-white' : 'bg-white text-slate-300 shadow-sm'}`}>
                          <Shield className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                          <p className="text-xs font-black text-slate-900 uppercase tracking-tight">Authorized to Work</p>
                          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">No visa sponsorship needed</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={preferences.work_authorized}
                          onChange={(e) => setPreferences((p) => ({ ...p, work_authorized: e.target.checked }))}
                          className="h-6 w-6 rounded-lg border-slate-300 text-emerald-600 focus:ring-emerald-500"
                        />
                      </label>
                    </div>

                    <div className="flex gap-4 pt-10">
                      <Button variant="ghost" onClick={prevStep} className="flex-1 h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all">
                        <ArrowLeft className="mr-2 h-5 w-5" />
                        PREV
                      </Button>
                      <Button onClick={handleSavePreferences} className="flex-[2] h-12 rounded-[1.25rem] font-black bg-primary-600 hover:bg-primary-500 shadow-2xl shadow-primary-500/30 text-lg sm:text-xl group" disabled={isSavingPreferences}>
                        {isSavingPreferences ? <LoadingSpinner size="sm" /> : "DEPLOY HUNTER ENGINE"}
                        <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </div>
                  </div>
                )}

                {/* Step 5: Review & Ready! */}
                {currentStep === 4 && (
                  <div className="text-center py-6">
                    <div className="mx-auto mb-10 relative">
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 0.5, times: [0, 0.5, 1] }}
                        className="absolute inset-0 bg-emerald-500/20 rounded-full blur-2xl"
                      />
                      <div className="relative mx-auto flex h-28 w-28 items-center justify-center rounded-[3rem] bg-emerald-500 shadow-2xl shadow-emerald-200">
                        <CheckCircle2 className="h-12 w-16 text-white" />
                      </div>
                    </div>

                    <h1 className="mb-4 font-display text-5xl font-black text-slate-900 tracking-tight">
                      System <span className="text-emerald-500 italic">Online.</span>
                    </h1>
                    <p className="mb-12 text-slate-500 font-medium max-w-sm mx-auto text-lg leading-relaxed">
                      Calibration successful. Your digital twin is initialized and ready for high-velocity deployment.
                    </p>

                    {/* Preferences Summary Table */}
                    <div className="mb-12 relative">
                      <div className="absolute -inset-4 bg-gradient-to-b from-slate-900/5 to-transparent rounded-[3rem] -z-10" />
                      <Card className="bg-slate-950 text-white p-8 rounded-[2.5rem] shadow-2xl text-left relative overflow-hidden border-white/5 border-t-white/10">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 rounded-full blur-[80px]" />
                        <div className="relative z-10">
                          <div className="flex items-center gap-3 mb-8 border-b border-white/5 pb-4">
                            <div className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center text-primary-400">
                              <Rocket className="h-4 w-4" />
                            </div>
                            <h3 className="font-black text-white/50 text-[10px] uppercase tracking-[0.3em]">Operational Directives</h3>
                          </div>
                          <div className="space-y-6">
                            <div className="flex items-start justify-between group">
                              <div>
                                <p className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">CONFIRMED IDENTITY</p>
                                <p className="font-black text-lg text-white group-hover:text-emerald-400 transition-colors uppercase">{contactInfo.first_name} {contactInfo.last_name}</p>
                                <p className="text-xs text-white/40 font-medium mt-0.5">{contactInfo.email}{contactInfo.phone ? ` • ${contactInfo.phone}` : ''}</p>
                              </div>
                              <User className="h-5 w-5 text-white/10 group-hover:text-emerald-500 transition-colors" />
                            </div>
                            <div className="flex items-start justify-between group">
                              <div>
                                <p className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">AOI GEOLOCATION</p>
                                <p className="font-black text-lg text-white group-hover:text-primary-400 transition-colors uppercase">{preferences.location || "Global Priority"}</p>
                              </div>
                              <MapPin className="h-5 w-5 text-white/10 group-hover:text-primary-500 transition-colors" />
                            </div>
                            <div className="flex items-start justify-between group">
                              <div>
                                <p className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">TARGET CLASSIFICATION</p>
                                <p className="font-black text-lg text-white group-hover:text-primary-400 transition-colors uppercase">{preferences.role_type || "Senior Impact Role"}</p>
                              </div>
                              <Briefcase className="h-5 w-5 text-white/10 group-hover:text-primary-500 transition-colors" />
                            </div>
                            <div className="flex items-start justify-between group">
                              <div>
                                <p className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">MIN COMP BASELINE</p>
                                <p className="font-black text-lg text-white group-hover:text-primary-400 transition-colors uppercase">
                                  {preferences.salary_min ? `$${(Number(preferences.salary_min) / 1000).toFixed(0)}k ANNUAL` : "PREMIUM ONLY"}
                                </p>
                              </div>
                              <DollarSign className="h-5 w-5 text-white/10 group-hover:text-primary-500 transition-colors" />
                            </div>
                            <div className="flex items-start justify-between group">
                              <div>
                                <p className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">WORK AUTHORIZATION</p>
                                <p className={`font-black text-lg transition-colors uppercase ${preferences.work_authorized ? 'text-emerald-400' : 'text-amber-400'}`}>
                                  {preferences.work_authorized ? "AUTHORIZED — NO SPONSORSHIP" : "SPONSORSHIP REQUIRED"}
                                </p>
                              </div>
                              <Shield className="h-5 w-5 text-white/10 group-hover:text-emerald-500 transition-colors" />
                            </div>
                          </div>
                          <div className="mt-10 pt-8 border-t border-white/5 grid grid-cols-2 gap-6">
                            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 group">
                              <p className="text-[9px] uppercase font-black text-emerald-500/70 mb-1 tracking-widest">Match Strength</p>
                              <p className="text-2xl font-black text-emerald-400 italic">{completeness}%</p>
                            </div>
                            <div className="p-4 rounded-2xl bg-primary-500/10 border border-primary-500/20 group">
                              <p className="text-[9px] uppercase font-black text-primary-500/70 mb-1 tracking-widest">Data Points</p>
                              <p className="text-2xl font-black text-primary-400 italic">{[contactInfo.first_name, contactInfo.email, preferences.location, preferences.role_type, preferences.salary_min, (profile?.resume_url || resumeFile)].filter(Boolean).length}/6</p>
                            </div>
                          </div>
                        </div>
                      </Card>
                    </div>

                    <Button size="lg" variant="primary" onClick={handleComplete} className="w-full h-20 rounded-[2rem] text-2xl font-black shadow-[0_20px_50px_-12px_rgba(59,130,246,0.5)] bg-primary-600 hover:bg-primary-500 hover:scale-[1.03] active:scale-95 transition-all group overflow-hidden relative" disabled={isCompleting}>
                      <span className="relative z-10 flex items-center justify-center gap-4">
                        {isCompleting ? <LoadingSpinner size="sm" /> : "LAUNCH COMMAND CENTER"}
                        <Rocket className="h-8 w-8 group-hover:translate-x-2 group-hover:-translate-y-2 transition-transform" />
                      </span>
                      <motion.div
                        animate={{ x: ['-100%', '200%'] }}
                        transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12"
                      />
                    </Button>
                    <p className="mt-8 text-[10px] text-slate-400 font-black uppercase tracking-[0.4em]">Full system authority granted.</p>
                  </div>
                )}
              </Card>
            </motion.div>
          </AnimatePresence>

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
