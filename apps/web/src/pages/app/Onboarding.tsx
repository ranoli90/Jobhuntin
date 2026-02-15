import * as React from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Sparkles } from "lucide-react";
import { Logo } from "../../components/brand/Logo";
import { useOnboarding } from "../../hooks/useOnboarding";
import { useProfile } from "../../hooks/useProfile";
import { useAISuggestions } from "../../hooks/useAISuggestions";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { pushToast } from "../../lib/toast";
import { api } from "../../lib/api";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Skeleton, OnboardingSkeleton } from "../../components/ui/Skeleton";
import { checkEmailTypo } from "../../lib/emailUtils";

// Step Components
import { WelcomeStep } from "./onboarding/steps/WelcomeStep";
import { ResumeStep } from "./onboarding/steps/ResumeStep";
import { SkillReviewStep } from "./onboarding/steps/SkillReviewStep";
import { ConfirmContactStep } from "./onboarding/steps/ConfirmContactStep";
import { PreferencesStep } from "./onboarding/steps/PreferencesStep";
import { WorkStyleStep } from "./onboarding/steps/WorkStyleStep";
import { ReadyStep } from "./onboarding/steps/ReadyStep";

// Types
import { ParsedResume, RichSkill } from "../../types/onboarding";

export default function Onboarding() {
  const navigate = useNavigate();
  const { steps, currentStep, currentStepData, progress, isFirstStep, isLastStep, nextStep, prevStep, resetOnboarding, formData, updateFormData } = useOnboarding();
  const { profile, loading, uploadResume, savePreferences, completeOnboarding, updateProfile } = useProfile();
  const aiSuggestions = useAISuggestions();
  const [isLowPowerMode, setIsLowPowerMode] = React.useState(false);

  React.useEffect(() => {
    // Check for save-data preference
    if ('connection' in navigator && (navigator as any).connection.saveData) {
      setIsLowPowerMode(true);
    }

    // Check battery status if available
    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((battery: any) => {
        setIsLowPowerMode(battery.level < 0.2 && !battery.charging);

        battery.addEventListener('levelchange', () => {
          setIsLowPowerMode(battery.level < 0.2 && !battery.charging);
        });
        battery.addEventListener('chargingchange', () => {
          setIsLowPowerMode(battery.level < 0.2 && !battery.charging);
        });
      });
    }
  }, []);

  const shouldReduceMotion = useReducedMotion() || isLowPowerMode;

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

  const [formErrors, setFormErrors] = React.useState<Record<string, string>>({});

  const [contactInfo, setContactInfo] = React.useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
  });
  const [isSavingContact, setIsSavingContact] = React.useState(false);

const [linkedinUrl, setLinkedinUrl] = React.useState(formData.linkedinUrl || "");
  const [parsedResume, setParsedResume] = React.useState<ParsedResume | null>(null);
  const [showParsingPreview, setShowParsingPreview] = React.useState(false);
  const [isSavingPreferences, setIsSavingPreferences] = React.useState(false);
  const [isCompleting, setIsCompleting] = React.useState(false);
const [parsedProfile, setParsedProfile] = React.useState<Record<string, unknown> | null>(null);
  const [emailTypoSuggestion, setEmailTypoSuggestion] = React.useState<string | null>(null);
  const [richSkills, setRichSkills] = React.useState<RichSkill[]>([]);
  const [isSavingSkills, setIsSavingSkills] = React.useState(false);
  const [workStyleAnswers, setWorkStyleAnswers] = React.useState<Record<string, string>>({});
  const [isSavingWorkStyle, setIsSavingWorkStyle] = React.useState(false);
  
  // Restore linkedinUrl from formData on mount (for page refresh persistence)
  React.useEffect(() => {
    if (formData.linkedinUrl && !linkedinUrl) {
      setLinkedinUrl(formData.linkedinUrl);
    }
  }, [formData.linkedinUrl, linkedinUrl]);

  const triggerHaptic = (type: 'success' | 'warning' | 'light' = 'light') => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      if (type === 'success') navigator.vibrate([10, 30, 10]);
      else if (type === 'warning') navigator.vibrate([30, 10, 30]);
      else navigator.vibrate(10);
    }
  };

  const handleSaveWorkStyle = async () => {
    triggerHaptic('light');
    setIsSavingWorkStyle(true);
    try {
      await api.post("/me/work-style", workStyleAnswers);
      nextStep();
    } catch (err) {
      console.error(err);
      pushToast({ title: "Failed to save work style", tone: "error" });
    } finally {
      setIsSavingWorkStyle(false);
    }
  };

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
      // Pre-fill LinkedIn URL from profile if available
      setLinkedinUrl(prev => prev || c.linkedin_url || "");
    }
  }, [profile?.contact, profile?.email]);

  // Sync internal states to useOnboarding's formData for refresh persistence
  React.useEffect(() => {
    updateFormData({ contactInfo, preferences, linkedinUrl });
  }, [contactInfo, preferences, linkedinUrl, updateFormData]);

  // Remember Me - Welcome Back
  React.useEffect(() => {
    // If we have a profile but haven't completed onboarding, welcome them back
    if (profile && !profile.has_completed_onboarding && currentStep > 0) {
      // Only show if we haven't shown it this session
      const hasWelcomed = sessionStorage.getItem("has_welcomed_back");
      if (!hasWelcomed) {
        pushToast({
          title: "Welcome back!",
          description: `Picking up where you left off at step ${currentStep + 1}.`,
          tone: "info"
        });
        sessionStorage.setItem("has_welcomed_back", "true");
      }
    }
  }, [profile, currentStep]);

  // Handle email typo check
  React.useEffect(() => {
    if (contactInfo.email) {
      const suggestion = checkEmailTypo(contactInfo.email);
      setEmailTypoSuggestion(suggestion);
    } else {
      setEmailTypoSuggestion(null);
    }
  }, [contactInfo.email]);

  // Keyboard Shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if inside an input/textarea to avoid conflict
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
        // Allow Ctrl+Enter even in inputs to submit
        if (!(e.ctrlKey && e.key === 'Enter')) return;
      }

      if (e.ctrlKey && e.key === 'Enter') {
        // Specific completion logic or generic next
        if (currentStep === 6 && !isCompleting) {
          handleComplete();
        } else if (!isLastStep) {
          // Basic validation check before blindly advancing?
          // The steps usuall have disabled buttons if invalid.
          // For now, let's just try calling nextStep, but generally the button state controls flow.
          // However, nextStep() in hook doesn't check validation. 
          // We might need to check specific step validation here or just trust the user/hook.
          // Ideally we trigger the button click.
          const nextBtn = document.querySelector('button[aria-label="Confirm identity and proceed"], button[aria-label="Save preferences and deploy hunter engine"], button[aria-label="Save answers and continue"], button[aria-label="Finalize setup and launch command center"]');
          if (nextBtn && !(nextBtn as HTMLButtonElement).disabled) {
            (nextBtn as HTMLElement).click();
          } else {
            // Fallback for simple steps
            nextStep();
          }
        }
      } else if (e.key === 'Escape') {
        // Maybe unrelated, but handy
      } else if (e.altKey && e.key === 'ArrowLeft') {
        if (!isFirstStep) prevStep();
      } else if (e.altKey && e.key === 'ArrowRight') {
        // Same logic as Ctrl+Enter for next
        const nextBtn = document.querySelector('button[aria-label*="proceed"], button[aria-label*="deploy"], button[aria-label*="continue"]');
        if (nextBtn && !(nextBtn as HTMLButtonElement).disabled) {
          (nextBtn as HTMLElement).click();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStep, isLastStep, isFirstStep, isCompleting, nextStep, prevStep]);

  React.useEffect(() => {
    if (profile?.has_completed_onboarding) {
      resetOnboarding();
      navigate("/app/jobs");
    }

    // Asset Pre-loading
    const preloadImages = [
      "/favicon.svg",
    ];
    preloadImages.forEach((src) => {
      const img = new Image();
      img.src = src;
    });

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
        
        // Extract rich skills from parsed profile (V2 format)
        const techSkills = p.skills?.technical || [];
        if (techSkills.length > 0 && typeof techSkills[0] === 'object') {
          // Rich skills format from V2 parser
          setRichSkills(techSkills.map((s: any) => ({
            skill: s.skill,
            confidence: s.confidence || 0.5,
            years_actual: s.years_actual || null,
            context: s.context || "",
            last_used: s.last_used || null,
            verified: s.verified || false,
            related_to: s.related_to || [],
            source: s.source || "resume",
            project_count: s.project_count || 0,
          })));
        } else {
          // Old format - convert to rich skills with default values
          setRichSkills(techSkills.map((skill: string) => ({
            skill,
            confidence: 0.5,
            years_actual: null,
            context: "",
            last_used: null,
            verified: false,
            related_to: [],
            source: "resume",
            project_count: 0,
          })));
        }

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

  const handleSaveSkills = async () => {
    triggerHaptic('light');
    setIsSavingSkills(true);
    try {
      // Save skills to backend
      await api.post("/me/skills", { skills: richSkills });
      nextStep();
    } catch (err) {
      console.error(err);
      pushToast({ title: "Failed to save skills", tone: "error" });
    } finally {
      setIsSavingSkills(false);
    }
  };

  const handleSaveContact = async () => {
    try {
      setIsSavingContact(true);
      const errors: Record<string, string> = {};
      if (!contactInfo.first_name?.trim()) errors.first_name = "Required";
      if (!contactInfo.last_name?.trim()) errors.last_name = "Required";

      const emailRes = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!contactInfo.email?.trim()) {
        errors.email = "Required";
      } else if (!emailRes.test(contactInfo.email.trim())) {
        errors.email = "Invalid format";
      }

      setFormErrors(errors);
      if (Object.keys(errors).length > 0) return;

      const trimmedContact = {
        ...contactInfo,
        first_name: contactInfo.first_name.trim(),
        last_name: contactInfo.last_name.trim(),
        email: contactInfo.email.trim(),
        phone: contactInfo.phone?.trim(),
      };

      await updateProfile({
        contact: trimmedContact,
        full_name: `${trimmedContact.first_name} ${trimmedContact.last_name}`
      });
      nextStep();
    } catch (err) {
      pushToast({ title: "Failed to save contact info.", tone: "error" });
    } finally {
      setIsSavingContact(false);
    }
  };


  const calculateCompleteness = () => {
    let score = 0;
    if (profile?.resume_url || resumeFile) score += 20;
    if (contactInfo.first_name && contactInfo.email) score += 15;
    if (preferences.location) score += 10;
    if (preferences.role_type) score += 10;
    if (preferences.salary_min) score += 5;
    if (preferences.work_authorized !== undefined) score += 5;
    if (richSkills.length >= 3) score += 15;
    else if (richSkills.length > 0) score += 5;
    if (Object.keys(workStyleAnswers).length >= 6) score += 15;
    else if (Object.keys(workStyleAnswers).length >= 3) score += 5;
    return score;
  };

  const completeness = calculateCompleteness();

  const handleSavePreferences = async () => {
    try {
      setIsSavingPreferences(true);
      const errors: Record<string, string> = {};
      if (!preferences.location?.trim()) errors.location = "Required";
      if (!preferences.role_type?.trim()) errors.role_type = "Required";

      setFormErrors(errors);
      if (Object.keys(errors).length > 0) return;

      const trimmedPrefs = {
        ...preferences,
        location: preferences.location.trim(),
        role_type: preferences.role_type.trim(),
        salary_min: preferences.salary_min.trim(),
      };

      await savePreferences({
        ...trimmedPrefs,
        salary_min: parseInt(trimmedPrefs.salary_min) || 0
      } as any);

      // Update contact info separately if LinkedIn URL is provided
      if (linkedinUrl) {
        await updateProfile({
          contact: {
            linkedin_url: linkedinUrl,
            location: trimmedPrefs.location,
          }
        });
      }
      nextStep();
    } catch (err) {
      pushToast({ title: "Failed to save preferences.", tone: "error" });
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
      <div className="h-[100dvh] w-full bg-slate-50 flex flex-col relative overflow-hidden">
        <header className="px-3 md:px-6 h-11 md:h-12 shrink-0 flex items-center bg-white/80 border-b border-slate-200 z-50">
          <Skeleton className="h-6 w-24" />
        </header>
        <main className="flex-1 w-full flex flex-col items-center justify-center p-1.5 md:p-4 bg-grid-premium">
          <div className="w-full max-w-xl lg:max-w-3xl h-full flex flex-col justify-center">
            <OnboardingSkeleton />
          </div>
        </main>
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

                {currentStepData.id === "welcome" && (
                  <WelcomeStep
                    onNext={nextStep}
                    shouldReduceMotion={!!shouldReduceMotion}
                  />
                )}

                {currentStepData.id === "resume" && (
                  <ResumeStep
                    onNext={nextStep}
                    onPrev={prevStep}
                    onUpload={handleResumeUpload}
                    resumeFile={resumeFile}
                    setResumeFile={setResumeFile}
                    isUploading={isUploading}
                    resumeError={resumeError}
                    setResumeError={setResumeError}
                    linkedinUrl={linkedinUrl}
                    setLinkedinUrl={setLinkedinUrl}
                    showParsingPreview={showParsingPreview}
                    setShowParsingPreview={setShowParsingPreview}
                    parsedResume={parsedResume}
                    onConfirmParsing={handleConfirmParsing}
                    shouldReduceMotion={!!shouldReduceMotion}
                  />
                )}

                {currentStepData.id === "skill-review" && (
                  <SkillReviewStep
                    onNext={handleSaveSkills}
                    onPrev={prevStep}
                    richSkills={richSkills}
                    setRichSkills={setRichSkills}
                    isSaving={isSavingSkills}
                  />
                )}

                {currentStepData.id === "confirm-contact" && (
                  <ConfirmContactStep
                    onNext={handleSaveContact}
                    onPrev={prevStep}
                    contactInfo={contactInfo}
                    setContactInfo={setContactInfo}
                    isSavingContact={isSavingContact}
                    parsedResume={parsedResume}
                    formErrors={formErrors}
                    emailTypoSuggestion={emailTypoSuggestion}
                    onApplyEmailSuggestion={(suggestion) => {
                      setContactInfo(prev => ({
                        ...prev,
                        email: `${prev.email.split('@')[0]}@${suggestion}`
                      }));
                      setEmailTypoSuggestion(null);
                    }}
                  />
                )}

                {currentStepData.id === "preferences" && (
                  <PreferencesStep
                    onNext={handleSavePreferences}
                    onPrev={prevStep}
                    preferences={preferences}
                    setPreferences={setPreferences}
                    isSavingPreferences={isSavingPreferences}
                    aiSuggestions={aiSuggestions}
                    formErrors={formErrors}
                  />
                )}

                {currentStepData.id === "work-style" && (
                  <WorkStyleStep
                    onNext={handleSaveWorkStyle}
                    onPrev={prevStep}
                    answers={workStyleAnswers}
                    setAnswers={setWorkStyleAnswers}
                    isSaving={isSavingWorkStyle}
                  />
                )}

                {currentStepData.id === "ready" && (
                  <ReadyStep
                    onNext={handleComplete}
                    isCompleting={isCompleting}
                    contactInfo={contactInfo}
                    preferences={preferences}
                    completeness={completeness}
                    profile={profile}
                    resumeFile={resumeFile}
                    shouldReduceMotion={!!shouldReduceMotion}
                  />
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
