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
import { telemetry } from "../../lib/telemetry";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { BrowserCacheService } from "../../lib/browserCache";
import { Skeleton, OnboardingSkeleton } from "../../components/ui/Skeleton";
import { checkEmailTypo } from "../../lib/emailUtils";
import { ErrorBoundary } from "../../components/ErrorBoundary";

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
    if ('connection' in navigator && (navigator as any).connection.saveData) {
      setIsLowPowerMode(true);
    }

    // Check battery status if available
    let batteryObj: any = null;
    let handleBatteryChange: (() => void) | null = null;

    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((battery: any) => {
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
  const [workStyleAnswers, setWorkStyleAnswers] = React.useState<Record<string, string>>(() => {
    // Initialize from formData if available (page refresh persistence)
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
    } catch (err: any) {
      console.error('[Onboarding] Failed to save work style:', err);
      const message = err?.message || "Failed to save work style";
      pushToast({ title: "Failed to save work style", description: message, tone: "error" });
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
        salary_max: p.salary_max ? String(p.salary_max) : "",
        remote_only: p.remote_only ?? false,
        onsite_only: p.onsite_acceptable ?? false,
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
        if (isLastStep) {
          // Use a custom event to trigger completion to avoid stale closure
          window.dispatchEvent(new CustomEvent('onboarding:complete'));
        } else if (!isLastStep) {
          // Trigger next button click
          const nextBtn = document.querySelector('button[aria-label="Confirm identity and proceed"], button[aria-label="Save preferences and deploy hunter engine"], button[aria-label="Save answers and continue"], button[aria-label="Finalize setup and launch command center"]');
          if (nextBtn && !(nextBtn as HTMLButtonElement).disabled) {
            (nextBtn as HTMLElement).click();
          } else {
            // Fallback for simple steps
            window.dispatchEvent(new CustomEvent('onboarding:next'));
          }
        }
      } else if (e.key === 'Escape') {
        // Maybe unrelated, but handy
      } else if (e.altKey && e.key === 'ArrowLeft') {
        if (!isFirstStep) window.dispatchEvent(new CustomEvent('onboarding:prev'));
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
  }, [isLastStep, isFirstStep]);

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
        if (import.meta.env.DEV) console.log('[Onboarding] Parsed profile:', p);

        // Cache parsed resume data for future use
        const resumeData = {
          title: p.headline || (p.experience?.[0]?.title),
          skills: p.skills?.technical?.slice(0, 5) || [],
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
          const parsedSkills = techSkills.map((s: any) => ({
            skill: s.skill || String(s),
            confidence: typeof s.confidence === 'number' ? s.confidence : 0.5,
            years_actual: s.years_actual || null,
            context: s.context || "",
            last_used: s.last_used || null,
            verified: s.verified || false,
            related_to: s.related_to || [],
            source: s.source || "resume",
            project_count: s.project_count || 0,
          }));
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
        setParsedProfile(data.parsed_profile);

        // Fetch AI suggestions in background (don't block)
        aiSuggestions.fetchAllSuggestions(
          data.parsed_profile,
          data.preferences?.location || data.contact?.location || ""
        ).catch(() => {
          // Non-critical failure
          if (import.meta.env.DEV) console.log("AI suggestions fetch failed, will continue without");
        });

        // Track AI learning event
        // Track AI learning event
        telemetry.track("AI Learned Resume Data", {
          hasSkills: !!data.parsed_profile.skills,
          skillCount: data.parsed_profile.skills?.technical?.length || 0,
          hasExperience: !!data.parsed_profile.experience,
          experienceYears: data.parsed_profile.experience?.length || 0,
          hasEducation: !!data.parsed_profile.education,
        });
      }
    } catch (err) {
      const message = (err as Error).message;
      const status = (err as any).status;
      console.error("Resume upload failed:", err);
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
      } catch (error: any) {
        if (i === maxRetries - 1) throw error;

        const isNetworkError = !navigator.onLine || error?.status >= 500;
        const nextDelay = delay * Math.pow(2, i);

        if (import.meta.env.DEV) {
          console.log(`[Onboarding] Retry ${i + 1}/${maxRetries} after ${nextDelay}ms:`, error);
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
    } catch (err: any) {
      console.error('[Onboarding] Failed to save skills:', err);
      const isNetworkError = !navigator.onLine || err?.status >= 500;
      const message = isNetworkError
        ? "Network error. Please check your connection and try again."
        : err?.message || "Failed to save skills";
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
    } catch (err: any) {
      console.error('[Onboarding] Failed to save contact:', err);
      const isNetworkError = !navigator.onLine || err?.status >= 500;
      const message = isNetworkError
        ? "Network error. Please check your connection and try again."
        : err?.message || "Please try again";
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

    // Salary validation - must be a positive number if provided
    if (preferences.salary_min?.trim()) {
      const salaryNum = parseInt(preferences.salary_min.trim());
      if (isNaN(salaryNum) || salaryNum < 0) {
        errors.salary_min = "Must be a valid number";
      } else if (salaryNum > 10000000) {
        errors.salary_min = "Please enter a reasonable value";
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
      pushToast({ title: "Preferences saved!", tone: "success" });

      // Track AI learning event
      if (import.meta.env.DEV) {
        console.log("[Telemetry] AI Learned Job Preferences", {
          location: trimmedPrefs.location,
          roleType: trimmedPrefs.role_type,
          salaryMin: parseInt(trimmedPrefs.salary_min) || 0,
          remoteOnly: trimmedPrefs.remote_only,
          onsiteOnly: trimmedPrefs.onsite_only,
          workAuthorized: trimmedPrefs.work_authorized,
          visaSponsorship: trimmedPrefs.visa_sponsorship,
          excludedCompaniesCount: trimmedPrefs.excluded_companies?.length || 0,
          excludedKeywordsCount: trimmedPrefs.excluded_keywords?.length || 0,
        });
      }

      nextStep();
    } catch (err: any) {
      console.error('[Onboarding] Failed to save preferences:', err);
      pushToast({
        title: "Failed to save preferences",
        description: err?.message || "Please try again",
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
      pushToast({ title: "You're all set! Let's job hunt! 🚀", tone: "success" });
      navigate("/app/jobs");
    } catch (err: any) {
      console.error('[Onboarding] Failed to complete:', err);
      pushToast({
        title: "Almost there!",
        description: err?.message || "Something went wrong. Please try again.",
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
              <div className="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
              <span className="text-[10px] font-black text-primary-700 uppercase tracking-widest">Setting Up Your Profile</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => resetOnboarding()} className="text-slate-500 text-[10px] md:text-xs font-bold uppercase hover:bg-slate-100">
              Restart
            </Button>
          </div>
        </header>

        <main className="flex-1 w-full flex flex-col items-center p-4 md:p-6 lg:p-8 bg-grid-premium">
          <div className="w-full max-w-xl lg:max-w-4xl xl:max-w-5xl">
            {/* Progress bar */}
            <div className="mb-4 md:mb-6">
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Setup Progress — {(progress).toFixed(0)}%
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
                key={currentStep}
                initial={shouldReduceMotion ? undefined : { opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={shouldReduceMotion ? undefined : { opacity: 0 }}
                transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.2 }}
                className="w-full"
              >
                <Card tone="glass" shadow="lift" className="p-4 md:p-6 lg:p-8 border-slate-200/60">
                  {/* Profile completeness indicator - Desktop: horizontal, Mobile: compact */}
                  <div className="mb-4 md:mb-6 rounded-xl md:rounded-2xl bg-slate-900 border border-slate-800 p-3 md:p-4 shadow-lg">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-2 md:gap-3">
                        <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center shrink-0">
                          <Sparkles className="h-4 w-4 md:h-5 md:w-5 text-emerald-400" />
                        </div>
                        <div>
                          <span className="block text-[10px] font-bold text-emerald-500/70 uppercase tracking-wider">Profile Strength</span>
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
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                          Resume Added
                        </Badge>
                      )}
                      {preferences.location && (
                        <Badge className="text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-1">
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                          Location Set
                        </Badge>
                      )}
                      {preferences.role_type && (
                        <Badge className="text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-1">
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                          Job Title Set
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
                      onResetParsingState={() => {
                        setParsedResume(null);
                        setParsedProfile(null);
                        setRichSkills([]);
                      }}
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
                      aiSuggestions={aiSuggestions}
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
                </Card>
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </ErrorBoundary>
    </div>
  );
}
