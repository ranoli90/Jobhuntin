import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { CheckCircle, Zap, ChevronDown, X, Sparkles, ArrowRight } from 'lucide-react';
import { t, getLocale } from '../lib/i18n';
import { motion, useReducedMotion, AnimatePresence } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { useAuth } from '../hooks/useAuth';
import { useBilling } from '../hooks/useBilling';
import { telemetry } from '../lib/telemetry';
import { PricingSkeleton } from '../components/ui/Skeleton';
import { cn } from '../lib/utils';

function ExitIntentPopup({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) return;
    const focusables = contentRef.current?.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const first = focusables?.[0] as HTMLElement | undefined;
    first?.focus();
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            ref={contentRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="exit-intent-title"
            aria-describedby="exit-intent-desc"
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="rounded-2xl p-8 max-w-md w-full shadow-2xl relative overflow-hidden border border-white/10 bg-[#2D2A26]"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 min-h-[44px] min-w-[44px] p-2 flex items-center justify-center text-white/50 hover:text-white hover:bg-white/10 rounded-full transition-colors"
              aria-label="Close popup"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="relative z-10">
              <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-6" style={{ background: 'rgba(69,93,211,0.2)' }}>
                <Zap className="w-8 h-8 text-[#7DD3CF]" />
              </div>

              <h3 id="exit-intent-title" className="text-2xl font-bold text-white mb-3 tracking-tight">
                Wait! Don't miss out
              </h3>

              <p id="exit-intent-desc" className="text-white/70 mb-6 leading-relaxed font-medium">
                Join <span className="font-bold text-white">thousands of job seekers</span> who automated their job search.
                Get your first interviews in just 48 hours.
              </p>

              <div className="space-y-3">
                <Link
                  to="/login"
                  onClick={onClose}
                  className="block w-full h-12 rounded-lg bg-[#455DD3] text-white font-bold text-center leading-[48px] hover:bg-[#3A4FB8] transition-colors"
                >
                  Start free
                </Link>

                <button
                  onClick={onClose}
                  className="block w-full h-12 text-white/60 font-medium hover:text-white transition-colors focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-[#2D2A26] focus-visible:outline-none rounded-lg"
                >
                  Maybe later
                </button>
              </div>

              <p className="text-xs text-white/40 text-center mt-4">
                20 free applications per week. No credit card required.
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function FAQItem({ question, answer, id }: { question: string; answer: string; id: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="border-b border-[#E9E9E7] pb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-[#455DD3] focus-visible:ring-offset-2 focus-visible:rounded-lg"
        aria-expanded={isOpen}
        aria-controls={`faq-answer-${id}`}
      >
        <span className="font-bold text-lg text-[#2D2A26] pr-4">{question}</span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.2 }}
        >
          <ChevronDown className="w-5 h-5 text-[#787774] flex-shrink-0" aria-hidden="true" />
        </motion.div>
      </button>
      <motion.div
        id={`faq-answer-${id}`}
        initial={false}
        animate={{
          height: isOpen ? "auto" : 0,
          opacity: isOpen ? 1 : 0,
        }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, ease: "easeInOut" }}
        className="overflow-hidden"
      >
        <p className="pt-3 text-[#787774] font-medium leading-relaxed">{answer}</p>
      </motion.div>
    </div>
  );
}

export default function Pricing() {
  const [showExitIntent, setShowExitIntent] = useState(false);
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const { plan, loading: billingLoading, upgrade } = useBilling();
  const locale = getLocale();

  const isLoggedIn = !!user;
  const isProOrHigher = plan === 'PRO' || plan === 'TEAM';

  useEffect(() => {
    if (isLoggedIn || isProOrHigher) return;
    if (sessionStorage.getItem('exitIntentShown')) return;

    let mouseY = 0;
    const handleMouseMove = (e: MouseEvent) => { mouseY = e.clientY; };
    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY < 10 && mouseY < 100 && !sessionStorage.getItem('exitIntentShown')) {
        setShowExitIntent(true);
        sessionStorage.setItem('exitIntentShown', 'true');
        telemetry.track("exit_intent_triggered", { page: "pricing" });
      }
    };

    if (window.innerWidth >= 1024) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseleave', handleMouseLeave);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [isLoggedIn, isProOrHigher]);

  const handleFreeCta = () => {
    if (isLoggedIn) navigate('/app/jobs');
    else navigate('/login');
  };

  const handleProCta = async () => {
    if (!isLoggedIn) {
      navigate(`/login?returnTo=${encodeURIComponent('/pricing')}`);
      return;
    }
    if (isProOrHigher) {
      navigate('/app/billing');
      return;
    }
    telemetry.track("upgrade_clicked", { source: "pricing", tier: "pro" });
    try {
      await upgrade("monthly");
    } catch (err) {
      if (import.meta.env.DEV) console.error('Checkout failed:', err);
    }
  };

  const getProCtaLabel = () => {
    if (authLoading || billingLoading) return t("app.loading", locale);
    if (!isLoggedIn) return "Get Unlimited";
    if (isProOrHigher) return "Current Plan";
    return "Get Unlimited";
  };

  const [showSkeleton, setShowSkeleton] = React.useState(true);
  React.useEffect(() => {
    const timer = setTimeout(() => setShowSkeleton(false), 1500);
    return () => clearTimeout(timer);
  }, []);

  if ((authLoading || billingLoading) && showSkeleton) {
    return <PricingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-[#F7F6F3] text-[#2D2A26] pb-20">
      <ExitIntentPopup isOpen={showExitIntent} onClose={() => setShowExitIntent(false)} />
      <SEO
        title="Pricing | JobHuntin: Start free, Upgrade to Unlimited"
        description="JobHuntin pricing: Start with 20 free applications per week. Upgrade to unlimited for $10 first month, then $29/month. Get hired faster with AI automation."
        ogTitle="JobHuntin Pricing: Start free"
        ogImage="https://jobhuntin.com/og-image.png"
        canonicalUrl="https://jobhuntin.com/pricing"
        includeDate={true}
        breadcrumbs={[{ name: "Home", url: "https://jobhuntin.com" }, { name: "Pricing", url: "https://jobhuntin.com/pricing" }]}
        keywords="JobHuntin pricing, AI job search cost, auto apply pricing, job automation price"
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "JobHuntin Pro",
            "description": "AI-powered job application automation with unlimited applications, resume tailoring, and interview coaching.",
            "offers": [
              { "@type": "Offer", "name": "Free Tier", "url": "https://jobhuntin.com/pricing", "priceCurrency": "USD", "price": "0", "description": "20 applications per week" },
              { "@type": "Offer", "name": "Pro - Launch Special", "url": "https://jobhuntin.com/pricing", "priceCurrency": "USD", "price": "10", "description": "First month $10, then $29/month" }
            ]
          },
          {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
              { "@type": "Question", "name": "What happens after my 20 free applications?", "acceptedAnswer": { "@type": "Answer", "text": "Your free applications reset every Monday. If you need more, upgrade to Pro for unlimited applications." } },
              { "@type": "Question", "name": "Can I cancel anytime?", "acceptedAnswer": { "@type": "Answer", "text": "Yes. Cancel anytime in your dashboard. No questions asked." } }
            ]
          }
        ]}
      />

      {/* Hero — homepage style */}
      <section className="relative overflow-hidden" style={{ background: 'linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)' }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(69,93,211,0.15) 0%, transparent 60%)' }} />
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-60" preserveAspectRatio="none" viewBox="0 0 1440 400" aria-hidden="true">
          <path d="M-100 200 C200 120, 500 280, 800 200 S1200 100, 1540 180" stroke="#455DD3" strokeOpacity="0.15" strokeWidth="2" fill="none" />
          <path d="M-100 250 C300 170, 600 330, 900 250 S1300 150, 1540 230" stroke="#7B93DB" strokeOpacity="0.1" strokeWidth="1.5" fill="none" />
        </svg>

        <div className="relative max-w-[1080px] mx-auto px-6 py-20 sm:py-28">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white px-4 py-2 rounded-lg text-sm font-semibold mb-6 border border-white/20">
            <Sparkles className="w-4 h-4" />
            Launch Special: 80% Off First Month
          </div>
          <h1 className="text-[clamp(2.25rem,5vw,3.5rem)] font-bold text-white leading-tight mb-4" style={{ letterSpacing: '-1.5px' }}>
            Start free.<br />
            <span className="text-[#7DD3CF]">Upgrade when you're ready.</span>
          </h1>
          <p className="text-lg text-white/70 max-w-xl font-medium">
            20 free applications every week. No credit card required.
          </p>
        </div>
      </section>

      {/* Main pricing — editorial layout, not cards */}
      <main className="max-w-[900px] mx-auto px-6 -mt-12 relative z-10">
        {/* Start free — primary offer */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="rounded-2xl border-2 border-[#E9E9E7] bg-white p-8 sm:p-10 lg:p-12 shadow-lg shadow-black/5 hover:shadow-xl hover:shadow-black/8 transition-shadow duration-300"
          aria-labelledby="pricing-free-heading"
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-[#787774] mb-2">Free forever</p>
              <h2 id="pricing-free-heading" className="text-3xl sm:text-4xl font-bold text-[#2D2A26] mb-3" style={{ letterSpacing: '-1px' }}>
                20 applications per week
              </h2>
              <p className="text-[#787774] font-medium mb-6 max-w-md">
                AI-powered applications, smart matching, resume parsing, and tracking. Resets every Monday.
              </p>
              <ul className="space-y-3">
                {["20 AI-Powered Applications/week", "Smart Job Matching", "Basic Resume Parsing", "Application Tracking", "Weekly Reset (Every Monday)"].map((f, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-[#16A34A] shrink-0" />
                    <span className="text-[#2D2A26] font-medium">{f}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="lg:w-[280px] shrink-0">
              <div className="text-5xl font-bold text-[#2D2A26] mb-1">$0</div>
              <p className="text-sm text-[#787774] font-medium mb-6">forever</p>
              <button
                onClick={handleFreeCta}
                className="w-full h-12 rounded-lg font-semibold text-white bg-[#455DD3] hover:bg-[#3A4FB8] transition-colors flex items-center justify-center gap-2 shadow-lg shadow-[#455DD3]/20 active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-[#455DD3] focus-visible:ring-offset-2 focus-visible:outline-none"
              >
                {isLoggedIn ? "Go to Dashboard" : "Start free"} <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.section>

        {/* Pro — upgrade path, warm dark block */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mt-6 rounded-2xl border border-white/10 bg-[#2D2A26] p-8 sm:p-10 lg:p-12 relative overflow-hidden hover:border-white/15 transition-colors duration-300"
          aria-labelledby="pricing-pro-heading"
        >
          <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 60% 40% at 100% 0%, rgba(69,93,211,0.1) 0%, transparent 70%)' }} />
          <div className="relative flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <p className="text-xs font-bold uppercase tracking-widest text-white/50">Pro</p>
                <Zap className="w-4 h-4 text-[#7DD3CF]" />
              </div>
              <h2 id="pricing-pro-heading" className="text-2xl sm:text-3xl font-bold text-white mb-3" style={{ letterSpacing: '-1px' }}>
                Unlimited applications
              </h2>
              <p className="text-white/70 font-medium mb-6 max-w-md">
                Everything in Free, plus resume tailoring, cover letters, stealth mode, and priority support.
              </p>
              <ul className="space-y-3">
                {["Unlimited AI Applications", "Resume Tailored for Every Job", "Custom Cover Letters", "Stealth Mode", "Priority Support", "LinkedIn Sync", "Interview Coaching"].map((f, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-[#7DD3CF] shrink-0" />
                    <span className="text-white font-medium">{f}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="lg:w-[240px] shrink-0">
              <div className="flex items-baseline gap-1 mb-1">
                <span className="text-4xl font-bold text-white">$10</span>
                <span className="text-sm text-white/50 font-medium">first month</span>
              </div>
              <p className="text-[10px] text-white/40 uppercase font-bold tracking-widest mb-6">
                Then $29/month • Cancel anytime
              </p>
              <button
                onClick={handleProCta}
                disabled={isProOrHigher}
                aria-label={isProOrHigher ? "View current plan in billing" : "Get unlimited applications"}
                className={cn(
                  "w-full h-12 rounded-lg font-semibold transition-colors active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-[#2D2A26] focus-visible:outline-none",
                  isProOrHigher
                    ? "bg-white/50 text-[#2D2A26]/70 cursor-default"
                    : "bg-white text-[#2D2A26] hover:bg-white/90"
                )}
              >
                {getProCtaLabel()}
              </button>
            </div>
          </div>
        </motion.section>

        {/* Trust */}
        <div className="mt-16 text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-[#787774] mb-4">Trusted by job seekers at</p>
          <div className="flex justify-center flex-wrap gap-8 text-[#787774]">
            {['Walmart', 'Target', 'Amazon', 'Costco', 'Home Depot'].map((c) => (
              <span key={c} className="text-lg font-bold">{c}</span>
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-24 border-t border-[#E9E9E7] pt-16">
          <h2 className="text-2xl font-bold text-center mb-12 text-[#2D2A26]" style={{ letterSpacing: '-0.5px' }}>
            Frequently Asked Questions
          </h2>
          <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
            {[
              { q: "What happens after my 20 free applications?", a: "Your free applications reset every Monday at midnight UTC. If you need more before the reset, you can upgrade to Pro for unlimited applications." },
              { q: "Can I cancel Pro anytime?", a: "Yes. Cancel anytime in your dashboard with one click. No phone calls, no hassle. You'll keep access until your billing period ends." },
              { q: "What happens after the first month?", a: "After your $10 first month, you'll be charged $29/month. We'll send you a reminder 3 days before the price change." },
              { q: "Is my data safe?", a: "We use bank-level encryption. Your resume is only shared with employers you choose to apply to. We never sell your data." },
              { q: "How does the weekly reset work?", a: "Every Monday at midnight UTC, your free application count resets to 20. Unused applications don't roll over." },
              { q: "Can I get a refund?", a: "If you're not satisfied, contact us within 7 days of upgrading for a full refund. No questions asked." },
            ].map((item, i) => (
              <FAQItem key={i} id={`faq-${i}`} question={item.q} answer={item.a} />
            ))}
          </div>
        </div>

        {/* Compare Our Pricing */}
        <section className="mt-16 max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-center text-slate-900 mb-6">Compare Our Pricing</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            {['lazyapply', 'jobright', 'simplify'].map(slug => (
              <Link key={slug} to={`/pricing-vs/${slug}`} className="bg-white p-5 rounded-2xl border border-slate-100 hover:border-primary-200 shadow-sm text-center transition-all">
                <p className="font-bold text-slate-900 capitalize">{slug.replace(/-/g, ' ')} vs JobHuntin</p>
                <p className="text-sm text-primary-600 mt-1">Compare pricing →</p>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
