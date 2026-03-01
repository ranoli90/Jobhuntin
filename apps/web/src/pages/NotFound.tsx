import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, TrendingUp, Briefcase, Sparkles } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { Button } from '../components/ui/Button';
import { t, getLocale } from '../lib/i18n';

export default function NotFound() {
  const trendingSearches = [
    { label: "Software Engineer in NYC", path: "/jobs/software-engineer/new-york" },
    { label: "Product Manager in SF", path: "/jobs/product-manager/san-francisco" },
    { label: "Data Scientist in Austin", path: "/jobs/data-scientist/austin" },
    { label: "Marketing Manager in London", path: "/jobs/marketing-manager/london" },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO 
        title="404 — This Page Doesn't Exist, But Your Dream Job Does | JobHuntin"
        description="Wrong turn? While you're here, JobHuntin's AI agent is applying to jobs for thousands of people. Start free and never miss a role again."
      />
      
      <main className="flex flex-col items-center justify-center min-h-screen px-6 text-center relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
           <div className="absolute top-[20%] left-[20%] w-64 h-64 bg-primary-500/10 rounded-full blur-3xl animate-pulse" />
           <div className="absolute bottom-[20%] right-[20%] w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="relative z-10 max-w-2xl"
        >
          {/* Live counter badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="inline-flex items-center gap-2 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-sm mb-6 border border-emerald-100 dark:border-emerald-900/50"
          >
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" aria-hidden />
            <span className="text-xs font-bold text-slate-600 dark:text-slate-400">
              {t("404.findNextRole", getLocale())}
            </span>
          </motion.div>
          
          <h1 className="text-7xl sm:text-8xl font-black font-display text-slate-900 mb-4 tracking-tighter">
            404
          </h1>
          <h2 className="text-2xl sm:text-3xl font-bold mb-4 text-slate-800 dark:text-slate-200">
            {t("404.heading", getLocale())}
          </h2>
          <p className="text-lg text-slate-500 mb-8 leading-relaxed max-w-lg mx-auto">
            {t("404.description", getLocale())}
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-12">
            <Link to="/login" aria-label={t("404.startFree", getLocale())}>
              <Button size="lg" className="rounded-xl px-8 shadow-xl shadow-primary-500/20 font-bold">
                <Sparkles className="w-4 h-4 mr-2" aria-hidden />
                {t("404.startFree", getLocale())}
              </Button>
            </Link>
            <Link to="/" aria-label={t("404.backHome", getLocale())}>
              <Button variant="outline" size="lg" className="rounded-xl px-8 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 font-bold">
                {t("404.backHome", getLocale())}
              </Button>
            </Link>
          </div>

          {/* Popular job searches - links to valid /jobs/:role/:city routes (X16: 10 applications matches FREE tier) */}
          <div className="text-left">
            <div className="flex items-center gap-2 mb-4 justify-center">
              <TrendingUp className="w-4 h-4 text-primary-500" aria-hidden />
              <span className="text-sm font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider">{t("404.popularSearches", getLocale())}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {trendingSearches.map((search) => (
                <Link
                  key={search.path}
                  to={search.path}
                  aria-label={`Browse ${search.label}`}
                  className="flex items-center gap-3 p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-700 hover:border-primary-200 dark:hover:border-primary-600 hover:shadow-md transition-all group"
                >
                  <div className="w-9 h-9 bg-primary-50 dark:bg-primary-900/30 rounded-lg flex items-center justify-center text-primary-500 group-hover:bg-primary-500 group-hover:text-white transition-colors shrink-0">
                    <Briefcase className="w-4 h-4" aria-hidden />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-slate-900 truncate">{search.label}</p>
                    <p className="text-[10px] text-slate-400 font-medium">{t("404.applyWithAI", getLocale())}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-primary-500 transition-colors shrink-0" aria-hidden />
                </Link>
              ))}
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
