import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { CheckCircle, Zap, Crown, CreditCard, ChevronDown, X, Sparkles } from 'lucide-react';
import { t, getLocale } from '../lib/i18n';
import { motion, useReducedMotion, AnimatePresence } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { useAuth } from '../hooks/useAuth';
import { useBilling } from '../hooks/useBilling';
import { telemetry } from '../lib/telemetry';
import { cn } from '../lib/utils';
import { FadeIn } from '../components/animations/FadeIn';
import { PricingSkeleton } from '../components/ui/Skeleton';

// Exit Intent Popup Component
function ExitIntentPopup({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const locale = getLocale();

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
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-white dark:bg-slate-950 rounded-2xl p-8 max-w-md w-full shadow-2xl relative overflow-hidden border border-gray-200 dark:border-gray-800"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-gray-400 hover:text-black dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full transition-colors"
              aria-label="Close popup"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="relative z-10">
              <div className="w-16 h-16 rounded-xl bg-gray-100 dark:bg-slate-900 flex items-center justify-center mb-6 border border-gray-200 dark:border-gray-800">
                <Zap className="w-8 h-8 text-black dark:text-white" />
              </div>

              <h3 className="text-2xl font-bold text-black dark:text-white mb-3 tracking-tight">
                Wait! Don't miss out
              </h3>

              <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed font-medium">
                Join <span className="font-bold text-black dark:text-white">10,000+ job seekers</span> who automated their job search.
                Get your first interviews in just 48 hours.
              </p>

              <div className="space-y-3">
                <Link
                  to="/login"
                  onClick={onClose}
                  className="block w-full h-12 rounded-lg bg-black dark:bg-white text-white dark:text-black font-bold text-center leading-[48px] hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors border border-black dark:border-white"
                >
                  Start Free
                </Link>

                <button
                  onClick={onClose}
                  className="block w-full h-12 text-gray-500 font-medium hover:text-black dark:hover:text-white transition-colors"
                >
                  Maybe later
                </button>
              </div>

              <p className="text-xs text-slate-400 text-center mt-4">
                20 free applications per week. No credit card required.
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="border-b border-gray-200 dark:border-gray-800 pb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between text-left focus:outline-none"
        aria-expanded={isOpen}
      >
        <span className="font-bold text-lg text-black dark:text-white pr-4">{question}</span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.2 }}
        >
          <ChevronDown className="w-5 h-5 text-gray-500 flex-shrink-0" aria-hidden="true" />
        </motion.div>
      </button>
      <motion.div
        initial={false}
        animate={{
          height: isOpen ? "auto" : 0,
          opacity: isOpen ? 1 : 0,
        }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, ease: "easeInOut" }}
        className="overflow-hidden"
      >
        <p className="pt-3 text-gray-600 dark:text-gray-400 font-medium leading-relaxed">{answer}</p>
      </motion.div>
    </div>
  );
}

export default function Pricing() {
  const [showExitIntent, setShowExitIntent] = useState(false);
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const { plan, loading: billingLoading, upgrade } = useBilling();
  const shouldReduceMotion = useReducedMotion();
  const locale = getLocale();

  const isLoggedIn = !!user;
  const isProOrHigher = plan === 'PRO' || plan === 'TEAM';

  // Exit intent detection
  useEffect(() => {
    // Skip if user is logged in or already pro
    if (isLoggedIn || isProOrHigher) return;

    // Check if we've already shown the popup this session
    if (sessionStorage.getItem('exitIntentShown')) return;

    let mouseY = 0;
    const handleMouseMove = (e: MouseEvent) => {
      mouseY = e.clientY;
    };

    const handleMouseLeave = (e: MouseEvent) => {
      // Trigger when mouse leaves through the top of the page
      if (e.clientY < 10 && mouseY < 100 && !sessionStorage.getItem('exitIntentShown')) {
        setShowExitIntent(true);
        sessionStorage.setItem('exitIntentShown', 'true');
        telemetry.track("exit_intent_triggered", { page: "pricing" });
      }
    };

    // Only track on desktop
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
    if (isLoggedIn) {
      navigate('/app/jobs');
    } else {
      navigate('/login');
    }
  };

  const handleProCta = async () => {
    if (!isLoggedIn) {
      navigate('/login?returnTo=/pricing');
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

  // Show skeleton while loading auth/billing state (max 2 seconds to prevent stuck state)
  const [showSkeleton, setShowSkeleton] = React.useState(true);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setShowSkeleton(false);
    }, 1500); // Max 1.5s loading time
    return () => clearTimeout(timer);
  }, []);

  if ((authLoading || billingLoading) && showSkeleton) {
    return <PricingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 font-sans text-black dark:text-white selection:bg-gray-200 selection:text-black pb-20">
      <ExitIntentPopup isOpen={showExitIntent} onClose={() => setShowExitIntent(false)} />
      <SEO
        title="Pricing | JobHuntin: Start Free, Upgrade to Unlimited"
        description="JobHuntin pricing: Start with 20 free applications per week. Upgrade to unlimited for $10 first month, then $29/month. Get hired faster with AI automation."
        ogTitle="JobHuntin Pricing: Start Free"
        ogImage="https://jobhuntin.com/og-image.png"
        canonicalUrl="https://jobhuntin.com/pricing"
        includeDate={true}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "JobHuntin Pro",
            "description": "AI-powered job application automation with unlimited applications, resume tailoring, and interview coaching.",
            "offers": [
              {
                "@type": "Offer",
                "name": "Free Tier",
                "url": "https://jobhuntin.com/pricing",
                "priceCurrency": "USD",
                "price": "0",
                "description": "20 applications per week"
              },
              {
                "@type": "Offer",
                "name": "Pro - Launch Special",
                "url": "https://jobhuntin.com/pricing",
                "priceCurrency": "USD",
                "price": "10",
                "description": "First month $10, then $29/month"
              }
            ]
          },
          {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
              {
                "@type": "Question",
                "name": "What happens after my 20 free applications?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Your free applications reset every Monday. If you need more, upgrade to Pro for unlimited applications."
                }
              },
              {
                "@type": "Question",
                "name": "Can I cancel anytime?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Yes. Cancel anytime in your dashboard. No questions asked."
                }
              }
            ]
          }
        ]}
      />

      <main className="max-w-7xl mx-auto px-6 py-28 sm:py-36">
        <div className="text-center mb-24 relative">
          <FadeIn>
            <div className="inline-flex items-center gap-2 bg-gray-100 dark:bg-slate-900 text-black dark:text-white px-4 py-2 rounded-lg text-sm font-bold mb-6 border border-gray-200 dark:border-gray-800">
              <Sparkles className="w-4 h-4" />
              Launch Special: 80% Off First Month
            </div>
            <h1 className="text-[clamp(2.5rem,6vw,4.5rem)] font-bold text-black dark:text-white mb-6 tracking-tight leading-[1.1]">
              Start free.<br />
              <span className="text-gray-500">Upgrade when you're ready.</span>
            </h1>
          </FadeIn>

          <FadeIn delay={100}>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-10 font-medium">
              20 free applications every week. No credit card required. Upgrade to unlimited when you're ready to accelerate your job search.
            </p>
          </FadeIn>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto items-stretch">
          {/* Free Tier */}
          <motion.div
            whileHover={{ y: -4 }}
            className="bg-white dark:bg-slate-950 rounded-xl p-8 lg:p-10 border border-gray-200 dark:border-gray-800 flex flex-col h-full"
          >
            <div className="mb-8">
              <h3 className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">Free</h3>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-bold text-black dark:text-white">$0</span>
                <span className="text-sm font-medium text-gray-400">forever</span>
              </div>
              <p className="text-sm text-gray-500 mt-2 font-medium">20 applications per week</p>
            </div>

            <div className="space-y-4 mb-10 flex-1">
              {[
                "20 AI-Powered Applications/week",
                "Smart Job Matching",
                "Basic Resume Parsing",
                "Application Tracking",
                "Weekly Reset (Every Monday)"
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-black dark:text-white" />
                  <span className="text-sm font-bold text-gray-700 dark:text-gray-300">{feature}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleFreeCta}
              className="w-full py-3.5 rounded-lg border border-gray-200 dark:border-gray-800 text-black dark:text-white font-bold hover:bg-gray-50 dark:hover:bg-slate-900 transition-colors"
            >
              {isLoggedIn ? "Go to Dashboard" : "Start Free"}
            </button>
          </motion.div>

          {/* Pro Tier — Clean dark card */}
          <motion.div
            initial={{ scale: 0.98 }}
            animate={{ scale: 1 }}
            whileHover={{ y: -4 }}
            className="bg-[#1a1a1a] rounded-xl p-8 lg:p-10 border border-[#333] flex flex-col h-full relative"
          >
            <div className="mb-8 relative z-10">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400">Pro</h3>
                <Zap className="w-4 h-4 text-white" />
              </div>
              <div className="flex items-baseline gap-1 text-white">
                <span className="text-6xl font-bold">$10</span>
                <span className="text-sm font-medium text-gray-400">first month</span>
              </div>
              <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest mt-2">
                Then $29/month • Cancel anytime
              </p>
            </div>

            <div className="space-y-4 mb-10 flex-1 relative z-10">
              <p className="text-gray-400 text-sm font-medium mb-4">Everything in Free, plus:</p>
              {[
                "Unlimited AI Applications",
                "Resume Tailored for Every Job",
                "Custom Cover Letters",
                "Stealth Mode",
                "Priority Support",
                "LinkedIn Sync",
                "Interview Coaching"
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-white" />
                  <span className="text-sm font-bold text-white">{feature}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleProCta}
              className="w-full py-3.5 rounded-lg bg-white text-black font-bold hover:bg-gray-200 transition-colors"
            >
              {getProCtaLabel()}
            </button>
          </motion.div>
        </div>

        {/* Trust indicators */}
        <div className="mt-16 text-center">
          <p className="text-sm text-gray-500 mb-4 font-bold uppercase tracking-widest">Trusted by job seekers at</p>
          <div className="flex justify-center flex-wrap gap-8 opacity-40">
            {['Walmart', 'Target', 'Amazon', 'Costco', 'Home Depot'].map((company) => (
              <span key={company} className="text-lg font-bold text-black dark:text-white">{company}</span>
            ))}
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-24 border-t border-gray-200 dark:border-gray-800 pt-16">
          <h2 className="text-3xl font-bold text-center mb-12 tracking-tight text-black dark:text-white">Frequently Asked Questions</h2>
          <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
            {[
              { q: "What happens after my 20 free applications?", a: "Your free applications reset every Monday at midnight UTC. If you need more before the reset, you can upgrade to Pro for unlimited applications." },
              { q: "Can I cancel Pro anytime?", a: "Yes. Cancel anytime in your dashboard with one click. No phone calls, no hassle. You'll keep access until your billing period ends." },
              { q: "What happens after the first month?", a: "After your $10 first month, you'll be charged $29/month. We'll send you a reminder 3 days before the price change." },
              { q: "Is my data safe?", a: "We use bank-level encryption. Your resume is only shared with employers you choose to apply to. We never sell your data." },
              { q: "How does the weekly reset work?", a: "Every Monday at midnight UTC, your free application count resets to 20. Unused applications don't roll over." },
              { q: "Can I get a refund?", a: "If you're not satisfied, contact us within 7 days of upgrading for a full refund. No questions asked." },
            ].map((item, i) => (
              <FAQItem key={i} question={item.q} answer={item.a} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
