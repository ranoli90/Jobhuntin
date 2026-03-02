import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CheckCircle, Zap, Crown, CreditCard, ChevronDown } from 'lucide-react';
import { t, getLocale } from '../lib/i18n';
import { motion, useReducedMotion } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { useAuth } from '../hooks/useAuth';
import { useBilling } from '../hooks/useBilling';
import { telemetry } from '../lib/telemetry';

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
          <ChevronDown className="w-5 h-5 text-gray-400" aria-hidden="true" />
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
export default function Pricing() {
  const [annual, setAnnual] = useState(false);
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const { plan, loading: billingLoading, upgrade } = useBilling();
  const shouldReduceMotion = useReducedMotion();
  const locale = getLocale();

  const isLoggedIn = !!user;
  const isProOrHigher = plan === 'PRO' || plan === 'TEAM';

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

    return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 selection:bg-primary-500/20 selection:text-primary-700 pb-20">
      <SEO
        title="Pricing | JobHuntin AI: Free to Start, $19/mo Pro for Unlimited Auto-Apply"
        description="JobHuntin pricing: Free tier to start, Pro at $19/month for unlimited AI job applications, resume tailoring, and stealth mode. One interview pays for a lifetime."
        ogTitle="JobHuntin Pricing: Free to Start"
        ogImage="https://jobhuntin.com/og/pricing.png"
        canonicalUrl="https://jobhuntin.com/pricing"
        includeDate={true}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "JobHuntin Pro",
            "description": "AI-powered job application automation: unlimited applications, resume tailoring, and interview coaching.",
            "offers": {
              "@type": "Offer",
              "url": "https://jobhuntin.com/pricing",
              "priceCurrency": "USD",
              "price": "29",
              "priceValidUntil": "2026-12-31",
              "availability": "https://schema.org/InStock"
            }
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

      <main className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-block"
          >
            <h1 className="text-5xl md:text-7xl font-black text-slate-900 mb-6 tracking-tight">
              Pricing that <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-blue-400">pays for itself.</span>
            </h1>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-xl text-gray-600 dark:text-slate-400 max-w-2xl mx-auto mb-10"
          >
            {t("pricing.subtitle", locale)}
          </motion.p>

          {/* Toggle */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 mb-12">
            <span className={`text-sm font-bold ${!annual ? 'text-gray-900 dark:text-slate-100' : 'text-gray-400 dark:text-slate-500'}`}>{t("pricing.monthly", locale)}</span>
            <button
              onClick={() => setAnnual(!annual)}
              className="w-16 h-8 bg-gray-200 rounded-full p-1 relative transition-colors duration-300 hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label={`Switch to ${annual ? 'monthly' : 'annual'} billing`}
              aria-live="polite"
            >
              <motion.div
                className="w-6 h-6 bg-white rounded-full shadow-md"
                animate={{ x: shouldReduceMotion ? (annual ? 32 : 0) : undefined, translateX: shouldReduceMotion ? 0 : (annual ? 32 : 0) }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            </button>
            <span className={`text-sm font-bold ${annual ? 'text-slate-900 dark:text-slate-100' : 'text-slate-400 dark:text-slate-500'}`}>
              {t("pricing.annual", locale)} <span className="text-white text-xs ml-1 bg-primary-600 px-2 py-0.5 rounded-full shadow-sm" aria-label={t("pricing.save20", locale)}>-20%</span>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto items-stretch">
          {/* Free Tier - Refactored to Standard Card */}
          <motion.div
            whileHover={{ y: shouldReduceMotion ? 0 : -10 }}
            className="bg-white rounded-3xl p-8 border border-gray-100 shadow-xl relative overflow-hidden group max-w-md mx-auto w-full lg:max-w-none min-h-[500px] lg:min-h-0"
          >
            <div className="h-full flex flex-col">
              <div>
                <h3 className="text-2xl font-bold mb-2 text-slate-900 dark:text-slate-100">{t("pricing.starter", locale)}</h3>
                <div className="text-4xl font-bold mb-6 text-slate-900 dark:text-slate-100">$0<span className="text-lg text-slate-500 dark:text-slate-400 font-normal">{t("pricing.perMonth", locale)}</span></div>
              </div>

              <div className="space-y-4 mb-8">
                {[
                  "5 AI Applications",
                  "Basic Resume Parsing",
                  "Job Tracker",
                  "Email Support"
                ].map((feature, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="bg-slate-100 p-1 rounded-full">
                      <CheckCircle className="w-4 h-4 text-slate-400" aria-hidden="true" />
                    </div>
                    <span className="text-slate-600 font-medium">{feature}</span>
                  </div>
                ))}
              </div>

              <div className="mt-auto">
                <button
                  onClick={handleFreeCta}
                  className="block w-full py-3 border-2 border-slate-200 text-center font-bold rounded-xl hover:border-slate-900 hover:text-slate-900 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2"
                  aria-label={isLoggedIn ? t("pricing.goToDashboard", locale) : t("pricing.startFree", locale)}
                >
                  {isLoggedIn ? t("pricing.goToDashboard", locale) : t("pricing.startFree", locale)}
                </button>
              </div>
            </div>
          </motion.div>

          {/* Pro Tier - Floating Holographic */}
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: shouldReduceMotion ? 1 : 1.05 }}
            className="relative z-10 max-w-md mx-auto w-full lg:max-w-none"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-primary-500 to-blue-400 rounded-3xl blur-xl opacity-30 animate-pulse"></div>
            <div className="bg-[#1a1a1a] text-white rounded-3xl p-8 border border-gray-800 shadow-2xl relative overflow-hidden h-full">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-3xl -mr-10 -mt-10"></div>

              <div className="flex justify-between items-start mb-4">
                <h3 className="text-2xl font-bold">{t("pricing.proHunter", locale)}</h3>
                <Crown className="text-primary-500 w-6 h-6" aria-hidden="true" />
              </div>

              <div className="text-5xl font-bold mb-2">
                ${annual ? '24' : '29'}
                <span className="text-lg text-gray-400 font-normal">/mo</span>
              </div>
              <p className="text-gray-400 text-sm mb-8">{annual ? t("pricing.billedAnnually", locale) : t("pricing.billedMonthly", locale)}</p>

              <div className="mb-8">
                <button
                  onClick={handleProCta}
                  disabled={isProOrHigher && isLoggedIn}
                  className={`block w-full py-4 rounded-xl text-center font-bold text-lg shadow-lg transition-all transform focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-[#1a1a1a] ${isProOrHigher && isLoggedIn
                    ? 'bg-gray-600 cursor-default shadow-none hover:translate-y-0'
                    : 'bg-gradient-to-r from-primary-600 to-primary-500 shadow-primary-500/30 hover:shadow-primary-500/50 hover:-translate-y-1'
                    }`}
                  aria-label={getProCtaLabel()}
                >
                  {getProCtaLabel()}
                </button>
              </div>

              <div className="space-y-4">
                {[
                  "Unlimited AI Applications",
                  "Custom Cover Letters",
                  "Priority Queue (Skip the Line)",
                  "LinkedIn Optimization",
                  "Interview Coaching Bot"
                ].map((feature, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="bg-white/10 p-1 rounded-full">
                      <CheckCircle className="w-4 h-4 text-primary-500" aria-hidden="true" />
                    </div>
                    <span className="text-gray-200 font-medium">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Agency - Corporate Card */}
          <motion.div
            whileHover={{ y: shouldReduceMotion ? 0 : -10 }}
            className="bg-white rounded-3xl p-8 border border-gray-100 shadow-xl relative overflow-hidden group max-w-md mx-auto w-full lg:max-w-none min-h-[500px] lg:min-h-0"
          >
            <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-primary-500 to-blue-400"></div>
            <div className="h-full flex flex-col">
              <div>
                <h3 className="text-2xl font-bold mb-2 text-slate-900 dark:text-slate-100">{t("pricing.agency", locale)}</h3>
                <div className="text-4xl font-bold mb-6 text-slate-900 dark:text-slate-100">$199<span className="text-lg text-slate-500 dark:text-slate-400 font-normal">{t("pricing.perMonth", locale)}</span></div>
              </div>

              <div className="bg-gray-50 rounded-xl p-4 mb-8 border border-gray-100">
                <div className="flex items-center gap-3 mb-2">
                  <CreditCard className="w-5 h-5 text-gray-400" aria-hidden="true" />
                  <span className="font-mono text-sm text-gray-500">**** 4242</span>
                </div>
                <p className="text-xs text-gray-400">Corporate billing available</p>
              </div>

              <div className="mb-8">
                <a
                  href="mailto:sales@jobhuntin.com"
                  className="block w-full py-3 border-2 border-slate-200 text-center font-bold rounded-xl hover:border-primary-500 hover:text-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                  aria-label={t("pricing.contactSales", locale)}
                >
                  {t("pricing.contactSales", locale)}
                </a>
              </div>

              <div className="mt-auto">
                <ul className="space-y-4 opacity-80">
                  <li className="flex items-center gap-3"><Zap className="w-5 h-5 text-primary-500" aria-hidden="true" /> 3 Team Seats</li>
                  <li className="flex items-center gap-3"><Zap className="w-5 h-5 text-primary-500" aria-hidden="true" /> White-label Reports</li>
                  <li className="flex items-center gap-3"><Zap className="w-5 h-5 text-primary-500" aria-hidden="true" /> API Access</li>
                </ul>
              </div>
            </div>
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
