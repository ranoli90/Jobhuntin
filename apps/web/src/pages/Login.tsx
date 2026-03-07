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

    const interval: any = setInterval(function() {
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
      {/* Skip to main content for accessibility */}
      <a href="#login-form" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg focus:font-medium">
        Skip to login form
      </a>
      
    <div className="min-h-screen bg-gradient-to-br from-[#FEF9F3] via-white to-[#F0FDF4] flex">
      {/* Left Side - Brand/Info Panel */}
      <div className="hidden lg:flex lg:w-[45%] xl:w-1/2 bg-[#2D2A26] relative overflow-hidden">
        {/* Subtle warm gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#F59E0B]/10 via-transparent to-[#2DD4BF]/10" />
        
        {/* Calmer animated elements */}
        <div className="absolute inset-0 overflow-hidden">
          <motion.div
            className="absolute top-20 left-10 w-48 h-48 bg-[#F59E0B]/10 rounded-full blur-3xl"
            animate={{ opacity: [0.3, 0.5, 0.3] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute bottom-20 right-10 w-64 h-64 bg-[#2DD4BF]/10 rounded-full blur-3xl"
            animate={{ opacity: [0.2, 0.4, 0.2] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          />
        </div>

        <div className="relative z-10 flex flex-col justify-between p-16 w-full">
          <div>
            <Logo className="text-white h-8 w-auto" />
          </div>

          <div className="space-y-10 max-w-xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h2 className="font-sans text-3xl xl:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-brand-sunrise to-brand-lagoon leading-tight mb-4 tracking-tight">
                {t("login.sidebarTitleLine1", getLocale())}{" "}
                <span className="text-brand-mango">
                  {t("login.sidebarTitleLine2", getLocale())}
                </span>
              </h2>
              <motion.p 
                className="text-slate-300 text-base leading-relaxed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.2 }}
              >
                {t("login.sidebarSubtitle", getLocale())}
              </motion.p>
            </motion.div>

            <div className="space-y-4">
              {[
                { icon: Zap, text: t("login.feature1", getLocale()) },
                { icon: Briefcase, text: t("login.feature2", getLocale()) },
                { icon: Send, text: t("login.feature3", getLocale()) },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.1 }}
                  className="flex items-center gap-4"
                  whileHover={{ scale: 1.05 }}
                >
                  <motion.div 
                    className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center shrink-0"
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    transition={{ duration: 0.3 }}
                  >
                    <motion.div
                      className="w-6 h-6 rounded-full bg-gradient-to-br from-brand-sunrise to-brand-mango flex items-center justify-center"
                      animate={{ rotate: [0, 360] }}
                      transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                    >
                      <item.icon className="w-3 h-3 text-white" />
                    </motion.div>
                  </motion.div>
                  <motion.span 
                    className="text-slate-300 text-sm font-medium"
                    whileHover={{ color: "#FFC857" }}
                    transition={{ duration: 0.2 }}
                  >
                    {item.text}
                  </motion.span>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm text-slate-400">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Link to="/terms" className="hover:text-brand-mango focus:outline-none focus:text-brand-sunrise transition-colors font-medium">Terms</Link>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Link to="/privacy" className="hover:text-brand-mango focus:outline-none focus:text-brand-sunrise transition-colors font-medium">Privacy</Link>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <a href="mailto:support@jobhuntin.com" className="hover:text-brand-mango focus:outline-none focus:text-brand-sunrise transition-colors font-medium">Support</a>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-[55%] xl:w-1/2 flex flex-col items-center justify-center p-6 sm:p-8 lg:p-16 relative">
        {/* Floating background elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 left-10 w-20 h-20 bg-gradient-to-br from-brand-sunrise/20 to-brand-mango/10 rounded-full blur-xl animate-pulse" />
          <div className="absolute bottom-10 right-10 w-16 h-16 bg-gradient-to-tr from-brand-lagoon/20 to-brand-plum/10 rounded-full blur-xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>
        
        <div className="absolute top-6 right-6 flex items-center gap-2 z-10">
          <LanguageSelector />
          <ThemeToggle />
        </div>
        
        <div className="w-full max-w-sm lg:max-w-md">
          {/* Mobile Logo and Value Prop */}
          <motion.div 
            className="lg:hidden text-center mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Logo className="mx-auto mb-4 h-10 w-auto" />
            <motion.h1 
              className="font-sans text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-brand-plum via-brand-sunrise to-brand-lagoon tracking-tight"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Welcome to JobHuntin
            </motion.h1>
            <motion.p 
              className="text-sm text-gray-600 mt-2 mb-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              Sign in to continue
            </motion.p>
            {/* Mobile value prop */}
            <motion.div 
              className="bg-white/80 backdrop-blur-xl dark:bg-slate-800/50 rounded-2xl p-4 text-left space-y-3 border border-brand-lagoon/20"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
            >
              {[
                { icon: Zap, text: "Apply to 100+ jobs while you sleep" },
                { icon: Briefcase, text: "AI-tailored resumes for every role" },
                { icon: Send, text: "Track all applications in one place" },
              ].map((item, i) => (
                <motion.div 
                  key={i} 
                  className="flex items-center gap-3"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.8 + i * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                >
                  <motion.div 
                    className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-sunrise/10 to-brand-mango/10 dark:from-brand-sunrise/20 dark:to-brand-mango/20 flex items-center justify-center shrink-0 border border-brand-sunrise/30"
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    transition={{ duration: 0.3 }}
                  >
                    <item.icon className="w-5 h-5 text-brand-sunrise dark:text-brand-mango" />
                  </motion.div>
                  <motion.span 
                    className="text-xs text-gray-700 dark:text-gray-300 font-medium"
                    whileHover={{ color: "#FF9C6B" }}
                    transition={{ duration: 0.2 }}
                  >
                    {item.text}
                  </motion.span>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>

          <motion.div
            id="login-form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="hidden lg:block mb-8">
              <h1 className="font-sans text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2 tracking-tight">
                Sign in to your account
              </h1>
              <p className="text-slate-500 text-sm">
                Enter your email and we'll send you a magic link
              </p>
            </div>

            {/* Social Login - Prominent on both mobile and desktop */}
            {/* UX FIX: Disabled with visual indicator instead of deceptive "coming soon" toasts */}
            <div className="space-y-3">
              <SocialLoginGroup
                onGoogleClick={() => {
                  // SECURITY: Social login disabled to prevent user confusion/phishing
                  // Previously showed "coming soon" toast which trains users to ignore warnings
                }}
                onLinkedInClick={() => {
                  // SECURITY: Social login disabled to prevent user confusion/phishing
                }}
                disabled={isLoading}
                showComingSoon={true}
              />
            </div>

            <SocialLoginDivider />

            <motion.form 
              onSubmit={handleSubmit} 
              className="space-y-4"
              animate={formError ? "shake" : "idle"}
              variants={{
                shake: {
                  x: [0, -10, 10, -10, 10, 0],
                  transition: { duration: 0.4 }
                },
                idle: {}
              }}
            >
              <div className="relative">
                <label htmlFor="login-email" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  {t("login.email", getLocale())}
                </label>
                <div className={cn(
                  "relative rounded-xl transition-all duration-200",
                  "focus-within:ring-2 focus-within:ring-primary-500/30 focus-within:ring-offset-2",
                  focused && "ring-2 ring-primary-500/20"
                )}>
                  <Mail className={cn(
                    "absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 transition-colors z-10",
                    focused ? "text-primary-500" : "text-slate-400"
                  )} aria-hidden />
                  <input
                    type="email"
                    placeholder={t("login.emailPlaceholder", getLocale())}
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
                      // UX FIX: Check if mouse is over suggestions before hiding
                      // This prevents the race condition where clicks on suggestions
                      // don't fire because the dropdown disappears before click completes
                      if (!isMouseOverSuggestions) {
                        setFocused(false);
                        setShowSuggestions(false);
                      }
                    }}
                    className={cn(
                      "w-full pl-12 pr-4 py-3.5 rounded-xl bg-white border transition-all duration-200 relative z-20",
                      "text-slate-900 placeholder:text-slate-400",
                      "focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 focus:outline-none",
                      formError ? "border-red-300 bg-red-50/50" : "border-slate-200 hover:border-slate-300"
                    )}
                    required
                    aria-invalid={formError ? "true" : "false"}
                    aria-describedby={formError ? "login-email-error" : undefined}
                  />
                  {/* Email Suggestions Dropdown */}
                  {showSuggestions && getEmailSuggestions().length > 0 && (
                    <div 
                      className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-xl shadow-slate-200/50 z-30 overflow-hidden max-h-60 overflow-y-auto"
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
                          className="w-full px-4 py-2.5 text-left text-sm text-slate-700 hover:bg-primary-50 hover:text-primary-700 transition-colors flex items-center gap-3 focus:bg-primary-50 focus:outline-none"
                        >
                          <Mail className="w-4 h-4 text-slate-400 flex-shrink-0" />
                          <span className="truncate">{suggestion}</span>
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
                  className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg"
                >
                  <AlertCircle className="w-4 h-4" aria-hidden />
                  {formError}
                </motion.div>
              )}

              {/* Captcha Field - shown when triggered by rate limiting or bot detection */}
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

              <Button
                type="submit"
                disabled={isLoading || !emailIsValid}
                className="w-full h-12 rounded-xl font-semibold text-white bg-primary-600 hover:bg-primary-500 focus:ring-4 focus:ring-primary-300 focus:outline-none transition-all shadow-lg shadow-primary-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                    <Loader2 className="w-5 h-5" />
                  </motion.div>
                ) : (
                  <span className="flex items-center gap-2">
                    {t("login.continue", getLocale())} <ArrowRight className="w-4 h-4" aria-hidden />
                  </span>
                )}
              </Button>
            </motion.form>

            {/* Security Badges - Enhanced */}
            <div className="flex items-center justify-center gap-4 py-3">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-50 dark:bg-slate-800 px-2.5 py-1.5 rounded-full">
                <Lock className="w-3.5 h-3.5 text-emerald-500" />
                <span className="font-medium">Secure</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-50 dark:bg-slate-800 px-2.5 py-1.5 rounded-full">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span className="font-medium">Encrypted</span>
              </div>
              <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500 bg-slate-50 dark:bg-slate-800 px-2.5 py-1.5 rounded-full">
                <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <span className="font-medium">Verified</span>
              </div>
            </div>

            <div className="text-center">
              <p className="text-xs text-slate-500">
                By continuing, you agree to our{' '}
                <Link to="/terms" className="underline hover:text-slate-700 focus:outline-none focus:text-primary-600">Terms</Link>
                {' '}and{' '}
                <Link to="/privacy" className="underline hover:text-slate-700 focus:outline-none focus:text-primary-600">Privacy Policy</Link>
              </p>
              <p className="text-xs text-slate-500 mt-3">
                Don't have an account?{' '}
                <Link to="/login?signup=true" className="text-primary-600 font-semibold hover:text-primary-700 focus:outline-none focus:text-primary-700">Sign up</Link>
              </p>
            </div>

            {/* Mobile footer links */}
            <div className="lg:hidden flex items-center justify-center gap-6 text-sm text-slate-500 pt-4 border-t border-slate-200">
              <Link to="/terms" className="hover:text-slate-700 focus:outline-none focus:text-primary-600 transition-colors">Terms</Link>
              <Link to="/privacy" className="hover:text-slate-700 focus:outline-none focus:text-primary-600 transition-colors">Privacy</Link>
              <a href="mailto:support@jobhuntin.com" className="hover:text-slate-700 focus:outline-none focus:text-primary-600 transition-colors">Support</a>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
    </>
  );
}
