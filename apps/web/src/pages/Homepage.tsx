import React, { useState, useEffect } from 'react';
import { motion, useScroll, useSpring, useMotionValue, useMotionTemplate, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { magicLinkService } from '../services/magicLinkService';
import {
  Rocket, Sparkles, Zap, CheckCircle, ArrowRight, UploadCloud,
  MailCheck, UserCircle, Target, Brain, Bell, Bot,
  Upload, Search, Send, Lock, Shield, Clock
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { MarketingFooter } from '../components/marketing/MarketingFooter';
import { Button } from '../components/ui/Button';

// --- UTILS ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- DATA ---
const TEASER_JOBS = [
  { id: "t1", title: "Marketing Lead", status: "AI Applied 2m ago" },
  { id: "t2", title: "Sales Manager", status: "Matching..." },
  { id: "t3", title: "Operations Dir", status: "Interview Request!" },
];

// --- COMPONENTS ---

// Animated Vertical Timeline (replaces Terminal)
const AgentTimeline = () => {
  const steps = [
    { icon: Upload, label: "Resume Uploaded", detail: "PDF parsed in 1.2s", status: "complete" },
    { icon: Search, label: "AI Scans 12,400 Jobs", detail: "Matching skills & context", status: "active" },
    { icon: Send, label: "47 Applications Sent", detail: "Custom-tailored each one", status: "pending" },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-slate-100 p-8 max-w-sm mx-auto w-full relative overflow-hidden">
      {/* Decorative gradient blob */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary-100 rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

      <div className="relative">
        {/* Thread line */}
        <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-slate-100"></div>

        <div className="space-y-10">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2 }}
              className="relative flex gap-5"
            >
              <div className={cn(
                "relative z-10 w-12 h-12 rounded-full flex items-center justify-center border-4 border-white shadow-sm transition-all duration-500",
                step.status === 'complete' ? "bg-slate-50 text-slate-400" :
                  step.status === 'active' ? "bg-primary-500 text-white scale-110 shadow-primary-500/30" : "bg-slate-50 text-slate-200"
              )}>
                {step.status === 'complete' ? (
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                ) : (
                  <step.icon className="w-5 h-5" />
                )}
              </div>
              <div className="pt-2">
                <h4 className={cn("font-bold text-base leading-none mb-1.5", step.status === 'pending' ? "text-slate-400" : "text-slate-900")}>
                  {step.label}
                </h4>
                <p className="text-xs text-slate-500 font-medium tracking-wide bg-slate-50 px-2 py-1 rounded inline-block">{step.detail}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

// 7. Hero Section
const Hero = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [matchCount, setMatchCount] = useState(0);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);

  // Animation refs for cleanup
  const timeoutRef = React.useRef<any>(null);
  const animationRef = React.useRef<any>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  const validateEmail = (e: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address.");
      return;
    }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);
    setMatchCount(0);

    // Use shared service
    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");

      if (!result.success) {
        throw new Error(result.error || "Failed to send magic link");
      }

      // Safe Animation Trigger
      try {
        if (
          typeof window !== 'undefined' &&
          typeof window.performance !== 'undefined' &&
          typeof window.requestAnimationFrame === 'function'
        ) {
          const end = 47;
          const duration = 1000;
          const startTime = performance.now();
          const animateCounter = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            setMatchCount(Math.floor(progress * end));
            if (progress < 1) {
              animationRef.current = requestAnimationFrame(animateCounter);
            }
          };
          animationRef.current = requestAnimationFrame(animateCounter);
        }
      } catch (e) {
        console.warn("Animation failed", e);
      }

      // Safe Confetti Trigger
      try {
        if (typeof window !== 'undefined' && confetti) {
          confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#FF9500', '#EA580C', '#FAFAFA'] // Updated to orange palette
          });
        }
      } catch (e) {
        console.warn("Confetti failed", e);
      }

      // Success state updates
      try {
        console.log("Magic link success, updating state", result);
        pushToast({ title: "Magic Link Sent! 📧", description: "Check your email to start hunting.", tone: "success" });
        setSentEmail(result.email);
        setEmail(""); // Clear
        setIsSubmitting(false);
      } catch (innerErr) {
        console.error("Critical error updating success state", innerErr);
        throw innerErr;
      }

    } catch (err: any) {
      console.error("Magic Link Submit Error:", err);
      setIsSubmitting(false);
      setSentEmail(null);
      const message = err?.message || "Failed to send magic link";
      setEmailError(message);
      pushToast({ title: "Error", description: message, tone: "error" });
    }
  };

  return (
    <>
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 bg-slate-50 overflow-hidden">
        {/* Subtle background mesh if needed, but keeping it clean for now */}

        <div className="container mx-auto px-4 max-w-6xl relative z-10 transition-all duration-500">
          <div className="text-center max-w-4xl mx-auto mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-2 bg-white border border-slate-200 rounded-full px-4 py-1.5 mb-8 shadow-sm"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
              </span>
              <span className="text-xs font-semibold text-slate-600 tracking-wide uppercase">
                AI Agent v2.1 Now Live
              </span>
            </motion.div>

            <h1 className="text-5xl sm:text-7xl lg:text-8xl font-bold font-display text-slate-900 tracking-tight leading-[1] mb-8">
              Stop applying. <br className="hidden sm:block" />
              <span className="text-primary-500">Start landing.</span>
            </h1>

            <p className="text-lg sm:text-xl text-slate-500 mb-10 max-w-2xl mx-auto leading-relaxed">
              You've spent <span className="text-slate-900 font-semibold">200+ hours</span> applying.
              Your AI agent does it in <span className="text-primary-600 font-semibold">20 minutes</span>.
              Upload once — it applies, tailors, and follows up while you sleep.
            </p>

            {/* Email Input Form */}
            {!sentEmail ? (
              <div className="max-w-md mx-auto relative group">
                <form onSubmit={onSubmit} className="relative z-10">
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1 relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <MailCheck className="h-5 w-5 text-slate-400" />
                      </div>
                      <input
                        type="email"
                        placeholder="you@example.com"
                        className={cn(
                          "w-full pl-10 pr-4 py-3.5 rounded-lg border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all shadow-sm",
                          emailError && "border-red-300 focus:ring-red-200 focus:border-red-500"
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
                      className="px-8 py-3.5 rounded-lg font-semibold shadow-lg shadow-primary-500/20 hover:shadow-primary-500/30 transition-all bg-primary-500 hover:bg-primary-600 text-white whitespace-nowrap"
                    >
                      {isSubmitting ? (
                        <div className="flex items-center gap-2">
                          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                            <Sparkles className="w-4 h-4" />
                          </motion.div>
                          <span>Starting...</span>
                        </div>
                      ) : (
                        <span className="flex items-center gap-2">Start Hunt <ArrowRight className="w-4 h-4" /></span>
                      )}
                    </Button>
                  </div>
                </form>
                {/* Error Message */}
                {emailError && (
                  <motion.p
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute -bottom-8 left-0 right-0 text-center text-red-500 text-sm font-medium"
                  >
                    {emailError}
                  </motion.p>
                )}
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-md mx-auto bg-white border border-slate-200 rounded-2xl p-6 shadow-xl text-left"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center shrink-0">
                    <MailCheck className="w-6 h-6 text-green-500" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900">Check your inbox!</h3>
                    <p className="text-sm text-slate-500">We sent a magic link to <span className="font-semibold text-slate-900">{sentEmail}</span></p>
                  </div>
                </div>
                <div className="bg-slate-50 rounded-lg p-4 mb-4 text-sm text-slate-600 border border-slate-100">
                  <p className="flex items-start gap-2">
                    <span className="mt-1 block w-1.5 h-1.5 rounded-full bg-primary-500 shrink-0"></span>
                    Tap the button in the email to sign in instantly.
                  </p>
                </div>
                <button
                  onClick={() => setSentEmail(null)}
                  className="text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline w-full text-center"
                >
                  Use a different email
                </button>
              </motion.div>
            )}
          </div>

          {/* Hero Video Placeholder */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
            className="relative aspect-video bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 overflow-hidden mx-auto max-w-5xl group"
          >
            <div className="absolute inset-0 bg-gradient-to-tr from-slate-900 via-slate-800 to-slate-900 opacity-90"></div>
            {/* Abstract UI Mockup in background */}
            <div className="absolute inset-x-12 top-12 bottom-0 bg-slate-950 rounded-t-xl border-t border-l border-r border-slate-800 shadow-2xl opacity-50 transform translate-y-4"></div>

            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6 backdrop-blur-md border border-white/10 group-hover:scale-110 transition-transform duration-300 cursor-pointer">
                  <div className="ml-1 w-0 h-0 border-t-[12px] border-t-transparent border-l-[20px] border-l-white border-b-[12px] border-b-transparent shadow-lg"></div>
                </div>
                <p className="text-slate-400 font-medium tracking-wide uppercase text-sm">Watch the Demo</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <JobMatchingSection />
    </>
  );
};

// New Job Matching Grid Section
const JobMatchingSection = () => {
  return (
    <section className="py-24 bg-white border-b border-slate-100">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4 tracking-tight">Matches that actually fit.</h2>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto">
            Our AI analyzes 50+ data points to ensure 98% compatibility before you even see the role.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {TEASER_JOBS.map((job, i) => (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="bg-white rounded-xl p-6 border border-slate-200 shadow-[0_4px_20px_rgba(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.08)] transition-all duration-300 hover:-translate-y-1 group"
            >
              <div className="flex items-start justify-between mb-6">
                <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center border border-slate-100 group-hover:border-primary-100 group-hover:bg-primary-50 transition-colors">
                  <Target className="w-6 h-6 text-slate-400 group-hover:text-primary-500 transition-colors" />
                </div>
                <div className="relative">
                  <svg className="w-12 h-12 transform -rotate-90">
                    <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="3" fill="transparent" className="text-slate-100" />
                    <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="3" fill="transparent" className="text-primary-500" strokeDasharray="125.6" strokeDashoffset="10" strokeLinecap="round" />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-slate-700">98%</span>
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">{job.title}</h3>
              <div className="flex items-center gap-2 mb-4">
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-sm font-medium text-emerald-600">{job.status}</span>
              </div>

              <div className="w-full bg-slate-50 rounded-lg p-3 border border-slate-100 mt-4">
                <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
                  <Brain className="w-3.5 h-3.5" />
                  <span>AI Analysis</span>
                </div>
                <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-slate-900 w-[92%] rounded-full"></div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// 8. Onboarding & Features
const Onboarding = () => {
  return (
    <section id="how-it-works" className="py-32 bg-white relative overflow-hidden">
      {/* Subtle Background Art */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-slate-50 rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2 pointer-events-none" />

      <div className="container mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-24 items-center">
          <div className="relative group">
            <motion.div
              className="aspect-square bg-slate-50 rounded-[3rem] flex items-center justify-center relative z-10 overflow-hidden shadow-inner"
              initial={{ scale: 0.9, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true }}
            >
              <AgentTimeline />
            </motion.div>
            <div className="absolute -top-12 -left-12 w-48 h-48 bg-primary-500/5 rounded-full blur-3xl" />
            <div className="absolute -bottom-12 -right-12 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl" />
          </div>

          <div>
            <div className="inline-block bg-primary-50 text-primary-600 px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.2em] mb-6">
              The Protocol
            </div>
            <h2 className="text-5xl sm:text-6xl font-black font-display text-slate-900 leading-[1.1] mb-12 tracking-tighter">
              One Click. <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-amber-500">Infinite Reach.</span>
            </h2>
            <div className="space-y-12">
              {[
                {
                  icon: UserCircle,
                  title: "We See The Real You",
                  desc: "Forget keywords. We build a psychological profile of your career narrative, capturing the nuance, ambition, and potential that resumes often miss. We translate 'you' into a language recruiters crave."
                },
                {
                  icon: Target,
                  title: "Stop Wasting Emotional Energy",
                  desc: "Applying is draining. Rejection is personal. We detach the emotion from the process. Our agent acts as your relentless, unfeeling advocate, ensuring you only engage when there's a real signal."
                },
                {
                  icon: Rocket,
                  title: "Autonomous Submission",
                  desc: "Every application is unique. Custom-tailored cover letters and optimized form-filling happen in milliseconds, not minutes. We handle the grind; you handle the interview."
                },
                {
                  icon: Bell,
                  title: "You Only Show Up for Wins",
                  desc: "Get notified the moment a recruiter responds. Approve next steps with one tap via Telegram or email. We handle the grind — you handle the interview."
                }
              ].map((step, i) => (
                <motion.div
                  key={i}
                  className="flex gap-8 group"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.2 }}
                  viewport={{ once: true }}
                >
                  <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center flex-shrink-0 group-hover:bg-primary-500 group-hover:rotate-6 transition-all duration-500 shadow-sm group-hover:shadow-primary-500/20">
                    <step.icon className="w-8 h-8 text-primary-500 group-hover:text-white transition-colors" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-slate-900 mb-2 tracking-tight">{step.title}</h3>
                    <p className="text-slate-500 text-lg leading-relaxed font-medium">{step.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// AutomationEdge removed — Telegram integrated into Protocol Step 4

// --- MAIN PAGE ---
export default function Homepage() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 overflow-x-hidden selection:bg-primary-500/20 selection:text-primary-700">
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

      <main>
        <Hero />
        <Onboarding />
      </main>
      <MarketingFooter />
    </div>
  );
}
