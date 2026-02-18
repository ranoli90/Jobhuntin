import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import {
  ArrowRight, MailCheck, Target, Sparkles, Activity,
  Upload, SlidersHorizontal, Send, Trophy,
  FileText, Search, PenTool, Brain, Clock, Shield, BarChart3, Zap,
  ChevronRight, Monitor, Smartphone, Layout,
  Star
} from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { cn } from '../lib/utils';

/* ─── Email capture hook (shared between hero + bottom CTA) ─── */
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
    } finally {
      setIsSubmitting(false);
    }
  };

  return { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit };
}

/* ─── Inline email form — purple-accent style ─── */
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
        <button onClick={() => setSentEmail(null)} className="text-xs ml-auto shrink-0 hover:underline text-gray-400">
          Change
        </button>
      </div>
    );
  }

  return (
    <div>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3">
        <input
          type="email"
          placeholder="name@company.com"
          className={cn(
            "flex-1 h-[52px] px-5 rounded-full text-[15px] transition-all outline-none",
            variant === "hero"
              ? "bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-purple-400 shadow-sm"
              : variant === "dark"
              ? "bg-white/10 border-2 border-white/10 text-white placeholder:text-white/40 focus:border-purple-400"
              : "bg-white border-2 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-purple-400",
            emailError && "border-red-400"
          )}
          value={email}
          onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className="h-[52px] px-8 rounded-full text-[15px] font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap bg-purple-600 text-white hover:bg-purple-700 hover:shadow-lg hover:shadow-purple-600/25 hover:-translate-y-0.5 active:translate-y-0"
        >
          {isSubmitting ? "Sending…" : "Get Started Free"} {!isSubmitting && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>
      {emailError && <p className="mt-2 text-xs text-red-500 pl-5">{emailError}</p>}
    </div>
  );
}

/* ─── Fade-in on scroll observer ─── */
function FadeIn({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold: 0.15 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={cn(
        "transition-all duration-700 ease-out",
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8",
        className
      )}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

/* ─── Live Activity Feed (animated ticker) ─── */
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
    { role: "iOS Developer", company: "Apple", time: "3m ago", type: "matched" },
    { role: "Growth Marketing Lead", company: "HubSpot", time: "4m ago", type: "applied" },
  ];

  const [currentIdx, setCurrentIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIdx((prev) => (prev + 1) % activities.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const visibleItems = [];
  for (let i = 0; i < 5; i++) {
    visibleItems.push(activities[(currentIdx + i) % activities.length]);
  }

  return (
    <div className="space-y-2">
      {visibleItems.map((item, idx) => (
        <div
          key={`${item.role}-${idx}-${currentIdx}`}
          className="flex items-center gap-3 px-4 py-2.5 bg-white rounded-xl border border-gray-100 shadow-sm transition-all duration-500"
          style={{ opacity: 1 - idx * 0.15, animationDelay: `${idx * 100}ms` }}
        >
          <div className={cn(
            "w-2 h-2 rounded-full shrink-0",
            item.type === "applied" ? "bg-green-400" : "bg-purple-400"
          )} />
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
   HOMEPAGE — Podia-style redesign
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

      {/* ════════════════════════════════════════════════════════════════════
          §1  HERO — full-width, light bg, bold headline, purple accents
          ════════════════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden bg-gradient-to-b from-purple-50/80 via-white to-white">
        {/* Subtle decorative blobs */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[600px] bg-gradient-to-br from-purple-200/30 via-purple-100/20 to-transparent rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-40 right-0 w-[400px] h-[400px] bg-gradient-to-bl from-teal-100/30 to-transparent rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-6 pt-32 sm:pt-40 pb-20 sm:pb-28">
          <div className="grid lg:grid-cols-2 gap-16 lg:gap-20 items-center">
            {/* Left — Copy */}
            <div>
              <FadeIn>
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-100 text-purple-700 text-sm font-medium mb-6">
                  <Sparkles className="w-4 h-4" />
                  AI-powered job applications
                </div>
              </FadeIn>

              <FadeIn delay={100}>
                <h1 className="text-[clamp(2.5rem,5.5vw,4.25rem)] font-extrabold leading-[1.08] tracking-[-0.035em] text-gray-900">
                  Your next job,<br />
                  <span className="text-purple-600">applied to while</span><br />
                  you sleep.
                </h1>
              </FadeIn>

              <FadeIn delay={200}>
                <p className="mt-6 text-lg sm:text-xl leading-relaxed text-gray-500 max-w-[520px]">
                  Upload your resume once. Our AI reads every listing, tailors your application, and submits it — hundreds of times a day, every day.
                </p>
              </FadeIn>

              <FadeIn delay={300}>
                <div className="mt-10 max-w-[500px]">
                  <EmailForm variant="hero" />
                  <p className="mt-4 text-sm text-gray-400 pl-1">Free plan available · No credit card required</p>
                </div>
              </FadeIn>

              <FadeIn delay={400}>
                <div className="mt-10 flex items-center gap-6 text-sm text-gray-400">
                  <span className="w-10 h-px bg-gray-200" />
                  <span>Averaging <strong className="text-gray-600 font-semibold">127 applications per user</strong> in the first 7 days</span>
                </div>
              </FadeIn>
            </div>

            {/* Right — Live activity feed */}
            <FadeIn delay={500} className="hidden lg:block">
              <div className="relative">
                <div className="absolute -inset-4 bg-gradient-to-br from-purple-100/50 to-teal-50/50 rounded-3xl blur-xl" />
                <div className="relative bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/80 shadow-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-sm font-semibold text-gray-700">Live Activity</span>
                    <span className="text-xs text-gray-400 ml-auto">Real-time updates</span>
                  </div>
                  <LiveActivityFeed />
                </div>
              </div>
            </FadeIn>
          </div>
        </div>

        {/* Trust bar */}
        <FadeIn>
          <div className="relative max-w-7xl mx-auto px-6 pb-16">
            <p className="text-sm text-gray-400 text-center mb-6">Trusted by job seekers landing roles at</p>
            <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4 opacity-40 grayscale">
              {["Google", "Amazon", "Meta", "Microsoft", "Stripe", "Shopify"].map((name) => (
                <span key={name} className="text-lg font-bold text-gray-900 tracking-tight">{name}</span>
              ))}
            </div>
          </div>
        </FadeIn>
      </section>

      {/* ════════════════════════════════════════════════════════════════════
          §2  THREE-COLUMN FEATURE CARDS (Podia's Store/Website/Email style)
          ════════════════════════════════════════════════════════════════════ */}
      <section className="bg-white py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-extrabold tracking-tight text-gray-900">
                Everything you need to land interviews
              </h2>
              <p className="mt-4 text-lg text-gray-500">
                One platform that handles precision matching, quality applications, and real-time tracking.
              </p>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Target,
                title: "Precision Matching",
                desc: "Our AI analyzes thousands of listings and only applies to roles that truly match your skills, experience, and preferences.",
                color: "purple",
                link: "#how-it-works",
              },
              {
                icon: Sparkles,
                title: "Curated Quality",
                desc: "Every resume and cover letter is custom-tailored for each role. ATS-optimized, company-tone matched, and personally branded.",
                color: "teal",
                link: "#features",
              },
              {
                icon: Activity,
                title: "Live Activity",
                desc: "Track every application in real-time. See matches, submissions, and responses as they happen — all from your dashboard.",
                color: "indigo",
                link: "#dashboard",
              },
            ].map((card, idx) => (
              <FadeIn key={card.title} delay={idx * 150}>
                <a
                  href={card.link}
                  className="group block p-8 rounded-2xl border-2 border-gray-100 hover:border-purple-200 bg-white hover:bg-purple-50/30 transition-all duration-300 hover:shadow-xl hover:shadow-purple-100/50 hover:-translate-y-1"
                >
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center mb-6",
                    card.color === "purple" ? "bg-purple-100 text-purple-600"
                      : card.color === "teal" ? "bg-teal-100 text-teal-600"
                      : "bg-indigo-100 text-indigo-600"
                  )}>
                    <card.icon className="w-7 h-7" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                    {card.title}
                    <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-purple-500 group-hover:translate-x-1 transition-all" />
                  </h3>
                  <p className="text-[15px] text-gray-500 leading-relaxed">{card.desc}</p>
                </a>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════════
          §3  SUCCESS STORIES / TESTIMONIALS
          ════════════════════════════════════════════════════════════════════ */}
      <section className="bg-gray-50 py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-extrabold tracking-tight text-gray-900">
                Job seekers found their dream roles with JobHuntin
              </h2>
              <p className="mt-4 text-lg text-gray-500">
                More than 10,000 professionals trust JobHuntin to automate their job search. Here's what they say.
              </p>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                q: "Got 4 interviews in my first week. I'd been applying manually for 3 months with nothing.",
                n: "Sarah K.",
                r: "Marketing Manager",
                res: "Landed at HubSpot",
                initials: "SK",
                color: "bg-purple-100 text-purple-700",
              },
              {
                q: "The cover letters are genuinely better than what I'd write myself. Not generic at all.",
                n: "Marcus T.",
                r: "Software Engineer",
                res: "Landed at Stripe",
                initials: "MT",
                color: "bg-teal-100 text-teal-700",
              },
              {
                q: "Found a listing 20 minutes after it was posted and applied instantly. That's how I got my current role.",
                n: "Priya R.",
                r: "Product Designer",
                res: "Landed at Figma",
                initials: "PR",
                color: "bg-indigo-100 text-indigo-700",
              },
              {
                q: "Landed 7 interviews in 2 weeks. The AI matched me with roles I didn't even know existed.",
                n: "James L.",
                r: "Data Analyst",
                res: "Landed at Netflix",
                initials: "JL",
                color: "bg-amber-100 text-amber-700",
              },
              {
                q: "I was skeptical about AI applications, but every single one was personalized. My response rate doubled.",
                n: "Elena M.",
                r: "Product Manager",
                res: "Landed at Airbnb",
                initials: "EM",
                color: "bg-rose-100 text-rose-700",
              },
            ].map((t, idx) => (
              <FadeIn key={t.n} delay={idx * 100}>
                <div className="bg-white rounded-2xl p-8 border border-gray-100 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col">
                  <div className="flex gap-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
                    ))}
                  </div>
                  <p className="text-[15px] text-gray-600 leading-relaxed flex-1 mb-6">"{t.q}"</p>
                  <div className="flex items-center gap-3 pt-4 border-t border-gray-100">
                    <div className={cn("w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold", t.color)}>
                      {t.initials}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{t.n}</p>
                      <p className="text-xs text-gray-400">{t.r} · {t.res}</p>
                    </div>
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>

          <FadeIn delay={400}>
            <div className="text-center mt-12">
              <Link
                to="/success-stories"
                className="inline-flex items-center gap-2 text-purple-600 hover:text-purple-700 font-semibold text-[15px] group"
              >
                Read more success stories
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════════
          §4  HOW IT WORKS — 4 steps, numbered cards with icons
          ════════════════════════════════════════════════════════════════════ */}
      <section id="how-it-works" className="bg-white py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-20">
              <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-extrabold tracking-tight text-gray-900">
                How it works
              </h2>
              <p className="mt-4 text-lg text-gray-500">
                Four simple steps. Under two minutes to set up. Then it runs on autopilot — 24/7.
              </p>
            </div>
          </FadeIn>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-6">
            {[
              {
                n: "01",
                icon: Upload,
                t: "Initialize",
                d: "Upload your resume. Our AI parses your skills, experience, and career goals instantly.",
                color: "purple",
              },
              {
                n: "02",
                icon: SlidersHorizontal,
                t: "Strategic Matching",
                d: "Set your filters — roles, locations, salary, company size. We only apply to what truly matches.",
                color: "teal",
              },
              {
                n: "03",
                icon: Send,
                t: "Crafted Applications",
                d: "Every application is individually tailored. Custom resume, cover letter, and optimal submission timing.",
                color: "indigo",
              },
              {
                n: "04",
                icon: Trophy,
                t: "Interview Ready",
                d: "Get interview prep insights, response tracking, and real-time updates on every application.",
                color: "amber",
              },
            ].map((step, idx) => (
              <FadeIn key={step.n} delay={idx * 150}>
                <div className="relative group">
                  {/* Connector line (hidden on mobile) */}
                  {idx < 3 && (
                    <div className="hidden lg:block absolute top-10 left-full w-full h-px bg-gradient-to-r from-gray-200 to-transparent z-0" />
                  )}
                  <div className="relative bg-white rounded-2xl p-8 border-2 border-gray-100 hover:border-purple-200 transition-all hover:shadow-lg hover:shadow-purple-100/30 hover:-translate-y-1">
                    <span className="text-xs font-bold text-gray-300 uppercase tracking-widest">{step.n}</span>
                    <div className={cn(
                      "w-14 h-14 rounded-2xl flex items-center justify-center mt-4 mb-5",
                      step.color === "purple" ? "bg-purple-100 text-purple-600"
                        : step.color === "teal" ? "bg-teal-100 text-teal-600"
                        : step.color === "indigo" ? "bg-indigo-100 text-indigo-600"
                        : "bg-amber-100 text-amber-600"
                    )}>
                      <step.icon className="w-7 h-7" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">{step.t}</h3>
                    <p className="text-[15px] text-gray-500 leading-relaxed">{step.d}</p>
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>

          <FadeIn delay={500}>
            <div className="text-center mt-14">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 h-[52px] px-10 rounded-full text-[15px] font-semibold bg-purple-600 text-white hover:bg-purple-700 hover:shadow-lg hover:shadow-purple-600/25 hover:-translate-y-0.5 transition-all"
              >
                Get Started Free <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="mt-3 text-sm text-gray-400">Set up in 2 minutes — your first applications go out today</p>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════════
          §5  DASHBOARD SHOWCASE ("Designs that turn heads" section)
          ════════════════════════════════════════════════════════════════════ */}
      <section id="dashboard" className="bg-gradient-to-b from-gray-50 to-white py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-extrabold tracking-tight text-gray-900">
                A dashboard that keeps you in control.
              </h2>
              <p className="mt-4 text-lg text-gray-500">
                Track every application, see live matches, and review AI-crafted submissions — all in one place.
              </p>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Monitor,
                title: "Live Activity Feed",
                desc: "Watch applications go out in real-time. See matched roles, submitted apps, and company responses as they happen.",
                mockLabel: "12 applications today",
              },
              {
                icon: Layout,
                title: "Application Tracker",
                desc: "Every application organized with status tracking: Applied, Viewed, Interview, Offered. Never lose track again.",
                mockLabel: "47 active applications",
              },
              {
                icon: Smartphone,
                title: "Mobile Optimized",
                desc: "Check your job search progress anywhere. Fully responsive dashboard with real-time push notifications.",
                mockLabel: "3 new responses",
              },
            ].map((card, idx) => (
              <FadeIn key={card.title} delay={idx * 150}>
                <div className="group bg-white rounded-2xl border-2 border-gray-100 overflow-hidden hover:border-purple-200 hover:shadow-xl hover:shadow-purple-100/30 transition-all hover:-translate-y-1">
                  {/* Mock preview area */}
                  <div className="h-48 bg-gradient-to-br from-gray-50 to-purple-50 flex items-center justify-center border-b border-gray-100 relative overflow-hidden">
                    <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzAwMCIgc3Ryb2tlLW9wYWNpdHk9IjAuMDMiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-50" />
                    <div className="relative flex flex-col items-center gap-2">
                      <card.icon className="w-10 h-10 text-purple-400" />
                      <span className="text-xs font-semibold text-purple-600 bg-purple-100 px-3 py-1 rounded-full">{card.mockLabel}</span>
                    </div>
                  </div>
                  <div className="p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-2">{card.title}</h3>
                    <p className="text-[15px] text-gray-500 leading-relaxed mb-4">{card.desc}</p>
                    <Link
                      to="/login"
                      className="inline-flex items-center gap-1.5 text-purple-600 hover:text-purple-700 font-semibold text-sm group/link"
                    >
                      View dashboard
                      <ChevronRight className="w-4 h-4 group-hover/link:translate-x-1 transition-transform" />
                    </Link>
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════════
          §6  WHAT MAKES IT DIFFERENT — clean alternating feature blocks
          ════════════════════════════════════════════════════════════════════ */}
      <section className="bg-white py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-20">
              <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-extrabold tracking-tight text-gray-900">
                Not another job board.<br />
                An agent that does the work.
              </h2>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-2 gap-x-20 gap-y-16">
            {[
              {
                icon: PenTool,
                t: "Tailored, not templated",
                d: "Every resume and cover letter is rewritten for the specific role. We match your experience to the job description, adjust tone for the company, and optimize for ATS systems.",
              },
              {
                icon: Clock,
                t: "Always on",
                d: "New jobs get posted at 2am, on weekends, on holidays. Our agent monitors boards continuously and applies within minutes of a listing going live.",
              },
              {
                icon: Shield,
                t: "You stay in control",
                d: "Review every application before it goes out, or let the agent run autonomously. Pause anytime. Adjust filters on the fly. Your data is encrypted and never shared.",
              },
              {
                icon: Zap,
                t: "Built for volume",
                d: "The average person applies to 5 jobs a week. Our users average 18 per day. More applications, better targeting, more interviews.",
              },
            ].map((item, idx) => (
              <FadeIn key={item.t} delay={idx * 100}>
                <div className="flex gap-5">
                  <div className="w-12 h-12 rounded-2xl bg-purple-100 text-purple-600 flex items-center justify-center shrink-0">
                    <item.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">{item.t}</h3>
                    <p className="text-[15px] text-gray-500 leading-relaxed">{item.d}</p>
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════════
          §7  COMPREHENSIVE FEATURES GRID (like Podia's checklist)
          ════════════════════════════════════════════════════════════════════ */}
      <section id="features" className="bg-gray-50 py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="text-center max-w-3xl mx-auto mb-6">
              <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-extrabold tracking-tight text-gray-900">
                Everything you need to run your job search, right out of the box.
              </h2>
            </div>
          </FadeIn>

          <FadeIn delay={100}>
            <div className="text-center max-w-xl mx-auto mb-16">
              <p className="text-gray-500 italic text-[15px]">
                "Instead of worrying about 20 different tools for resumes, tracking, and applications…I just run my search from JobHuntin."
              </p>
              <p className="mt-2 text-sm text-gray-400">– Sarah K., Marketing Manager</p>
            </div>
          </FadeIn>

          <FadeIn delay={200}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {[
                "AI resume analysis",
                "Custom cover letters",
                "ATS optimization",
                "Thousands of positions",
                "Real-time tracking",
                "Interview prep insights",
                "Personalized applications",
                "Salary filtering",
                "Company size filters",
                "Location preferences",
                "Role matching AI",
                "Auto-apply engine",
                "Application dashboard",
                "Response tracking",
                "Resume versioning",
                "Email notifications",
                "Mobile dashboard",
                "Data encryption",
                "Bulk applications",
                "Smart scheduling",
                "Company research",
                "Skills gap analysis",
                "Application analytics",
                "Priority support",
              ].map((feature) => (
                <div
                  key={feature}
                  className="flex items-center gap-3 px-4 py-3.5 rounded-xl bg-white border border-gray-100 hover:border-purple-200 hover:bg-purple-50/30 transition-colors"
                >
                  <div className="w-5 h-5 rounded-full bg-purple-100 flex items-center justify-center shrink-0">
                    <svg className="w-3 h-3 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-gray-700">{feature}</span>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════════════
          §8  FINAL BIG CTA
          ════════════════════════════════════════════════════════════════════ */}
      <section className="bg-gradient-to-b from-white to-purple-50/60 py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <FadeIn>
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-[clamp(2rem,5vw,3.25rem)] font-extrabold tracking-tight text-gray-900 leading-tight">
                Job searching is much simpler<br />when AI does the heavy lifting.
              </h2>
              <p className="mt-6 text-lg text-gray-500 max-w-lg mx-auto">
                Stop applying manually. Set it up in 2 minutes and your first applications go out today.
              </p>
              <div className="mt-10 max-w-[480px] mx-auto">
                <EmailForm variant="light" />
              </div>
              <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-gray-400">
                <span className="flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  Free plan
                </span>
                <span className="flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  No credit card
                </span>
                <span className="flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  Cancel anytime
                </span>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── Sticky mobile CTA ── */}
      {stickyVisible && (
        <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-white/95 backdrop-blur-sm border-t border-gray-200 p-3 shadow-lg">
          <Link
            to="/login"
            className="flex items-center justify-center gap-2 w-full h-12 rounded-full text-[15px] font-semibold bg-purple-600 text-white hover:bg-purple-700 transition-colors"
          >
            Get Started Free <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </>
  );
}