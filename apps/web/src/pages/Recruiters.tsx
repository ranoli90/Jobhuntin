import React, { useState } from 'react';
import { Terminal, User, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { Button } from '../components/ui/Button';

export default function Recruiters() {
  const [view, setView] = useState<'human' | 'terminal'>('human');
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className={`min-h-[calc(100vh-80px)] transition-colors duration-500 ${view === 'terminal' ? 'bg-[#0d1117] text-gray-300' : 'bg-slate-50 text-slate-900'}`}>
      <SEO
        title="For Recruiters | JobHuntin: Hire Pre-Screened AI-Matched Talent"
        description="JobHuntin for recruiters: Access pre-screened candidates with AI-verified skills. Get structured data, salary expectations, and match scores delivered to your ATS."
        ogTitle="For Recruiters | JobHuntin Talent Pipeline"
        ogImage="https://jobhuntin.com/og/recruiters.png"
        canonicalUrl="https://jobhuntin.com/recruiters"
        includeDate={true}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": "JobHuntin Recruiter API",
            "description": "AI-powered candidate screening and structured data delivery for recruiters.",
            "provider": {
              "@type": "Organization",
              "name": "JobHuntin"
            },
            "offers": {
              "@type": "Offer",
              "price": "0",
              "priceCurrency": "USD",
              "description": "API access for qualified recruiters"
            }
          },
          {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": "JobHuntin for Recruiters",
            "description": "AI-powered talent pipeline for recruiters",
            "url": "https://jobhuntin.com/recruiters"
          }
        ]}
      />

      <main className="max-w-7xl mx-auto px-6 py-24 relative">
        {/* View Toggle */}
        <div className="flex justify-center mb-16">
          <div className={`p-1 rounded-full flex gap-1 relative shadow-sm border ${view === 'terminal' ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200'}`}>
            {!shouldReduceMotion && (
              <motion.div
                layoutId="activeTab"
                className={`absolute inset-1 w-1/2 rounded-full shadow-sm ${view === 'terminal' ? 'bg-gray-700' : 'bg-primary-50'}`}
                animate={{ x: view === 'human' ? 0 : '100%' }}
              />
            )}
            <button
              onClick={() => setView('human')}
              className={`px-4 sm:px-6 py-2 rounded-full text-sm font-bold relative z-10 transition-colors flex items-center gap-2 ${view === 'human' ? 'text-primary-700' : 'text-gray-500'} focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2`}
              aria-label="Switch to human view"
              aria-pressed={view === 'human'}
            >
              <User className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline">Human</span>
              <span className="sm:hidden">People</span>
            </button>
            <button
              onClick={() => setView('terminal')}
              className={`px-4 sm:px-6 py-2 rounded-full text-sm font-bold relative z-10 transition-colors flex items-center gap-2 ${view === 'terminal' ? 'text-white' : 'text-slate-400'} focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2`}
              aria-label="Switch to terminal view"
              aria-pressed={view === 'terminal'}
            >
              <Terminal className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline">Terminal</span>
              <span className="sm:hidden">API</span>
            </button>
          </div>
        </div>

        <AnimatePresence mode={shouldReduceMotion ? 'wait' : 'sync'}>
          {view === 'human' ? (
            <motion.div
              key="human"
              initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: 20 }}
              transition={{ duration: shouldReduceMotion ? 0 : 0.3 }}
              className="space-y-20"
            >
              <div className="text-center">
                <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black font-display mb-6 leading-tight text-slate-900 text-balance">
                  Hire talent, <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-blue-400">not keyword stuffers.</span>
                </h1>
                <p className="text-lg sm:text-xl text-slate-500 max-w-2xl mx-auto mb-8 font-medium text-balance">
                  Our AI pre-interviews every candidate before they reach your inbox. You get structured data, not PDF chaos.
                </p>
                <Button variant="secondary" size="lg" className="px-6 sm:px-8 py-3 sm:py-4 h-auto rounded-xl text-base sm:text-lg shadow-lg hover:shadow-primary-500/20">
                  Request API Access
                </Button>
              </div>

              <div className="grid md:grid-cols-2 gap-12 items-center">
                <div className="relative">
                  <div className="absolute -inset-4 bg-gradient-to-r from-primary-500 to-blue-400 rounded-[2rem] opacity-20 blur-xl" />
                  <div className="bg-white p-6 sm:p-8 rounded-3xl shadow-xl relative border border-slate-100">
                    <div className="flex items-center gap-4 mb-6 border-b border-slate-100 pb-4">
                      <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&auto=format&fit=crop&w=64&q=80" alt="Michael Chen - Top Talent Candidate" className="w-12 h-12 rounded-full ring-2 ring-white shadow-sm" loading="lazy" />
                      <div>
                        <h3 className="font-bold text-slate-900">Michael Chen</h3>
                        <p className="text-sm text-slate-500">Senior React Developer</p>
                      </div>
                      <div className="ml-auto bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-bold">
                        98% Match
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="bg-slate-50 p-4 rounded-xl">
                        <p className="text-xs font-bold text-slate-400 uppercase mb-1">Q: Experience with High Scale?</p>
                        <p className="text-sm text-slate-800 font-medium">"Yes, at CloudScale I optimized a dashboard handling 50k WS connections..."</p>
                      </div>
                      <div className="bg-slate-50 p-4 rounded-xl">
                        <p className="text-xs font-bold text-slate-400 uppercase mb-1">Q: Salary Expectations?</p>
                        <p className="text-sm text-slate-800 font-medium">$160k - $180k (Remote)</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-2xl sm:text-3xl font-bold font-display mb-6 text-slate-900">Structured Candidate Cards</h3>
                  <p className="text-slate-500 text-base sm:text-lg leading-relaxed mb-6 font-medium">
                    Stop parsing PDFs. We deliver JSON-ready profiles with verified answers to your screening questions.
                  </p>
                  <ul className="space-y-4">
                    <li className="flex items-center gap-3 font-medium text-slate-700"><CheckCircle className="w-5 h-5 text-emerald-500" aria-hidden="true" /> Auto-screened for skills</li>
                    <li className="flex items-center gap-3 font-medium text-slate-700"><CheckCircle className="w-5 h-5 text-emerald-500" aria-hidden="true" /> Salary expectations verified</li>
                    <li className="flex items-center gap-3 font-medium text-slate-700"><CheckCircle className="w-5 h-5 text-emerald-500" aria-hidden="true" /> "Human-verified" badge</li>
                  </ul>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="terminal"
              initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: -20 }}
              transition={{ duration: shouldReduceMotion ? 0 : 0.3 }}
              className="font-mono"
            >
              <div className="text-center mb-16">
                <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-7xl font-bold mb-6 text-emerald-400 break-all sm:break-normal font-mono">
                  $ curl api.jobhuntin.io/v1/candidates
                </h2>
                <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-8 text-balance">
                  Direct pipe to the top 1% of the market. Webhooks, JSON streams, and zero UI friction.
                </p>
                <Button variant="outline" size="lg" className="border-emerald-500 text-emerald-500 bg-transparent hover:bg-emerald-500/10 px-6 sm:px-8 py-3 sm:py-4 h-auto rounded-xl font-bold transition-colors">
                  Generate API Key
                </Button>
              </div>

              <div className="max-w-4xl mx-auto bg-[#0d1117] border border-gray-800 rounded-lg overflow-hidden shadow-2xl">
                <div className="bg-[#161b22] px-4 py-2 border-b border-gray-800 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="ml-2 text-xs text-gray-500">bash — 80x24</span>
                </div>
                <div className="p-4 sm:p-6 text-xs sm:text-sm text-gray-300 overflow-x-auto font-mono leading-relaxed">
                  <div className="min-w-[300px] sm:min-w-[500px]">
                    <p className="mb-2"><span className="text-emerald-400">➜</span> <span className="text-blue-400">~</span> curl -X POST https://api.jobhuntin.io/webhook \</p>
                    <p className="mb-2 pl-4">-H "Authorization: Bearer sk_live_..." \</p>
                    <p className="mb-4 pl-4">-d {'{\"criteria\": [\"react\", \"node\", \"5+ years\"]}'}</p>

                    <p className="mb-2 text-gray-500"># Response stream initiating...</p>
                    <p className="mb-2 text-emerald-400">{'{'}</p>
                    <p className="mb-1 pl-4">"id": "cand_892301",</p>
                    <p className="mb-1 pl-4">"match_score": 0.98,</p>
                    <p className="mb-1 pl-4">"github_activity": "high",</p>
                    <p className="mb-1 pl-4">"screening": {'{'}</p>
                    <p className="mb-1 pl-8">"q1_scale": "Architected k8s cluster for...",</p>
                    <p className="mb-1 pl-8">"q2_salary": "160000"</p>
                    <p className="mb-1 pl-4">{'}'}</p>
                    <p className="text-emerald-400">{'}'}</p>
                    {!shouldReduceMotion && (
                      <motion.div
                        animate={{ opacity: [0, 1, 0] }}
                        transition={{ repeat: Infinity, duration: 0.8 }}
                        className="inline-block w-2 h-4 bg-emerald-400 ml-1 align-middle"
                      />
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
