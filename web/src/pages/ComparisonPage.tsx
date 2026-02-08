import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Bot, ArrowLeft, Sparkles, Shield, Zap, Target } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { CompetitorComparison } from '../components/marketing/CompetitorComparison';
import { motion } from 'framer-motion';

const COMPETITORS_DATA: Record<string, { name: string; weakness: string; strength: string }> = {
  'sorce': {
    name: 'Sorce.jobs',
    weakness: 'Manual intervention required for many steps. Lacks "Stealth Mode" human-browsing simulation.',
    strength: 'Market familiarity and early mover advantage.'
  },
  'simplify': {
    name: 'Simplify',
    weakness: 'Primarily a form-filler extension, not an autonomous agent. Requires active tab focus.',
    strength: 'Large database of common job application forms.'
  },
  'teal': {
    name: 'Teal',
    weakness: 'Broad career management tool. Lacks the specialized AI "hunting" focus for high-volume apps.',
    strength: 'Strong resume builder and career tracking features.'
  }
};

export default function ComparisonPage() {
  const { competitorSlug } = useParams<{ competitorSlug: string }>();
  const competitor = competitorSlug ? COMPETITORS_DATA[competitorSlug] : null;

  if (!competitor) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
        <Bot className="w-16 h-16 text-[#FF6B35] mb-4 animate-bounce" />
        <h1 className="text-2xl font-bold mb-4">Competitor Simulation Not Found</h1>
        <Link to="/" className="text-[#4A90E2] hover:underline flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Return to HQ
        </Link>
      </div>
    );
  }

  const title = `JobHuntin vs ${competitor.name} | The Best AI Job Hunter Alternative`;
  const description = `Compare JobHuntin with ${competitor.name}. See why our autonomous AI agent is the superior alternative for high-volume, human-like job applications.`;
  const canonicalUrl = `https://jobhuntin.com/vs/${competitorSlug}`;
  const ogImage = `https://sorce-web.onrender.com/api/og?job=${encodeURIComponent(`Vs ${competitor.name}`)}&company=JobHuntin&score=100&location=Global`;

  return (
    <div className="min-h-screen bg-[#FAF9F6] font-inter text-[#2D2D2D]">
      <SEO 
        title={title}
        description={description}
        ogTitle={title}
        ogImage={ogImage}
        canonicalUrl={canonicalUrl}
        schema={{
          "@context": "https://schema.org",
          "@type": "Article",
          "headline": title,
          "description": description,
          "url": canonicalUrl,
          "about": competitor.name
        }}
      />
      
      <nav className="px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="bg-[#FF6B35] p-2 rounded-xl rotate-3">
              <Bot className="text-white w-6 h-6" />
            </div>
            <span className="text-xl font-bold font-poppins">JobHuntin</span>
          </Link>
          <Link to="/" className="text-sm font-medium hover:text-[#FF6B35] flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </Link>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-20">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-20"
        >
          <div className="inline-flex items-center gap-2 bg-blue-50 text-[#4A90E2] px-4 py-1 rounded-full text-sm font-bold mb-6">
            <Sparkles className="w-4 h-4" />
            Competitive Authority Modeling
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold font-poppins mb-8 leading-tight">
            Better than <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF6B35] to-[#4A90E2]">{competitor.name}</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Experience the next evolution of career automation. While others fill forms, we hunt roles.
          </p>
        </motion.div>

        <CompetitorComparison competitor={competitor} />

        <div className="mt-24 grid md:grid-cols-3 gap-12">
          {[
            { icon: Shield, title: "Undetectable", desc: "Human-like browsing patterns bypass bot detection effortlessly." },
            { icon: Zap, title: "Autonomous", desc: "Set it and forget it. Our agent works while you sleep." },
            { icon: Target, title: "High Quality", desc: "Custom cover letters and resume tailoring for every role." }
          ].map((item, i) => (
            <div key={i} className="text-center">
              <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-sm border border-gray-100 text-[#FF6B35]">
                <item.icon className="w-8 h-8" />
              </div>
              <h3 className="font-bold text-lg mb-2">{item.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-32 bg-gray-900 rounded-[3rem] p-12 text-white text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10" />
          <h2 className="text-3xl font-bold mb-6 relative z-10">Stop grinding. Start interviewing.</h2>
          <p className="text-gray-400 mb-10 relative z-10 max-w-lg mx-auto">
            Join the elite hunters who have already switched from {competitor.name} to JobHuntin.
          </p>
          <Link 
            to="/login" 
            className="inline-block bg-[#FF6B35] text-white px-10 py-4 rounded-2xl font-bold text-lg hover:scale-105 transition-transform shadow-xl shadow-orange-500/20"
          >
            Switch to JobHuntin
          </Link>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 py-12 mt-20">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-400 text-sm">
          &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
