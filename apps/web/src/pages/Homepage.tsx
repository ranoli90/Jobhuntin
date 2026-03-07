import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import { telemetry } from '../lib/telemetry';
import { ArrowRight, MailCheck, Check, Briefcase, TrendingUp } from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { TestimonialsSection } from '../components/TestimonialsSection';
import { cn } from '../lib/utils';
import { ValidationUtils } from '../lib/validation';

/* ────────────────────────────────────────────────────────
   Design tokens — consistent system, not ad-hoc values
   ──────────────────────────────────────────────────────── */
const color = {
  ink: '#191919',
  body: '#555',
  muted: '#999',
  border: '#E8E4DF',
  cream: '#FFFCF8',
  white: '#FFFFFF',
  blue: '#4A6CF7',
  blueHover: '#3B5DE8',
  coral: '#FFB8A0',
  coralDark: '#F5A088',
  sage: '#C2DCC8',
  amber: '#FFD6A0',
  skyBg: '#EEF4FF',
};

/* ────────────────────────────────────────────────────────
   Hero background artwork — flowing curves like Notion
   ──────────────────────────────────────────────────────── */
function HeroArtwork() {
  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none" viewBox="0 0 1440 900" fill="none">
      <path d="M-80 600C200 500 400 700 720 550S1100 350 1520 480" stroke={color.coral} strokeOpacity="0.2" strokeWidth="2" />
      <path d="M-80 650C250 550 500 750 800 600S1150 400 1520 530" stroke={color.sage} strokeOpacity="0.15" strokeWidth="1.5" />
      <path d="M-80 320C200 400 500 250 760 360S1080 500 1520 380" stroke={color.blue} strokeOpacity="0.08" strokeWidth="1.5" />
      <circle cx="200" cy="250" r="180" fill={color.coral} fillOpacity="0.04" />
      <circle cx="1200" cy="600" r="220" fill={color.blue} fillOpacity="0.03" />
    </svg>
  );
}

/* ────────────────────────────────────────────────────────
   Email capture hook
   ──────────────────────────────────────────────────────── */
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

function EmailForm({ variant = "light" }: { variant?: "light" | "dark" }) {
  const { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit } = useEmailCapture();
  const dark = variant === "dark";

  if (sentEmail) {
    return (
      <div className="flex items-center gap-4 p-5 rounded-[16px] bg-emerald-50 border border-emerald-200">
        <MailCheck className="w-6 h-6 text-emerald-600 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-[#191919]">Check your inbox</p>
          <p className="text-xs text-[#999] mt-0.5 truncate">{sentEmail}</p>
        </div>
        <button onClick={() => setSentEmail(null)} className="text-xs font-semibold text-emerald-700 hover:underline">Change</button>
      </div>
    );
  }

  return (
    <div>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3">
        <input type="email" placeholder="you@example.com" aria-label="Email address"
          className={cn(
            "flex-1 h-[52px] px-5 rounded-[10px] text-[15px] transition-all outline-none",
            dark
              ? "bg-white/10 border border-white/20 text-white placeholder:text-white/40 focus:border-white/50 focus:ring-2 focus:ring-white/10"
              : "bg-white border border-[#E8E4DF] text-[#191919] placeholder:text-[#BBB] focus:border-[#4A6CF7] focus:ring-2 focus:ring-[#4A6CF7]/10 shadow-[0_1px_3px_rgba(0,0,0,0.04)]",
            emailError && "!border-red-400"
          )}
          value={email} onChange={e => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button type="submit" disabled={isSubmitting}
          className={cn(
            "h-[52px] px-7 rounded-[10px] text-[15px] font-semibold flex items-center justify-center gap-2 whitespace-nowrap transition-all disabled:opacity-50",
            dark
              ? "bg-white text-[#191919] hover:bg-white/90 shadow-[0_2px_8px_rgba(255,255,255,0.1)]"
              : "bg-[#4A6CF7] text-white hover:bg-[#3B5DE8] shadow-[0_2px_8px_rgba(74,108,247,0.3)] hover:shadow-[0_4px_16px_rgba(74,108,247,0.35)] hover:-translate-y-px active:translate-y-0"
          )}
        >
          {isSubmitting ? "Sending…" : "Get started free"} {!isSubmitting && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>
      {emailError && <p className="mt-2 text-xs text-red-500 pl-1">{emailError}</p>}
    </div>
  );
}

/* ────────────────────────────────────────────────────────
   Scroll reveal
   ──────────────────────────────────────────────────────── */
function Reveal({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [vis, setVis] = useState(false);
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  useEffect(() => {
    if (reduced) { setVis(true); return; }
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); obs.disconnect(); } }, { threshold: 0.1 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [reduced]);
  return (
    <div ref={ref}
      className={cn(reduced ? "" : "transition-all duration-[800ms] ease-[cubic-bezier(0.16,1,0.3,1)]", vis ? "opacity-100 translate-y-0" : (reduced ? "" : "opacity-0 translate-y-6"), className)}
      style={{ transitionDelay: reduced ? '0ms' : `${delay}ms` }}
    >{children}</div>
  );
}

/* ────────────────────────────────────────────────────────
   Animated counter (fires when visible)
   ──────────────────────────────────────────────────────── */
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
    const dur = 1400, t0 = Date.now();
    const tick = () => { const p = Math.min((Date.now() - t0) / dur, 1); setVal(Math.round((1 - Math.pow(1 - p, 3)) * to)); if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  }, [go, to]);
  return <span ref={ref}>{val.toLocaleString()}{suffix}</span>;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   PAGE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
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
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#191919] focus:text-white focus:rounded-lg">Skip to main content</a>

      <SEO title="JobHuntin — The Application Engine That Runs While You Sleep" description="Upload your resume. Our platform tailors every application and submits to hundreds of jobs daily. More interviews, zero effort." ogTitle="JobHuntin — The Application Engine That Runs While You Sleep" canonicalUrl="https://jobhuntin.com/" schema={{ "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }, "description": "Automated system that tailors and submits job applications." }} />

      {/* ══════════════════════════════════════════════════
          HERO
          ══════════════════════════════════════════════════ */}
      <section id="main-content" className="relative overflow-hidden" style={{ background: color.cream }}>
        <HeroArtwork />

        <div className="relative max-w-[1120px] mx-auto px-6 pt-[140px] sm:pt-[180px] pb-[80px] sm:pb-[100px]">
          <div className="max-w-[720px] mx-auto text-center">
            <Reveal>
              <h1 className="font-display text-[clamp(3rem,7vw,5.25rem)] leading-[1.05] tracking-[-0.025em]" style={{ color: color.ink }}>
                Your job hunt,<br />
                <span className="italic">on autopilot.</span>
              </h1>
            </Reveal>
            <Reveal delay={80}>
              <p className="mt-6 text-[18px] sm:text-[20px] leading-[1.65] max-w-[520px] mx-auto" style={{ color: color.body }}>
                Upload your resume once. JobHuntin matches, tailors, and auto-applies to hundreds of jobs — every single day.
              </p>
            </Reveal>
            <Reveal delay={160}>
              <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
                <Link to="/login" className="h-[52px] px-8 rounded-[10px] text-[15px] font-semibold bg-[#4A6CF7] text-white hover:bg-[#3B5DE8] shadow-[0_2px_8px_rgba(74,108,247,0.3)] hover:shadow-[0_6px_20px_rgba(74,108,247,0.35)] hover:-translate-y-px active:translate-y-0 transition-all flex items-center justify-center gap-2">
                  Get started free <ArrowRight className="w-4 h-4" />
                </Link>
                <a href="#how-it-works" className="h-[52px] px-8 rounded-[10px] text-[15px] font-semibold border border-[#E8E4DF] text-[#555] hover:border-[#D0CCC6] hover:bg-white/60 transition-all flex items-center justify-center gap-2">
                  See how it works
                </a>
              </div>
            </Reveal>
          </div>
        </div>

        {/* Hero product screenshot */}
        <Reveal delay={280}>
          <div className="relative max-w-[960px] mx-auto px-6 pb-[60px]">
            <div className="rounded-[20px] shadow-[0_25px_60px_-12px_rgba(0,0,0,0.12)] border border-[#E8E4DF]/60 overflow-hidden bg-white">
              <div className="flex items-center h-[44px] px-4 bg-[#FAFAF8] border-b border-[#F0EDE8]">
                <div className="flex gap-[6px]"><div className="w-[10px] h-[10px] rounded-full bg-[#E8E4DF]" /><div className="w-[10px] h-[10px] rounded-full bg-[#E8E4DF]" /><div className="w-[10px] h-[10px] rounded-full bg-[#E8E4DF]" /></div>
                <div className="ml-4 flex-1 max-w-[280px] h-[28px] bg-white rounded-[6px] border border-[#E8E4DF] flex items-center px-3"><span className="text-[11px] text-[#BBB]">app.jobhuntin.com</span></div>
              </div>
              <div className="p-5 sm:p-8">
                <div className="grid grid-cols-3 gap-4 sm:gap-5 mb-6">
                  {[
                    { n: "127", l: "Applied this week", bg: "#FFFCF8", c: color.ink },
                    { n: "23", l: "Responses", bg: "#F0FAF4", c: "#16A34A" },
                    { n: "7", l: "Interviews", bg: "#FFF7ED", c: "#EA580C" },
                  ].map(s => (
                    <div key={s.l} className="rounded-[12px] p-4 sm:p-5" style={{ background: s.bg }}>
                      <div className="text-[28px] sm:text-[36px] font-bold leading-none" style={{ color: s.c }}>{s.n}</div>
                      <div className="text-[12px] sm:text-[13px] mt-2 font-medium" style={{ color: color.muted }}>{s.l}</div>
                    </div>
                  ))}
                </div>
                <div>
                  {[
                    { role: "Senior Frontend Engineer", co: "Stripe", time: "2h ago", status: "Interview", sBg: "#F0FAF4", sColor: "#16A34A" },
                    { role: "Product Manager", co: "Airbnb", time: "4h ago", status: "Applied", sBg: "#F5F3F0", sColor: "#888" },
                    { role: "Data Scientist", co: "Netflix", time: "6h ago", status: "Viewed", sBg: "#FFF7ED", sColor: "#EA580C" },
                    { role: "UX Designer", co: "Figma", time: "8h ago", status: "Applied", sBg: "#F5F3F0", sColor: "#888" },
                  ].map((r, i) => (
                    <div key={i} className="flex items-center gap-4 py-[14px] border-t border-[#F0EDE8] first:border-t-0">
                      <div className="w-[40px] h-[40px] rounded-[10px] bg-[#F5F3F0] flex items-center justify-center shrink-0"><Briefcase className="w-[16px] h-[16px] text-[#BBB]" /></div>
                      <div className="flex-1 min-w-0"><p className="text-[14px] font-semibold text-[#191919] truncate">{r.role}</p><p className="text-[12px] text-[#999]">{r.co}</p></div>
                      <span className="text-[12px] text-[#BBB] hidden sm:block">{r.time}</span>
                      <span className="px-[10px] py-[4px] rounded-[8px] text-[11px] font-semibold shrink-0" style={{ background: r.sBg, color: r.sColor }}>{r.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* ══════════════════════════════════════════════════
          TRUST
          ══════════════════════════════════════════════════ */}
      <section className="bg-white border-b border-[#F0EDE8] py-[48px]">
        <div className="max-w-[1120px] mx-auto px-6">
          <p className="text-center text-[13px] font-medium tracking-[0.06em] uppercase mb-[32px]" style={{ color: color.muted }}>People hired at leading companies</p>
          <div className="flex flex-wrap items-center justify-center gap-x-[48px] sm:gap-x-[64px] gap-y-[16px]">
            {["Google", "Amazon", "Stripe", "Airbnb", "Shopify", "Netflix", "Meta", "Figma"].map(n => (
              <span key={n} className="text-[16px] font-semibold tracking-[-0.01em]" style={{ color: '#D0CCC6' }}>{n}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════
          FEATURE CARDS — bold color blocks, real UI
          ══════════════════════════════════════════════════ */}
      <section className="bg-white py-[96px] sm:py-[128px]">
        <div className="max-w-[1120px] mx-auto px-6">
          <Reveal>
            <h2 className="text-[clamp(2rem,4.5vw,3.25rem)] font-bold tracking-[-0.02em] leading-[1.1] mb-[64px] max-w-[600px]" style={{ color: color.ink }}>
              Meet your 24/7 application engine.
            </h2>
          </Reveal>

          <div className="grid md:grid-cols-2 gap-[20px]">
            {/* Card: Matching — coral */}
            <Reveal delay={0}>
              <div className="rounded-[20px] overflow-hidden border border-[#F0EDE8] shadow-[0_4px_16px_rgba(0,0,0,0.04)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.08)] transition-shadow duration-300 h-full flex flex-col">
                <div className="p-[32px] sm:p-[40px] flex-1">
                  <p className="text-[13px] font-semibold tracking-[0.05em] uppercase mb-[8px]" style={{ color: color.muted }}>Matching</p>
                  <h3 className="text-[24px] sm:text-[28px] font-bold leading-[1.2] mb-[12px]" style={{ color: color.ink }}>Precision job matching.</h3>
                  <p className="text-[15px] leading-[1.65]" style={{ color: color.body }}>We scan thousands of listings and surface only the roles that fit your skills, salary, and goals.</p>
                </div>
                <div className="px-[24px] sm:px-[32px] pb-[24px] sm:pb-[32px]">
                  <div className="rounded-[12px] overflow-hidden" style={{ background: color.coral }}>
                    <div className="bg-white rounded-[12px] m-[16px] sm:m-[20px] p-[16px] sm:p-[20px] shadow-[0_8px_24px_rgba(0,0,0,0.06)]">
                      {[
                        { role: "Sr. Frontend Eng", co: "Stripe", pct: 98 },
                        { role: "Product Manager", co: "Airbnb", pct: 95 },
                        { role: "UX Designer", co: "Figma", pct: 92 },
                      ].map(j => (
                        <div key={j.role} className="flex items-center gap-3 py-[10px] border-b border-[#F0EDE8] last:border-b-0">
                          <div className="flex-1 min-w-0"><p className="text-[13px] font-semibold text-[#191919] truncate">{j.role}</p><p className="text-[11px] text-[#999]">{j.co}</p></div>
                          <div className="w-[48px] h-[20px] rounded-full bg-[#F0FAF4] flex items-center justify-center"><span className="text-[11px] font-bold text-[#16A34A]">{j.pct}%</span></div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </Reveal>

            {/* Card: Tailoring — sage */}
            <Reveal delay={100}>
              <div className="rounded-[20px] overflow-hidden border border-[#F0EDE8] shadow-[0_4px_16px_rgba(0,0,0,0.04)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.08)] transition-shadow duration-300 h-full flex flex-col">
                <div className="p-[32px] sm:p-[40px] flex-1">
                  <p className="text-[13px] font-semibold tracking-[0.05em] uppercase mb-[8px]" style={{ color: color.muted }}>Tailoring</p>
                  <h3 className="text-[24px] sm:text-[28px] font-bold leading-[1.2] mb-[12px]" style={{ color: color.ink }}>Every resume, custom-built.</h3>
                  <p className="text-[15px] leading-[1.65]" style={{ color: color.body }}>Each application gets a tailored resume — rewritten for the role, ATS-optimized, keyword-matched.</p>
                </div>
                <div className="px-[24px] sm:px-[32px] pb-[24px] sm:pb-[32px]">
                  <div className="rounded-[12px] overflow-hidden" style={{ background: color.sage }}>
                    <div className="bg-white rounded-[12px] m-[16px] sm:m-[20px] p-[16px] sm:p-[20px] shadow-[0_8px_24px_rgba(0,0,0,0.06)]">
                      <div className="flex items-center justify-between mb-[16px]">
                        <span className="text-[13px] font-semibold text-[#191919]">Tailored Resume</span>
                        <span className="flex items-center gap-1 text-[11px] font-semibold text-[#16A34A] bg-[#F0FAF4] px-[8px] py-[3px] rounded-[6px]"><TrendingUp className="w-3 h-3" /> ATS 94%</span>
                      </div>
                      <div className="space-y-[8px]">
                        <div className="h-[18px] rounded-[4px] w-[55%]" style={{ background: color.ink }} />
                        <div className="h-[8px] rounded-full w-full bg-[#F0EDE8]" />
                        <div className="h-[8px] rounded-full w-[85%] bg-[#F0EDE8]" />
                        <div className="h-[8px] rounded-full w-[75%] bg-[#F0EDE8]" />
                        <div className="h-px bg-[#F0EDE8] my-[12px]" />
                        <div className="h-[14px] rounded-[4px] w-[40%]" style={{ background: '#333' }} />
                        <div className="h-[6px] rounded-full w-full bg-[#F5F3F0]" />
                        <div className="h-[6px] rounded-full w-[90%] bg-[#F5F3F0]" />
                      </div>
                      <div className="flex gap-[6px] mt-[16px]">
                        {["React", "TypeScript", "Node.js", "AWS"].map(t => (
                          <span key={t} className="text-[10px] font-semibold px-[8px] py-[3px] rounded-[6px] bg-[#F5F3F0] text-[#888]">{t}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Reveal>

            {/* Card: Auto-apply — dark, full width */}
            <Reveal delay={200} className="md:col-span-2">
              <div className="rounded-[20px] overflow-hidden shadow-[0_4px_16px_rgba(0,0,0,0.04)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.08)] transition-shadow duration-300" style={{ background: color.ink }}>
                <div className="grid md:grid-cols-2 gap-0">
                  <div className="p-[32px] sm:p-[48px] flex flex-col justify-center">
                    <p className="text-[13px] font-semibold tracking-[0.05em] uppercase mb-[8px] text-[#666]">Auto-apply</p>
                    <h3 className="text-[24px] sm:text-[32px] font-bold leading-[1.2] mb-[16px] text-white">Runs 24/7. Even while you sleep.</h3>
                    <p className="text-[15px] sm:text-[16px] leading-[1.65] text-[#888] mb-[32px]">New jobs posted at 2am? On weekends? We apply within minutes. Your agent monitors every board, every day, every hour.</p>
                    <div className="flex items-center gap-[24px] text-[14px]">
                      <span className="flex items-center gap-[8px] text-white/60"><span className="w-[8px] h-[8px] rounded-full bg-emerald-400 animate-pulse" /> Active now</span>
                      <span className="text-white/30">·</span>
                      <span className="text-white/60">18 applied today</span>
                      <span className="text-white/30">·</span>
                      <span className="text-white/60">127 this week</span>
                    </div>
                  </div>
                  <div className="p-[24px] sm:p-[32px] flex items-center justify-center">
                    <div className="w-full rounded-[12px] p-[20px] sm:p-[24px]" style={{ background: 'rgba(255,255,255,0.06)' }}>
                      <div className="flex items-end gap-[6px] h-[100px] sm:h-[120px]">
                        {[35, 52, 44, 68, 58, 85, 72, 90, 65, 78, 95, 82].map((h, i) => (
                          <div key={i} className="flex-1 rounded-t-[3px] transition-all duration-500" style={{ height: `${h}%`, background: `rgba(74,108,247,${0.3 + (h / 200)})` }} />
                        ))}
                      </div>
                      <div className="flex justify-between mt-[8px] text-[10px] font-medium text-white/30">
                        {["M","T","W","T","F","S","S","M","T","W","T","F"].map((d, i) => <span key={i}>{d}</span>)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════
          HOW IT WORKS
          ══════════════════════════════════════════════════ */}
      <section id="how-it-works" className="py-[96px] sm:py-[128px] border-y border-[#F0EDE8]" style={{ background: color.cream }}>
        <div className="max-w-[1120px] mx-auto px-6">
          <Reveal>
            <div className="text-center max-w-[560px] mx-auto mb-[64px] sm:mb-[80px]">
              <p className="text-[13px] font-semibold tracking-[0.05em] uppercase mb-[12px]" style={{ color: color.muted }}>How it works</p>
              <h2 className="text-[clamp(2rem,4.5vw,3.25rem)] font-bold tracking-[-0.02em] leading-[1.1]" style={{ color: color.ink }}>
                Set up in two minutes.{' '}
                <span className="font-display italic font-normal" style={{ color: '#999' }}>Then relax.</span>
              </h2>
            </div>
          </Reveal>

          <div className="grid sm:grid-cols-3 gap-[20px]">
            {[
              { n: "01", title: "Upload your resume", desc: "Just drop it in. We parse skills, experience, and preferences — you don't fill out a single form.", bg: "#FFF7ED", border: "#F5DCC4" },
              { n: "02", title: "Set your preferences", desc: "Target roles, salary range, location, remote — we only apply to jobs you'd actually want.", bg: "#F0FAF4", border: "#C2E0CC" },
              { n: "03", title: "We handle the rest", desc: "Sit back. We tailor, apply, and track responses. You just show up to interviews.", bg: "#EEF4FF", border: "#C4D6F7" },
            ].map((step, i) => (
              <Reveal key={step.n} delay={i * 100}>
                <div className="rounded-[20px] p-[32px] sm:p-[40px] h-full border" style={{ background: step.bg, borderColor: step.border }}>
                  <div className="font-display text-[56px] leading-none italic mb-[24px]" style={{ color: `${color.ink}08` }}>{step.n}</div>
                  <h3 className="text-[20px] font-bold leading-[1.3] mb-[8px]" style={{ color: color.ink }}>{step.title}</h3>
                  <p className="text-[15px] leading-[1.65]" style={{ color: color.body }}>{step.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>

          <Reveal delay={400}>
            <div className="text-center mt-[48px]">
              <Link to="/login" className="inline-flex items-center gap-2 h-[52px] px-8 rounded-[10px] text-[15px] font-semibold bg-[#4A6CF7] text-white hover:bg-[#3B5DE8] shadow-[0_2px_8px_rgba(74,108,247,0.3)] hover:shadow-[0_6px_20px_rgba(74,108,247,0.35)] hover:-translate-y-px active:translate-y-0 transition-all">
                Get started free <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="mt-[16px] text-[14px]" style={{ color: color.muted }}>20 applications per week. No credit card.</p>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════
          NUMBERS
          ══════════════════════════════════════════════════ */}
      <section className="py-[96px] sm:py-[128px]" style={{ background: color.ink }}>
        <div className="max-w-[1120px] mx-auto px-6">
          <Reveal>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-[32px] sm:gap-[48px]">
              {[
                { to: 500000, suffix: "+", label: "Applications sent" },
                { to: 10000, suffix: "+", label: "Jobs landed" },
                { to: 3, suffix: ".2x", label: "More interviews" },
                { to: 94, suffix: "%", label: "Avg. ATS score" },
              ].map(s => (
                <div key={s.label} className="text-center">
                  <div className="text-[clamp(2rem,5vw,3.5rem)] font-bold tracking-[-0.02em] text-white mb-[8px]"><Counter to={s.to} suffix={s.suffix} /></div>
                  <div className="text-[13px] font-medium text-[#666]">{s.label}</div>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════
          PULL QUOTE
          ══════════════════════════════════════════════════ */}
      <section className="bg-white py-[96px] sm:py-[128px]">
        <div className="max-w-[800px] mx-auto px-6 text-center">
          <Reveal>
            <div className="font-display text-[80px] sm:text-[100px] leading-none italic mb-[16px] select-none" style={{ color: '#F0EDE8' }}>"</div>
            <blockquote className="text-[clamp(1.5rem,3.5vw,2.25rem)] font-medium leading-[1.35] tracking-[-0.01em]" style={{ color: color.ink }}>
              That first week I literally did nothing and got 4 interview callbacks. This changed how I think about job hunting.
            </blockquote>
            <div className="mt-[40px] flex items-center justify-center gap-[16px]">
              <div className="w-[48px] h-[48px] rounded-full bg-gradient-to-br from-[#FFB8A0] to-[#F5886A] flex items-center justify-center text-[14px] font-bold text-white">SK</div>
              <div className="text-left">
                <p className="text-[15px] font-semibold" style={{ color: color.ink }}>Sarah K.</p>
                <p className="text-[13px]" style={{ color: color.muted }}>Marketing Manager · Now at HubSpot</p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════
          FEATURE LIST
          ══════════════════════════════════════════════════ */}
      <section id="features" className="py-[96px] sm:py-[128px] border-y border-[#F0EDE8]" style={{ background: color.cream }}>
        <div className="max-w-[1120px] mx-auto px-6">
          <Reveal>
            <div className="text-center max-w-[480px] mx-auto mb-[48px] sm:mb-[64px]">
              <h2 className="text-[clamp(2rem,4.5vw,3.25rem)] font-bold tracking-[-0.02em] leading-[1.1]" style={{ color: color.ink }}>
                Everything you need.
              </h2>
            </div>
          </Reveal>
          <Reveal delay={100}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-[12px]">
              {["Smart resume analysis", "Custom cover letters", "ATS optimization", "Thousands of positions", "Real-time tracking", "Interview prep insights", "Personalized applications", "Salary filtering", "Role matching engine", "Auto-apply engine", "Resume versioning", "Data encryption"].map(f => (
                <div key={f} className="flex items-center gap-[12px] px-[16px] py-[14px] rounded-[12px] bg-white border border-[#F0EDE8] hover:border-[#E0DCD6] hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)] transition-all">
                  <Check className="w-[16px] h-[16px] shrink-0" style={{ color: '#16A34A' }} />
                  <span className="text-[14px] font-medium" style={{ color: '#555' }}>{f}</span>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════
          TESTIMONIALS
          ══════════════════════════════════════════════════ */}
      <TestimonialsSection />

      {/* ══════════════════════════════════════════════════
          FINAL CTA
          ══════════════════════════════════════════════════ */}
      <section className="py-[96px] sm:py-[128px] relative overflow-hidden" style={{ background: color.ink }}>
        <div className="absolute inset-0">
          <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1440 600" fill="none">
            <path d="M-80 400C300 300 600 500 900 350S1200 200 1520 320" stroke="white" strokeOpacity="0.03" strokeWidth="2" />
            <path d="M-80 250C300 350 600 200 900 300S1200 400 1520 280" stroke="white" strokeOpacity="0.02" strokeWidth="1.5" />
          </svg>
        </div>
        <div className="relative max-w-[1120px] mx-auto px-6 z-10">
          <Reveal>
            <div className="max-w-[560px] mx-auto text-center">
              <h2 className="text-[clamp(2rem,4.5vw,3.25rem)] font-bold tracking-[-0.02em] leading-[1.1] text-white mb-[20px]">
                Your next role is one upload away.
              </h2>
              <p className="text-[16px] sm:text-[18px] leading-[1.65] text-[#888] mb-[40px]">Stop applying manually. Join thousands who've reclaimed their time.</p>
              <div className="max-w-[480px] mx-auto">
                <EmailForm variant="dark" />
              </div>
              <div className="mt-[32px] flex flex-wrap items-center justify-center gap-x-[24px] gap-y-[8px] text-[13px] text-[#666]">
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
        <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-white/95 backdrop-blur-md border-t border-[#E8E4DF] p-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-[0_-4px_20px_rgba(0,0,0,0.08)]">
          <Link to="/login" className="flex items-center justify-center gap-2 w-full h-[52px] rounded-[10px] text-[15px] font-semibold bg-[#4A6CF7] text-white hover:bg-[#3B5DE8] transition-all shadow-[0_2px_8px_rgba(74,108,247,0.3)]">
            Start applying free <ArrowRight className="w-[18px] h-[18px]" />
          </Link>
        </div>
      )}
    </>
  );
}
