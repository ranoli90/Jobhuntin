import * as React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
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
import {
  Skeleton,
  OnboardingSkeleton,
  ResumeStepSkeleton,
  PreferencesStepSkeleton,
  SkillReviewStepSkeleton,
  WorkStyleStepSkeleton,
} from "../../components/ui/Skeleton";
import { checkEmailTypo, isValidEmail } from "../../lib/emailUtils";
import { isValidLinkedInUrl } from "../../lib/linkedinValidation";
import { ErrorBoundary } from "../../components/ErrorBoundary";
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { resumeUploadRetry } from "../../lib/resumeUploadRetry";
import ResumeUploadRetry from "../../components/ui/ResumeUploadRetry";

// Step Components - lazy loaded to reduce Onboarding chunk size
const WelcomeStep = React.lazy(() =>
  import("./onboarding/steps/WelcomeStep").then((m) => ({
    default: m.WelcomeStep,
  })),
);
const ResumeStep = React.lazy(() =>
  import("./onboarding/steps/ResumeStep").then((m) => ({
    default: m.ResumeStep,
  })),
);
const SkillReviewStep = React.lazy(() =>
  import("./onboarding/steps/SkillReviewStep").then((m) => ({
    default: m.SkillReviewStep,
  })),
);
const ConfirmContactStep = React.lazy(() =>
  import("./onboarding/steps/ConfirmContactStep").then((m) => ({
    default: m.ConfirmContactStep,
  })),
);
const PreferencesStep = React.lazy(() =>
  import("./onboarding/steps/PreferencesStep").then((m) => ({
    default: m.PreferencesStep,
  })),
);
const WorkStyleStep = React.lazy(() =>
  import("./onboarding/steps/WorkStyleStep").then((m) => ({
    default: m.WorkStyleStep,
  })),
);
const CareerGoalsStep = React.lazy(() =>
  import("./onboarding/steps/CareerGoalsStep").then((m) => ({
    default: m.CareerGoalsStep,
  })),
);
const ReadyStep = React.lazy(() =>
  import("./onboarding/steps/ReadyStep").then((m) => ({
    default: m.ReadyStep,
  })),
);

// Types
import {
  ParsedResume,
  RichSkill,
  OnboardingFormData,
} from "../../types/onboarding";

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
  const {
    profile,
    loading,
    uploadResume,
    savePreferences,
    completeOnboarding,
    updateProfile,
  } = useProfile();
  const syncToastLastShownRef = React.useRef(0);
  const onSyncError = React.useCallback(
    (error: unknown) => {
      if (import.meta.env.DEV)
        console.warn("[Onboarding] Progress sync failed:", error);
      const now = Date.now();
      const DEBOUNCE_MS = 5000;
      if (now - syncToastLastShownRef.current < DEBOUNCE_MS) return;
      syncToastLastShownRef.current = now;
      pushToast({
        title: "Could not save progress",
        description: "Your progress is saved locally. Check your connection.",
        tone: "warning",
      });
    },
    [],
  );
  const onSyncErrorRef = React.useRef(onSyncError);
  onSyncErrorRef.current = onSyncError;
  // O25: Throttle profile sync to max 1 req per 2s to avoid 429 rate limits
  const syncProgressToServer = React.useMemo(() => {
    let lastSyncTime = 0;
    let pending: { step: number; completed: string[] } | null = null;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    const MIN_INTERVAL_MS = 2000;

    const doPatch = async (step: number, completed: string[]) => {
      await api.patch("me/profile", {
        onboarding_step: step,
        onboarding_completed_steps: completed,
      });
    };

    const flushPending = (onError: (err: unknown) => void) => {
      if (!pending || !timeoutId) return;
      const { step, completed } = pending;
      pending = null;
      timeoutId = null;
      lastSyncTime = Date.now();
      doPatch(step, completed).catch((err) => {
        if (import.meta.env.DEV)
          console.warn("[Onboarding] syncProgressToServer failed:", err);
        onError(err);
      });
    };

    return async (step: number, completed: string[]) => {
      const now = Date.now();
      if (now - lastSyncTime >= MIN_INTERVAL_MS) {
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
          pending = null;
        }
        lastSyncTime = now;
        try {
          await doPatch(step, completed);
        } catch (error) {
          if (import.meta.env.DEV)
            console.warn("[Onboarding] syncProgressToServer failed:", error);
          const err = error as Error & { status?: number };
          const isRetryable =
            !err.status || err.status >= 500 || err.status === 429;
          if (isRetryable) {
            try {
              await new Promise((r) => setTimeout(r, 500));
              await doPatch(step, completed);
              return;
            } catch (retryErr) {
              if (import.meta.env.DEV)
                console.warn(
                  "[Onboarding] syncProgressToServer retry failed:",
                  retryErr,
                );
              throw retryErr;
            }
          }
          throw error;
        }
        return;
      }
      pending = { step, completed };
      if (!timeoutId) {
        timeoutId = setTimeout(
          () => flushPending((e) => onSyncErrorRef.current(e)),
          MIN_INTERVAL_MS - (now - lastSyncTime),
        );
      }
    };
  }, []);
  const [searchParameters, setSearchParameters] = useSearchParams();
  const urlStep = React.useMemo(() => {
    const s = searchParameters.get("step");
    if (s == undefined) return null;
    const n = Number.parseInt(s, 10);
    return Number.isFinite(n) && n >= 0 ? n : null;
  }, [searchParameters]);

  const {
    steps,
    currentStep,
    currentStepData,
    completedSteps,
    progress,
    isFirstStep,
    isLastStep,
    nextStep,
    prevStep,
    goToStep,
    resetOnboarding,
    formData,
    updateFormData,
  } = useOnboarding({
    serverProgress:
      profile &&
      !profile.has_completed_onboarding &&
      profile.onboarding_step != undefined
        ? {
            step: profile.onboarding_step,
            completed: profile.onboarding_completed_steps || [],
          }
        : null,
    syncToServer: profile ? syncProgressToServer : undefined,
    initialStepFromUrl: urlStep,
    onSyncError,
  });
  const aiSuggestions = useAISuggestions();
  const locale = getLocale();
  const [isLowPowerMode, setIsLowPowerMode] = React.useState(false);
  const cacheService = React.useMemo(
    () => BrowserCacheService.getInstance(),
    [],
  );

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

  // N1: Keep URL in sync with current step for shareable deep-links
  React.useEffect(() => {
    const urlStep = searchParameters.get("step");
    const mismatch = urlStep !== String(currentStep);
    console.log("[DEBUG] URL sync effect", {
      currentStep,
      urlStep,
      mismatch,
      willUpdate: mismatch,
    });
    if (mismatch) {
      setSearchParameters(
        (previous) => {
          const next = new URLSearchParams(previous);
          next.set("step", String(currentStep));
          return next;
        },
        { replace: true },
      );
    }
  }, [currentStep, searchParameters, setSearchParameters]);

  React.useEffect(() => {
    // Check for save-data preference
    if (navigator.connection?.saveData) {
      setIsLowPowerMode(true);
    }

    // Check battery status if available
    let batteryObject: BatteryManager | null = null;
    let handleBatteryChange: (() => void) | null = null;
    let mounted = true;

    if (navigator.getBattery) {
      navigator.getBattery().then((battery) => {
        if (!mounted) return; // Component unmounted before promise resolved
        batteryObject = battery;
        handleBatteryChange = () => {
          setIsLowPowerMode(battery.level < 0.2 && !battery.charging);
        };

        setIsLowPowerMode(battery.level < 0.2 && !battery.charging);
        battery.addEventListener("levelchange", handleBatteryChange);
        battery.addEventListener("chargingchange", handleBatteryChange);
      });
    }

    return () => {
      mounted = false;
      // Cleanup battery event listeners
      if (batteryObject && handleBatteryChange) {
        batteryObject.removeEventListener("levelchange", handleBatteryChange);
        batteryObject.removeEventListener(
          "chargingchange",
          handleBatteryChange,
        );
      }
    };
  }, []);

  // Load cached data on component mount (skills: prefer skill-review cache over resume)
  React.useEffect(() => {
    const loadCachedData = async () => {
      if (profile?.id) {
        try {
          const [cachedResume, cachedSkills, cachedPrefs] = await Promise.all([
            cacheService.getParsedResume(profile.id),
            cacheService.getSkills(profile.id),
            cacheService.getUserPreferences(profile.id),
          ]);

          if (cachedResume) {
            if (import.meta.env.DEV)
              console.log("[Onboarding] Loading cached resume data");
            setParsedResume({
              title: cachedResume.title,
              skills: cachedResume.skills,
              years: cachedResume.years,
              summary: cachedResume.summary,
              headline: cachedResume.headline,
            });
            setParsedProfile(cachedResume.parsedProfile);
          }

          if (cachedSkills?.length) {
            if (import.meta.env.DEV)
              console.log("[Onboarding] Loading cached skills");
            setRichSkills(cachedSkills);
          } else if (cachedResume?.richSkills?.length) {
            setRichSkills(cachedResume.richSkills);
          }

          if (cachedPrefs) {
            if (import.meta.env.DEV)
              console.log("[Onboarding] Loading cached preferences");
            setPreferences(cachedPrefs);
          }
        } catch (error) {
          if (import.meta.env.DEV)
            console.error("[Onboarding] Error loading cached data:", error);
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

  const [formErrors, setFormErrors] = React.useState<Record<string, string>>(
    {},
  );
  const [saveError, setSaveError] = React.useState<string | null>(null);
  const [showRestartConfirm, setShowRestartConfirm] = React.useState(false);

  const [contactInfo, setContactInfo] = React.useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
  });
  const [isSavingContact, setIsSavingContact] = React.useState(false);

  const [linkedinUrl, setLinkedinUrl] = React.useState(
    formData.linkedinUrl || "",
  );
  const [parsedResume, setParsedResume] = React.useState<ParsedResume | null>(
    null,
  );
  const [showParsingPreview, setShowParsingPreview] = React.useState(false);
  const [isSavingPreferences, setIsSavingPreferences] = React.useState(false);
  const [isCompleting, setIsCompleting] = React.useState(false);
  const [parsedProfile, setParsedProfile] = React.useState<Record<
    string,
    unknown
  > | null>(null);
  const [emailTypoSuggestion, setEmailTypoSuggestion] = React.useState<
    string | null
  >(null);
  const [richSkills, setRichSkills] = React.useState<RichSkill[]>([]);
  const [isSavingSkills, setIsSavingSkills] = React.useState(false);
  const [workStyleAnswers, setWorkStyleAnswers] = React.useState<
    Record<string, string>
  >(() => {
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
  const previousStepReference = React.useRef(currentStep);

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
    if (currentStep > previousStepReference.current && !shouldReduceMotion) {
      setShowStepConfetti(true);
    }
    previousStepReference.current = currentStep;
  }, [currentStep, shouldReduceMotion]);

  // Resume upload retry state
  const [showRetryComponent, setShowRetryComponent] = React.useState(false);

  // Skeleton loading states removed — shouldShowSkeleton uses direct state instead

  // Helper function to determine if current step should show skeleton
  const shouldShowSkeleton = React.useCallback(() => {
    const stepId = currentStepData.id;

    // Show skeleton during specific loading states
    switch (stepId) {
      case "resume": {
        return isUploading;
      }
      case "preferences": {
        return (
          isSavingPreferences ||
          aiSuggestions.roles.loading ||
          aiSuggestions.locations.loading ||
          aiSuggestions.salary.loading
        );
      }
      case "skill-review": {
        return isSavingSkills;
      }
      case "confirm-contact": {
        return isSavingContact;
      }
      case "work-style": {
        return isSavingWorkStyle;
      }
      default: {
        return false;
      }
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
    aiSuggestions.salary.loading,
  ]);

  // Helper function to get the appropriate skeleton component
  const getSkeletonComponent = React.useCallback(() => {
    const stepId = currentStepData.id;

    switch (stepId) {
      case "resume": {
        return <ResumeStepSkeleton />;
      }
      case "preferences": {
        return <PreferencesStepSkeleton />;
      }
      case "skill-review": {
        return <SkillReviewStepSkeleton />;
      }
      case "work-style": {
        return <WorkStyleStepSkeleton />;
      }
      default: {
        return <OnboardingSkeleton />;
      }
    }
  }, [currentStepData.id]);

  // Restore local state from formData on mount and step changes (for back navigation persistence)
  // E1: Only restore when local state is empty to avoid overwriting user input while typing
  React.useEffect(() => {
    if (formData.linkedinUrl && !linkedinUrl.trim())
      setLinkedinUrl(formData.linkedinUrl);
    if (formData.workStyleAnswers && Object.keys(workStyleAnswers).length === 0)
      setWorkStyleAnswers(formData.workStyleAnswers);
    if (formData.parsedResume && !parsedResume)
      setParsedResume(formData.parsedResume);
    if (formData.parsedProfile && !parsedProfile)
      setParsedProfile(formData.parsedProfile);
    if (formData.richSkills?.length && richSkills.length === 0)
      setRichSkills(formData.richSkills);
    if (formData.showParsingPreview !== undefined && !showParsingPreview)
      setShowParsingPreview(formData.showParsingPreview);
    if (formData.careerGoals && Object.keys(careerGoals).length === 0)
      setCareerGoals(formData.careerGoals);
  }, [
    currentStep,
    formData.linkedinUrl,
    formData.workStyleAnswers,
    formData.parsedResume,
    formData.parsedProfile,
    formData.richSkills,
    formData.showParsingPreview,
    formData.careerGoals,
  ]);

  // Clear save error when changing steps (e.g. prev/next) so it doesn't persist across steps
  React.useEffect(() => {
    setSaveError(null);
  }, [currentStep]);

  const triggerHaptic = (type: "success" | "warning" | "light" = "light") => {
    if (typeof navigator !== "undefined" && navigator.vibrate) {
      if (type === "success") navigator.vibrate([10, 30, 10]);
      else if (type === "warning") navigator.vibrate([30, 10, 30]);
      else navigator.vibrate(10);
    }
  };

  /** Map frontend work style values to backend API enums (A2/A3) */
  const mapWorkStyleForApi = (answers: Record<string, string>) => {
    const mapped: Record<string, string> = {};
    for (const [k, v] of Object.entries(answers)) {
      if (!v) continue;
      if (k === "autonomy_preference" && v === "flexible") mapped[k] = "medium";
      else if (k === "learning_style" && v === "pairing") mapped[k] = "mixed";
      else if (k === "learning_style" && v === "courses")
        mapped[k] = "studying";
      else if (k === "pace_preference" && v === "relaxed")
        mapped[k] = v; // backend has relaxed
      else mapped[k] = v;
    }
    return mapped;
  };

  const handleSaveWorkStyle = async () => {
    triggerHaptic("light");
    setSaveError(null);
    setIsSavingWorkStyle(true);
    try {
      // A1: Work style is optional; advance without POST when user skips (no answers)
      const hasAnswers = Object.keys(workStyleAnswers).some(
        (k) => workStyleAnswers[k],
      );
      if (hasAnswers) {
        const payload = mapWorkStyleForApi(workStyleAnswers);
        await api.post("/me/work-style", payload);
        pushToast({ title: "Work style saved!", tone: "success" });
        telemetry.track("AI Learned Work Style", {
          answersCount: Object.keys(workStyleAnswers).length,
          hasAutonomyPreference: !!workStyleAnswers.autonomy_preference,
          hasLearningStyle: !!workStyleAnswers.learning_style,
          hasCompanyStagePreference:
            !!workStyleAnswers.company_stage_preference,
          hasCommunicationStyle: !!workStyleAnswers.communication_style,
          hasPacePreference: !!workStyleAnswers.pace_preference,
          hasOwnershipPreference: !!workStyleAnswers.ownership_preference,
          hasCareerTrajectory: !!workStyleAnswers.career_trajectory,
        });
      }
      nextStep();
    } catch (error) {
      const error_ = error as Error;
      if (import.meta.env.DEV)
        console.error("[Onboarding] Failed to save work style:", error_);
      let message = "Failed to save work style";
      if (
        typeof error_.message === "string" &&
        !error_.message.includes("[object")
      ) {
        message = error_.message;
      }
      setSaveError(message);
      pushToast({
        title: "Failed to save work style",
        description: message,
        tone: "error",
      });
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
      setContactInfo((previous) => ({
        first_name: previous.first_name || c.first_name || "",
        last_name: previous.last_name || c.last_name || "",
        email: previous.email || c.email || profile.email || "",
        phone: previous.phone || c.phone || "",
      }));
      // Pre-fill LinkedIn URL from profile if available
      setLinkedinUrl((previous) => previous || c.linkedin_url || "");
    }
  }, [profile?.contact, profile?.email]);

  // Persist internal states to useOnboarding's formData for refresh persistence
  // Separate from restore effect to avoid dependency loop (formData not in deps)
  // FIXED: Use debouncing and ref to prevent infinite loop
  const previousValuesReference = React.useRef<string>("");
  const updateTimeoutReference = React.useRef<NodeJS.Timeout | null>(null);

  React.useEffect(() => {
    // Clear any pending update
    if (updateTimeoutReference.current) {
      clearTimeout(updateTimeoutReference.current);
    }

    // Debounce the update to prevent rapid re-renders
    updateTimeoutReference.current = setTimeout(() => {
      const currentValues = JSON.stringify({
        contactInfo,
        preferences,
        linkedinUrl,
        workStyleAnswers,
        parsedResume,
        parsedProfile,
        richSkills,
        showParsingPreview,
        careerGoals,
      });

      // Only update if values actually changed
      if (currentValues !== previousValuesReference.current) {
        updateFormData({
          contactInfo,
          preferences,
          linkedinUrl,
          workStyleAnswers,
          parsedResume,
          parsedProfile,
          richSkills,
          showParsingPreview,
          careerGoals,
        });
        previousValuesReference.current = currentValues;
      }
    }, 100); // 100ms debounce

    return () => {
      if (updateTimeoutReference.current) {
        clearTimeout(updateTimeoutReference.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    contactInfo,
    preferences,
    linkedinUrl,
    workStyleAnswers,
    parsedResume,
    parsedProfile,
    richSkills,
    showParsingPreview,
    careerGoals,
  ]);

  // OB4: Resume Where You Left Off - Show banner for returning users
  React.useEffect(() => {
    if (profile && !profile.has_completed_onboarding && currentStep > 0) {
      const welcomeKey = `has_welcomed_back_${profile.id || "anon"}`;
      const hasWelcomed = sessionStorage.getItem(welcomeKey);
      if (!hasWelcomed) {
        const locale = getLocale();
        pushToast({
          title: t("onboarding.welcomeBack", locale) || "Welcome back!",
          description:
            t("onboarding.pickingUpAt", locale).replace(
              "{step}",
              currentStepData.title,
            ) || `Picking up at: ${currentStepData.title}`,
          tone: "info",
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

  const stepContainerReference = React.useRef<HTMLDivElement>(null);

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
        description:
          t("onboarding.redirectingToDashboard", getLocale()) ||
          "Redirecting to your dashboard...",
        tone: "info",
      });
    }
  }, [profile, navigate, resetOnboarding, currentStep]);

  // O25: Backend rate limits magic-link (auth.py), profile writes (user.py), and AI endpoints (ai_rate_limiting.py)
  // O14: Asset preloading (favicon + critical fonts for LCP)
  React.useEffect(() => {
    for (const source of ["/favicon.svg"]) {
      const img = new Image();
      img.src = source;
    }
    const fontUrl =
      "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Instrument+Serif:ital@0;1&display=swap";
    if (
      !document.querySelector(
        'link[rel="preload"][as="style"][href*="fonts.googleapis.com"]',
      )
    ) {
      const link = document.createElement("link");
      link.rel = "preload";
      link.as = "style";
      link.href = fontUrl;
      document.head.append(link);
    }
  }, []);

  const handleResumeNext = async () => {
    const trimmed = linkedinUrl?.trim();
    if (trimmed && isValidLinkedInUrl(trimmed)) {
      try {
        await updateProfile({ contact: { linkedin_url: trimmed } });
      } catch (error) {
        if (import.meta.env.DEV)
          console.warn("[Onboarding] Failed to persist LinkedIn:", error);
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
      const data = await retryWithBackoff(
        async () => {
          return await uploadResume(uploadFile);
        },
        3,
        1000,
      );

      pushToast({ title: "Resume uploaded!", tone: "success" });

      if (data.parsed_profile) {
        const p = data.parsed_profile;

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
          title: p.headline || p.experience?.[0]?.title,
          skills: (p.skills?.technical || [])
            .filter((s: unknown) => typeof s === "string")
            .slice(0, 5),
          years: p.experience?.length || 0,
          summary: p.summary,
          headline: p.headline,
          parsedProfile: data.parsed_profile,
          richSkills: null,
        };

        // Extract rich skills from parsed profile (V2 format)
        const techSkills = p.skills?.technical || [];

        const ensureClientId = (sk: RichSkill, index: number): RichSkill => ({
          ...sk,
          clientId:
            sk.clientId ??
            crypto.randomUUID?.() ??
            `skill-${Date.now()}-${index}`,
        });
        if (
          techSkills.length > 0 &&
          typeof techSkills[0] === "object" &&
          techSkills[0] !== null
        ) {
          // Rich skills format from V2 parser
          const parsedSkills: RichSkill[] = techSkills.map(
            (s: RichSkill | string, index: number) =>
              ensureClientId(
                typeof s === "string"
                  ? {
                      skill: s,
                      confidence: 0.5,
                      years_actual: null,
                      context: "",
                      last_used: null,
                      verified: false,
                      related_to: [],
                      source: "resume",
                      project_count: 0,
                    }
                  : {
                      skill: s.skill || String(s),
                      confidence:
                        typeof s.confidence === "number" ? s.confidence : 0.5,
                      years_actual: s.years_actual || null,
                      context: s.context || "",
                      last_used: s.last_used || null,
                      verified: s.verified || false,
                      related_to: s.related_to || [],
                      source: s.source || "resume",
                      project_count: s.project_count || 0,
                    },
                index,
              ),
          );
          setRichSkills(parsedSkills);
          resumeData.richSkills = parsedSkills;
        } else {
          // Old format - convert to rich skills with default values
          const parsedSkills = techSkills.map((skill: string, index: number) =>
            ensureClientId(
              {
                skill,
                confidence: 0.5,
                years_actual: null,
                context: "",
                last_used: null,
                verified: false,
                related_to: [],
                source: "resume",
                project_count: 0,
              },
              index,
            ),
          );
          setRichSkills(parsedSkills);
          resumeData.richSkills = parsedSkills;
        }

        // Cache the resume data
        await cacheService.cacheParsedResume(
          profile?.id || "anonymous",
          resumeData,
        );

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
        setParsedProfile(
          data.parsed_profile as unknown as Record<string, unknown>,
        );

        // Fetch AI suggestions in background (don't block)
        aiSuggestions
          .fetchAllSuggestions(
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            data.parsed_profile as any,
            data.preferences?.location || (data.contact as any)?.location || "",
          )
          .catch(() => {
            // Non-critical failure
            if (import.meta.env.DEV)
              console.log("AI suggestions fetch failed, will continue without");
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
      const error_ = error as Error & { status?: number };
      const message = error_.message;
      const status = error_.status;
      if (import.meta.env.DEV) console.error("Resume upload failed:", error_);

      // Save metadata for retry
      await resumeUploadRetry.saveResumeMetadata(uploadFile, message);
      await resumeUploadRetry.updateAfterFailure(message);
      setShowRetryComponent(true);

      // OB2: Improve Resume Upload Error Messages - Provide actionable recovery steps
      let userFriendlyMessage = message;
      if (status === 413) {
        userFriendlyMessage =
          "File is too large. Please use a PDF under 15MB and try again.";
      } else if (status === 400) {
        userFriendlyMessage =
          "Invalid file format. Please upload a PDF resume.";
      } else if (status && status >= 500) {
        userFriendlyMessage =
          "Server error. Your file was saved and will retry automatically. Check back in a moment.";
      } else if (message.includes("network") || message.includes("timeout")) {
        userFriendlyMessage =
          "Network error. Your file was saved and will retry when connection is restored.";
      } else if (!message || message === "Upload failed") {
        userFriendlyMessage =
          "Upload failed. Your file was saved and will retry automatically. You can also try again manually.";
      } else if (
        message.toLowerCase().includes("extract") ||
        message.toLowerCase().includes("readable text")
      ) {
        userFriendlyMessage =
          "We couldn't read text from your resume. Try a different PDF or ensure it's not image-only (scanned documents may need OCR).";
      } else if (
        message.toLowerCase().includes("parse") ||
        message.toLowerCase().includes("parsing")
      ) {
        userFriendlyMessage =
          "Resume parsing failed. Your file was saved — you can skip and add details manually, or try a different resume.";
      }

      setResumeError(userFriendlyMessage);
      pushToast({
        title: "Upload failed",
        description: userFriendlyMessage,
        tone: "error",
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
    function_: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000,
  ): Promise<T> => {
    return withRetry(function_, {
      maxRetries,
      baseDelayMs: delay,
      shouldRetry: (error: Error & { status?: number }) => {
        const isNetworkError =
          !navigator.onLine ||
          (error.status !== undefined && error.status >= 500);
        if (!isNetworkError) return false; // Don't retry client errors
        return true;
      },
      onRetry: (error, attempt) => {
        if (import.meta.env.DEV)
          console.log(
            "[Onboarding] Retry",
            attempt + 1 + "/" + maxRetries,
            ":",
            error,
          );
      },
    });
  };

  const handleSaveSkills = async () => {
    triggerHaptic("light");
    setSaveError(null);
    setIsSavingSkills(true);
    try {
      // Cache skills data
      await cacheService.cacheSkills(profile?.id || "anonymous", richSkills);

      // Save skills to backend with retry logic
      await retryWithBackoff(() =>
        api.post<{ status: string; count: number }>("/me/skills", {
          skills: richSkills,
        }),
      );
      pushToast({ title: "Skills saved!", tone: "success" });
      nextStep();
    } catch (error) {
      const error_ = error as Error & { status?: number };
      if (import.meta.env.DEV)
        console.error("[Onboarding] Failed to save skills:", error_);
      const isNetworkError =
        !navigator.onLine || (error_.status && error_.status >= 500);
      let message = "Failed to save skills";
      if (isNetworkError) {
        message = "Network error. Please check your connection and try again.";
      } else if (
        typeof (error_ as Error).message === "string" &&
        !error_.message.includes("[object")
      ) {
        message = error_.message;
      }
      setSaveError(message);
      pushToast({
        title: "Failed to save skills",
        description: message,
        tone: "error",
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

    if (!contactInfo.email?.trim()) {
      errors.email = "Required";
    } else if (!isValidEmail(contactInfo.email)) {
      errors.email = "Invalid format";
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setFormErrors({});
    setSaveError(null);
    setIsSavingContact(true);

    try {
      const trimmedContact = {
        ...contactInfo,
        first_name: contactInfo.first_name.trim(),
        last_name: contactInfo.last_name.trim(),
        email: contactInfo.email.trim(),
        phone: contactInfo.phone?.trim(),
      };

      await retryWithBackoff(() =>
        updateProfile({
          contact: trimmedContact,
          full_name: `${trimmedContact.first_name} ${trimmedContact.last_name}`,
        }),
      );
      pushToast({ title: "Contact info saved!", tone: "success" });

      nextStep();
    } catch (error) {
      const error_ = error as Error & { status?: number };
      if (import.meta.env.DEV)
        console.error("[Onboarding] Failed to save contact:", error_);
      const isNetworkError =
        !navigator.onLine || (error_.status && error_.status >= 500);
      let message = "Please try again";
      if (isNetworkError) {
        message = "Network error. Please check your connection and try again.";
      } else if (
        typeof (error_ as Error).message === "string" &&
        !error_.message.includes("[object")
      ) {
        message = error_.message;
      }
      setSaveError(message);
      pushToast({
        title: "Failed to save contact info",
        description: message,
        tone: "error",
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
      const salaryNumber = Number.parseInt(preferences.salary_min.trim());
      if (Number.isNaN(salaryNumber) || salaryNumber < 0) {
        errors.salary_min = "Must be a valid number";
      } else if (salaryNumber > SALARY_CAP) {
        errors.salary_min = `Min salary cannot exceed $${(SALARY_CAP / 1_000_000).toFixed(0)}M`;
      }
    }
    if (preferences.salary_max?.trim()) {
      const maxNumber = Number.parseInt(preferences.salary_max.trim());
      const minNumber = preferences.salary_min?.trim()
        ? Number.parseInt(preferences.salary_min.trim())
        : 0;
      if (Number.isNaN(maxNumber) || maxNumber < 0) {
        errors.salary_max = "Must be a valid number";
      } else if (maxNumber > SALARY_CAP) {
        errors.salary_max = `Max salary cannot exceed $${(SALARY_CAP / 1_000_000).toFixed(0)}M`;
      } else if (minNumber > 0 && maxNumber < minNumber) {
        errors.salary_max = "Max must be ≥ min";
      }
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setFormErrors({});
    setSaveError(null);
    setIsSavingPreferences(true);

    try {
      const trimmedPrefs = {
        ...preferences,
        location: (preferences.location ?? "").trim(),
        role_type: (preferences.role_type ?? "").trim(),
        salary_min: (preferences.salary_min ?? "").trim(),
      };

      // Cache preferences data
      await cacheService.cacheUserPreferences(
        profile?.id || "anonymous",
        trimmedPrefs,
      );

      const prefs: import("../../hooks/useProfile").Preferences = {
        location: trimmedPrefs.location,
        role_type: trimmedPrefs.role_type,
        salary_min: Number.parseInt(trimmedPrefs.salary_min) || 0,
        salary_max: trimmedPrefs.salary_max?.trim()
          ? Number.parseInt(trimmedPrefs.salary_max.trim())
          : undefined,
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
          },
        });
      }
      pushToast({ title: "Preferences saved!", tone: "success" });

      nextStep();
    } catch (error) {
      const error_ = error as Error & { status?: number };
      const message =
        typeof error_.message === "string" &&
        !error_.message.includes("[object")
          ? error_.message
          : "Please try again";
      if (import.meta.env.DEV)
        console.error("[Onboarding] Failed to save preferences:", error_);
      setSaveError(message);
      pushToast({
        title: "Failed to save preferences",
        description: message,
        tone: "error",
      });
    } finally {
      setIsSavingPreferences(false);
    }
  };

  const handleSaveCareerGoals = async () => {
    setSaveError(null);
    // F5: Explicit validation before submit (e.g. Ctrl+Enter bypasses button disabled)
    if (!careerGoals.experience_level?.trim() || !careerGoals.urgency?.trim()) {
      setSaveError(
        t("onboarding.careerGoalsRequired", locale) ||
          "Please select experience level and search urgency.",
      );
      return;
    }
    try {
      setIsSavingCareerGoals(true);
      // Map frontend values to backend enums (experience_level: entry|mid|senior|staff, urgency: passive|casual|active|urgent)
      const expMap: Record<string, string> = {
        "0-1": "entry",
        "1-3": "entry",
        "3-5": "mid",
        "5-10": "senior",
        "10+": "staff",
      };
      const urgencyMap: Record<string, string> = {
        active: "active",
        open: "casual",
        exploring: "passive",
      };
      await updateProfile({
        career_goals: {
          experience_level:
            expMap[careerGoals.experience_level] ?? careerGoals.experience_level,
          urgency:
            urgencyMap[careerGoals.urgency] ?? careerGoals.urgency,
          primary_goal: careerGoals.primary_goal,
          why_leaving: careerGoals.why_leaving,
        },
      });
      updateFormData({ careerGoals });
      pushToast({ title: "Career goals saved!", tone: "success" });
      nextStep();
    } catch (error) {
      const error_ = error as Error & { status?: number };
      const message =
        typeof error_.message === "string" &&
        !error_.message.includes("[object")
          ? error_.message
          : "Please try again";
      if (import.meta.env.DEV)
        console.error("[Onboarding] Failed to save career goals:", error_);
      setSaveError(message);
      pushToast({
        title: "Failed to save career goals",
        description: message,
        tone: "error",
      });
    } finally {
      setIsSavingCareerGoals(false);
    }
  };

  // I1: Ref guard prevents double-submit before React state update (rapid double-click)
  const completingReference = React.useRef(false);
  // C4: Debounce handleComplete to prevent double-click
  const lastCompleteReference = React.useRef(0);
  const handleComplete = async () => {
    if (Date.now() - lastCompleteReference.current < 200) return;
    lastCompleteReference.current = Date.now();
    if (completingReference.current) return;
    completingReference.current = true;
    setSaveError(null);
    try {
      setIsCompleting(true);
      // O20: Validation before completion (names, email) handled by useProfile hook
      await completeOnboarding();

      // A4: Call growth endpoint; surface non-critical failure so user knows
      let growthFailed = false;
      try {
        await api.post("/onboarding/complete", {});
      } catch (error) {
        growthFailed = true;
        if (import.meta.env.DEV)
          console.warn(
            "[Onboarding] Growth endpoint failed but profile marked complete:",
            error,
          );
      }

      resetOnboarding();
      sessionStorage.setItem("onboarding_just_completed", "true");
      sessionStorage.setItem("show_first_steps", "true");
      telemetry.track("onboarding_completed", {
        step: "ready",
        total_steps: steps.length,
        final_progress: Math.round(progress),
        has_resume: !!profile?.resume_url,
        has_skills: richSkills.length > 0,
        has_preferences: !!preferences.location && !!preferences.role_type,
      });
      if (growthFailed) {
        pushToast({
          title: t("onboarding.allSet", locale) || "You're all set!",
          description:
            t("onboarding.growthEndpointHint", locale) ||
            "One optional step didn't complete. You're ready to job hunt!",
          tone: "warning",
        });
      } else {
        pushToast({
          title:
            t("onboarding.allSet", locale) || "You're all set! Let's job hunt!",
          tone: "success",
        });
      }
      navigate("/app/dashboard");
    } catch (error) {
      const error_ = error as Error & { status?: number };
      const message =
        typeof error_.message === "string" &&
        !error_.message.includes("[object")
          ? error_.message
          : t("onboarding.somethingWrong", locale) ||
            "Something went wrong. Please try again.";
      if (import.meta.env.DEV)
        console.error("[Onboarding] Failed to complete:", error_);
      setSaveError(message);
      pushToast({
        title:
          t("onboarding.somethingWrong", locale) ||
          "We couldn't complete that. Please try again.",
        description: message,
        tone: "error",
      });
    } finally {
      setIsCompleting(false);
      completingReference.current = false; // Allow retry on failure
    }
  };

  // #19: Ctrl+Enter / Cmd+Enter to continue; Alt+Arrow for prev/next (single handler to avoid double-submit)
  // N3: Use ref for handlers to avoid effect re-run on every render
  const handlersReference = React.useRef({
    handleResumeNext,
    handleConfirmParsing,
    handleSaveSkills,
    handleSaveContact,
    handleSavePreferences,
    handleSaveWorkStyle,
    handleSaveCareerGoals,
    handleComplete,
    nextStep,
    prevStep,
    showParsingPreview,
    parsedResume,
    isSavingPreferences,
    isSavingContact,
    isSavingSkills,
    isSavingWorkStyle,
    isSavingCareerGoals,
    isCompleting,
    isUploading,
    currentStepData,
    isFirstStep,
  });
  handlersReference.current = {
    handleResumeNext,
    handleConfirmParsing,
    handleSaveSkills,
    handleSaveContact,
    handleSavePreferences,
    handleSaveWorkStyle,
    handleSaveCareerGoals,
    handleComplete,
    nextStep,
    prevStep,
    showParsingPreview,
    parsedResume,
    isSavingPreferences,
    isSavingContact,
    isSavingSkills,
    isSavingWorkStyle,
    isSavingCareerGoals,
    isCompleting,
    isUploading,
    currentStepData,
    isFirstStep,
  };
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const h = handlersReference.current;
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        if (document.activeElement?.closest('[role="dialog"]')) return;
        const stepId = h.currentStepData?.id;
        if (!stepId) return;
        if (
          h.isSavingPreferences ||
          h.isSavingContact ||
          h.isSavingSkills ||
          h.isSavingWorkStyle ||
          h.isSavingCareerGoals ||
          h.isCompleting ||
          h.isUploading
        )
          return;
        e.preventDefault();
        switch (stepId) {
          case "welcome": {
            h.nextStep();
            break;
          }
          case "resume": {
            (h.showParsingPreview && h.parsedResume
              ? h.handleConfirmParsing
              : h.handleResumeNext)();
            break;
          }
          case "skill-review": {
            h.handleSaveSkills();
            break;
          }
          case "confirm-contact": {
            h.handleSaveContact();
            break;
          }
          case "preferences": {
            h.handleSavePreferences();
            break;
          }
          case "work-style": {
            h.handleSaveWorkStyle();
            break;
          }
          case "career-goals": {
            h.handleSaveCareerGoals();
            break;
          }
          case "ready": {
            {
              h.handleComplete();
              // No default
            }
            break;
          }
        }
      } else if (e.altKey && e.key === "ArrowLeft" && !h.isFirstStep) {
        e.preventDefault();
        h.prevStep();
      } else if (e.altKey && e.key === "ArrowRight") {
        if (
          h.isSavingPreferences ||
          h.isSavingContact ||
          h.isSavingSkills ||
          h.isSavingWorkStyle ||
          h.isSavingCareerGoals ||
          h.isCompleting ||
          h.isUploading
        )
          return;
        e.preventDefault();
        const stepId = h.currentStepData?.id;
        switch (stepId) {
          case "welcome": {
            h.nextStep();
            break;
          }
          case "resume": {
            (h.showParsingPreview && h.parsedResume
              ? h.handleConfirmParsing
              : h.handleResumeNext)();
            break;
          }
          case "skill-review": {
            h.handleSaveSkills();
            break;
          }
          case "confirm-contact": {
            h.handleSaveContact();
            break;
          }
          case "preferences": {
            h.handleSavePreferences();
            break;
          }
          case "work-style": {
            h.handleSaveWorkStyle();
            break;
          }
          case "career-goals": {
            h.handleSaveCareerGoals();
            break;
          }
          case "ready": {
            {
              h.handleComplete();
              // No default
            }
            break;
          }
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []); // N3: Empty deps - handler reads from ref

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
        <Confetti
          active={showStepConfetti}
          onComplete={() => setShowStepConfetti(false)}
        />
        {/* Minimal Header */}
        <header className="px-3 md:px-6 h-11 md:h-12 shrink-0 flex items-center justify-between bg-white/90 backdrop-blur-sm border-b border-[#E9E9E7] z-50 sticky top-0">
          <Logo to="/app/onboarding" size="sm" />
          <div className="flex items-center gap-2 md:gap-4">
            {/* OB1: Progress Persistence Warning - Show auto-save indicator */}
            <div className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-50 border border-emerald-200">
              <div
                className="w-1.5 h-1.5 rounded-full bg-emerald-500"
                aria-hidden
              />
              <span className="text-[9px] font-medium text-emerald-700">
                {t("onboarding.autoSaved", locale) || "Auto-saved"}
              </span>
            </div>
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#455DD3]/10 border border-[#455DD3]/20">
              <div
                className="w-2 h-2 rounded-full bg-[#455DD3] animate-pulse"
                aria-hidden
              />
              <span className="text-[10px] font-black text-[#455DD3] uppercase tracking-widest">
                {t("onboarding.settingUpProfile", locale) ||
                  "Setting up your profile"}
              </span>
            </div>
            <div className="lg:hidden flex items-center gap-1.5 px-2 py-1 rounded-full bg-[#455DD3]/10 border border-[#455DD3]/20">
              <div
                className="w-1.5 h-1.5 rounded-full bg-[#455DD3] animate-pulse"
                aria-hidden
              />
              <span className="text-[9px] font-black text-[#455DD3] uppercase tracking-wider">
                {t("onboarding.setup", locale) || "Setup"}
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowRestartConfirm(true)}
              className="text-[#787774] text-[10px] md:text-xs font-bold uppercase hover:bg-[#E9E9E7]"
              title={
                t("onboarding.clearProgress", locale) ||
                "Clear progress and start over"
              }
              aria-label={
                t("onboarding.restartOnboarding", locale) ||
                "Restart onboarding and clear progress"
              }
            >
              {t("onboarding.restart", locale) || "Restart"}
            </Button>
            <ConfirmModal
              isOpen={showRestartConfirm}
              onClose={() => setShowRestartConfirm(false)}
              onConfirm={() => {
                resetOnboarding();
                setShowRestartConfirm(false);
              }}
              title={
                t("onboarding.confirmRestartTitle", locale) ||
                "Restart onboarding?"
              }
              description={
                t("onboarding.confirmRestart", locale) ||
                "Are you sure? This will clear your progress."
              }
              confirmText={t("onboarding.restart", locale) || "Restart"}
              cancelText={t("onboarding.cancel", locale) || "Cancel"}
              variant="warning"
            />
          </div>
        </header>

        <main
          className="flex-1 w-full flex flex-col items-center p-4 md:p-6 lg:p-8"
          id="main-content"
          aria-label="Onboarding"
        >
          <div className="w-full max-w-xl lg:max-w-4xl xl:max-w-5xl">
            {/* Progress bar */}
            <div
              className="mb-4 md:mb-6"
              role="progressbar"
              aria-valuenow={currentStep + 1}
              aria-valuemin={1}
              aria-valuemax={steps.length}
              aria-label={`Setup progress: step ${currentStep + 1} of ${steps.length}`}
            >
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-[10px] md:text-xs font-bold text-[#9B9A97] uppercase tracking-wider">
                  {t("onboarding.step", locale) || "Step"} {currentStep + 1}{" "}
                  {t("onboarding.of", locale) || "of"} {steps.length} —{" "}
                  {progress.toFixed(0)}%
                </span>
                <span className="text-[10px] md:text-xs font-bold text-[#455DD3] uppercase tracking-wider">
                  {currentStepData.title}
                </span>
              </div>
              {/* OB1: Progress Persistence Warning - Show auto-save indicator */}
              <div className="flex items-center gap-1.5 mb-2 px-1">
                <div className="flex items-center gap-1 text-[9px] text-emerald-600 font-medium">
                  <div
                    className="w-1.5 h-1.5 rounded-full bg-emerald-500"
                    aria-hidden
                  />
                  <span>
                    {t("onboarding.progressAutoSaved", locale) ||
                      "Your progress is saved automatically"}
                  </span>
                </div>
              </div>
              <div className="h-1.5 w-full rounded-full bg-[#E9E9E7] overflow-hidden">
                <motion.div
                  initial={
                    shouldReduceMotion
                      ? { width: `${progress}%` }
                      : { width: 0 }
                  }
                  animate={{ width: `${progress}%` }}
                  className="h-full bg-[#455DD3]"
                  transition={
                    shouldReduceMotion
                      ? { duration: 0 }
                      : { duration: 0.4, ease: [0.4, 0, 0.2, 1] }
                  }
                />
              </div>
              {/* N2: Clickable step dots - jump to completed/current steps */}
              <div
                className="flex gap-1 mt-2"
                role="group"
                aria-label={
                  t("onboarding.step", locale) +
                  " " +
                  (currentStep + 1) +
                  " " +
                  (t("onboarding.of", locale) || "of") +
                  " " +
                  steps.length
                }
              >
                {steps.map((s, index) => {
                  const isCompleted =
                    completedSteps.includes(s.id) || index < currentStep;
                  const isCurrent = index === currentStep;
                  const canJump = isCompleted || isCurrent;
                  return (
                    <button
                      key={s.id}
                      type="button"
                      aria-current={isCurrent ? "step" : undefined}
                      aria-label={`${t("onboarding.step", locale) || "Step"} ${index + 1}: ${s.title}`}
                      onClick={() => canJump && goToStep(index)}
                      className={`h-2 w-2 rounded-full transition-all min-h-[44px] min-w-[44px] flex items-center justify-center p-[18px] -m-[18px] ${
                        isCurrent
                          ? "bg-[#455DD3] ring-2 ring-[#455DD3]/30"
                          : isCompleted
                            ? "bg-[#455DD3]/60 hover:bg-[#455DD3]/80"
                            : "bg-[#E9E9E7] cursor-default"
                      }`}
                      disabled={!canJump}
                    />
                  );
                })}
              </div>
              <p
                className="mt-1 text-[9px] text-[#9B9A97] hidden sm:block"
                aria-hidden
              >
                {t("onboarding.keyboardHint", locale) ||
                  "Ctrl+Enter to continue"}
              </p>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                ref={stepContainerReference}
                key={currentStep}
                initial={shouldReduceMotion ? undefined : { opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={shouldReduceMotion ? undefined : { opacity: 0 }}
                transition={
                  shouldReduceMotion ? { duration: 0 } : { duration: 0.2 }
                }
                className="w-full"
              >
                <Card
                  tone="glass"
                  shadow="lift"
                  className="p-4 md:p-6 lg:p-8 border-[#E9E9E7] bg-white/95"
                >
                  {/* ProgressRing + Motivational Copy */}
                  <div className="mb-4 md:mb-6 flex flex-col items-center">
                    <ProgressRing
                      progress={completeness}
                      stepLabel={`${currentStep + 1} of ${steps.length}`}
                      size={100}
                      strokeWidth={5}
                    />
                    <p className="mt-2 text-xs md:text-sm font-bold text-[#787774] text-center max-w-xs">
                      {stepMotivationalCopy[currentStepData.id] ||
                        t("onboarding.buildingProfile", locale) ||
                        "Building your profile"}
                    </p>
                    {/* Completion badges */}
                    <div className="flex flex-wrap gap-1.5 mt-3 justify-center">
                      {(profile?.resume_url || resumeFile) && (
                        <Badge className="text-[8px] font-bold uppercase tracking-wider bg-[#17BEBB]/10 text-[#17BEBB] border-[#17BEBB]/20 px-1.5 py-0.5">
                          <CheckCircle2
                            className="mr-0.5 h-2.5 w-2.5"
                            aria-hidden
                          />
                          {t("onboarding.resumeBadge", locale) || "Resume"}
                        </Badge>
                      )}
                      {preferences.location && (
                        <Badge className="text-[8px] font-bold uppercase tracking-wider bg-[#17BEBB]/10 text-[#17BEBB] border-[#17BEBB]/20 px-1.5 py-0.5">
                          <CheckCircle2
                            className="mr-0.5 h-2.5 w-2.5"
                            aria-hidden
                          />
                          {t("onboarding.locationBadge", locale) || "Location"}
                        </Badge>
                      )}
                      {preferences.role_type && (
                        <Badge className="text-[8px] font-bold uppercase tracking-wider bg-[#17BEBB]/10 text-[#17BEBB] border-[#17BEBB]/20 px-1.5 py-0.5">
                          <CheckCircle2
                            className="mr-0.5 h-2.5 w-2.5"
                            aria-hidden
                          />
                          {t("onboarding.roleBadge", locale) || "Role"}
                        </Badge>
                      )}
                      {richSkills.length > 0 && (
                        <Badge className="text-[8px] font-bold uppercase tracking-wider bg-[#17BEBB]/10 text-[#17BEBB] border-[#17BEBB]/20 px-1.5 py-0.5">
                          <CheckCircle2
                            className="mr-0.5 h-2.5 w-2.5"
                            aria-hidden
                          />
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
                        {saveError &&
                          [
                            "skill-review",
                            "confirm-contact",
                            "preferences",
                            "work-style",
                            "career-goals",
                            "ready",
                          ].includes(currentStepData?.id || "") && (
                            <div
                              className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex items-start gap-2"
                              role="alert"
                            >
                              <span className="shrink-0">⚠</span>
                              <span className="flex-1">{saveError}</span>
                              <button
                                type="button"
                                onClick={() => setSaveError(null)}
                                className="shrink-0 text-red-600 hover:underline text-xs font-medium"
                                aria-label={
                                  t("dashboard.dismiss", locale) || "Dismiss"
                                }
                              >
                                {t("dashboard.dismiss", locale) || "Dismiss"}
                              </button>
                            </div>
                          )}
                        {currentStepData.id === "welcome" && (
                          <React.Suspense fallback={<OnboardingSkeleton />}>
                            <WelcomeStep
                              onNext={nextStep}
                              shouldReduceMotion={!!shouldReduceMotion}
                              firstName={profile?.contact?.first_name}
                            />
                          </React.Suspense>
                        )}

                        {currentStepData.id === "resume" && (
                          <>
                            <React.Suspense fallback={<ResumeStepSkeleton />}>
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
                            </React.Suspense>

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
                          <React.Suspense
                            fallback={<SkillReviewStepSkeleton />}
                          >
                            <SkillReviewStep
                              onNext={handleSaveSkills}
                              onPrev={prevStep}
                              richSkills={richSkills}
                              setRichSkills={setRichSkills}
                              isSaving={isSavingSkills}
                            />
                          </React.Suspense>
                        )}

                        {currentStepData.id === "confirm-contact" && (
                          <React.Suspense fallback={<OnboardingSkeleton />}>
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
                                setContactInfo((previous) => ({
                                  ...previous,
                                  email: `${(previous.email ?? "").split("@")[0]}@${suggestion}`,
                                }));
                                setEmailTypoSuggestion(null);
                              }}
                              onClearError={(field) =>
                                setFormErrors((previous) => {
                                  const updated = { ...previous };
                                  delete updated[field];
                                  return updated;
                                })
                              }
                              onSetFormError={(field, error) =>
                                setFormErrors((previous) => ({
                                  ...previous,
                                  [field]: error,
                                }))
                              }
                            />
                          </React.Suspense>
                        )}

                        {currentStepData.id === "preferences" && (
                          <React.Suspense
                            fallback={<PreferencesStepSkeleton />}
                          >
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
                                rolesLoading: aiSuggestions.roles.loading,
                                salaryLoading: aiSuggestions.salary.loading,
                                locationsLoading:
                                  aiSuggestions.locations.loading,
                                rolesError: aiSuggestions.roles.error,
                                salaryError: aiSuggestions.salary.error,
                                locationsError: aiSuggestions.locations.error,
                              }}
                              formErrors={formErrors}
                              hasParsedProfile={!!parsedProfile}
                              onClearError={(field) =>
                                setFormErrors((previous) => {
                                  const updated = { ...previous };
                                  delete updated[field];
                                  return updated;
                                })
                              }
                            />
                          </React.Suspense>
                        )}

                        {currentStepData.id === "work-style" && (
                          <React.Suspense fallback={<OnboardingSkeleton />}>
                            <WorkStyleStep
                              onNext={handleSaveWorkStyle}
                              onPrev={prevStep}
                              answers={workStyleAnswers}
                              setAnswers={setWorkStyleAnswers}
                              isSaving={isSavingWorkStyle}
                            />
                          </React.Suspense>
                        )}

                        {currentStepData.id === "career-goals" && (
                          <React.Suspense fallback={<OnboardingSkeleton />}>
                            <CareerGoalsStep
                              onNext={handleSaveCareerGoals}
                              onPrev={prevStep}
                              careerGoals={careerGoals}
                              setCareerGoals={setCareerGoals}
                              isSaving={isSavingCareerGoals}
                            />
                          </React.Suspense>
                        )}

                        {currentStepData.id === "ready" && (
                          <React.Suspense fallback={<OnboardingSkeleton />}>
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
                          </React.Suspense>
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
