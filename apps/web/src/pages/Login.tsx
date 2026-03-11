import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { useAuth } from '../hooks/useAuth';
import { pushToast } from '../lib/toast';
import {
  ArrowRight, AlertCircle,
  MailCheck, Briefcase, Send, Zap, Loader2,
  Lock, ShieldCheck
} from 'lucide-react';
import { Logo } from '../components/brand/Logo';
import { ThemeToggle } from '../components/ThemeToggle';
import { LanguageSelector } from '../components/LanguageSelector';
import { Button } from '../components/ui/Button';
import { cn } from '../lib/utils';
import { magicLinkService } from '../services/magicLinkService';
import { ValidationUtils } from '../lib/validation';
import { checkEmailTypo } from '../lib/emailUtils';
import { telemetry } from '../lib/telemetry';
import { t, formatT, getLocale } from '../lib/i18n';
import { SocialLoginGroup, SocialLoginDivider } from '../components/auth/SocialLogin';
import { CaptchaField } from '../components/ui/Captcha';
import { SkipLink } from '../components/SkipLink';
import { SEO } from '../components/marketing/SEO';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  const returnTo = searchParams.get("returnTo");

  const safeReturnTo = useMemo(() => {
    if (returnTo && returnTo.startsWith("/") && !returnTo.startsWith("//")) {
      return returnTo;
    }
    const storedReturnTo = sessionStorage.getItem('magicLinkReturnTo');
    if (storedReturnTo) {
      sessionStorage.removeItem('magicLinkReturnTo');
      if (storedReturnTo.startsWith("/") && !storedReturnTo.startsWith("//")) {
        return storedReturnTo;
      }
    }
    return "/app/onboarding";
  }, [returnTo]);

  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successState, setSuccessState] = useState<{ email: string } | null>(null);
  const [resendLoading, setResendLoading] = useState(false);
  const [rateLimitCountdown, setRateLimitCountdown] = useState<number | null>(null);
  const [focused, setFocused] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestionHighlight, setSuggestionHighlight] = useState(0);
  const [captchaToken, setCaptchaToken] = useState<string>("");
  const [showCaptcha, setShowCaptcha] = useState(false);
  const [isMouseOverSuggestions, setIsMouseOverSuggestions] = useState(false);

  const emailDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com', 'me.com', 'aol.com', 'protonmail.com', 'zoho.com', 'mail.com'];

  const getEmailSuggestions = () => {
    const atIndex = email.lastIndexOf('@');
    if (atIndex === -1) return [];
    const prefix = email.slice(0, atIndex);
    const partialDomain = email.slice(atIndex + 1).toLowerCase();
    if (!partialDomain) return emailDomains.map(d => `${prefix}@${d}`);
    return emailDomains
      .filter(d => d.startsWith(partialDomain))
      .map(d => `${prefix}@${d}`);
  };

  // H9: Loading States - Show loading during token verification
  const [isVerifying, setIsVerifying] = useState(false);
  
  useEffect(() => {
    const token = searchParams.get('token');
    if (token && !isVerifying) {
      setIsVerifying(true);
      // Token verification happens via backend redirect, show loading state
    }
  }, [searchParams, isVerifying]);
  
  useEffect(() => {
    if (!authLoading && user) {
      navigate(safeReturnTo, { replace: true });
    }
  }, [authLoading, user, navigate, safeReturnTo]);

  useEffect(() => {
    if (sessionStorage.getItem('session_expired') === 'true') {
      sessionStorage.removeItem('session_expired');
      pushToast({ title: t("login.sessionExpired", getLocale()), description: t("login.signInAgain", getLocale()), tone: "info" });
    }
  }, []);

  useEffect(() => {
    const error = searchParams.get('error');
    const hint = searchParams.get('hint');
    if (error === 'auth_failed') {
      setIsVerifying(false);
      const messages: Record<string, string> = {
        expired: 'Your magic link has expired. Request a new one below.',
        used: 'This link was already used. Request a new one below.',
        invalid: 'This link is invalid or expired. Request a new one below.',
        ip_mismatch: 'This link was opened from a different device or network. Request a new one from the same place you signed in.',
      };
      setFormError(messages[hint || ''] || 'Your magic link has expired or was already used. Please request a new one.');
      telemetry.track("magic_link_failed", { reason: "auth_failed", hint: hint || "unknown" });
    }
  }, [searchParams]);

  const emailIsValid = useMemo(() => {
    return ValidationUtils.validate.email(email.trim()).isValid;
  }, [email]);

  useEffect(() => {
    if (!rateLimitCountdown || rateLimitCountdown <= 0) return;
    const timer = setInterval(() => {
      setRateLimitCountdown(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          return null;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [rateLimitCountdown]);

  const requestMagicLink = async (targetEmail: string, destination: string, token?: string) => {
    const result = await magicLinkService.sendMagicLink(targetEmail, destination, token);
    if (!result.success) {
      if (result.retryAfter) setRateLimitCountdown(result.retryAfter);
      if (result.captchaRequired) {
        setShowCaptcha(true);
        const err = new Error(result.error || "Please complete the captcha verification") as Error & { status?: number };
        err.status = result.status;
        throw err;
      }
      const err = new Error(result.error || "Magic link failed") as Error & { status?: number };
      err.status = result.status;
      throw err;
    }
    return result.email;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailIsValid) return;

    // #6: Email typo detection - auto-correct and proceed
    const trimmed = email.trim();
    const typoSuggestion = checkEmailTypo(trimmed);
    const emailToSend = typoSuggestion
      ? `${trimmed.split("@")[0]}@${typoSuggestion}`
      : trimmed;
    if (typoSuggestion) {
      setEmail(emailToSend);
      pushToast({ title: "Email corrected", description: `Sent to ${emailToSend}`, tone: "info" });
    }

    setIsLoading(true);
    setFormError(null);

    try {
      const normalized = await requestMagicLink(emailToSend, safeReturnTo, captchaToken || undefined);
      setShowCaptcha(false);
      setCaptchaToken("");
      telemetry.track("login_magic_link_requested", { usedCaptcha: !!captchaToken, destination: safeReturnTo });
      setSuccessState({ email: normalized || email.trim().toLowerCase() });
      pushToast({ title: "Check your inbox", tone: "success" });
    } catch (error) {
      const err = error as Error & { status?: number };
      let msg = "We couldn't send your magic link. Please check your email and try again.";
      const m = err.message || "";
      const status = err.status;
      if (m.includes('rate limit') || m.includes('too many requests') || status === 429) {
        msg = "Too many requests. Please wait a few minutes before trying again.";
      } else if (m.includes('captcha') || m.includes('CAPTCHA')) {
        msg = "Please complete the captcha verification and try again.";
      } else if (m.includes('invalid email')) {
        msg = "Please enter a valid email address.";
      } else if (m.includes('network') || m.includes('connection') || m.includes('fetch')) {
        msg = "Network error. Please check your connection and try again.";
      } else if (status === 502 || status === 503 || m.includes('temporarily unavailable')) {
        msg = "Email service temporarily unavailable. Please try again in a moment.";
      } else if (status === 504 || m.includes('timeout')) {
        msg = "Request timed out. Please try again.";
      } else if (typeof m === 'string' && m.length > 0 && !m.includes('[object')) {
        msg = m;
      }
      setFormError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const triggerConfetti = useCallback(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };
    const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;

    const interval: ReturnType<typeof setInterval> = setInterval(function () {
      const timeLeft = animationEnd - Date.now();
      if (timeLeft <= 0) return clearInterval(interval);
      const particleCount = 50 * (timeLeft / duration);
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
    }, 250);
  }, []);

  useEffect(() => {
    if (successState) {
      const hasLoggedInBefore = localStorage.getItem('jobhuntin_has_logged_in');
      if (!hasLoggedInBefore) {
        triggerConfetti();
        localStorage.setItem('jobhuntin_has_logged_in', 'true');
      }
    }
  }, [successState, triggerConfetti]);

  if (successState) {
    return (
      <>
        <SEO title="Check Your Email | JobHuntin" description="We sent you a magic link. Check your inbox to sign in." noindex />
        <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)' }}>
        {/* M6: Skip link for keyboard navigation */}
        <SkipLink href="#login-form">Skip to login form</SkipLink>
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(69,93,211,0.12) 0%, transparent 60%)' }} />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative w-full max-w-md"
        >
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-8 sm:p-10">
            <div className="text-center mb-8" role="alert">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6" style={{ background: 'rgba(69,93,211,0.2)' }}>
                <MailCheck className="w-8 h-8 text-[#7DD3CF]" />
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white mb-3 tracking-tight" style={{ letterSpacing: '-1px' }}>
                {t("login.checkInbox", getLocale())}
              </h1>
              <p className="text-white/70 leading-relaxed">
                {t("login.sentTo", getLocale())}<br />
                <span className="font-semibold text-white">{successState.email}</span>
              </p>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(successState.email);
                  pushToast({ title: "Email copied", tone: "success" });
                }}
                aria-label={`Copy email address ${successState.email} to clipboard`}
                className="mt-2 text-xs text-[#7DD3CF] hover:text-[#9EE7E4] font-medium flex items-center justify-center gap-1 mx-auto transition-colors focus:outline-none focus:ring-2 focus:ring-[#7DD3CF] focus:ring-offset-2 rounded"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy email
              </button>
              <p className="text-xs text-white/50 mt-3">
                {t("login.checkSpam", getLocale())}
              </p>
            </div>

            <div className="rounded-xl bg-white/5 border border-white/10 p-6 mb-6">
              <ol className="space-y-4">
                {[
                  t("login.step1", getLocale()),
                  t("login.step2", getLocale()),
                  t("login.step3", getLocale()),
                ].map((step, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + i * 0.1 }}
                    className="flex items-start gap-3"
                  >
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0" style={{ background: 'rgba(69,93,211,0.3)', color: 'white' }}>
                      {i + 1}
                    </div>
                    <span className="text-white/80 text-sm">{step}</span>
                  </motion.li>
                ))}
              </ol>
            </div>

            <div className="space-y-3">
              {formError && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 text-red-400 text-sm bg-red-500/20 border border-red-500/30 p-3 rounded-lg"
                >
                  <AlertCircle className="w-4 h-4" />
                  {formError}
                </motion.div>
              )}
              <Button
                variant="ghost"
                aria-busy={resendLoading}
                onClick={async () => {
                  try {
                    setResendLoading(true);
                    await requestMagicLink(successState.email, safeReturnTo, captchaToken || undefined);
                    pushToast({ title: "Link resent", tone: "success" });
                  } catch (error) {
                    const err = error as Error;
                    const msg = (typeof err?.message === 'string' && !err.message.includes('[object')) ? err.message : "Failed to resend. Please try again.";
                    setFormError(msg);
                  } finally {
                    setResendLoading(false);
                  }
                }}
                disabled={resendLoading || !!rateLimitCountdown || (showCaptcha && !captchaToken)}
                className="w-full text-white/90 hover:bg-white/10 hover:text-white border border-white/20 focus:ring-2 focus:ring-[#455DD3] focus:outline-none"
              >
                {resendLoading ? t("login.sending", getLocale()) : rateLimitCountdown ? formatT("login.resendIn", { seconds: String(rateLimitCountdown) }, getLocale()) : t("login.resendLink", getLocale())}
              </Button>
              <Button variant="outline" onClick={() => setSuccessState(null)} className="w-full border-white/30 text-white hover:bg-white/10 focus:ring-2 focus:ring-[#455DD3] focus:outline-none">
                {t("login.useDifferentEmail", getLocale())}
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
      </>
    );
  }

  // H9: Loading States - Show loading overlay during token verification
  if (isVerifying) {
    return (
      <>
        <SEO title="Verifying | JobHuntin" description="Verifying your sign-in link." noindex />
        <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)' }} role="status" aria-live="polite" aria-label="Verifying your sign-in link">
        <div className="text-center space-y-4 max-w-sm px-6">
          <Loader2 className="w-14 h-14 text-[#7DD3CF] animate-spin mx-auto" aria-hidden />
          <h2 className="text-xl font-bold text-white">Verifying your magic link...</h2>
          <p className="text-white/70">Please wait while we sign you in. This usually takes a few seconds.</p>
          <div className="h-1 w-32 mx-auto rounded-full bg-white/20 overflow-hidden">
            <div className="h-full w-1/3 bg-[#7DD3CF] rounded-full animate-pulse" />
          </div>
        </div>
      </div>
      </>
    );
  }

  return (
    <>
      <SEO title="Sign In | JobHuntin" description="Sign in to JobHuntin to access your job search dashboard." noindex />
      <a href="#login-form" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#455DD3] focus:text-white focus:rounded-lg focus:font-medium">
        Skip to login form
      </a>

      <div className="min-h-screen flex">
        {/* Left — Hero panel (homepage style) */}
        <div className="hidden lg:flex lg:w-[48%] xl:w-[45%] relative overflow-hidden" style={{ background: 'linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)' }}>
          <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(69,93,211,0.15) 0%, transparent 60%)' }} />
          <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-60" preserveAspectRatio="none" viewBox="0 0 1440 800" aria-hidden="true">
            <path d="M-100 500 C200 380, 500 620, 800 450 S1200 300, 1540 420" stroke="#455DD3" strokeOpacity="0.15" strokeWidth="2" fill="none" />
            <path d="M-100 550 C300 430, 600 670, 900 500 S1300 350, 1540 470" stroke="#7B93DB" strokeOpacity="0.1" strokeWidth="1.5" fill="none" />
          </svg>

          <div className="relative z-10 flex flex-col justify-between p-12 xl:p-16 w-full">
            <Logo to="/" variant="dark" size="md" />

            <div className="space-y-10 max-w-md">
              <div>
                <h2 className="text-3xl xl:text-4xl font-bold text-white leading-tight mb-4" style={{ letterSpacing: '-1.5px' }}>
                  {t("login.sidebarTitleLine1", getLocale())}{" "}
                  <span className="text-[#7DD3CF]">{t("login.sidebarTitleLine2", getLocale())}</span>
                </h2>
                <p className="text-white/70 text-base leading-relaxed">
                  {t("login.sidebarSubtitle", getLocale())}
                </p>
              </div>

              <div className="space-y-4">
                {[
                  { icon: Zap, text: t("login.feature1", getLocale()) },
                  { icon: Briefcase, text: t("login.feature2", getLocale()) },
                  { icon: Send, text: t("login.feature3", getLocale()) },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0" style={{ background: 'rgba(69,93,211,0.2)' }}>
                      <item.icon className="w-5 h-5 text-[#7DD3CF]" />
                    </div>
                    <span className="text-white/80 text-sm font-medium">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-6 text-sm text-white/50">
              <Link to="/terms" className="hover:text-white/80 transition-colors font-medium">Terms</Link>
              <Link to="/privacy" className="hover:text-white/80 transition-colors font-medium">Privacy</Link>
              <a href="mailto:support@jobhuntin.com" className="hover:text-white/80 transition-colors font-medium">Support</a>
            </div>
          </div>
        </div>

        {/* Right — Form (homepage white section style) */}
        <div className="w-full lg:w-[52%] xl:w-[55%] flex flex-col p-6 sm:p-8 lg:p-12 xl:p-16 bg-[#F7F6F3] dark:bg-slate-900 relative">
          {/* Mobile: subtle top gradient for visual interest */}
          <div className="lg:hidden absolute top-0 left-0 right-0 h-32 pointer-events-none bg-gradient-to-b from-[#455DD3]/5 to-transparent dark:from-[#455DD3]/10" aria-hidden />
          {/* Top bar: controls right (navbar has logo, avoid duplicate) */}
          <div className="absolute top-6 left-6 right-6 flex items-center justify-end z-10">
            <div className="flex items-center gap-2">
              <LanguageSelector />
              <ThemeToggle />
            </div>
          </div>

          <div className="w-full max-w-[400px] mx-auto flex-1 flex flex-col justify-center pt-16 lg:pt-0">
            <div className="lg:hidden text-center mb-8">
              <Logo to="/" variant="light" size="sm" className="mb-6 justify-center" />
              <h1 className="text-2xl font-bold text-[#2D2A26] dark:text-slate-100 mb-2 tracking-tight" style={{ letterSpacing: '-0.5px' }}>
                Sign in
              </h1>
              <p className="text-[#787774] dark:text-slate-400 text-sm">
                Enter your email to continue your job hunt
              </p>
            </div>

            <motion.div
              id="login-form"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="space-y-6"
            >
              <div className="hidden lg:block mb-8">
                <h1 className="text-2xl font-bold text-[#2D2A26] dark:text-slate-100 mb-2 tracking-tight" style={{ letterSpacing: '-0.5px' }}>
                  Sign in to your account
                </h1>
                <p className="text-[#787774] dark:text-slate-400 text-sm">
                  Enter your email and we'll send you a magic link
                </p>
              </div>

              <SocialLoginGroup
                onGoogleClick={() => { }}
                onLinkedInClick={() => { }}
                disabled={isLoading}
                showComingSoon={true}
              />
              <SocialLoginDivider />

              <motion.form
                onSubmit={handleSubmit}
                className="space-y-4"
                aria-label="Sign in with email"
                noValidate
                animate={formError ? "shake" : "idle"}
                variants={{
                  shake: { x: [0, -10, 10, -10, 10, 0], transition: { duration: 0.4 } },
                  idle: {}
                }}
              >
                <div className="relative">
                  <label htmlFor="login-email" className="block text-sm font-semibold text-[#2D2A26] dark:text-slate-100 mb-2">
                    {t("login.email", getLocale())}
                  </label>
                  <div className={cn(
                    "relative rounded-lg transition-all duration-200",
                    "focus-within:ring-2 focus-within:ring-[#455DD3]/30 focus-within:ring-offset-2",
                    focused && "ring-2 ring-[#455DD3]/20"
                  )}>
                    <input
                      type="text"
                      inputMode="email"
                      autoComplete="email"
                      placeholder={t("login.emailPlaceholder", getLocale())}
                      id="login-email"
                      value={email}
                      onChange={(e) => {
                        const val = e.target.value.trimStart();
                        setEmail(val);
                        const show = val.includes('@');
                        setShowSuggestions(show);
                        if (show) setSuggestionHighlight(0);
                        if (formError) setFormError(null);
                      }}
                      onPaste={(e) => {
                        const pasted = (e.clipboardData?.getData('text') || '').trim();
                        if (pasted && ValidationUtils.validate.email(pasted).isValid) {
                          e.preventDefault();
                          setEmail(pasted.toLowerCase());
                          setShowSuggestions(false);
                          setFormError(null);
                        }
                      }}
                      onFocus={() => {
                        setFocused(true);
                        setShowSuggestions(email.includes('@'));
                        setSuggestionHighlight(0);
                      }}
                      onBlur={() => {
                        if (!isMouseOverSuggestions) {
                          setFocused(false);
                          setShowSuggestions(false);
                        }
                      }}
                      onKeyDown={(e) => {
                        if (!showSuggestions || getEmailSuggestions().length === 0) return;
                        const suggestions = getEmailSuggestions().slice(0, 5);
                        if (e.key === 'ArrowDown') {
                          e.preventDefault();
                          setSuggestionHighlight((i) => (i + 1) % suggestions.length);
                        } else if (e.key === 'ArrowUp') {
                          e.preventDefault();
                          setSuggestionHighlight((i) => (i - 1 + suggestions.length) % suggestions.length);
                        } else if (e.key === 'Enter' && suggestions[suggestionHighlight]) {
                          e.preventDefault();
                          setEmail(suggestions[suggestionHighlight]);
                          setShowSuggestions(false);
                          setFocused(false);
                        } else if (e.key === 'Escape') {
                          setShowSuggestions(false);
                          setFocused(false);
                        }
                      }}
                      aria-autocomplete="list"
                      aria-expanded={showSuggestions && getEmailSuggestions().length > 0}
                      aria-controls="login-email-suggestions"
                      aria-activedescendant={showSuggestions && getEmailSuggestions().length > 0 ? `login-suggestion-${suggestionHighlight}` : undefined}
                      className={cn(
                        "w-full px-4 py-3.5 rounded-lg bg-white dark:bg-slate-800 border border-[#E9E9E7] dark:border-slate-700 transition-all text-[#2D2A26] dark:text-slate-100 placeholder:text-[#9B9A97] dark:placeholder:text-slate-500 text-base",
                        "focus:outline-none focus:border-[#455DD3] focus:ring-2 focus:ring-[#455DD3]/20",
                        "min-h-[48px] sm:min-h-[44px]",
                        formError ? "border-red-400 bg-red-50/50 dark:bg-red-900/20 dark:border-red-600" : "hover:border-[#D6D3D1] dark:hover:border-slate-600"
                      )}
                      aria-invalid={formError ? "true" : "false"}
                      aria-describedby={formError ? "login-email-error" : undefined}
                    />
                    {showSuggestions && getEmailSuggestions().length > 0 && (
                      <div
                        id="login-email-suggestions"
                        role="listbox"
                        className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-800 border border-[#E9E9E7] dark:border-slate-700 rounded-lg shadow-lg z-30 overflow-hidden max-h-60 overflow-y-auto"
                        onMouseEnter={() => setIsMouseOverSuggestions(true)}
                        onMouseLeave={() => setIsMouseOverSuggestions(false)}
                      >
                        {getEmailSuggestions().slice(0, 5).map((suggestion, index) => (
                          <button
                            key={index}
                            id={`login-suggestion-${index}`}
                            type="button"
                            role="option"
                            aria-selected={index === suggestionHighlight}
                            onClick={() => {
                              setEmail(suggestion);
                              setShowSuggestions(false);
                              setFocused(false);
                            }}
                            onMouseEnter={() => setSuggestionHighlight(index)}
                            className={cn(
                              "w-full px-4 py-2.5 text-left text-sm text-[#2D2A26] dark:text-slate-100 transition-colors",
                              index === suggestionHighlight ? "bg-[#F7F6F3] dark:bg-slate-700" : "hover:bg-[#F7F6F3] dark:hover:bg-slate-700"
                            )}
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {formError && (
                  <motion.div
                    id="login-email-error"
                    role="alert"
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 p-3 rounded-lg"
                  >
                    <AlertCircle className="w-4 h-4" aria-hidden />
                    {formError}
                  </motion.div>
                )}

                <AnimatePresence>
                  {showCaptcha && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <CaptchaField
                        value={captchaToken}
                        onChange={setCaptchaToken}
                        onValidate={(isValid) => { if (isValid) setFormError(null); }}
                        className="mb-4"
                      />
                    </motion.div>
                  )}
                </AnimatePresence>

                <button
                  type="submit"
                  disabled={isLoading || !emailIsValid}
                  aria-label={isLoading ? "Sending magic link..." : "Continue to sign in"}
                  aria-busy={isLoading}
                  className="w-full h-12 rounded-lg font-semibold text-white flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-[#455DD3] hover:bg-[#3A4FB8] focus:ring-4 focus:ring-[#455DD3]/30 focus:outline-none shadow-lg shadow-[#455DD3]/20"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      {t("login.continue", getLocale())} <ArrowRight className="w-4 h-4" aria-hidden />
                    </>
                  )}
                </button>
              </motion.form>

              <div className="flex items-center justify-center gap-4 py-3">
                <div className="flex items-center gap-1.5 text-xs text-[#787774] bg-white px-3 py-1.5 rounded-full border border-[#E9E9E7]" aria-label="Secure connection">
                  <Lock className="w-3.5 h-3.5 text-[#16A34A]" aria-hidden />
                  <span className="font-medium">Secure</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-[#787774] bg-white px-3 py-1.5 rounded-full border border-[#E9E9E7]" aria-label="Encrypted data">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#16A34A]" aria-hidden />
                  <span className="font-medium">Encrypted</span>
                </div>
              </div>

              <div className="text-center pt-4 border-t border-[#E9E9E7]">
                <p className="text-xs text-[#787774]">
                  By continuing, you agree to our{' '}
                  <Link to="/terms" className="text-[#455DD3] hover:underline font-medium">Terms</Link>
                  {' '}and{' '}
                  <Link to="/privacy" className="text-[#455DD3] hover:underline font-medium">Privacy Policy</Link>
                </p>
                <p className="text-xs text-[#787774] mt-3">
                  Don't have an account?{' '}
                  <Link to="/login?signup=true" className="text-[#2D2A26] font-semibold hover:underline">Sign up</Link>
                </p>
              </div>

              <div className="lg:hidden flex items-center justify-center gap-6 text-sm text-[#787774] pt-4">
                <Link to="/terms" className="hover:text-[#2D2A26] transition-colors">Terms</Link>
                <Link to="/privacy" className="hover:text-[#2D2A26] transition-colors">Privacy</Link>
                <a href="mailto:support@jobhuntin.com" className="hover:text-[#2D2A26] transition-colors">Support</a>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </>
  );
}
