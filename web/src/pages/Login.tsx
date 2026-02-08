import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import { supabase } from '../lib/supabase';
import { pushToast } from '../lib/toast';
import { magicLinkService } from '../services/magicLinkService';
import { 
  ArrowRight, Mail, Lock, Sparkles, AlertCircle, 
  Chrome, Linkedin, Bot, CheckCircle, ArrowLeft,
  ShieldCheck, MailCheck
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

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
      color: i % 3 === 0 ? 'rgba(255, 107, 53, 0.15)' : i % 3 === 1 ? 'rgba(74, 144, 226, 0.15)' : 'rgba(255, 255, 255, 0.05)',
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

  const handleSocialLogin = async (provider: "google" | "linkedin_oidc") => {
    setSocialProviderLoading(provider === "linkedin_oidc" ? "linkedin" : "google");
    setFormError(null);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: `${window.location.origin}/login?returnTo=${encodeURIComponent(safeReturnTo)}`,
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
    const result = await magicLinkService.sendMagicLink(targetEmail, destination);
    if (!result.success) {
      if (result.error?.includes("Too many")) {
        setRateLimitReset(Date.now() + 60_000);
      }
      throw new Error(result.error || "Magic link failed");
    }
    setRateLimitReset(null);
    return result.email;
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
        navigate(safeReturnTo, { replace: true });
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
          navigate(safeReturnTo, { replace: true });
        } else {
          setSuccessState({ type: "register", email: email.trim() });
          pushToast({ title: "Verify your email", description: "Confirm the link we sent to finish setup.", tone: "info" });
        }
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
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1 }}
        >
          <Bot className="w-12 h-12 text-primary-500" />
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
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 font-sans text-slate-900 relative overflow-hidden pt-24">
         {/* Background Decoration for Success State */}
         <div className="absolute inset-0 pointer-events-none opacity-30">
          <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-primary-400/10 rounded-full blur-3xl -translate-x-1/3 -translate-y-1/3" />
          <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-3xl translate-x-1/3 translate-y-1/3" />
        </div>

        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-white/80 backdrop-blur-xl rounded-3xl p-8 max-w-md w-full shadow-2xl shadow-primary-500/5 text-center border border-white/50 relative z-10"
        >
          <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm border border-green-100">
            {isMagic ? <MailCheck className="w-10 h-10 text-green-600" /> : <ShieldCheck className="w-10 h-10 text-green-600" />}
          </div>
          <h2 className="text-3xl font-bold font-display mb-4 text-slate-900">
            {isMagic ? "Check your email" : "Confirm your email"}
          </h2>
          <p className="text-slate-500 mb-6 leading-relaxed">
            {isMagic
              ? (
                <>We sent a magic link to <strong className="text-slate-900">{successState.email}</strong>. Follow the steps below—if it doesn’t show up in 2 minutes, resend it.</>
              )
              : (
                <>You're almost set. Secure your account by confirming <strong className="text-slate-900">{successState.email}</strong>. Delivery can take up to 2 minutes.</>
              )}
          </p>
          <ol className="text-left list-decimal list-inside space-y-3 text-slate-600 mb-8 bg-slate-50/50 p-4 rounded-xl border border-slate-100/50">
            {steps.map((step, idx) => (
              <li key={idx} className="text-sm">{step}</li>
            ))}
          </ol>
          <div className="flex flex-col gap-3">
            {isMagic && (
              <Button
                variant="ghost"
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
                className="text-primary-600 hover:text-primary-700 hover:bg-primary-50"
              >
                {resendLoading ? "Resending..." : rateLimitCountdown ? `Retry in ${rateLimitCountdown}s` : "Resend magic link"}
              </Button>
            )}
            <Button 
              variant="outline"
              onClick={() => setSuccessState(null)}
            >
              Use a different email
            </Button>
            <a href="mailto:support@sorce.app" className="text-xs text-slate-400 hover:text-slate-600 mt-2">
              Need help? support@sorce.app
            </a>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center font-sans text-slate-900 relative overflow-hidden py-20 lg:py-32">
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

      <div className="w-full max-w-md relative z-10 px-6">
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass-panel rounded-[2.5rem] p-8 sm:p-10 shadow-2xl shadow-slate-200/50 border-white/60 bg-white/80 backdrop-blur-xl"
        >
          <div className="mb-8 text-center">
            <h1 className="font-display text-3xl font-black text-slate-900 mb-3 tracking-tight">
              {mode === "magic" ? "Let's get hunting" : mode === "password" ? "Welcome back" : "Create your vault"}
            </h1>
            <p className="text-slate-500 font-medium text-sm">{destinationHint}</p>
          </div>

          <div className="grid grid-cols-3 gap-2 mb-8 bg-slate-100 p-1.5 rounded-2xl" role="tablist">
            {AUTH_MODE_OPTIONS.map((option) => (
              <button
                type="button"
                key={option.key}
                onClick={() => setMode(option.key)}
                role="tab"
                className={cn(
                  "rounded-xl py-2.5 text-center transition-all text-xs font-bold uppercase tracking-wider",
                  mode === option.key
                    ? "bg-white text-primary-600 shadow-sm ring-1 ring-black/5"
                    : "text-slate-500 hover:text-slate-700 hover:bg-white/50"
                )}
              >
                {option.label.split(' ')[0]}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-4 mb-8">
            <Button
              variant="outline"
              type="button"
              onClick={() => handleSocialLogin("google")}
              disabled={!!socialProviderLoading}
              className="w-full justify-center gap-3 py-6 rounded-2xl font-bold text-slate-700 text-sm hover:bg-white hover:shadow-lg transition-all border-slate-200"
            >
              {socialProviderLoading === "google" ? (
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Sparkles className="w-4 h-4" /></motion.div>
              ) : (
                <Chrome className="w-5 h-5 text-slate-900" />
              )}
              Continue with Google
            </Button>
            <Button
              variant="outline"
              type="button"
              onClick={() => handleSocialLogin("linkedin_oidc")}
              disabled={!!socialProviderLoading}
              className="w-full justify-center gap-3 py-6 rounded-2xl font-bold text-slate-700 text-sm hover:bg-white hover:shadow-lg transition-all border-slate-200"
            >
              {socialProviderLoading === "linkedin" ? (
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Sparkles className="w-4 h-4" /></motion.div>
              ) : (
                <Linkedin className="w-5 h-5 text-[#0077b5]" />
              )}
              Continue with LinkedIn
            </Button>
          </div>

          <div className="relative mb-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-4 bg-white/80 text-slate-400 font-bold uppercase tracking-widest backdrop-blur-xl">Or with email</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              <Input
                  type="email"
                  placeholder="tech-wizard@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  icon={<Mail className="w-5 h-5" />}
                  required
                  className="py-4 bg-white/50 border-slate-200 focus:bg-white transition-all"
              />

              {mode !== "magic" && (
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  className="overflow-hidden"
                >
                  <Input
                    type="password"
                    placeholder={mode === "register" ? "Create a strong password" : "••••••••"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    icon={<Lock className="w-5 h-5" />}
                    className="py-4 bg-white/50 border-slate-200 focus:bg-white transition-all"
                  />
                </motion.div>
              )}

              {mode === "register" && (
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  className="overflow-hidden"
                >
                  <Input
                    type="password"
                    placeholder="Confirm password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    icon={<Lock className="w-5 h-5" />}
                    className="py-4 bg-white/50 border-slate-200 focus:bg-white transition-all"
                  />
                </motion.div>
              )}
            </div>

            {mode === "register" && (
              <div className="bg-slate-50/80 rounded-2xl p-4 lg:p-5 space-y-3 border border-slate-100">
                <p className="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-black">Security Checklist</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                  {passwordChecks.map((check) => (
                    <div key={check.label} className="flex items-center gap-2 text-[10px] lg:text-[11px] font-bold">
                      <CheckCircle className={cn("w-3 h-3", check.pass ? "text-green-500" : "text-slate-300")} />
                      <span className={cn(check.pass ? "text-slate-700" : "text-slate-400")}>{check.label}</span>
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
                className="flex items-center gap-2 text-red-600 text-xs font-bold bg-red-50 p-3 lg:p-4 rounded-xl lg:rounded-2xl border border-red-100"
                role="alert"
              >
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {formError}
              </motion.div>
            )}

            <Button
              type="submit"
              disabled={isLoading || !canSubmit || !!rateLimitCountdown}
              variant="primary"
              size="lg"
              className="w-full py-4 lg:py-6 rounded-xl lg:rounded-2xl shadow-xl shadow-primary-500/20 uppercase tracking-widest text-xs lg:text-sm font-black"
            >
              {isLoading ? (
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                  <Sparkles className="w-5 h-5" />
                </motion.div>
              ) : (
                <>
                  {mode === "magic" ? "Send Magic Link" : mode === "password" ? "Sign In" : "Create Account"}
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>

            {rateLimitCountdown && (
              <p className="text-xs text-center text-orange-600 font-bold uppercase tracking-wider">Cooldown active · {rateLimitCountdown}s</p>
            )}
          </form>

          <p className="mt-6 lg:mt-10 text-center text-xs text-slate-400 font-medium relative z-10 pb-4 lg:pb-0">
            By joining, you agree to our{' '}
            <Link to="/terms" className="underline hover:text-primary-500">Terms</Link>
            {' '}and{' '}
            <Link to="/privacy" className="underline hover:text-primary-500">Privacy Policy</Link>.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
