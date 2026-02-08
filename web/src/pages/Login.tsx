import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import { supabase } from '../lib/supabase';
import { pushToast } from '../lib/toast';
import { 
  ArrowRight, Mail, Lock, Sparkles, AlertCircle, 
  Chrome, Linkedin, Bot, CheckCircle, ArrowLeft,
  ShieldCheck, MailCheck 
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE = ((import.meta.env.VITE_API_URL ?? "") || `${window.location.origin}/api`).replace(/\/$/, "");
type AuthMode = "magic" | "password" | "register";

const AUTH_MODE_OPTIONS: { key: AuthMode; label: string; description: string }[] = [
  { key: "magic", label: "Magic Link", description: "No password" },
  { key: "password", label: "Password Login", description: "Existing users" },
  { key: "register", label: "Create Account", description: "New hunters" },
];

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { session, loading: authLoading } = useAuth();
  const returnTo = searchParams.get("returnTo") || "/app/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [mode, setMode] = useState<AuthMode>("magic");
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [socialProviderLoading, setSocialProviderLoading] = useState<"google" | "linkedin" | null>(null);
  const [successState, setSuccessState] = useState<{ type: "magic" | "register"; email: string } | null>(null);
  const [resendLoading, setResendLoading] = useState(false);
  const [rateLimitReset, setRateLimitReset] = useState<number | null>(null);
  const [rateLimitCountdown, setRateLimitCountdown] = useState<number | null>(null);

  // Background Particles Data - Shared artistic style
  const particles = React.useMemo(() => {
    return [...Array(20)].map((_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: i < 3 ? Math.random() * 200 + 150 : Math.random() * 60 + 20,
      duration: Math.random() * 30 + 30,
      delay: Math.random() * 10,
      yMove: (Math.random() - 0.5) * 100,
      xMove: (Math.random() - 0.5) * 100,
      color: i % 3 === 0 ? 'rgba(255, 107, 53, 0.2)' : i % 3 === 1 ? 'rgba(74, 144, 226, 0.2)' : 'rgba(255, 255, 255, 0.1)',
      blur: i < 3 ? 'blur(80px)' : 'none'
    }));
  }, []);

  useEffect(() => {
    if (!authLoading && session) {
      navigate(returnTo, { replace: true });
    }
  }, [authLoading, session, navigate, returnTo]);

  const emailIsValid = useMemo(() => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  }, [email]);

  const passwordChecks = useMemo(
    () => [
      { label: "10+ characters", pass: password.length >= 10 },
      { label: "Contains a letter", pass: /[A-Za-z]/.test(password) },
      { label: "Contains a number", pass: /\d/.test(password) },
      { label: "Contains a symbol", pass: /[^A-Za-z0-9]/.test(password) },
    ],
    [password]
  );

  const passwordIsStrong = useMemo(() => passwordChecks.every((check) => check.pass), [passwordChecks]);
  const passwordsMatch = mode !== "register" || password === confirmPassword;
  const canSubmit = emailIsValid && (
    mode === "magic" ||
    (mode === "password" && password.length > 0) ||
    (mode === "register" && passwordIsStrong && passwordsMatch)
  );

  useEffect(() => {
    setFormError(null);
    if (mode === "magic") {
      setPassword("");
      setConfirmPassword("");
    }
  }, [mode]);

  const safeReturnTo = useMemo(() => {
    if (!returnTo.startsWith("/")) return "/app/dashboard";
    if (returnTo.startsWith("//")) return "/app/dashboard";
    return returnTo;
  }, [returnTo]);

  const destinationHint = useMemo(() => {
    if (safeReturnTo === "/app/onboarding") return "We'll drop you into onboarding as soon as you're verified.";
    if (safeReturnTo === "/app/dashboard") return "You'll land on your dashboard after signing in.";
    return `We'll take you to ${safeReturnTo} once you're in.`;
  }, [safeReturnTo]);

  useEffect(() => {
    if (!rateLimitReset) {
      setRateLimitCountdown(null);
      return;
    }
    const tick = () => {
      const remaining = Math.max(0, Math.ceil((rateLimitReset - Date.now()) / 1000));
      setRateLimitCountdown(remaining);
      if (remaining <= 0) {
        setRateLimitReset(null);
      }
    };
    tick();
    const interval = window.setInterval(tick, 1000);
    return () => window.clearInterval(interval);
  }, [rateLimitReset]);

  const handleSocialLogin = async (provider: "google" | "linkedin") => {
    setSocialProviderLoading(provider);
    setFormError(null);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: `${window.location.origin}/login?returnTo=${encodeURIComponent(returnTo)}`,
        },
      });
      if (error) throw error;
      pushToast({ title: "Redirecting...", tone: "info" });
    } catch (err: any) {
      setFormError(err.message || "Social sign-in failed");
    } finally {
      setSocialProviderLoading(null);
    }
  };

  const sendMagicLink = async (targetEmail: string, destination: string) => {
    const normalizedEmail = targetEmail.trim().toLowerCase();
    try {
      const resp = await fetch(`${API_BASE}/auth/magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: normalizedEmail,
          return_to: destination,
        }),
      });

      if (!resp.ok) {
        let message = "Magic link failed";
        try {
          const data = await resp.json();
          message = data?.detail || data?.error || message;
        } catch {
          const errText = await resp.text();
          message = errText || message;
        }
        if (resp.status === 429) {
          setRateLimitReset(Date.now() + 60_000);
          message = "Too many magic link requests. Please wait before trying again.";
        }
        throw new Error(message);
      }

      setRateLimitReset(null);
      return normalizedEmail;
    } catch (err: any) {
      if (!API_BASE) {
        throw new Error("Magic links are warming up. Please try again soon.");
      }
      throw err;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailIsValid) return;
    
    setIsLoading(true);
    setFormError(null);
    setSuccessState(null);

    try {
      if (mode === "magic") {
        const normalized = await sendMagicLink(email, safeReturnTo);
        setSuccessState({ type: "magic", email: normalized });
        pushToast({ title: "Check your email! 📧", tone: "success" });
      } else if (mode === "password") {
        if (!password.length) {
          throw new Error("Password is required");
        }
        const { error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });
        if (error) throw error;
        pushToast({ title: "Welcome back!", tone: "success" });
        navigate(returnTo, { replace: true });
      } else {
        if (!passwordIsStrong) {
          throw new Error("Password must meet all strength requirements.");
        }
        if (!passwordsMatch) {
          throw new Error("Passwords do not match");
        }
        const { data, error } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/login?returnTo=${encodeURIComponent(safeReturnTo)}`,
            data: {
              onboarding_intent: safeReturnTo,
            },
          },
        });
        if (error) throw error;
        if (data.session) {
          pushToast({ title: "Account created", tone: "success" });
          navigate(returnTo, { replace: true });
        } else {
          setSuccessState({ type: "register", email: email.trim() });
          setMode("password");
          pushToast({ title: "Verify your email", description: "Confirm the link we sent to finish setup.", tone: "info" });
        }
        setEmail("");
        setPassword("");
        setConfirmPassword("");
      }
    } catch (err: any) {
      setFormError(err.message || "Sign-in failed");
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#FAF9F6] flex items-center justify-center">
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1 }}
        >
          <Bot className="w-12 h-12 text-[#FF6B35]" />
        </motion.div>
      </div>
    );
  }

  if (successState) {
    const isMagic = successState.type === "magic";
    const steps = isMagic
      ? [
          "Open the inbox (or spam) for " + successState.email,
          "Look for the email titled 'Start your JobHuntin run' from noreply@sorce.app",
          "Tap the magic link and keep this tab open—onboarding launches instantly",
        ]
      : [
          "Check " + successState.email + " for 'Verify your JobHuntin account'",
          "Click the confirm button to lock in your password",
          "Return to this tab and sign in securely",
        ];
    return (
      <div className="min-h-screen bg-[#FAF9F6] flex items-center justify-center p-6 font-inter text-[#2D2D2D]">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-white rounded-3xl p-8 max-w-md w-full shadow-xl text-center border border-gray-100"
        >
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            {isMagic ? <MailCheck className="w-10 h-10 text-green-600" /> : <ShieldCheck className="w-10 h-10 text-green-600" />}
          </div>
          <h2 className="text-3xl font-bold font-poppins mb-4">
            {isMagic ? "Check your email" : "Confirm your email"}
          </h2>
          <p className="text-gray-600 mb-6">
            {isMagic
              ? (
                <>We sent a magic link to <strong className="text-[#2D2D2D]">{successState.email}</strong>. Follow the steps below—if it doesn’t show up in 2 minutes, resend it.</>
              )
              : (
                <>You're almost set. Secure your account by confirming <strong className="text-[#2D2D2D]">{successState.email}</strong>. Delivery can take up to 2 minutes.</>
              )}
          </p>
          <ol className="text-left list-decimal list-inside space-y-2 text-gray-600 mb-6">
            {steps.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
          <div className="flex flex-col gap-3">
            {isMagic && (
              <button
                onClick={async () => {
                  try {
                    setResendLoading(true);
                    await sendMagicLink(successState.email, safeReturnTo);
                    pushToast({ title: "Magic link resent", tone: "success" });
                  } catch (err: any) {
                    setFormError(err?.message || "Unable to resend");
                  } finally {
                    setResendLoading(false);
                  }
                }}
                disabled={resendLoading || !!rateLimitCountdown}
                className="text-sm font-semibold text-[#FF6B35] disabled:text-gray-300 hover:underline"
              >
                {resendLoading ? "Resending..." : rateLimitCountdown ? `Retry in ${rateLimitCountdown}s` : "Resend magic link"}
              </button>
            )}
            <button 
              onClick={() => setSuccessState(null)}
              className="text-sm font-semibold text-[#FF6B35] hover:underline"
            >
              Use a different email
            </button>
            <a href="mailto:support@sorce.app" className="text-sm text-gray-500 hover:text-[#2D2D2D]">
              Need help? support@sorce.app
            </a>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF9F6] flex flex-col lg:flex-row font-inter text-[#2D2D2D] relative overflow-hidden lg:items-stretch">
      {/* Left Artistic Panel - Hidden on Mobile */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-[#1a1a1a] items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-grid-premium-dark opacity-20 pointer-events-none" />
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-[#FF6B35]/15 rounded-full blur-3xl -translate-x-1/3 -translate-y-1/3" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-[#4A90E2]/20 rounded-full blur-3xl translate-x-1/3 translate-y-1/3" />
        {/* Generative Background Blobs */}
        <div className="absolute inset-0 pointer-events-none">
          {particles.map((particle) => (
            <motion.div
              key={particle.id}
              className="absolute rounded-full"
              animate={{ 
                y: [0, particle.yMove, 0],
                x: [0, particle.xMove, 0],
                scale: [1, 1.1, 1],
                opacity: [0.3, 0.5, 0.3]
              }}
              transition={{ 
                duration: particle.duration, 
                repeat: Infinity, 
                ease: "easeInOut",
                delay: particle.delay
              }}
              style={{
                left: `${particle.left}%`,
                top: `${particle.top}%`,
                width: particle.size,
                height: particle.size,
                background: particle.color,
                filter: particle.blur,
                willChange: "transform"
              }}
            />
          ))}
        </div>

        <div className="relative z-10 text-center px-12">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="mb-8"
          >
            <div className="bg-[#FF6B35] w-20 h-20 rounded-3xl rotate-6 shadow-2xl flex items-center justify-center mx-auto mb-6">
              <Bot className="text-white w-10 h-10" />
            </div>
            <h2 className="text-5xl font-black font-poppins text-white leading-tight mb-4 tracking-tighter">
              Join the Elite <br />
              <span className="text-[#FF6B35]">Job Hunters</span>
            </h2>
            <p className="text-gray-400 text-xl max-w-md mx-auto leading-relaxed">
              Experience the first-of-its-kind AI agent that transforms your career while you sleep.
            </p>
          </motion.div>
        </div>

        {/* Floating Stat Pills */}
        <motion.div 
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 4, repeat: Infinity }}
          className="absolute bottom-12 left-12 glass-panel-dark px-4 py-2 rounded-full text-xs text-white flex items-center gap-2 border-white/10"
        >
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          1,247 active hunts in Denver
        </motion.div>
      </div>

      {/* Right Form Panel */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 lg:p-12 relative z-10">
        <div className="w-full max-w-md">
          <Link to="/" className="inline-flex items-center gap-2 text-gray-500 hover:text-[#FF6B35] mb-12 transition-colors font-medium group">
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Home
          </Link>

          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="glass-panel rounded-[2.5rem] p-8 sm:p-12 shadow-2xl border-white/40"
          >
            <div className="mb-10">
              <h1 className="font-poppins text-3xl font-black text-[#2D2D2D] mb-2 tracking-tight">
                {mode === "magic" ? "Let's get hunting" : mode === "password" ? "Welcome back" : "Create your vault"}
              </h1>
              <p className="text-gray-500 font-medium">{destinationHint}</p>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-10 bg-gray-100/50 p-1.5 rounded-2xl" role="tablist">
              {AUTH_MODE_OPTIONS.map((option) => (
                <button
                  type="button"
                  key={option.key}
                  onClick={() => setMode(option.key)}
                  role="tab"
                  className={cn(
                    "rounded-xl py-2.5 text-center transition-all text-xs font-bold uppercase tracking-wider",
                    mode === option.key
                      ? "bg-white text-[#FF6B35] shadow-sm"
                      : "text-gray-500 hover:text-gray-700"
                  )}
                >
                  {option.label.split(' ')[0]}
                </button>
              ))}
            </div>

            <div className="space-y-4 mb-10">
              <button
                onClick={() => handleSocialLogin("google")}
                disabled={!!socialProviderLoading}
                className="w-full flex items-center justify-center gap-3 bg-white border border-gray-100 hover:border-gray-200 hover:bg-gray-50 text-gray-700 font-bold py-3.5 rounded-2xl transition-all shadow-sm group"
              >
                {socialProviderLoading === "google" ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Sparkles className="w-4 h-4" /></motion.div>
                ) : (
                  <Chrome className="w-5 h-5 text-gray-900 group-hover:scale-110 transition-transform" />
                )}
                Continue with Google
              </button>
              <button
                onClick={() => handleSocialLogin("linkedin")}
                disabled={!!socialProviderLoading}
                className="w-full flex items-center justify-center gap-3 bg-white border border-gray-100 hover:border-gray-200 hover:bg-gray-50 text-gray-700 font-bold py-3.5 rounded-2xl transition-all shadow-sm group"
              >
                {socialProviderLoading === "linkedin" ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Sparkles className="w-4 h-4" /></motion.div>
                ) : (
                  <Linkedin className="w-5 h-5 text-[#0077b5] group-hover:scale-110 transition-transform" />
                )}
                Continue with LinkedIn
              </button>
            </div>

            <div className="relative mb-10">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-100"></div>
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-4 bg-transparent text-gray-400 font-bold uppercase tracking-widest">Or with email</span>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4">
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    placeholder="tech-wizard@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-white/50 border border-gray-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-[#FF6B35]/10 focus:border-[#FF6B35] transition-all font-medium placeholder:text-gray-300"
                  />
                </div>

                {mode !== "magic" && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    className="relative"
                  >
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="password"
                      placeholder={mode === "register" ? "Create a strong password" : "••••••••"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-12 pr-4 py-4 bg-white/50 border border-gray-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-[#FF6B35]/10 focus:border-[#FF6B35] transition-all font-medium placeholder:text-gray-300"
                    />
                  </motion.div>
                )}

                {mode === "register" && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    className="relative"
                  >
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="password"
                      placeholder="Confirm password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full pl-12 pr-4 py-4 bg-white/50 border border-gray-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-[#FF6B35]/10 focus:border-[#FF6B35] transition-all font-medium placeholder:text-gray-300"
                    />
                  </motion.div>
                )}
              </div>

              {mode === "register" && (
                <div className="bg-gray-50/50 rounded-2xl p-5 space-y-3">
                  <p className="text-[10px] uppercase tracking-[0.2em] text-gray-400 font-black">Security Checklist</p>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                    {passwordChecks.map((check) => (
                      <div key={check.label} className="flex items-center gap-2 text-[11px] font-bold">
                        <CheckCircle className={cn("w-3 h-3", check.pass ? "text-green-500" : "text-gray-300")} />
                        <span className={cn(check.pass ? "text-gray-700" : "text-gray-400")}>{check.label}</span>
                      </div>
                    ))}
                  </div>
                  {!passwordsMatch && confirmPassword.length > 0 && (
                    <p className="text-[10px] text-red-500 font-bold uppercase tracking-wider">Passwords must match</p>
                  )}
                </div>
              )}

              {formError && (
                <motion.div 
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 text-red-500 text-xs font-bold bg-red-50 p-4 rounded-2xl border border-red-100"
                  role="alert"
                >
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {formError}
                </motion.div>
              )}

              <button
                type="submit"
                disabled={isLoading || !canSubmit || !!rateLimitCountdown}
                className="w-full bg-[#2D2D2D] hover:bg-[#FF6B35] text-white font-black py-4 rounded-2xl transition-all shadow-xl hover:shadow-orange-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 uppercase tracking-widest text-sm"
              >
                {isLoading ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                    <Sparkles className="w-5 h-5" />
                  </motion.div>
                ) : (
                  <>
                    {mode === "magic" ? "Send Magic Link" : mode === "password" ? "Sign In" : "Create Account"}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              {rateLimitCountdown && (
                <p className="text-xs text-center text-orange-600 font-bold uppercase tracking-wider">Cooldown active · {rateLimitCountdown}s</p>
              )}
            </form>
          </motion.div>

          <p className="mt-10 text-center text-xs text-gray-400 font-medium">
            By joining, you agree to our{' '}
            <Link to="/terms" className="underline hover:text-[#FF6B35]">Terms</Link>
            {' '}and{' '}
            <Link to="/privacy" className="underline hover:text-[#FF6B35]">Privacy Policy</Link>.
          </p>
        </div>
      </div>
    </div>
  );
}
