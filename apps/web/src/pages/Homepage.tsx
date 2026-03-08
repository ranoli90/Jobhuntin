import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import { telemetry } from '../lib/telemetry';
import {
  ArrowRight, MailCheck, Menu, X, Check, ChevronRight
} from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { cn } from '../lib/utils';
import { ValidationUtils } from '../lib/validation';

/* ─── Mobile navigation hook ─── */
function useMobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const toggle = () => setIsOpen(!isOpen);
  const close = () => setIsOpen(false);
  return { isOpen, toggle, close };
}

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

/* ─── Email form (Notion style) ─── */
function EmailForm({ variant = "light" }: { variant?: "light" | "dark" }) {
  const { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit } = useEmailCapture();
  if (sentEmail) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-lg bg-[#F7F6F3] border border-[#E9E9E7]">
        <div className="w-8 h-8 rounded-lg bg-black flex items-center justify-center">
          <MailCheck className="w-4 h-4 text-white" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-[#2D2A26]">Check your inbox</p>
          <p className="text-xs text-[#787774] truncate mt-0.5">{sentEmail}</p>
        </div>
        <button 
          onClick={() => setSentEmail(null)} 
          className="text-xs font-medium text-[#2D2A26] hover:text-[#4A4540] transition-colors"
        >
          Change
        </button>
      </div>
    );
  }
  return (
    <div className="w-full max-w-md">
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <input 
          type="email" 
          placeholder="Enter your email" 
          aria-label="Email address"
          className={cn(
            "w-full h-12 px-4 rounded-md border bg-white text-[#2D2A26] placeholder:text-[#9B9A97]",
            "focus:outline-none focus:ring-2 focus:ring-[#2D2A26] focus:border-[#2D2A26]",
            "transition-colors",
            variant === "dark" ? "border-[#37352F] bg-[#2F2E2B] text-white" : "border-[#E9E9E7]",
            emailError && "border-red-500 focus:border-red-500 focus:ring-red-500"
          )} 
          value={email} 
          onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button 
          type="submit" 
          disabled={isSubmitting}
          className={cn(
            "w-full h-12 px-6 rounded-md font-medium transition-all duration-150",
            "focus:outline-none focus:ring-2 focus:ring-offset-2",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "bg-[#FFC107] text-white hover:bg-[#FFA000] focus:ring-[#FFC107]",
            "flex items-center justify-center gap-2"
          )}
        >
          {isSubmitting ? "Sending..." : "Get started free"}
          {!isSubmitting && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>
      {emailError && (
        <p className="mt-2 text-xs text-red-500">{emailError}</p>
      )}
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

/* ━━━ HOMEPAGE ━━━ */
export default function Homepage() {
  const { isOpen, toggle, close } = useMobileNav();

  return (
    <>
      {/* Skip to main content for accessibility */}
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-black focus:text-white focus:rounded-lg focus:font-medium">
        Skip to main content
      </a>

      <SEO
        title="JobHuntin — One resume. Zero applications."
        description="Upload your resume once. Our AI applies to hundreds of matching jobs while you sleep. Land interviews without the work."
        ogTitle="JobHuntin — One resume. Zero applications."
        canonicalUrl="https://jobhuntin.com/"
        schema={{ "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD", "description": "20 free applications per week. Upgrade to unlimited for $10 first month." }, "description": "AI-powered job application automation platform." }}
      />

      {/* ═══════════════════════════════════════════════════════════════
          NOTION-STYLE NAVIGATION
          ═══════════════════════════════════════════════════════════════ */}
      <nav className="sticky top-0 z-50 bg-white border-b border-[#E9E9E7]">
        <div className="max-w-6xl mx-auto px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="text-2xl font-black tracking-tight text-[#2D2A26]">
              JobHuntin
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="small-text text-[#2D2A26] hover:text-[#4A4540] hover:scale-105 transition-all duration-200">
                Features
              </a>
              <a href="#how-it-works" className="small-text text-[#2D2A26] hover:text-[#4A4540] hover:scale-105 transition-all duration-200">
                How it works
              </a>
              <a href="#pricing" className="small-text text-[#2D2A26] hover:text-[#4A4540] hover:scale-105 transition-all duration-200">
                Pricing
              </a>
              <Link to="/login" className="small-text text-[#2D2A26] hover:text-[#4A4540] hover:scale-105 transition-all duration-200">
                Sign in
              </Link>
            </div>

            {/* Mobile menu button */}
            <button 
              onClick={toggle} 
              className="md:hidden p-3 rounded-lg text-[#2D2A26] hover:bg-[#F7F6F3] transition-colors touch-manipulation" 
              aria-label="Toggle navigation"
            >
              {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isOpen && (
          <div className="md:hidden absolute top-16 left-0 right-0 bg-white border-b border-[#E9E9E7] shadow-lg">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-2">
              <a href="#features" onClick={close} className="block px-4 py-3 text-base font-medium text-[#2D2A26] hover:bg-[#F7F6F3] hover:text-[#4A4540] transition-colors rounded-lg">
                Features
              </a>
              <a href="#how-it-works" onClick={close} className="block px-4 py-3 text-base font-medium text-[#2D2A26] hover:bg-[#F7F6F3] hover:text-[#4A4540] transition-colors rounded-lg">
                How it works
              </a>
              <a href="#pricing" onClick={close} className="block px-4 py-3 text-base font-medium text-[#2D2A26] hover:bg-[#F7F6F3] hover:text-[#4A4540] transition-colors rounded-lg">
                Pricing
              </a>
              <Link to="/login" onClick={close} className="block px-4 py-3 text-base font-medium text-[#2D2A26] hover:bg-[#F7F6F3] hover:text-[#4A4540] transition-colors rounded-lg">
                Sign in
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* ═══════════════════════════════════════════════════════════════
          NOTION-STYLE HERO
          ═════════════════════════════════════════════════════════════ */}
      <section id="main-content" className="bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-32">
          <div className="max-w-4xl mx-auto text-center">
            <FadeIn>
              <h1 className="hero-title text-[#2D2A26] mb-16">
                One resume.<br className="hidden sm:block" />
                Zero applications.
              </h1>
            </FadeIn>
            <FadeIn delay={100}>
              <p className="body-text text-[#5A5653] max-w-3xl mx-auto mb-20">
                Upload your resume once. Our AI finds matching jobs, tailors every application, and submits while you sleep.
              </p>
            </FadeIn>
            <FadeIn delay={200}>
              <div className="flex flex-col sm:flex-row gap-3 justify-center items-center mb-20">
                <Link to="/login" className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 h-12 px-6 rounded-lg bg-[#2D2A26] text-white font-medium hover:bg-[#4A4540] hover:scale-105 hover:shadow-lg transition-all duration-200 min-w-[140px]">
                  Get started free
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <a href="#how-it-works" className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 h-12 px-6 rounded-lg border border-[#E9E9E7] text-[#2D2A26] font-medium hover:bg-[#F7F6F3] hover:border-[#2D2A26] hover:scale-105 transition-all duration-200 min-w-[140px]">
                  See how it works
                  <ChevronRight className="w-4 h-4" />
                </a>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          TRUSTED BY SECTION
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-[#F7F6F3] py-16">
        <div className="max-w-6xl mx-auto px-8">
          <FadeIn>
            <div className="text-center mb-24">
              <p className="caption-text text-[#2D2A26] tracking-wide mb-16">
                Trusted by professionals at
              </p>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-6 sm:gap-8 lg:gap-12">
              {[
                "Google", "Meta", "Amazon", "Stripe", "Netflix", "Apple"
              ].map((company) => (
                <div key={company} className="flex items-center justify-center p-4 sm:p-6 lg:p-8 bg-white rounded-lg border border-[#E9E9E7]">
                  <span className="text-sm sm:text-base lg:text-lg font-semibold text-[#2D2A26]">{company}</span>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          FEATURES GRID
          ═══════════════════════════════════════════════════════════════ */}
      <section id="features" className="bg-white py-16">
        <div className="max-w-6xl mx-auto px-8">
          <FadeIn>
            <div className="text-center max-w-4xl mx-auto mb-24">
              <h2 className="h2-title text-[#2D2A26] mb-16">
                Everything you need to<br className="hidden sm:block" />
                automate your job search
              </h2>
              <p className="body-text text-[#5A5653] max-w-3xl mx-auto mb-16">
                Stop applying manually. Let AI handle the busywork while you focus on what matters.
              </p>
            </div>
          </FadeIn>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                title: "AI Job Matching",
                description: "Our AI scans thousands of jobs daily and matches you with roles that fit your skills, salary, and preferences.",
                icon: "🎯"
              },
              {
                title: "Resume Tailoring", 
                description: "Every application gets a custom-tailored resume and cover letter optimized for the specific role and company.",
                icon: "📝"
              },
              {
                title: "Auto-Apply Agent",
                description: "Our agent applies to matching jobs 24/7, submitting applications within minutes of new postings.",
                icon: "🤖"
              },
              {
                title: "Real-time Tracking",
                description: "Monitor every application, response, and interview invite in your clean, organized dashboard.",
                icon: "📊"
              },
              {
                title: "Interview Prep",
                description: "Get AI-generated insights about each company and role to crush your interviews.",
                icon: "🎯"
              },
              {
                title: "Salary Optimization",
                description: "We filter for roles that match your salary requirements and negotiate better offers.",
                icon: "💰"
              }
            ].map((feature, index) => (
              <FadeIn key={feature.title} delay={index * 100}>
                <div className="p-8 sm:p-12 bg-white rounded-xl border border-[#E9E9E7] hover:border-[#2D2A26] hover:shadow-xl hover:scale-105 transition-all duration-300 cursor-pointer">
                  <div className="text-3xl sm:text-4xl mb-4 sm:mb-6">{feature.icon}</div>
                  <h3 className="text-xl sm:text-2xl font-semibold text-[#2D2A26] mb-3 sm:mb-4">{feature.title}</h3>
                  <p className="text-sm sm:text-base text-[#5A5653] leading-relaxed">{feature.description}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          HOW IT WORKS
          ═══════════════════════════════════════════════════════════════ */}
      <section id="how-it-works" className="bg-[#F7F6F3] py-16">
        <div className="max-w-6xl mx-auto px-8">
          <FadeIn>
            <div className="text-center max-w-4xl mx-auto mb-20">
              <h2 className="text-5xl sm:text-6xl font-black tracking-tight text-[#2D2A26] leading-tight mb-16">
                Set up in 2 minutes.<br className="hidden sm:block" />
                Then relax.
              </h2>
              <p className="body-text text-[#5A5653] max-w-3xl mx-auto leading-relaxed">
                Three simple steps to automate your entire job search.
              </p>
            </div>
          </FadeIn>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                step: "01",
                title: "Upload Resume",
                description: "Drop your resume. We'll analyze your skills, experience, and preferences automatically."
              },
              {
                step: "02", 
                title: "Set Preferences",
                description: "Tell us what you want: role types, salary range, location, and company size."
              },
              {
                step: "03",
                title: "Watch Applications",
                description: "Our AI agent applies to matching jobs 24/7. You just check for interviews."
              }
            ].map((step, index) => (
              <FadeIn key={step.title} delay={index * 150}>
                <div className="text-center">
                  <div className="text-4xl sm:text-5xl font-black text-[#2D2A26] mb-4 sm:mb-6">{step.step}</div>
                  <h3 className="text-xl sm:text-2xl font-semibold text-[#2D2A26] mb-3 sm:mb-4">{step.title}</h3>
                  <p className="text-sm sm:text-base text-[#5A5653] leading-relaxed">{step.description}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          SOCIAL PROOF
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-white py-16">
        <div className="max-w-6xl mx-auto px-8">
          <FadeIn>
            <div className="grid md:grid-cols-3 gap-20 text-center">
              <div>
                <div className="text-6xl font-black text-[#2D2A26] mb-4">500K+</div>
                <p className="text-xl font-medium text-[#2D2A26]">Applications Sent</p>
                <p className="small-text text-[#5A5653]">By our users last month</p>
              </div>
              <div>
                <div className="text-6xl font-black text-[#2D2A26] mb-4">3.2x</div>
                <p className="text-xl font-medium text-[#2D2A26]">More Interviews</p>
                <p className="small-text text-[#5A5653]">Compared to manual applying</p>
              </div>
              <div>
                <div className="text-6xl font-black text-[#2D2A26] mb-4">92%</div>
                <p className="text-xl font-medium text-[#2D2A26]">Success Rate</p>
                <p className="small-text text-[#5A5653]">Of users land jobs in 90 days</p>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          FINAL CTA
          ═══════════════════════════════════════════════════════════════ */}
      <section className="bg-black py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-6">
          <FadeIn>
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-4xl sm:text-5xl font-black tracking-tight text-white mb-6">
                Ready to automate<br className="hidden sm:block" />
                your job search?
              </h2>
              <p className="body-text text-[#9B9A97] max-w-2xl mx-auto leading-relaxed mb-12">
                Join thousands who've reclaimed their time and landed dream roles.
              </p>
              <div className="max-w-md mx-auto">
                <EmailForm variant="dark" />
              </div>
              <div className="flex flex-wrap items-center justify-center gap-8 mt-8 text-sm text-[#9B9A97]">
                <span className="flex items-center gap-2">
                  <Check className="w-4 h-4" />
                  Free plan available
                </span>
                <span className="flex items-center gap-2">
                  <Check className="w-4 h-4" />
                  No credit card required
                </span>
                <span className="flex items-center gap-2">
                  <Check className="w-4 h-4" />
                  Cancel anytime
                </span>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Sentinel for sticky CTA hide (preserving existing functionality) */}
      <div ref={useRef<HTMLDivElement>(null)} className="h-px w-full" aria-hidden />
    </>
  );
}
