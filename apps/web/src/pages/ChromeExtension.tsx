import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft, Download, Linkedin, Briefcase, Plus, Check } from 'lucide-react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { Button } from '../components/ui/Button';
import { Logo } from '../components/brand/Logo';

export default function ChromeExtension() {
  const [activeStep, setActiveStep] = useState(0);
  const shouldReduceMotion = useReducedMotion();

  // Simulation Loop - disabled with reduced motion
  useEffect(() => {
    if (shouldReduceMotion) return;
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 4);
    }, 3000);
    return () => clearInterval(timer);
  }, [shouldReduceMotion]);

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO
        title="Chrome Extension | JobHuntin — One-Click Auto-Apply from LinkedIn & Indeed"
        description="JobHuntin Chrome extension: Auto-apply to jobs with one click from LinkedIn, Indeed, and Glassdoor. AI tailors your resume and writes cover letters instantly."
        ogTitle="Chrome Extension | JobHuntin Auto-Apply"
        ogImage="https://jobhuntin.com/og/chrome-extension.png"
        canonicalUrl="https://jobhuntin.com/chrome-extension"
        includeDate={true}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "JobHuntin Chrome Extension",
            "operatingSystem": "ChromeOS, Windows, macOS, Linux",
            "applicationCategory": "BrowserApplication",
            "offers": {
              "@type": "Offer",
              "price": "0",
              "priceCurrency": "USD"
            },
            "aggregateRating": {
              "@type": "AggregateRating",
              "ratingValue": "4.9",
              "ratingCount": "1247"
            }
          }
        ]}
      />
      <main className="max-w-7xl mx-auto px-6 py-24">
        <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-20">
          <div className="flex-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-block bg-primary-100 text-primary-700 px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-6"
            >
              v2.0 Now Available
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black font-display text-slate-900 mb-6 sm:mb-8 leading-tight tracking-tight text-balance"
            >
              The "Add to Cart" <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400">for your career.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-lg sm:text-xl text-slate-500 mb-8 sm:mb-10 leading-relaxed max-w-lg font-medium text-balance"
            >
              Browse LinkedIn, Indeed, or Glassdoor. See a job you like?
              Click one button. Our AI handles the resume tailoring, cover letter, and submission.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4 sm:gap-4"
            >
              <Button variant="primary" size="lg" className="px-6 sm:px-8 py-3 sm:py-4 h-auto rounded-xl font-bold bg-primary-600 hover:bg-primary-500 transition-colors flex items-center justify-center gap-3 shadow-xl shadow-primary-500/20 transform hover:-translate-y-1 w-full sm:w-auto">
                <Download className="w-5 h-5" />
                Add to Chrome
                <span className="text-white/50 font-normal text-sm ml-2 font-mono">v2.4</span>
              </Button>
              <Button variant="outline" size="lg" className="bg-white border-2 border-slate-200 text-slate-700 px-6 sm:px-8 py-3 sm:py-4 h-auto rounded-xl font-bold hover:border-primary-500 hover:text-primary-500 transition-colors w-full sm:w-auto">
                Watch Demo
              </Button>
            </motion.div>
          </div>

          {/* Fake Browser Interaction */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="flex-1 w-full max-w-2xl relative"
          >
            {/* Browser Window - Responsive aspect ratio */}
            <div className="bg-white rounded-[2rem] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.15)] border border-slate-200 overflow-hidden relative z-10 aspect-[4/3] sm:aspect-none sm:h-[450px]">
              {/* Browser Bar */}
              <div className="bg-slate-50 px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 flex items-center gap-2 sm:gap-4">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-slate-300" />
                  <div className="w-3 h-3 rounded-full bg-slate-300" />
                  <div className="w-3 h-3 rounded-full bg-slate-300" />
                </div>
                <div className="bg-white rounded-lg flex-1 px-2 sm:px-4 py-1.5 text-[9px] sm:text-[10px] text-slate-400 font-mono flex items-center border border-slate-200 truncate">
                  <span className="text-emerald-500 mr-2">🔒</span> 
                  <span className="hidden sm:inline">linkedin.com/jobs/view/382910...</span>
                  <span className="sm:hidden">linkedin.com...</span>
                </div>
              </div>

              {/* Web Content */}
              <div className="p-3 sm:p-8 h-full bg-white relative">
                {/* Job Header */}
                <div className="flex justify-between items-start mb-4 sm:mb-8">
                  <div className="flex gap-2 sm:gap-4">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-slate-900 rounded-xl flex items-center justify-center text-white font-black text-lg sm:text-xl">L</div>
                    <div>
                      <div className="h-3 w-32 sm:w-48 bg-slate-900 rounded-full mb-2 sm:mb-3"></div>
                      <div className="h-2.5 sm:h-3 w-20 sm:w-24 bg-slate-200 rounded-full"></div>
                    </div>
                  </div>
                  {/* The Magic Button */}
                  <motion.button
                    animate={{
                      scale: shouldReduceMotion ? 1 : (activeStep === 1 ? [1, 0.95, 1] : 1),
                      backgroundColor: activeStep >= 2 ? "#10B981" : "#2563eb"
                    }}
                    className="bg-primary-600 text-white px-3 sm:px-5 py-2 sm:py-2.5 rounded-xl text-[10px] sm:text-xs font-black uppercase tracking-wider flex items-center gap-1.5 sm:gap-2 shadow-xl shadow-primary-500/20 relative z-50 transition-colors text-xs sm:text-sm"
                  >
                    {activeStep >= 2 ? (
                      <><Check className="w-3 sm:w-4 h-3 sm:h-4 stroke-[3]" /> <span className="hidden sm:inline">Added to Queue</span><span className="sm:hidden">Added</span></>
                    ) : (
                      <><Plus className="w-3 sm:w-4 h-3 sm:h-4 stroke-[3]" /> <span className="hidden sm:inline">Auto-Apply</span><span className="sm:hidden">Apply</span></>
                    )}
                  </motion.button>
                </div>

                {/* Job Body */}
                <div className="space-y-2 sm:space-y-4 opacity-10">
                  <div className="h-2.5 sm:h-3 w-full bg-slate-400 rounded-full"></div>
                  <div className="h-2.5 sm:h-3 w-full bg-slate-400 rounded-full"></div>
                  <div className="h-2.5 sm:h-3 w-3/4 bg-slate-400 rounded-full"></div>
                  <div className="h-2.5 sm:h-3 w-full bg-slate-400 rounded-full"></div>
                  <div className="h-2.5 sm:h-3 w-5/6 bg-slate-400 rounded-full"></div>
                </div>

                {/* Extension Overlay - Hidden on mobile */}
                <AnimatePresence>
                  {activeStep >= 1 && !shouldReduceMotion && (
                    <motion.div
                      initial={{ x: 300, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      exit={{ x: 300, opacity: 0 }}
                      className="hidden sm:block absolute top-6 right-6 w-72 bg-slate-900 text-white rounded-2xl shadow-2xl p-5 z-40 border border-white/10"
                    >
                      <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-3">
                        <div className="bg-primary-500 p-1.5 rounded-lg">
                          <Bot className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-bold text-xs uppercase tracking-widest text-primary-400">Agent Intelligence</span>
                      </div>

                      {activeStep === 1 && (
                        <div className="flex items-center gap-3 text-xs text-slate-400 font-medium">
                          <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                          Parsing opportunities...
                        </div>
                      )}

                      {activeStep === 2 && (
                        <div className="space-y-4">
                          <div className="flex items-center gap-2 text-xs text-emerald-400 font-black uppercase tracking-wider">
                            <Check className="w-4 h-4 stroke-[3]" /> Match Score: 94%
                          </div>
                          <div className="bg-white/5 p-3 rounded-xl text-[10px] text-slate-400 font-mono leading-relaxed">
                            <span className="text-primary-400">&gt;</span> Tailoring resume for role...<br />
                            <span className="text-primary-400">&gt;</span> Drafting cover letter...<br />
                            <span className="text-primary-400">&gt;</span> Task queued in cloud.
                          </div>
                        </div>
                      )}

                      {activeStep === 3 && (
                        <div className="text-center py-4">
                          <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-3 text-emerald-400 border border-emerald-500/50">
                            <Check className="w-6 h-6 stroke-[3]" />
                          </div>
                          <h4 className="font-black text-white text-xs uppercase tracking-widest">Autonomous Sync</h4>
                          <p className="text-[10px] text-slate-400 mt-1">Application pending submission</p>
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Mouse Cursor - Hidden on mobile and with reduced motion */}
                {!shouldReduceMotion && (
                  <motion.div
                    animate={{
                      x: activeStep === 0 ? 280 : 300,
                      y: activeStep === 0 ? 40 : 50,
                      scale: activeStep === 1 ? 0.9 : 1
                    }}
                    transition={{ duration: 1 }}
                    className="hidden sm:block absolute top-0 left-0 w-6 h-6 pointer-events-none z-50"
                    style={{ filter: "drop-shadow(0px 2px 8px rgba(0,0,0,0.3))" }}
                  >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z" fill="black" stroke="white" strokeWidth="2" />
                    </svg>
                  </motion.div>
                )}
              </div>
            </div>

            {/* Background Blob */}
            <div className="absolute -inset-20 bg-gradient-to-tr from-primary-500/20 to-blue-500/20 rounded-full blur-[100px] -z-10 animate-pulse" />
          </motion.div>
        </div>

        {/* Premium Supported Platforms Section */}
        <div className="mt-32 relative">
          <div className="absolute inset-0 bg-slate-900/[0.02] -skew-y-3 rounded-[4rem] -z-10" />
          <div className="py-20 px-6">
            <div className="text-center mb-16">
              <h3 className="text-2xl font-black text-slate-900 mb-4 tracking-tight">Works where you hunt.</h3>
              <p className="text-slate-500 font-medium">Native integration with the platforms you already use.</p>
            </div>

            <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12 lg:gap-20">
              <div className="flex items-center gap-3 grayscale hover:grayscale-0 transition-all duration-700 cursor-pointer">
                <Linkedin className="w-8 h-8 text-[#0077b5]" />
                <span className="text-lg sm:text-xl font-bold tracking-tight">LinkedIn</span>
              </div>
              <div className="flex items-center gap-3 grayscale hover:grayscale-0 transition-all duration-700 cursor-pointer">
                <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-black italic">f</div>
                <span className="text-lg sm:text-xl font-bold tracking-tight">FlexJobs</span>
              </div>
              <div className="flex items-center gap-3 grayscale hover:grayscale-0 transition-all duration-700 cursor-pointer">
                <div className="w-8 h-8 bg-black rounded flex items-center justify-center text-white font-black">W</div>
                <span className="text-lg sm:text-xl font-bold tracking-tight">Wellfound</span>
              </div>
              <div className="flex items-center gap-3 grayscale hover:grayscale-0 transition-all duration-700 cursor-pointer">
                <div className="w-8 h-8 bg-[#212121] rounded-full flex items-center justify-center text-white font-black text-[10px]">IND</div>
                <span className="text-lg sm:text-xl font-bold tracking-tight">Indeed</span>
              </div>
            </div>

            {/* Performance Stats Overlay */}
            <div className="grid md:grid-cols-3 gap-8 mt-24">
              <div className="p-8 rounded-[2rem] bg-white border border-slate-100 shadow-xl shadow-slate-200/20 text-center group hover:-translate-y-2 transition-transform">
                <p className="text-primary-600 font-black text-4xl mb-2">0.4s</p>
                <p className="text-slate-900 font-bold uppercase text-[10px] tracking-widest">Parsing Latency</p>
                <div className="h-1 w-8 bg-primary-100 mx-auto mt-4 group-hover:w-16 transition-all" />
              </div>
              <div className="p-8 rounded-[2rem] bg-white border border-slate-100 shadow-xl shadow-slate-200/20 text-center group hover:-translate-y-2 transition-transform">
                <p className="text-blue-600 font-black text-4xl mb-2">99.8%</p>
                <p className="text-slate-900 font-bold uppercase text-[10px] tracking-widest">Field Accuracy</p>
                <div className="h-1 w-8 bg-blue-100 mx-auto mt-4 group-hover:w-16 transition-all" />
              </div>
              <div className="p-8 rounded-[2rem] bg-white border border-slate-100 shadow-xl shadow-slate-200/20 text-center group hover:-translate-y-2 transition-transform">
                <p className="text-emerald-600 font-black text-4xl mb-2">24/7</p>
                <p className="text-slate-900 font-bold uppercase text-[10px] tracking-widest">Active Scouting</p>
                <div className="h-1 w-8 bg-emerald-100 mx-auto mt-4 group-hover:w-16 transition-all" />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
