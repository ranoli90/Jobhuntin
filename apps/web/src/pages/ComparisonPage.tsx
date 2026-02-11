import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Bot, ArrowLeft, Sparkles, Shield, Zap, Target, TrendingUp, ArrowRight } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { ComparisonTable } from '../components/seo/ComparisonTable';
import { FAQAccordion, type FAQItem } from '../components/seo/FAQAccordion';
import { InternalLinkMesh } from '../components/seo/InternalLinkMesh';
import { ConversionCTA } from '../components/seo/ConversionCTA';
import { motion } from 'framer-motion';
import { Button } from '../components/ui/Button';
import competitorsData from '../data/competitors.json';

// Build lookup map from JSON data
const COMPETITORS_MAP = Object.fromEntries(
  competitorsData.map(c => [c.slug, c])
);

function generateFAQ(competitor: typeof competitorsData[0]): FAQItem[] {
  return [
    {
      question: `Is JobHuntin better than ${competitor.name}?`,
      answer: `JobHuntin tailors every resume and cover letter per application — ${competitor.name} ${competitor.features.auto_apply ? 'auto-applies but can\'t match that personalization' : 'doesn\'t even auto-apply'}. ${competitor.verdict}`,
    },
    {
      question: `How much does ${competitor.name} cost compared to JobHuntin?`,
      answer: `${competitor.name} starts at ${competitor.pricing.starts_at}. JobHuntin starts free with 10 apps, then $19/mo for unlimited — one interview pays for a lifetime of the tool.`,
    },
    {
      question: `Can I switch from ${competitor.name} to JobHuntin?`,
      answer: `Takes under 2 minutes. Upload your resume, set preferences, and the AI agent takes over — no data migration needed. Users who switch report 3x more interview callbacks.`,
    },
    {
      question: `Does ${competitor.name} tailor resumes for each application?`,
      answer: `${competitor.features.resume_tailoring ? `${competitor.name} has basic tailoring, but it's not per-application.` : `No, ${competitor.name} sends the same resume everywhere.`} JobHuntin customizes your resume and cover letter for every single submission to maximize ATS scores.`,
    },
    {
      question: `What makes JobHuntin different from ${competitor.name}?`,
      answer: `Fully autonomous operation, per-application resume tailoring, and stealth mode that makes every submission look hand-crafted. ${competitor.name} ${competitor.strengths[0]?.toLowerCase() || 'has its merits'}, but can't match that level of automation.`,
    },
  ];
}

function RatingBar({ label, them, us }: { label: string; them: number; us: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm font-medium">
        <span className="text-slate-600 capitalize">{label}</span>
        <span className="text-slate-400">{them}/10 vs <span className="text-primary-600 font-bold">{us}/10</span></span>
      </div>
      <div className="flex gap-2">
        <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-slate-400 h-full rounded-full transition-all duration-700"
            style={{ width: `${them * 10}%` }}
          />
        </div>
        <div className="flex-1 bg-primary-50 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-primary-500 h-full rounded-full transition-all duration-700"
            style={{ width: `${us * 10}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default function ComparisonPage() {
  const { competitorSlug } = useParams<{ competitorSlug: string }>();
  const competitor = competitorSlug ? COMPETITORS_MAP[competitorSlug] : null;

  if (!competitor) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-slate-50">
        <Bot className="w-16 h-16 text-primary-500 mb-4 animate-bounce" />
        <h1 className="text-2xl font-bold mb-4 text-slate-900">Competitor Not Found</h1>
        <p className="text-slate-500 mb-6">We don't have a comparison for this tool yet.</p>
        <Link to="/best/ai-auto-apply-tools" className="text-primary-600 hover:underline flex items-center gap-2 font-medium">
          <ArrowLeft className="w-4 h-4" /> Browse All Comparisons
        </Link>
      </div>
    );
  }

  const title = `JobHuntin vs ${competitor.name} | Features, Pricing & Verdict`;
  const description = `Detailed comparison of JobHuntin vs ${competitor.name}. Compare features, pricing, automation level, and see why job hunters choose JobHuntin as the best ${competitor.name} alternative.`;
  const canonicalUrl = `https://jobhuntin.com/vs/${competitorSlug}`;
  const faq = generateFAQ(competitor);

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO
        title={title}
        description={description}
        ogTitle={title}
        canonicalUrl={canonicalUrl}
        includeDate={true}
        schema={{
          "@context": "https://schema.org",
          "@type": "WebPage",
          "name": title,
          "description": description,
          "url": canonicalUrl,
          "about": [
            { "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "Job Search Automation" },
            { "@type": "SoftwareApplication", "name": competitor.name, "applicationCategory": "Job Search" },
          ],
        }}
      />

      <main className="max-w-5xl mx-auto px-6 py-24">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-20"
        >
          <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-blue-100">
            <Sparkles className="w-4 h-4" />
            Head-to-Head Comparison
          </div>
          <h1 className="text-4xl md:text-6xl font-black font-display mb-6 leading-tight text-slate-900">
            JobHuntin vs{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-blue-400">
              {competitor.name}
            </span>
          </h1>
          <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
            {competitor.verdict}
          </p>
          {competitor.status === 'discontinued' && (
            <div className="mt-4 inline-flex items-center gap-2 bg-red-50 text-red-600 px-4 py-2 rounded-full text-sm font-bold border border-red-100">
              ⚠️ {competitor.name} has been discontinued
            </div>
          )}
        </motion.div>

        {/* Feature Comparison Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-20"
        >
          <h2 className="text-2xl font-bold text-slate-900 mb-6">Feature Comparison</h2>
          <ComparisonTable competitor={competitor} />
        </motion.div>

        {/* Rating Bars */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-20 bg-white rounded-3xl border border-slate-100 p-8 shadow-sm"
        >
          <h2 className="text-2xl font-bold text-slate-900 mb-8">
            Performance Ratings
            <span className="block text-sm font-normal text-slate-400 mt-1">
              <span className="text-slate-500">{competitor.name}</span> vs <span className="text-primary-600">JobHuntin</span>
            </span>
          </h2>
          <div className="space-y-6">
            {Object.entries(competitor.rating_vs_jobhuntin || {}).map(([key, ratings]) => {
              const [them, us] = Array.isArray(ratings) ? ratings : [0, 0];
              return <RatingBar key={key} label={key.replace('_', ' ')} them={them} us={us} />;
            })}
          </div>
        </motion.div>

        {/* Weaknesses section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-20 grid md:grid-cols-2 gap-8"
        >
          <div className="bg-white rounded-3xl border border-red-100 p-8 shadow-sm">
            <h2 className="text-xl font-bold text-red-600 mb-6 flex items-center gap-2">
              <Target className="w-5 h-5" />
              Where {competitor.name} Falls Short
            </h2>
            <ul className="space-y-3">
              {competitor.weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-3 text-slate-600">
                  <span className="text-red-400 mt-1 text-lg leading-none">—</span>
                  <span className="text-sm font-medium">{w}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white rounded-3xl border border-emerald-100 p-8 shadow-sm">
            <h2 className="text-xl font-bold text-emerald-600 mb-6 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Why JobHuntin Wins
            </h2>
            <ul className="space-y-3">
              {competitor.differentiators.map((d, i) => (
                <li key={i} className="flex items-start gap-3 text-slate-600">
                  <span className="text-emerald-500 mt-1 text-lg leading-none">✓</span>
                  <span className="text-sm font-medium">{d}</span>
                </li>
              ))}
            </ul>
          </div>
        </motion.div>

        {/* Pricing Quick Compare */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-20"
        >
          <h2 className="text-2xl font-bold text-slate-900 mb-6">Pricing at a Glance</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-slate-100 rounded-3xl p-8">
              <h3 className="text-lg font-bold text-slate-500 mb-3">{competitor.name}</h3>
              <p className="text-3xl font-black text-slate-700 mb-2">
                {competitor.pricing.starts_at}
              </p>
              <ul className="text-sm text-slate-500 space-y-1 mt-4">
                {competitor.pricing.tiers?.map((t, i) => (
                  <li key={i}>• {t}</li>
                ))}
              </ul>
            </div>
            <div className="bg-primary-50 rounded-3xl p-8 border-2 border-primary-200 relative">
              <div className="absolute -top-3 right-6 bg-primary-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                BETTER VALUE
              </div>
              <h3 className="text-lg font-bold text-primary-600 mb-3">JobHuntin</h3>
              <p className="text-3xl font-black text-slate-900 mb-2">Free to Start</p>
              <ul className="text-sm text-slate-600 space-y-1 mt-4">
                <li>• Free tier — get started instantly</li>
                <li>• Pro — unlimited AI applications</li>
                <li>• Includes Stealth Mode & resume tailoring</li>
              </ul>
              <Link
                to="/pricing"
                className="inline-flex items-center gap-1 text-primary-600 font-bold text-sm mt-4 hover:gap-2 transition-all"
              >
                See full pricing <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </motion.div>

        {/* Key Features Grid */}
        <div className="mb-16 grid md:grid-cols-3 gap-8">
          {[
            { icon: Shield, title: "Undetectable", desc: "Stealth Mode simulates human browsing patterns to bypass bot detection on every job board." },
            { icon: Zap, title: "Fully Autonomous", desc: "Set your preferences once. Our AI agent discovers jobs, tailors resumes, and submits applications 24/7." },
            { icon: Target, title: "Personalized Quality", desc: "Every application gets a custom resume and cover letter optimized for the specific role's requirements." },
          ].map((item, i) => (
            <motion.div
              key={i}
              className="text-center bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-lg transition-all"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
            >
              <div className="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-5 text-primary-500 border border-slate-100">
                <item.icon className="w-7 h-7" />
              </div>
              <h3 className="font-bold text-lg mb-2 text-slate-900">{item.title}</h3>
              <p className="text-slate-500 text-sm leading-relaxed font-medium">{item.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* FAQ */}
        <FAQAccordion items={faq} competitorName={competitor.name} />

        {/* Internal Link Mesh */}
        <InternalLinkMesh
          currentSlug={competitorSlug!}
          currentType="vs"
          competitorCategory={competitor.category}
        />

        {/* Conversion CTA */}
        <ConversionCTA competitorName={competitor.name} variant="compare" />
      </main>


    </div>
  );
}
