import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft, BookOpen, Zap, Shield, Search, Sparkles, ChevronRight, Target } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { motion } from 'framer-motion';
import { GoogleSearch } from '../components/ui/GoogleSearch';

const GUIDES = [
  {
    slug: 'how-to-beat-ats-with-ai',
    title: 'How to Beat ATS with AI Agents',
    desc: 'The definitive guide to bypassing Applicant Tracking Systems using human-like automation.',
    category: 'Strategy',
    readTime: '8 min'
  },
  {
    slug: 'automated-job-search-ethics',
    title: 'The Ethics of Automated Job Hunting',
    desc: 'Why using AI to apply for jobs is the new standard, and how to stay transparent.',
    category: 'Ethics',
    readTime: '12 min'
  },
  {
    slug: 'scaling-your-applications-safely',
    title: 'Scaling Applications Safely',
    desc: 'How to send 100+ high-quality applications without getting banned by job boards.',
    category: 'Safety',
    readTime: '10 min'
  },
  {
    slug: 'ai-cover-letter-mastery',
    title: 'AI Cover Letter Mastery',
    desc: 'Crafting the perfect prompt for cover letters that recruiters actually read.',
    category: 'Tips',
    readTime: '6 min'
  }
];

export default function GuidesHome() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO 
        title="Job Search Playbook | AI Automation Guides"
        description="Master the art of automated job hunting. Explore our deep-dive guides on beating ATS, ethical AI usage, and scaling your search safely."
        ogTitle="Job Search Playbook | AI Automation Guides"
        ogImage="https://jobhuntin.com/og/guides.png"
        canonicalUrl="https://jobhuntin.com/guides"
        schema={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          "name": "JobHuntin Guides",
          "description": "AI job search guides and playbooks",
          "url": "https://jobhuntin.com/guides"
        }}
      />
      
      <nav className="px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="bg-gradient-to-tr from-primary-500 to-primary-600 p-2 rounded-xl rotate-3 shadow-lg shadow-primary-500/20">
              <Bot className="text-white w-6 h-6" />
            </div>
            <span className="text-xl font-bold font-display text-slate-900">JobHuntin</span>
          </Link>
          <Link to="/" className="text-sm font-medium text-slate-600 hover:text-primary-600 flex items-center gap-2 group transition-colors">
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Home
          </Link>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-24">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-orange-50 text-primary-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-orange-100"
          >
            <BookOpen className="w-4 h-4" />
            Topical Authority Hub
          </motion.div>
          <h1 className="text-5xl md:text-7xl font-black font-display mb-8 leading-tight text-slate-900">
            The AI Job Search <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-amber-500">Playbook</span>
          </h1>
          <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
            Deep-dives into the mechanisms of modern visibility and discovery in the job market.
          </p>
          
          <div className="mt-12">
            <GoogleSearch />
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {GUIDES.map((guide, i) => (
            <motion.div
              key={guide.slug}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="group bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-6">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400 bg-slate-50 px-3 py-1 rounded-full border border-slate-100">
                    {guide.category}
                  </span>
                  <span className="text-xs text-slate-400 font-mono font-medium">
                    {guide.readTime} read
                  </span>
                </div>
                <h3 className="text-3xl font-bold font-display mb-4 text-slate-900 group-hover:text-primary-600 transition-colors">
                  {guide.title}
                </h3>
                <p className="text-slate-500 mb-8 leading-relaxed font-medium">
                  {guide.desc}
                </p>
              </div>
              <Link 
                to={`/guides/${guide.slug}`} 
                className="inline-flex items-center gap-2 font-bold text-slate-900 hover:text-primary-600 hover:gap-4 transition-all"
              >
                Read Guide <ChevronRight className="w-5 h-5" />
              </Link>
            </motion.div>
          ))}
        </div>

        <div className="mt-32 p-12 bg-slate-900 rounded-[3rem] text-white relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary-500/20 rounded-full blur-[100px] -mr-48 -mt-48" />
          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-12">
            <div className="max-w-xl">
              <h2 className="text-3xl font-bold mb-6 font-display">Looking for a specific role?</h2>
              <p className="text-slate-400 mb-0 text-lg font-medium">
                Explore our programmatic niche hubs to see how JobHuntin optimizes visibility for your specific career path.
              </p>
            </div>
            <div className="flex flex-wrap gap-4">
              <Link to="/jobs/software-engineer/remote" className="bg-white/10 hover:bg-white/20 px-6 py-3 rounded-2xl text-sm font-bold transition-colors border border-white/5">Software Engineer Jobs</Link>
              <Link to="/jobs/marketing-manager/denver" className="bg-white/10 hover:bg-white/20 px-6 py-3 rounded-2xl text-sm font-bold transition-colors border border-white/5">Marketing Manager Denver</Link>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 py-12 mt-20">
        <div className="max-w-7xl mx-auto px-6 text-center text-slate-400 text-sm font-medium">
          &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
