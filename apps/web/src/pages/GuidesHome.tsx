import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Bot,
  ArrowLeft,
  BookOpen,
  Zap,
  Shield,
  Search,
  ChevronRight,
  Target,
  Menu,
  X,
} from "lucide-react";
import { SEO } from "../components/marketing/SEO";
import { motion, useReducedMotion } from "framer-motion";
import { GoogleSearch } from "../components/ui/GoogleSearch";
import { useDynamicData } from "../hooks/useDynamicData";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

export default function GuidesHome() {
  const [searchOpen, setSearchOpen] = useState(false);
  const shouldReduceMotion = useReducedMotion();
  const { data: guidesRaw, loading } = useDynamicData(
    () => import("../data/guides.json"),
  );

  const GUIDES = useMemo(() => {
    if (!guidesRaw) return [];
    return Object.entries(
      guidesRaw as Record<
        string,
        { title: string; category: string; readTime: string; content: string }
      >,
    ).map(([slug, data]) => ({
      slug,
      title: data.title,
      desc: data.content.replaceAll(/<[^>]+>/g, "").slice(0, 140) + "...",
      category: data.category,
      readTime: data.readTime,
    }));
  }, [guidesRaw]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingSpinner label="Loading..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO
        title="Job Search Guides | AI Auto-Apply, ATS Optimization & Resume Tips 2026"
        description="Master AI-powered job hunting with our guides. Learn to beat ATS systems, optimize your resume, use auto-apply tools ethically, and scale your job search safely."
        ogTitle="Job Search Guides | AI Automation Playbook"
        ogImage="https://jobhuntin.com/og-image.png"
        canonicalUrl="https://jobhuntin.com/guides"
        keywords="job search guides, AI job hunting tips, ATS optimization guide, resume tips 2026, cover letter guide"
        breadcrumbs={[
          { name: "Home", url: "https://jobhuntin.com" },
          { name: "Guides", url: "https://jobhuntin.com/guides" },
        ]}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: "JobHuntin Guides",
            description: "AI job search guides and playbooks",
            url: "https://jobhuntin.com/guides",
          },
          {
            "@context": "https://schema.org",
            "@type": "ItemList",
            name: "Job Search Guides",
            numberOfItems: GUIDES.length,
            itemListElement: GUIDES.map((guide, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: guide.title,
              url: `https://jobhuntin.com/guides/${guide.slug}`,
              description: guide.desc,
            })),
          },
        ]}
      />

      <main className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16 sm:mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-primary-50 text-primary-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-primary-100"
          >
            <BookOpen className="w-4 h-4" />
            Topical Authority Hub
          </motion.div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-sans font-black mb-6 sm:mb-8 leading-tight text-slate-900 text-balance">
            The AI Job Search <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-blue-400">
              Playbook
            </span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-500 max-w-2xl mx-auto font-medium text-balance">
            Deep-dives into the mechanisms of modern visibility and discovery in
            the job market.
          </p>

          <div className="mt-8 sm:mt-12">
            {/* Mobile Search Toggle */}
            <div className="sm:hidden">
              <button
                onClick={() => setSearchOpen(!searchOpen)}
                className="w-full bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between gap-4 hover:border-primary-500 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                aria-label={searchOpen ? "Close search" : "Open search"}
                aria-expanded={searchOpen}
              >
                <div className="flex items-center gap-3 text-slate-400">
                  <Search className="w-5 h-5" />
                  <span>Search guides...</span>
                </div>
                {searchOpen ? (
                  <X className="w-5 h-5" />
                ) : (
                  <Menu className="w-5 h-5" />
                )}
              </button>

              {searchOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4"
                >
                  <GoogleSearch />
                </motion.div>
              )}
            </div>

            {/* Desktop Search */}
            <div className="hidden sm:block">
              <GoogleSearch />
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 sm:gap-8">
          {GUIDES.map((guide, index) => (
            <motion.div
              key={guide.slug}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: shouldReduceMotion ? 0 : index * 0.1 }}
              viewport={{ once: true }}
              className="group bg-white rounded-[2rem] sm:rounded-[2.5rem] p-6 sm:p-8 lg:p-10 border border-slate-100 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4 sm:mb-6">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400 bg-slate-50 px-2 sm:px-3 py-1 rounded-full border border-slate-100">
                    {guide.category}
                  </span>
                  <span className="text-xs text-slate-400 font-mono font-medium">
                    {guide.readTime} read
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl lg:text-3xl font-bold font-display mb-3 sm:mb-4 text-slate-900 group-hover:text-primary-600 transition-colors line-clamp-2">
                  {guide.title}
                </h3>
                <p className="text-slate-500 mb-6 sm:mb-8 leading-relaxed font-medium text-sm sm:text-base line-clamp-3">
                  {guide.desc}
                </p>
              </div>
              <Link
                to={`/guides/${guide.slug}`}
                className="inline-flex items-center gap-2 font-bold text-slate-900 hover:text-primary-600 hover:gap-4 transition-all text-sm sm:text-base"
              >
                Read Guide <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />
              </Link>
            </motion.div>
          ))}
        </div>

        <div className="mt-24 sm:mt-32 p-8 sm:p-12 bg-slate-900 rounded-[2rem] sm:rounded-[3rem] text-white relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-64 sm:w-96 h-64 sm:h-96 bg-primary-500/20 rounded-full blur-[60px] sm:blur-[100px] -mr-32 sm:-mr-48 -mt-32 sm:-mt-48" />
          <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-8 lg:gap-12">
            <div className="max-w-xl">
              <h2 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6 font-display text-balance">
                Looking for a specific role?
              </h2>
              <p className="text-slate-400 mb-0 text-base sm:text-lg font-medium text-balance">
                Explore our programmatic niche hubs to see how JobHuntin
                optimizes visibility for your specific career path.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 w-full lg:w-auto">
              <Link
                to="/jobs/cashier/remote"
                className="bg-white/10 hover:bg-white/20 px-4 sm:px-6 py-3 rounded-xl sm:rounded-2xl text-sm font-bold transition-colors border border-white/5 text-center"
              >
                Cashier Jobs
              </Link>
              <Link
                to="/jobs/sales-associate/denver"
                className="bg-white/10 hover:bg-white/20 px-4 sm:px-6 py-3 rounded-xl sm:rounded-2xl text-sm font-bold transition-colors border border-white/5 text-center"
              >
                Sales Associate Denver
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
