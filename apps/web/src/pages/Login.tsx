import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { useAuth } from '../hooks/useAuth';
import { pushToast } from '../lib/toast';
import {
  ArrowRight, Mail, AlertCircle,
  CheckCircle, ShieldCheck, MailCheck,
  Briefcase, Send, Zap, Loader2,
  Lock
} from 'lucide-react';
import { Logo } from '../components/brand/Logo';
import { ThemeToggle } from '../components/ThemeToggle';
import { LanguageSelector } from '../components/LanguageSelector';
import { Button } from '../components/ui/Button';
import { cn } from '../lib/utils';
import { magicLinkService } from '../services/magicLinkService';
import { telemetry } from '../lib/telemetry';
import { t, formatT, getLocale } from '../lib/i18n';
import { SocialLoginGroup, SocialLoginDivider } from '../components/auth/SocialLogin';
import { CaptchaField } from '../components/ui/Captcha';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  const returnTo = searchParams.get("returnTo");

  const safeReturnTo = useMemo(() => {
    // First check URL parameter
    if (returnTo) {
      // Check if it's a relative path (starts with /) and NOT protocol-relative (starts with //)
      if (returnTo.startsWith("/") && !returnTo.startsWith("//")) {
        return returnTo;
      }
    }
    // Second: Check if we have a stored returnTo from magic link flow (when api_public_url is not set)
    const storedReturnTo = sessionStorage.getItem('magicLinkReturnTo');
    if (storedReturnTo) {
      sessionStorage.removeItem('magicLinkReturnTo'); // Clear after use
      if (storedReturnTo.startsWith("/") && !storedReturnTo.startsWith("//")) {
        return storedReturnTo;
      }
    }
    // Default fallback
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
  const [captchaToken, setCaptchaToken] = useState<string>("");
  const [showCaptcha, setShowCaptcha] = useState(false);
  // UX FIX: Track mouse position to prevent race condition with email suggestions dropdown
  const [isMouseOverSuggestions, setIsMouseOverSuggestions] = useState(false);

  // Email domain suggestions
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

  useEffect(() => {
    if (!authLoading && user) {
      // Security: safeReturnTo is already sanitized to be a relative path
      navigate(safeReturnTo, { replace: true });
    }
  }, [authLoading, user, navigate, safeReturnTo]);

  // Show session expired toast when redirected from 401
  useEffect(() => {
    if (sessionStorage.getItem('session_expired') === 'true') {
      sessionStorage.removeItem('session_expired');
      pushToast({ title: t("login.sessionExpired", getLocale()), description: t("login.signInAgain", getLocale()), tone: "info" });
    }
  }, []);

  const emailIsValid = useMemo(() => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
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
        throw new Error(result.error || "Please complete the captcha verification");
      }
      throw new Error(result.error || "Magic link failed");
    }
    return result.email;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailIsValid) return;

    setIsLoading(true);
    setFormError(null);

    try {
      const normalized = await requestMagicLink(email, safeReturnTo, captchaToken || undefined);
      setShowCaptcha(false);
      setCaptchaToken("");
      telemetry.track("login_magic_link_requested", { usedCaptcha: !!captchaToken });
      setSuccessState({ email: normalized || email.trim().toLowerCase() });
      pushToast({ title: "Check your inbox", tone: "success" });
    } catch (error) {
      const err = error as Error;
      let msg = "Something went wrong. Please try again.";

      // Specific error handling for better user experience
      if (err.message) {
        if (err.message.includes('rate limit') || err.message.includes('too many requests')) {
          msg = "Too many requests. Please wait a few minutes before trying again.";
        } else if (err.message.includes('captcha')) {
          msg = "Please complete the captcha verification and try again.";
        } else if (err.message.includes('invalid email')) {
          msg = "Please enter a valid email address.";
        } else if (err.message.includes('network') || err.message.includes('connection')) {
          msg = "Network error. Please check your connection and try again.";
        } else if (typeof err.message === 'string' && !err.message.includes('[object')) {
          msg = err.message;
        }
      }

      setFormError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Confetti celebration on success
  const triggerConfetti = useCallback(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;

    const interval: any = setInterval(function () {
      const timeLeft = animationEnd - Date.now();
      if (timeLeft <= 0) return clearInterval(interval);
      const particleCount = 50 * (timeLeft / duration);
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
    }, 250);
  }, []);

  useEffect(() => {
    if (successState) {
      triggerConfetti();
    }
  }, [successState, triggerConfetti]);

  if (successState) {
    return (
      <div className="min-h-screen bg-white dark:bg-slate-950 flex items-center justify-center p-5">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md"
        >
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gray-900 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-gray-900/15">
              <MailCheck className="w-8 h-8 text-white" />
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 mb-3 tracking-tight">
              {t("login.checkInbox", getLocale())}
            </h1>
            <p className="text-slate-500 leading-relaxed">
              {t("login.sentTo", getLocale())}<br />
              <span className="font-semibold text-slate-900 dark:text-slate-100">{successState.email}</span>
            </p>
            <button
              onClick={() => {
                navigator.clipboard.writeText(successState.email);
                pushToast({ title: "Email copied", tone: "success" });
              }}
              className="mt-2 text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center justify-center gap-1 mx-auto transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy email
            </button>
            <p className="text-xs text-slate-500 mt-3">
              {t("login.checkSpam", getLocale())}
            </p>
          </div>

          <div className="bg-slate-50 dark:bg-slate-900/50 rounded-2xl p-6 mb-6">
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
                  <div className="w-6 h-6 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                    {i + 1}
                  </div>
                  <span className="text-slate-600 dark:text-slate-300 text-sm">{step}</span>
                </motion.li>
              ))}
            </ol>
          </div>

          <div className="space-y-3">
            {formError && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg"
              >
                <AlertCircle className="w-4 h-4" />
                {formError}
              </motion.div>
            )}
            <Button
              variant="ghost"
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
              className="w-full text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-primary-300 focus:outline-none"
            >
              {resendLoading ? t("login.sending", getLocale()) : rateLimitCountdown ? formatT("login.resendIn", { seconds: String(rateLimitCountdown) }, getLocale()) : t("login.resendLink", getLocale())}
            </Button>
            <Button variant="outline" onClick={() => setSuccessState(null)} className="w-full focus:ring-2 focus:ring-primary-300 focus:outline-none">
              {t("login.useDifferentEmail", getLocale())}
            </Button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <>
      <a href="#login-form" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-black focus:text-white focus:rounded-lg focus:font-medium">
        Skip to login form
      </a>

      <div className="min-h-screen bg-white dark:bg-slate-950 flex flex-col">
        {/* Simple top nav with logo */}
        <header className="w-full p-6 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 outline-none">
            <Logo className="h-6 w-auto text-black dark:text-white" />
          </Link>
          <div className="flex items-center gap-4">
            <LanguageSelector />
            <ThemeToggle />
          </div>
        </header>

        {/* Centered Form Container */}
        <main className="flex-1 flex flex-col items-center justify-center p-6 sm:p-8">
          <motion.div
            id="login-form"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-[360px] space-y-6"
          >
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-black dark:text-white mb-2 tracking-tight">
                Log in
              </h1>
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
              animate={formError ? "shake" : "idle"}
              variants={{
                shake: { x: [0, -10, 10, -10, 10, 0], transition: { duration: 0.4 } },
                idle: {}
              }}
            >
              <div className="relative">
                <label htmlFor="login-email" className="block text-sm font-semibold text-black dark:text-white mb-2">
                  Email
                </label>
                <div className={cn(
                  "relative transition-all duration-200",
                  "focus-within:ring-2 focus-within:ring-gray-200 dark:focus-within:ring-gray-800",
                  focused && "ring-2 ring-gray-200 dark:ring-gray-800"
                )}>
                  <input
                    type="email"
                    placeholder="Enter your email address..."
                    id="login-email"
                    autoComplete="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setShowSuggestions(e.target.value.includes('@'));
                      if (formError) setFormError(null);
                    }}
                    onFocus={() => {
                      setFocused(true);
                      setShowSuggestions(email.includes('@'));
                    }}
                    onBlur={() => {
                      if (!isMouseOverSuggestions) {
                        setFocused(false);
                        setShowSuggestions(false);
                      }
                    }}
                    className={cn(
                      "w-full px-3 py-2 rounded-md bg-white dark:bg-slate-900 border transition-all duration-200 relative z-20",
                      "text-black dark:text-white placeholder:text-gray-400 font-medium text-sm",
                      "focus:outline-none",
                      formError ? "border-red-300 bg-red-50" : "border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700"
                    )}
                    required
                    aria-invalid={formError ? "true" : "false"}
                  />
                  {showSuggestions && getEmailSuggestions().length > 0 && (
                    <div
                      className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-900 border border-gray-200 dark:border-gray-800 rounded-md shadow-sm z-30 overflow-hidden max-h-60 overflow-y-auto"
                      onMouseEnter={() => setIsMouseOverSuggestions(true)}
                      onMouseLeave={() => setIsMouseOverSuggestions(false)}
                    >
                      {getEmailSuggestions().slice(0, 5).map((suggestion, index) => (
                        <button
                          key={index}
                          type="button"
                          onClick={() => {
                            setEmail(suggestion);
                            setShowSuggestions(false);
                            setFocused(false);
                          }}
                          className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {formError && (
                <div className="text-red-600 text-sm font-medium">
                  {formError}
                </div>
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
                      onValidate={(isValid) => {
                        if (isValid) setFormError(null);
                      }}
                      className="mb-4"
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              <button
                type="submit"
                disabled={isLoading || !emailIsValid}
                className="w-full h-10 rounded-md font-semibold text-sm text-white bg-black hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-black dark:border-white flex items-center justify-center"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Continue with email"
                )}
              </button>
            </motion.form>

            <div className="text-center pt-8 border-t border-gray-100 dark:border-gray-800">
              <p className="text-xs text-gray-500 font-medium">
                Don't have an account?{' '}
                <Link to="/login?signup=true" className="text-black dark:text-white font-bold hover:underline">Sign up</Link>
              </p>
            </div>

            <div className="flex items-center justify-center gap-6 text-xs text-gray-400 font-medium pt-8">
              <Link to="/terms" className="hover:text-black dark:hover:text-white transition-colors">Terms</Link>
              <Link to="/privacy" className="hover:text-black dark:hover:text-white transition-colors">Privacy</Link>
            </div>
          </motion.div>
        </main>
      </div>
    </>
  );
}
