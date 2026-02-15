import React, { useState, useEffect, useRef } from 'react';
import { motion, useScroll, useSpring, useReducedMotion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { magicLinkService } from '../services/magicLinkService';
import {
  Sparkles, CheckCircle, ArrowRight,
  MailCheck, Bell,
  Upload, Search, Send, Lock, Shield, Clock,
  Briefcase, MapPin, User
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';

import { Button } from '../components/ui/Button';

// --- UTILS ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- DATA ---
const ACTIVITY_DATA = [
  { name: "Michael K.", role: "Senior Product Manager", company: "Stripe", location: "San Francisco", time: "just now" },
  { name: "Sarah L.", role: "Software Engineer", company: "Vercel", location: "Remote", time: "2m ago" },
  { name: "David R.", role: "Data Scientist", company: "Netflix", location: "Los Angeles", time: "3m ago" },
  { name: "Emily W.", role: "UX Designer", company: "Figma", location: "San Francisco", time: "5m ago" },
  { name: "James T.", role: "Engineering Manager", company: "Airbnb", location: "Remote", time: "7m ago" },
  { name: "Amanda C.", role: "Frontend Developer", company: "Linear", location: "Remote", time: "9m ago" },
  { name: "Chris M.", role: "DevOps Engineer", company: "Datadog", location: "New York", time: "11m ago" },
  { name: "Jessica H.", role: "Product Designer", company: "Notion", location: "San Francisco", time: "14m ago" },
];

const COMPANIES = ["Stripe", "Vercel", "Netflix", "Figma", "Airbnb", "Linear", "Datadog", "Notion", "OpenAI", "Anthropic"];
const ROLES = ["Senior PM", "Software Engineer", "Data Scientist", "UX Designer", "Engineering Manager", "Frontend Dev", "DevOps Engineer", "Product Designer"];
const LOCATIONS = ["San Francisco", "New York", "Remote", "Los Angeles", "Seattle", "Austin"];
const FIRST_NAMES = ["Michael", "Sarah", "David", "Emily", "James", "Amanda", "Chris", "Jessica", "Ryan", "Lisa", "Kevin", "Rachel"];
const LAST_INITIALS = ["K", "L", "R", "W", "T", "C", "M", "H", "P", "S", "J", "B"];

function generateActivity() {
  const firstName = FIRST_NAMES[Math.floor(Math.random() * FIRST_NAMES.length)];
  const lastInitial = LAST_INITIALS[Math.floor(Math.random() * LAST_INITIALS.length)];
  return {
    name: `${firstName} ${lastInitial}.`,
    role: ROLES[Math.floor(Math.random() * ROLES.length)],
    company: COMPANIES[Math.floor(Math.random() * COMPANIES.length)],
    location: LOCATIONS[Math.floor(Math.random() * LOCATIONS.length)],
    time: "just now"
  };
}

// --- COMPONENTS ---

const LiveActivityStream = () => {
  const [activities, setActivities] = useState(ACTIVITY_DATA);
  const [isPaused, setIsPaused] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    if (shouldReduceMotion || isPaused) return;
    
    const interval = setInterval(() => {
      const newActivity = generateActivity();
      setActivities(prev => {
        const updated = [newActivity, ...prev.slice(0, 7)];
        updated.forEach((a, i) => {
          if (i === 0) a.time = "just now";
          else if (i === 1) a.time = "1m ago";
          else if (i < 4) a.time = `${i + 1}m ago`;
          else a.time = `${(i + 1) * 2}m ago`;
        });
        return updated;
      });
    }, 4000);

    return () => clearInterval(interval);
  }, [shouldReduceMotion, isPaused]);

  return (
    <div 
      ref={containerRef}
      className="relative"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="absolute -left-4 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-500 via-violet-500 to-pink-500 rounded-full" />
      
      <div className="space-y-0">
        <AnimatePresence mode="popLayout">
          {activities.slice(0, 5).map((activity, i) => (
            <motion.div
              key={`${activity.name}-${activity.company}-${i}`}
              initial={{ opacity: 0, x: -20, height: 0 }}
              animate={{ opacity: i === 0 ? 1 : 0.7 - i * 0.12, x: 0, height: "auto" }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className={cn(
                "flex items-center gap-3 py-3",
                i === 0 && "bg-gradient-to-r from-blue-50/80 to-violet-50/80 -mx-3 px-3 rounded-lg"
              )}
            >
              <div className={cn(
                "w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0",
                i === 0 
                  ? "bg-gradient-to-br from-blue-500 to-violet-500 shadow-lg shadow-blue-500/20" 
                  : "bg-slate-100"
              )}>
                {i === 0 ? (
                  <Send className="w-4 h-4 text-white" />
                ) : (
                  <User className="w-4 h-4 text-slate-400" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className={cn(
                  "text-sm leading-tight",
                  i === 0 ? "text-slate-900 font-medium" : "text-slate-600"
                )}>
                  <span className="font-semibold">{activity.name}</span>
                  <span className="text-slate-400 mx-1.5">→</span>
                  <span className="text-blue-600">{activity.role}</span>
                  <span className="text-slate-400"> at </span>
                  <span className="text-slate-700">{activity.company}</span>
                </p>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-400">
                  <MapPin className="w-3 h-3" />
                  <span>{activity.location}</span>
                  <span className="text-slate-300">•</span>
                  <span>{activity.time}</span>
                </div>
              </div>
              
              {i === 0 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="flex items-center gap-1 px-2 py-1 bg-emerald-50 text-emerald-600 rounded-full text-xs font-medium"
                >
                  <CheckCircle className="w-3 h-3" />
                  Applied
                </motion.div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      
      <div className="mt-4 pt-3 border-t border-slate-200/60">
        <p className="text-xs text-slate-400 text-center">
          {isPaused ? "Paused" : "Live"} • Updated in real-time
        </p>
      </div>
    </div>
  );
};

const ProgressBar = () => {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  return (
    <div className="fixed top-0 left-0 right-0 h-1 bg-slate-100 z-[60]">
      <motion.div
        className="h-full bg-gradient-to-r from-primary-500 to-amber-500"
        style={{ scaleX, transformOrigin: "0%" }}
      />
    </div>
  );
};

const Hero = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);
  const shouldReduceMotion = useReducedMotion();

  const validateEmail = (e: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    if (!validateEmail(email)) {
      setEmailError("Enter a valid email");
      return;
    }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);

    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");
      if (!result.success) throw new Error(result.error || "Failed");
      
      if (typeof window !== 'undefined' && confetti && !shouldReduceMotion) {
        confetti({ particleCount: 80, spread: 60, origin: { y: 0.7 }, colors: ['#3b82f6', '#8b5cf6', '#ec4899'] });
      }
      
      pushToast({ title: "Check your inbox", description: "Magic link sent!", tone: "success" });
      setSentEmail(result.email);
      setEmail("");
      setIsSubmitting(false);
    } catch (err: any) {
      setIsSubmitting(false);
      setEmailError(err?.message || "Failed to send");
      pushToast({ title: "Error", description: err?.message || "Failed", tone: "error" });
    }
  };

  return (
    <section className="relative min-h-[100svh] lg:min-h-[90svh] flex items-center justify-center overflow-hidden bg-white">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-gradient-to-br from-blue-100/40 to-violet-100/40 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-gradient-to-tr from-pink-100/30 to-amber-100/30 rounded-full blur-3xl" />
      </div>

      <div className="absolute inset-0 bg-grid-premium opacity-20 pointer-events-none" />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-5 sm:px-8 lg:px-12 py-20 lg:py-0">
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-slate-50 border border-slate-200/80 mb-8"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs sm:text-sm font-medium text-slate-600 tracking-wide">
              <span className="font-bold text-slate-900">147</span> jobs applied today
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tighter-display leading-[0.95] mb-6 text-balance-hero max-w-3xl"
          >
            <span className="text-slate-900">Your AI applies to</span>
            <br />
            <span className="bg-gradient-to-r from-blue-600 via-violet-600 to-pink-600 bg-clip-text text-transparent animate-gradient-flow bg-[length:200%_auto]">
              100 jobs daily
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="font-body text-lg sm:text-xl lg:text-2xl text-slate-500 max-w-2xl mb-10 leading-relaxed"
          >
            Upload your resume. Our agent matches, tailors, and submits applications
            <span className="hidden sm:inline"> while you focus on interviews.</span>
            <span className="sm:hidden"> automatically.</span>
          </motion.p>

          {!sentEmail ? (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="w-full max-w-md"
            >
              <form onSubmit={onSubmit} className="relative">
                <div className="flex flex-col sm:flex-row gap-3 p-2 bg-slate-50 rounded-2xl border border-slate-200/60">
                  <div className="relative flex-1">
                    <MailCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="email"
                      placeholder="your@email.com"
                      className={cn(
                        "w-full pl-12 pr-4 py-3.5 rounded-xl bg-white border transition-all text-slate-900 placeholder:text-slate-400",
                        "focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400",
                        emailError ? "border-red-300 bg-red-50/50" : "border-slate-200"
                      )}
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        if (emailError) setEmailError("");
                      }}
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    variant="primary"
                    className="h-12 sm:h-auto px-8 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
                  >
                    {isSubmitting ? (
                      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                        <Sparkles className="w-5 h-5" />
                      </motion.div>
                    ) : (
                      <span className="flex items-center gap-2">
                        Get started <ArrowRight className="w-4 h-4" />
                      </span>
                    )}
                  </Button>
                </div>
              </form>
              
              {emailError && (
                <motion.p
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-3 text-sm text-red-500 font-medium"
                >
                  {emailError}
                </motion.p>
              )}

              <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-slate-400">
                <span className="flex items-center gap-1.5"><Lock className="w-4 h-4" /> No credit card</span>
                <span className="flex items-center gap-1.5"><Shield className="w-4 h-4" /> Secure</span>
                <span className="flex items-center gap-1.5"><Clock className="w-4 h-4" /> 2-min setup</span>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className="w-full max-w-md bg-gradient-to-br from-slate-50 to-white rounded-2xl border border-slate-200 p-6 text-left shadow-xl"
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center shadow-lg shadow-blue-500/25">
                  <MailCheck className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold mb-0.5">Sent</p>
                  <p className="font-semibold text-slate-900">{sentEmail}</p>
                </div>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed mb-4">
                Check your inbox for the magic link. Click it to start your AI job search.
              </p>
              <button
                type="button"
                onClick={() => setSentEmail(null)}
                className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
              >
                Use different email
              </button>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="mt-16 w-full max-w-3xl"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent z-10 pointer-events-none" />
              
              <div className="bg-slate-900 rounded-2xl sm:rounded-3xl border border-slate-800 overflow-hidden shadow-2xl">
                <div className="flex items-center gap-2 px-4 sm:px-5 py-3 border-b border-slate-800">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-3 text-[10px] sm:text-xs font-mono text-slate-500 uppercase tracking-wider">AI Agent</span>
                </div>
                
                <div className="p-4 sm:p-6 space-y-3">
                  {[
                    { icon: Upload, label: "Resume parsed", detail: "24 skills extracted", done: true },
                    { icon: Search, label: "Scanning 12,847 jobs", detail: "Matching your profile...", done: false },
                    { icon: Send, label: "47 applications queued", detail: "Tailored per listing", done: true },
                    { icon: Bell, label: "3 interview requests", detail: "Recruiters responded!", done: true },
                  ].map((step, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.7 + i * 0.15, duration: 0.4 }}
                      className="flex items-center gap-3 sm:gap-4"
                    >
                      <div className={cn(
                        "w-9 sm:w-10 h-9 sm:h-10 rounded-lg flex items-center justify-center flex-shrink-0",
                        step.done ? "bg-emerald-500/20" : "bg-blue-500/20"
                      )}>
                        <step.icon className={cn("w-4 sm:w-5 h-4 sm:h-5", step.done ? "text-emerald-400" : "text-blue-400")} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm sm:text-base font-semibold text-white">{step.label}</p>
                        <p className="text-xs sm:text-sm text-slate-400">{step.detail}</p>
                      </div>
                      {step.done && <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />}
                    </motion.div>
                  ))}
                </div>
                
                <div className="px-4 sm:px-6 py-3 border-t border-slate-800 bg-slate-900/50">
                  <div className="flex justify-between text-xs font-mono text-slate-500 mb-2">
                    <span>Progress</span>
                    <span>78%</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-blue-500 via-violet-500 to-pink-500 rounded-full"
                      initial={{ width: "0%" }}
                      animate={{ width: "78%" }}
                      transition={{ delay: 1.5, duration: 1.2, ease: "easeOut" }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

<div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-50 to-transparent pointer-events-none" />
    </section>
  );
};

const LiveActivitySection = () => {
  const shouldReduceMotion = useReducedMotion();
  
  return (
    <section className="py-16 sm:py-20 bg-white border-y border-slate-100 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-12">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100 mb-6"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Live Feed</span>
            </motion.div>
            
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tighter-display text-slate-900 mb-4"
            >
              Watch it happen<br />
              <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">in real-time</span>
            </motion.h2>
            
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="font-body text-lg text-slate-500 mb-8 leading-relaxed"
            >
              Every few seconds, our AI submits another tailored application. 
              This is happening right now for users like you.
            </motion.p>
            
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
              className="flex flex-wrap gap-8"
            >
              <div>
                <p className="font-display text-4xl font-bold text-slate-900">847</p>
                <p className="text-sm text-slate-500">applications today</p>
              </div>
              <div>
                <p className="font-display text-4xl font-bold text-slate-900">23</p>
                <p className="text-sm text-slate-500">interview requests</p>
              </div>
              <div>
                <p className="font-display text-4xl font-bold text-slate-900">4.2s</p>
                <p className="text-sm text-slate-500">avg. apply time</p>
              </div>
            </motion.div>
          </div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="bg-slate-50 rounded-2xl border border-slate-200 p-6"
          >
            <LiveActivityStream />
          </motion.div>
        </div>
      </div>
    </section>
  );
};

const Onboarding = () => {
  return (
    <section id="how-it-works" className="py-24 sm:py-32 bg-slate-50 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-blue-100/30 to-violet-100/30 rounded-full blur-3xl opacity-60 -translate-y-1/2 translate-x-1/2 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-tr from-pink-100/20 to-amber-100/20 rounded-full blur-3xl opacity-50 translate-y-1/2 -translate-x-1/2 pointer-events-none" />

      <div className="container mx-auto px-5 sm:px-8 lg:px-12 relative z-10">
        <div className="text-center mb-16 lg:mb-20">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-slate-200 mb-6"
          >
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">How It Works</span>
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tighter-display text-slate-900 mb-4"
          >
            Four steps to <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">more interviews</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="font-body text-lg text-slate-500 max-w-2xl mx-auto"
          >
            Set up once, let the agent run. You only show up for the wins.
          </motion.p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          {[
            { icon: Upload, step: "01", title: "Upload Resume", desc: "Drop your PDF. We extract 40+ data points in seconds." },
            { icon: Search, step: "02", title: "AI Matches Jobs", desc: "Scans thousands of listings against your profile daily." },
            { icon: Send, step: "03", title: "Auto-Applies", desc: "Tailors each application to the specific job requirements." },
            { icon: Bell, step: "04", title: "You Get Interviews", desc: "We notify you only when a recruiter responds." },
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.1, duration: 0.5 }}
              viewport={{ once: true }}
              className="group relative bg-white rounded-2xl p-6 lg:p-8 border border-slate-200 hover:border-blue-200 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/5"
            >
              <div className="absolute top-4 right-4 text-xs font-mono text-slate-300 font-semibold">{item.step}</div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-blue-500/20">
                <item.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-display text-xl font-bold text-slate-900 mb-2 tracking-tight">{item.title}</h3>
              <p className="font-body text-sm text-slate-500 leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// AutomationEdge removed — Telegram integrated into Protocol Step 4

// --- MAIN PAGE ---
export default function Homepage() {
  return (
    <>
      <SEO
        title="JobHuntin — AI That Applies to Jobs While You Sleep"
        description="Upload your resume once. Your AI agent tailors and applies to hundreds of jobs daily. Land 3.4× more interviews with zero effort."
        ogTitle="JobHuntin — AI That Applies to Jobs While You Sleep"
        canonicalUrl="https://jobhuntin.com/"
        schema={{
          "@context": "https://schema.org",
          "@type": "FAQPage",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "Is this legit? Will I get banned from job sites?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Absolutely legit. We follow each platform's Terms of Service. We don't spam, we don't use bots that violate rate limits, and we never submit low-quality applications."
              }
            },
            {
              "@type": "Question",
              "name": "How is this different from just applying myself?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Speed and quality. Most people take 20-30 minutes per application. We do it in under 2 minutes, and we customize every resume and cover letter using AI."
              }
            },
            {
              "@type": "Question",
              "name": "What happens to my resume and data?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Your data is yours. We store it securely (encrypted at rest), never sell it to third parties, and you can delete everything anytime."
              }
            }
          ]
        }}
      />
<ProgressBar />
      <Hero />
      <LiveActivitySection />
      <Onboarding />
    </>
  );
}
