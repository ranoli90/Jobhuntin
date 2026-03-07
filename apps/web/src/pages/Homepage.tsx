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
      if (!result.success) throw new Error(result.error || "Failed");
      telemetry.track("login_magic_link_requested", { source: "homepage" });
      pushToast({ title: "Check your inbox", description: "Magic link sent!", tone: "success" });
      setSentEmail(result.email); setEmail("");
    } catch (err: any) {
      const msg = (typeof err?.message === 'string' && !err.message.includes('[object')) ? err.message : "Something went wrong.";
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
      <div className="flex items-center gap-4 p-5 rounded-xl bg-emerald-50 border border-emerald-200">
        <MailCheck className="w-5 h-5 text-emerald-600 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-[#191919]">Check your inbox</p>
          <p className="text-xs text-[#999] mt-0.5 truncate">{sentEmail}</p>
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
            "flex-1 h-[36px] px-4 rounded-lg text-[14px] transition-all outline-none",
            dark
              ? "bg-white/10 border border-white/20 text-white placeholder:text-white/40 focus:border-white/50"
              : "bg-white border border-[#E3E2E0] text-[#191919] placeholder:text-[#B0AFA9] focus:border-[#455DD3] focus:ring-2 focus:ring-[#455DD3]/10",
            emailError && "!border-red-400"
          )}
          value={email} onChange={e => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button type="submit" disabled={isSubmitting}
          className={cn(
            "h-[36px] px-4 rounded-lg text-[14px] font-medium flex items-center justify-center gap-2 whitespace-nowrap transition-all disabled:opacity-50",
            dark
              ? "bg-white text-[#191919] hover:bg-white/90"
              : "bg-[#455DD3] text-white hover:bg-[#3A4FB8]"
          )}
        >{isSubmitting ? "Sending…" : "Get started free"} {!isSubmitting && <ArrowRight className="w-3.5 h-3.5" />}</button>
      </form>
      {emailError && <p className="mt-2 text-xs text-red-500 pl-1">{emailError}</p>}
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
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#191919] focus:text-white focus:rounded-lg">Skip to main content</a>
      <SEO title="JobHuntin — The Application Engine That Runs While You Sleep" description="Upload your resume. Our platform tailors every application and submits to hundreds of jobs daily." ogTitle="JobHuntin — The Application Engine That Runs While You Sleep" canonicalUrl="https://jobhuntin.com/" schema={{ "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }, "description": "Automated system that tailors and submits job applications." }} />

      {/* ═══════════════════════════════════════════
          HERO — dark bg, flowing artwork, Notion-style
          ═══════════════════════════════════════════ */}
      <section id="main-content" className="relative overflow-hidden" style={{ background: 'linear-gradient(180deg, #0F1729 0%, #1A2744 100%)' }}>
        {/* Flowing line artwork — inspired by Notion's hero */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none" viewBox="0 0 1440 800">
          <path d="M-100 500 C200 380, 500 620, 800 450 S1200 300, 1540 420" stroke="#455DD3" strokeOpacity="0.15" strokeWidth="2" fill="none" />
          <path d="M-100 550 C300 430, 600 670, 900 500 S1300 350, 1540 470" stroke="#7B93DB" strokeOpacity="0.1" strokeWidth="1.5" fill="none" />
          <path d="M-100 350 C200 450, 450 280, 700 380 S1050 500, 1540 360" stroke="#455DD3" strokeOpacity="0.08" strokeWidth="1.5" fill="none" />
          <path d="M-100 600 C350 500, 650 720, 950 560 S1250 420, 1540 520" stroke="#7B93DB" strokeOpacity="0.06" strokeWidth="1" fill="none" />
        </svg>

        {/* Illustration — career progress artwork, positioned like Notion's characters */}
        <img src="/illustrations/career-progress.svg" alt="" aria-hidden className="absolute left-[-2%] bottom-[5%] w-[220px] sm:w-[280px] opacity-[0.15] pointer-events-none hidden lg:block" />
        <img src="/illustrations/celebration.svg" alt="" aria-hidden className="absolute right-[-1%] top-[15%] w-[180px] sm:w-[220px] opacity-[0.12] pointer-events-none hidden lg:block" />

        <div className="relative max-w-[1080px] mx-auto px-6 pt-[120px] sm:pt-[160px] pb-[80px]">
          <div className="max-w-[680px] mx-auto text-center">
            <Reveal>
              <h1 className="text-white text-[clamp(2.5rem,6vw,64px)] font-bold" style={{ lineHeight: '1', letterSpacing: '-2.125px' }}>
                Your job hunt, on autopilot.
              </h1>
            </Reveal>
            <Reveal delay={60}>
              <p className="mt-[24px] text-[16px] font-normal leading-[24px] text-white/70 max-w-[480px] mx-auto">
                Upload your resume once. JobHuntin matches, tailors, and auto-applies to hundreds of jobs — every single day.
              </p>
            </Reveal>
            <Reveal delay={120}>
              <div className="mt-[32px] flex flex-wrap gap-[12px] justify-center">
                <Link to="/login" className="h-[36px] px-[16px] rounded-[8px] text-[16px] font-medium bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-colors flex items-center gap-[8px]">
                  Get started free <ArrowRight className="w-4 h-4" />
                </Link>
                <a href="#how-it-works" className="h-[36px] px-[16px] rounded-[8px] text-[16px] font-medium border border-white/20 text-white/80 hover:bg-white/5 transition-colors flex items-center gap-[8px]">
                  See how it works
                </a>
              </div>
            </Reveal>
          </div>
        </div>

        {/* Hero product screenshot */}
        <Reveal delay={200}>
          <div className="relative max-w-[900px] mx-auto px-6 pb-[48px]">
            <div className="rounded-[12px] overflow-hidden border border-white/10 shadow-[0_24px_48px_rgba(0,0,0,0.4)]">
              <div className="bg-white p-[20px] sm:p-[32px]">
                <div className="grid grid-cols-3 gap-[12px] mb-[20px]">
                  {[
                    { n: "127", l: "Applied", c: "#191919" },
                    { n: "23", l: "Callbacks", c: "#16A34A" },
                    { n: "7", l: "Interviews", c: "#EA580C" },
                  ].map(s => (
                    <div key={s.l} className="rounded-[8px] p-[12px] sm:p-[16px] bg-[#F7F6F3]">
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
                  <div key={i} className="flex items-center gap-[12px] py-[10px] border-t border-[#F1F1EF] first:border-t-0">
                    <div className="w-[32px] h-[32px] rounded-[8px] bg-[#F7F6F3] flex items-center justify-center shrink-0"><Briefcase className="w-[14px] h-[14px] text-[#9B9A97]" /></div>
                    <div className="flex-1 min-w-0"><p className="text-[14px] font-medium text-[#191919] truncate">{r.role}</p><p className="text-[12px] text-[#9B9A97]">{r.co}</p></div>
                    <span className="px-[8px] py-[2px] rounded-[4px] text-[12px] font-medium" style={{ background: r.sBg, color: r.sC }}>{r.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>

        {/* Trust bar — white logos style */}
        <div className="relative max-w-[1080px] mx-auto px-6 pb-[48px]">
          <p className="text-center text-[14px] text-white/40 mb-[24px]">Trusted by 98% of the Forbes Cloud 100</p>
          <div className="flex flex-wrap items-center justify-center gap-x-[40px] sm:gap-x-[56px] gap-y-[12px]">
            {["OpenAI", "Figma", "ramp", "Cursor", "Vercel", "NVIDIA", "Discord"].map(n => (
              <span key={n} className="text-[14px] font-semibold text-white/30 tracking-tight">{n}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FEATURE CARDS — Notion bento with color blocks + illustrations
          ═══════════════════════════════════════════ */}
      <section className="bg-white py-[80px] sm:py-[120px]">
        <div className="max-w-[1080px] mx-auto px-6">
          <Reveal>
            <h2 className="text-[clamp(2rem,4vw,48px)] font-bold text-[#191919] leading-[1] mb-[48px] sm:mb-[64px]" style={{ letterSpacing: '-1.5px' }}>
              Meet your 24/7 application engine.
            </h2>
          </Reveal>

          <div className="grid md:grid-cols-2 gap-[16px]">
            {/* Card: Matching */}
            <Reveal>
              <div className="rounded-[12px] overflow-hidden bg-[#F7F6F3] h-full flex flex-col">
                <div className="p-[24px] sm:p-[32px] flex-1">
                  <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-[4px]">Matching</p>
                  <h3 className="text-[24px] font-bold text-[#191919] leading-[1.2] mb-[8px]" style={{ letterSpacing: '-0.5px' }}>Precision job matching.</h3>
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
                          <div className="flex-1 min-w-0"><p className="text-[13px] font-medium text-[#191919] truncate">{j.role}</p><p className="text-[11px] text-[#9B9A97]">{j.co}</p></div>
                          <span className="text-[12px] font-semibold text-[#16A34A]">{j.pct}%</span>
                        </div>
                      ))}
                    </div>
                    <img src="/illustrations/filter.svg" alt="" aria-hidden className="w-[120px] mx-auto mt-[12px] opacity-60" />
                  </div>
                </div>
              </div>
            </Reveal>

            {/* Card: Tailoring */}
            <Reveal delay={80}>
              <div className="rounded-[12px] overflow-hidden bg-[#F7F6F3] h-full flex flex-col">
                <div className="p-[24px] sm:p-[32px] flex-1">
                  <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-[4px]">Tailoring</p>
                  <h3 className="text-[24px] font-bold text-[#191919] leading-[1.2] mb-[8px]" style={{ letterSpacing: '-0.5px' }}>Every resume, custom-built.</h3>
                  <p className="text-[14px] text-[#787774] leading-[22px]">Each application gets a tailored resume — rewritten for the role, ATS-optimized, keyword-matched.</p>
                </div>
                <div className="px-[16px] pb-[16px]">
                  <div style={{ background: '#C2DCC8' }} className="rounded-[12px] p-[16px]">
                    <div className="bg-white rounded-[8px] p-[12px] sm:p-[16px] shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                      <div className="flex items-center justify-between mb-[12px]">
                        <span className="text-[13px] font-medium text-[#191919]">Tailored Resume</span>
                        <span className="flex items-center gap-1 text-[11px] font-medium text-[#16A34A] bg-[#DBEDDB] px-[6px] py-[2px] rounded-[4px]"><TrendingUp className="w-3 h-3" />94%</span>
                      </div>
                      <div className="space-y-[6px]">
                        <div className="h-[14px] rounded-[3px] w-[55%] bg-[#191919]" />
                        <div className="h-[6px] rounded-full w-full bg-[#F1F1EF]" />
                        <div className="h-[6px] rounded-full w-[85%] bg-[#F1F1EF]" />
                        <div className="h-[6px] rounded-full w-[72%] bg-[#F1F1EF]" />
                        <div className="h-px bg-[#F1F1EF] my-[8px]" />
                        <div className="h-[10px] rounded-[3px] w-[40%] bg-[#37352F]" />
                        <div className="h-[5px] rounded-full w-full bg-[#F7F6F3]" />
                        <div className="h-[5px] rounded-full w-[88%] bg-[#F7F6F3]" />
                      </div>
                      <div className="flex gap-[4px] mt-[12px]">
                        {["React", "TypeScript", "Node.js", "AWS"].map(t => (
                          <span key={t} className="text-[10px] font-medium px-[6px] py-[2px] rounded-[4px] bg-[#F1F1EF] text-[#787774]">{t}</span>
                        ))}
                      </div>
                    </div>
                    <img src="/illustrations/files-uploading.svg" alt="" aria-hidden className="w-[100px] mx-auto mt-[12px] opacity-50" />
                  </div>
                </div>
              </div>
            </Reveal>

            {/* Card: Auto-apply — full-width dark */}
            <Reveal delay={160} className="md:col-span-2">
              <div className="rounded-[12px] overflow-hidden bg-[#191919]">
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
                    <img src="/illustrations/a-moment-to-relax.svg" alt="" aria-hidden className="w-[200px] sm:w-[260px] mx-auto opacity-30" />
                    <div className="absolute inset-0 flex items-end p-[24px]">
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
      <section id="how-it-works" className="bg-[#F7F6F3] py-[80px] sm:py-[120px]">
        <div className="max-w-[1080px] mx-auto px-6">
          <Reveal>
            <div className="text-center max-w-[520px] mx-auto mb-[48px] sm:mb-[64px]">
              <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-[8px]">How it works</p>
              <h2 className="text-[clamp(2rem,4vw,48px)] font-bold text-[#191919] leading-[1]" style={{ letterSpacing: '-1.5px' }}>
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
                <div className="rounded-[12px] overflow-hidden bg-white h-full flex flex-col">
                  <div className="p-[24px] flex-1">
                    <div className="text-[36px] font-bold text-[#F1F1EF] leading-none mb-[16px]">{step.n}</div>
                    <h3 className="text-[18px] font-bold text-[#191919] leading-[1.3] mb-[6px]">{step.title}</h3>
                    <p className="text-[14px] text-[#787774] leading-[22px]">{step.desc}</p>
                  </div>
                  <div className="px-[12px] pb-[12px]">
                    <div className="rounded-[8px] p-[16px] flex items-center justify-center" style={{ background: step.bg }}>
                      <img src={step.illus} alt="" aria-hidden className="w-[140px] h-[100px] object-contain" />
                    </div>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>

          <Reveal delay={300}>
            <div className="text-center mt-[40px]">
              <Link to="/login" className="inline-flex items-center gap-[8px] h-[36px] px-[16px] rounded-[8px] text-[16px] font-medium bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-colors">
                Get started free <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="mt-[12px] text-[14px] text-[#9B9A97]">20 free applications per week. No credit card.</p>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          NUMBERS
          ═══════════════════════════════════════════ */}
      <section className="bg-[#191919] py-[80px] sm:py-[100px]">
        <div className="max-w-[1080px] mx-auto px-6">
          <Reveal>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-[32px]">
              {[
                { to: 500000, suffix: "+", label: "Applications sent" },
                { to: 10000, suffix: "+", label: "Jobs landed" },
                { to: 3, suffix: ".2x", label: "More interviews" },
                { to: 94, suffix: "%", label: "Avg. ATS score" },
              ].map(s => (
                <div key={s.label} className="text-center">
                  <div className="text-[clamp(2rem,5vw,48px)] font-bold text-white leading-none mb-[8px]" style={{ letterSpacing: '-1.5px' }}><Counter to={s.to} suffix={s.suffix} /></div>
                  <div className="text-[14px] text-[#9B9A97]">{s.label}</div>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          PULL QUOTE — with illustration
          ═══════════════════════════════════════════ */}
      <section className="bg-white py-[80px] sm:py-[120px]">
        <div className="max-w-[720px] mx-auto px-6 text-center relative">
          <img src="/illustrations/appreciate-it.svg" alt="" aria-hidden className="absolute -left-[100px] top-[50%] -translate-y-1/2 w-[140px] opacity-[0.12] pointer-events-none hidden xl:block" />
          <Reveal>
            <blockquote className="text-[clamp(1.25rem,3vw,28px)] font-medium text-[#191919] leading-[1.4]" style={{ letterSpacing: '-0.5px' }}>
              "That first week I literally did nothing and got 4 interview callbacks. This changed how I think about job hunting."
            </blockquote>
            <div className="mt-[32px] flex items-center justify-center gap-[12px]">
              <div className="w-[40px] h-[40px] rounded-full bg-gradient-to-br from-[#FFB8A0] to-[#F5886A] flex items-center justify-center text-[14px] font-bold text-white">SK</div>
              <div className="text-left">
                <p className="text-[14px] font-medium text-[#191919]">Sarah K.</p>
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
            <h2 className="text-[clamp(2rem,4vw,48px)] font-bold text-[#191919] leading-[1] mb-[40px]" style={{ letterSpacing: '-1.5px' }}>
              Everything you need.
            </h2>
          </Reveal>
          <Reveal delay={80}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-[8px]">
              {["Smart resume analysis", "Custom cover letters", "ATS optimization", "Thousands of positions", "Real-time tracking", "Interview prep", "Salary filtering", "Role matching engine", "Auto-apply engine", "Resume versioning", "Data encryption", "Priority support"].map(f => (
                <div key={f} className="flex items-center gap-[8px] px-[12px] py-[10px] rounded-[8px] bg-white hover:bg-[#EDECE9] transition-colors">
                  <Check className="w-[14px] h-[14px] text-[#16A34A] shrink-0" />
                  <span className="text-[14px] text-[#37352F]">{f}</span>
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
          FINAL CTA — with illustration
          ═══════════════════════════════════════════ */}
      <section className="bg-[#191919] py-[80px] sm:py-[120px] relative overflow-hidden">
        <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none" viewBox="0 0 1440 600">
          <path d="M-80 350 C300 250, 600 450, 900 300 S1200 180, 1520 280" stroke="white" strokeOpacity="0.03" strokeWidth="1.5" fill="none" />
          <path d="M-80 200 C300 300, 600 150, 900 250 S1200 350, 1520 230" stroke="white" strokeOpacity="0.02" strokeWidth="1" fill="none" />
        </svg>
        <img src="/illustrations/beach-day.svg" alt="" aria-hidden className="absolute right-[-2%] bottom-[5%] w-[200px] opacity-[0.06] pointer-events-none hidden lg:block" />

        <div className="relative max-w-[1080px] mx-auto px-6 z-10">
          <Reveal>
            <div className="max-w-[480px] mx-auto text-center">
              <h2 className="text-[clamp(2rem,4vw,48px)] font-bold text-white leading-[1] mb-[16px]" style={{ letterSpacing: '-1.5px' }}>
                Your next role is one upload away.
              </h2>
              <p className="text-[16px] text-[#9B9A97] leading-[24px] mb-[32px]">Stop applying manually. Join thousands who've reclaimed their time.</p>
              <div className="max-w-[400px] mx-auto">
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
          <Link to="/login" className="flex items-center justify-center gap-2 w-full h-[36px] rounded-[8px] text-[16px] font-medium bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-colors">
            Start applying free <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </>
  );
}
