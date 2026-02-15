import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import { pushToast } from '../lib/toast';
import {
  ArrowRight, Mail, Sparkles, AlertCircle,
  CheckCircle, ShieldCheck, MailCheck,
  Briefcase, Send, Zap
} from 'lucide-react';
import { Logo } from '../components/brand/Logo';
import { Button } from '../components/ui/Button';
import { cn } from '../lib/utils';
import { magicLinkService } from '../services/magicLinkService';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  const returnTo = searchParams.get("returnTo") || "/app/dashboard";

  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successState, setSuccessState] = useState<{ email: string } | null>(null);
  const [resendLoading, setResendLoading] = useState(false);
  const [rateLimitCountdown, setRateLimitCountdown] = useState<number | null>(null);
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!authLoading && user) {
      const decodedReturnTo = decodeURIComponent(returnTo);
      const finalDest = decodedReturnTo.includes('/login') ? '/app/dashboard' : decodedReturnTo;
      navigate(finalDest, { replace: true });
    }
  }, [authLoading, user, navigate, returnTo]);

  const emailIsValid = useMemo(() => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  }, [email]);

  const safeReturnTo = useMemo(() => {
    if (!returnTo.startsWith("/")) return "/app/dashboard";
    if (returnTo.startsWith("//")) return "/app/dashboard";
    return returnTo;
  }, [returnTo]);

  useEffect(() => {
    if (!rateLimitCountdown) return;
    const timer = setTimeout(() => setRateLimitCountdown(null), rateLimitCountdown * 1000);
    return () => clearTimeout(timer);
  }, [rateLimitCountdown]);

  const requestMagicLink = async (targetEmail: string, destination: string) => {
    const result = await magicLinkService.sendMagicLink(targetEmail, destination);
    if (!result.success) {
      if (result.retryAfter) setRateLimitCountdown(result.retryAfter);
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
      const normalized = await requestMagicLink(email, safeReturnTo);
      setSuccessState({ email: normalized });
      pushToast({ title: "Check your inbox", tone: "success" });
    } catch (err: any) {
      setFormError(err.message || "Failed to send magic link");
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}>
          <Sparkles className="w-8 h-8 text-blue-500" />
        </motion.div>
      </div>
    );
  }

  if (successState) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-5">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md"
        >
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-blue-500/25">
              <MailCheck className="w-8 h-8 text-white" />
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 mb-3 tracking-tight">
              Check your email
            </h1>
            <p className="text-slate-500 leading-relaxed">
              We sent a magic link to<br />
              <span className="font-semibold text-slate-900">{successState.email}</span>
            </p>
          </div>

          <div className="bg-slate-50 rounded-2xl p-6 mb-6">
            <ol className="space-y-4">
              {[
                "Open your inbox (check spam too)",
                "Find the email from JobHuntin",
                "Click the magic link to sign in"
              ].map((step, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.1 }}
                  className="flex items-start gap-3"
                >
                  <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
                    {i + 1}
                  </div>
                  <span className="text-slate-600 text-sm">{step}</span>
                </motion.li>
              ))}
            </ol>
          </div>

          <div className="space-y-3">
            <Button
              variant="ghost"
              onClick={async () => {
                try {
                  setResendLoading(true);
                  await requestMagicLink(successState.email, safeReturnTo);
                  pushToast({ title: "Link resent", tone: "success" });
                } catch (err: any) {
                  setFormError(err?.message);
                } finally {
                  setResendLoading(false);
                }
              }}
              disabled={resendLoading || !!rateLimitCountdown}
              className="w-full text-blue-600 hover:bg-blue-50"
            >
              {resendLoading ? "Sending..." : rateLimitCountdown ? `Wait ${rateLimitCountdown}s` : "Resend link"}
            </Button>
            <Button variant="outline" onClick={() => setSuccessState(null)} className="w-full">
              Use different email
            </Button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex">
      {/* Left Side - Desktop Only */}
      <div className="hidden lg:flex lg:w-1/2 bg-slate-900 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-gradient-to-br from-blue-500/20 to-violet-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-gradient-to-tr from-pink-500/10 to-amber-500/10 rounded-full blur-3xl" />
        </div>
        
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <div>
            <div className="flex items-center gap-2 text-white/60 mb-2">
              <Logo className="text-white" />
            </div>
          </div>

          <div className="space-y-8">
            <div>
              <h2 className="font-display text-4xl xl:text-5xl font-bold text-white leading-tight mb-4 tracking-tight">
                Your AI agent<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-violet-400">
                  is ready to hunt
                </span>
              </h2>
              <p className="text-slate-400 text-lg leading-relaxed max-w-md">
                Sign in to access your dashboard, track applications, and land more interviews.
              </p>
            </div>

            <div className="space-y-4">
              {[
                { icon: Zap, text: "100+ tailored applications daily" },
                { icon: Briefcase, text: "Matches from 50+ job boards" },
                { icon: Send, text: "One-click apply everywhere" },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.1 }}
                  className="flex items-center gap-4"
                >
                  <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                    <item.icon className="w-5 h-5 text-blue-400" />
                  </div>
                  <span className="text-slate-300">{item.text}</span>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm text-slate-500">
            <Link to="/terms" className="hover:text-white transition-colors">Terms</Link>
            <Link to="/privacy" className="hover:text-white transition-colors">Privacy</Link>
            <a href="mailto:support@jobhuntin.com" className="hover:text-white transition-colors">Support</a>
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-8 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-10">
            <Logo className="mx-auto mb-4" />
            <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight">
              Welcome back
            </h1>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div className="hidden lg:block">
              <h1 className="font-display text-3xl font-bold text-slate-900 mb-2 tracking-tight">
                Sign in to JobHuntin
              </h1>
              <p className="text-slate-500">
                We'll send you a magic link for passwordless sign in.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="relative">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Email address
                </label>
                <div className={cn(
                  "relative rounded-xl transition-all duration-200",
                  focused && "ring-2 ring-blue-500/20"
                )}>
                  <Mail className={cn(
                    "absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 transition-colors",
                    focused ? "text-blue-500" : "text-slate-400"
                  )} />
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (formError) setFormError(null);
                    }}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                    className={cn(
                      "w-full pl-12 pr-4 py-4 rounded-xl bg-slate-50 border transition-all",
                      "text-slate-900 placeholder:text-slate-400",
                      "focus:outline-none",
                      formError ? "border-red-300 bg-red-50/50" : "border-slate-200 focus:border-blue-400"
                    )}
                    required
                  />
                </div>
              </div>

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
                type="submit"
                disabled={isLoading || !emailIsValid}
                className="w-full h-12 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                    <Sparkles className="w-5 h-5" />
                  </motion.div>
                ) : (
                  <span className="flex items-center gap-2">
                    Continue <ArrowRight className="w-4 h-4" />
                  </span>
                )}
              </Button>
            </form>

            <div className="space-y-4">
              <p className="text-center text-xs text-slate-400">
                By continuing, you agree to our{' '}
                <Link to="/terms" className="underline hover:text-slate-600">Terms</Link>
                {' '}and{' '}
                <Link to="/privacy" className="underline hover:text-slate-600">Privacy Policy</Link>
              </p>

              <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span>Secure • Encrypted • No passwords stored</span>
              </div>
            </div>

            {/* Mobile footer links */}
            <div className="lg:hidden flex items-center justify-center gap-6 text-sm text-slate-400 pt-4 border-t border-slate-100">
              <Link to="/terms" className="hover:text-slate-600">Terms</Link>
              <Link to="/privacy" className="hover:text-slate-600">Privacy</Link>
              <a href="mailto:support@jobhuntin.com" className="hover:text-slate-600">Support</a>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
