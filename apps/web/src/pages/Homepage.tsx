import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import { telemetry } from '../lib/telemetry';
import { ArrowRight, MailCheck, Check, Briefcase, TrendingUp } from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { FAQAccordion } from '../components/seo/FAQAccordion';
import { TestimonialsSection } from '../components/TestimonialsSection';
import { cn } from '../lib/utils';
import { ValidationUtils } from '../lib/validation';

/*
 * Design tokens — matched to Notion.com's inspected values
 * H1: Inter 700, 64px, line-height 64px, letter-spacing -2.125px
 * Body: Inter 400, 16px, line-height 24px
 * Button: Inter 500, 16px, 8px radius, #455DD3, 36px height, padding 6px 16px
 * Cards: 12px radius, no box-shadow, color blocks create depth
 */

/* ── Email capture ── */
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
    setEmailError(""); setIsSubmitting(true); setSentEmail(null);
    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");
      if (!result.success) throw new Error(result.error || "Could not send magic link");
      telemetry.track("login_magic_link_requested", { source: "homepage" });
      pushToast({ title: "Check your inbox", description: "Magic link sent!", tone: "success" });
      setSentEmail(result.email); setEmail("");
    } catch (err: unknown) {
      const msg = (typeof (err as Error)?.message === 'string' && !(err as Error).message.includes('[object')) ? (err as Error).message : "We couldn't send the magic link. Please try again.";
      setEmailError(msg);
      pushToast({ title: "Could not send magic link", description: msg, tone: "error" });
    } finally { setIsSubmitting(false); }
  };
  return { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit };
}

function EmailForm({ variant = "light" }: { variant?: "light" | "dark" }) {
  const { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit } = useEmailCapture();
  const dark = variant === "dark";
  if (sentEmail) {
    return (
      <div className="flex items-center gap-4 p-5 rounded-xl bg-emerald-50 border border-emerald-200">
        <MailCheck className="w-5 h-5 text-emerald-600 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-[#2D2A26]">Check your inbox</p>
          <p className="text-xs text-[#787774] mt-0.5 truncate">{sentEmail}</p>
        </div>
        <button onClick={() => setSentEmail(null)} className="text-xs font-medium text-emerald-700 hover:underline">Change</button>
      </div>
    );
  }
  return (
    <div>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3">
        <input type="email" placeholder="you@example.com" aria-label="Email address"
          className={cn(
            "flex-1 min-h-[48px] sm:min-h-[44px] px-4 rounded-xl text-base sm:text-[14px] transition-all outline-none w-full",
            dark
              ? "bg-white/10 border-2 border-white/20 text-white placeholder:text-white/50 focus:border-white/50 focus:ring-2 focus:ring-white/20"
              : "bg-white border-2 border-[#E3E2E0] text-[#2D2A26] placeholder:text-[#B0AFA9] focus:border-[#455DD3] focus:ring-2 focus:ring-[#455DD3]/10",
            emailError && "!border-red-400"
          )}
          value={email}
          onChange={e => { setEmail(e.target.value.trimStart()); setEmailError(""); }}
          onPaste={e => {
            const pasted = (e.clipboardData?.getData('text') || '').trim();
            if (pasted && ValidationUtils.validate.email(pasted).isValid) {
              e.preventDefault();
              setEmail(pasted.toLowerCase());
              setEmailError("");
            }
          }}
        />
        <button type="submit" disabled={isSubmitting}
          className={cn(
            "min-h-[48px] sm:min-h-[44px] px-6 rounded-xl text-base sm:text-[14px] font-semibold flex items-center justify-center gap-2 whitespace-nowrap transition-all disabled:opacity-50 shrink-0",
            dark
              ? "bg-white text-[#2D2A26] hover:bg-white/90"
              : "bg-[#455DD3] text-white hover:bg-[#3A4FB8]"
          )}
        >{isSubmitting ? "Sending…" : "Start free"} {!isSubmitting && <ArrowRight className="w-4 h-4" />}</button>
      </form>
      {emailError && <p className="mt-2 text-sm text-red-500 pl-1">{emailError}</p>}
    </div>
  );
}

/* ── Scroll reveal ── */
function Reveal({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [vis, setVis] = useState(false);
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  useEffect(() => {
    if (reduced) { setVis(true); return; }
    const el = ref.current; if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); obs.disconnect(); } }, { threshold: 0.1 });
    obs.observe(el); return () => obs.disconnect();
  }, [reduced]);
  return (
    <div ref={ref}
      className={cn(reduced ? "" : "transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]", vis ? "opacity-100 translate-y-0" : (reduced ? "" : "opacity-0 translate-y-5"), className)}
      style={{ transitionDelay: reduced ? '0ms' : `${delay}ms` }}
    >{children}</div>
  );
}

/* ── Counter ── */
function Counter({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [val, setVal] = useState(0);
  const [go, setGo] = useState(false);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setGo(true); obs.disconnect(); } }, { threshold: 0.3 });
    obs.observe(el); return () => obs.disconnect();
  }, []);
  useEffect(() => {
    if (!go) return;
    const dur = 1200, t0 = Date.now();
    const tick = () => { const p = Math.min((Date.now() - t0) / dur, 1); setVal(Math.round((1 - Math.pow(1 - p, 3)) * to)); if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  }, [go, to]);
  return <span ref={ref}>{val.toLocaleString()}{suffix}</span>;
}

/* ── User journey animated story ── */
const JOURNEY_ILLUSTRATIONS: Record<string, string> = {
  signup: '/illustrations/files-uploading.svg',
  apply: '/illustrations/application.svg',
  callbacks: '/illustrations/emails.svg',
  landed: '/illustrations/celebration.svg',
};
const JOURNEY_STEPS = [
  { id: 'signup', title: 'You sign up', sub: 'Drop your resume', color: '#455DD3', duration: 3500 },
  { id: 'apply', title: 'We apply', sub: '127 applications sent', color: '#17BEBB', duration: 3500 },
  { id: 'callbacks', title: 'Callbacks roll in', sub: '23 companies reached out', color: '#16A34A', duration: 3500 },
  { id: 'landed', title: 'You land the role', sub: 'Interview → Offer → Start', color: '#EA580C', duration: 4000 },
];

function UserJourneySection() {
  const [step, setStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [tabVisible, setTabVisible] = useState(true);
  const [justLanded, setJustLanded] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => setIsVisible(e.isIntersecting), { threshold: 0.2 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    setTabVisible(!document.hidden);
    const h = () => setTabVisible(!document.hidden);
    document.addEventListener('visibilitychange', h);
    return () => document.removeEventListener('visibilitychange', h);
  }, []);

  useEffect(() => {
    if (!isVisible || reduced || !tabVisible) return;
    const current = JOURNEY_STEPS[step];
    const t = setTimeout(() => {
      const next = (step + 1) % JOURNEY_STEPS.length;
      setJustLanded(next === 3);
      setStep(next);
    }, current.duration);
    return () => clearTimeout(t);
  }, [step, isVisible, reduced, tabVisible]);

  const s = JOURNEY_STEPS[step];

  return (
    <section ref={ref} className="bg-[#2D2A26] py-[80px] sm:py-[100px] relative overflow-hidden" aria-live="polite" aria-atomic="true">
      {/* Floating orbs */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[15%] left-[10%] w-3 h-3 rounded-full bg-[#455DD3]/40 animate-pulse" style={{ animationDuration: '3s' }} />
        <div className="absolute top-[25%] right-[15%] w-2 h-2 rounded-full bg-[#17BEBB]/30 animate-pulse" style={{ animationDuration: '2.5s', animationDelay: '0.5s' }} />
        <div className="absolute bottom-[30%] left-[20%] w-2 h-2 rounded-full bg-[#EA580C]/30 animate-pulse" style={{ animationDuration: '2s', animationDelay: '1s' }} />
        <div className="absolute bottom-[20%] right-[10%] w-3 h-3 rounded-full bg-[#16A34A]/30 animate-pulse" style={{ animationDuration: '2.8s', animationDelay: '0.3s' }} />
      </div>
      <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 60% 40% at 50% 100%, rgba(69,93,211,0.12) 0%, transparent 70%)' }} />
      <div className="relative max-w-[1080px] mx-auto px-6">
        <Reveal>
          <p className="text-center text-[12px] font-medium text-[#7DD3CF] uppercase tracking-widest mb-[12px]">Your story starts here</p>
          <h2 className="text-center text-[clamp(1.75rem,4vw,40px)] font-bold text-white leading-tight mb-[48px]" style={{ letterSpacing: '-1.5px' }}>
            From signup to offer —<br />
            <span className="text-[#7DD3CF]">in one flow</span>
          </h2>
        </Reveal>

        <div className="max-w-[600px] mx-auto">
          <Reveal delay={100}>
            <div className="relative min-h-[300px] sm:min-h-[340px] rounded-2xl border-2 border-white/15 bg-gradient-to-b from-white/[0.08] to-white/[0.02] overflow-hidden shadow-2xl shadow-black/20">
              {/* Wavy progress path */}
              <div className="absolute top-0 left-0 right-0 h-1.5 bg-white/10">
                <div
                  className="h-full transition-all duration-700 ease-out rounded-r-full"
                  style={{ width: `${((step + 1) / JOURNEY_STEPS.length) * 100}%`, background: `linear-gradient(90deg, ${s.color}, ${s.color}99)` }}
                />
              </div>

              {/* Step content with illustration */}
              <div className="p-8 sm:p-12 flex flex-col items-center justify-center min-h-[270px] sm:min-h-[310px]">
                <div
                  className={cn(
                    "w-full max-w-[220px] h-[140px] sm:h-[160px] mb-6 flex items-center justify-center transition-transform duration-500",
                    justLanded && !reduced && "animate-bounce"
                  )}
                >
                  <img
                    src={JOURNEY_ILLUSTRATIONS[s.id]}
                    alt=""
                    width={220}
                    height={160}
                    className="object-contain w-full h-full"
                    loading="lazy"
                    aria-hidden
                  />
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold text-white mb-2 text-center">{s.title}</h3>
                <p className="text-white/80 text-center font-medium">{s.sub}</p>

                {/* Step rail - dots aligned horizontally */}
                <div className="flex justify-center items-center gap-3 sm:gap-4 mt-8">
                  {JOURNEY_STEPS.map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "w-3 h-3 rounded-full shrink-0 transition-all duration-300",
                        i === step ? "scale-125 ring-2 ring-offset-2 ring-offset-[#2D2A26]" : "opacity-40"
                      )}
                      style={{
                        background: i === step ? s.color : 'white',
                        boxShadow: i === step ? `0 0 12px ${s.color}` : 'none',
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Dashboard mock - more playful */}
              <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10 bg-black/20">
                <div className="flex items-center gap-2 text-white/40 text-xs font-mono">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-red-500/60" />
                    <div className="w-2 h-2 rounded-full bg-amber-500/60" />
                    <div className="w-2 h-2 rounded-full bg-emerald-500/60" />
                  </div>
                  <span className="ml-2 truncate">jobhuntin.com/dashboard</span>
                  <span className="ml-auto text-[#7DD3CF]/60">● Live</span>
                </div>
              </div>
            </div>
          </Reveal>

          <p className="text-center text-[15px] text-white/60 mt-8 font-medium">
            <span className="text-[#7DD3CF]">Your turn is next.</span>
          </p>
        </div>
      </div>
    </section>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   PAGE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function Homepage() {
  const [stickyVisible, setStickyVisible] = useState(false);
  const [footerInView, setFooterInView] = useState(false);
  const footerSentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = () => setStickyVisible(!footerInView && window.scrollY > 600);
    h(); window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, [footerInView]);

  useEffect(() => {
    const s = footerSentinelRef.current; if (!s) return;
    const io = new IntersectionObserver(([e]) => setFooterInView(e.isIntersecting), { rootMargin: '-100px 0px 0px 0px', threshold: 0 });
    io.observe(s); return () => io.disconnect();
  }, []);

  return (
    <>
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#2D2A26] focus:text-white focus:rounded-lg">Skip to main content</a>
      <SEO title="JobHuntin — The Application Engine That Runs While You Sleep" description="Upload your resume. Our platform tailors every application and submits to hundreds of jobs daily." ogTitle="JobHuntin — The Application Engine That Runs While You Sleep" canonicalUrl="https://jobhuntin.com/" ogImage="https://jobhuntin.com/og-image.png"  breadcrumbs={[{ name: "Home", url: "https://jobhuntin.com" }]} schema={{ "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD", "priceValidUntil": new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split("T")[0] }, "description": "Automated system that tailors and submits job applications." }} />

      {/* ═══════════════════════════════════════════
          HERO — dark bg, flowing artwork, experiential
          ═══════════════════════════════════════════ */}
      <section id="main-content" className="relative overflow-hidden min-h-[90vh] flex flex-col justify-center" style={{ background: 'linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)' }}>
        {/* Radial spotlight for depth */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(69,93,211,0.15) 0%, transparent 60%)' }} />
        {/* Flowing line artwork */}
        <style>{`
          @keyframes line-draw { from { stroke-dashoffset: 2000; } to { stroke-dashoffset: 0; } }
          @keyframes hero-glow { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }
          .hero-line { stroke-dasharray: 2000; animation: line-draw 3s ease-out forwards; }
          .hero-line-2 { animation-delay: 0.3s; stroke-dashoffset: 2000; }
          .hero-line-3 { animation-delay: 0.6s; stroke-dashoffset: 2000; }
          .hero-line-4 { animation-delay: 0.9s; stroke-dashoffset: 2000; }
        `}</style>
        <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none" viewBox="0 0 1440 800">
          <path className="hero-line" d="M-100 500 C200 380, 500 620, 800 450 S1200 300, 1540 420" stroke="#455DD3" strokeOpacity="0.18" strokeWidth="2" fill="none" />
          <path className="hero-line hero-line-2" d="M-100 550 C300 430, 600 670, 900 500 S1300 350, 1540 470" stroke="#7B93DB" strokeOpacity="0.12" strokeWidth="1.5" fill="none" />
          <path className="hero-line hero-line-3" d="M-100 350 C200 450, 450 280, 700 380 S1050 500, 1540 360" stroke="#455DD3" strokeOpacity="0.10" strokeWidth="1.5" fill="none" />
          <path className="hero-line hero-line-4" d="M-100 600 C350 500, 650 720, 950 560 S1250 420, 1540 520" stroke="#7B93DB" strokeOpacity="0.07" strokeWidth="1" fill="none" />
        </svg>

        <img src="/illustrations/career-progress.svg" alt="" aria-hidden loading="lazy" decoding="async" width={300} height={240} className="absolute left-[-2%] bottom-[8%] w-[240px] sm:w-[300px] opacity-[0.18] pointer-events-none hidden lg:block" />
        <img src="/illustrations/celebration.svg" alt="" aria-hidden loading="lazy" decoding="async" width={240} height={200} className="absolute right-[-1%] top-[12%] w-[200px] sm:w-[240px] opacity-[0.15] pointer-events-none hidden lg:block" />

        <div className="relative max-w-[1080px] mx-auto px-6 pt-[140px] sm:pt-[180px] pb-[60px]">
          <div className="max-w-[680px] mx-auto text-center">
            <Reveal>
              <h1 className="text-white text-[clamp(2.5rem,6vw,64px)] font-bold" style={{ lineHeight: '1', letterSpacing: '-2.125px' }}>
                Your job hunt, <span className="text-[#7DD3CF] sm:whitespace-nowrap">on autopilot.</span>
              </h1>
            </Reveal>
            <Reveal delay={60}>
              <p className="mt-[24px] text-[16px] font-normal leading-[24px] text-white/75 max-w-[480px] mx-auto">
                Upload your resume once. JobHuntin matches, tailors, and auto-applies to hundreds of jobs — every single day.
              </p>
            </Reveal>
            <Reveal delay={120}>
              <div className="mt-[36px] flex flex-wrap gap-[12px] justify-center">
                <Link to="/login" className="group h-[44px] px-[20px] rounded-[10px] text-[16px] font-semibold bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-all duration-300 flex items-center gap-[10px] shadow-lg shadow-[#455DD3]/30 hover:shadow-[#455DD3]/50 hover:scale-[1.02] active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-[#455DD3] focus-visible:ring-offset-2 focus-visible:outline-none">
                  Get started free <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </Link>
                <a href="#how-it-works" aria-label="Scroll to how it works section" className="h-[44px] px-[20px] rounded-[10px] text-[16px] font-semibold border-2 border-white/30 text-white hover:bg-white/10 hover:border-white/50 transition-all duration-300 flex items-center gap-[10px] focus-visible:ring-2 focus-visible:ring-[#455DD3] focus-visible:ring-offset-2 focus-visible:outline-none">
                  See how it works
                </a>
              </div>
            </Reveal>
          </div>
        </div>

        {/* Hero product screenshot — elevated card with subtle depth */}
        <Reveal delay={200}>
          <div className="relative max-w-[900px] mx-auto px-6 pb-[64px]">
            <div className="rounded-[16px] overflow-hidden border border-white/15 shadow-[0_32px_64px_rgba(0,0,0,0.5),0_0_0_1px_rgba(255,255,255,0.05)] hover:shadow-[0_40px_80px_rgba(0,0,0,0.55)] transition-shadow duration-500">
              <div className="bg-white p-[20px] sm:p-[32px]">
                <div className="grid grid-cols-3 gap-[12px] mb-[20px]" role="img" aria-label="Dashboard stats: 127 applied, 23 callbacks, 7 interviews">
                  {[
                    { n: "127", l: "Applied", c: "#2D2A26" },
                    { n: "23", l: "Callbacks", c: "#16A34A" },
                    { n: "7", l: "Interviews", c: "#EA580C" },
                  ].map(s => (
                    <div key={s.l} className="rounded-[10px] p-[12px] sm:p-[16px] bg-[#F7F6F3] transition-transform duration-300 hover:scale-[1.02]">
                      <div className="text-[24px] sm:text-[32px] font-bold leading-none" style={{ color: s.c }}>{s.n}</div>
                      <div className="text-[12px] mt-[6px] text-[#9B9A97] font-medium">{s.l}</div>
                    </div>
                  ))}
                </div>
                {[
                  { role: "Senior Frontend Engineer", co: "Stripe", status: "Interview", sC: "#16A34A", sBg: "#DBEDDB" },
                  { role: "Product Manager", co: "Airbnb", status: "Applied", sC: "#9B9A97", sBg: "#F1F1EF" },
                  { role: "Data Scientist", co: "Netflix", status: "Viewed", sC: "#D9730D", sBg: "#FADEC9" },
                  { role: "UX Designer", co: "Figma", status: "Applied", sC: "#9B9A97", sBg: "#F1F1EF" },
                ].map((r, i) => (
                  <div key={i} className={cn("flex items-center gap-[12px] py-[10px] border-t border-[#F1F1EF] first:border-t-0", i >= 3 && "hidden sm:flex")}>
                    <div className="w-[32px] h-[32px] rounded-[8px] bg-[#F7F6F3] flex items-center justify-center shrink-0"><Briefcase className="w-[14px] h-[14px] text-[#9B9A97]" /></div>
                    <div className="flex-1 min-w-0"><p className="text-[14px] font-medium text-[#2D2A26] truncate">{r.role}</p><p className="text-[12px] text-[#9B9A97]">{r.co}</p></div>
                    <span className="px-[8px] py-[2px] rounded-[4px] text-[12px] font-medium" style={{ background: r.sBg, color: r.sC }}>{r.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>

        {/* Trust bar */}
        <div className="relative max-w-[1080px] mx-auto px-6 pb-[48px]">
          <p className="text-center text-[13px] text-white/45 mb-[16px] uppercase tracking-widest">Trusted by professionals at</p>
          <div className="flex flex-wrap items-center justify-center gap-x-[28px] sm:gap-x-[40px] gap-y-[10px]">
            {["OpenAI", "Figma", "ramp", "Cursor", "Vercel", "NVIDIA", "Discord"].map(n => (
              <span key={n} className="text-[14px] font-semibold text-white/30 tracking-tight hover:text-white/50 transition-colors cursor-default">{n}</span>
            ))}
          </div>
        </div>

      </section>

      {/* ═══════════════════════════════════════════
          AS SEEN IN — trust bar
          ═══════════════════════════════════════════ */}
      <section className="py-8 border-y border-[#E9E9E7]" aria-label="Trusted by job seekers worldwide">
        <div className="max-w-5xl mx-auto px-6">
          <p className="text-center text-sm font-medium text-[#787774] mb-4">Trusted by job seekers from companies like</p>
          <div className="flex flex-wrap items-center justify-center gap-8 opacity-60">
            {['Google', 'Meta', 'Amazon', 'Microsoft', 'Apple', 'Netflix'].map(company => (
              <span key={company} className="text-lg font-bold text-[#2D2A26] tracking-tight">{company}</span>
            ))}
          </div>
          <div className="mt-6 text-center">
            <Link to="/login" className="inline-flex items-center gap-2 h-11 px-6 rounded-xl text-[15px] font-semibold bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-all">
              Start applying free <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FEATURE CARDS — bento with color blocks + illustrations
          ═══════════════════════════════════════════ */}
      <section className="bg-white py-[72px] sm:py-[112px] relative">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#E9E9E7] to-transparent" />
        <div className="max-w-[1080px] mx-auto px-6">
          <Reveal>
            <h2 className="text-[clamp(2rem,4vw,48px)] font-bold text-[#2D2A26] leading-[1] mb-[40px] sm:mb-[56px]" style={{ letterSpacing: '-1.5px' }}>
              Meet your 24/7 application engine.
            </h2>
          </Reveal>

          <div className="grid md:grid-cols-2 gap-[16px]">
            {/* Card: Matching */}
            <Reveal>
              <div className="rounded-[12px] overflow-hidden bg-[#F7F6F3] h-full flex flex-col hover:-translate-y-[2px] transition-transform duration-300">
                <div className="p-[24px] sm:p-[32px] flex-1">
                  <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-[4px]">Matching</p>
                  <h3 className="text-[24px] font-bold text-[#2D2A26] leading-[1.2] mb-[8px]" style={{ letterSpacing: '-0.5px' }}>Precision job matching.</h3>
                  <p className="text-[14px] text-[#787774] leading-[22px]">We scan thousands of listings and surface only the roles that fit your skills, salary, and goals.</p>
                </div>
                <div className="px-[16px] pb-[16px]">
                  <div style={{ background: '#FFB8A0' }} className="rounded-[12px] p-[16px]">
                    <div className="bg-white rounded-[8px] p-[12px] sm:p-[16px] shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                      {[
                        { role: "Sr. Frontend Eng", co: "Stripe", pct: 98 },
                        { role: "Product Manager", co: "Airbnb", pct: 95 },
                        { role: "UX Designer", co: "Figma", pct: 92 },
                      ].map((j, i) => (
                        <div key={j.role} className={cn("flex items-center gap-[8px] py-[8px]", i > 0 && "border-t border-[#F1F1EF]")}>
                          <div className="flex-1 min-w-0"><p className="text-[13px] font-medium text-[#2D2A26] truncate">{j.role}</p><p className="text-[11px] text-[#9B9A97]">{j.co}</p></div>
                          <span className="text-[12px] font-semibold text-[#16A34A]">{j.pct}%</span>
                        </div>
                      ))}
                    </div>
                    <img src="/illustrations/filter.svg" alt="" aria-hidden loading="lazy" className="w-[180px] h-[90px] object-contain mx-auto mt-[16px] opacity-70" />
                  </div>
                </div>
              </div>
            </Reveal>

            {/* Card: Tailoring */}
            <Reveal delay={80}>
              <div className="rounded-[12px] overflow-hidden bg-[#F7F6F3] h-full flex flex-col hover:-translate-y-[2px] transition-transform duration-300">
                <div className="p-[24px] sm:p-[32px] flex-1">
                  <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-[4px]">Tailoring</p>
                  <h3 className="text-[24px] font-bold text-[#2D2A26] leading-[1.2] mb-[8px]" style={{ letterSpacing: '-0.5px' }}>Every resume, custom-built.</h3>
                  <p className="text-[14px] text-[#787774] leading-[22px]">Each application gets a tailored resume — rewritten for the role, ATS-optimized, keyword-matched.</p>
                </div>
                <div className="px-[16px] pb-[16px]">
                  <div style={{ background: '#C2DCC8' }} className="rounded-[12px] p-[16px]">
                    <div className="bg-white rounded-[8px] p-[12px] sm:p-[16px] shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                      <div className="flex items-center justify-between mb-[12px]">
                        <span className="text-[13px] font-medium text-[#2D2A26]">Tailored Resume</span>
                        <span className="flex items-center gap-1 text-[11px] font-medium text-[#16A34A] bg-[#DBEDDB] px-[6px] py-[2px] rounded-[4px]"><TrendingUp className="w-3 h-3" />94%</span>
                      </div>
                      <div className="space-y-[6px]">
                        <div className="h-[14px] rounded-[3px] w-[55%] bg-[#2D2A26]" />
                        <div className="h-[6px] rounded-full w-full bg-[#F1F1EF]" />
                        <div className="h-[6px] rounded-full w-[85%] bg-[#F1F1EF]" />
                        <div className="h-[6px] rounded-full w-[72%] bg-[#F1F1EF]" />
                        <div className="h-px bg-[#F1F1EF] my-[8px]" />
                        <div className="h-[10px] rounded-[3px] w-[40%] bg-[#2D2A26]" />
                        <div className="h-[5px] rounded-full w-full bg-[#F7F6F3]" />
                        <div className="h-[5px] rounded-full w-[88%] bg-[#F7F6F3]" />
                      </div>
                      <div className="flex gap-[4px] mt-[12px]">
                        {["React", "TypeScript", "Node.js", "AWS"].map(t => (
                          <span key={t} className="text-[10px] font-medium px-[6px] py-[2px] rounded-[4px] bg-[#F1F1EF] text-[#787774]">{t}</span>
                        ))}
                      </div>
                    </div>
                    <img src="/illustrations/files-uploading.svg" alt="" aria-hidden loading="lazy" className="w-[160px] h-[80px] object-contain mx-auto mt-[16px] opacity-65" />
                  </div>
                </div>
              </div>
            </Reveal>

            {/* Card: Auto-apply — full-width warm dark */}
            <Reveal delay={160} className="md:col-span-2">
              <div className="rounded-[12px] overflow-hidden bg-[#2D2A26] hover:-translate-y-[2px] transition-transform duration-300">
                <div className="grid md:grid-cols-2">
                  <div className="p-[24px] sm:p-[40px] flex flex-col justify-center">
                    <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-[4px]">Auto-apply</p>
                    <h3 className="text-[24px] sm:text-[32px] font-bold text-white leading-[1.15] mb-[12px]" style={{ letterSpacing: '-1px' }}>Runs 24/7. Even while you sleep.</h3>
                    <p className="text-[14px] sm:text-[16px] text-[#9B9A97] leading-[24px] mb-[24px]">New jobs posted at 2am? On weekends? We apply within minutes. Your agent monitors every board, every day.</p>
                    <div className="flex items-center gap-[16px] text-[14px]">
                      <span className="flex items-center gap-[6px] text-white/50"><span className="w-[6px] h-[6px] rounded-full bg-emerald-400 animate-pulse" />Active now</span>
                      <span className="text-white/20">·</span>
                      <span className="text-white/50">18 applied today</span>
                    </div>
                  </div>
                  <div className="p-[24px] sm:p-[32px] flex items-center relative">
                    <img src="/illustrations/a-moment-to-relax.svg" alt="" aria-hidden loading="lazy" className="relative z-10 w-[200px] sm:w-[260px] mx-auto opacity-30" />
                    <div className="absolute inset-0 flex items-end p-[24px] pointer-events-none">
                      <div className="w-full bg-white/5 rounded-[8px] p-[16px]">
                        <div className="flex items-end gap-[4px] h-[80px]">
                          {[35, 52, 44, 68, 58, 85, 72, 90, 65, 78, 95, 82].map((h, i) => (
                            <div key={i} className="flex-1 rounded-t-[2px]" style={{ height: `${h}%`, background: `rgba(69,93,211,${0.3 + h / 250})` }} />
                          ))}
                        </div>
                        <div className="flex justify-between mt-[4px] text-[9px] text-white/20">
                          {["M","T","W","T","F","S","S","M","T","W","T","F"].map((d, i) => <span key={i}>{d}</span>)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          HOW IT WORKS — with illustrations
          ═══════════════════════════════════════════ */}
      <section id="how-it-works" className="bg-[#F7F6F3] py-[64px] sm:py-[96px]">
        <div className="max-w-[1080px] mx-auto px-6">
          <Reveal>
            <div className="text-center max-w-[520px] mx-auto mb-[48px] sm:mb-[64px]">
              <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-[8px]">How it works</p>
              <h2 className="text-[clamp(2rem,4vw,48px)] font-bold text-[#2D2A26] leading-[1]" style={{ letterSpacing: '-1.5px' }}>
                Set up in two minutes.
              </h2>
            </div>
          </Reveal>

          <div className="grid sm:grid-cols-3 gap-[16px]">
            {[
              { n: "01", title: "Upload your resume", desc: "Just drop it in. We parse skills, experience, and preferences — no forms.", bg: "#FADEC9", illus: "/illustrations/files-uploading.svg" },
              { n: "02", title: "Set your preferences", desc: "Target roles, salary, location, remote — we only apply to jobs you'd want.", bg: "#C2DCC8", illus: "/illustrations/filter.svg" },
              { n: "03", title: "We handle the rest", desc: "Sit back. We tailor, apply, and track. You show up to interviews.", bg: "#D3E5EF", illus: "/illustrations/beach-day.svg" },
            ].map((step, i) => (
              <Reveal key={step.n} delay={i * 80}>
                <div className="rounded-[12px] overflow-hidden bg-white h-full flex flex-col hover:-translate-y-[2px] transition-transform duration-300">
                  <div className="p-[24px] flex-1">
                    <div className="text-[36px] font-bold text-[#9B9A97] leading-none mb-[16px]">{step.n}</div>
                    <h3 className="text-[18px] font-bold text-[#2D2A26] leading-[1.3] mb-[6px]">{step.title}</h3>
                    <p className="text-[14px] text-[#787774] leading-[22px]">{step.desc}</p>
                  </div>
                  <div className="px-[12px] pb-[12px]">
                    <div className="rounded-[8px] p-[20px] flex items-center justify-center" style={{ background: step.bg }}>
                      <img src={step.illus} alt="" aria-hidden loading="lazy" className="w-[160px] h-[110px] object-contain" />
                    </div>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>

          <Reveal delay={300}>
            <div className="text-center mt-[40px]">
              <Link to="/login" className="inline-flex items-center gap-[8px] h-[36px] px-[16px] rounded-[8px] text-[16px] font-medium bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-colors focus-visible:ring-2 focus-visible:ring-[#455DD3] focus-visible:ring-offset-2 focus-visible:outline-none">
                Get started free <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="mt-[12px] text-[14px] text-[#9B9A97]">20 free applications per week. No credit card.</p>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          USER JOURNEY — animated story
          ═══════════════════════════════════════════ */}
      <UserJourneySection />

      {/* ═══════════════════════════════════════════
          PULL QUOTE — with illustration
          ═══════════════════════════════════════════ */}
      <section className="bg-white py-[80px] sm:py-[120px]">
        <div className="max-w-[720px] mx-auto px-6 text-center relative">
          <img src="/illustrations/appreciate-it.svg" alt="" aria-hidden loading="lazy" className="absolute left-0 top-[50%] -translate-x-full -translate-y-1/2 w-[140px] opacity-[0.12] pointer-events-none hidden xl:block" />
          <Reveal>
            <blockquote className="text-[clamp(1.25rem,3vw,28px)] font-medium text-[#2D2A26] leading-[1.4]" style={{ letterSpacing: '-0.5px' }}>
              "That first week I literally did nothing and got 4 interview callbacks. This changed how I think about job hunting."
            </blockquote>
            <div className="mt-[32px] flex items-center justify-center gap-[12px]">
              <div className="w-[40px] h-[40px] rounded-full bg-gradient-to-br from-[#FFB8A0] to-[#F5886A] flex items-center justify-center text-[14px] font-bold text-white">SK</div>
              <div className="text-left">
                <p className="text-[14px] font-medium text-[#2D2A26]">Sarah K.</p>
                <p className="text-[12px] text-[#9B9A97]">Marketing Manager · Now at HubSpot</p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FEATURES LIST
          ═══════════════════════════════════════════ */}
      <section id="features" className="bg-[#F7F6F3] py-[80px] sm:py-[100px]">
        <div className="max-w-[1080px] mx-auto px-6">
          <Reveal>
            <h2 className="text-[clamp(2rem,4vw,48px)] font-bold text-[#2D2A26] leading-[1] mb-[40px]" style={{ letterSpacing: '-1.5px' }}>
              Everything you need.
            </h2>
          </Reveal>
          <Reveal delay={80}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-[8px]">
              {["Smart resume analysis", "Custom cover letters", "ATS optimization", "Thousands of positions", "Real-time tracking", "Interview prep", "Salary filtering", "Role matching engine", "Auto-apply engine", "Resume versioning", "Data encryption", "Priority support"].map(f => (
                <div key={f} className="flex items-center gap-[8px] px-[12px] py-[10px] rounded-[8px] bg-white hover:bg-[#EDECE9] transition-colors">
                  <Check className="w-[14px] h-[14px] text-[#16A34A] shrink-0" />
                  <span className="text-[14px] text-[#2D2A26]">{f}</span>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          TESTIMONIALS
          ═══════════════════════════════════════════ */}
      <TestimonialsSection />

      {/* ═══════════════════════════════════════════
          FAQ
          ═══════════════════════════════════════════ */}
      <section>
        <FAQAccordion items={[
          { question: "Is JobHuntin free?", answer: "Yes. JobHuntin offers a free plan with 20 applications per week. No credit card required. You can upgrade for more applications and premium features when you're ready." },
          { question: "How does the AI auto-apply work?", answer: "You upload your resume and set your preferences (role, salary, location). Our AI matches you to relevant jobs, tailors your resume and cover letter for each application, and submits them automatically. You can track everything in your dashboard." },
          { question: "Is it safe to use auto-apply tools?", answer: "Yes. JobHuntin uses secure connections and encrypts your data. We only apply to jobs you've approved through your preferences, and you maintain full control over your applications and profile." },
          { question: "How many jobs can JobHuntin apply to per day?", answer: "On the free plan, you get 20 applications per week. Paid plans support hundreds of applications per day, depending on your subscription. Our system runs 24/7 to catch new postings as they go live." },
          { question: "Does JobHuntin work with LinkedIn and Indeed?", answer: "JobHuntin integrates with major job boards including LinkedIn, Indeed, and many others. We aggregate listings from thousands of sources so you can apply across platforms from one dashboard." },
        ]} />
      </section>

      {/* ═══════════════════════════════════════════
          EXPLORE MORE — internal links
          ═══════════════════════════════════════════ */}
      <section className="py-16 sm:py-20 bg-white">
        <div className="max-w-[1080px] mx-auto px-6">
          <h2 className="text-[clamp(1.5rem,3vw,28px)] font-bold text-[#2D2A26] text-center mb-10 sm:mb-12" style={{ letterSpacing: '-0.5px' }}>
            Explore More
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-8 sm:gap-8 lg:gap-8 justify-items-center sm:justify-items-start">
            {[
              { label: 'Compare Tools', links: [{ text: 'vs LazyApply', to: '/vs/lazyapply' }, { text: 'vs Jobright', to: '/vs/jobright' }, { text: 'vs Simplify', to: '/vs/simplify' }, { text: 'vs Teal', to: '/vs/teal' }] },
              { label: 'Guides', links: [{ text: 'Beat ATS with AI', to: '/guides/how-to-beat-ats-with-ai' }, { text: 'Resume Tailoring', to: '/guides/resume-tailoring-guide' }, { text: 'Cover Letter Mastery', to: '/guides/ai-cover-letter-mastery' }, { text: 'All Guides', to: '/guides' }] },
              { label: 'Topics', links: [{ text: 'Remote Work', to: '/topics/remote-work' }, { text: 'ATS Optimization', to: '/topics/ats-optimization' }, { text: 'Salary Negotiation', to: '/topics/salary-negotiation' }, { text: 'All Topics', to: '/blog' }] },
              { label: 'Tools', links: [{ text: 'AI Resume Tailor', to: '/tools' }, { text: 'ATS Score Checker', to: '/tools' }, { text: 'Cover Letter Gen', to: '/tools' }, { text: 'All Free Tools', to: '/tools' }] },
            ].map(section => (
              <div key={section.label} className="min-w-0 w-full sm:w-auto flex flex-col items-center sm:items-start">
                <h3 className="text-[12px] font-semibold text-[#9B9A97] uppercase tracking-wider mb-4">{section.label}</h3>
                <ul className="space-y-3 text-center sm:text-left">
                  {section.links.map(link => (
                    <li key={link.text}>
                      <Link to={link.to} className="text-[14px] sm:text-[15px] text-[#2D2A26] hover:text-[#455DD3] font-medium transition-colors block">
                        {link.text}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FINAL CTA — with illustration
          ═══════════════════════════════════════════ */}
      <section className="bg-[#2D2A26] py-[80px] sm:py-[120px] relative overflow-hidden">
        <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none" viewBox="0 0 1440 600">
          <path d="M-80 350 C300 250, 600 450, 900 300 S1200 180, 1520 280" stroke="white" strokeOpacity="0.03" strokeWidth="1.5" fill="none" />
          <path d="M-80 200 C300 300, 600 150, 900 250 S1200 350, 1520 230" stroke="white" strokeOpacity="0.02" strokeWidth="1" fill="none" />
        </svg>
        <img src="/illustrations/beach-day.svg" alt="" aria-hidden loading="lazy" className="absolute right-[-2%] bottom-[5%] w-[200px] opacity-[0.06] pointer-events-none hidden lg:block" />

        <div className="relative max-w-[1080px] mx-auto px-6 z-10">
          <Reveal>
            <div className="max-w-[480px] mx-auto text-center">
              <h2 className="text-[clamp(2rem,4vw,48px)] font-bold text-white leading-[1] mb-[16px]" style={{ letterSpacing: '-1.5px' }}>
                Your next role is one upload away.
              </h2>
              <p className="text-[16px] text-[#9B9A97] leading-[24px] mb-[32px]">Stop applying manually. Join thousands who've reclaimed their time.</p>
              <div className="w-full max-w-[420px] mx-auto px-2 sm:px-0">
                <EmailForm variant="dark" />
              </div>
              <div className="mt-[24px] flex flex-wrap items-center justify-center gap-x-[20px] gap-y-[6px] text-[14px] text-[#787774]">
                {["Free plan", "No credit card", "Cancel anytime"].map(t => (
                  <span key={t} className="flex items-center gap-[6px]"><Check className="w-[14px] h-[14px] text-emerald-500" />{t}</span>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <div ref={footerSentinelRef} className="h-px w-full" aria-hidden />

      {stickyVisible && (
        <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-white/95 backdrop-blur-md border-t border-[#E3E2E0] p-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-[0_-4px_20px_rgba(0,0,0,0.06)]">
          <Link to="/login" className="flex items-center justify-center gap-2 w-full min-h-[44px] rounded-[8px] text-[16px] font-medium bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-colors active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-[#455DD3] focus-visible:ring-offset-2 focus-visible:outline-none">
            Start applying free <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </>
  );
}
