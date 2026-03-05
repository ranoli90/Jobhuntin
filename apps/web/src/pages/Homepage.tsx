import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import { telemetry } from '../lib/telemetry';
import {
  ArrowRight, MailCheck, Target, Activity,
  Upload, SlidersHorizontal, Send, Trophy,
  ChevronRight, Check, Star, Briefcase, TrendingUp, PenTool, Sparkles
} from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { TestimonialsSection } from '../components/TestimonialsSection';
import { cn } from '../lib/utils';
import { ValidationUtils } from '../lib/validation';
import { motion } from 'framer-motion';

/* ─── Email capture hook ─── */
function useEmailCapture() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);
  const validateEmail = (e: string) => ValidationUtils.validate.email(e.trim()).isValid;
  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    if (!validateEmail(email)) { setEmailError("Enter a valid email"); return; }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);
    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");
      if (!result.success) throw new Error(result.error || "Failed");
      telemetry.track("login_magic_link_requested", { source: "homepage" });
      pushToast({ title: "Check your inbox", description: "Magic link sent!", tone: "success" });
      setSentEmail(result.email);
      setEmail("");
    } catch (err: any) {
      const msg = (typeof err?.message === 'string' && !err.message.includes('[object')) ? err.message : "Something went wrong. Please try again.";
      setEmailError(msg);
      pushToast({ title: "Error", description: msg, tone: "error" });
    } finally { setIsSubmitting(false); }
  };
  return { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit };
}

/* ─── Email form ─── */
function EmailForm({ variant = "light" }: { variant?: "light" | "dark" }) {
  const { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit } = useEmailCapture();
  if (sentEmail) {
    return (
      <div className="flex items-center gap-3 p-5 rounded-2xl border border-primary-100 bg-primary-50/50 shadow-sm">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 bg-primary-100"><MailCheck className="w-6 h-6 text-primary-600" /></div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-gray-900">Check your inbox</p>
          <p className="text-xs truncate text-gray-500 mt-0.5">{sentEmail}</p>
        </div>
        <button onClick={() => setSentEmail(null)} className="text-xs shrink-0 font-medium hover:underline text-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-300 rounded">Change</button>
      </div>
    );
  }
  return (
    <div>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3">
        <input type="email" placeholder="you@example.com" aria-label="Email address"
          className={cn("flex-1 h-14 px-6 rounded-full text-base transition-all", variant === "dark" ? "bg-white/10 border-2 border-white/20 text-white placeholder:text-gray-500 focus:border-primary-400" : "bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-500 focus:border-primary-400 hover:border-gray-300 shadow-sm", emailError && "border-red-400 focus:border-red-400")}
          value={email} onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button type="submit" disabled={isSubmitting}
          className="h-12 px-6 rounded-full text-base font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap bg-primary-600 text-white hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-600/25 hover:-translate-y-0.5 active:translate-y-0 focus:ring-4 focus:ring-primary-300 focus:outline-none"
        >
          {isSubmitting ? "Sending…" : "Start free"} {!isSubmitting && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>
      {emailError && <p className="mt-2 text-xs text-red-500 pl-6">{emailError}</p>}
    </div>
  );
}

/* ─── Fade-in on scroll ─── */
function FadeIn({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const prefersReducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  useEffect(() => {
    if (prefersReducedMotion) {
      setVisible(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } }, { threshold: 0.08 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [prefersReducedMotion]);
  
  return (
    <div ref={ref} className={cn(prefersReducedMotion ? "" : "transition-all duration-700 ease-out", visible ? "opacity-100 translate-y-0" : (prefersReducedMotion ? "" : "opacity-0 translate-y-10"), className)} style={{ transitionDelay: prefersReducedMotion ? '0ms' : `${delay}ms` }}>
      {children}
    </div>
  );
}

/* ─── Live Activity Feed (sample data for demo) ─── */
function LiveActivityFeed({ compact = false }: { compact?: boolean }) {
  const [announcement, setAnnouncement] = useState("");
  const activities = [
    { role: "Senior Frontend Engineer", company: "Stripe", time: "2s ago", type: "applied" },
    { role: "Product Manager", company: "Airbnb", time: "15s ago", type: "applied" },
    { role: "Data Scientist", company: "Netflix", time: "32s ago", type: "matched" },
    { role: "UX Designer", company: "Figma", time: "1m ago", type: "applied" },
    { role: "Backend Engineer", company: "Shopify", time: "1m ago", type: "applied" },
    { role: "ML Engineer", company: "OpenAI", time: "2m ago", type: "matched" },
    { role: "DevOps Engineer", company: "Datadog", time: "2m ago", type: "applied" },
    { role: "Full Stack Developer", company: "Vercel", time: "3m ago", type: "applied" },
  ];
  const [currentIdx, setCurrentIdx] = useState(0);
  const prefersReducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  useEffect(() => {
    if (prefersReducedMotion) return;
    let interval: ReturnType<typeof setInterval> | null = null;
    const start = () => {
      interval = setInterval(() => {
        setCurrentIdx((prev) => {
          const next = (prev + 1) % activities.length;
          const item = activities[next];
          setAnnouncement(`${item.role} at ${item.company} - ${item.type}`);
          return next;
        });
      }, 3000);
    };
    const stop = () => { if (interval) clearInterval(interval); interval = null; };
    const onVisibility = () => (document.hidden ? stop() : start());
    start();
    document.addEventListener('visibilitychange', onVisibility);
    return () => { stop(); document.removeEventListener('visibilitychange', onVisibility); };
  }, [prefersReducedMotion]);
  const count = compact ? 3 : 4;
  const visibleItems = [];
  for (let i = 0; i < count; i++) visibleItems.push(activities[(currentIdx + i) % activities.length]);
  return (
    <div className="space-y-2">
      <div className="sr-only" aria-live="polite" aria-atomic="true">{announcement}</div>
      <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider mb-1">Demo activity</p>
      {visibleItems.map((item, idx) => (
        <div key={`${item.role}-${idx}-${currentIdx}`} className={cn("flex items-center gap-3 px-4 py-2.5 bg-white rounded-xl border border-gray-100 shadow-sm", prefersReducedMotion ? "" : "transition-all duration-500")} style={{ opacity: prefersReducedMotion ? 1 : 1 - idx * 0.15 }}>
          <div className={cn("w-2 h-2 rounded-full shrink-0", item.type === "applied" ? "bg-green-500" : "bg-primary-500")} />
          <div className="flex-1 min-w-0"><p className="text-sm font-medium text-gray-900 truncate">{item.role}</p><p className="text-xs text-gray-500">{item.company}</p></div>
          <span className="text-[11px] text-gray-500 shrink-0">{item.time}</span>
        </div>
      ))}
    </div>
  );
}

/* ━━━ HOMEPAGE ━━━ */
export default function Homepage() {
  return (
    <>
      {/* Skip to main content for accessibility */}
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg focus:font-medium">
        Skip to main content
      </a>
      
      <SEO
        title="JobHuntin — The Application Engine That Runs While You Sleep"
        description="Upload your resume. Our platform tailors every application and submits to hundreds of jobs daily. More interviews, zero effort."
        ogTitle="JobHuntin — The Application Engine That Runs While You Sleep"
        canonicalUrl="https://jobhuntin.com/"
        schema={{ "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "20 free applications per week. Upgrade to unlimited for $10 first month." }, "description": "Automated system that tailors and submits job applications." }}
      />

      {/* ═══════════════════════════════════════════════════════════════
          §1  HERO — centered, big headline, CTA, then visual showcase below
          ═══════════════════════════════════════════════════════════════ */}
      <section id="main-content" className="relative overflow-hidden bg-gradient-to-b from-[#FEF9F3] via-white to-white">
        {/* Subtle warm gradient background */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-gradient-to-br from-[#FCD34D]/10 to-transparent rounded-full blur-3xl" />
          <div className="absolute top-20 right-1/4 w-[500px] h-[500px] bg-gradient-to-bl from-[#2DD4BF]/8 to-transparent rounded-full blur-3xl" />
        </div>
        
        {/* Purposeful animated elements - subtle job search flow visualization */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <svg className="absolute top-1/4 left-0 w-full h-32 opacity-20" preserveAspectRatio="none">
            <motion.path
              d="M -50,60 Q 200,40 400,60 T 800,50 T 1200,60"
              stroke="#F59E0B"
              strokeWidth="1"
              fill="none"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: [0, 1, 1, 0], opacity: [0, 0.4, 0.4, 0], x: [0, 100, 200] }}
              transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            />
          </svg>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 sm:pt-28 pb-12">
          <div className="max-w-3xl mx-auto text-center">
            <FadeIn>
              <motion.h1
                className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight tracking-tight px-2 sm:px-0"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              >
                <span className="block text-[#2D2A26]">
                  Land your next job
                </span>
                <span className="block text-transparent bg-clip-text bg-gradient-to-r from-[#F59E0B] to-[#2DD4BF]">
                  without the search
                </span>
              </motion.h1>
            </FadeIn>
            <FadeIn delay={80}>
              <motion.p
                className="mt-5 sm:mt-6 text-lg text-[#6B6560] max-w-xl mx-auto leading-relaxed px-4 sm:px-0"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                Stop spending 20 hours a week applying. We find matching jobs, tailor your resume, and apply for you — all while you sleep.
              </motion.p>
            </FadeIn>
            <FadeIn delay={160}>
              <motion.div
                className="mt-6 sm:mt-8 flex flex-row gap-3 justify-center items-center px-4 sm:px-0"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Link to="/login" className="group h-11 sm:h-12 px-6 sm:px-8 rounded-xl text-sm sm:text-base font-semibold bg-[#2D2A26] text-white hover:bg-[#3D3A36] shadow-sm hover:shadow-md transition-all flex items-center justify-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    Get 20 Free
                  </Link>
                </motion.div>
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <a href="#how-it-works" className="group h-11 sm:h-12 px-6 sm:px-8 rounded-xl text-sm sm:text-base font-medium border-2 border-[#E7E5E4] text-[#57534E] hover:border-[#D6D3D1] hover:text-[#2D2A26] transition-all flex items-center justify-center gap-2">
                    <Target className="w-4 h-4" />
                    How It Works
                  </a>
                </motion.div>
              </motion.div>
              <motion.div
                className="mt-6 flex items-center justify-center gap-3"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <div className="flex -space-x-2">
                  {['SK', 'MT', 'JL', 'AR'].map((initials, i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-full border-2 border-white bg-gradient-to-br from-[#F59E0B] to-[#F87171] flex items-center justify-center text-[10px] font-semibold text-white"
                    >
                      {initials}
                    </div>
                  ))}
                </div>
                <p className="text-sm text-[#78716C]">
                  <span className="font-semibold text-[#2D2A26]">10,000+</span> hired already
                </p>
              </motion.div>
            </FadeIn>
          </div>
        </div>

        {/* ── HERO VISUAL SHOWCASE ── */}
        <FadeIn delay={300}>
          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 pb-20 mt-12 sm:mt-20 overflow-hidden">
            <div className="relative h-[360px] sm:h-[520px] lg:h-[580px] min-h-[360px]">
              {/* Card 1 — Dashboard (center-left, tilted) - Glassmorphism dark card */}
              <motion.div 
                className="absolute left-[0%] sm:left-[5%] top-[5%] sm:top-[8%] w-[58%] sm:w-[45%] transform rotate-0 sm:-rotate-2 z-20"
                initial={{ opacity: 0, x: -50, rotate: -10 }}
                animate={{ opacity: 1, x: 0, rotate: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                whileHover={{ rotate: 0, scale: 1.02 }}
              >
                <div className="bg-slate-900/80 backdrop-blur-xl rounded-xl sm:rounded-2xl p-3 sm:p-4 shadow-2xl shadow-brand-sunrise/10 border border-brand-sunrise/20">
                  {/* Window chrome */}
                  <div className="flex items-center gap-2 mb-3">
                    <div className="flex gap-1.5">
                      <motion.div 
                        className="w-3 h-3 rounded-full bg-gradient-to-br from-red-400 to-red-600"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      />
                      <motion.div 
                        className="w-3 h-3 rounded-full bg-gradient-to-br from-amber-400 to-amber-600"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                      />
                      <motion.div 
                        className="w-3 h-3 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity, delay: 1 }}
                      />
                    </div>
                    <div className="flex-1 h-5 bg-slate-700/50 rounded-lg mx-2 backdrop-blur-sm" />
                  </div>
                  {/* Dashboard stats */}
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <motion.div 
                      className="bg-gradient-to-br from-brand-sunrise/20 to-brand-sunrise/10 rounded-lg p-2 text-center border border-brand-sunrise/30"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.6 }}
                    >
                      <div className="text-lg sm:text-xl font-bold text-white">127</div>
                      <div className="text-[8px] sm:text-[9px] text-brand-sunrise/80">Applied</div>
                    </motion.div>
                    <motion.div 
                      className="bg-gradient-to-br from-brand-lagoon/20 to-brand-lagoon/10 rounded-lg p-2 text-center border border-brand-lagoon/30"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.7 }}
                    >
                      <div className="text-lg sm:text-xl font-bold text-white">23</div>
                      <div className="text-[8px] sm:text-[9px] text-brand-lagoon/80">Responses</div>
                    </motion.div>
                    <motion.div 
                      className="bg-gradient-to-br from-brand-plum/20 to-brand-plum/10 rounded-lg p-2 text-center border border-brand-plum/30"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.8 }}
                    >
                      <div className="text-lg sm:text-xl font-bold text-white">7</div>
                      <div className="text-[8px] sm:text-[9px] text-brand-plum/80">Interviews</div>
                    </motion.div>
                  </div>
                  {/* Application rows */}
                  {[
                    { name: "Stripe", status: "Interview", color: "from-brand-lagoon to-brand-plum" },
                    { name: "Airbnb", status: "Applied", color: "from-brand-sunrise to-brand-mango" },
                    { name: "Figma", status: "Viewed", color: "from-brand-plum to-brand-lagoon" },
                  ].map((app, i) => (
                    <motion.div 
                      key={i} 
                      className="flex items-center gap-2 py-2 border-t border-slate-700/50"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: 0.9 + i * 0.1 }}
                    >
                      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-slate-600 to-slate-700 shrink-0" />
                      <div className="flex-1">
                        <div className="h-2 bg-slate-600 rounded-full w-3/4" />
                        <div className="h-1.5 bg-slate-700 rounded-full w-1/2 mt-1" />
                      </div>
                      <div className={cn("px-2 py-0.5 rounded-md text-[7px] sm:text-[8px] font-semibold bg-gradient-to-r", app.color, "text-white")}>
                        {app.status}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Card 2 — Resume (center-right, tilted other way) - Glassmorphism white card */}
              <motion.div 
                className="absolute right-[0%] sm:right-[5%] top-[0%] sm:top-[2%] w-[52%] sm:w-[40%] transform rotate-0 sm:rotate-2 z-30"
                initial={{ opacity: 0, x: 50, rotate: 10 }}
                animate={{ opacity: 1, x: 0, rotate: 0 }}
                transition={{ duration: 0.8, delay: 0.5 }}
                whileHover={{ rotate: 0, scale: 1.02 }}
              >
                <div className="bg-white/80 backdrop-blur-xl rounded-xl sm:rounded-2xl p-3 sm:p-4 shadow-2xl shadow-brand-lagoon/10 border border-brand-lagoon/20">
                  <div className="flex items-center justify-between mb-3">
                    <motion.div 
                      className="text-xs font-bold text-transparent bg-clip-text bg-gradient-to-r from-brand-plum to-brand-lagoon"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: 0.6 }}
                    >
                      Resume Preview
                    </motion.div>
                    <motion.div 
                      className="px-2 py-0.5 rounded-md bg-gradient-to-r from-brand-lagoon to-brand-plum text-white text-[8px] font-bold shadow-lg shadow-brand-lagoon/25"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.5, delay: 0.7 }}
                      whileHover={{ scale: 1.05 }}
                    >
                      <TrendingUp className="w-3 h-3 inline mr-1" /> ATS 94%
                    </motion.div>
                  </div>
                  <div className="space-y-2">
                    <motion.div 
                      className="h-5 bg-gradient-to-r from-brand-plum via-brand-sunrise to-brand-lagoon rounded-lg w-2/3"
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: '66.67%' }}
                      transition={{ duration: 0.8, delay: 0.8 }}
                    />
                    <motion.div 
                      className="h-2.5 bg-gradient-to-r from-brand-sunrise/20 to-brand-mango/20 rounded-full"
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: '100%' }}
                      transition={{ duration: 0.8, delay: 0.9 }}
                    />
                    <motion.div 
                      className="h-2.5 bg-gradient-to-r from-brand-lagoon/20 to-brand-plum/20 rounded-full w-5/6"
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: '83.33%' }}
                      transition={{ duration: 0.8, delay: 1.0 }}
                    />
                    <motion.div 
                      className="h-2.5 bg-gradient-to-r from-brand-plum/20 to-brand-sunrise/20 rounded-full w-4/5"
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: '80%' }}
                      transition={{ duration: 0.8, delay: 1.1 }}
                    />
                    <div className="h-px bg-gradient-to-r from-transparent via-brand-lagoon/30 to-transparent my-3" />
                    <motion.div 
                      className="h-4 bg-gradient-to-r from-brand-mango to-brand-sunrise rounded-lg w-2/5"
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: '40%' }}
                      transition={{ duration: 0.8, delay: 1.2 }}
                    />
                    <motion.div 
                      className="h-2 bg-gradient-to-r from-brand-lagoon/10 to-brand-plum/10 rounded-full"
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: '100%' }}
                      transition={{ duration: 0.8, delay: 1.3 }}
                    />
                    <motion.div 
                      className="h-2 bg-gradient-to-r from-brand-sunrise/10 to-brand-mango/10 rounded-full"
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: '100%' }}
                      transition={{ duration: 0.8, delay: 1.4 }}
                    />
                  </div>
                  <motion.div 
                    className="mt-3 flex gap-1.5 flex-wrap"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 1.5 }}
                  >
                    {["React", "TypeScript", "Node.js"].map((skill, i) => (
                      <motion.div 
                        key={skill}
                        className="px-2 py-1 rounded-lg bg-gradient-to-r from-brand-sunrise/10 to-brand-lagoon/10 text-[7px] sm:text-[8px] font-bold text-brand-plum border border-brand-plum/20"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3, delay: 1.6 + i * 0.1 }}
                        whileHover={{ scale: 1.1, y: -2 }}
                      >
                        {skill}
                      </motion.div>
                    ))}
                  </motion.div>
                </div>
              </motion.div>

              {/* Card 3 — Live Feed (bottom center) - Glassmorphism dark card */}
              <motion.div 
                className="absolute left-[10%] sm:left-[22%] bottom-[2%] sm:bottom-[0%] w-[60%] sm:w-[42%] transform rotate-0 z-10"
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.6 }}
                whileHover={{ scale: 1.02 }}
              >
                <div className="bg-slate-900/80 backdrop-blur-xl rounded-xl sm:rounded-2xl p-3 sm:p-4 shadow-2xl shadow-brand-mango/10 border border-brand-mango/20">
                  <div className="flex items-center gap-2 mb-2">
                    <motion.div 
                      className="w-2 h-2 rounded-full bg-gradient-to-r from-brand-mango to-brand-sunrise"
                      animate={{ scale: [1, 1.5, 1], opacity: [1, 0.7, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                    <motion.span 
                      className="text-[10px] font-semibold text-transparent bg-clip-text bg-gradient-to-r from-brand-mango to-brand-sunrise"
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      Live Activity
                    </motion.span>
                  </div>
                  <LiveActivityFeed compact />
                </div>
              </motion.div>
            </div>
          </div>
        </FadeIn>
      </section>

      {/* ═══ TRUST BAR ═══ */}
      <section className="bg-white border-y border-[#E7E5E4] py-10 sm:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-sm font-medium text-[#78716C] text-center mb-6">Trusted by job seekers landing roles at</p>
          <div className="flex flex-wrap justify-center gap-x-6 sm:gap-x-10 gap-y-3">
            {['Google', 'Stripe', 'Airbnb', 'Netflix', 'Shopify', 'Figma'].map((company) => (
              <span key={company} className="text-base sm:text-lg font-semibold text-[#A8A29E]">
                {company}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §2  THREE PRODUCT CARDS
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-white py-16 sm:py-24 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <p className="text-[#F59E0B] font-semibold text-sm uppercase tracking-wide mb-3">Your secret weapon</p>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-[#2D2A26] leading-tight">
                Everything you need to land your dream role
              </h2>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-6">
            {/* ── Card 1: Precision Matching ── */}
            <FadeIn delay={0}>
              <div className="group rounded-2xl overflow-hidden bg-white shadow-lg shadow-[#2D2A26]/5 border border-[#E7E5E4] p-6 sm:p-8 pb-0 min-h-[480px] flex flex-col hover:-translate-y-1 transition-all duration-300 hover:shadow-xl cursor-pointer">
                <div className="flex-1">
                  <div className="w-12 h-12 rounded-xl bg-[#FEF3C7] flex items-center justify-center mb-5">
                    <Target className="w-6 h-6 text-[#F59E0B]" />
                  </div>
                  <h3 className="text-xl font-semibold text-[#2D2A26] mb-2">Perfect Matches, Every Time</h3>
                  <p className="text-[#6B6560] leading-relaxed text-[15px] mb-3">Our engine analyzes thousands of listings daily and only applies to the ones that fit your skills, goals, and salary requirements.</p>
                  <a href="#how-it-works" className="inline-flex items-center gap-1.5 text-[#F59E0B] hover:text-[#D97706] font-semibold text-sm group/l">
                    How it works <ChevronRight className="w-4 h-4 group-hover/l:translate-x-0.5 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-gray-50/80 backdrop-blur-sm rounded-t-2xl p-4 -mx-1 border-t border-gray-100">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Top Matches</span>
                    <span className="text-[9px] text-gray-500">3 of 47 found</span>
                  </div>
                  {[
                    { role: "Sr. Frontend Eng", co: "Stripe", match: 98, salary: "$180k–$220k" },
                    { role: "Product Manager", co: "Airbnb", match: 95, salary: "$165k–$200k" },
                    { role: "UX Designer", co: "Figma", match: 92, salary: "$140k–$175k" },
                  ].map((j, i) => (
                    <div key={i} className="flex items-center gap-3 bg-white border border-gray-100 rounded-xl p-3 mb-2 last:mb-0">
                      <div className="w-9 h-9 rounded-xl bg-primary-50 flex items-center justify-center text-[11px] font-black text-primary-700 shrink-0">{j.co.charAt(0)}</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] font-bold text-gray-900 truncate">{j.role}</p>
                        <p className="text-[9px] text-gray-500">{j.co} · {j.salary}</p>
                        <div className="mt-1.5 h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 rounded-full" style={{ width: `${j.match}%` }} />
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-[13px] font-extrabold text-green-600">{j.match}%</div>
                        <div className="text-[7px] text-gray-500 uppercase">Match</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </FadeIn>

            {/* ── Card 2: Curated Quality ── */}
            <FadeIn delay={120}>
              <div className="group rounded-2xl overflow-hidden bg-white shadow-lg shadow-[#2D2A26]/5 border border-[#E7E5E4] p-6 sm:p-8 pb-0 min-h-[480px] flex flex-col hover:-translate-y-1 transition-all duration-300 hover:shadow-xl cursor-pointer">
                <div className="flex-1">
                  <div className="w-12 h-12 rounded-xl bg-[#F0FDF4] flex items-center justify-center mb-5">
                    <PenTool className="w-6 h-6 text-[#16A34A]" />
                  </div>
                  <h3 className="text-xl font-semibold text-[#2D2A26] mb-2">Your Best Resume</h3>
                  <p className="text-[#6B6560] leading-relaxed text-[15px] mb-3">We rewrite your resume for every single job, making sure you highlight exactly what the hiring managers are looking for.</p>
                  <a href="#features" className="inline-flex items-center gap-1.5 text-[#16A34A] hover:text-[#15803D] font-semibold text-sm group/l">
                    View features <ChevronRight className="w-4 h-4 group-hover/l:translate-x-0.5 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-gray-50/80 backdrop-blur-sm rounded-t-2xl p-4 -mx-1 border-t border-gray-100">
                  {/* Mini resume document mock */}
                  <div className="bg-white border border-gray-100 rounded-xl p-3.5">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="h-3 w-24 bg-gray-300 rounded-full mb-1" />
                        <div className="h-2 w-16 bg-gray-200 rounded-full" />
                      </div>
                      <div className="px-2.5 py-1 rounded-lg bg-green-100 text-[9px] font-bold text-green-700 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" /> ATS 94%
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="h-1.5 bg-gray-200 rounded-full w-full" />
                      <div className="h-1.5 bg-gray-200 rounded-full w-[90%]" />
                      <div className="h-1.5 bg-gray-200 rounded-full w-[75%]" />
                    </div>
                    <div className="mt-2.5 pt-2.5 border-t border-gray-200">
                      <div className="h-2 w-14 bg-gray-200 rounded-full mb-1.5" />
                      <div className="space-y-1">
                        <div className="h-1.5 bg-gray-200 rounded-full w-full" />
                        <div className="h-1.5 bg-gray-200 rounded-full w-[85%]" />
                      </div>
                    </div>
                    <div className="mt-2.5 flex gap-1.5 flex-wrap">
                      {["React", "TS", "Node", "AWS"].map((s) => (
                        <span key={s} className="px-2 py-0.5 rounded bg-primary-50 text-[7px] font-bold text-primary-700">{s}</span>
                      ))}
                    </div>
                  </div>
                  {/* Quality metrics */}
                  <div className="mt-2.5 grid grid-cols-3 gap-1.5">
                    {[
                      { label: "Tone", icon: "✓", color: "bg-green-100 text-green-700" },
                      { label: "Keywords", icon: "✓", color: "bg-green-100 text-green-700" },
                      { label: "Format", icon: "✓", color: "bg-green-100 text-green-700" },
                    ].map((m) => (
                      <div key={m.label} className={cn("rounded-lg px-2 py-1.5 text-center text-[8px] font-bold", m.color)}>
                        {m.icon} {m.label}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </FadeIn>

            {/* ── Card 3: Live Tracking (Blue) ── */}
            <FadeIn delay={240}>
              <div className="group rounded-3xl overflow-hidden bg-white shadow-xl shadow-primary-900/5 border border-primary-100/50 p-7 sm:p-8 pb-0 min-h-[520px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl cursor-pointer">
                <div className="flex-1">
                  <div className="w-14 h-14 rounded-2xl bg-primary-50 border border-primary-100/50 backdrop-blur-sm flex items-center justify-center mb-6">
                    <Activity className="w-7 h-7 text-primary-600" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-3">Real-time Tracking</h3>
                  <p className="text-gray-600 leading-relaxed text-[15px] mb-2">Watch applications go out in real-time. See matches, responses, and interview invites instantly.</p>
                  <a href="#dashboard" className="inline-flex items-center gap-1.5 text-primary-600 hover:text-primary-700 font-semibold text-sm mt-2 group/l focus:outline-none focus:ring-2 focus:ring-primary-300 rounded">
                    Learn more <ChevronRight className="w-4 h-4 group-hover/l:translate-x-1 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-gray-50/80 backdrop-blur-sm rounded-t-2xl p-4 -mx-1 border-t border-gray-100">
                  {/* Mini stats row */}
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="bg-white border border-gray-100 rounded-lg p-2 text-center">
                      <div className="text-[15px] font-extrabold text-gray-900">18</div>
                      <div className="text-[7px] text-gray-500 uppercase tracking-wide">Today</div>
                    </div>
                    <div className="bg-white border border-gray-100 rounded-lg p-2 text-center">
                      <div className="text-[15px] font-extrabold text-gray-900">127</div>
                      <div className="text-[7px] text-gray-500 uppercase tracking-wide">This week</div>
                    </div>
                    <div className="bg-white border border-gray-100 rounded-lg p-2 text-center">
                      <div className="text-[15px] font-extrabold text-green-600">4</div>
                      <div className="text-[7px] text-gray-500 uppercase tracking-wide">Interviews</div>
                    </div>
                  </div>
                  {/* Activity bar chart */}
                  <div className="flex items-center gap-1.5 mb-2"><div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" /><span className="text-[8px] text-gray-500 uppercase tracking-wider font-bold">Activity This Week</span></div>
                  <div className="flex items-end gap-1 h-10 mb-1">
                    {[40, 65, 55, 80, 70, 90, 45].map((h, i) => (
                      <div key={i} className="flex-1 rounded-t bg-primary-300 hover:bg-primary-400 transition-colors cursor-pointer" style={{ height: `${h}%` }} title={`${h}% activity`} />
                    ))}
                  </div>
                  <div className="flex justify-between text-[7px] text-gray-500 font-medium">
                    {["M", "T", "W", "T", "F", "S", "S"].map((d, i) => <span key={i}>{d}</span>)}
                  </div>
                </div>
              </div>
            </FadeIn>
          </div>
        </div>
      </section >

      {/* ═══════════════════════════════════════════════════════════════
          §3  BIG TESTIMONIAL QUOTE
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-slate-50 py-20 sm:py-32 overflow-hidden">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <FadeIn>
            <div className="inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-primary-100 mb-8 sm:mb-12">
              <span className="text-2xl sm:text-3xl text-primary-600 font-serif leading-none">"</span>
            </div>
            <blockquote className="text-[clamp(1.25rem,4vw,2.5rem)] font-black text-slate-900 leading-[1.3] sm:leading-snug tracking-tight text-balance">
              That first week I literally did nothing and got 4 interview callbacks. This is the future of job hunting.
            </blockquote>
            <div className="mt-10 flex items-center justify-center gap-4">
              <div className="w-14 h-14 rounded-full bg-primary-100 flex items-center justify-center text-lg font-bold text-primary-700">SK</div>
              <div className="text-left">
                <p className="font-semibold text-gray-900 text-lg">Sarah K.</p>
                <p className="text-sm text-gray-500">Marketing Manager · Landed at HubSpot</p>
              </div>
            </div>
          </FadeIn>
        </div>
      </section >

      {/* ═══════════════════════════════════════════════════════════════
          §4  FEATURE SHOWCASE ROWS — large mockups on colored backgrounds
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-white py-20 sm:py-32 lg:py-48">
        <div className="max-w-7xl mx-auto px-6 space-y-32 sm:space-y-48">

          {/* Row 1 — Dashboard */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-16 lg:gap-24 items-center">
              <div className="relative">
                <div className="bg-gradient-to-br from-primary-100 via-primary-50 to-violet-100 rounded-[2rem] p-6 sm:p-10 lg:p-12">
                  <div className="bg-white rounded-2xl shadow-2xl shadow-primary-200/50 p-5 sm:p-6 border border-gray-100/80">
                    <div className="flex items-center gap-2 mb-5">
                      <div className="flex gap-1.5"><div className="w-3 h-3 rounded-full bg-red-400" /><div className="w-3 h-3 rounded-full bg-amber-400" /><div className="w-3 h-3 rounded-full bg-green-400" /></div>
                      <div className="flex-1 h-7 bg-gray-100 rounded-full mx-6" />
                    </div>
                    <div className="grid grid-cols-3 gap-3 mb-5">
                      <div className="bg-primary-50 rounded-xl p-3 sm:p-4 text-center"><div className="text-2xl sm:text-3xl font-extrabold text-primary-600">127</div><div className="text-[10px] sm:text-xs text-gray-500 mt-1">Applied</div></div>
                      <div className="bg-green-50 rounded-xl p-3 sm:p-4 text-center"><div className="text-2xl sm:text-3xl font-extrabold text-green-600">23</div><div className="text-[10px] sm:text-xs text-gray-500 mt-1">Responses</div></div>
                      <div className="bg-amber-50 rounded-xl p-3 sm:p-4 text-center"><div className="text-2xl sm:text-3xl font-extrabold text-amber-600">7</div><div className="text-[10px] sm:text-xs text-gray-500 mt-1">Interviews</div></div>
                    </div>
                    <div className="space-y-0">
                      {[
                        { role: "Senior Frontend Engineer", co: "Stripe", status: "Interview", color: "bg-green-100 text-green-700" },
                        { role: "Product Manager", co: "Airbnb", status: "Applied", color: "bg-primary-100 text-primary-700" },
                        { role: "Data Scientist", co: "Netflix", status: "Viewed", color: "bg-amber-100 text-amber-700" },
                        { role: "UX Designer", co: "Figma", status: "Applied", color: "bg-primary-100 text-primary-700" },
                      ].map((row, i) => (
                        <div key={i} className="flex items-center gap-3 py-3 border-t border-gray-50">
                          <div className="w-9 h-9 rounded-xl bg-gray-100 flex items-center justify-center shrink-0"><Briefcase className="w-4 h-4 text-gray-500" /></div>
                          <div className="flex-1 min-w-0"><p className="text-sm font-medium text-gray-900 truncate">{row.role}</p><p className="text-xs text-gray-500">{row.co}</p></div>
                          <div className={cn("px-2.5 py-1 rounded-full text-[10px] font-bold shrink-0", row.color)}>{row.status}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <p className="text-primary-600 font-semibold text-sm uppercase tracking-wider mb-4">Your command center</p>
                <h2 className="text-[clamp(2rem,4vw,3rem)] font-extrabold tracking-tight text-gray-900 leading-[1.1]">
                  A dashboard that keeps you in complete control
                </h2>
                <p className="mt-6 text-lg text-gray-500 leading-relaxed">
                  Track every application, see live matches, monitor responses, and review AI-crafted submissions — all in one beautiful dashboard.
                </p>
                <ul className="mt-10 space-y-5">
                  {["Real-time application tracking", "Response & interview monitoring", "AI match confidence scores", "One-click application review"].map((f) => (
                    <li key={f} className="flex items-center gap-4"><div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center shrink-0"><Check className="w-4 h-4 text-primary-600" /></div><span className="text-gray-700 font-medium text-[15px]">{f}</span></li>
                  ))}
                </ul>
                <Link to="/login" className="inline-flex items-center gap-2 mt-10 h-14 px-10 rounded-full text-lg font-bold bg-primary-600 text-white hover:bg-primary-700 hover:shadow-2xl hover:shadow-primary-600/30 hover:-translate-y-1 focus:ring-4 focus:ring-primary-300 focus:outline-none transition-all">
                  Try it free <ArrowRight className="w-5 h-5" />
                </Link>
              </div>
            </div>
          </FadeIn>

          {/* Row 2 — Resume Tailoring (reversed) */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-16 lg:gap-24 items-center">
              <div className="order-2 lg:order-1">
                <p className="text-orange-500 font-semibold text-sm uppercase tracking-wider mb-4">AI-Powered</p>
                <h2 className="text-[clamp(2rem,4vw,3rem)] font-extrabold tracking-tight text-gray-900 leading-[1.1]">
                  Applications that actually get responses
                </h2>
                <p className="mt-6 text-lg text-gray-500 leading-relaxed">
                  Every resume and cover letter is rewritten for the specific role, adjusted for the company's tone, and optimized for ATS.
                </p>
                <ul className="mt-10 space-y-5">
                  {["Custom resume for every single role", "Company-tone matched cover letters", "ATS keyword optimization built in", "Skills highlighting & gap analysis"].map((f) => (
                    <li key={f} className="flex items-center gap-4"><div className="w-7 h-7 rounded-full bg-orange-100 flex items-center justify-center shrink-0"><Check className="w-4 h-4 text-orange-500" /></div><span className="text-gray-700 font-medium text-[15px]">{f}</span></li>
                  ))}
                </ul>
              </div>
              <div className="order-1 lg:order-2">
                <div className="bg-gradient-to-br from-orange-100 via-rose-50 to-amber-100 rounded-[2rem] p-6 sm:p-10 lg:p-12">
                  <div className="bg-white rounded-2xl shadow-2xl shadow-orange-200/50 p-5 sm:p-6 border border-gray-100/80">
                    <div className="flex items-center justify-between mb-6">
                      <div className="text-sm font-bold text-gray-900">Tailored Resume</div>
                      <div className="flex gap-2">
                        <div className="px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center gap-1"><TrendingUp className="w-3 h-3" /> ATS: 94%</div>
                      </div>
                    </div>
                    <div className="space-y-3.5">
                      <div className="h-6 bg-gray-900 rounded-lg w-3/5" />
                      <div className="h-3 bg-gray-200 rounded-full w-full" />
                      <div className="h-3 bg-gray-200 rounded-full w-5/6" />
                      <div className="h-3 bg-gray-200 rounded-full w-4/5" />
                      <div className="h-px bg-gray-100 my-4" />
                      <div className="h-5 bg-gray-800 rounded-lg w-2/5" />
                      <div className="h-2.5 bg-gray-100 rounded-full w-full" />
                      <div className="h-2.5 bg-gray-100 rounded-full w-full" />
                      <div className="h-2.5 bg-gray-100 rounded-full w-3/4" />
                      <div className="h-px bg-gray-100 my-4" />
                      <div className="h-5 bg-gray-800 rounded-lg w-1/3" />
                      <div className="h-2.5 bg-gray-100 rounded-full w-full" />
                      <div className="h-2.5 bg-gray-100 rounded-full w-5/6" />
                    </div>
                    <div className="mt-5 flex gap-2 flex-wrap">
                      {["React", "TypeScript", "Node.js", "AWS", "GraphQL"].map((s) => (
                        <div key={s} className="px-3 py-1.5 rounded-lg bg-primary-50 text-primary-700 text-[10px] font-bold">{s}</div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </FadeIn>

          {/* Row 3 — 24/7 Agent */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-16 lg:gap-24 items-center">
              <div className="relative">
                <div className="bg-gradient-to-br from-sky-100 via-blue-50 to-teal-100 rounded-[2rem] p-6 sm:p-10 lg:p-12">
                  <div className="bg-white rounded-2xl shadow-2xl shadow-blue-200/50 p-5 sm:p-6 border border-gray-100/80">
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm font-bold text-gray-900">Live Activity Feed</div>
                      <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" /><span className="text-[10px] text-gray-500 font-medium">Updating live</span></div>
                    </div>
                    <LiveActivityFeed />
                    <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-3 gap-2">
                      <div className="text-center"><div className="text-lg font-bold text-gray-900">18</div><div className="text-[9px] text-gray-500">Today</div></div>
                      <div className="text-center"><div className="text-lg font-bold text-gray-900">127</div><div className="text-[9px] text-gray-500">This week</div></div>
                      <div className="text-center"><div className="text-lg font-bold text-gray-900">4</div><div className="text-[9px] text-gray-500">Interviews</div></div>
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <p className="text-blue-600 font-semibold text-sm uppercase tracking-wider mb-4">Always running</p>
                <h2 className="text-[clamp(2rem,4vw,3rem)] font-extrabold tracking-tight text-gray-900 leading-[1.1]">
                  Your agent works 24/7 — even while you sleep
                </h2>
                <p className="mt-6 text-lg text-gray-500 leading-relaxed">
                  New jobs get posted at 2am, on weekends, on holidays. Our agent monitors boards continuously and applies within minutes of a listing going live.
                </p>
                <ul className="mt-10 space-y-5">
                  {["Continuous job board monitoring", "Applies within minutes of new listings", "Smart timing for maximum visibility", "Weekend & off-hours coverage"].map((f) => (
                    <li key={f} className="flex items-center gap-4"><div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center shrink-0"><Check className="w-4 h-4 text-blue-600" /></div><span className="text-gray-700 font-medium text-[15px]">{f}</span></li>
                  ))}
                </ul>
              </div>
            </div>
          </FadeIn>
        </div>
      </section >

      {/* ═══════════════════════════════════════════════════════════════
          §5  HOW IT WORKS — colorful step cards
          ═══════════════════════════════════════════════════════════════ */}
      <section id="how-it-works" className="bg-slate-50 py-20 sm:py-32 lg:py-40">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-16 sm:mb-24">
              <p className="text-primary-600 font-black text-xs sm:text-sm uppercase tracking-[0.2em] mb-4">The process</p>
              <h2 className="text-[clamp(2.25rem,5vw,4rem)] font-black tracking-tight text-slate-900 leading-[1.1] text-balance">
                Set up in 2 minutes.<br className="hidden sm:block" /> Then relax.
              </h2>
            </div>
          </FadeIn>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Step 1 — Upload Resume */}
            <FadeIn delay={0}>
              <div className="relative rounded-3xl overflow-hidden bg-white border border-slate-200 p-7 text-slate-900 shadow-xl shadow-slate-200/50 min-h-[340px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl cursor-pointer focus-within:ring-2 focus-within:ring-primary-300">
                <div className="hidden sm:block absolute top-3 right-3 w-24 h-24 bg-slate-50 border border-slate-100 rounded-2xl rotate-12" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-2xl bg-primary-50 border border-primary-100 flex items-center justify-center mb-5">
                    <Upload className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-primary-600 mb-2">Step 1</div>
                  <h3 className="text-xl font-bold mb-3">Upload</h3>
                  <p className="text-slate-600 text-[13px] leading-relaxed mb-5">Just drop your resume. We'll read everything and figure out what you're good at.</p>
                </div>
                <div className="mt-auto relative bg-slate-50 rounded-xl p-3 border border-slate-100">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-white border border-slate-100 shadow-sm flex items-center justify-center shrink-0">
                      <Upload className="w-5 h-5 text-primary-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="h-2 bg-slate-200 rounded-full w-2/3 mb-1.5" />
                      <div className="h-1.5 bg-slate-100 rounded-full w-1/2" />
                    </div>
                    <div className="px-2 py-1 rounded-lg bg-green-50 text-[10px] font-bold text-green-600">Done ✓</div>
                  </div>
                </div>
              </div>
            </FadeIn>

            {/* Step 2 — Set Filters */}
            <FadeIn delay={100}>
              <div className="relative rounded-3xl overflow-hidden bg-white border border-slate-200 p-7 text-slate-900 shadow-xl shadow-slate-200/50 min-h-[340px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl cursor-pointer focus-within:ring-2 focus-within:ring-primary-300">
                <div className="hidden sm:block absolute top-4 right-4 w-20 h-20 bg-slate-50 border border-slate-100 rounded-full" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-2xl bg-primary-50 border border-primary-100 flex items-center justify-center mb-5">
                    <SlidersHorizontal className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-primary-600 mb-2">Step 2</div>
                  <h3 className="text-xl font-bold mb-3">Choose jobs</h3>
                  <p className="text-slate-600 text-[13px] leading-relaxed mb-5">Tell us what you want: salary, location, and role. We ONLY apply to what you actually want.</p>
                </div>
                <div className="mt-auto relative space-y-2">
                  {[
                    { label: "Role", value: "Designer" },
                    { label: "Salary", value: "$150k+" },
                    { label: "Remote", value: "Yes" },
                  ].map((f) => (
                    <div key={f.label} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2 border border-slate-100">
                      <span className="text-[10px] text-slate-400 font-bold uppercase">{f.label}</span>
                      <span className="text-[10px] text-primary-600 font-bold">{f.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </FadeIn>

            {/* Step 3 — AI Applies */}
            <FadeIn delay={200}>
              <div className="relative rounded-3xl overflow-hidden bg-white border border-slate-200 p-7 text-slate-900 shadow-xl shadow-slate-200/50 min-h-[340px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl cursor-pointer focus-within:ring-2 focus-within:ring-primary-300">
                <div className="hidden sm:block absolute top-3 right-3 w-28 h-16 bg-slate-50 rounded-xl rotate-6" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-2xl bg-primary-50 border border-primary-100 flex items-center justify-center mb-5">
                    <Send className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-primary-600 mb-2">Step 3</div>
                  <h3 className="text-xl font-bold mb-3">Sit back</h3>
                  <p className="text-slate-600 text-[13px] leading-relaxed mb-5">We tailor your resume for every job and submit it within minutes of them being posted.</p>
                </div>
                <div className="mt-auto relative bg-slate-50 rounded-xl p-3 border border-slate-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-[10px] text-green-600 font-bold uppercase tracking-tight">Applying now…</span>
                  </div>
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-primary-500 rounded-full w-[72%] transition-all" />
                  </div>
                  <div className="flex justify-between mt-2">
                    <span className="text-[10px] font-bold text-slate-400">18 sent today</span>
                    <span className="text-[10px] text-primary-600 font-black">72%</span>
                  </div>
                </div>
              </div>
            </FadeIn>

            {/* Step 4 — Get Interviews */}
            <FadeIn delay={300}>
              <div className="relative rounded-3xl overflow-hidden bg-white border border-slate-200 p-7 text-slate-900 shadow-xl shadow-slate-200/50 min-h-[340px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl cursor-pointer focus-within:ring-2 focus-within:ring-primary-300">
                <div className="hidden sm:block absolute top-3 right-3 w-20 h-20 bg-slate-50 border border-slate-100 rounded-2xl rotate-12" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-2xl bg-primary-50 border border-primary-100 flex items-center justify-center mb-5">
                    <Trophy className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-primary-600 mb-2">Step 4</div>
                  <h3 className="text-xl font-bold mb-3">Get hired</h3>
                  <p className="text-slate-600 text-[13px] leading-relaxed mb-5">Check your inbox for interview requests. We give you the data to crush the interview.</p>
                </div>
                <div className="mt-auto relative grid grid-cols-3 gap-2">
                  <div className="bg-slate-50 rounded-xl p-2.5 text-center border border-slate-100">
                    <div className="text-lg font-black text-slate-900">7</div>
                    <div className="text-[7px] text-slate-400 uppercase font-black tracking-widest">Interviews</div>
                  </div>
                  <div className="bg-slate-50 rounded-xl p-2.5 text-center border border-slate-100">
                    <div className="text-lg font-black text-slate-900">3</div>
                    <div className="text-[7px] text-slate-400 uppercase font-black tracking-widest">Offers</div>
                  </div>
                  <div className="bg-primary-600 rounded-xl p-2.5 text-center shadow-lg shadow-primary-600/20">
                    <div className="text-lg font-black text-white">1</div>
                    <div className="text-[7px] text-primary-100 uppercase font-black tracking-widest">Hired</div>
                  </div>
                </div>
              </div>
            </FadeIn>
          </div>

          <FadeIn delay={400}>
            <div className="text-center mt-16">
              <Link to="/login" className="inline-flex items-center gap-2 h-14 px-10 rounded-full text-base font-semibold bg-primary-600 text-white hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-600/25 hover:-translate-y-0.5 focus:ring-4 focus:ring-primary-300 focus:outline-none transition-all">
                Start Free <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="mt-4 text-sm text-gray-500">20 applications per week. No credit card required.</p>
            </div>
          </FadeIn>
        </div>
      </section >

      {/* ═══════════════════════════════════════════════════════════════
          §6  TESTIMONIALS GRID
          ═══════════════════════════════════════════════════════════════ */}
      {/* ═══════════════════════════════════════════════════════════════
          §6  GLOBAL SUCCESS FEED — high-energy social proof
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-slate-900 py-24 sm:py-36 overflow-hidden relative">
        {/* Background glow effects */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-600/20 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="grid lg:grid-cols-2 gap-16 lg:gap-24 items-center">
            <div>
              <FadeIn>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-xs font-bold uppercase tracking-widest mb-6">
                  <Activity className="w-3.5 h-3.5" /> Live success engine
                </div>
                <h2 className="text-[clamp(2.5rem,6vw,4.5rem)] font-black tracking-tight text-white leading-[1.05] text-balance mb-8">
                  We don't just apply. <br />
                  <span className="text-primary-400">We win.</span>
                </h2>
                <p className="text-lg sm:text-xl text-slate-400 max-w-lg leading-relaxed mb-12">
                  While other platforms send generic spam, JobHuntin sends high-fidelity, tailored applications that actually get callbacks.
                </p>
                <div className="grid grid-cols-2 gap-8">
                  <div>
                    <div className="text-4xl sm:text-5xl font-black text-white mb-2 flex items-baseline gap-1">
                      <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-purple-400">500K+</span>
                      <span className="text-lg text-slate-500 font-medium">+</span>
                    </div>
                    <div className="text-xs sm:text-sm font-bold text-slate-500 uppercase tracking-widest">Applications Sent</div>
                  </div>
                  <div>
                    <div className="text-4xl sm:text-5xl font-black text-primary-400 mb-2">3.2x</div>
                    <div className="text-xs sm:text-sm font-bold text-slate-500 uppercase tracking-widest">More Interviews</div>
                  </div>
                </div>
                <div className="mt-8 pt-8 border-t border-white/10">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Trusted by job seekers at</span>
                    <div className="flex gap-4 text-slate-500 font-medium">
                      <span>Google</span>
                      <span>Meta</span>
                      <span>Stripe</span>
                      <span>+50 more</span>
                    </div>
                  </div>
                </div>
              </FadeIn>
            </div>

            <div className="relative h-[500px] sm:h-[600px] flex items-center justify-center">
              <div className="absolute inset-0 bg-slate-800/50 rounded-[2.5rem] border border-white/5 backdrop-blur-sm overflow-hidden p-6 sm:p-8">
                <div className="space-y-4 animate-scroll-v">
                  {[
                    { n: "Sarah K.", c: "Stripe", r: "Software Engineer", t: "2m ago" },
                    { n: "Marcus T.", c: "Google", r: "Product Manager", t: "5m ago" },
                    { n: "James L.", c: "Airbnb", r: "UX Designer", t: "12m ago" },
                    { n: "Priya R.", c: "Meta", r: "Data Scientist", t: "15m ago" },
                    { n: "Elena M.", c: "Figma", r: "Product Lead", t: "22m ago" },
                    { n: "David C.", c: "Shopify", r: "Backend Dev", t: "28m ago" },
                    { n: "Chris B.", c: "Netflix", r: "SRE", t: "35m ago" },
                    { n: "Alex J.", c: "Vercel", r: "Front End", t: "42m ago" },
                  ].map((win, i) => (
                    <div key={`win-${i}`} className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-pointer">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
                        {win.n.split(' ').map(x => x[0]).join('')}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-white truncate">{win.n} <span className="text-slate-500 font-normal">landed at</span> {win.c}</p>
                        <p className="text-[11px] text-slate-400 font-medium">{win.r}</p>
                      </div>
                      <div className="px-2 py-1 rounded-lg bg-green-500/20 text-[10px] font-black text-green-400 shrink-0">
                        SUCCESS ✓
                      </div>
                    </div>
                  ))}
                </div>
                {/* Fade overlays */}
                <div className="absolute top-0 left-0 right-0 h-24 bg-gradient-to-b from-slate-800/50 to-transparent pointer-events-none" />
                <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none" />
              </div>

              {/* Floating badges - hidden on mobile */}
              <div className="hidden sm:flex absolute -top-6 -right-6 w-32 h-32 bg-primary-600 rounded-3xl rotate-12 flex flex-col items-center justify-center p-4 shadow-2xl shadow-primary-600/40 z-20">
                <Trophy className="w-8 h-8 text-white mb-2" />
                <div className="text-[10px] font-black text-primary-100 uppercase tracking-widest text-center leading-tight">Match Rate 98.4%</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §7  FEATURES GRID
          ═══════════════════════════════════════════════════════════════ */}
      <section id="features" className="bg-slate-50 py-20 sm:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-3xl mx-auto mb-12 sm:mb-20">
              <p className="text-primary-600 font-black text-xs sm:text-sm uppercase tracking-[0.2em] mb-4">Full feature set</p>
              <h2 className="text-[clamp(2.25rem,5vw,3.5rem)] font-black tracking-tight text-slate-900 leading-[1.1] text-balance">
                Everything you need to<br className="hidden sm:block" /> automate your hunt
              </h2>
            </div>
          </FadeIn>
          <FadeIn delay={100}>
            <div className="text-center max-w-xl mx-auto mb-16 px-4">
              <p className="text-slate-600 italic text-base leading-relaxed">"Instead of worrying about 20 different tools… I just run my career searches from JobHuntin."</p>
              <p className="mt-4 text-sm text-slate-400 font-bold uppercase tracking-wider">– Sarah K., Marketing Manager</p>
            </div>
          </FadeIn>
          <FadeIn delay={200}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              {[
                { name: "Smart resume analysis", link: "#features" },
                { name: "Custom cover letters", link: "#features" },
                { name: "ATS optimization", link: "#features" },
                { name: "Thousands of positions", link: "#how-it-works" },
                { name: "Real-time tracking", link: "#dashboard" },
                { name: "Interview prep insights", link: "#features" },
                { name: "Personalized applications", link: "#features" },
                { name: "Salary filtering", link: "#how-it-works" },
                { name: "Company size filters", link: "#how-it-works" },
                { name: "Location preferences", link: "#how-it-works" },
                { name: "Role matching engine", link: "#features" },
                { name: "Auto-apply engine", link: "#how-it-works" },
                { name: "Application dashboard", link: "#dashboard" },
                { name: "Response tracking", link: "#dashboard" },
                { name: "Resume versioning", link: "#features" },
                { name: "Email notifications", link: "#features" },
                { name: "Mobile dashboard", link: "#features" },
                { name: "Data encryption", link: "/privacy" },
                { name: "Bulk applications", link: "#how-it-works" },
                { name: "Smart scheduling", link: "#features" },
                { name: "Company research", link: "#features" },
                { name: "Skills gap analysis", link: "#features" },
                { name: "Application analytics", link: "#dashboard" },
                { name: "Priority support", link: "#cta" },
              ].map((feature) => (
                <a 
                  key={feature.name} 
                  href={feature.link}
                  className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-white border border-slate-100 hover:border-primary-200 hover:shadow-xl hover:shadow-primary-600/5 transition-all group cursor-pointer focus-within:ring-2 focus-within:ring-primary-200"
                >
                  <div className="w-6 h-6 rounded-full bg-primary-50 flex items-center justify-center shrink-0 group-hover:bg-primary-600 transition-colors"><Check className="w-3.5 h-3.5 text-primary-600 group-hover:text-white transition-colors" /></div>
                  <span className="text-sm font-bold text-slate-700 group-hover:text-slate-900 transition-colors">{feature.name}</span>
                </a>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §8  TESTIMONIALS
          ═══════════════════════════════════════════════════════════════ */}
      <TestimonialsSection />

      {/* ═══════════════════════════════════════════════════════════════
          §9  FINAL CTA
          ═══════════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden bg-white py-24 sm:py-32 lg:py-48">
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-[10%] left-[3%] w-[220px] h-[170px] bg-slate-100 rounded-3xl rotate-12 opacity-[0.6]" />
          <div className="absolute bottom-[8%] right-[3%] w-[260px] h-[200px] bg-slate-100 rounded-3xl -rotate-6 opacity-[0.6]" />
          <div className="absolute top-[35%] right-[12%] w-[180px] h-[140px] bg-primary-50 rounded-2xl rotate-6 opacity-[0.5]" />
          <div className="absolute bottom-[30%] left-[10%] w-[200px] h-[160px] bg-primary-50 rounded-2xl -rotate-12 opacity-[0.5]" />
        </div>
        <div className="relative max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-[clamp(2.5rem,6vw,4.5rem)] font-black tracking-tight text-slate-900 leading-[1.05] text-balance mb-8">
                Automation is the secret <br className="hidden sm:block" />
                of the modern job hunt
              </h2>
              <p className="text-lg sm:text-xl text-slate-600 max-w-lg mx-auto leading-relaxed mb-12">
                Stop applying manually. Join thousands who've reclaimed their time and landed dream roles.
              </p>
              <div className="max-w-[520px] mx-auto px-4 sm:px-0">
                <EmailForm variant="light" />
              </div>
              <div className="mt-10 flex flex-wrap items-center justify-center gap-x-10 gap-y-4 text-xs sm:text-sm font-bold uppercase tracking-widest text-slate-400">
                {["Free plan", "No credit card", "Cancel anytime"].map((t) => (
                  <span key={t} className="flex items-center gap-2.5"><Check className="w-5 h-5 text-primary-600" /> {t}</span>
                ))}
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

    </>
  );
}
