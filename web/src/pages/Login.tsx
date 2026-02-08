import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import { supabase } from '../lib/supabase';
import { pushToast } from '../lib/toast';
import { 
  ArrowRight, Mail, Lock, Sparkles, AlertCircle, 
  Chrome, Linkedin, Bot, CheckCircle, ArrowLeft 
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { session, loading: authLoading } = useAuth();
  const returnTo = searchParams.get("returnTo") || "/app/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isMagicLink, setIsMagicLink] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [socialProviderLoading, setSocialProviderLoading] = useState<"google" | "linkedin" | null>(null);

  useEffect(() => {
    if (!authLoading && session) {
      navigate(returnTo, { replace: true });
    }
  }, [authLoading, session, navigate, returnTo]);

  const emailIsValid = useMemo(() => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  }, [email]);

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
      setSocialProviderLoading(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailIsValid) return;
    
    setIsLoading(true);
    setFormError(null);

    try {
      if (isMagicLink) {
        if (!API_BASE) throw new Error("API configuration missing");
        
        const resp = await fetch(`${API_BASE}/auth/magic-link`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email.trim(),
            return_to: returnTo,
          }),
        });
        
        if (!resp.ok) {
          const err = await resp.text();
          throw new Error(err || "Magic link failed");
        }
        
        setMagicLinkSent(true);
        pushToast({ title: "Check your email! 📧", tone: "success" });
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });
        if (error) throw error;
        pushToast({ title: "Welcome back!", tone: "success" });
        navigate(returnTo, { replace: true });
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

  if (magicLinkSent) {
    return (
      <div className="min-h-screen bg-[#FAF9F6] flex items-center justify-center p-6 font-inter text-[#2D2D2D]">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-white rounded-3xl p-8 max-w-md w-full shadow-xl text-center border border-gray-100"
        >
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-3xl font-bold font-poppins mb-4">Check your email</h2>
          <p className="text-gray-600 mb-8">
            We sent a magic link to <strong className="text-[#2D2D2D]">{email}</strong>.<br/>
            Click it to start hunting.
          </p>
          <button 
            onClick={() => setMagicLinkSent(false)}
            className="text-[#FF6B35] font-bold hover:underline"
          >
            Try different email
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF9F6] flex flex-col items-center justify-center p-6 font-inter text-[#2D2D2D] relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-[#FF6B35]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-[#4A90E2]/10 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative z-10">
        <Link to="/" className="inline-flex items-center gap-2 text-gray-500 hover:text-[#FF6B35] mb-8 transition-colors font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>

        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-white rounded-3xl shadow-xl p-8 sm:p-10 border border-gray-100"
        >
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-[#FF6B35] p-2 rounded-xl rotate-3 shadow-sm">
              <Bot className="text-white w-6 h-6" />
            </div>
            <h1 className="font-poppins text-2xl font-bold text-[#2D2D2D]">
              {isMagicLink ? "Let's get hunting" : "Welcome back"}
            </h1>
          </div>

          <div className="space-y-4 mb-8">
            <button
              onClick={() => handleSocialLogin("google")}
              disabled={!!socialProviderLoading}
              className="w-full flex items-center justify-center gap-3 bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-3 rounded-xl transition-all"
            >
              {socialProviderLoading === "google" ? (
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Sparkles className="w-4 h-4" /></motion.div>
              ) : (
                <Chrome className="w-5 h-5 text-gray-900" />
              )}
              Continue with Google
            </button>
            <button
              onClick={() => handleSocialLogin("linkedin")}
              disabled={!!socialProviderLoading}
              className="w-full flex items-center justify-center gap-3 bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-3 rounded-xl transition-all"
            >
              {socialProviderLoading === "linkedin" ? (
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><Sparkles className="w-4 h-4" /></motion.div>
              ) : (
                <Linkedin className="w-5 h-5 text-[#0077b5]" />
              )}
              Continue with LinkedIn
            </button>
          </div>

          <div className="relative mb-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-100"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-gray-400">Or with email</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  placeholder="tech-wizard@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FF6B35]/20 focus:border-[#FF6B35] transition-all font-medium"
                />
              </div>
            </div>

            {!isMagicLink && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                className="relative"
              >
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FF6B35]/20 focus:border-[#FF6B35] transition-all font-medium"
                />
              </motion.div>
            )}

            {formError && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 text-red-500 text-sm font-medium bg-red-50 p-3 rounded-lg"
              >
                <AlertCircle className="w-4 h-4" />
                {formError}
              </motion.div>
            )}

            <button
              type="submit"
              disabled={isLoading || !emailIsValid}
              className="w-full bg-[#2D2D2D] hover:bg-[#FF6B35] text-white font-bold py-3 rounded-xl transition-all shadow-lg hover:shadow-orange-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                  <Sparkles className="w-5 h-5" />
                </motion.div>
              ) : (
                <>
                  {isMagicLink ? "Send Magic Link" : "Sign In"}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsMagicLink(!isMagicLink)}
              className="text-sm text-gray-500 hover:text-[#FF6B35] transition-colors"
            >
              {isMagicLink ? "Use password instead" : "Use magic link instead"}
            </button>
          </div>
        </motion.div>

        <p className="mt-8 text-center text-sm text-gray-400">
          By joining, you agree to our{' '}
          <Link to="/terms" className="underline hover:text-[#FF6B35]">Terms</Link>
          {' '}and{' '}
          <Link to="/privacy" className="underline hover:text-[#FF6B35]">Privacy Policy</Link>.
        </p>
      </div>
    </div>
  );
}
