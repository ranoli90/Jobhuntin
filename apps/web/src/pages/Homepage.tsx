import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import { telemetry } from '../lib/telemetry';
import {
  ArrowRight, MailCheck, Upload, SlidersHorizontal, Send,
  Check, Briefcase, TrendingUp, Zap, Shield, Clock, BarChart3,
  FileText, Users, Sparkles, Globe
} from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { TestimonialsSection } from '../components/TestimonialsSection';
import { cn } from '../lib/utils';
import { ValidationUtils } from '../lib/validation';

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
      <div className="flex items-center gap-3 p-5 rounded-2xl border border-amber-200 bg-amber-50/60">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 bg-amber-100"><MailCheck className="w-6 h-6 text-amber-700" /></div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-stone-900">Check your inbox</p>
          <p className="text-xs truncate text-stone-500 mt-0.5">{sentEmail}</p>
        </div>
        <button onClick={() => setSentEmail(null)} className="text-xs shrink-0 font-medium hover:underline text-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-300 rounded">Change</button>
      </div>
    );
  }
  const isDark = variant === "dark";
  return (
    <div>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3">
        <input type="email" placeholder="you@example.com" aria-label="Email address"
          className={cn(
            "flex-1 h-14 px-6 rounded-xl text-base transition-all outline-none",
            isDark
              ? "bg-white/10 border border-white/20 text-white placeholder:text-stone-400 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/20"
              : "bg-white border border-stone-200 text-stone-900 placeholder:text-stone-400 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-sm",
            emailError && "border-red-400 focus:border-red-400 focus:ring-red-400/20"
          )}
          value={email} onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button type="submit" disabled={isSubmitting}
          className={cn(
            "h-14 px-8 rounded-xl text-base font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap",
            isDark
              ? "bg-amber-500 text-stone-900 hover:bg-amber-400 focus:ring-2 focus:ring-amber-400/40 focus:outline-none"
              : "bg-stone-900 text-white hover:bg-stone-800 shadow-lg shadow-stone-900/10 hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 focus:ring-2 focus:ring-stone-900/30 focus:outline-none"
          )}
        >
          {isSubmitting ? "Sending…" : "Get started free"} {!isSubmitting && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>
      {emailError && <p className="mt-2 text-xs text-red-500 pl-1">{emailError}</p>}
    </div>
  );
}

/* ─── Fade-in on scroll ─── */
function FadeIn({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const prefersReducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => {
    if (prefersReducedMotion) { setVisible(true); return; }
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } }, { threshold: 0.08 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [prefersReducedMotion]);

  return (
    <div ref={ref} className={cn(prefersReducedMotion ? "" : "transition-all duration-700 ease-out", visible ? "opacity-100 translate-y-0" : (prefersReducedMotion ? "" : "opacity-0 translate-y-8"), className)} style={{ transitionDelay: prefersReducedMotion ? '0ms' : `${delay}ms` }}>
      {children}
    </div>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   HOMEPAGE — Warm, editorial, Notion-inspired design
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function Homepage() {
  const [stickyVisible, setStickyVisible] = useState(false);
  const [footerInView, setFooterInView] = useState(false);
  const footerSentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = () => setStickyVisible(!footerInView && window.scrollY > 600);
    h();
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, [footerInView]);

  useEffect(() => {
    const sentinel = footerSentinelRef.current;
    if (!sentinel) return;
    const io = new IntersectionObserver(
      ([e]) => setFooterInView(e.isIntersecting),
      { rootMargin: '-100px 0px 0px 0px', threshold: 0 }
    );
    io.observe(sentinel);
    return () => io.disconnect();
  }, []);

  return (
    <>
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-stone-900 focus:text-white focus:rounded-lg focus:font-medium">
        Skip to main content
      </a>

      <SEO
        title="JobHuntin — The Application Engine That Runs While You Sleep"
        description="Upload your resume. Our platform tailors every application and submits to hundreds of jobs daily. More interviews, zero effort."
        ogTitle="JobHuntin — The Application Engine That Runs While You Sleep"
        canonicalUrl="https://jobhuntin.com/"
        schema={{ "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "20 free applications per week. Upgrade to unlimited for $10 first month." }, "description": "Automated system that tailors and submits job applications." }}
      />

      {/* ════════════════════════════════════════════════════
          §1  HERO — editorial serif headline, warm & inviting
          ════════════════════════════════════════════════════ */}
      <section id="main-content" className="relative bg-[#FAFAF9] overflow-hidden">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-bl from-amber-100/40 to-transparent rounded-full blur-3xl -translate-y-1/3 translate-x-1/4 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-tr from-orange-50/50 to-transparent rounded-full blur-3xl translate-y-1/3 -translate-x-1/4 pointer-events-none" />

        <div className="relative max-w-6xl mx-auto px-6 pt-32 sm:pt-40 pb-20 sm:pb-28">
          <div className="max-w-4xl mx-auto text-center">
            <FadeIn>
              <p className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-50 border border-amber-200/60 text-amber-800 text-sm font-medium mb-8">
                <Sparkles className="w-4 h-4" /> Now with AI-powered resume tailoring
              </p>
            </FadeIn>
            <FadeIn delay={60}>
              <h1 className="font-display text-[clamp(2.75rem,7vw,5.5rem)] leading-[1.05] tracking-tight text-stone-900">
                Your next job,{' '}
                <span className="italic text-stone-900">found and applied&nbsp;to</span>
                <br className="hidden sm:block" />
                <span className="text-stone-400"> — while you sleep</span>
              </h1>
            </FadeIn>
            <FadeIn delay={120}>
              <p className="mt-8 text-lg sm:text-xl text-stone-500 max-w-2xl mx-auto leading-relaxed font-normal">
                Upload your resume once. JobHuntin matches you with the right roles, tailors every application, and submits — automatically, every single day.
              </p>
            </FadeIn>
            <FadeIn delay={180}>
              <div className="mt-10 flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-center">
                <Link to="/login" className="h-14 px-10 rounded-xl text-base font-semibold bg-stone-900 text-white hover:bg-stone-800 shadow-lg shadow-stone-900/10 hover:shadow-xl hover:-translate-y-0.5 focus:ring-2 focus:ring-stone-900/30 focus:outline-none transition-all flex items-center justify-center gap-2 w-full sm:w-auto">
                  Start free — 20 applications <ArrowRight className="w-4 h-4" />
                </Link>
                <a href="#how-it-works" className="h-14 px-10 rounded-xl text-base font-medium border border-stone-200 text-stone-600 hover:border-stone-300 hover:bg-white focus:ring-2 focus:ring-stone-200 focus:outline-none transition-all flex items-center justify-center gap-2 w-full sm:w-auto">
                  See how it works
                </a>
              </div>
              <p className="mt-6 text-sm text-stone-400">No credit card required · Cancel anytime</p>
            </FadeIn>
          </div>
        </div>

        {/* Hero product visual */}
        <FadeIn delay={300}>
          <div className="relative max-w-5xl mx-auto px-6 pb-16 sm:pb-24">
            <div className="bg-white rounded-2xl shadow-[0_8px_60px_-12px_rgba(0,0,0,0.08)] border border-stone-200/60 overflow-hidden">
              {/* Browser chrome */}
              <div className="flex items-center gap-2 px-5 py-3.5 bg-stone-50 border-b border-stone-100">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-stone-200" />
                  <div className="w-3 h-3 rounded-full bg-stone-200" />
                  <div className="w-3 h-3 rounded-full bg-stone-200" />
                </div>
                <div className="flex-1 h-7 bg-white rounded-lg border border-stone-200 mx-12 max-w-md flex items-center px-3">
                  <span className="text-[11px] text-stone-400">app.jobhuntin.com/dashboard</span>
                </div>
              </div>
              {/* Dashboard mock */}
              <div className="p-5 sm:p-8">
                <div className="grid grid-cols-3 gap-4 mb-6">
                  {[
                    { label: "Applied this week", value: "127", color: "text-stone-900" },
                    { label: "Responses", value: "23", color: "text-emerald-600" },
                    { label: "Interviews", value: "7", color: "text-amber-600" },
                  ].map((stat) => (
                    <div key={stat.label} className="bg-stone-50 rounded-xl p-4 sm:p-5">
                      <div className={cn("text-2xl sm:text-3xl font-bold", stat.color)}>{stat.value}</div>
                      <div className="text-xs sm:text-sm text-stone-400 mt-1">{stat.label}</div>
                    </div>
                  ))}
                </div>
                <div className="space-y-0">
                  {[
                    { role: "Senior Frontend Engineer", co: "Stripe", status: "Interview", statusColor: "bg-emerald-50 text-emerald-700", time: "2h ago" },
                    { role: "Product Manager", co: "Airbnb", status: "Applied", statusColor: "bg-stone-100 text-stone-600", time: "4h ago" },
                    { role: "Data Scientist", co: "Netflix", status: "Viewed", statusColor: "bg-amber-50 text-amber-700", time: "6h ago" },
                    { role: "UX Designer", co: "Figma", status: "Applied", statusColor: "bg-stone-100 text-stone-600", time: "8h ago" },
                  ].map((row, i) => (
                    <div key={i} className="flex items-center gap-4 py-3.5 border-t border-stone-100 first:border-t-0">
                      <div className="w-10 h-10 rounded-xl bg-stone-100 flex items-center justify-center shrink-0">
                        <Briefcase className="w-4 h-4 text-stone-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-stone-900 truncate">{row.role}</p>
                        <p className="text-xs text-stone-400">{row.co}</p>
                      </div>
                      <span className="text-xs text-stone-400 hidden sm:block">{row.time}</span>
                      <div className={cn("px-3 py-1 rounded-lg text-xs font-medium shrink-0", row.statusColor)}>{row.status}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </FadeIn>
      </section>

      {/* ════════════════════════════════════════════════════
          §2  TRUST BAR — clean company names
          ════════════════════════════════════════════════════ */}
      <section className="bg-white border-y border-stone-100 py-10 sm:py-12">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-center text-xs font-medium text-stone-400 uppercase tracking-widest mb-8">People hired at leading companies</p>
          <div className="flex flex-wrap items-center justify-center gap-x-10 sm:gap-x-16 gap-y-4">
            {["Google", "Amazon", "Stripe", "Airbnb", "Shopify", "Netflix", "Meta", "Figma"].map((name) => (
              <span key={name} className="text-stone-300 font-bold text-base sm:text-lg tracking-tight hover:text-stone-500 transition-colors cursor-default">{name}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════
          §3  BENTO FEATURE GRID — asymmetric, warm cards
          ════════════════════════════════════════════════════ */}
      <section className="bg-white py-20 sm:py-32">
        <div className="max-w-6xl mx-auto px-6">
          <FadeIn>
            <div className="max-w-2xl mb-16 sm:mb-20">
              <p className="text-amber-700 font-semibold text-sm mb-3">The platform</p>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-stone-900 leading-[1.1]">
                Everything you need to land your next role
              </h2>
              <p className="mt-5 text-lg text-stone-500 leading-relaxed">Three powerful systems working together, so you can focus on what matters — preparing for interviews.</p>
            </div>
          </FadeIn>

          {/* Bento grid - 2 columns with varied heights */}
          <div className="grid md:grid-cols-2 gap-5">
            {/* Large card — AI Matching */}
            <FadeIn delay={0}>
              <div className="bg-[#FAF8F5] rounded-2xl p-7 sm:p-9 border border-stone-100 h-full flex flex-col">
                <div className="w-11 h-11 rounded-xl bg-amber-100 flex items-center justify-center mb-5">
                  <Zap className="w-5 h-5 text-amber-700" />
                </div>
                <h3 className="text-xl sm:text-2xl font-bold text-stone-900 mb-2">Precision job matching</h3>
                <p className="text-stone-500 leading-relaxed mb-6">We scan thousands of listings daily and surface only the roles that match your skills, salary, and preferences.</p>
                {/* Mini match preview */}
                <div className="mt-auto bg-white rounded-xl border border-stone-100 divide-y divide-stone-50 overflow-hidden">
                  {[
                    { role: "Sr. Frontend Eng", co: "Stripe", match: 98 },
                    { role: "Product Manager", co: "Airbnb", match: 95 },
                    { role: "UX Designer", co: "Figma", match: 92 },
                  ].map((j) => (
                    <div key={j.role} className="flex items-center gap-3 px-4 py-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-stone-800 truncate">{j.role}</p>
                        <p className="text-xs text-stone-400">{j.co}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-stone-100 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${j.match}%` }} />
                        </div>
                        <span className="text-xs font-semibold text-emerald-600 w-8 text-right">{j.match}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </FadeIn>

            {/* Right column - two stacked cards */}
            <div className="flex flex-col gap-5">
              {/* Resume tailoring */}
              <FadeIn delay={100}>
                <div className="bg-[#F5F5F0] rounded-2xl p-7 sm:p-9 border border-stone-100">
                  <div className="w-11 h-11 rounded-xl bg-stone-200 flex items-center justify-center mb-5">
                    <FileText className="w-5 h-5 text-stone-600" />
                  </div>
                  <h3 className="text-xl font-bold text-stone-900 mb-2">Resume tailoring</h3>
                  <p className="text-stone-500 leading-relaxed mb-5">Every application gets a custom resume, rewritten to match the job description and optimized for ATS systems.</p>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-medium">
                      <TrendingUp className="w-3.5 h-3.5" /> ATS Score: 94%
                    </div>
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 text-amber-700 text-xs font-medium">
                      <Check className="w-3.5 h-3.5" /> Keyword optimized
                    </div>
                  </div>
                </div>
              </FadeIn>

              {/* 24/7 Auto-apply */}
              <FadeIn delay={200}>
                <div className="bg-stone-900 rounded-2xl p-7 sm:p-9 text-white">
                  <div className="w-11 h-11 rounded-xl bg-white/10 flex items-center justify-center mb-5">
                    <Clock className="w-5 h-5 text-amber-400" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">Runs 24/7, even while you sleep</h3>
                  <p className="text-stone-400 leading-relaxed mb-5">New jobs posted at 2am? On weekends? We apply within minutes, so you never miss an opportunity.</p>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="text-stone-400">18 applied today</span>
                    </div>
                    <span className="text-stone-600">·</span>
                    <span className="text-stone-400">127 this week</span>
                  </div>
                </div>
              </FadeIn>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════
          §4  HOW IT WORKS — clean numbered steps
          ════════════════════════════════════════════════════ */}
      <section id="how-it-works" className="bg-[#FAFAF9] py-20 sm:py-32 border-y border-stone-100">
        <div className="max-w-6xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-16 sm:mb-20">
              <p className="text-amber-700 font-semibold text-sm mb-3">How it works</p>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-stone-900 leading-[1.1]">
                Set up in 2 minutes, then relax
              </h2>
            </div>
          </FadeIn>

          <div className="grid sm:grid-cols-3 gap-8 sm:gap-12 relative">
            {/* Connector line (desktop) */}
            <div className="hidden sm:block absolute top-12 left-[calc(16.67%+24px)] right-[calc(16.67%+24px)] h-px bg-stone-200" />

            {[
              {
                step: "01",
                icon: Upload,
                title: "Upload your resume",
                desc: "Drop your resume. We parse your skills, experience, and preferences automatically."
              },
              {
                step: "02",
                icon: SlidersHorizontal,
                title: "Set your preferences",
                desc: "Tell us your target roles, salary range, location, and company preferences."
              },
              {
                step: "03",
                icon: Send,
                title: "We handle the rest",
                desc: "Sit back. We tailor, apply, and track responses — you just show up to interviews."
              },
            ].map((item, i) => (
              <FadeIn key={item.step} delay={i * 100}>
                <div className="text-center relative">
                  <div className="w-14 h-14 rounded-2xl bg-white border border-stone-200 shadow-sm flex items-center justify-center mx-auto mb-6 relative z-10">
                    <item.icon className="w-6 h-6 text-stone-600" />
                  </div>
                  <span className="font-display text-4xl text-stone-200 font-normal italic block mb-3">{item.step}</span>
                  <h3 className="text-lg font-bold text-stone-900 mb-2">{item.title}</h3>
                  <p className="text-stone-500 text-[15px] leading-relaxed max-w-xs mx-auto">{item.desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>

          <FadeIn delay={400}>
            <div className="text-center mt-16">
              <Link to="/login" className="inline-flex items-center gap-2 h-14 px-10 rounded-xl text-base font-semibold bg-stone-900 text-white hover:bg-stone-800 shadow-lg shadow-stone-900/10 hover:shadow-xl hover:-translate-y-0.5 focus:ring-2 focus:ring-stone-900/30 focus:outline-none transition-all">
                Get started free <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="mt-4 text-sm text-stone-400">20 applications per week. No credit card required.</p>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════
          §5  PULL QUOTE — warm editorial moment
          ════════════════════════════════════════════════════ */}
      <section className="bg-white py-20 sm:py-28 overflow-hidden">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <FadeIn>
            <div className="font-display text-6xl sm:text-7xl text-stone-200 italic leading-none mb-6">"</div>
            <blockquote className="text-2xl sm:text-3xl lg:text-4xl font-medium text-stone-800 leading-snug tracking-tight max-w-3xl mx-auto">
              That first week I literally did nothing and got 4 interview callbacks. This changed how I think about job hunting.
            </blockquote>
            <div className="mt-10 flex items-center justify-center gap-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-sm font-bold text-white">SK</div>
              <div className="text-left">
                <p className="font-semibold text-stone-900">Sarah K.</p>
                <p className="text-sm text-stone-400">Marketing Manager · Now at HubSpot</p>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════
          §6  STATS — bold numbers, warm dark section
          ════════════════════════════════════════════════════ */}
      <section className="bg-stone-900 py-20 sm:py-28">
        <div className="max-w-6xl mx-auto px-6">
          <FadeIn>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 sm:gap-12">
              {[
                { value: "500K+", label: "Applications sent" },
                { value: "3.2x", label: "More interviews" },
                { value: "10K+", label: "Jobs landed" },
                { value: "94%", label: "Avg. ATS score" },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight mb-2">{stat.value}</div>
                  <div className="text-sm text-stone-400 font-medium">{stat.label}</div>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════
          §7  FEATURE DETAILS — alternating rows
          ════════════════════════════════════════════════════ */}
      <section id="features" className="bg-white py-20 sm:py-32">
        <div className="max-w-6xl mx-auto px-6 space-y-24 sm:space-y-32">

          {/* Row 1 — Dashboard */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
              <div className="bg-[#FAF8F5] rounded-2xl p-6 sm:p-8 border border-stone-100">
                <div className="bg-white rounded-xl shadow-sm border border-stone-100 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-stone-200" /><div className="w-2.5 h-2.5 rounded-full bg-stone-200" /><div className="w-2.5 h-2.5 rounded-full bg-stone-200" /></div>
                  </div>
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    <div className="bg-stone-50 rounded-lg p-3 text-center"><div className="text-xl font-bold text-stone-900">127</div><div className="text-[10px] text-stone-400 mt-0.5">Applied</div></div>
                    <div className="bg-emerald-50 rounded-lg p-3 text-center"><div className="text-xl font-bold text-emerald-600">23</div><div className="text-[10px] text-stone-400 mt-0.5">Responses</div></div>
                    <div className="bg-amber-50 rounded-lg p-3 text-center"><div className="text-xl font-bold text-amber-600">7</div><div className="text-[10px] text-stone-400 mt-0.5">Interviews</div></div>
                  </div>
                  {/* Activity bars */}
                  <div className="flex items-end gap-1.5 h-16 px-1">
                    {[40, 65, 55, 80, 70, 90, 45].map((h, i) => (
                      <div key={i} className="flex-1 rounded-t bg-stone-200 hover:bg-amber-300 transition-colors" style={{ height: `${h}%` }} />
                    ))}
                  </div>
                  <div className="flex justify-between text-[9px] text-stone-400 mt-1 px-1">
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => <span key={d}>{d}</span>)}
                  </div>
                </div>
              </div>
              <div>
                <p className="text-amber-700 font-semibold text-sm mb-3">Your command center</p>
                <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-stone-900 leading-[1.15] mb-5">
                  Track everything from one dashboard
                </h2>
                <p className="text-lg text-stone-500 leading-relaxed mb-8">
                  See every application, response, and interview in real time. Know exactly where you stand at a glance.
                </p>
                <ul className="space-y-4">
                  {["Real-time application tracking", "Response & interview monitoring", "AI match confidence scores", "One-click application review"].map((f) => (
                    <li key={f} className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-full bg-stone-100 flex items-center justify-center shrink-0"><Check className="w-3 h-3 text-stone-600" /></div>
                      <span className="text-stone-600 text-[15px]">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </FadeIn>

          {/* Row 2 — Resume Tailoring (reversed) */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
              <div className="order-2 lg:order-1">
                <p className="text-amber-700 font-semibold text-sm mb-3">AI-powered</p>
                <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-stone-900 leading-[1.15] mb-5">
                  Applications that actually get responses
                </h2>
                <p className="text-lg text-stone-500 leading-relaxed mb-8">
                  Every resume and cover letter is rewritten for the specific role, adjusted for company tone, and optimized for ATS.
                </p>
                <ul className="space-y-4">
                  {["Custom resume for every single role", "Company-tone matched cover letters", "ATS keyword optimization built in", "Skills highlighting & gap analysis"].map((f) => (
                    <li key={f} className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-full bg-stone-100 flex items-center justify-center shrink-0"><Check className="w-3 h-3 text-stone-600" /></div>
                      <span className="text-stone-600 text-[15px]">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="order-1 lg:order-2">
                <div className="bg-[#F5F5F0] rounded-2xl p-6 sm:p-8 border border-stone-100">
                  <div className="bg-white rounded-xl shadow-sm border border-stone-100 p-5">
                    <div className="flex items-center justify-between mb-5">
                      <span className="text-sm font-semibold text-stone-900">Tailored Resume</span>
                      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-medium">
                        <TrendingUp className="w-3 h-3" /> ATS: 94%
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="h-5 bg-stone-800 rounded-lg w-3/5" />
                      <div className="h-2.5 bg-stone-100 rounded-full w-full" />
                      <div className="h-2.5 bg-stone-100 rounded-full w-5/6" />
                      <div className="h-2.5 bg-stone-100 rounded-full w-4/5" />
                      <div className="h-px bg-stone-100 my-3" />
                      <div className="h-4 bg-stone-700 rounded-lg w-2/5" />
                      <div className="h-2 bg-stone-50 rounded-full w-full" />
                      <div className="h-2 bg-stone-50 rounded-full w-full" />
                      <div className="h-2 bg-stone-50 rounded-full w-3/4" />
                    </div>
                    <div className="mt-5 flex gap-2 flex-wrap">
                      {["React", "TypeScript", "Node.js", "AWS", "GraphQL"].map((s) => (
                        <span key={s} className="px-2.5 py-1 rounded-md bg-stone-50 text-stone-600 text-[11px] font-medium border border-stone-100">{s}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════
          §8  FEATURES GRID — clean checklist
          ════════════════════════════════════════════════════ */}
      <section className="bg-[#FAFAF9] py-20 sm:py-28 border-y border-stone-100">
        <div className="max-w-6xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <p className="text-amber-700 font-semibold text-sm mb-3">Full feature set</p>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-stone-900 leading-[1.1]">
                Everything you need to automate your hunt
              </h2>
            </div>
          </FadeIn>
          <FadeIn delay={100}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { name: "Smart resume analysis", icon: FileText },
                { name: "Custom cover letters", icon: FileText },
                { name: "ATS optimization", icon: TrendingUp },
                { name: "Thousands of positions", icon: Globe },
                { name: "Real-time tracking", icon: BarChart3 },
                { name: "Interview prep insights", icon: Users },
                { name: "Personalized applications", icon: Sparkles },
                { name: "Salary filtering", icon: SlidersHorizontal },
                { name: "Role matching engine", icon: Zap },
                { name: "Auto-apply engine", icon: Send },
                { name: "Resume versioning", icon: FileText },
                { name: "Data encryption", icon: Shield },
              ].map((feature) => (
                <div
                  key={feature.name}
                  className="flex items-center gap-3 px-4 py-3.5 rounded-xl bg-white border border-stone-100 hover:border-stone-200 hover:shadow-sm transition-all group"
                >
                  <div className="w-7 h-7 rounded-lg bg-stone-50 flex items-center justify-center shrink-0 group-hover:bg-amber-50 transition-colors">
                    <feature.icon className="w-3.5 h-3.5 text-stone-400 group-hover:text-amber-600 transition-colors" />
                  </div>
                  <span className="text-sm font-medium text-stone-700">{feature.name}</span>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════
          §9  TESTIMONIALS
          ════════════════════════════════════════════════════ */}
      <TestimonialsSection />

      {/* ════════════════════════════════════════════════════
          §10  FINAL CTA — warm, inviting close
          ════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden bg-[#FAFAF9] py-24 sm:py-32 border-t border-stone-100">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-br from-amber-50/60 to-orange-50/30 rounded-full blur-3xl pointer-events-none" />
        <div className="relative max-w-6xl mx-auto px-6">
          <FadeIn>
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-stone-900 leading-[1.1] mb-6">
                Your next role is closer than you think
              </h2>
              <p className="text-lg text-stone-500 max-w-lg mx-auto leading-relaxed mb-10">
                Stop applying manually. Join thousands who've reclaimed their time and landed roles they love.
              </p>
              <div className="max-w-[520px] mx-auto">
                <EmailForm variant="light" />
              </div>
              <div className="mt-8 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-stone-400">
                {["Free plan", "No credit card", "Cancel anytime"].map((t) => (
                  <span key={t} className="flex items-center gap-2"><Check className="w-4 h-4 text-stone-400" /> {t}</span>
                ))}
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Sentinel for hide sticky CTA when footer approaches */}
      <div ref={footerSentinelRef} className="h-px w-full" aria-hidden />

      {/* ── Sticky mobile CTA ── */}
      {stickyVisible && (
        <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-white/95 backdrop-blur-md border-t border-stone-200 p-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-2xl">
          <Link to="/login" className="flex items-center justify-center gap-2 w-full h-14 rounded-xl text-base font-semibold bg-stone-900 text-white hover:bg-stone-800 focus:ring-2 focus:ring-stone-900/30 focus:outline-none transition-all shadow-lg">
            Start applying free <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      )}
    </>
  );
}
