import React, { useState, useEffect } from 'react';
import { motion, useScroll, useSpring, useMotionValue, useMotionTemplate, AnimatePresence, useReducedMotion } from 'framer-motion';
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

// Animated Terminal Product Demo (replaces static Bot icon)
const ProductFlowDemo = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(typeof window !== 'undefined' && window.innerWidth < 640);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const steps = [
    { icon: Upload, label: isMobile ? "Resume" : "Resume Uploaded", detail: isMobile ? "1.2s" : "PDF parsed in 1.2s", color: "from-blue-500 to-blue-600" },
    { icon: Search, label: isMobile ? "Scanning" : "AI Scans 12,400 Jobs", detail: isMobile ? "Matching" : "Matching skills & context", color: "from-violet-500 to-violet-600" },
    { icon: Send, label: isMobile ? "Applied" : "47 Applications Sent", detail: isMobile ? "Tailored" : "Custom-tailored each one", color: "from-emerald-500 to-emerald-600" },
    { icon: Bell, label: isMobile ? "Interviews" : "3 Interview Requests", detail: isMobile ? "Response!" : "Recruiter responded!", color: "from-amber-500 to-amber-600" },
  ];

  useEffect(() => {
    if (shouldReduceMotion) return;
    const timer = setInterval(() => setActiveStep(s => (s + 1) % steps.length), 3000);
    return () => clearInterval(timer);
  }, [shouldReduceMotion]);

  const animationProps = shouldReduceMotion ? {} : {
    animate: {
      top: ["0%", "100%", "0%"]
    },
    transition: { duration: 6, repeat: Infinity, ease: "linear" }
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <div className={`w-full ${isMobile ? 'max-w-[90vw]' : 'max-w-md'} bg-slate-950 rounded-[2rem] p-4 sm:p-6 lg:p-8 shadow-2xl border border-white/5 overflow-hidden relative`}>
        {/* Scan line - disabled with reduced motion */}
        {!shouldReduceMotion && (
          <motion.div
            className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-primary-400/60 to-transparent"
            {...animationProps}
          />
        )}
        <div className="absolute inset-0 bg-grid-premium-dark opacity-40 pointer-events-none" />

        {/* Terminal header */}
        <div className="relative z-10 flex items-center gap-2 mb-4 sm:mb-6 pb-2 sm:pb-3 border-b border-white/5">
          <div className="w-2 sm:w-2.5 h-2 sm:h-2.5 rounded-full bg-red-500/80" />
          <div className="w-2 sm:w-2.5 h-2 sm:h-2.5 rounded-full bg-amber-500/80" />
          <div className="w-2 sm:w-2.5 h-2 sm:h-2.5 rounded-full bg-emerald-500/80" />
          <span className="ml-2 text-[8px] sm:text-[9px] font-mono text-white/30 uppercase tracking-widest">{isMobile ? 'v2.1' : 'agent v2.1 — live'}</span>
        </div>

        {/* Steps */}
        <div className="relative z-10 space-y-2 sm:space-y-3">
          {steps.map((step, i) => {
            const isActive = i === activeStep;
            const isPast = i < activeStep;
            const stepAnimationProps = shouldReduceMotion ? {
              opacity: 1,
              x: 0,
              scale: 1
            } : {
              animate: {
                opacity: isActive ? 1 : isPast ? 0.5 : 0.2,
                x: isActive ? 0 : isPast ? -4 : 4,
                scale: isActive ? 1 : 0.97,
              },
              transition: { duration: 0.5, ease: "easeOut" }
            };

            return (
              <motion.div
                key={i}
                {...stepAnimationProps}
                className="flex items-center gap-2 sm:gap-3"
              >
                <div className={cn(
                  `w-7 sm:w-9 h-7 sm:h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-500`,
                  isActive ? `bg-gradient-to-br ${step.color} shadow-lg` : "bg-white/5"
                )}>
                  <step.icon className={cn("w-3 sm:w-4 h-3 sm:h-4", isActive ? "text-white" : "text-white/30")} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1 sm:gap-2">
                    <p className={cn(`text-xs sm:text-sm font-bold tracking-tight`, isActive ? "text-white" : "text-white/30")}>
                      {step.label}
                    </p>
                    {isPast && <CheckCircle className="w-2 sm:w-3 h-2 sm:h-3 text-emerald-400" />}
                  </div>
                  <p className={cn("text-[10px] sm:text-xs font-mono", isActive ? "text-white/60" : "text-white/15")}>
                    {step.detail}
                  </p>
                </div>
                {isActive && !shouldReduceMotion && (
                  <motion.div
                    className="w-1.5 sm:w-2 h-1.5 sm:h-2 rounded-full bg-emerald-400"
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="relative z-10 mt-4 sm:mt-6 pt-3 sm:pt-4 border-t border-white/5">
          <div className="flex justify-between text-[8px] sm:text-[9px] font-mono text-white/30 mb-1 sm:mb-1.5 uppercase tracking-widest">
            <span>{isMobile ? 'Progress' : 'Agent Progress'}</span>
            <span>{((activeStep + 1) / steps.length * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1 sm:h-1.5 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-primary-500 to-emerald-500 rounded-full"
              animate={{ width: shouldReduceMotion ? "100%" : `${((activeStep + 1) / steps.length) * 100}%` }}
              transition={{ duration: shouldReduceMotion ? 0 : 0.8, ease: "easeOut" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// 3. Progress Bar
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

// 7. Hero Section
const Hero = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [matchCount, setMatchCount] = useState(0);
  const [jobs, setJobs] = useState(TEASER_JOBS);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);
  const shouldReduceMotion = useReducedMotion();

  // Background Particles Data - Responsive design
  const particles = React.useMemo(() => {
    const isMobile = typeof window !== 'undefined' && window.innerWidth < 640;
    const particleCount = isMobile ? 8 : 25;
    
    return [...Array(particleCount)].map((_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: i < 5 ? Math.random() * 150 + 100 : Math.random() * 40 + 10,
      duration: Math.random() * 20 + 20,
      delay: Math.random() * 10,
      yMove: (Math.random() - 0.5) * 100,
      xMove: (Math.random() - 0.5) * 50,
      color: i % 3 === 0 ? 'rgba(255, 107, 53, 0.15)' : 'rgba(74, 144, 226, 0.15)',
      blur: i < 5 ? 'blur(60px)' : 'none'
    }));
  }, []);

  // Mouse Glow
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  const validateEmail = (e: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());
  };

  const timeoutRef = React.useRef<any>(null);
  const animationRef = React.useRef<any>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) {
      console.log("Already submitting, ignoring duplicate request");
      return;
    }
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

      // Safe Animation Trigger - wrapped in try-catch to prevent crashes
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
        // Don't crash if animation fails
      }

      // Safe Confetti Trigger - disabled with reduced motion
      try {
        if (typeof window !== 'undefined' && confetti && !shouldReduceMotion) {
          confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#FF6B35', '#4A90E2', '#FAF9F6']
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
        throw innerErr; // Re-throw to trigger outer catch
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

  const removeJob = (index: number) => {
    setJobs(prev => prev.filter((_, i) => i !== index));
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setJobs(prev => [...prev, {
        id: Math.random().toString(36).substr(2, 9),
        title: "New Match Found!",
        status: "Analyzing..."
      }]);
    }, 500);
  };

  return (
    <section className="relative min-h-screen lg:min-h-[85vh] pt-20 sm:pt-24 md:pt-28 lg:pt-0 pb-12 sm:pb-16 lg:pb-20 flex items-start lg:items-center justify-center overflow-hidden bg-slate-50">
      {/* Premium Background Layers */}
      <div className="absolute inset-0 bg-grid-premium opacity-[0.4] pointer-events-none" />

      {/* Large Artistic Gradient Blobs - Responsive */}
      {!shouldReduceMotion && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {particles.map((particle, index) => (
            <motion.div
              key={particle.id}
              className="absolute rounded-full"
              animate={{
                y: [0, particle.yMove, 0],
                x: [0, particle.xMove, 0],
                rotate: [0, 360],
                scale: [1, 1.1, 1]
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
                width: typeof window !== 'undefined' && window.innerWidth < 640 ? particle.size * 0.6 : particle.size,
                height: typeof window !== 'undefined' && window.innerWidth < 640 ? particle.size * 0.6 : particle.size,
                background: particle.color,
                filter: particle.blur,
                willChange: "transform",
                opacity: typeof window !== 'undefined' && window.innerWidth < 640 ? 0.3 : 1
              }}
            />
          ))}
        </div>
      )}

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 grid lg:grid-cols-2 gap-12 lg:gap-20 gap-y-16 items-start lg:items-center min-h-[640px] lg:min-h-0">
        {/* Left Content */}
        <div className="w-full text-center lg:text-left pt-6 sm:pt-10 lg:pt-0 space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-sm mb-6 border border-primary-100"
          >
            <Sparkles className="w-4 h-4 text-primary-500" />
            <span className="text-xs sm:text-sm font-semibold text-slate-600">
              12,847 applications sent this week
            </span>
          </motion.div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-black font-display text-slate-900 leading-tight sm:leading-[1.05] mb-6 sm:mb-8 tracking-tight text-balance mx-auto lg:mx-0 max-w-2xl">
            Someone else applied<br />
            <span className="relative inline-block mt-2">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 via-amber-500 to-red-500 animate-gradient-x">
                to your dream job today.
              </span>
            </span>
          </h1>

          <p className="text-base sm:text-lg lg:text-2xl text-slate-500 mb-8 sm:mb-10 max-w-xl mx-auto lg:mx-0 leading-relaxed font-medium text-balance">
            JobHuntin's AI agent fires off <span className="text-slate-900 font-bold">100 tailored applications</span> while you sleep.
            Wake up to <span className="text-emerald-700 font-bold">interview requests</span>, not rejection silence.
          </p>

          {!sentEmail && (
            <div
              className="group relative max-w-lg mx-auto lg:mx-0 p-1 rounded-2xl bg-gradient-to-r from-primary-500 to-amber-500 transition-transform hover:scale-[1.01]"
              onMouseMove={handleMouseMove}
            >
              {/* Mouse glow effect only on non-touch devices */}
              {typeof window !== 'undefined' && window.matchMedia('(pointer: fine)').matches && (
                <motion.div
                  className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                  style={{
                    background: useMotionTemplate`
                    radial-gradient(
                      650px circle at ${mouseX}px ${mouseY}px,
                      rgba(255, 255, 255, 0.4),
                      transparent 40%
                    )
                  `,
                  }}
                />
              )}
              <form onSubmit={onSubmit} className="bg-white rounded-xl p-2 flex flex-col sm:flex-row gap-2 relative z-10">
                <div className="flex-1">
                  <input
                    type="email"
                    placeholder="you@example.com"
                    className={cn(
                      "w-full px-4 py-3 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 transition-all text-slate-900",
                      emailError ? "ring-2 ring-red-500 bg-red-50" : "focus:ring-primary-500/20"
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
                  variant="secondary"
                  size="lg"
                  className="w-full sm:w-auto px-8 py-3 rounded-lg shadow-lg hover:shadow-primary-500/25 whitespace-nowrap"
                >
                  {isSubmitting ? (
                    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                      <Sparkles className="w-5 h-5" />
                    </motion.div>
                  ) : (
                    <>
                      Start free — before they hire someone else <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </form>
            </div>
          )}

          {emailError && (
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-red-500 text-sm mt-2 font-medium"
            >
              {emailError}
            </motion.p>
          )}

          {matchCount > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 flex items-center gap-2 justify-center lg:justify-start text-primary-600 font-bold"
            >
              <CheckCircle className="w-5 h-5" />
              Found {matchCount} Denver matches!
            </motion.div>
          )}

          {/* Trust Signals */}
          <div className="mt-6 flex items-center justify-center lg:justify-start gap-5 text-xs text-slate-400 font-medium">
            <span className="flex items-center gap-1.5"><Lock className="w-3.5 h-3.5" /> No credit card</span>
            <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5" /> Encrypted data</span>
            <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> 2 min setup</span>
            <span className="flex items-center gap-1.5 border-l border-slate-300 pl-4 ml-1">
              <span className="sr-only">Featured on Wellfound</span>
              <svg viewBox="0 0 108 24" className="h-4 w-auto text-slate-400" fill="currentColor">
                <path d="M12.9 8.6c-.7-1.5-3-2.6-5.8-2.6-4.2 0-7.2 3.1-7.2 7.7s2.9 7.7 7.2 7.7c2.8 0 5-1.1 5.8-2.6h2.8c-1.1 2.8-4.6 4.9-8.6 4.9C3.1 23.7 0 19.8 0 13.7S3.1 3.7 7.1 3.7c4 0 7.5 2.1 8.6 4.9h-2.8zm11.2-4.6h3.2v19.4h-3.2V4zm-1.6 2.6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm28.3 1.9h3.3v15.2h-3.2v-1.4c-1.2 1.2-2.9 1.7-4.4 1.7-4.5 0-7.8-3.4-7.8-8s3.4-8 7.8-8c1.5 0 3.3.5 4.3 1.7V8.5zm-4.3 13c2.7 0 4.7-2.1 4.7-5.5 0-3.3-2-5.5-4.7-5.5-2.8 0-4.8 2.1-4.8 5.5.1 3.4 2.1 5.5 4.8 5.5zm16-5.8c.1 4.6 3.4 5.9 6.2 5.9 1.8 0 3.8-.5 5.5-1.4l.7 2.3c-1.8 1.1-4.3 1.7-6.5 1.7-4.7 0-9.1-2.9-9.1-8.5 0-5.2 3.7-8.3 8.6-8.3 5.3 0 7.9 3.6 7.9 8.3v.1h-13.3zm10.1-2.2c-.1-2.6-1.8-4-4.8-4-2.6 0-4.4 1.5-4.9 4h9.7zM97.1 8.5h3.2v1.5c1-1.3 2.9-1.8 4.6-1.8 1.3 0 2.4.3 3.3.7l-.8 2.8c-.8-.4-1.7-.7-2.6-.7-2.8 0-4.5 2.2-4.5 5v7.7h-3.2V8.5z" />
              </svg>
            </span>
          </div>

          {sentEmail && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 bg-white border border-slate-100 rounded-2xl p-5 shadow-lg text-left"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-primary-50 flex items-center justify-center">
                  <MailCheck className="w-5 h-5 text-primary-500" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold">Magic link en route</p>
                  <p className="text-base font-semibold text-slate-900">Sent to {sentEmail}</p>
                </div>
              </div>
              <p className="text-sm text-slate-600 mb-3">
                Look for an email from <span className="font-semibold">noreply@jobhuntin.com</span>. When you tap the link we’ll drop you straight into onboarding.
              </p>
              <ol className="list-decimal list-inside space-y-2 text-sm text-slate-600">
                <li>Open the inbox (or spam folder) for {sentEmail}.</li>
                <li>Find the message titled <em>“Start your JobHuntin run”</em> and press the button.</li>
                <li>Keep this tab open—onboarding launches as soon as the link opens.</li>
              </ol>
              <div className="flex flex-wrap gap-3 mt-4">
                <button
                  type="button"
                  onClick={() => setSentEmail(null)}
                  className="text-sm font-semibold text-primary-600 hover:underline"
                >
                  Use a different email
                </button>
              </div>
            </motion.div>
          )}

          <div className="mt-8 flex items-center justify-center lg:justify-start gap-4 text-sm text-slate-500">
            <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center animate-bounce-slow">
              <UploadCloud className="w-6 h-6 text-primary-500" />
            </div>
            <p className="leading-tight">
              <span className="font-bold text-slate-900">Drag & Drop Resume</span><br />
              to activate auto-apply
            </p>
          </div>
        </div>

        {/* Right Content - Swipe Cards */}
        <div className="relative h-[320px] sm:h-[420px] lg:h-[520px] w-full flex items-center justify-center perspective-1000 mt-4 lg:mt-0">
          <AnimatePresence>
            {jobs.slice(0, 3).map((job, index) => (
              <motion.div
                key={job.id}
                className="absolute w-full max-w-[min(85vw,22rem)] sm:max-w-sm bg-white rounded-2xl shadow-2xl p-5 sm:p-6 border border-slate-100 cursor-grab active:cursor-grabbing touch-pan-y"
                style={{ zIndex: jobs.length - index }}
                initial={{ scale: 0.9, y: 50 * index, opacity: 1 - index * 0.3 }}
                animate={{ scale: 1 - index * 0.05, y: 20 * index, opacity: 1 - index * 0.2 }}
                exit={{ x: 200, opacity: 0, rotate: 20 }}
                drag="x"
                dragConstraints={{ left: 0, right: 0 }}
                onDragEnd={(_, info) => {
                  if (info.offset.x > 100 || info.offset.x < -100) {
                    removeJob(index);
                  }
                }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
                    <Bot className="w-6 h-6 text-blue-500" />
                  </div>
                  <span className="bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full text-xs font-bold">
                    98% Match
                  </span>
                </div>
                <h3 className="text-xl font-bold text-slate-900">{job.title}</h3>
                <p className="text-slate-500 mb-4">{job.status}</p>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-primary-500"
                    initial={{ width: 0 }}
                    animate={{ width: "98%" }}
                    transition={{ duration: 1.5, delay: 0.5 }}
                  />
                </div>
                <p className="text-xs text-right mt-1 text-slate-400">AI Analysis Complete</p>
              </motion.div>
            ))}
          </AnimatePresence>

          <motion.div
            className="absolute bottom-4 sm:bottom-10 right-10 text-slate-400 flex items-center gap-2 pointer-events-none bg-white/50 backdrop-blur px-2 py-1 rounded"
            animate={{ x: [0, 20, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            <span className="text-sm font-medium">Swipe to apply</span>
            <ArrowRight className="w-4 h-4" />
          </motion.div>
        </div>
      </div>

      {/* Wavy Divider */}
      <div className="absolute bottom-0 left-0 right-0 w-full overflow-hidden leading-none">
        <svg className="relative block w-[calc(100%+1.3px)] h-[50px] sm:h-[100px]" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none">
          <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z" className="fill-white"></path>
        </svg>
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
              <ProductFlowDemo />
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
              <span className="text-primary-600">Infinite Reach.</span>
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
      <Onboarding />
    </>
  );
}
