import * as React from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Zap, Sparkles } from "lucide-react";
import { Logo } from "../../components/brand/Logo";
import { useOnboarding } from "../../hooks/useOnboarding";
import { useProfile } from "../../hooks/useProfile";
import { useAISuggestions } from "../../hooks/useAISuggestions";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ProgressRing } from "../../components/ui/ProgressRing";
import { Confetti } from "../../components/ui/Confetti";
import { pushToast } from "../../lib/toast";
import { t, getLocale } from "../../lib/i18n";
import { api, withRetry } from "../../lib/api";
import { telemetry } from "../../lib/telemetry";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { BrowserCacheService } from "../../lib/browserCache";
import { Skeleton, OnboardingSkeleton, ResumeStepSkeleton, PreferencesStepSkeleton, SkillReviewStepSkeleton, WorkStyleStepSkeleton } from "../../components/ui/Skeleton";
import { checkEmailTypo } from "../../lib/emailUtils";
import { ErrorBoundary } from "../../components/ErrorBoundary";
import { resumeUploadRetry } from "../../lib/resumeUploadRetry";
import ResumeUploadRetry from "../../components/ui/ResumeUploadRetry";

// Step Components
import { WelcomeStep } from "./onboarding/steps/WelcomeStep";
import { ResumeStep } from "./onboarding/steps/ResumeStep";
import { SkillReviewStep } from "./onboarding/steps/SkillReviewStep";
import { ConfirmContactStep } from "./onboarding/steps/ConfirmContactStep";
import { PreferencesStep } from "./onboarding/steps/PreferencesStep";
import { WorkStyleStep } from "./onboarding/steps/WorkStyleStep";
import { CareerGoalsStep } from "./onboarding/steps/CareerGoalsStep";
import { ReadyStep } from "./onboarding/steps/ReadyStep";

// Types
import { ParsedResume, RichSkill, OnboardingFormData } from "../../types/onboarding";

// Type for preferences state - matches PreferencesStepProps
interface PreferencesState {
  location: string;
  role_type: string;
  salary_min: string;
  salary_max?: string;
  remote_only: boolean;
  onsite_only?: boolean;
  work_authorized?: boolean;
  visa_sponsorship?: boolean;
  excluded_companies?: string[];
  excluded_keywords?: string[];
}

export default function Onboarding() {
  const navigate = useNavigate();
  const { steps, currentStep, currentStepData, progress, isFirstStep, isLastStep, nextStep, prevStep, resetOnboarding, formData, updateFormData } = useOnboarding();
  const { profile, loading, uploadResume, savePreferences, completeOnboarding, updateProfile } = useProfile();
  const aiSuggestions = useAISuggestions();
  const locale = getLocale();
  const [isLowPowerMode, setIsLowPowerMode] = React.useState(false);
  const cacheService = React.useMemo(() => BrowserCacheService.getInstance(), []);
  
  // C4: Analytics Tracking - Track onboarding start
  React.useEffect(() => {
    if (!loading && profile && !profile.has_completed_onboarding) {
      telemetry.track("onboarding_started", {
        user_id: profile.id,
        step_count: steps.length,
      });
    }
  }, [loading, profile?.id, profile?.has_completed_onboarding]);
  
  // C4: Analytics Tracking - Track each step view
  React.useEffect(() => {
    if (!loading && profile && currentStepData) {
      telemetry.track("onboarding_step_viewed", {
        step_id: currentStepData.id,
        step_number: currentStep + 1,
        step_title: currentStepData.title,
        progress: Math.round(progress),
      });
    }
  }, [currentStep, currentStepData?.id, loading, profile?.id, progress]);

  React.useEffect(() => {
    // Check for save-data preference
    if (navigator.connection?.saveData) {
      setIsLowPowerMode(true);
    }

    // Check battery status if available
    let batteryObj: BatteryManager | null = null;
    let handleBatteryChange: (() => void) | null = null;
    let mounted = true;

    if (navigator.getBattery) {
      navigator.getBattery().then((battery) => {
        if (!mounted) return; // Component unmounted before promise resolved
        batteryObj = battery;
        handleBatteryChange = () => {
          setIsLowPowerMode(battery.level < 0.2 && !battery.charging);
        };

        setIsLowPowerMode(battery.level < 0.2 && !battery.charging);
        battery.addEventListener('levelchange', handleBatteryChange);
        battery.addEventListener('chargingchange', handleBatteryChange);
      });
    }

    return () => {
      mounted = false;
      // Cleanup battery event listeners
      if (batteryObj && handleBatteryChange) {
        batteryObj.removeEventListener('levelchange', handleBatteryChange);
        batteryObj.removeEventListener('chargingchange', handleBatteryChange);
      }
    };
  }, []);

  // Load cached data on component mount
  React.useEffect(() => {
    const loadCachedData = async () => {
      if (profile?.id) {
        try {
          // Load cached resume data
          const cachedResume = await cacheService.getParsedResume(profile.id);
          if (cachedResume) {
            if (import.meta.env.DEV) console.log('[Onboarding] Loading cached resume data');
            setParsedResume({
              title: cachedResume.title,
              skills: cachedResume.skills,
              years: cachedResume.years,
              summary: cachedResume.summary,
              headline: cachedResume.headline,
            });
            setParsedProfile(cachedResume.parsedProfile);
            setRichSkills(cachedResume.richSkills || []);
          }

          // Load cached skills
          const cachedSkills = await cacheService.getSkills(profile.id);
          if (cachedSkills) {
            if (import.meta.env.DEV) console.log('[Onboarding] Loading cached skills');
            setRichSkills(cachedSkills);
          }

          // Load cached preferences
          const cachedPrefs = await cacheService.getUserPreferences(profile.id);
          if (cachedPrefs) {
            if (import.meta.env.DEV) console.log('[Onboarding] Loading cached preferences');
            setPreferences(cachedPrefs);
          }
        } catch (error) {
          if (import.meta.env.DEV) console.error('[Onboarding] Error loading cached data:', error);
        }
      }
    };

    loadCachedData();
  }, [profile?.id, cacheService]);

  const shouldReduceMotion = useReducedMotion() || isLowPowerMode;

  const [resumeFile, setResumeFile] = React.useState<File | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [resumeError, setResumeError] = React.useState<string | null>(null);
  const [preferences, setPreferences] = React.useState<PreferencesState>({
    location: "",
    role_type: "",
    salary_min: "",
    salary_max: undefined,
    remote_only: false,
    onsite_only: undefined,
    work_authorized: true,
    visa_sponsorship: false,
    excluded_companies: [],
    excluded_keywords: [],
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
  // O9: onboarding_state in localStorage; no encryption — acceptable for non-PII (preferences, step index)
  const [workStyleAnswers, setWorkStyleAnswers] = React.useState<Record<string, string>>(() => {
    try {
      const stored = localStorage.getItem("onboarding_state");
      if (stored) {
        const state = JSON.parse(stored);
        return state.formData?.workStyleAnswers || {};
      }
    } catch {
      // ignore
    }
    return {};
  });
  const [isSavingWorkStyle, setIsSavingWorkStyle] = React.useState(false);

  // Career goals state
  const [careerGoals, setCareerGoals] = React.useState({
    experience_level: "",
    urgency: "",
    primary_goal: "",
    why_leaving: "",
  });
  const [isSavingCareerGoals, setIsSavingCareerGoals] = React.useState(false);

  // Step completion confetti
  const [showStepConfetti, setShowStepConfetti] = React.useState(false);
  const prevStepRef = React.useRef(currentStep);

  // Motivational copy per step — conversational, less overwhelming
  const stepMotivationalCopy: Record<string, string> = {
    welcome: "Your career transformation starts here",
    resume: "One upload, no more form-filling",
    "skill-review": "Quick check — we got most of it",
    "confirm-contact": "So employers can reach you",
    preferences: "What you want, we'll find it",
    "work-style": "A few quick questions",
    "career-goals": "Where you're headed",
    ready: "You're all set — let's go",
  };

  // Trigger confetti when stepping forward
  React.useEffect(() => {
    if (currentStep > prevStepRef.current && !shouldReduceMotion) {
      setShowStepConfetti(true);
    }
    prevStepRef.current = currentStep;
  }, [currentStep, shouldReduceMotion]);

  // Resume upload retry state
  const [showRetryComponent, setShowRetryComponent] = React.useState(false);

  // Skeleton loading states removed — shouldShowSkeleton uses direct state instead

  // Helper function to determine if current step should show skeleton
  const shouldShowSkeleton = React.useCallback(() => {
    const stepId = currentStepData.id;

    // Show skeleton during specific loading states
    switch (stepId) {
      case 'resume':
        return isUploading;
      case 'preferences':
        return isSavingPreferences ||
          aiSuggestions.roles.loading || aiSuggestions.locations.loading || aiSuggestions.salary.loading;
      case 'skill-review':
        return isSavingSkills;
      case 'confirm-contact':
        return isSavingContact;
      case 'work-style':
        return isSavingWorkStyle;
      default:
        return false;
    }
  }, [
    currentStepData.id,
    isUploading,
    isSavingPreferences,
    isSavingSkills,
    isSavingContact,
    isSavingWorkStyle,
    aiSuggestions.roles.loading,
    aiSuggestions.locations.loading,
    aiSuggestions.salary.loading
  ]);

  // Helper function to get the appropriate skeleton component
  const getSkeletonComponent = React.useCallback(() => {
    const stepId = currentStepData.id;

    switch (stepId) {
      case 'resume':
        return <ResumeStepSkeleton />;
      case 'preferences':
        return <PreferencesStepSkeleton />;
      case 'skill-review':
        return <SkillReviewStepSkeleton />;
      case 'work-style':
        return <WorkStyleStepSkeleton />;
      default:
        return <OnboardingSkeleton />;
    }
  }, [currentStepData.id]);

  // Restore local state from formData on mount and step changes (for back navigation persistence)
  // Only restores; does NOT call updateFormData to avoid dependency loop
  React.useEffect(() => {
    if (formData.linkedinUrl && linkedinUrl !== formData.linkedinUrl) {
      setLinkedinUrl(formData.linkedinUrl);
    }
    if (formData.workStyleAnswers && JSON.stringify(workStyleAnswers) !== JSON.stringify(formData.workStyleAnswers)) {
      setWorkStyleAnswers(formData.workStyleAnswers);
    }
    if (formData.parsedResume && (!parsedResume || JSON.stringify(parsedResume) !== JSON.stringify(formData.parsedResume))) {
      setParsedResume(formData.parsedResume);
    }
    if (formData.parsedProfile && (!parsedProfile || JSON.stringify(parsedProfile) !== JSON.stringify(formData.parsedProfile))) {
      setParsedProfile(formData.parsedProfile);
    }
    if (formData.richSkills && (!richSkills.length || JSON.stringify(richSkills) !== JSON.stringify(formData.richSkills))) {
      setRichSkills(formData.richSkills);
    }
    if (formData.showParsingPreview !== undefined && showParsingPreview !== formData.showParsingPreview) {
      setShowParsingPreview(formData.showParsingPreview);
    }
  }, [currentStep, formData, linkedinUrl, workStyleAnswers, parsedResume, parsedProfile, richSkills, showParsingPreview]);

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
      const hasAnswers = Object.keys(workStyleAnswers).some((k) => workStyleAnswers[k]);
      if (hasAnswers) {
        if (import.meta.env.DEV) console.log('[Onboarding] Saving work style:', workStyleAnswers);
        await api.post("/me/work-style", workStyleAnswers);
        pushToast({ title: "Work style saved!", tone: "success" });
        telemetry.track("AI Learned Work Style", {
          answersCount: Object.keys(workStyleAnswers).length,
          hasAutonomyPreference: !!workStyleAnswers.autonomy_preference,
          hasLearningStyle: !!workStyleAnswers.learning_style,
          hasCompanyStagePreference: !!workStyleAnswers.company_stage_preference,
          hasCommunicationStyle: !!workStyleAnswers.communication_style,
          hasPacePreference: !!workStyleAnswers.pace_preference,
          hasOwnershipPreference: !!workStyleAnswers.ownership_preference,
          hasCareerTrajectory: !!workStyleAnswers.career_trajectory,
        });
      }
      nextStep();
    } catch (error) {
      const err = error as Error;
      if (import.meta.env.DEV) console.error('[Onboarding] Failed to save work style:', err);
      let message = "Failed to save work style";
      if (typeof (err as Error).message === 'string' && !err.message.includes('[object')) {
        message = err.message;
      }
      pushToast({ title: "Failed to save work style", description: message, tone: "error" });
    } finally {
      setIsSavingWorkStyle(false);
    }
  };

  // O17: Profile API returns onsite_acceptable; we map to onsite_only for internal state (API expects onsite_only)
  React.useEffect(() => {
    if (profile?.preferences) {
      const p = profile.preferences;
      setPreferences({
        location: p.location ?? "",
        role_type: p.role_type ?? "",
        salary_min: p.salary_min ? String(p.salary_min) : "",
        salary_max: p.salary_max ? String(p.salary_max) : "",
        remote_only: p.remote_only ?? false,
        onsite_only: p.onsite_only ?? false,
        work_authorized: p.work_authorized ?? true,
        visa_sponsorship: p.visa_sponsorship ?? false,
        excluded_companies: p.excluded_companies ?? [],
        excluded_keywords: p.excluded_keywords ?? [],
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

  // Persist internal states to useOnboarding's formData for refresh persistence
  // Separate from restore effect to avoid dependency loop (formData not in deps)
  // FIXED: Use debouncing and ref to prevent infinite loop
  const prevValuesRef = React.useRef<string>('');
  const updateTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  
  React.useEffect(() => {
    // Clear any pending update
    if (updateTimeoutRef.current) {
      clearTimeout(updateTimeoutRef.current);
    }
    
    // Debounce the update to prevent rapid re-renders
    updateTimeoutRef.current = setTimeout(() => {
      const currentValues = JSON.stringify({
        contactInfo,
        preferences,
        linkedinUrl,
        workStyleAnswers,
        parsedResume,
        parsedProfile,
        richSkills,
        showParsingPreview,
      });
      
      // Only update if values actually changed
      if (currentValues !== prevValuesRef.current) {
        updateFormData({
          contactInfo,
          preferences,
          linkedinUrl,
          workStyleAnswers,
          parsedResume,
          parsedProfile,
          richSkills,
          showParsingPreview,
        });
        prevValuesRef.current = currentValues;
      }
    }, 100); // 100ms debounce
    
    return () => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contactInfo, preferences, linkedinUrl, workStyleAnswers, parsedResume, parsedProfile, richSkills, showParsingPreview]);

  // OB4: Resume Where You Left Off - Show banner for returning users
  React.useEffect(() => {
    if (profile && !profile.has_completed_onboarding && currentStep > 0) {
      const welcomeKey = `has_welcomed_back_${profile.id || 'anon'}`;
      const hasWelcomed = sessionStorage.getItem(welcomeKey);
      if (!hasWelcomed) {
        const locale = getLocale();
        pushToast({
          title: t("onboarding.welcomeBack", locale) || "Welcome back!",
          description: t("onboarding.pickingUpAt", locale).replace("{step}", currentStepData.title) || `Picking up at: ${currentStepData.title}`,
          tone: "info"
        });
        sessionStorage.setItem(welcomeKey, "true");
      }
    }
  }, [profile?.id, currentStep, currentStepData.title]); // Re-run when step changes to show updated step info

  // Handle email typo check (FV1: debounce to avoid flicker while typing)
  React.useEffect(() => {
    if (!contactInfo.email) {
      setEmailTypoSuggestion(null);
      return;
    }
    const timer = setTimeout(() => {
      const suggestion = checkEmailTypo(contactInfo.email);
      setEmailTypoSuggestion(suggestion);
    }, 400);
    return () => clearTimeout(timer);
  }, [contactInfo.email]);

  // O4: Keyboard shortcuts — use ref to step container for robust button lookup
  const stepContainerRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
        if (!(e.ctrlKey && e.key === 'Enter')) return;
      }

      if (e.ctrlKey && e.key === 'Enter') {
        if (isLastStep) {
          globalThis.dispatchEvent(new CustomEvent('onboarding:complete'));
        } else {
          const nextBtn = stepContainerRef.current?.querySelector<HTMLButtonElement>('[data-onboarding-next]:not([disabled])');
          if (nextBtn) nextBtn.click();
          else globalThis.dispatchEvent(new CustomEvent('onboarding:next'));
        }
      } else if (e.altKey && e.key === 'ArrowLeft') {
        if (!isFirstStep) globalThis.dispatchEvent(new CustomEvent('onboarding:prev'));
      } else if (e.altKey && e.key === 'ArrowRight') {
        const nextBtn = stepContainerRef.current?.querySelector<HTMLButtonElement>('[data-onboarding-next]:not([disabled])');
        if (nextBtn) nextBtn.click();
      }
    };

    globalThis.addEventListener('keydown', handleKeyDown);
    return () => globalThis.removeEventListener('keydown', handleKeyDown);
  }, [isLastStep, isFirstStep]);

  // Onboarding completion guard - redirect if already completed
  React.useEffect(() => {
    if (profile?.has_completed_onboarding) {
      // C4: Analytics Tracking - Track onboarding abandonment (user already completed)
      telemetry.track("onboarding_abandoned", {
        reason: "already_completed",
        current_step: currentStep,
      });
      // Clear onboarding state and redirect to dashboard
      resetOnboarding();
      // Use replace to prevent back navigation to onboarding
      navigate("/app/dashboard", { replace: true });
      pushToast({
        title: t("onboarding.alreadyComplete", getLocale()) || "Already set up",
        description: t("onboarding.redirectingToDashboard", getLocale()) || "Redirecting to your dashboard...",
        tone: "info"
      });
    }
  }, [profile, navigate, resetOnboarding, currentStep]);

  // O25: Backend rate limits magic-link (auth.py), profile writes (user.py), and AI endpoints (ai_rate_limiting.py)
  // O14: Asset preloading (favicon + critical fonts for LCP)
  React.useEffect(() => {
    ["/favicon.svg"].forEach((src) => {
      const img = new Image();
      img.src = src;
    });
    const fontUrl = "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Instrument+Serif:ital@0;1&display=swap";
    if (!document.querySelector('link[rel="preload"][as="style"][href*="fonts.googleapis.com"]')) {
      const link = document.createElement("link");
      link.rel = "preload";
      link.as = "style";
      link.href = fontUrl;
      document.head.appendChild(link);
    }
  }, []);

  const handleResumeNext = async () => {
    // Persist LinkedIn URL when leaving Resume step (not only at Preferences)
    const trimmed = linkedinUrl?.trim();
    if (trimmed && /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+/i.test(trimmed)) {
      try {
        await updateProfile({ contact: { linkedin_url: trimmed } });
      } catch (e) {
        if (import.meta.env.DEV) console.warn("[Onboarding] Failed to persist LinkedIn:", e);
      }
    }
    nextStep();
  };

  const handleResumeUpload = async (file?: File) => {
    const uploadFile = file || resumeFile;
    if (!uploadFile) return;

    setIsUploading(true);
    setResumeError(null);

    try {
      // Use retry with backoff for better reliability
      const data = await retryWithBackoff(async () => {
        return await uploadResume(uploadFile);
      }, 3, 1000);

      pushToast({ title: "Resume uploaded!", tone: "success" });

      if (data.parsed_profile) {
        const p = data.parsed_profile;
        if (import.meta.env.DEV) console.log('[Onboarding] Parsed profile:', p);

        // Cache parsed resume data for future use
        const resumeData: {
          title: string | undefined;
          skills: string[];
          years: number;
          summary: string | undefined;
          headline: string | undefined;
          parsedProfile: typeof data.parsed_profile;
          richSkills: RichSkill[] | null;
        } = {
          title: p.headline || (p.experience?.[0]?.title),
          skills: (p.skills?.technical || []).filter((s: unknown) => typeof s === 'string').slice(0, 5),
          years: p.experience?.length || 0,
          summary: p.summary,
          headline: p.headline,
          parsedProfile: data.parsed_profile,
          richSkills: null
        };

        // Extract rich skills from parsed profile (V2 format)
        const techSkills = p.skills?.technical || [];
        if (import.meta.env.DEV) {
          console.log('[Onboarding] Tech skills raw:', techSkills);
          console.log('[Onboarding] First skill type:', techSkills.length > 0 ? typeof techSkills[0] : 'empty');
        }

        if (techSkills.length > 0 && typeof techSkills[0] === 'object' && techSkills[0] !== null) {
          // Rich skills format from V2 parser
          const parsedSkills: RichSkill[] = techSkills.map((s: RichSkill | string) => (
            typeof s === 'string' ? {
              skill: s,
              confidence: 0.5,
              years_actual: null,
              context: "",
              last_used: null,
              verified: false,
              related_to: [],
              source: "resume",
              project_count: 0,
            } : {
              skill: s.skill || String(s),
              confidence: typeof s.confidence === 'number' ? s.confidence : 0.5,
              years_actual: s.years_actual || null,
              context: s.context || "",
              last_used: s.last_used || null,
              verified: s.verified || false,
              related_to: s.related_to || [],
              source: s.source || "resume",
              project_count: s.project_count || 0,
            }
          ));
          if (import.meta.env.DEV) console.log('[Onboarding] Parsed rich skills:', parsedSkills);
          setRichSkills(parsedSkills);
          resumeData.richSkills = parsedSkills;
        } else {
          // Old format - convert to rich skills with default values
          if (import.meta.env.DEV) console.log('[Onboarding] Using old format for skills');
          const parsedSkills = techSkills.map((skill: string) => ({
            skill,
            confidence: 0.5,
            years_actual: null,
            context: "",
            last_used: null,
            verified: false,
            related_to: [],
            source: "resume",
            project_count: 0,
          }));
          setRichSkills(parsedSkills);
          resumeData.richSkills = parsedSkills;
        }

        // Cache the resume data
        await cacheService.cacheParsedResume(profile?.id || 'anonymous', resumeData);

        setParsedResume({
          title: resumeData.title,
          skills: resumeData.skills,
          years: resumeData.years,
          summary: resumeData.summary,
          headline: resumeData.headline,
        });
        setShowParsingPreview(true);

        // Store the full parsed profile for AI suggestions
        // Cast to satisfy state type (Record<string,unknown>) — the shape is compatible at runtime
        setParsedProfile(data.parsed_profile as unknown as Record<string, unknown>);

        // Fetch AI suggestions in background (don't block)
        aiSuggestions.fetchAllSuggestions(
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          data.parsed_profile as any,
          data.preferences?.location || (data.contact as any)?.location || ""
        ).catch(() => {
          // Non-critical failure
          if (import.meta.env.DEV) console.log("AI suggestions fetch failed, will continue without");
        });

        // Track AI learning event
        telemetry.track("AI Learned Resume Data", {
          hasSkills: !!data.parsed_profile.skills,
          skillCount: data.parsed_profile.skills?.technical?.length || 0,
          hasExperience: !!data.parsed_profile.experience,
          experienceYears: data.parsed_profile.experience?.length || 0,
          hasEducation: !!data.parsed_profile.education,
        });
      }

      // Clear any retry metadata on success
      await resumeUploadRetry.clearMetadata();
      setShowRetryComponent(false);

    } catch (error) {
      const err = error as Error & { status?: number };
      const message = err.message;
      const status = err.status;
      if (import.meta.env.DEV) console.error("Resume upload failed:", err);

      // Save metadata for retry
      await resumeUploadRetry.saveResumeMetadata(uploadFile, message);
      await resumeUploadRetry.updateAfterFailure(message);
      setShowRetryComponent(true);

      // OB2: Improve Resume Upload Error Messages - Provide actionable recovery steps
      let userFriendlyMessage = message;
      if (status === 413) {
        userFriendlyMessage = "File is too large. Please use a PDF under 15MB and try again.";
      } else if (status === 400) {
        userFriendlyMessage = "Invalid file format. Please upload a PDF resume.";
      } else if (status && status >= 500) {
        userFriendlyMessage = "Server error. Your file was saved and will retry automatically. Check back in a moment.";
      } else if (message.includes("network") || message.includes("timeout")) {
        userFriendlyMessage = "Network error. Your file was saved and will retry when connection is restored.";
      } else if (!message || message === "Upload failed") {
        userFriendlyMessage = "Upload failed. Your file was saved and will retry automatically. You can also try again manually.";
      }
      
      setResumeError(userFriendlyMessage);
      pushToast({
        title: "Upload failed",
        description: userFriendlyMessage,
        tone: "error"
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Handle retry from the retry component
  const handleResumeRetry = async () => {
    const storedFile = await resumeUploadRetry.getStoredFile();
    if (storedFile) {
      setResumeFile(storedFile);
      await handleResumeUpload(storedFile);
    }
  };

  // Handle clearing retry state
  const handleClearRetry = () => {
    resumeUploadRetry.clearMetadata();
    setShowRetryComponent(false);
    setResumeError(null);
  };

  const handleConfirmParsing = async () => {
    setShowParsingPreview(false);
    await handleResumeNext();
  };

  // Using withRetry from api.ts for consistent retry logic with network error handling
  const retryWithBackoff = async <T,>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> => {
    return withRetry(fn, {
      maxRetries,
      baseDelayMs: delay,
      shouldRetry: (err: Error & { status?: number }) => {
        const isNetworkError = !navigator.onLine || (err.status !== undefined && err.status >= 500);
        if (!isNetworkError) return false; // Don't retry client errors
        return true;
      },
      onRetry: (err, attempt) => {
        if (import.meta.env.DEV) console.log("[Onboarding] Retry", attempt + 1 + "/" + maxRetries, ":", err);
      },
    });
  };

  const handleSaveSkills = async () => {
    triggerHaptic('light');
    setIsSavingSkills(true);
    try {
      // Cache skills data
      await cacheService.cacheSkills(profile?.id || 'anonymous', richSkills);

      // Save skills to backend with retry logic
      if (import.meta.env.DEV) console.log('[Onboarding] Saving skills:', richSkills);
      const result = await retryWithBackoff(() =>
        api.post<{ status: string; count: number }>("/me/skills", { skills: richSkills })
      );
      if (import.meta.env.DEV) console.log('[Onboarding] Skills saved:', result);
      pushToast({ title: "Skills saved!", tone: "success" });
      nextStep();
    } catch (error) {
      const err = error as Error & { status?: number };
      if (import.meta.env.DEV) console.error('[Onboarding] Failed to save skills:', err);
      const isNetworkError = !navigator.onLine || (err.status && err.status >= 500);
      let message = "Failed to save skills";
      if (isNetworkError) {
        message = "Network error. Please check your connection and try again.";
      } else if (typeof (err as Error).message === 'string' && !err.message.includes('[object')) {
        message = err.message;
      }
      pushToast({
        title: "Failed to save skills",
        description: message,
        tone: "error"
      });
    } finally {
      setIsSavingSkills(false);
    }
  };

  const handleSaveContact = async () => {
    // Validate first before setting loading state
    const errors: Record<string, string> = {};
    if (!contactInfo.first_name?.trim()) errors.first_name = "Required";
    if (!contactInfo.last_name?.trim()) errors.last_name = "Required";

    const emailRes = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!contactInfo.email?.trim()) {
      errors.email = "Required";
    } else if (!emailRes.test(contactInfo.email.trim())) {
      errors.email = "Invalid format";
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    // Clear any previous errors and set loading
    setFormErrors({});
    setIsSavingContact(true);

    try {
      const trimmedContact = {
        ...contactInfo,
        first_name: contactInfo.first_name.trim(),
        last_name: contactInfo.last_name.trim(),
        email: contactInfo.email.trim(),
        phone: contactInfo.phone?.trim(),
      };

      await retryWithBackoff(() => updateProfile({
        contact: trimmedContact,
        full_name: `${trimmedContact.first_name} ${trimmedContact.last_name}`
      }));
      pushToast({ title: "Contact info saved!", tone: "success" });

      // Track AI learning event
      if (import.meta.env.DEV) console.log("[Telemetry] AI Learned Contact Info", {
        hasFirstName: !!trimmedContact.first_name,
        hasLastName: !!trimmedContact.last_name,
        hasEmail: !!trimmedContact.email,
        hasPhone: !!trimmedContact.phone,
        hasLinkedIn: !!linkedinUrl,
      });

      nextStep();
    } catch (error) {
      const err = error as Error & { status?: number };
      if (import.meta.env.DEV) console.error('[Onboarding] Failed to save contact:', err);
      const isNetworkError = !navigator.onLine || (err.status && err.status >= 500);
      let message = "Please try again";
      if (isNetworkError) {
        message = "Network error. Please check your connection and try again.";
      } else if (typeof (err as Error).message === 'string' && !err.message.includes('[object')) {
        message = err.message;
      }
      pushToast({
        title: "Failed to save contact info",
        description: message,
        tone: "error"
      });
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
    // Validate first before setting loading state
    const errors: Record<string, string> = {};
    if (!preferences.location?.trim()) errors.location = "Required";
    if (!preferences.role_type?.trim()) errors.role_type = "Required";

    const SALARY_CAP = 10_000_000;
    if (preferences.salary_min?.trim()) {
      const salaryNum = Number.parseInt(preferences.salary_min.trim());
      if (Number.isNaN(salaryNum) || salaryNum < 0) {
        errors.salary_min = "Must be a valid number";
      } else if (salaryNum > SALARY_CAP) {
        errors.salary_min = `Min salary cannot exceed $${(SALARY_CAP / 1_000_000).toFixed(0)}M`;
      }
    }
    if (preferences.salary_max?.trim()) {
      const maxNum = Number.parseInt(preferences.salary_max.trim());
      const minNum = preferences.salary_min?.trim() ? Number.parseInt(preferences.salary_min.trim()) : 0;
      if (Number.isNaN(maxNum) || maxNum < 0) {
        errors.salary_max = "Must be a valid number";
      } else if (maxNum > SALARY_CAP) {
        errors.salary_max = `Max salary cannot exceed $${(SALARY_CAP / 1_000_000).toFixed(0)}M`;
      } else if (minNum > 0 && maxNum < minNum) {
        errors.salary_max = "Max must be ≥ min";
      }
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    // Clear any previous errors and set loading
    setFormErrors({});
    setIsSavingPreferences(true);

    try {
      const trimmedPrefs = {
        ...preferences,
        location: preferences.location.trim(),
        role_type: preferences.role_type.trim(),
        salary_min: preferences.salary_min.trim(),
      };

      // Cache preferences data
      await cacheService.cacheUserPreferences(profile?.id || 'anonymous', trimmedPrefs);

      const prefs: import("../../hooks/useProfile").Preferences = {
        location: trimmedPrefs.location,
        role_type: trimmedPrefs.role_type,
        salary_min: Number.parseInt(trimmedPrefs.salary_min) || 0,
        salary_max: trimmedPrefs.salary_max?.trim() ? Number.parseInt(trimmedPrefs.salary_max.trim()) : undefined,
        remote_only: trimmedPrefs.remote_only,
        onsite_only: trimmedPrefs.onsite_only,
        work_authorized: trimmedPrefs.work_authorized,
        visa_sponsorship: trimmedPrefs.visa_sponsorship,
        excluded_companies: trimmedPrefs.excluded_companies,
        excluded_keywords: trimmedPrefs.excluded_keywords,
      };
      await savePreferences(prefs);

      // Update contact info separately if LinkedIn URL is provided
      if (linkedinUrl) {
        await updateProfile({
          contact: {
            linkedin_url: linkedinUrl,
            location: trimmedPrefs.location,
          }
        });
      }
      pushToast({ title: "Preferences saved!", tone: "success" });

      // Track AI learning event
      if (import.meta.env.DEV) {
        if (import.meta.env.DEV) console.log("[Telemetry] AI Learned Job Preferences", {
          location: trimmedPrefs.location,
          roleType: trimmedPrefs.role_type,
          salaryMin: Number.parseInt(trimmedPrefs.salary_min, 10) || 0,
          remoteOnly: trimmedPrefs.remote_only,
          onsiteOnly: trimmedPrefs.onsite_only,
          workAuthorized: trimmedPrefs.work_authorized,
          visaSponsorship: trimmedPrefs.visa_sponsorship,
          excludedCompaniesCount: trimmedPrefs.excluded_companies?.length || 0,
          excludedKeywordsCount: trimmedPrefs.excluded_keywords?.length || 0,
        });
      }

      nextStep();
    } catch (error) {
      const err = error as Error & { status?: number };
      if (import.meta.env.DEV) console.error("[Onboarding] Failed to save preferences:", err);
      pushToast({
        title: "Failed to save preferences",
        description: (typeof err.message === 'string' && !err.message.includes('[object')) ? err.message : "Please try again",
        tone: "error"
      });
    } finally {
      setIsSavingPreferences(false);
    }
  };

  const handleSaveCareerGoals = async () => {
    try {
      setIsSavingCareerGoals(true);
      // Save career goals to profile
      await updateProfile({
        career_goals: {
          experience_level: careerGoals.experience_level,
          urgency: careerGoals.urgency,
          primary_goal: careerGoals.primary_goal,
          why_leaving: careerGoals.why_leaving,
        }
      });
      updateFormData({ careerGoals });
      pushToast({ title: "Career goals saved!", tone: "success" });
      nextStep();
    } catch (error) {
      const err = error as Error & { status?: number };
      if (import.meta.env.DEV) console.error('[Onboarding] Failed to save career goals:', err);
      pushToast({
        title: "Failed to save career goals",
        description: (typeof err.message === 'string' && !err.message.includes('[object')) ? err.message : "Please try again",
        tone: "error"
      });
    } finally {
      setIsSavingCareerGoals(false);
    }
  };

  const handleComplete = async () => {
    try {
      setIsCompleting(true);
      // O20: Validation before completion (names, email) handled by useProfile hook
      await completeOnboarding();

      // NEW: Call the growth endpoint to process referrals and bonus apps
      try {
        await api.post("/onboarding/complete", {});
      } catch (growthErr) {
        // Non-critical if growth endpoint fails, but log it
        if (import.meta.env.DEV) console.warn("[Onboarding] Growth endpoint failed but profile marked complete:", growthErr);
      }

      resetOnboarding();
      sessionStorage.setItem("onboarding_just_completed", "true");
      sessionStorage.setItem("show_first_steps", "true");
      // C4: Analytics Tracking - Track onboarding completion
      telemetry.track("onboarding_completed", { 
        step: "ready",
        total_steps: steps.length,
        final_progress: Math.round(progress),
        has_resume: !!profile?.resume_url,
        has_skills: richSkills.length > 0,
        has_preferences: !!preferences.location && !!preferences.role_type,
      });
      pushToast({ title: t("onboarding.allSet", locale) || "You're all set! Let's job hunt!", tone: "success" });
      navigate("/app/dashboard");
    } catch (error) {
      const err = error as Error & { status?: number };
      if (import.meta.env.DEV) console.error('[Onboarding] Failed to complete:', err);
      pushToast({
        title: t("onboarding.almostThere", locale) || "Almost there!",
        description: (typeof err.message === 'string' && !err.message.includes('[object')) ? err.message : (t("onboarding.somethingWrong", locale) || "Something went wrong. Please try again."),
        tone: "error"
      });
    } finally {
      setIsCompleting(false);
    }
  };

  if (loading) {
    return (
      <div className="h-[100dvh] w-full bg-[#F7F6F3] flex flex-col relative overflow-hidden">
        <header className="px-3 md:px-6 h-11 md:h-12 shrink-0 flex items-center bg-white/90 backdrop-blur-sm border-b border-[#E9E9E7] z-50">
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
    <div className="min-h-screen w-full bg-[#F7F6F3] flex flex-col relative">
      <ErrorBoundary>
        <Confetti active={showStepConfetti} onComplete={() => setShowStepConfetti(false)} />
        {/* Minimal Header */}
        <header className="px-3 md:px-6 h-11 md:h-12 shrink-0 flex items-center justify-between bg-white/90 backdrop-blur-sm border-b border-[#E9E9E7] z-50 sticky top-0">
          <Logo to="/app/onboarding" size="sm" />
          <div className="flex items-center gap-2 md:gap-4">
            {/* OB1: Progress Persistence Warning - Show auto-save indicator */}
            <div className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-50 border border-emerald-200">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" aria-hidden />
              <span className="text-[9px] font-medium text-emerald-700">
                {t("onboarding.autoSaved", locale) || "Auto-saved"}
              </span>
            </div>
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#455DD3]/10 border border-[#455DD3]/20">
              <div className="w-2 h-2 rounded-full bg-[#455DD3] animate-pulse" aria-hidden />
              <span className="text-[10px] font-black text-[#455DD3] uppercase tracking-widest">{t("onboarding.settingUpProfile", locale) || "Setting up your profile"}</span>
            </div>
            <div className="lg:hidden flex items-center gap-1.5 px-2 py-1 rounded-full bg-[#455DD3]/10 border border-[#455DD3]/20">
              <div className="w-1.5 h-1.5 rounded-full bg-[#455DD3] animate-pulse" aria-hidden />
              <span className="text-[9px] font-black text-[#455DD3] uppercase tracking-wider">{t("onboarding.setup", locale) || "Setup"}</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => { if (globalThis.confirm(t("onboarding.confirmRestart", locale) || 'Are you sure? This will clear your progress.')) resetOnboarding(); }} className="text-[#787774] text-[10px] md:text-xs font-bold uppercase hover:bg-[#E9E9E7]" title={t("onboarding.clearProgress", locale) || "Clear progress and start over"} aria-label={t("onboarding.restartOnboarding", locale) || "Restart onboarding and clear progress"}>
              {t("onboarding.restart", locale) || "Restart"}
            </Button>
          </div>
        </header>

        <main className="flex-1 w-full flex flex-col items-center p-4 md:p-6 lg:p-8" id="main-content" aria-label="Onboarding">
          <div className="w-full max-w-xl lg:max-w-4xl xl:max-w-5xl">
            {/* Progress bar */}
            <div className="mb-4 md:mb-6" role="progressbar" aria-valuenow={currentStep + 1} aria-valuemin={1} aria-valuemax={steps.length} aria-label={`Setup progress: step ${currentStep + 1} of ${steps.length}`}>
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-[10px] md:text-xs font-bold text-[#9B9A97] uppercase tracking-wider">
                  {t("onboarding.step", locale) || "Step"} {currentStep + 1} {t("onboarding.of", locale) || "of"} {steps.length} — {(progress).toFixed(0)}%
                </span>
                <span className="text-[10px] md:text-xs font-bold text-[#455DD3] uppercase tracking-wider">{currentStepData.title}</span>
              </div>
              {/* OB1: Progress Persistence Warning - Show auto-save indicator */}
              <div className="flex items-center gap-1.5 mb-2 px-1">
                <div className="flex items-center gap-1 text-[9px] text-emerald-600 font-medium">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" aria-hidden />
                  <span>
                    {t("onboarding.progressAutoSaved", locale) || "Your progress is saved automatically"}
                  </span>
                </div>
              </div>
              <div className="h-1.5 w-full rounded-full bg-[#E9E9E7] overflow-hidden">
                <motion.div
                  initial={shouldReduceMotion ? { width: `${progress}%` } : { width: 0 }}
                  animate={{ width: `${progress}%` }}
                  className="h-full bg-[#455DD3]"
                  transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                />
              </div>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                ref={stepContainerRef}
                key={currentStep}
                initial={shouldReduceMotion ? undefined : { opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={shouldReduceMotion ? undefined : { opacity: 0 }}
                transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.2 }}
                className="w-full"
              >
                <Card tone="glass" shadow="lift" className="p-4 md:p-6 lg:p-8 border-[#E9E9E7] bg-white/95">
                  {/* ProgressRing + Motivational Copy */}
                  <div className="mb-4 md:mb-6 flex flex-col items-center">
                    <ProgressRing
                      progress={completeness}
                      stepLabel={`${currentStep + 1} of ${steps.length}`}
                      size={100}
                      strokeWidth={5}
                    />
                    <p className="mt-2 text-xs md:text-sm font-bold text-[#787774] text-center max-w-xs">
                      {stepMotivationalCopy[currentStepData.id] || t("onboarding.buildingProfile", locale) || "Building your profile"}
                    </p>
                    {/* Completion badges */}
                    <div className="flex flex-wrap gap-1.5 mt-3 justify-center">
                      {(profile?.resume_url || resumeFile) && (
                        <Badge className="text-[8px] font-bold uppercase tracking-wider bg-[#17BEBB]/10 text-[#17BEBB] border-[#17BEBB]/20 px-1.5 py-0.5">
                          <CheckCircle2 className="mr-0.5 h-2.5 w-2.5" aria-hidden />
                          {t("onboarding.resumeBadge", locale) || "Resume"}
                        </Badge>
                      )}
                      {preferences.location && (
                        <Badge className="text-[8px] font-bold uppercase tracking-wider bg-[#17BEBB]/10 text-[#17BEBB] border-[#17BEBB]/20 px-1.5 py-0.5">
                          <CheckCircle2 className="mr-0.5 h-2.5 w-2.5" aria-hidden />
                          {t("onboarding.locationBadge", locale) || "Location"}
                        </Badge>
                      )}
                      {preferences.role_type && (
                        <Badge className="text-[8px] font-bold uppercase tracking-wider bg-[#17BEBB]/10 text-[#17BEBB] border-[#17BEBB]/20 px-1.5 py-0.5">
                          <CheckCircle2 className="mr-0.5 h-2.5 w-2.5" aria-hidden />
                          {t("onboarding.roleBadge", locale) || "Role"}
                        </Badge>
                      )}
                      {richSkills.length > 0 && (
                        <Badge className="text-[8px] font-bold uppercase tracking-wider bg-[#17BEBB]/10 text-[#17BEBB] border-[#17BEBB]/20 px-1.5 py-0.5">
                          <CheckCircle2 className="mr-0.5 h-2.5 w-2.5" aria-hidden />
                          {t("onboarding.skillsBadge", locale) || "Skills"}
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Step Content with Skeleton Loading */}
                  <AnimatePresence mode="wait">
                    {shouldShowSkeleton() ? (
                      <motion.div
                        key="skeleton"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        {getSkeletonComponent()}
                      </motion.div>
                    ) : (
                      <motion.div
                        key="content"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        {currentStepData.id === "welcome" && (
                          <WelcomeStep
                            onNext={nextStep}
                            shouldReduceMotion={!!shouldReduceMotion}
                            firstName={profile?.contact?.first_name}
                          />
                        )}

                        {currentStepData.id === "resume" && (
                          <>
                            <ResumeStep
                              onNext={handleResumeNext}
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
                              onResetParsingState={() => {
                                setParsedResume(null);
                                setParsedProfile(null);
                                setRichSkills([]);
                              }}
                            />

                            {/* Resume Upload Retry Component */}
                            <AnimatePresence>
                              {showRetryComponent && (
                                <motion.div
                                  initial={{ opacity: 0, y: 20 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  exit={{ opacity: 0, y: -20 }}
                                  transition={{ duration: 0.3 }}
                                  className="mt-4"
                                >
                                  <ResumeUploadRetry
                                    onRetry={handleResumeRetry}
                                    onClear={handleClearRetry}
                                  />
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </>
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
                            onClearError={(field) => setFormErrors(prev => {
                              const updated = { ...prev };
                              delete updated[field];
                              return updated;
                            })}
                            onSetFormError={(field, error) => setFormErrors(prev => ({
                              ...prev,
                              [field]: error
                            }))}
                          />
                        )}

                        {currentStepData.id === "preferences" && (
                          <PreferencesStep
                            onNext={handleSavePreferences}
                            onPrev={prevStep}
                            preferences={preferences}
                            setPreferences={setPreferences}
                            isSavingPreferences={isSavingPreferences}
                            aiSuggestions={{
                              roles: aiSuggestions.roles.data,
                              salary: aiSuggestions.salary.data,
                              locations: aiSuggestions.locations.data,
                            }}
                            formErrors={formErrors}
                            hasParsedProfile={!!parsedProfile}
                            onClearError={(field) => setFormErrors(prev => {
                              const updated = { ...prev };
                              delete updated[field];
                              return updated;
                            })}
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

                        {currentStepData.id === "career-goals" && (
                          <CareerGoalsStep
                            onNext={handleSaveCareerGoals}
                            onPrev={prevStep}
                            careerGoals={careerGoals}
                            setCareerGoals={setCareerGoals}
                            isSaving={isSavingCareerGoals}
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
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </ErrorBoundary>
    </div>
  );
}
