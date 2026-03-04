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
import { t, getLocale } from "../../lib/i18n";
import { api } from "../../lib/api";
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
  const [isLowPowerMode, setIsLowPowerMode] = React.useState(false);
  const cacheService = React.useMemo(() => BrowserCacheService.getInstance(), []);

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

  // Resume upload retry state
  const [showRetryComponent, setShowRetryComponent] = React.useState(false);

  // Skeleton loading states for better UX
  const [stepLoadingStates] = React.useState<Record<string, boolean>>({});

  // Helper function to determine if current step should show skeleton
  const shouldShowSkeleton = React.useCallback(() => {
    const stepId = currentStepData.id;

    // Show skeleton during specific loading states
    switch (stepId) {
      case 'resume':
        return isUploading || stepLoadingStates[stepId];
      case 'preferences':
        return isSavingPreferences || stepLoadingStates[stepId] ||
          aiSuggestions.roles.loading || aiSuggestions.locations.loading || aiSuggestions.salary.loading;
      case 'skill-review':
        return isSavingSkills || stepLoadingStates[stepId];
      case 'confirm-contact':
        return isSavingContact || stepLoadingStates[stepId];
      case 'work-style':
        return isSavingWorkStyle || stepLoadingStates[stepId];
      default:
        return stepLoadingStates[stepId];
    }
  }, [
    currentStepData.id,
    isUploading,
    isSavingPreferences,
    isSavingSkills,
    isSavingContact,
    isSavingWorkStyle,
    stepLoadingStates,
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

  // Restore data from formData on mount and step changes (for back navigation persistence)
  React.useEffect(() => {
    // Restore linkedinUrl
    if (formData.linkedinUrl && linkedinUrl !== formData.linkedinUrl) {
      setLinkedinUrl(formData.linkedinUrl);
    }
    // Restore workStyleAnswers
    if (formData.workStyleAnswers && JSON.stringify(workStyleAnswers) !== JSON.stringify(formData.workStyleAnswers)) {
      setWorkStyleAnswers(formData.workStyleAnswers);
    }
    // Restore parsed resume data
    if (formData.parsedResume && (!parsedResume || JSON.stringify(parsedResume) !== JSON.stringify(formData.parsedResume))) {
      setParsedResume(formData.parsedResume);
    }
    // Restore parsed profile
    if (formData.parsedProfile && (!parsedProfile || JSON.stringify(parsedProfile) !== JSON.stringify(formData.parsedProfile))) {
      setParsedProfile(formData.parsedProfile);
    }
    // Restore rich skills
    if (formData.richSkills && (!richSkills.length || JSON.stringify(richSkills) !== JSON.stringify(formData.richSkills))) {
      setRichSkills(formData.richSkills);
    }
    // Restore parsing preview state
    if (formData.showParsingPreview !== undefined && showParsingPreview !== formData.showParsingPreview) {
      setShowParsingPreview(formData.showParsingPreview);
    }
  }, [currentStep, formData]);

  // Sync workStyleAnswers to formData for persistence
  React.useEffect(() => {
    if (Object.keys(workStyleAnswers).length > 0) {
      updateFormData({ workStyleAnswers });
    }
  }, [workStyleAnswers, updateFormData]);

  // Sync resume-related states to formData for persistence
  React.useEffect(() => {
    updateFormData({
      parsedResume,
      parsedProfile,
      richSkills,
      showParsingPreview,
    });
  }, [parsedResume, parsedProfile, richSkills, showParsingPreview, updateFormData]);

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
      if (import.meta.env.DEV) console.log('[Onboarding] Saving work style:', workStyleAnswers);
      await api.post("/me/work-style", workStyleAnswers);
      if (import.meta.env.DEV) console.log('[Onboarding] Work style saved');
      pushToast({ title: "Work style saved!", tone: "success" });

      // Track AI learning event
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

      nextStep();
    } catch (error) {
      const err = error as Error;
      console.error('[Onboarding] Failed to save work style:', err);
      const message = (typeof (err as Error).message === 'string' && !err.message.includes('[object')) ? err.message : "Failed to save work style";
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

  // Sync internal states to useOnboarding's formData for refresh persistence
  React.useEffect(() => {
    updateFormData({ contactInfo, preferences, linkedinUrl });
  }, [contactInfo, preferences, linkedinUrl, updateFormData]);

  // Remember Me - Welcome Back (OB-7 fix: only once per browser session, skipped on step 0)
  React.useEffect(() => {
    if (profile && !profile.has_completed_onboarding && currentStep > 0) {
      const welcomeKey = `has_welcomed_back_${profile.id || 'anon'}`;
      const hasWelcomed = sessionStorage.getItem(welcomeKey);
      if (!hasWelcomed) {
        const locale = getLocale();
        pushToast({
          title: t("onboarding.welcomeBack", locale),
          description: t("onboarding.pickingUpAt", locale).replace("{step}", currentStepData.title),
          tone: "info"
        });
        sessionStorage.setItem(welcomeKey, "true");
      }
    }
  }, [profile?.id]); // Only re-run when profile ID changes, not on every step change

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
          window.dispatchEvent(new CustomEvent('onboarding:complete'));
        } else {
          const nextBtn = stepContainerRef.current?.querySelector<HTMLButtonElement>('[data-onboarding-next]:not([disabled])');
          if (nextBtn) nextBtn.click();
          else window.dispatchEvent(new CustomEvent('onboarding:next'));
        }
      } else if (e.altKey && e.key === 'ArrowLeft') {
        if (!isFirstStep) window.dispatchEvent(new CustomEvent('onboarding:prev'));
      } else if (e.altKey && e.key === 'ArrowRight') {
        const nextBtn = stepContainerRef.current?.querySelector<HTMLButtonElement>('[data-onboarding-next]:not([disabled])');
        if (nextBtn) nextBtn.click();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isLastStep, isFirstStep]);

  // Onboarding completion guard - redirect if already completed
  React.useEffect(() => {
    if (profile?.has_completed_onboarding) {
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
  }, [profile, navigate, resetOnboarding]);

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
      console.error("Resume upload failed:", err);

      // Save metadata for retry
      await resumeUploadRetry.saveResumeMetadata(uploadFile, message);
      await resumeUploadRetry.updateAfterFailure(message);
      setShowRetryComponent(true);

      setResumeError(message);
      pushToast({
        title: "Upload failed",
        description: status ? `[${status}] ${message}` : message,
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

  const handleConfirmParsing = () => {
    setShowParsingPreview(false);
    nextStep();
  };

  const retryWithBackoff = async <T,>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> => {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        const err = error as Error & { status?: number };
        if (i === maxRetries - 1) throw err;

        const isNetworkError = !navigator.onLine || (err.status && err.status >= 500);
        const nextDelay = delay * Math.pow(2, i);

        if (import.meta.env.DEV) {
          console.log("[Onboarding] Retry", i + 1 + "/" + maxRetries, "after", nextDelay, "ms:", error);
        }

        if (isNetworkError) {
          await new Promise(resolve => setTimeout(resolve, nextDelay));
        } else {
          throw error; // Don't retry client errors
        }
      }
    }
    throw new Error('Max retries exceeded');
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
      console.error('[Onboarding] Failed to save skills:', err);
      const isNetworkError = !navigator.onLine || (err.status && err.status >= 500);
      const message = isNetworkError
        ? "Network error. Please check your connection and try again."
        : (typeof (err as Error).message === 'string' && !err.message.includes('[object')) ? err.message : "Failed to save skills";
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
      if (import.meta.env.DEV) {
        console.log("[Telemetry] AI Learned Contact Info", {
          hasFirstName: !!trimmedContact.first_name,
          hasLastName: !!trimmedContact.last_name,
          hasEmail: !!trimmedContact.email,
          hasPhone: !!trimmedContact.phone,
          hasLinkedIn: !!linkedinUrl,
        });
      }

      nextStep();
    } catch (error) {
      const err = error as Error & { status?: number };
      console.error('[Onboarding] Failed to save contact:', err);
      const isNetworkError = !navigator.onLine || (err.status && err.status >= 500);
      const message = isNetworkError
        ? "Network error. Please check your connection and try again."
        : (typeof (err as Error).message === 'string' && !err.message.includes('[object')) ? err.message : "Please try again";
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
      const salaryNum = parseInt(preferences.salary_min.trim());
      if (isNaN(salaryNum) || salaryNum < 0) {
        errors.salary_min = "Must be a valid number";
      } else if (salaryNum > SALARY_CAP) {
        errors.salary_min = `Min salary cannot exceed $${(SALARY_CAP / 1_000_000).toFixed(0)}M`;
      }
    }
    if (preferences.salary_max?.trim()) {
      const maxNum = parseInt(preferences.salary_max.trim());
      const minNum = preferences.salary_min?.trim() ? parseInt(preferences.salary_min.trim()) : 0;
      if (isNaN(maxNum) || maxNum < 0) {
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
        console.log("[Telemetry] AI Learned Job Preferences", {
          location: trimmedPrefs.location,
          roleType: trimmedPrefs.role_type,
          salaryMin: parseInt(trimmedPrefs.salary_min, 10) || 0,
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
      console.error("[Onboarding] Failed to save preferences:", err);
      pushToast({
        title: "Failed to save preferences",
        description: (typeof err.message === 'string' && !err.message.includes('[object')) ? err.message : "Please try again",
        tone: "error"
      });
    } finally {
      setIsSavingPreferences(false);
    }
  };

  const handleComplete = async () => {
    try {
      setIsCompleting(true);
      await completeOnboarding();
      resetOnboarding();
      sessionStorage.setItem("onboarding_just_completed", "true");
      sessionStorage.setItem("show_first_steps", "true");
      telemetry.track("onboarding_completed", { step: "ready" });
      pushToast({ title: "You're all set! Let's job hunt!", tone: "success" });
      navigate("/app/dashboard");
    } catch (error) {
      const err = error as Error & { status?: number };
      console.error('[Onboarding] Failed to complete:', err);
      pushToast({
        title: "Almost there!",
        description: (typeof err.message === 'string' && !err.message.includes('[object')) ? err.message : "Something went wrong. Please try again.",
        tone: "error"
      });
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
    <div className="min-h-screen w-full bg-slate-50 flex flex-col relative">
      <ErrorBoundary>
        {/* Minimal Header */}
        <header className="px-3 md:px-6 h-11 md:h-12 shrink-0 flex items-center justify-between bg-white/80 backdrop-blur-xl border-b border-slate-200 z-50 sticky top-0">
          <Logo to="/app/onboarding" size="sm" />
          <div className="flex items-center gap-2 md:gap-4">
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-50 border border-primary-100">
              <div className="w-2 h-2 rounded-full bg-primary-500 animate-pulse" aria-hidden />
              <span className="text-[10px] font-black text-primary-700 uppercase tracking-widest">Setting up your profile</span>
            </div>
            <div className="lg:hidden flex items-center gap-1.5 px-2 py-1 rounded-full bg-primary-50 border border-primary-100">
              <div className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse" aria-hidden />
              <span className="text-[9px] font-black text-primary-700 uppercase tracking-wider">Setup</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => { if (globalThis.confirm('Are you sure? This will clear your progress.')) resetOnboarding(); }} className="text-slate-500 text-[10px] md:text-xs font-bold uppercase hover:bg-slate-100 dark:hover:bg-slate-800" title="Clear progress and start over" aria-label="Restart onboarding and clear progress">
              Restart
            </Button>
          </div>
        </header>

        <main className="flex-1 w-full flex flex-col items-center p-4 md:p-6 lg:p-8 bg-grid-premium">
          <div className="w-full max-w-xl lg:max-w-4xl xl:max-w-5xl">
            {/* Progress bar */}
            <div className="mb-4 md:mb-6" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100} aria-label={`Setup progress: step ${currentStep + 1} of ${steps.length}`}>
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Step {currentStep + 1} of {steps.length} — {(progress).toFixed(0)}%
                </span>
                <span className="text-[10px] md:text-xs font-bold text-primary-600 uppercase tracking-wider">{currentStepData.title}</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
                <motion.div
                  initial={shouldReduceMotion ? { width: `${progress}%` } : { width: 0 }}
                  animate={{ width: `${progress}%` }}
                  className="h-full bg-primary-600"
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
                <Card tone="glass" shadow="lift" className="p-4 md:p-6 lg:p-8 border-slate-200/60">
                  {/* Profile completeness indicator - O22: tooltip explains calculation */}
                  <div
                    className="mb-4 md:mb-6 rounded-xl md:rounded-2xl bg-slate-900 border border-slate-800 p-3 md:p-4 shadow-lg"
                    title="Resume 20%, Contact 15%, Location 10%, Role 10%, Salary 5%, Work auth 5%, Skills up to 15%, Work style up to 15%"
                    aria-describedby="profile-strength-hint"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-2 md:gap-3">
                        <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center shrink-0">
                          <Sparkles className="h-4 w-4 md:h-5 md:w-5 text-emerald-400" aria-hidden />
                        </div>
                        <div>
                          <span className="block text-[10px] font-bold text-emerald-500/70 uppercase tracking-wider">Profile Strength</span>
                          <span id="profile-strength-hint" className="sr-only">Resume 20%, Contact 15%, Location 10%, Role 10%, Salary 5%, Work auth 5%, Skills up to 15%, Work style up to 15%</span>
                          <span className="text-xs md:text-sm font-bold text-white">Setup Progress</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 md:gap-4">
                        <div className="flex-1 md:w-32 h-1.5 rounded-full bg-white/10 overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${completeness}%` }}
                            className="h-full bg-emerald-500"
                            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                          />
                        </div>
                        <span className="text-lg md:text-2xl font-black text-white">{completeness}%</span>
                      </div>
                    </div>
                    {/* Badges row */}
                    <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/10">
                      {(profile?.resume_url || resumeFile) && (
                        <Badge className="text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-1">
                          <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden />
                          Resume Added
                        </Badge>
                      )}
                      {preferences.location && (
                        <Badge className="text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-1">
                          <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden />
                          Location Set
                        </Badge>
                      )}
                      {preferences.role_type && (
                        <Badge className="text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-1">
                          <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden />
                          Job Title Set
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
