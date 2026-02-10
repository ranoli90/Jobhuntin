import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bot, ArrowLeft, CheckCircle, Zap, Crown, Receipt, CreditCard } from 'lucide-react';
import { motion } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { useAuth } from '../hooks/useAuth';
import { useBilling } from '../hooks/useBilling';

export default function Pricing() {
  const [annual, setAnnual] = useState(false);
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const { plan, loading: billingLoading, upgrade } = useBilling();

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
    try {
      await upgrade();
    } catch (err) {
      console.error('Checkout failed:', err);
    }
  };

  const getProCtaLabel = () => {
    if (authLoading || billingLoading) return 'Loading...';
    if (!isLoggedIn) return 'Start Free 7-Day Trial';
    if (isProOrHigher) return 'Current Plan';
    return 'Start Free 7-Day Trial';
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700 pb-20">
      <SEO
        title="Pricing | JobHuntin AI - Investment that Pays for Itself"
        description="Choose the plan that fits your job search. From free starter kits to pro hunter automation. 7-day free trial available."
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
            className="text-xl text-gray-600 max-w-2xl mx-auto mb-10"
          >
            One interview lands a salary that covers this for a lifetime.
          </motion.p>

          {/* Toggle */}
          <div className="flex items-center justify-center gap-4 mb-12">
            <span className={`text-sm font-bold ${!annual ? 'text-gray-900' : 'text-gray-400'}`}>Monthly</span>
            <button
              onClick={() => setAnnual(!annual)}
              className="w-16 h-8 bg-gray-200 rounded-full p-1 relative transition-colors duration-300 hover:bg-gray-300"
            >
              <motion.div
                className="w-6 h-6 bg-white rounded-full shadow-md"
                animate={{ x: annual ? 32 : 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            </button>
            <span className={`text-sm font-bold ${annual ? 'text-slate-900' : 'text-slate-400'}`}>
              Annual <span className="text-primary-600 text-xs ml-1 bg-primary-100 px-2 py-0.5 rounded-full">-20%</span>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto items-center">
          {/* Free Tier - Receipt Style */}
          <motion.div
            whileHover={{ y: -10 }}
            className="bg-white p-1 rounded-sm shadow-sm rotate-1 relative group max-w-md mx-auto w-full lg:max-w-none"
          >
            <div className="bg-white border-x-2 border-t-2 border-b-[6px] border-gray-200 p-8 relative" style={{ backgroundImage: 'radial-gradient(#e5e7eb 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
              {/* Jagged Bottom */}
              <div className="absolute -bottom-3 left-0 right-0 h-3 bg-white" style={{ clipPath: 'polygon(0% 0%, 5% 100%, 10% 0%, 15% 100%, 20% 0%, 25% 100%, 30% 0%, 35% 100%, 40% 0%, 45% 100%, 50% 0%, 55% 100%, 60% 0%, 65% 100%, 70% 0%, 75% 100%, 80% 0%, 85% 100%, 90% 0%, 95% 100%, 100% 0%)' }}></div>

              <h3 className="font-mono text-xl font-bold mb-4 uppercase tracking-widest text-gray-500">Starter</h3>
              <div className="font-mono text-4xl font-bold mb-6">$0<span className="text-sm text-gray-400">/mo</span></div>

              <div className="space-y-3 font-mono text-sm border-t border-b border-dashed border-gray-300 py-6 mb-6">
                <div className="flex justify-between"><span>ITEM: 5 APPS</span> <span>$0.00</span></div>
                <div className="flex justify-between"><span>ITEM: RESUME PARSE</span> <span>$0.00</span></div>
                <div className="flex justify-between"><span>TAX: EFFORT</span> <span>$0.00</span></div>
                <div className="flex justify-between font-bold pt-2 border-t border-gray-200 mt-2"><span>TOTAL</span> <span>$0.00</span></div>
              </div>

              <button onClick={handleFreeCta} className="block w-full py-3 border-2 border-black text-center font-bold font-mono hover:bg-black hover:text-white transition-all uppercase">
                {isLoggedIn ? 'Go to Dashboard' : 'Print Ticket'}
              </button>
            </div>
          </motion.div>

          {/* Pro Tier - Floating Holographic */}
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: 1.05 }}
            className="relative z-10"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-primary-500 to-blue-400 rounded-3xl blur-xl opacity-30 animate-pulse"></div>
            <div className="bg-[#1a1a1a] text-white rounded-3xl p-8 border border-gray-800 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-3xl -mr-10 -mt-10"></div>

              <div className="flex justify-between items-start mb-4">
                <h3 className="text-2xl font-bold">Pro Hunter</h3>
                <Crown className="text-primary-500 w-6 h-6" />
              </div>

              <div className="text-5xl font-bold mb-2">
                ${annual ? '24' : '29'}
                <span className="text-lg text-gray-400 font-normal">/mo</span>
              </div>
              <p className="text-gray-400 text-sm mb-8">Billed {annual ? 'annually' : 'monthly'}</p>

              <button
                onClick={handleProCta}
                disabled={isProOrHigher && isLoggedIn}
                className={`block w-full py-4 rounded-xl text-center font-bold text-lg shadow-lg transition-all transform hover:-translate-y-1 ${isProOrHigher && isLoggedIn
                    ? 'bg-gray-600 cursor-default shadow-none hover:translate-y-0'
                    : 'bg-gradient-to-r from-primary-600 to-primary-500 shadow-primary-500/30 hover:shadow-primary-500/50'
                  }`}
              >
                {getProCtaLabel()}
              </button>

              <div className="mt-8 space-y-4">
                {[
                  "Unlimited AI Applications",
                  "Custom Cover Letters",
                  "Priority Queue (Skip the Line)",
                  "LinkedIn Optimization",
                  "Interview Coaching Bot"
                ].map((feature, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="bg-white/10 p-1 rounded-full">
                      <CheckCircle className="w-4 h-4 text-primary-500" />
                    </div>
                    <span className="text-gray-200 font-medium">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Agency - Corporate Card */}
          <motion.div
            whileHover={{ y: -10 }}
            className="bg-white rounded-3xl p-8 border border-gray-100 shadow-xl relative overflow-hidden group max-w-md mx-auto w-full lg:max-w-none"
          >
            <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-primary-500 to-blue-400"></div>
            <h3 className="text-2xl font-bold mb-2 text-slate-900">Agency</h3>
            <div className="text-4xl font-bold mb-6 text-slate-900">$199<span className="text-lg text-slate-500 font-normal">/mo</span></div>

            <div className="bg-gray-50 rounded-xl p-4 mb-8 border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <CreditCard className="w-5 h-5 text-gray-400" />
                <span className="font-mono text-sm text-gray-500">**** 4242</span>
              </div>
              <p className="text-xs text-gray-400">Corporate billing available</p>
            </div>

            <a href="mailto:sales@jobhuntin.com" className="block w-full py-3 border-2 border-slate-200 text-center font-bold rounded-xl hover:border-primary-500 hover:text-primary-600 transition-colors">
              Contact Sales
            </a>

            <ul className="mt-8 space-y-4 opacity-80">
              <li className="flex items-center gap-3"><Zap className="w-5 h-5 text-primary-500" /> 3 Team Seats</li>
              <li className="flex items-center gap-3"><Zap className="w-5 h-5 text-primary-500" /> White-label Reports</li>
              <li className="flex items-center gap-3"><Zap className="w-5 h-5 text-primary-500" /> API Access</li>
            </ul>
          </motion.div>
        </div>

        {/* FAQ Section */}
        <div className="mt-32 border-t border-gray-200 pt-20">
          <h2 className="text-3xl font-black text-center mb-16 tracking-tight">Questions? We've got answers.</h2>
          <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
            {[
              { q: "Can I cancel anytime?", a: "Yes. One click in your dashboard. No awkward phone calls." },
              { q: "Does this actually work?", a: "We've sent over 1M applications. Our users interview at Google, Amazon, and startups daily." },
              { q: "Is my data safe?", a: "We use bank-level encryption. Your resume is only shared with employers you apply to." },
              { q: "What if I get hired?", a: "Then we did our job! Cancel your sub and pop the champagne. 🍾" }
            ].map((item, i) => (
              <div key={i} className="bg-white p-6 rounded-2xl border border-gray-100 hover:border-orange-100 transition-colors">
                <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                  <span className="text-primary-600">Q.</span> {item.q}
                </h3>
                <p className="text-gray-600 pl-6">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

