import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import {
  ArrowRight, MailCheck, Target, Sparkles, Activity,
  Upload, SlidersHorizontal, Send, Trophy,
  PenTool, Clock, Shield, Zap,
  ChevronRight, Check, Star
} from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { cn } from '../lib/utils';

/* ─── Email capture hook ─── */
function useEmailCapture() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);
  const validateEmail = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());
  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    if (!validateEmail(email)) { setEmailError("Enter a valid email"); return; }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);
    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/dashboard");
      if (!result.success) throw new Error(result.error || "Failed");
      pushToast({ title: "Check your inbox", description: "Magic link sent!", tone: "success" });
      setSentEmail(result.email);
      setEmail("");
    } catch (err: any) {
      setEmailError(err?.message || "Failed to send");
      pushToast({ title: "Error", description: err?.message || "Failed", tone: "error" });
    } finally { setIsSubmitting(false); }
  };
  return { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit };
}

/* ─── Email form ─── */
function EmailForm({ variant = "light" }: { variant?: "light" | "hero" | "dark" }) {
  const { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit } = useEmailCapture();
  if (sentEmail) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-2xl border border-gray-200 bg-white">
        <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 bg-purple-100">
          <MailCheck className="w-5 h-5 text-purple-600" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900">Check your inbox</p>
          <p className="text-xs truncate text-gray-500">{sentEmail}</p>
        </div>
        <button onClick={() => setSentEmail(null)} className="text-xs ml-auto shrink-0 hover:underline text-gray-400">Change</button>
      </div>
    );
  }
  return (
    <div>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3">
        <input type="email" placeholder="name@company.com"
          className={cn(
            "flex-1 h-[52px] px-5 rounded-full text-[15px] transition-all outline-none",
            variant === "dark"
              ? "bg-white/10 border-2 border-white/20 text-white placeholder:text-white/40 focus:border-purple-400"
              : "bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-purple-400 shadow-sm",
            emailError && "border-red-400"
          )}
          value={email} onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button type="submit" disabled={isSubmitting}
          className="h-[52px] px-8 rounded-full text-[15px] font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap bg-purple-600 text-white hover:bg-purple-700 hover:shadow-lg hover:shadow-purple-600/25 hover:-translate-y-0.5 active:translate-y-0"
        >
          {isSubmitting ? "Sending…" : "Get Started Free"} {!isSubmitting && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>
      {emailError && <p className="mt-2 text-xs text-red-500 pl-5">{emailError}</p>}
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
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold: 0.1 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return (
    <div ref={ref} className={cn("transition-all duration-700 ease-out", visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8", className)} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

/* ─── Live Activity Feed ─── */
function LiveActivityFeed() {
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
    const interval = setInterval(() => setCurrentIdx((prev) => (prev + 1) % activities.length), 3000);
    return () => clearInterval(interval);
  }, []);
  const visibleItems = [];
  for (let i = 0; i < 4; i++) visibleItems.push(activities[(currentIdx + i) % activities.length]);
  return (
    <div className="space-y-2">
      {visibleItems.map((item, idx) => (
        <div key={`${item.role}-${idx}-${currentIdx}`} className="flex items-center gap-3 px-4 py-2.5 bg-white/90 rounded-xl border border-gray-100 shadow-sm transition-all duration-500" style={{ opacity: 1 - idx * 0.2 }}>
          <div className={cn("w-2 h-2 rounded-full shrink-0", item.type === "applied" ? "bg-green-400" : "bg-purple-400")} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{item.role}</p>
            <p className="text-xs text-gray-400">{item.company}</p>
          </div>
          <span className="text-[11px] text-gray-400 shrink-0">{item.time}</span>
        </div>
      ))}
    </div>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   HOMEPAGE — Podia-style visual redesign
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function Homepage() {
  const [stickyVisible, setStickyVisible] = useState(false);
  useEffect(() => {
    const h = () => setStickyVisible(window.scrollY > 600);
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, []);

  return (
    <>
      <SEO
        title="JobHuntin — AI That Applies to Jobs While You Sleep"
        description="Upload your resume. Our AI agent tailors every application and applies to hundreds of jobs daily. More interviews, zero effort."
        ogTitle="JobHuntin — AI That Applies to Jobs While You Sleep"
        canonicalUrl="https://jobhuntin.com/"
        schema={{
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          "name": "JobHuntin",
          "applicationCategory": "BusinessApplication",
          "operatingSystem": "Web",
          "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
          "description": "AI agent that tailors and submits job applications autonomously."
        }}
      />

      {/* ═══ §1 HERO — Centered headline + floating colorful cards ═══ */}
      <section className="relative overflow-hidden bg-gradient-to-b from-white via-purple-50/40 to-white min-h-[85vh] flex items-center">
        {/* Floating decorative cards — Podia style overlapping shapes */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-10 right-[5%] w-[340px] h-[260px] bg-gradient-to-br from-purple-400 to-purple-600 rounded-3xl rotate-6 opacity-[0.12] blur-[2px]" />
          <div className="absolute top-[15%] right-[10%] w-[280px] h-[200px] bg-gradient-to-br from-orange-300 to-rose-400 rounded-3xl -rotate-3 opacity-[0.15]" />
          <div className="absolute top-[8%] right-[2%] w-[220px] h-[180px] bg-gradient-to-br from-sky-300 to-blue-500 rounded-3xl rotate-12 opacity-[0.12]" />
          <div className="absolute bottom-[20%] right-[8%] w-[260px] h-[190px] bg-gradient-to-br from-teal-300 to-emerald-400 rounded-3xl -rotate-6 opacity-[0.10]" />
          <div className="absolute top-[40%] right-[22%] w-[160px] h-[120px] bg-gradient-to-br from-violet-300 to-purple-500 rounded-2xl rotate-3 opacity-[0.08]" />
          <div className="absolute bottom-[10%] left-[5%] w-[200px] h-[150px] bg-gradient-to-br from-amber-200 to-orange-300 rounded-3xl rotate-12 opacity-[0.08]" />
          <div className="absolute top-[5%] left-[8%] w-[120px] h-[100px] bg-gradient-to-br from-purple-200 to-purple-400 rounded-2xl -rotate-12 opacity-[0.08]" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 py-20 sm:py-28 w-full">
          <div className="max-w-3xl mx-auto text-center">
            <FadeIn>
              <h1 className="text-[clamp(2.5rem,6vw,4.75rem)] font-extrabold leading-[1.05] tracking-[-0.04em] text-gray-900">
                The all-in-one for<br />
                <span className="bg-gradient-to-r from-purple-600 via-purple-500 to-violet-500 bg-clip-text text-transparent">job seekers</span>
              </h1>
            </FadeIn>

            <FadeIn delay={100}>
              <p className="mt-6 text-xl sm:text-2xl text-gray-500 max-w-2xl mx-auto leading-relaxed font-normal">
                Upload your resume once. Our AI agent tailors every application and applies to hundreds of jobs — while you sleep.
              </p>
            </FadeIn>

            <FadeIn delay={200}>
              <div className="mt-10 max-w-[520px] mx-auto">
                <EmailForm variant="hero" />
                <p className="mt-4 text-sm text-gray-400">Free to start · No credit card required</p>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ═══ §2 COLORFUL PRODUCT CARDS — Podia's card grid style ═══ */}
      <section className="bg-white py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-6">
              <p className="text-purple-600 font-semibold text-sm uppercase tracking-wider mb-3">Everything you need</p>
              <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-extrabold tracking-tight text-gray-900 leading-tight">
                Everything you need to land interviews
              </h2>
            </div>
          </FadeIn>

          <div className="mt-16 grid md:grid-cols-3 gap-6">
            {/* Card 1 — Purple */}
            <FadeIn delay={0}>
              <div className="group relative rounded-3xl overflow-hidden bg-gradient-to-br from-purple-500 to-purple-700 p-8 pb-0 min-h-[420px] flex flex-col hover:-translate-y-1 transition-all duration-300 hover:shadow-2xl hover:shadow-purple-500/20">
                <div className="flex-1">
                  <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center mb-5">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Precision Matching</h3>
                  <p className="text-purple-100 leading-relaxed text-[15px]">
                    Our AI analyzes thousands of listings and only applies to roles that truly match your skills and preferences.
                  </p>
                  <a href="#how-it-works" className="inline-flex items-center gap-1.5 text-white/80 hover:text-white font-semibold text-sm mt-4 group/l">
                    Learn more <ChevronRight className="w-4 h-4 group-hover/l:translate-x-1 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-white/10 backdrop-blur-sm rounded-t-2xl p-4 mx-[-8px] border-t border-white/10">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-white/20" />
                    <div className="flex-1"><div className="h-3 w-3/4 bg-white/20 rounded-full" /><div className="h-2 w-1/2 bg-white/10 rounded-full mt-1.5" /></div>
                    <div className="px-2 py-1 rounded-full bg-green-400/20 text-[10px] font-bold text-green-200">98% match</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-white/20" />
                    <div className="flex-1"><div className="h-3 w-2/3 bg-white/20 rounded-full" /><div className="h-2 w-2/5 bg-white/10 rounded-full mt-1.5" /></div>
                    <div className="px-2 py-1 rounded-full bg-green-400/20 text-[10px] font-bold text-green-200">95% match</div>
                  </div>
                </div>
              </div>
            </FadeIn>

            {/* Card 2 — Coral/Orange */}
            <FadeIn delay={150}>
              <div className="group relative rounded-3xl overflow-hidden bg-gradient-to-br from-orange-400 to-rose-500 p-8 pb-0 min-h-[420px] flex flex-col hover:-translate-y-1 transition-all duration-300 hover:shadow-2xl hover:shadow-orange-500/20">
                <div className="flex-1">
                  <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center mb-5">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Curated Quality</h3>
                  <p className="text-orange-100 leading-relaxed text-[15px]">
                    Every resume and cover letter is custom-tailored for each role. ATS-optimized, company-tone matched.
                  </p>
                  <a href="#features" className="inline-flex items-center gap-1.5 text-white/80 hover:text-white font-semibold text-sm mt-4 group/l">
                    Learn more <ChevronRight className="w-4 h-4 group-hover/l:translate-x-1 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-white/10 backdrop-blur-sm rounded-t-2xl p-4 mx-[-8px] border-t border-white/10">
                  <div className="text-white/70 text-[11px] font-mono space-y-1.5">
                    <div className="flex gap-2"><span className="text-white/40">Aa</span><div className="h-2.5 w-full bg-white/15 rounded-full" /></div>
                    <div className="flex gap-2"><span className="text-white/40">Aa</span><div className="h-2.5 w-4/5 bg-white/15 rounded-full" /></div>
                    <div className="flex gap-2"><span className="text-white/40">Aa</span><div className="h-2.5 w-3/5 bg-white/15 rounded-full" /></div>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <div className="px-2.5 py-1 rounded-full bg-white/15 text-[10px] text-white/80 font-medium">ATS: 94%</div>
                    <div className="px-2.5 py-1 rounded-full bg-white/15 text-[10px] text-white/80 font-medium">Tailored ✓</div>
                  </div>
                </div>
              </div>
            </FadeIn>

            {/* Card 3 — Blue */}
            <FadeIn delay={300}>
              <div className="group relative rounded-3xl overflow-hidden bg-gradient-to-br from-sky-400 to-blue-600 p-8 pb-0 min-h-[420px] flex flex-col hover:-translate-y-1 transition-all duration-300 hover:shadow-2xl hover:shadow-blue-500/20">
                <div className="flex-1">
                  <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center mb-5">
                    <Activity className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">Live Activity</h3>
                  <p className="text-sky-100 leading-relaxed text-[15px]">
                    Track every application in real-time. See matches, submissions, and responses from your dashboard.
                  </p>
                  <a href="#dashboard" className="inline-flex items-center gap-1.5 text-white/80 hover:text-white font-semibold text-sm mt-4 group/l">
                    Learn more <ChevronRight className="w-4 h-4 group-hover/l:translate-x-1 transition-transform" />
                  </a>
                </div>
                <div className="mt-6 bg-white/10 backdrop-blur-sm rounded-t-2xl p-4 mx-[-8px] border-t border-white/10">
                  <div className="flex items-center gap-2 mb-2"><div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" /><span className="text-[11px] text-white/60">Live now</span></div>
                  {["Applied to Stripe", "Matched at Vercel", "Applied to Figma"].map((a, i) => (
                    <div key={i} className="flex items-center gap-2 py-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-white/30" />
                      <span className="text-[11px] text-white/60 flex-1">{a}</span>
                      <span className="text-[10px] text-white/30">{i + 1}m ago</span>
                    </div>
                  ))}
                </div>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ═══ §3 BIG TESTIMONIAL QUOTE — Podia style ═══ */}
      <section className="bg-gray-50 py-20 sm:py-28">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <FadeIn>
            <div className="text-5xl sm:text-6xl text-purple-300 mb-6 leading-none">"</div>
            <blockquote className="text-2xl sm:text-3xl lg:text-[2.5rem] font-bold text-gray-900 leading-snug tracking-tight">
              That first week I literally did nothing — and got 4 interview callbacks.
            </blockquote>
            <div className="mt-8 flex items-center justify-center gap-4">
              <div className="w-14 h-14 rounded-full bg-purple-100 flex items-center justify-center text-lg font-bold text-purple-700">SK</div>
              <div className="text-left">
                <p className="font-semibold text-gray-900">Sarah K.</p>
                <p className="text-sm text-gray-500">Marketing Manager · Landed at HubSpot</p>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══ §4 FEATURE ROWS — alternating image+text like Podia ═══ */}
      <section className="bg-white py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-6 space-y-24 sm:space-y-32">

          {/* Row 1 — Dashboard (image left, text right) */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
              <div className="relative">
                <div className="bg-gradient-to-br from-purple-100 via-purple-50 to-violet-100 rounded-3xl p-8 sm:p-10">
                  <div className="bg-white rounded-2xl shadow-xl p-5 border border-gray-100">
                    <div className="flex items-center gap-2 mb-4">
                      <div className="flex gap-1.5"><div className="w-3 h-3 rounded-full bg-red-400" /><div className="w-3 h-3 rounded-full bg-amber-400" /><div className="w-3 h-3 rounded-full bg-green-400" /></div>
                      <div className="flex-1 h-6 bg-gray-100 rounded-full mx-8" />
                    </div>
                    <div className="grid grid-cols-3 gap-3 mb-4">
                      <div className="bg-purple-50 rounded-xl p-3 text-center"><div className="text-2xl font-bold text-purple-600">127</div><div className="text-[10px] text-gray-500 mt-0.5">Applied</div></div>
                      <div className="bg-green-50 rounded-xl p-3 text-center"><div className="text-2xl font-bold text-green-600">23</div><div className="text-[10px] text-gray-500 mt-0.5">Responses</div></div>
                      <div className="bg-amber-50 rounded-xl p-3 text-center"><div className="text-2xl font-bold text-amber-600">7</div><div className="text-[10px] text-gray-500 mt-0.5">Interviews</div></div>
                    </div>
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex items-center gap-3 py-2.5 border-t border-gray-50">
                        <div className="w-8 h-8 rounded-lg bg-gray-100" />
                        <div className="flex-1"><div className="h-3 bg-gray-100 rounded-full w-3/4" /><div className="h-2 bg-gray-50 rounded-full w-1/2 mt-1" /></div>
                        <div className={cn("w-16 h-6 rounded-full text-[9px] font-bold flex items-center justify-center", i === 1 ? "bg-green-100 text-green-700" : i === 2 ? "bg-purple-100 text-purple-700" : "bg-amber-100 text-amber-700")}>{i === 1 ? "Interview" : i === 2 ? "Applied" : "Viewed"}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div>
                <p className="text-purple-600 font-semibold text-sm uppercase tracking-wider mb-3">Your command center</p>
                <h2 className="text-[clamp(1.75rem,3.5vw,2.75rem)] font-extrabold tracking-tight text-gray-900 leading-tight">
                  A dashboard that keeps you in control
                </h2>
                <p className="mt-5 text-lg text-gray-500 leading-relaxed">
                  Track every application, see live matches, and review AI-crafted submissions — all in one beautiful dashboard.
                </p>
                <ul className="mt-8 space-y-4">
                  {["Real-time application tracking", "Response & interview monitoring", "AI match confidence scores"].map((f) => (
                    <li key={f} className="flex items-center gap-3"><div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center shrink-0"><Check className="w-3.5 h-3.5 text-purple-600" /></div><span className="text-gray-700 font-medium">{f}</span></li>
                  ))}
                </ul>
                <Link to="/login" className="inline-flex items-center gap-2 mt-8 h-12 px-8 rounded-full text-[15px] font-semibold bg-purple-600 text-white hover:bg-purple-700 hover:shadow-lg hover:shadow-purple-600/25 hover:-translate-y-0.5 transition-all">
                  View dashboard <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </FadeIn>

          {/* Row 2 — Resume builder (text left, image right) */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
              <div className="order-2 lg:order-1">
                <p className="text-orange-500 font-semibold text-sm uppercase tracking-wider mb-3">AI-Powered</p>
                <h2 className="text-[clamp(1.75rem,3.5vw,2.75rem)] font-extrabold tracking-tight text-gray-900 leading-tight">
                  Crafted applications that actually get responses
                </h2>
                <p className="mt-5 text-lg text-gray-500 leading-relaxed">
                  Every resume and cover letter is rewritten for the specific role, adjusted for the company's tone, and optimized for ATS systems.
                </p>
                <ul className="mt-8 space-y-4">
                  {["Custom resume for every role", "Company-tone matched cover letters", "ATS optimization built in"].map((f) => (
                    <li key={f} className="flex items-center gap-3"><div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center shrink-0"><Check className="w-3.5 h-3.5 text-orange-500" /></div><span className="text-gray-700 font-medium">{f}</span></li>
                  ))}
                </ul>
              </div>
              <div className="order-1 lg:order-2 relative">
                <div className="bg-gradient-to-br from-orange-100 via-rose-50 to-amber-100 rounded-3xl p-8 sm:p-10">
                  <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
                    <div className="flex items-center justify-between mb-5">
                      <div className="text-sm font-bold text-gray-900">Resume Preview</div>
                      <div className="px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs font-bold">ATS Score: 94%</div>
                    </div>
                    <div className="space-y-3">
                      <div className="h-5 bg-gray-900 rounded-full w-3/5" />
                      <div className="h-3 bg-gray-200 rounded-full w-full" />
                      <div className="h-3 bg-gray-200 rounded-full w-5/6" />
                      <div className="h-3 bg-gray-200 rounded-full w-4/5" />
                      <div className="h-px bg-gray-100 my-3" />
                      <div className="h-4 bg-gray-800 rounded-full w-2/5" />
                      <div className="h-3 bg-gray-100 rounded-full w-full" />
                      <div className="h-3 bg-gray-100 rounded-full w-3/4" />
                    </div>
                    <div className="mt-4 flex gap-2 flex-wrap">
                      <div className="px-3 py-1.5 rounded-lg bg-purple-50 text-purple-700 text-[10px] font-bold">React</div>
                      <div className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 text-[10px] font-bold">TypeScript</div>
                      <div className="px-3 py-1.5 rounded-lg bg-green-50 text-green-700 text-[10px] font-bold">Node.js</div>
                      <div className="px-3 py-1.5 rounded-lg bg-amber-50 text-amber-700 text-[10px] font-bold">AWS</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </FadeIn>

          {/* Row 3 — Live feed (image left, text right) */}
          <FadeIn>
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
              <div className="relative">
                <div className="bg-gradient-to-br from-sky-100 via-blue-50 to-teal-100 rounded-3xl p-8 sm:p-10">
                  <div className="bg-white rounded-2xl shadow-xl p-5 border border-gray-100">
                    <div className="text-sm font-bold text-gray-900 mb-4">Live Activity Feed</div>
                    <div className="flex items-center gap-2 mb-3"><div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" /><span className="text-xs text-gray-500">Updating in real-time</span></div>
                    <LiveActivityFeed />
                  </div>
                </div>
              </div>
              <div>
                <p className="text-blue-600 font-semibold text-sm uppercase tracking-wider mb-3">Always running</p>
                <h2 className="text-[clamp(1.75rem,3.5vw,2.75rem)] font-extrabold tracking-tight text-gray-900 leading-tight">
                  Your agent works 24/7 — even while you sleep
                </h2>
                <p className="mt-5 text-lg text-gray-500 leading-relaxed">
                  New jobs get posted at 2am, on weekends, on holidays. Our agent monitors boards continuously and applies within minutes.
                </p>
                <ul className="mt-8 space-y-4">
                  {["Continuous job board monitoring", "Instant application on new listings", "Smart timing for best results"].map((f) => (
                    <li key={f} className="flex items-center gap-3"><div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shrink-0"><Check className="w-3.5 h-3.5 text-blue-600" /></div><span className="text-gray-700 font-medium">{f}</span></li>
                  ))}
                </ul>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══ §5 HOW IT WORKS — colorful step cards ═══ */}
      <section id="how-it-works" className="bg-gray-50 py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-16">
              <p className="text-purple-600 font-semibold text-sm uppercase tracking-wider mb-3">Simple setup</p>
              <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-extrabold tracking-tight text-gray-900">
                How it works
              </h2>
              <p className="mt-4 text-lg text-gray-500">Under two minutes to set up. Then it runs on autopilot.</p>
            </div>
          </FadeIn>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { n: "1", icon: Upload, t: "Upload resume", d: "Drop your PDF. We parse skills, experience, and preferences instantly.", bg: "bg-purple-500", iconBg: "bg-purple-400/30" },
              { n: "2", icon: SlidersHorizontal, t: "Set your filters", d: "Roles, locations, salary, company size — we only apply to what matches.", bg: "bg-orange-400", iconBg: "bg-orange-300/30" },
              { n: "3", icon: Send, t: "AI applies for you", d: "Every application is individually tailored with custom resume and cover letter.", bg: "bg-sky-500", iconBg: "bg-sky-400/30" },
              { n: "4", icon: Trophy, t: "Get interviews", d: "Track responses, prep for interviews, and land your dream role.", bg: "bg-emerald-500", iconBg: "bg-emerald-400/30" },
            ].map((step, idx) => (
              <FadeIn key={step.n} delay={idx * 100}>
                <div className={cn("rounded-3xl p-7 text-white min-h-[240px] flex flex-col hover:-translate-y-1 transition-all duration-300 hover:shadow-xl", step.bg)}>
                  <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center mb-5", step.iconBg)}>
                    <step.icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-[11px] font-bold uppercase tracking-widest text-white/50 mb-2">Step {step.n}</div>
                  <h3 className="text-xl font-bold mb-2">{step.t}</h3>
                  <p className="text-white/80 text-[14px] leading-relaxed">{step.d}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ §6 MORE TESTIMONIALS — grid ═══ */}
      <section className="bg-white py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-extrabold tracking-tight text-gray-900">
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
                <div className="bg-gray-50 rounded-2xl p-7 hover:bg-gray-100/80 transition-colors h-full flex flex-col">
                  <div className="flex gap-0.5 mb-4">
                    {[...Array(5)].map((_, i) => <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />)}
                  </div>
                  <p className="text-[15px] text-gray-700 leading-relaxed flex-1 mb-5">"{t.q}"</p>
                  <div className="flex items-center gap-3">
                    <div className={cn("w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold", t.bg)}>{t.initials}</div>
                    <div><p className="text-sm font-semibold text-gray-900">{t.n}</p><p className="text-xs text-gray-400">{t.r}</p></div>
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ §7 FEATURES GRID ═══ */}
      <section id="features" className="bg-gray-50 py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-3xl mx-auto mb-6">
              <p className="text-purple-600 font-semibold text-sm uppercase tracking-wider mb-3">Full feature set</p>
              <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-extrabold tracking-tight text-gray-900">
                Everything you need, right out of the box
              </h2>
            </div>
          </FadeIn>

          <FadeIn delay={100}>
            <div className="text-center max-w-xl mx-auto mb-14">
              <p className="text-gray-500 italic text-[15px]">"Instead of worrying about 20 different tools…I just run my search from JobHuntin."</p>
              <p className="mt-2 text-sm text-gray-400">– Sarah K., Marketing Manager</p>
            </div>
          </FadeIn>

          <FadeIn delay={200}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {[
                "AI resume analysis", "Custom cover letters", "ATS optimization", "Thousands of positions",
                "Real-time tracking", "Interview prep insights", "Personalized applications", "Salary filtering",
                "Company size filters", "Location preferences", "Role matching AI", "Auto-apply engine",
                "Application dashboard", "Response tracking", "Resume versioning", "Email notifications",
                "Mobile dashboard", "Data encryption", "Bulk applications", "Smart scheduling",
                "Company research", "Skills gap analysis", "Application analytics", "Priority support",
              ].map((feature) => (
                <div key={feature} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white border border-gray-100 hover:border-purple-200 hover:shadow-sm transition-all">
                  <div className="w-5 h-5 rounded-full bg-purple-100 flex items-center justify-center shrink-0">
                    <Check className="w-3 h-3 text-purple-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">{feature}</span>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══ §8 FINAL CTA — with colorful background like Podia's bottom ═══ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-purple-50 via-blue-50 to-teal-50 py-24 sm:py-32">
        {/* Decorative shapes */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-[10%] left-[5%] w-[200px] h-[160px] bg-gradient-to-br from-purple-300 to-purple-500 rounded-3xl rotate-12 opacity-[0.08]" />
          <div className="absolute bottom-[10%] right-[5%] w-[240px] h-[180px] bg-gradient-to-br from-blue-300 to-sky-500 rounded-3xl -rotate-6 opacity-[0.08]" />
          <div className="absolute top-[30%] right-[15%] w-[160px] h-[130px] bg-gradient-to-br from-orange-300 to-rose-400 rounded-2xl rotate-6 opacity-[0.07]" />
          <div className="absolute bottom-[25%] left-[15%] w-[180px] h-[140px] bg-gradient-to-br from-teal-300 to-emerald-400 rounded-2xl -rotate-12 opacity-[0.07]" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-[clamp(2rem,5vw,3.25rem)] font-extrabold tracking-tight text-gray-900 leading-tight">
                Job searching is much simpler when AI does the heavy lifting.
              </h2>
              <p className="mt-6 text-lg text-gray-500 max-w-lg mx-auto">
                Stop applying manually. Set it up in 2 minutes and your first applications go out today.
              </p>
              <div className="mt-10 max-w-[480px] mx-auto">
                <EmailForm variant="light" />
              </div>
              <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-gray-400">
                {["Free plan", "No credit card", "Cancel anytime"].map((t) => (
                  <span key={t} className="flex items-center gap-1.5">
                    <Check className="w-4 h-4 text-green-500" /> {t}
                  </span>
                ))}
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

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
