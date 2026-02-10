import React, { useState, useEffect, useRef } from 'react';
import { motion, useScroll, useSpring, useMotionValue, useMotionTemplate, AnimatePresence, useInView } from 'framer-motion';
import confetti from 'canvas-confetti';
import { magicLinkService } from '../services/magicLinkService';
import {
  Sparkles, Zap, CheckCircle, ArrowRight, ArrowDown,
  MailCheck, Rocket, FileText, Shield, Clock,
  Upload, Search, Send, Bell, ChevronRight, Lock,
  UserCircle, Target, Brain, Cpu, BarChart3, Globe
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { MarketingFooter } from '../components/marketing/MarketingFooter';
import { Button } from '../components/ui/Button';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ─── Animated Counter ─────────────────────────────────────────────────
function AnimatedNumber({ target, duration = 2000, suffix = '' }: { target: number; duration?: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;
    const start = performance.now();
    const animate = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3); // cubic ease out
      setCount(Math.floor(ease * target));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [isInView, target, duration]);

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>;
}

// ─── Scroll Progress ──────────────────────────────────────────────────
const ProgressBar = () => {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });
  return (
    <div className="fixed top-0 left-0 right-0 h-1 bg-slate-100 z-[60]">
      <motion.div className="h-full bg-gradient-to-r from-primary-500 to-emerald-500" style={{ scaleX, transformOrigin: "0%" }} />
    </div>
  );
};

// ─── Animated Product Flow Demo ───────────────────────────────────────
//   Replaces the static Bot icon. Shows: Upload → AI Scan → Match → Apply
const ProductFlowDemo = () => {
  const [activeStep, setActiveStep] = useState(0);
  const steps = [
    { icon: Upload, label: "Resume Uploaded", detail: "PDF parsed in 1.2s", color: "from-blue-500 to-blue-600" },
    { icon: Search, label: "AI Scans 12,400 Jobs", detail: "Matching skills & context", color: "from-violet-500 to-violet-600" },
    { icon: Send, label: "47 Applications Sent", detail: "Custom-tailored each one", color: "from-emerald-500 to-emerald-600" },
    { icon: Bell, label: "3 Interview Requests", detail: "Recruiter responded!", color: "from-amber-500 to-amber-600" },
  ];

  useEffect(() => {
    const timer = setInterval(() => setActiveStep(s => (s + 1) % steps.length), 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative">
      {/* Glow backdrop */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 via-transparent to-emerald-500/10 rounded-[3rem] blur-2xl" />

      <div className="relative bg-slate-950 rounded-[2.5rem] p-8 md:p-10 shadow-2xl border border-white/5 overflow-hidden">
        {/* Scan line */}
        <motion.div
          className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-primary-400/60 to-transparent"
          animate={{ top: ["0%", "100%", "0%"] }}
          transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
        />

        {/* Grid background */}
        <div className="absolute inset-0 bg-grid-premium-dark opacity-40 pointer-events-none" />

        {/* Terminal header */}
        <div className="relative z-10 flex items-center gap-2 mb-8 pb-4 border-b border-white/5">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-amber-500/80" />
          <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          <span className="ml-3 text-[10px] font-mono text-white/30 uppercase tracking-widest">jobhuntin agent v2.1 — live</span>
        </div>

        {/* Steps */}
        <div className="relative z-10 space-y-4">
          {steps.map((step, i) => {
            const isActive = i === activeStep;
            const isPast = i < activeStep;
            return (
              <motion.div
                key={i}
                animate={{
                  opacity: isActive ? 1 : isPast ? 0.5 : 0.2,
                  x: isActive ? 0 : isPast ? -4 : 4,
                  scale: isActive ? 1 : 0.97,
                }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="flex items-center gap-4"
              >
                <div className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-500",
                  isActive ? `bg-gradient-to-br ${step.color} shadow-lg` : "bg-white/5"
                )}>
                  <step.icon className={cn("w-5 h-5", isActive ? "text-white" : "text-white/30")} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className={cn("text-sm font-bold tracking-tight", isActive ? "text-white" : "text-white/30")}>
                      {step.label}
                    </p>
                    {isPast && <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
                  </div>
                  <p className={cn("text-xs font-mono", isActive ? "text-white/60" : "text-white/15")}>
                    {step.detail}
                  </p>
                </div>
                {isActive && (
                  <motion.div
                    className="w-2 h-2 rounded-full bg-emerald-400"
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="relative z-10 mt-8 pt-6 border-t border-white/5">
          <div className="flex justify-between text-[10px] font-mono text-white/30 mb-2 uppercase tracking-widest">
            <span>Agent Progress</span>
            <span>{((activeStep + 1) / steps.length * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-primary-500 to-emerald-500 rounded-full"
              animate={{ width: `${((activeStep + 1) / steps.length) * 100}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Hero Section ─────────────────────────────────────────────────────
const Hero = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);
  const timeoutRef = useRef<any>(null);
  const animationRef = useRef<any>(null);

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  const validateEmail = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address.");
      return;
    }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);

    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");
      if (!result.success) throw new Error(result.error || "Failed to send magic link");

      try {
        if (typeof window !== 'undefined' && confetti) {
          confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 }, colors: ['#3b82f6', '#10b981', '#f8fafc'] });
        }
      } catch { /* animation failure is non-critical */ }

      pushToast({ title: "Magic Link Sent! 📧", description: "Check your email to start hunting.", tone: "success" });
      setSentEmail(result.email);
      setEmail("");
      setIsSubmitting(false);
    } catch (err: any) {
      setIsSubmitting(false);
      setSentEmail(null);
      const message = err?.message || "Failed to send magic link";
      setEmailError(message);
      pushToast({ title: "Error", description: message, tone: "error" });
    }
  };

  // Ambient particles — organic, warm blobs
  const particles = React.useMemo(() =>
    [...Array(18)].map((_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: i < 4 ? Math.random() * 200 + 120 : Math.random() * 50 + 15,
      duration: Math.random() * 25 + 15,
      delay: Math.random() * 8,
      yMove: (Math.random() - 0.5) * 120,
      xMove: (Math.random() - 0.5) * 120,
      color: i % 4 === 0 ? 'rgba(59, 130, 246, 0.08)'
        : i % 4 === 1 ? 'rgba(16, 185, 129, 0.06)'
          : i % 4 === 2 ? 'rgba(139, 92, 246, 0.05)'
            : 'rgba(248, 250, 252, 0.15)',
      blur: i < 4 ? 'blur(80px)' : 'blur(20px)',
    })), []);

  return (
    <section className="relative min-h-[92vh] pt-32 pb-20 flex items-center overflow-hidden bg-slate-50">
      {/* Subtle grid */}
      <div className="absolute inset-0 bg-grid-premium opacity-30 pointer-events-none" />

      {/* Ambient particles */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {particles.map((p) => (
          <motion.div
            key={p.id}
            className="absolute rounded-full"
            animate={{
              y: [0, p.yMove, 0],
              x: [0, p.xMove, 0],
              scale: [1, 1.08, 1],
            }}
            transition={{ duration: p.duration, repeat: Infinity, ease: "easeInOut", delay: p.delay }}
            style={{
              left: `${p.left}%`, top: `${p.top}%`,
              width: p.size, height: p.size,
              background: p.color, filter: p.blur, willChange: "transform",
            }}
          />
        ))}
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-6 relative z-10 grid lg:grid-cols-2 gap-14 lg:gap-20 items-center">
        {/* ─ Left: Copy ─ */}
        <div className="text-center lg:text-left pt-8 lg:pt-0">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2.5 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-sm mb-8 border border-primary-100"
          >
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
            </span>
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">AI Agent Active — Applying Now</span>
          </motion.div>

          {/* ── Emotional headline ── */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl sm:text-6xl lg:text-7xl font-black font-display text-slate-900 leading-[0.92] mb-6 tracking-tighter"
          >
            Stop applying.<br />
            <span className="relative inline-block mt-1">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 via-violet-500 to-emerald-500 animate-gradient-x">
                Start landing.
              </span>
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-lg sm:text-xl text-slate-500 mb-10 max-w-lg mx-auto lg:mx-0 leading-relaxed font-medium"
          >
            You've spent <span className="text-slate-900 font-bold">200+ hours</span> applying to jobs this year.
            Your AI agent does it in <span className="text-emerald-600 font-bold">20 minutes</span>.
            Upload once — it applies, tailors, and follows up while you sleep.
          </motion.p>

          {/* ── Email capture ── */}
          {!sentEmail ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div
                className="group relative max-w-md mx-auto lg:mx-0 p-[2px] rounded-2xl bg-gradient-to-r from-primary-500 via-violet-500 to-emerald-500 transition-transform hover:scale-[1.01]"
                onMouseMove={handleMouseMove}
              >
                <motion.div
                  className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                  style={{
                    background: useMotionTemplate`radial-gradient(500px circle at ${mouseX}px ${mouseY}px, rgba(255,255,255,0.25), transparent 40%)`,
                  }}
                />
                <form onSubmit={onSubmit} className="bg-white rounded-[14px] p-2 flex flex-col sm:flex-row gap-2 relative z-10">
                  <div className="flex-1">
                    <input
                      type="email"
                      placeholder="you@example.com"
                      className={cn(
                        "w-full px-4 py-3.5 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 transition-all text-slate-900 font-medium",
                        emailError ? "ring-2 ring-red-500 bg-red-50" : "focus:ring-primary-500/20"
                      )}
                      value={email}
                      onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    variant="secondary"
                    size="lg"
                    className="w-full sm:w-auto px-8 py-3.5 rounded-xl shadow-lg hover:shadow-primary-500/25 whitespace-nowrap font-bold"
                  >
                    {isSubmitting ? (
                      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                        <Sparkles className="w-5 h-5" />
                      </motion.div>
                    ) : (
                      <>Launch Agent <ArrowRight className="w-4 h-4 ml-2" /></>
                    )}
                  </Button>
                </form>
              </div>
              {emailError && (
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-3 font-medium">
                  {emailError}
                </motion.p>
              )}
              <div className="flex items-center gap-6 mt-5 text-xs text-slate-400 justify-center lg:justify-start">
                <span className="flex items-center gap-1.5"><Lock className="w-3.5 h-3.5" /> No credit card</span>
                <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5" /> SOC2 compliant</span>
                <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> 2 min setup</span>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-md mx-auto lg:mx-0 bg-white border border-slate-100 rounded-2xl p-6 shadow-xl text-left"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center">
                  <MailCheck className="w-6 h-6 text-emerald-500" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold">Magic link sent</p>
                  <p className="text-base font-bold text-slate-900">{sentEmail}</p>
                </div>
              </div>
              <p className="text-sm text-slate-600 mb-4">
                Look for an email from <span className="font-semibold">noreply@jobhuntin.com</span>. Click the link to jump straight into onboarding.
              </p>
              <button type="button" onClick={() => setSentEmail(null)} className="text-sm font-semibold text-primary-600 hover:underline">
                Use a different email
              </button>
            </motion.div>
          )}
        </div>

        {/* ─ Right: Animated Product Demo ─ */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="mt-8 lg:mt-0"
        >
          <ProductFlowDemo />
        </motion.div>
      </div>

      {/* Scroll hint */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-slate-300"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <ArrowDown className="w-5 h-5" />
      </motion.div>

      {/* Seamless wave blend into white */}
      <div className="absolute bottom-0 left-0 right-0 w-full overflow-hidden leading-none">
        <svg className="relative block w-[calc(100%+1.3px)] h-[60px] sm:h-[100px]" viewBox="0 0 1200 120" preserveAspectRatio="none">
          <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z" className="fill-white" />
        </svg>
      </div>
    </section>
  );
};

// ─── Social Proof Strip ───────────────────────────────────────────────
const SocialProof = () => {
  return (
    <section className="py-16 bg-white relative overflow-hidden">
      <div className="max-w-5xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-4"
        >
          {[
            { value: 12400, suffix: "+", label: "Jobs Scanned Daily" },
            { value: 47, suffix: "s", label: "Avg. Apply Time" },
            { value: 340, suffix: "%", label: "More Interviews" },
            { value: 2, suffix: " min", label: "Setup to First Apply" },
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="text-center group"
            >
              <p className="text-3xl md:text-4xl font-black text-slate-900 tracking-tighter">
                <AnimatedNumber target={stat.value} suffix={stat.suffix} />
              </p>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

// ─── How It Works — The Protocol ──────────────────────────────────────
const HowItWorks = () => {
  const steps = [
    {
      icon: UserCircle,
      title: "We See the Real You",
      desc: "Forget keywords. We build a psychological profile of your career narrative — capturing nuance, ambition, and potential that resumes miss.",
      accent: "from-blue-500 to-blue-600",
      glow: "bg-blue-500/10",
    },
    {
      icon: Brain,
      title: "AI Reads Between the Lines",
      desc: "Our agent doesn't just match titles. It understands context — your growth trajectory, transferable skills, and the roles you'd actually thrive in.",
      accent: "from-violet-500 to-violet-600",
      glow: "bg-violet-500/10",
    },
    {
      icon: Target,
      title: "Precision Auto-Apply",
      desc: "Every application is unique. Custom cover letters, optimized form-filling, and strategic timing — all happening in seconds, not hours.",
      accent: "from-emerald-500 to-emerald-600",
      glow: "bg-emerald-500/10",
    },
    {
      icon: Bell,
      title: "You Only Show Up for Wins",
      desc: "Get notified the moment a recruiter responds. Approve next steps with one tap. We handle the grind — you handle the interview.",
      accent: "from-amber-500 to-amber-600",
      glow: "bg-amber-500/10",
    },
  ];

  return (
    <section id="how-it-works" className="py-32 bg-white relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-slate-50 rounded-full blur-3xl opacity-50 -translate-y-1/3 translate-x-1/3 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-primary-50 rounded-full blur-3xl opacity-30 translate-y-1/3 -translate-x-1/3 pointer-events-none" />

      <div className="max-w-6xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <div className="inline-block bg-primary-50 text-primary-600 px-5 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.25em] mb-6">
            The Protocol
          </div>
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black font-display text-slate-900 leading-[1.05] tracking-tighter mb-5">
            One Upload.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-emerald-500">Infinite Momentum.</span>
          </h2>
          <p className="text-lg text-slate-500 max-w-xl mx-auto font-medium">
            From resume upload to recruiter inbox in 4 autonomous steps. No babysitting required.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="group relative bg-white rounded-3xl p-8 border border-slate-100 hover:border-slate-200 hover:shadow-xl transition-all duration-500"
            >
              {/* Hover glow */}
              <div className={cn("absolute -inset-px rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl", step.glow)} />

              <div className="relative z-10">
                <div className="flex items-start gap-5 mb-5">
                  <div className={cn("w-14 h-14 rounded-2xl bg-gradient-to-br flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-500", step.accent)}>
                    <step.icon className="w-7 h-7 text-white" />
                  </div>
                  <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest mt-2">Step {String(i + 1).padStart(2, '0')}</span>
                </div>
                <h3 className="text-xl font-black text-slate-900 tracking-tight mb-3">{step.title}</h3>
                <p className="text-slate-500 leading-relaxed font-medium">{step.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// ─── Emotional Differentiator ─────────────────────────────────────────
const EmotionalSection = () => {
  return (
    <section className="py-28 bg-slate-950 relative overflow-hidden">
      {/* Grid */}
      <div className="absolute inset-0 bg-grid-premium-dark opacity-40 pointer-events-none" />

      {/* Gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-emerald-500/8 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black font-display text-white leading-[1.05] tracking-tighter mb-8">
            Applying to jobs is{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-amber-400 italic">emotionally exhausting.</span>
          </h2>
          <p className="text-xl text-white/50 max-w-2xl mx-auto leading-relaxed font-medium mb-14">
            Every rejection stings. Every hour spent tailoring a cover letter for silence hurts.
            We built JobHuntin to absorb that pain — so you only engage when a real human is ready to talk.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="grid sm:grid-cols-3 gap-6"
        >
          {[
            { icon: Cpu, metric: "47s", label: "Per Application", subtext: "vs 25 min manually" },
            { icon: BarChart3, metric: "3.4×", label: "More Interviews", subtext: "statistically" },
            { icon: Globe, metric: "24/7", label: "Always Hunting", subtext: "even while you sleep" },
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 + i * 0.1 }}
              className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/5 hover:border-white/10 transition-all group"
            >
              <item.icon className="w-6 h-6 text-primary-400 mb-4 group-hover:scale-110 transition-transform" />
              <p className="text-3xl font-black text-white tracking-tight">{item.metric}</p>
              <p className="text-sm font-bold text-white/60 uppercase tracking-wider mt-1">{item.label}</p>
              <p className="text-xs text-white/30 mt-2 font-medium">{item.subtext}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

// ─── Final CTA ────────────────────────────────────────────────────────
const FinalCTA = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError("Enter a valid email.");
      return;
    }
    setError("");
    setIsSubmitting(true);
    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");
      if (!result.success) throw new Error(result.error || "Failed");
      setSent(true);
      pushToast({ title: "Check your inbox! 📧", tone: "success" });
    } catch (err: any) {
      setError(err?.message || "Something went wrong");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="py-28 bg-slate-50 relative overflow-hidden">
      <div className="absolute inset-0 bg-grid-premium opacity-20 pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary-500/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-2xl mx-auto px-6 relative z-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl sm:text-5xl font-black font-display text-slate-900 tracking-tighter mb-5">
            Ready to let AI{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-emerald-500">do the work?</span>
          </h2>
          <p className="text-lg text-slate-500 mb-10 font-medium">
            Free to start. No credit card. Your agent begins applying in under 2 minutes.
          </p>

          {!sent ? (
            <form onSubmit={onSubmit} className="max-w-md mx-auto flex flex-col sm:flex-row gap-3">
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(""); }}
                className="flex-1 px-5 py-4 rounded-2xl bg-white border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-slate-900 font-medium shadow-sm transition-all"
              />
              <Button
                type="submit"
                disabled={isSubmitting}
                variant="secondary"
                size="lg"
                className="px-8 py-4 rounded-2xl font-bold shadow-xl hover:shadow-primary-500/30 whitespace-nowrap"
              >
                {isSubmitting ? "Sending..." : "Launch Agent"}
                <Rocket className="w-4 h-4 ml-2" />
              </Button>
            </form>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="inline-flex items-center gap-3 bg-emerald-50 text-emerald-700 px-6 py-4 rounded-2xl font-bold"
            >
              <CheckCircle className="w-5 h-5" />
              Magic link sent — check your inbox!
            </motion.div>
          )}
          {error && <p className="text-red-500 text-sm mt-3 font-medium">{error}</p>}
        </motion.div>
      </div>
    </section>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────
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
                "text": "Absolutely legit. We follow each platform's Terms of Service. We don't spam and we never submit low-quality applications."
              }
            },
            {
              "@type": "Question",
              "name": "How is this different from applying myself?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Speed and quality. Most people take 20-30 minutes per application. We do it in under 47 seconds, and we customize every resume and cover letter using AI."
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
      <main>
        <Hero />
        <SocialProof />
        <HowItWorks />
        <EmotionalSection />
        <FinalCTA />
      </main>
      <MarketingFooter />
    </div>
  );
}
