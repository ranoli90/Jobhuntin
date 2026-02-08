import * as React from "react";
import { useState, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { supabase } from "../lib/supabase";
import { pushToast } from "../lib/toast";
import { ArrowRight, Mail, Lock, Sparkles, ShieldAlert, Chrome, Linkedin } from "lucide-react";

const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { session, loading: authLoading } = useAuth();
  const returnTo = searchParams.get("returnTo") || "/app/dashboard";

  useEffect(() => {
    if (!authLoading && session) {
      navigate(returnTo, { replace: true });
    }
  }, [authLoading, session, navigate, returnTo]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isMagicLink, setIsMagicLink] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [socialProviderLoading, setSocialProviderLoading] = useState<"google" | "linkedin" | null>(null);

  const emailIsValid = useMemo(() => {
    const trimmed = email.trim();
    if (!trimmed) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed);
  }, [email]);

  const passwordStrength = useMemo(() => calculatePasswordStrength(password), [password]);

  const primaryDisabled = isMagicLink ? !emailIsValid || isLoading : !emailIsValid || !password || isLoading;

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
      pushToast({ title: "Redirecting to provider…", tone: "info" });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Social sign-in failed";
      setFormError(message);
      pushToast({ title: "Social sign-in failed", description: message, tone: "error" });
      setSocialProviderLoading(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailIsValid) {
      pushToast({ title: "Enter a valid email", tone: "error" });
      return;
    }
    setIsLoading(true);
    setFormError(null);
    try {
      if (isMagicLink) {
        if (!API_BASE) {
          throw new Error("API base URL is not configured");
        }
        const resp = await fetch(`${API_BASE}/auth/magic-link`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email.trim(),
            return_to: returnTo,
          }),
        });
        if (!resp.ok) {
          const description = await resp.text().catch(() => "");
          throw new Error(description || `Magic link request failed (${resp.status})`);
        }
        setMagicLinkSent(true);
        pushToast({ title: "Check your email for the sign-in link", tone: "success" });
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });
        if (error) throw error;
        pushToast({ title: "Welcome back!", tone: "success" });
        navigate(returnTo, { replace: true });
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Sign-in failed";
      setFormError(message);
      pushToast({ title: "Sign-in failed", description: message, tone: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailIsValid || !password) {
      pushToast({ title: "Enter a valid email and password", tone: "error" });
      return;
    }
    if (password.length < 6) {
      pushToast({ title: "Password must be at least 6 characters", tone: "error" });
      return;
    }
    setIsLoading(true);
    try {
      const { error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: { emailRedirectTo: `${window.location.origin}/app/onboarding` },
      });
      if (error) throw error;
      pushToast({
        title: "Account created!",
        description: "Check your email to confirm, or sign in with your password.",
        tone: "success",
      });
      setIsMagicLink(false);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Sign-up failed";
      pushToast({ title: "Sign-up failed", description: message, tone: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-brand-shell flex items-center justify-center">
        <LoadingSpinner label="Loading…" />
      </div>
    );
  }

  if (magicLinkSent) {
    return (
      <div className="min-h-screen bg-brand-shell flex items-center justify-center px-6">
        <Card tone="shell" shadow="lift" className="max-w-md w-full p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-lagoon/20">
            <Mail className="h-8 w-8 text-brand-lagoon" />
          </div>
          <h1 className="font-display text-2xl text-brand-ink">Check your email</h1>
          <p className="mt-2 text-brand-ink/70">
            We sent a sign-in link to <strong>{email}</strong>. Click it to get into your account.
          </p>
          <p className="mt-4 text-sm text-brand-ink/60">
            Didn’t get it? Check spam or{" "}
            <button
              type="button"
              className="text-brand-sunrise font-semibold underline"
              onClick={() => setMagicLinkSent(false)}
            >
              try again
            </button>
          </p>
          <Link to="/" className="mt-6 inline-block text-sm text-brand-ink/60 hover:text-brand-ink">
            ← Back to home
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-shell flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <Link to="/" className="inline-flex items-center gap-2 text-brand-ink/70 hover:text-brand-ink mb-8">
          <div className="h-9 w-9 rounded-xl bg-brand-sunrise text-white grid place-items-center text-sm font-bold">
            JH
          </div>
          <span className="font-display text-xl">JobHuntin</span>
        </Link>

        <Card tone="shell" shadow="lift" className="p-8">
          <div className="flex items-center gap-2 mb-6">
            <Sparkles className="h-5 w-5 text-brand-sunrise" />
            <h1 className="font-display text-2xl text-brand-ink">
              {isMagicLink ? "Sign in or create an account" : "Sign in"}
            </h1>
          </div>

          <div className="mb-6 space-y-3">
            <p className="text-sm text-center text-brand-ink/60">Or continue with</p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => handleSocialLogin("google")}
                disabled={!!socialProviderLoading}
              >
                {socialProviderLoading === "google" ? (
                  <LoadingSpinner />
                ) : (
                  <Chrome className="mr-2 h-4 w-4" />
                )}
                Google
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => handleSocialLogin("linkedin")}
                disabled={!!socialProviderLoading}
              >
                {socialProviderLoading === "linkedin" ? (
                  <LoadingSpinner />
                ) : (
                  <Linkedin className="mr-2 h-4 w-4" />
                )}
                LinkedIn
              </Button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-brand-ink mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-brand-ink/50" />
                <input
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`w-full rounded-2xl border bg-white pl-11 pr-4 py-3 text-brand-ink placeholder:text-brand-ink/40 focus:outline-none focus:ring-2 transition-colors ${
                    email && !emailIsValid
                      ? "border-red-300 focus:ring-red-200"
                      : "border-brand-ink/10 focus:ring-brand-sunrise/30"
                  }`}
                />
              </div>
              {email && !emailIsValid && (
                <p className="mt-1 text-sm text-red-500">Please enter a valid email address.</p>
              )}
            </div>

            {!isMagicLink && (
              <div className="transition-all">
                <label className="block text-sm font-medium text-brand-ink mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-brand-ink/50" />
                  <input
                    type="password"
                    autoComplete="current-password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-2xl border border-brand-ink/10 bg-white pl-11 pr-4 py-3 text-brand-ink placeholder:text-brand-ink/40 focus:outline-none focus:ring-2 focus:ring-brand-sunrise/30"
                  />
                </div>
                {password && <PasswordStrengthMeter strength={passwordStrength} />}
              </div>
            )}

            {formError && (
              <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">
                <ShieldAlert className="h-4 w-4" />
                <span>{formError}</span>
              </div>
            )}

            {isLoading ? (
              <div className="pt-2">
                <LoadingSpinner label={isMagicLink ? "Sending link…" : "Signing in…"} />
              </div>
            ) : (
              <div className="space-y-3 pt-2">
                <Button type="submit" className="w-full" size="lg" disabled={primaryDisabled}>
                  {isMagicLink ? "Send magic link" : "Sign in"}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                {!isMagicLink && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={handleSignUp}
                    disabled={!emailIsValid || !password || password.length < 6}
                  >
                    Create account
                  </Button>
                )}
              </div>
            )}
          </form>

          <div className="mt-6 pt-6 border-t border-brand-ink/10">
            <button
              type="button"
              className="text-sm text-brand-ink/70 hover:text-brand-ink"
              onClick={() => {
                setIsMagicLink(!isMagicLink);
                setPassword("");
              }}
            >
              {isMagicLink ? "Use password instead" : "Use magic link instead"}
            </button>
          </div>
        </Card>

        <p className="mt-6 text-center text-sm text-brand-ink/60">
          By continuing, you agree to our{" "}
          <Link to="/terms" className="text-brand-ink/80 hover:underline">Terms</Link>
          {" "}and{" "}
          <Link to="/privacy" className="text-brand-ink/80 hover:underline">Privacy Policy</Link>.
        </p>
      </div>
    </div>
  );
}

interface PasswordStrength {
  label: string;
  score: number;
  tone: "weak" | "ok" | "great";
}

function calculatePasswordStrength(value: string): PasswordStrength {
  if (!value) {
    return { label: "Start typing…", score: 0, tone: "weak" };
  }
  let score = 0;
  if (value.length >= 8) score += 1;
  if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score += 1;
  if (/\d/.test(value) && /[^A-Za-z0-9]/.test(value)) score += 1;
  if (value.length >= 12) score += 1;

  if (score >= 3) return { label: "Strong password", score, tone: "great" };
  if (score === 2) return { label: "Looks okay", score, tone: "ok" };
  return { label: "Too weak", score, tone: "weak" };
}

function PasswordStrengthMeter({ strength }: { strength: PasswordStrength }) {
  const pct = Math.min((strength.score / 4) * 100, 100);
  const toneClasses = {
    weak: "text-red-600 bg-red-100",
    ok: "text-amber-600 bg-amber-100",
    great: "text-emerald-600 bg-emerald-100",
  } as const;

  return (
    <div className="mt-2 space-y-1">
      <div className="h-2 w-full rounded-full bg-brand-ink/10">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            strength.tone === "great"
              ? "bg-emerald-500"
              : strength.tone === "ok"
              ? "bg-amber-500"
              : "bg-red-500"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${toneClasses[strength.tone]}`}>
        {strength.label}
      </span>
    </div>
  );
}
