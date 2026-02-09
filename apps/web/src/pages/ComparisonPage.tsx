import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Bot, ArrowLeft, Sparkles, Shield, Zap, Target } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { CompetitorComparison } from '../components/marketing/CompetitorComparison';
import { motion } from 'framer-motion';
import { Button } from '../components/ui/Button';

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
      <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-slate-50">
        <Bot className="w-16 h-16 text-primary-500 mb-4 animate-bounce" />
        <h1 className="text-2xl font-bold mb-4 text-slate-900">Competitor Simulation Not Found</h1>
        <Link to="/" className="text-primary-600 hover:underline flex items-center gap-2 font-medium">
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
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
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


      <main className="max-w-5xl mx-auto px-6 py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-20"
        >
          <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-blue-100">
            <Sparkles className="w-4 h-4" />
            Competitive Authority Modeling
          </div>
          <h1 className="text-5xl md:text-7xl font-black font-display mb-8 leading-tight text-slate-900">
            Better than <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-blue-400">{competitor.name}</span>
          </h1>
          <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
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
            <motion.div
              key={i}
              className="text-center bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-lg transition-all"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
            >
              <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-sm border border-slate-100 text-primary-500 group-hover:bg-primary-50 transition-colors">
                <item.icon className="w-8 h-8" />
              </div>
              <h3 className="font-bold text-xl mb-3 text-slate-900">{item.title}</h3>
              <p className="text-slate-500 leading-relaxed font-medium">{item.desc}</p>
            </motion.div>
          ))}
        </div>

        <div className="mt-32 bg-slate-900 rounded-[3rem] p-12 text-white text-center relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10" />
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary-500/20 rounded-full blur-[100px] -mr-48 -mt-48" />

          <h2 className="text-4xl font-bold mb-6 relative z-10 font-display">Stop grinding. Start interviewing.</h2>
          <p className="text-slate-400 mb-10 relative z-10 max-w-lg mx-auto text-lg">
            Join the elite hunters who have already switched from {competitor.name} to JobHuntin.
          </p>
          <Button asChild className="bg-primary-600 hover:bg-primary-700 text-white px-10 py-6 h-auto rounded-2xl font-bold text-xl shadow-xl shadow-primary-500/20 relative z-10 border-none">
            <Link to="/login">
              Switch to JobHuntin
            </Link>
          </Button>
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
