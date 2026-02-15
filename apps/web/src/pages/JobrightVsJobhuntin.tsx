import React from 'react';
import { Link } from 'react-router-dom';
import { SEO } from '../components/marketing/SEO';
import { motion } from 'framer-motion';
import { 
  CheckCircle2, XCircle, ArrowRight, Star, Zap, Shield, Bot,
  Users, Clock, TrendingUp, Target, MessageSquare, FileText
} from 'lucide-react';

const jobrightData = {
  name: 'Jobright AI',
  tagline: 'AI job search copilot',
  founded: 2022,
  users: '1.25M',
  pricing: 'Free / $29.99/mo',
  features: {
    autoApply: true,
    resumeTailoring: true,
    coverLetter: true,
    stealthMode: false,
    fullAutonomy: false,
    aiAgent: true,
    insiderReferrals: true,
  }
};

const jobhuntinData = {
  name: 'JobHuntin',
  tagline: 'Fully autonomous AI job agent',
  founded: 2024,
  users: '50K+',
  pricing: 'Free / $19/mo',
  features: {
    autoApply: true,
    resumeTailoring: true,
    coverLetter: true,
    stealthMode: true,
    fullAutonomy: true,
    aiAgent: true,
    insiderReferrals: false,
  }
};

const comparisonTable = [
  { feature: 'AI-Powered Job Matching', jobright: true, jobhuntin: true },
  { feature: 'Auto-Apply to Jobs', jobright: true, jobhuntin: true },
  { feature: 'Resume Tailoring per Job', jobright: true, jobhuntin: true },
  { feature: 'Cover Letter Generation', jobright: true, jobhuntin: true },
  { feature: 'Fully Autonomous Operation', jobright: false, jobhuntin: true },
  { feature: 'Stealth Mode (Undetectable Apps)', jobright: false, jobhuntin: true },
  { feature: 'Background 24/7 Operation', jobright: false, jobhuntin: true },
  { feature: 'Insider Referral Network', jobright: true, jobhuntin: false },
  { feature: 'Browser Extension', jobright: true, jobhuntin: true },
  { feature: 'Mobile App', jobright: false, jobhuntin: false },
  { feature: 'Job Tracking Dashboard', jobright: true, jobhuntin: true },
  { feature: 'Interview Preparation', jobright: true, jobhuntin: true },
];

const faqItems = [
  {
    question: 'Is JobHuntin better than Jobright?',
    answer: 'It depends on your needs. Jobright is a "copilot" that helps you find and apply to jobs with AI assistance — but you\'re still actively involved. JobHuntin is an "autopilot" that runs completely in the background, tailoring resumes and applying to jobs while you sleep. If you want to set it and forget it, JobHuntin wins.',
  },
  {
    question: 'What\'s the main difference between Jobright and JobHuntin?',
    answer: 'Jobright requires your active participation — you review matches, click apply, and customize applications. JobHuntin operates autonomously: upload your resume once, set preferences, and the AI agent handles everything from job discovery to submission without further input.',
  },
  {
    question: 'Is Jobright free to use?',
    answer: 'Jobright offers a free tier with limited features. Their Pro plan costs $29.99/month. JobHuntin also offers a free tier (10 applications) and Pro at $19/month — significantly cheaper for unlimited autonomous applications.',
  },
  {
    question: 'Does Jobright have stealth mode?',
    answer: 'No, Jobright does not have stealth mode. Applications sent through Jobright may be detectable as automated by ATS systems. JobHuntin\'s Stealth Mode makes every application appear human-crafted, reducing the risk of automatic rejection.',
  },
  {
    question: 'Can I use both Jobright and JobHuntin together?',
    answer: 'You can, but most users find it redundant. JobHuntin handles the entire pipeline from job discovery to tailored submission. Using both would mean managing two separate systems for the same goal.',
  },
  {
    question: 'Which is better for job seekers with limited time?',
    answer: 'JobHuntin is better for busy professionals. Once configured, it requires zero daily effort. Jobright, while helpful, still needs your time to review matches and initiate applications.',
  },
];

export default function JobrightVsJobhuntin() {
  const title = 'Jobright vs JobHuntin | Honest 2026 Comparison';
  const description = 'Detailed comparison of Jobright AI vs JobHuntin. Compare features, pricing, automation level, and see which AI job search tool is right for you in 2026.';

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      <SEO
        title={title}
        description={description}
        ogTitle={title}
        canonicalUrl="https://jobhuntin.com/vs/jobright"
        includeDate={true}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": "https://jobhuntin.com/vs/jobright",
          },
          {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faqItems.map(item => ({
              "@type": "Question",
              "name": item.question,
              "acceptedAnswer": {
                "@type": "Answer",
                "text": item.answer
              }
            }))
          },
          {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "author": { "@type": "Organization", "name": "JobHuntin" },
            "datePublished": "2026-02-15",
            "dateModified": "2026-02-15",
          }
        ]}
      />

      <main className="max-w-5xl mx-auto px-6 py-16">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-semibold mb-6">
            <Star className="w-4 h-4" />
            Updated February 2026
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-slate-900 mb-6 tracking-tight">
            Jobright vs JobHuntin: Which AI Job Tool Wins?
          </h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto">
            An honest, detailed comparison of two leading AI job search platforms. We break down features, pricing, and real-world performance.
          </p>
        </motion.div>

        {/* Quick Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-3xl p-8 md:p-12 text-white mb-16"
        >
          <h2 className="text-2xl font-bold mb-6">Quick Verdict</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-primary-100 mb-3">Choose Jobright if:</h3>
              <ul className="space-y-2 text-primary-50">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  You want to stay hands-on with your job search
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  Insider referrals are important to you
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  You prefer a "copilot" approach
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-primary-100 mb-3">Choose JobHuntin if:</h3>
              <ul className="space-y-2 text-primary-50">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  You want fully autonomous job applications
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  Stealth mode is a priority
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  You\'re busy and want "set it and forget it"
                </li>
              </ul>
            </div>
          </div>
        </motion.div>

        {/* Feature Comparison Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-16"
        >
          <div className="p-6 border-b border-slate-100">
            <h2 className="text-2xl font-bold">Feature Comparison</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-6 py-4 font-semibold text-slate-600">Feature</th>
                  <th className="text-center px-6 py-4 font-semibold text-slate-600">
                    <div>Jobright</div>
                    <div className="text-sm font-normal text-slate-400">AI Copilot</div>
                  </th>
                  <th className="text-center px-6 py-4 font-semibold text-primary-600">
                    <div>JobHuntin</div>
                    <div className="text-sm font-normal text-primary-400">AI Autopilot</div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {comparisonTable.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-6 py-4 text-slate-700">{row.feature}</td>
                    <td className="px-6 py-4 text-center">
                      {row.jobright ? (
                        <CheckCircle2 className="w-6 h-6 text-green-500 mx-auto" />
                      ) : (
                        <XCircle className="w-6 h-6 text-slate-300 mx-auto" />
                      )}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {row.jobhuntin ? (
                        <CheckCircle2 className="w-6 h-6 text-green-500 mx-auto" />
                      ) : (
                        <XCircle className="w-6 h-6 text-slate-300 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Pricing Comparison */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid md:grid-cols-2 gap-6 mb-16"
        >
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">
            <h3 className="text-xl font-bold mb-4">Jobright Pricing</h3>
            <div className="space-y-4">
              <div className="flex justify-between py-3 border-b border-slate-100">
                <span className="text-slate-600">Free Tier</span>
                <span className="font-semibold">Limited features</span>
              </div>
              <div className="flex justify-between py-3 border-b border-slate-100">
                <span className="text-slate-600">Pro Plan</span>
                <span className="font-bold text-xl">$29.99/mo</span>
              </div>
              <div className="flex justify-between py-3">
                <span className="text-slate-600">Enterprise</span>
                <span className="font-semibold">Custom</span>
              </div>
            </div>
          </div>
          <div className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl p-8 border border-primary-200">
            <h3 className="text-xl font-bold mb-4 text-primary-900">JobHuntin Pricing</h3>
            <div className="space-y-4">
              <div className="flex justify-between py-3 border-b border-primary-200">
                <span className="text-primary-700">Free Tier</span>
                <span className="font-semibold text-primary-900">10 applications</span>
              </div>
              <div className="flex justify-between py-3 border-b border-primary-200">
                <span className="text-primary-700">Pro Plan</span>
                <span className="font-bold text-xl text-primary-900">$19/mo</span>
              </div>
              <div className="flex justify-between py-3">
                <span className="text-primary-700">Pro Annual</span>
                <span className="font-semibold text-primary-900">$15.80/mo</span>
              </div>
            </div>
            <div className="mt-6 p-4 bg-white/50 rounded-xl">
              <p className="text-sm text-primary-700 font-medium">
                💡 JobHuntin Pro is 37% cheaper than Jobright Pro
              </p>
            </div>
          </div>
        </motion.div>

        {/* Key Differences */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-16"
        >
          <h2 className="text-2xl font-bold mb-8">Key Differences Explained</h2>
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold mb-2">Copilot vs Autopilot</h3>
                  <p className="text-slate-600">
                    Jobright describes itself as an "AI copilot" — it assists you in your job search but requires your active participation. You review job matches, initiate applications, and stay involved. JobHuntin is an "autopilot" — once configured, it runs entirely in the background, discovering jobs, tailoring your materials, and submitting applications while you sleep.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center flex-shrink-0">
                  <Shield className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold mb-2">Stealth Mode Matters</h3>
                  <p className="text-slate-600">
                    Jobright doesn\'t offer stealth mode. This means ATS systems may detect automated applications, potentially flagging them. JobHuntin\'s Stealth Mode makes every application appear hand-crafted — random timing, varied mouse movements, and natural submission patterns that bypass detection.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center flex-shrink-0">
                  <Users className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold mb-2">Insider Referrals Network</h3>
                  <p className="text-slate-600">
                    Jobright offers a unique feature: their Insider Referrals network connects you with alumni and hiring managers at target companies. This is Jobright\'s standout feature and can significantly boost interview chances. JobHuntin doesn\'t currently offer this feature, focusing instead on application volume and quality.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* FAQ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mb-16"
        >
          <h2 className="text-2xl font-bold mb-8">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqItems.map((item, i) => (
              <details key={i} className="bg-white rounded-2xl shadow-sm border border-slate-200 group">
                <summary className="p-6 cursor-pointer list-none flex items-center justify-between font-semibold text-slate-900 hover:text-primary-600">
                  {item.question}
                  <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <div className="px-6 pb-6 text-slate-600">
                  {item.answer}
                </div>
              </details>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-center bg-white rounded-3xl p-12 shadow-sm border border-slate-200"
        >
          <h2 className="text-3xl font-bold mb-4">Ready to Try JobHuntin?</h2>
          <p className="text-slate-600 mb-8 max-w-xl mx-auto">
            Start with our free tier — 10 AI-tailored applications to see the difference autonomous job hunting makes.
          </p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 bg-primary-600 text-white px-8 py-4 rounded-xl font-bold hover:bg-primary-700 transition-colors"
          >
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </motion.div>
      </main>
    </div>
  );
}
