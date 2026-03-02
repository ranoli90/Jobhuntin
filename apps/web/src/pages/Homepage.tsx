import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import { telemetry } from '../lib/telemetry';
import { t, getLocale } from '../lib/i18n';
import {
  ArrowRight, MailCheck, Target, Sparkles, Activity,
  Upload, SlidersHorizontal, Send, Trophy,
  ChevronRight, Check, Star, Briefcase, TrendingUp
} from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
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
    if (!validateEmail(email)) { setEmailError(t("homepage.enterValidEmail", getLocale())); return; }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);
    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");
      if (!result.success) throw new Error(result.error || "Failed");
      telemetry.track("login_magic_link_requested", { source: "homepage" });
      pushToast({ title: t("homepage.checkInbox", getLocale()), description: t("homepage.magicLinkSent", getLocale()), tone: "success" });
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
      <div className="flex items-center gap-3 p-4 rounded-2xl border border-gray-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 bg-purple-100 dark:bg-purple-900/30"><MailCheck className="w-5 h-5 text-purple-600 dark:text-purple-400" /></div>
        <div className="min-w-0"><p className="text-sm font-semibold text-gray-900 dark:text-slate-100">{t("homepage.checkInbox", getLocale())}</p><p className="text-xs truncate text-gray-500 dark:text-slate-400">{sentEmail}</p></div>
        <button onClick={() => setSentEmail(null)} className="min-h-[44px] min-w-[44px] px-3 py-2 -m-2 text-xs ml-auto shrink-0 hover:underline text-gray-400 rounded-lg hover:bg-gray-100 transition-colors" aria-label="Change email address">Change</button>
      </div>
    );
  }
  return (
    <div>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3">
        <input type="email" placeholder="you@example.com" aria-label="Email address"
          className={cn("flex-1 h-14 px-6 rounded-full text-base transition-all focus:outline-none focus:ring-2 focus:ring-purple-400 focus:ring-offset-2", variant === "dark" ? "bg-white/10 border-2 border-white/20 text-white placeholder:text-white/40 focus:border-purple-400" : "bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-purple-400 shadow-sm", emailError && "border-red-400")}
          value={email} onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button type="submit" disabled={isSubmitting}
          className="h-14 px-8 rounded-full text-base font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap bg-purple-600 text-white hover:bg-purple-700 hover:shadow-xl hover:shadow-purple-600/25 hover:-translate-y-0.5 active:translate-y-0"
        >
          {isSubmitting ? t("homepage.sending", getLocale()) : t("homepage.startFree", getLocale())} {!isSubmitting && <ArrowRight className="w-4 h-4" aria-hidden />}
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
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } }, { threshold: 0.08 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return (
    <div ref={ref} className={cn("transition-all duration-700 ease-out", visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10", className)} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

/* ─── Live Activity Feed (sample data for demo) ─── */
function LiveActivityFeed({ compact = false }: { compact?: boolean }) {
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
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    const start = () => { interval = setInterval(() => setCurrentIdx((prev) => (prev + 1) % activities.length), 3000); };
    const stop = () => { if (interval) clearInterval(interval); interval = null; };
    const onVisibility = () => (document.hidden ? stop() : start());
    start();
    document.addEventListener('visibilitychange', onVisibility);
    return () => { stop(); document.removeEventListener('visibilitychange', onVisibility); };
  }, []);
  const count = compact ? 3 : 4;
  const visibleItems = [];
  for (let i = 0; i < count; i++) visibleItems.push(activities[(currentIdx + i) % activities.length]);
  return (
    <div className="space-y-2">
      <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wider mb-1">Sample activity — not live</p>
      {visibleItems.map((item, idx) => (
        <div key={`${item.role}-${idx}-${currentIdx}`} className="flex items-center gap-3 px-4 py-2.5 bg-white rounded-xl border border-gray-100 shadow-sm transition-all duration-500" style={{ opacity: 1 - idx * 0.15 }}>
          <div className={cn("w-2 h-2 rounded-full shrink-0", item.type === "applied" ? "bg-green-400" : "bg-purple-400")} />
          <div className="flex-1 min-w-0"><p className="text-sm font-medium text-gray-900 truncate">{item.role}</p><p className="text-xs text-gray-400">{item.company}</p></div>
          <span className="text-[11px] text-gray-400 shrink-0">{item.time}</span>
        </div>
      ))}
    </div>
  );
}

/* ━━━ HOMEPAGE ━━━ */
export default function Homepage() {
  const [stickyVisible, setStickyVisible] = useState(false);
  const [footerInView, setFooterInView] = useState(false);
  const footerSentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = () => setStickyVisible(!footerInView && window.scrollY > 600);
    h(); // initial
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, [footerInView]);

  // X19: Hide sticky CTA when footer is in view
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
      <SEO
        title="JobHuntin | AI That Applies to Jobs While You Sleep"
        description="Upload your resume. Our AI agent tailors every application and applies to hundreds of jobs daily. More interviews, zero effort."
        ogTitle="JobHuntin | AI That Applies to Jobs While You Sleep"
        canonicalUrl="https://jobhuntin.com/"
        schema={{ "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }, "description": "AI agent that tailors and submits job applications autonomously." }}
      />

      {/* ═══════════════════════════════════════════════════════════════
          §1  HERO — centered, big headline, CTA, then visual showcase below
          ═══════════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden">
        {/* Soft gradient bg */}
        <div className="absolute inset-0 bg-gradient-to-b from-purple-50/60 via-white to-white" />

        <div className="relative max-w-7xl mx-auto px-6 pt-16 sm:pt-24 pb-12">
          <div className="max-w-3xl mx-auto text-center">
            <FadeIn>
              <h1 className="text-[clamp(2.75rem,7vw,5.5rem)] font-extrabold leading-[1.02] tracking-[-0.045em] text-gray-900">
                The all-in-one for<br />
                <span className="bg-gradient-to-r from-purple-600 to-violet-500 bg-clip-text text-transparent">job seekers</span>
              </h1>
            </FadeIn>
            <FadeIn delay={80}>
              <p className="mt-7 text-xl sm:text-[1.4rem] text-gray-500 max-w-2xl mx-auto leading-relaxed">
                Upload your resume. Our AI tailors every application and submits to hundreds of jobs daily — while you sleep.
              </p>
            </FadeIn>
            <FadeIn delay={160}>
              <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/login" className="h-14 px-10 rounded-full text-base font-semibold bg-purple-600 text-white hover:bg-purple-700 hover:shadow-xl hover:shadow-purple-600/25 hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2">
                  Get Started Free <ArrowRight className="w-4 h-4" />
                </Link>
                <a href="#how-it-works" className="h-14 px-10 rounded-full text-base font-semibold border-2 border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50 transition-all flex items-center justify-center gap-2">
                  See How It Works
                </a>
              </div>
              <p className="mt-5 text-sm text-gray-400">Free to start · No credit card required</p>
            </FadeIn>
          </div>
        </div>

        {/* ── HERO VISUAL SHOWCASE — overlapping angled cards with mock UI ── */}
        <FadeIn delay={300}>
          <div className="relative max-w-6xl mx-auto px-6 pb-8">
            <div className="relative h-[420px] sm:h-[520px] lg:h-[580px]">
              {/* Card 1 — Purple — Dashboard (center-left, tilted) */}
              <div className="absolute left-[2%] sm:left-[5%] top-[8%] w-[55%] sm:w-[45%] transform -rotate-3 z-20 transition-transform duration-500 hover:rotate-0 hover:scale-[1.02]">
                <div className="bg-gradient-to-br from-purple-500 to-purple-700 rounded-2xl sm:rounded-3xl p-4 sm:p-6 shadow-2xl shadow-purple-500/30">
                  <div className="bg-white rounded-xl sm:rounded-2xl p-3 sm:p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="flex gap-1"><div className="w-2.5 h-2.5 rounded-full bg-red-400" /><div className="w-2.5 h-2.5 rounded-full bg-amber-400" /><div className="w-2.5 h-2.5 rounded-full bg-green-400" /></div>
                      <div className="flex-1 h-4 bg-gray-100 rounded-full mx-4" />
                    </div>
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      <div className="bg-purple-50 rounded-lg p-2 text-center"><div className="text-lg sm:text-xl font-bold text-purple-600">127</div><div className="text-[8px] sm:text-[9px] text-gray-500">Applied</div></div>
                      <div className="bg-green-50 rounded-lg p-2 text-center"><div className="text-lg sm:text-xl font-bold text-green-600">23</div><div className="text-[8px] sm:text-[9px] text-gray-500">Responses</div></div>
                      <div className="bg-amber-50 rounded-lg p-2 text-center"><div className="text-lg sm:text-xl font-bold text-amber-600">7</div><div className="text-[8px] sm:text-[9px] text-gray-500">Interviews</div></div>
                    </div>
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex items-center gap-2 py-1.5 border-t border-gray-50">
                        <div className="w-6 h-6 rounded bg-gray-100 shrink-0" />
                        <div className="flex-1"><div className="h-2 bg-gray-100 rounded-full w-3/4" /><div className="h-1.5 bg-gray-50 rounded-full w-1/2 mt-1" /></div>
                        <div className={cn("px-2 py-0.5 rounded-full text-[7px] sm:text-[8px] font-bold", i === 1 ? "bg-green-100 text-green-700" : i === 2 ? "bg-purple-100 text-purple-700" : "bg-amber-100 text-amber-700")}>{i === 1 ? "Interview" : i === 2 ? "Applied" : "Viewed"}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Card 2 — Coral/Orange — Resume (center-right, tilted other way) */}
              <div className="absolute right-[2%] sm:right-[5%] top-[2%] w-[50%] sm:w-[40%] transform rotate-3 z-30 transition-transform duration-500 hover:rotate-0 hover:scale-[1.02]">
                <div className="bg-gradient-to-br from-orange-400 to-rose-500 rounded-2xl sm:rounded-3xl p-4 sm:p-6 shadow-2xl shadow-orange-500/30">
                  <div className="bg-white rounded-xl sm:rounded-2xl p-3 sm:p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="text-xs font-bold text-gray-900">Resume Preview</div>
                      <div className="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-[8px] font-bold">ATS: 94%</div>
                    </div>
                    <div className="space-y-2">
                      <div className="h-4 bg-gray-900 rounded-full w-2/3" />
                      <div className="h-2.5 bg-gray-200 rounded-full w-full" />
                      <div className="h-2.5 bg-gray-200 rounded-full w-5/6" />
                      <div className="h-2.5 bg-gray-200 rounded-full w-4/5" />
                      <div className="h-px bg-gray-100 my-2" />
                      <div className="h-3 bg-gray-800 rounded-full w-2/5" />
                      <div className="h-2 bg-gray-100 rounded-full w-full" />
                      <div className="h-2 bg-gray-100 rounded-full w-3/4" />
                    </div>
                    <div className="mt-3 flex gap-1.5 flex-wrap">
                      <div className="px-2 py-1 rounded bg-purple-50 text-purple-700 text-[7px] sm:text-[8px] font-bold">React</div>
                      <div className="px-2 py-1 rounded bg-blue-50 text-blue-700 text-[7px] sm:text-[8px] font-bold">TypeScript</div>
                      <div className="px-2 py-1 rounded bg-green-50 text-green-700 text-[7px] sm:text-[8px] font-bold">Node.js</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Card 3 — Blue — Live Feed (bottom center) */}
              <div className="absolute left-[15%] sm:left-[22%] bottom-[0%] w-[55%] sm:w-[42%] transform rotate-1 z-10 transition-transform duration-500 hover:rotate-0 hover:scale-[1.02]">
                <div className="bg-gradient-to-br from-sky-400 to-blue-600 rounded-2xl sm:rounded-3xl p-4 sm:p-6 shadow-2xl shadow-blue-500/30">
                  <div className="bg-white rounded-xl sm:rounded-2xl p-3 sm:p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                      <span className="text-[10px] font-semibold text-gray-700">Live Activity</span>
                    </div>
                    <LiveActivityFeed compact />
                  </div>
                </div>
              </div>

              {/* Small accent shapes */}
              <div className="absolute top-0 right-[35%] w-20 h-20 bg-gradient-to-br from-teal-300 to-emerald-400 rounded-2xl rotate-12 opacity-60 z-0" />
              <div className="absolute bottom-[15%] left-0 w-16 h-16 bg-gradient-to-br from-amber-300 to-orange-400 rounded-xl -rotate-12 opacity-50 z-0" />
              <div className="absolute top-[30%] right-0 w-14 h-14 bg-gradient-to-br from-purple-300 to-violet-400 rounded-lg rotate-6 opacity-40 z-0" />
            </div>
          </div>
        </FadeIn>
      </section>

      {/* ═══ TRUST BAR ═══ */}
      <section className="bg-white border-y border-gray-100 py-10">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider text-center mb-6">Trusted by job seekers landing roles at</p>
          <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-4">
            {["Google", "Amazon", "Meta", "Stripe", "Shopify", "Netflix"].map((name) => (
              <span key={name} className="text-xl font-bold text-gray-300 tracking-tight select-none">{name}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §2  THREE COLORFUL PRODUCT CARDS
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-white py-24 sm:py-36">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-3xl mx-auto mb-20">
              <p className="text-purple-600 font-semibold text-sm uppercase tracking-wider mb-4">How JobHuntin works for you</p>
              <h2 className="text-[clamp(2rem,4.5vw,3.5rem)] font-extrabold tracking-tight text-gray-900 leading-[1.1]">
                Everything you need to<br />land more interviews
              </h2>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-7">
            {/* ── Card 1: Precision Matching (Purple) ── */}
            <FadeIn delay={0}>
              <div className="group rounded-3xl overflow-hidden bg-gradient-to-br from-purple-500 to-purple-700 shadow-purple-500/25 p-7 sm:p-8 pb-0 min-h-[520px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl">
                <div className="flex-1">
                  <div className="w-14 h-14 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center mb-6">
                    <Target className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Precision Matching</h3>
                  <p className="text-white/75 leading-relaxed text-[15px] mb-2">AI analyzes thousands of listings and only applies to roles that truly fit your skills and goals.</p>
                  <a href="#how-it-works" className="inline-flex items-center gap-1.5 text-white/70 hover:text-white font-semibold text-sm mt-2 group/l">
                    Learn more <ChevronRight className="w-4 h-4 group-hover/l:translate-x-1 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-white/[0.08] backdrop-blur-sm rounded-t-2xl p-4 -mx-1 border-t border-white/10">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-bold text-white/60 uppercase tracking-wider">Top Matches</span>
                    <span className="text-[9px] text-white/40">3 of 47 found</span>
                  </div>
                  {[
                    { role: "Sr. Frontend Eng", co: "Stripe", match: 98, salary: "$180k–$220k" },
                    { role: "Product Manager", co: "Airbnb", match: 95, salary: "$165k–$200k" },
                    { role: "UX Designer", co: "Figma", match: 92, salary: "$140k–$175k" },
                  ].map((j, i) => (
                    <div key={i} className="flex items-center gap-3 bg-white/[0.06] rounded-xl p-3 mb-2 last:mb-0">
                      <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center text-[11px] font-black text-white/60 shrink-0">{j.co.charAt(0)}</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] font-bold text-white truncate">{j.role}</p>
                        <p className="text-[9px] text-white/40">{j.co} · {j.salary}</p>
                        <div className="mt-1.5 h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-green-400/60 rounded-full" style={{ width: `${j.match}%` }} />
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-[13px] font-extrabold text-green-300">{j.match}%</div>
                        <div className="text-[7px] text-white/30 uppercase">match</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </FadeIn>

            {/* ── Card 2: Curated Quality (Orange) ── */}
            <FadeIn delay={120}>
              <div className="group rounded-3xl overflow-hidden bg-gradient-to-br from-orange-400 to-rose-500 shadow-orange-500/25 p-7 sm:p-8 pb-0 min-h-[520px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl">
                <div className="flex-1">
                  <div className="w-14 h-14 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center mb-6">
                    <Sparkles className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Curated Quality</h3>
                  <p className="text-white/75 leading-relaxed text-[15px] mb-2">Every resume &amp; cover letter is custom-tailored, ATS-optimized, and company-tone matched.</p>
                  <a href="#features" className="inline-flex items-center gap-1.5 text-white/70 hover:text-white font-semibold text-sm mt-2 group/l">
                    Learn more <ChevronRight className="w-4 h-4 group-hover/l:translate-x-1 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-white/[0.08] backdrop-blur-sm rounded-t-2xl p-4 -mx-1 border-t border-white/10">
                  {/* Mini resume document mock */}
                  <div className="bg-white/[0.06] rounded-xl p-3.5">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="h-3 w-24 bg-white/30 rounded-full mb-1" />
                        <div className="h-2 w-16 bg-white/15 rounded-full" />
                      </div>
                      <div className="px-2.5 py-1 rounded-lg bg-green-400/20 text-[9px] font-bold text-green-200 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" /> ATS 94%
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="h-1.5 bg-white/20 rounded-full w-full" />
                      <div className="h-1.5 bg-white/15 rounded-full w-[90%]" />
                      <div className="h-1.5 bg-white/10 rounded-full w-[75%]" />
                    </div>
                    <div className="mt-2.5 pt-2.5 border-t border-white/5">
                      <div className="h-2 w-14 bg-white/20 rounded-full mb-1.5" />
                      <div className="space-y-1">
                        <div className="h-1.5 bg-white/10 rounded-full w-full" />
                        <div className="h-1.5 bg-white/10 rounded-full w-[85%]" />
                      </div>
                    </div>
                    <div className="mt-2.5 flex gap-1.5 flex-wrap">
                      {["React", "TS", "Node", "AWS"].map((s) => (
                        <span key={s} className="px-2 py-0.5 rounded bg-white/10 text-[7px] font-bold text-white/60">{s}</span>
                      ))}
                    </div>
                  </div>
                  {/* Quality metrics */}
                  <div className="mt-2.5 grid grid-cols-3 gap-1.5">
                    {[
                      { label: "Tone", icon: "✓", color: "bg-green-400/15 text-green-200" },
                      { label: "Keywords", icon: "✓", color: "bg-green-400/15 text-green-200" },
                      { label: "Format", icon: "✓", color: "bg-green-400/15 text-green-200" },
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
              <div className="group rounded-3xl overflow-hidden bg-gradient-to-br from-sky-400 to-blue-600 shadow-blue-500/25 p-7 sm:p-8 pb-0 min-h-[520px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl">
                <div className="flex-1">
                  <div className="w-14 h-14 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center mb-6">
                    <Activity className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Live Tracking</h3>
                  <p className="text-white/75 leading-relaxed text-[15px] mb-2">Watch applications go out in real-time. See matches, responses, and interview invites instantly.</p>
                  <a href="#dashboard" className="inline-flex items-center gap-1.5 text-white/70 hover:text-white font-semibold text-sm mt-2 group/l">
                    Learn more <ChevronRight className="w-4 h-4 group-hover/l:translate-x-1 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-white/[0.08] backdrop-blur-sm rounded-t-2xl p-4 -mx-1 border-t border-white/10">
                  {/* Mini stats row */}
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="bg-white/[0.06] rounded-lg p-2 text-center">
                      <div className="text-[15px] font-extrabold text-white">18</div>
                      <div className="text-[7px] text-white/40 uppercase tracking-wide">Today</div>
                    </div>
                    <div className="bg-white/[0.06] rounded-lg p-2 text-center">
                      <div className="text-[15px] font-extrabold text-white">127</div>
                      <div className="text-[7px] text-white/40 uppercase tracking-wide">This week</div>
                    </div>
                    <div className="bg-white/[0.06] rounded-lg p-2 text-center">
                      <div className="text-[15px] font-extrabold text-green-300">4</div>
                      <div className="text-[7px] text-white/40 uppercase tracking-wide">Interviews</div>
                    </div>
                  </div>
                  {/* Activity bar chart */}
                  <div className="flex items-center gap-1.5 mb-2"><div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /><span className="text-[8px] text-white/40 uppercase tracking-wider font-bold">Activity This Week</span></div>
                  <div className="flex items-end gap-1 h-10 mb-1">
                    {[40, 65, 55, 80, 70, 90, 45].map((h, i) => (
                      <div key={i} className="flex-1 rounded-t bg-white/15 hover:bg-white/25 transition-colors" style={{ height: `${h}%` }} />
                    ))}
                  </div>
                  <div className="flex justify-between text-[7px] text-white/25 font-medium">
                    {["M", "T", "W", "T", "F", "S", "S"].map((d, i) => <span key={i}>{d}</span>)}
                  </div>
                </div>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §3  BIG TESTIMONIAL QUOTE
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-gray-50 py-24 sm:py-32">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <FadeIn>
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 mb-8">
              <span className="text-3xl text-purple-600 font-serif leading-none">"</span>
            </div>
            <blockquote className="text-[clamp(1.5rem,3.5vw,2.75rem)] font-bold text-gray-900 leading-snug tracking-tight">
              That first week I literally did nothing and got 4 interview callbacks. This is the future of job hunting.
            </blockquote>
            <div className="mt-10 flex items-center justify-center gap-4">
              <div className="w-14 h-14 rounded-full bg-purple-100 flex items-center justify-center text-lg font-bold text-purple-700">SK</div>
              <div className="text-left">
                <p className="font-semibold text-gray-900 text-lg">Sarah K.</p>
                <p className="text-sm text-gray-500">Marketing Manager · Landed at HubSpot</p>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §4  FEATURE SHOWCASE ROWS — large mockups on colored backgrounds
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-white py-24 sm:py-36">
        <div className="max-w-7xl mx-auto px-6 space-y-32 sm:space-y-44">

          {/* Row 1 — Dashboard */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-16 lg:gap-24 items-center">
              <div className="relative">
                <div className="bg-gradient-to-br from-purple-100 via-purple-50 to-violet-100 rounded-[2rem] p-6 sm:p-10 lg:p-12">
                  <div className="bg-white rounded-2xl shadow-2xl shadow-purple-200/50 p-5 sm:p-6 border border-gray-100/80">
                    <div className="flex items-center gap-2 mb-5">
                      <div className="flex gap-1.5"><div className="w-3 h-3 rounded-full bg-red-400" /><div className="w-3 h-3 rounded-full bg-amber-400" /><div className="w-3 h-3 rounded-full bg-green-400" /></div>
                      <div className="flex-1 h-7 bg-gray-100 rounded-full mx-6" />
                    </div>
                    <div className="grid grid-cols-3 gap-3 mb-5">
                      <div className="bg-purple-50 rounded-xl p-3 sm:p-4 text-center"><div className="text-2xl sm:text-3xl font-extrabold text-purple-600">127</div><div className="text-[10px] sm:text-xs text-gray-500 mt-1">Applied</div></div>
                      <div className="bg-green-50 rounded-xl p-3 sm:p-4 text-center"><div className="text-2xl sm:text-3xl font-extrabold text-green-600">23</div><div className="text-[10px] sm:text-xs text-gray-500 mt-1">Responses</div></div>
                      <div className="bg-amber-50 rounded-xl p-3 sm:p-4 text-center"><div className="text-2xl sm:text-3xl font-extrabold text-amber-600">7</div><div className="text-[10px] sm:text-xs text-gray-500 mt-1">Interviews</div></div>
                    </div>
                    <div className="space-y-0">
                      {[
                        { role: "Senior Frontend Engineer", co: "Stripe", status: "Interview", color: "bg-green-100 text-green-700" },
                        { role: "Product Manager", co: "Airbnb", status: "Applied", color: "bg-purple-100 text-purple-700" },
                        { role: "Data Scientist", co: "Netflix", status: "Viewed", color: "bg-amber-100 text-amber-700" },
                        { role: "UX Designer", co: "Figma", status: "Applied", color: "bg-purple-100 text-purple-700" },
                      ].map((row, i) => (
                        <div key={i} className="flex items-center gap-3 py-3 border-t border-gray-50">
                          <div className="w-9 h-9 rounded-xl bg-gray-100 flex items-center justify-center shrink-0"><Briefcase className="w-4 h-4 text-gray-400" /></div>
                          <div className="flex-1 min-w-0"><p className="text-sm font-medium text-gray-900 truncate">{row.role}</p><p className="text-xs text-gray-400">{row.co}</p></div>
                          <div className={cn("px-2.5 py-1 rounded-full text-[10px] font-bold shrink-0", row.color)}>{row.status}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <p className="text-purple-600 font-semibold text-sm uppercase tracking-wider mb-4">Your command center</p>
                <h2 className="text-[clamp(2rem,4vw,3rem)] font-extrabold tracking-tight text-gray-900 leading-[1.1]">
                  A dashboard that keeps you in complete control
                </h2>
                <p className="mt-6 text-lg text-gray-500 leading-relaxed">
                  Track every application, see live matches, monitor responses, and review AI-crafted submissions — all in one beautiful dashboard.
                </p>
                <ul className="mt-10 space-y-5">
                  {["Real-time application tracking", "Response & interview monitoring", "AI match confidence scores", "One-click application review"].map((f) => (
                    <li key={f} className="flex items-center gap-4"><div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center shrink-0"><Check className="w-4 h-4 text-purple-600" /></div><span className="text-gray-700 font-medium text-[15px]">{f}</span></li>
                  ))}
                </ul>
                <Link to="/login" className="inline-flex items-center gap-2 mt-10 h-14 px-10 rounded-full text-base font-semibold bg-purple-600 text-white hover:bg-purple-700 hover:shadow-xl hover:shadow-purple-600/25 hover:-translate-y-0.5 transition-all">
                  Try it free <ArrowRight className="w-4 h-4" />
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
                        <div key={s} className="px-3 py-1.5 rounded-lg bg-purple-50 text-purple-700 text-[10px] font-bold">{s}</div>
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
                      <div className="text-center"><div className="text-lg font-bold text-gray-900">18</div><div className="text-[9px] text-gray-400">Today</div></div>
                      <div className="text-center"><div className="text-lg font-bold text-gray-900">127</div><div className="text-[9px] text-gray-400">This week</div></div>
                      <div className="text-center"><div className="text-lg font-bold text-gray-900">4</div><div className="text-[9px] text-gray-400">Interviews</div></div>
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
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §5  HOW IT WORKS — colorful step cards
          ═══════════════════════════════════════════════════════════════ */}
      <section id="how-it-works" className="bg-gray-50 py-24 sm:py-36">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-20">
              <p className="text-purple-600 font-semibold text-sm uppercase tracking-wider mb-4">Simple setup</p>
              <h2 className="text-[clamp(2rem,4.5vw,3.5rem)] font-extrabold tracking-tight text-gray-900 leading-[1.1]">
                Set up in 2 minutes.<br />Then it runs on autopilot.
              </h2>
            </div>
          </FadeIn>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Step 1 — Upload Resume */}
            <FadeIn delay={0}>
              <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-purple-500 via-purple-600 to-violet-700 p-7 text-white min-h-[340px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl hover:shadow-purple-500/20">
                <div className="absolute top-3 right-3 w-24 h-24 bg-white/[0.06] rounded-2xl rotate-12" />
                <div className="absolute bottom-8 right-6 w-16 h-16 bg-white/[0.04] rounded-xl -rotate-6" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center mb-5">
                    <Upload className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-2">Step 1</div>
                  <h3 className="text-xl font-bold mb-3">Upload resume</h3>
                  <p className="text-white/70 text-[13px] leading-relaxed mb-5">Drop your PDF or paste a URL. We parse skills, experience, and preferences instantly.</p>
                </div>
                <div className="mt-auto relative bg-white/[0.08] rounded-xl p-3 border border-white/[0.06]">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center shrink-0">
                      <Upload className="w-5 h-5 text-white/50" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="h-2 bg-white/20 rounded-full w-2/3 mb-1.5" />
                      <div className="h-1.5 bg-white/10 rounded-full w-1/2" />
                    </div>
                    <div className="px-2 py-1 rounded-lg bg-green-400/20 text-[8px] font-bold text-green-300">Parsed ✓</div>
                  </div>
                </div>
              </div>
            </FadeIn>

            {/* Step 2 — Set Filters */}
            <FadeIn delay={100}>
              <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-orange-400 via-rose-500 to-pink-600 p-7 text-white min-h-[340px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl hover:shadow-orange-500/20">
                <div className="absolute top-4 right-4 w-20 h-20 bg-white/[0.06] rounded-full" />
                <div className="absolute bottom-10 right-8 w-12 h-12 bg-white/[0.04] rounded-full" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center mb-5">
                    <SlidersHorizontal className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-2">Step 2</div>
                  <h3 className="text-xl font-bold mb-3">Set your filters</h3>
                  <p className="text-white/70 text-[13px] leading-relaxed mb-5">Roles, locations, salary range, company size — we only apply to what genuinely matches.</p>
                </div>
                <div className="mt-auto relative space-y-2">
                  {[
                    { label: "Role", value: "Frontend Engineer" },
                    { label: "Salary", value: "$150k – $200k" },
                    { label: "Remote", value: "Yes" },
                  ].map((f) => (
                    <div key={f.label} className="flex items-center justify-between bg-white/[0.08] rounded-lg px-3 py-2 border border-white/[0.06]">
                      <span className="text-[10px] text-white/40 font-semibold">{f.label}</span>
                      <span className="text-[10px] text-white/80 font-bold">{f.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </FadeIn>

            {/* Step 3 — AI Applies */}
            <FadeIn delay={200}>
              <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-sky-400 via-blue-500 to-indigo-600 p-7 text-white min-h-[340px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl hover:shadow-blue-500/20">
                <div className="absolute top-3 right-3 w-28 h-16 bg-white/[0.05] rounded-xl rotate-6" />
                <div className="absolute bottom-12 right-4 w-14 h-14 bg-white/[0.04] rounded-lg -rotate-12" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center mb-5">
                    <Send className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-2">Step 3</div>
                  <h3 className="text-xl font-bold mb-3">AI applies for you</h3>
                  <p className="text-white/70 text-[13px] leading-relaxed mb-5">Every application is individually tailored with a custom resume and cover letter.</p>
                </div>
                <div className="mt-auto relative bg-white/[0.08] rounded-xl p-3 border border-white/[0.06]">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-[9px] text-white/50 font-semibold">Applying now…</span>
                  </div>
                  <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-white/30 rounded-full w-[72%] animate-pulse" />
                  </div>
                  <div className="flex justify-between mt-1.5">
                    <span className="text-[8px] text-white/30">18 of 25 today</span>
                    <span className="text-[8px] text-green-300 font-bold">72%</span>
                  </div>
                </div>
              </div>
            </FadeIn>

            {/* Step 4 — Get Interviews */}
            <FadeIn delay={300}>
              <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-emerald-400 via-emerald-500 to-teal-600 p-7 text-white min-h-[340px] flex flex-col hover:-translate-y-2 transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-500/20">
                <div className="absolute top-4 right-4 w-20 h-20 bg-white/[0.06] rounded-2xl rotate-12" />
                <div className="absolute bottom-8 right-6 w-14 h-10 bg-white/[0.04] rounded-xl -rotate-3" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center mb-5">
                    <Trophy className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-2">Step 4</div>
                  <h3 className="text-xl font-bold mb-3">Get interviews</h3>
                  <p className="text-white/70 text-[13px] leading-relaxed mb-5">Track responses, prep for interviews with AI insights, and land your dream role.</p>
                </div>
                <div className="mt-auto relative grid grid-cols-3 gap-2">
                  <div className="bg-white/[0.08] rounded-xl p-2.5 text-center border border-white/[0.06]">
                    <div className="text-lg font-extrabold">7</div>
                    <div className="text-[7px] text-white/40 uppercase font-bold tracking-wide">Interviews</div>
                  </div>
                  <div className="bg-white/[0.08] rounded-xl p-2.5 text-center border border-white/[0.06]">
                    <div className="text-lg font-extrabold">3</div>
                    <div className="text-[7px] text-white/40 uppercase font-bold tracking-wide">Offers</div>
                  </div>
                  <div className="bg-white/[0.08] rounded-xl p-2.5 text-center border border-white/[0.06]">
                    <div className="text-lg font-extrabold text-green-300">1</div>
                    <div className="text-[7px] text-white/40 uppercase font-bold tracking-wide">Accepted</div>
                  </div>
                </div>
              </div>
            </FadeIn>
          </div>

          <FadeIn delay={400}>
            <div className="text-center mt-16">
              <Link to="/login" className="inline-flex items-center gap-2 h-14 px-10 rounded-full text-base font-semibold bg-purple-600 text-white hover:bg-purple-700 hover:shadow-xl hover:shadow-purple-600/25 hover:-translate-y-0.5 transition-all">
                Get Started Free <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="mt-4 text-sm text-gray-400">Your first applications go out today</p>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §6  TESTIMONIALS GRID
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-white py-24 sm:py-36">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-20">
              <h2 className="text-[clamp(2rem,4.5vw,3.5rem)] font-extrabold tracking-tight text-gray-900 leading-[1.1]">
                Loved by job seekers everywhere
              </h2>
            </div>
          </FadeIn>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { q: "Got 4 interviews in my first week. I'd been applying manually for 3 months with nothing.", n: "Sarah K.", r: "Marketing Manager", initials: "SK", bg: "bg-purple-100 text-purple-700" },
              { q: "The cover letters are genuinely better than what I'd write myself. Not generic at all.", n: "Marcus T.", r: "Software Engineer", initials: "MT", bg: "bg-teal-100 text-teal-700" },
              { q: "Found a listing 20 minutes after it was posted and applied instantly. That's how I got my current role.", n: "Priya R.", r: "Product Designer", initials: "PR", bg: "bg-orange-100 text-orange-700" },
              { q: "Landed 7 interviews in 2 weeks. The AI matched me with roles I didn't even know existed.", n: "James L.", r: "Data Analyst", initials: "JL", bg: "bg-sky-100 text-sky-700" },
              { q: "I was skeptical about AI applications, but every single one was personalized. My response rate doubled.", n: "Elena M.", r: "Product Manager", initials: "EM", bg: "bg-rose-100 text-rose-700" },
              { q: "Set it up in 5 minutes and forgot about it. Got a call from Google the next week.", n: "David C.", r: "Engineering Lead", initials: "DC", bg: "bg-amber-100 text-amber-700" },
            ].map((t, idx) => (
              <FadeIn key={t.n} delay={idx * 80}>
                <div className="bg-gray-50 rounded-2xl p-8 hover:bg-gray-100/80 transition-colors h-full flex flex-col">
                  <div className="flex gap-0.5 mb-5">{[...Array(5)].map((_, i) => <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />)}</div>
                  <p className="text-[15px] text-gray-700 leading-relaxed flex-1 mb-6">"{t.q}"</p>
                  <div className="flex items-center gap-3">
                    <div className={cn("w-11 h-11 rounded-full flex items-center justify-center text-sm font-bold", t.bg)}>{t.initials}</div>
                    <div><p className="text-sm font-semibold text-gray-900">{t.n}</p><p className="text-xs text-gray-400">{t.r}</p></div>
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §7  FEATURES GRID
          ═══════════════════════════════════════════════════════════════ */}
      <section id="features" className="bg-gray-50 py-24 sm:py-36">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-3xl mx-auto mb-8">
              <p className="text-purple-600 font-semibold text-sm uppercase tracking-wider mb-4">Full feature set</p>
              <h2 className="text-[clamp(2rem,4.5vw,3.5rem)] font-extrabold tracking-tight text-gray-900 leading-[1.1]">
                Everything you need,<br />right out of the box
              </h2>
            </div>
          </FadeIn>
          <FadeIn delay={100}>
            <div className="text-center max-w-xl mx-auto mb-16">
              <p className="text-gray-500 italic text-base">"Instead of worrying about 20 different tools…<br />I just run my search from JobHuntin."</p>
              <p className="mt-3 text-sm text-gray-400 font-medium">– Sarah K., Marketing Manager</p>
            </div>
          </FadeIn>
          <FadeIn delay={200}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {["AI resume analysis", "Custom cover letters", "ATS optimization", "Thousands of positions", "Real-time tracking", "Interview prep insights", "Personalized applications", "Salary filtering", "Company size filters", "Location preferences", "Role matching AI", "Auto-apply engine", "Application dashboard", "Response tracking", "Resume versioning", "Email notifications", "Mobile dashboard", "Data encryption", "Bulk applications", "Smart scheduling", "Company research", "Skills gap analysis", "Application analytics", "Priority support"].map((feature) => (
                <div key={feature} className="flex items-center gap-3 px-4 py-3.5 rounded-xl bg-white border border-gray-100 hover:border-purple-200 hover:shadow-sm transition-all">
                  <div className="w-5 h-5 rounded-full bg-purple-100 flex items-center justify-center shrink-0"><Check className="w-3 h-3 text-purple-600" /></div>
                  <span className="text-sm font-medium text-gray-700">{feature}</span>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          §8  FINAL CTA — colorful bg with floating shapes
          ═══════════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-purple-50 via-blue-50/80 to-teal-50 py-28 sm:py-40">
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-[10%] left-[3%] w-[220px] h-[170px] bg-gradient-to-br from-purple-300 to-purple-500 rounded-3xl rotate-12 opacity-[0.1]" />
          <div className="absolute bottom-[8%] right-[3%] w-[260px] h-[200px] bg-gradient-to-br from-blue-300 to-sky-500 rounded-3xl -rotate-6 opacity-[0.1]" />
          <div className="absolute top-[35%] right-[12%] w-[180px] h-[140px] bg-gradient-to-br from-orange-300 to-rose-400 rounded-2xl rotate-6 opacity-[0.08]" />
          <div className="absolute bottom-[30%] left-[10%] w-[200px] h-[160px] bg-gradient-to-br from-teal-300 to-emerald-400 rounded-2xl -rotate-12 opacity-[0.08]" />
        </div>
        <div className="relative max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-[clamp(2.25rem,5vw,3.75rem)] font-extrabold tracking-tight text-gray-900 leading-[1.08]">
                Job searching is simpler when AI does the heavy lifting
              </h2>
              <p className="mt-7 text-xl text-gray-500 max-w-lg mx-auto leading-relaxed">
                Stop applying manually. Set it up in 2 minutes and your first applications go out today.
              </p>
              <div className="mt-12 max-w-[520px] mx-auto">
                <EmailForm variant="light" />
              </div>
              <div className="mt-7 flex flex-wrap items-center justify-center gap-x-7 gap-y-2 text-sm text-gray-400">
                {["Free plan", "No credit card", "Cancel anytime"].map((t) => (
                  <span key={t} className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> {t}</span>
                ))}
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Sentinel for X19: hide sticky CTA when footer approaches */}
      <div ref={footerSentinelRef} className="h-px w-full" aria-hidden />

      {/* ── Sticky mobile CTA ── */}
      {stickyVisible && (
        <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-white/95 backdrop-blur-sm border-t border-gray-200 p-3 shadow-lg">
          <Link to="/login" className="flex items-center justify-center gap-2 w-full h-12 rounded-full text-[15px] font-semibold bg-purple-600 text-white hover:bg-purple-700 transition-colors">
            Get Started Free <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </>
  );
}
