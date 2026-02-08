import * as React from "react";
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { supabase } from "../lib/supabase";
import { pushToast } from "../lib/toast";
import { ArrowRight, Mail, Lock, Sparkles } from "lucide-react";

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      pushToast({ title: "Enter your email", tone: "error" });
      return;
    }
    setIsLoading(true);
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
      pushToast({ title: "Sign-in failed", description: message, tone: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      pushToast({ title: "Enter email and password", tone: "error" });
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
            Sk
          </div>
          <span className="font-display text-xl">Skedaddle</span>
        </Link>

        <Card tone="shell" shadow="lift" className="p-8">
          <div className="flex items-center gap-2 mb-6">
            <Sparkles className="h-5 w-5 text-brand-sunrise" />
            <h1 className="font-display text-2xl text-brand-ink">
              {isMagicLink ? "Sign in or create an account" : "Sign in"}
            </h1>
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
                  className="w-full rounded-2xl border border-brand-ink/10 bg-white pl-11 pr-4 py-3 text-brand-ink placeholder:text-brand-ink/40 focus:outline-none focus:ring-2 focus:ring-brand-sunrise/30"
                />
              </div>
            </div>

            {!isMagicLink && (
              <div>
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
              </div>
            )}

            {isLoading ? (
              <div className="pt-2">
                <LoadingSpinner label={isMagicLink ? "Sending link…" : "Signing in…"} />
              </div>
            ) : (
              <div className="space-y-3 pt-2">
                <Button type="submit" className="w-full" size="lg" disabled={isMagicLink ? !email.trim() : !email.trim() || !password}>
                  {isMagicLink ? "Send magic link" : "Sign in"}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                {!isMagicLink && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={handleSignUp}
                    disabled={!email.trim() || !password || password.length < 6}
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
          <a href="#" className="text-brand-ink/80 hover:underline">Terms</a>
          {" "}and{" "}
          <a href="#" className="text-brand-ink/80 hover:underline">Privacy Policy</a>.
        </p>
      </div>
    </div>
  );
}
