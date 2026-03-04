import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CheckCircle, Zap, Crown, CreditCard, ChevronDown, X } from 'lucide-react';
import { t, getLocale } from '../lib/i18n';
import { motion, useReducedMotion, AnimatePresence } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { useAuth } from '../hooks/useAuth';
import { useBilling } from '../hooks/useBilling';
import { telemetry } from '../lib/telemetry';
import { cn } from '../lib/utils';
import { FadeIn } from '../components/animations/FadeIn';
import { PricingSkeleton } from '../components/ui/Skeleton';

// FAQ Item Component for collapsible behavior
const FAQItem = ({ question, answer }: { question: string; answer: string }) => {
  const [isOpen, setIsOpen] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="bg-white p-6 rounded-2xl border border-gray-100 hover:border-orange-100 transition-colors">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full text-left flex items-center justify-between gap-4 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-lg p-2 -m-2"
        aria-expanded={isOpen}
        aria-controls={`faq-answer-${question.replace(/\s+/g, '-')}`}
      >
        <h3 className="font-bold text-lg text-slate-800 leading-snug">
          <span className="text-primary-600 mr-2">Q.</span>{question}
        </h3>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: shouldReduceMotion ? 0 : 0.2 }}
          className="flex-shrink-0"
        >
          <ChevronDown className="w-5 h-5 text-gray-500" aria-hidden="true" />
        </motion.div>
      </button>
      <motion.div
        id={`faq-answer-${question.replace(/\s+/g, '-')}`}
        initial={false}
        animate={{
          height: isOpen ? "auto" : 0,
          opacity: isOpen ? 1 : 0
        }}
        transition={{ duration: shouldReduceMotion ? 0 : 0.3 }}
        className="overflow-hidden"
      >
        <p className="text-gray-600 pl-6 pt-2">{answer}</p>
      </motion.div>
    </div>
  );
};

// B3: Verify plan IDs (FREE, PRO, TEAM) match backend /billing/checkout and Stripe products
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
            className="bg-white dark:bg-slate-900 rounded-3xl p-8 max-w-md w-full shadow-2xl relative overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Decorative gradient */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary-400/20 to-primary-600/20 blur-3xl -mr-16 -mt-16" />
            
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
              aria-label="Close popup"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="relative z-10">
              <div className="w-16 h-16 rounded-2xl bg-primary-100 flex items-center justify-center mb-6">
                <Zap className="w-8 h-8 text-primary-600" />
              </div>
              
              <h3 className="text-2xl font-black text-slate-900 dark:text-slate-100 mb-3">
                Wait! Don't miss out
              </h3>
              
              <p className="text-slate-600 dark:text-slate-400 mb-6 leading-relaxed">
                Join <span className="font-bold text-slate-900">10,000+ job seekers</span> who automated their job search. 
                Get your first interviews in just 48 hours.
              </p>
              
              <div className="space-y-3">
                <Link
                  to="/login"
                  onClick={onClose}
                  className="block w-full h-14 rounded-2xl bg-primary-600 text-white font-bold text-center leading-[56px] hover:bg-primary-700 transition-all shadow-lg shadow-primary-600/25 hover:shadow-primary-600/40 hover:-translate-y-0.5"
                >
                  Start Free Trial
                </Link>
                
                <button
                  onClick={onClose}
                  className="block w-full h-12 text-slate-500 font-medium hover:text-slate-700 transition-colors"
                >
                  Maybe later
                </button>
              </div>
              
              <p className="text-xs text-slate-400 text-center mt-4">
                No credit card required. Cancel anytime.
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function Pricing() {
  const [annual, setAnnual] = useState(false);
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
    telemetry.track("upgrade_clicked", { source: "pricing", period: annual ? "annual" : "monthly" });
    try {
      await upgrade(annual ? "annual" : "monthly");
    } catch (err) {
      console.error('Checkout failed:', err);
    }
  };

  const getProCtaLabel = () => {
    if (authLoading || billingLoading) return t("app.loading", locale);
    if (!isLoggedIn) return t("pricing.startTrial", locale);
    if (isProOrHigher) return t("pricing.currentPlan", locale);
    return t("pricing.startTrial", locale);
  };

  // Show skeleton while loading auth/billing state
  if (authLoading || billingLoading) {
    return <PricingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 selection:bg-primary-500/20 selection:text-primary-700 pb-20">
      <ExitIntentPopup isOpen={showExitIntent} onClose={() => setShowExitIntent(false)} />
      <SEO
        title="Pricing | JobHuntin AI: Free to Start, $19/mo Pro for Unlimited Auto-Apply"
        description="JobHuntin pricing: Free tier to start, Pro at $19/month for unlimited AI job applications, resume tailoring, and stealth mode. One interview pays for a lifetime."
        ogTitle="JobHuntin Pricing: Free to Start"
        ogImage="https://jobhuntin.com/og-image.png"
        canonicalUrl="https://jobhuntin.com/pricing"
        includeDate={true}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "JobHuntin Pro",
            "description": "AI-powered job application automation: unlimited applications, resume tailoring, and interview coaching.",
            "offers": [
              {
                "@type": "Offer",
                "name": "Monthly",
                "url": "https://jobhuntin.com/pricing",
                "priceCurrency": "USD",
                "price": "29",
                "priceValidUntil": "2026-12-31",
                "availability": "https://schema.org/InStock"
              },
              {
                "@type": "Offer",
                "name": "Annual",
                "url": "https://jobhuntin.com/pricing",
                "priceCurrency": "USD",
                "price": "22",
                "priceValidUntil": "2026-12-31",
                "availability": "https://schema.org/InStock"
              }
            ]
          },
          {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
              {
                "@type": "Question",
                "name": "Can I cancel anytime?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "Yes. One click in your dashboard. No awkward phone calls."
                }
              },
              {
                "@type": "Question",
                "name": "Is my data safe?",
                "acceptedAnswer": {
                  "@type": "Answer",
                  "text": "We use bank-level encryption. Your resume is only shared with employers you apply to."
                }
              }
            ]
          }
        ]}
      />

      <main className="max-w-7xl mx-auto px-6 py-28 sm:py-36">
        <div className="text-center mb-24 relative">
          <FadeIn>
            <div className="text-primary-600 font-black text-[10px] uppercase tracking-[0.3em] mb-4">Investment in you</div>
            <h1 className="text-[clamp(3rem,7vw,6.5rem)] font-black text-slate-900 dark:text-slate-100 mb-8 tracking-[-0.05em] leading-[0.95]">
              Get hired, <br />
              <span className="text-primary-600">for the price of lunch.</span>
            </h1>
          </FadeIn>

          <FadeIn delay={100}>
            <p className="text-xl text-gray-500 dark:text-slate-400 max-w-2xl mx-auto mb-12 font-medium">
              Join thousands of professionals automating their career growth with JobHuntin Intelligence.
            </p>
          </FadeIn>

          {/* Toggle */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <span className={`text-xs font-black uppercase tracking-widest ${!annual ? 'text-slate-950 dark:text-slate-100' : 'text-gray-500 dark:text-slate-500'}`}>Monthly</span>
            <button
              onClick={() => setAnnual(!annual)}
              className="w-14 h-8 bg-slate-200 dark:bg-slate-800 rounded-full p-1 relative transition-all hover:scale-105 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-pressed={annual}
              aria-label={annual ? "Switch to monthly billing" : "Switch to annual billing"}
            >
              <motion.div
                className="w-6 h-6 bg-white dark:bg-slate-100 rounded-full shadow-sm"
                animate={{ x: annual ? 24 : 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            </button>
            <span className={`text-xs font-black uppercase tracking-widest flex items-center gap-2 ${annual ? 'text-slate-950 dark:text-slate-100' : 'text-gray-500 dark:text-slate-500'}`}>
              Annual <span className="bg-primary-600 text-white text-[9px] px-2 py-0.5 rounded-full shadow-lg shadow-primary-600/20">Save 25%</span>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-6xl mx-auto items-stretch">
          {/* Starter Tier */}
          <motion.div
            whileHover={{ y: -8 }}
            className="bg-white rounded-[2.5rem] p-10 border border-slate-200 shadow-xl shadow-slate-200/20 flex flex-col h-full"
          >
            <div className="mb-10">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-gray-500 mb-4">Starter</h3>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-black text-slate-950">$0</span>
                <span className="text-sm font-bold text-gray-500">/mo</span>
              </div>
            </div>

            <div className="space-y-5 mb-12 flex-1">
              {[
                "10 Active Applications",
                "Basic Profile Parsing",
                "Personal CRM",
                "Daily Market Insights"
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <CheckCircle className="w-4 h-4 text-primary-500" />
                  <span className="text-sm font-bold text-gray-600">{feature}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleFreeCta}
              className="w-full py-4 rounded-2xl border-2 border-slate-100 text-slate-950 font-bold hover:bg-slate-50 transition-all active:scale-95"
            >
              Start Hunting
            </button>
          </motion.div>

          {/* Pro Tier — Vibrant Indigo */}
          <motion.div
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            whileHover={{ y: -12, scale: 1.02 }}
            className="bg-primary-600 rounded-[2.5rem] p-10 shadow-3xl shadow-primary-600/30 flex flex-col h-full relative overflow-hidden"
          >
            {/* Glossy overlay effect */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 blur-3xl -mr-16 -mt-16" />

            <div className="mb-10 relative z-10">
              <div className="flex justify-between items-center mb-4 text-white">
                <h3 className="text-xs font-black uppercase tracking-[0.2em] opacity-80">Pro Hunter</h3>
                <Zap className="w-4 h-4" />
              </div>
              <div className="flex items-baseline gap-1 text-white">
                <span className="text-6xl font-black">${annual ? '22' : '29'}</span>
                <span className="text-sm font-bold opacity-60">/mo</span>
              </div>
              <p className="text-[10px] text-white/40 uppercase font-black tracking-widest mt-2">{annual ? "Billed annually" : "Billed monthly"}</p>
            </div>

            <div className="space-y-5 mb-12 flex-1 relative z-10">
              {[
                "Unlimited AI Applications",
                "Resume rewritten for every job",
                "Custom Cover Letters",
                "Priority Support",
                "LinkedIn Sync",
                "Stealth Mode"
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <CheckCircle className="w-4 h-4 text-primary-200" />
                  <span className="text-sm font-bold text-white leading-tight">{feature}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleProCta}
              className="w-full py-5 rounded-2xl bg-white text-primary-600 font-bold hover:bg-slate-50 transform transition-all shadow-xl active:scale-95"
            >
              Start Free Trial
            </button>
          </motion.div>

          {/* Agency/Team Tier */}
          <motion.div
            whileHover={{ y: -8 }}
            className="bg-white rounded-[2.5rem] p-10 border border-slate-200 shadow-xl shadow-slate-200/20 flex flex-col h-full"
          >
            <div className="mb-10">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-gray-500 mb-4">Agency</h3>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-black text-slate-950">$199</span>
                <span className="text-sm font-bold text-gray-500">/mo</span>
              </div>
            </div>

            <ul className="space-y-5 mb-12 flex-1 text-sm font-bold text-gray-500">
              <li className="flex items-center gap-3"><Zap className="w-4 h-4 text-primary-500" /> 5 Team Seats</li>
              <li className="flex items-center gap-3"><Zap className="w-4 h-4 text-primary-500" /> Custom Domain Integration</li>
              <li className="flex items-center gap-3"><Zap className="w-4 h-4 text-primary-500" /> Full API Access</li>
              <li className="flex items-center gap-3"><Zap className="w-4 h-4 text-primary-500" /> White-label Reporting</li>
            </ul>

            <button
              onClick={() => window.location.href = 'mailto:sales@jobhuntin.com'}
              className="w-full py-4 rounded-2xl border-2 border-slate-100 text-slate-950 font-bold hover:bg-slate-50 transition-all"
            >
              Talk to Sales
            </button>
          </motion.div>
        </div>

        {/* FAQ Section */}
        <div className="mt-32 border-t border-gray-200 dark:border-slate-700 pt-20">
          <h2 className="text-3xl font-black text-center mb-16 tracking-tight text-slate-900 dark:text-slate-100">{t("pricing.faqTitle", locale)}</h2>
          <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
            {[
              { q: t("pricing.faqCancel", locale), a: t("pricing.faqCancelA", locale) },
              { q: t("pricing.faqWork", locale), a: t("pricing.faqWorkA", locale) },
              { q: t("pricing.faqSafe", locale), a: t("pricing.faqSafeA", locale) },
              { q: t("pricing.faqHired", locale), a: t("pricing.faqHiredA", locale) },
            ].map((item, i) => (
              <FAQItem key={i} question={item.q} answer={item.a} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
