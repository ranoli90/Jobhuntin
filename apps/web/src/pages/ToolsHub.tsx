import React from "react";
import { Link } from "react-router-dom";
import { SEO } from "../components/marketing/SEO";
import { motion } from "framer-motion";
import {
  FileText,
  Mail,
  Target,
  Briefcase,
  BarChart3,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Zap,
  Shield,
  Clock,
} from "lucide-react";

const tools = [
  {
    slug: "ai-resume-builder",
    name: "AI Resume Builder",
    description:
      "Create a professional, ATS-optimized resume in minutes. Our AI analyzes job descriptions and tailors your resume for maximum impact.",
    icon: FileText,
    features: [
      "ATS-optimized templates",
      "Keyword matching",
      "One-click tailoring",
      "Export to PDF/Word",
    ],
    path: "/tools/ai-resume-builder",
  },
  {
    slug: "cover-letter-generator",
    name: "AI Cover Letter Generator",
    description:
      "Generate personalized cover letters for any job in seconds. Each letter is unique, professional, and tailored to the specific role.",
    icon: Mail,
    features: [
      "Job-specific content",
      "Multiple styles",
      "Quick customization",
      "ATS-friendly format",
    ],
    path: "/tools/cover-letter-generator",
  },
  {
    slug: "job-application-tracker",
    name: "Job Application Tracker",
    description:
      "Keep all your applications organized in one place. Track status, deadlines, follow-ups, and interviews effortlessly.",
    icon: Briefcase,
    features: [
      "Status tracking",
      "Interview scheduling",
      "Follow-up reminders",
      "Analytics dashboard",
    ],
    path: "/tools/job-tracker",
  },
  {
    slug: "ats-score-checker",
    name: "ATS Score Checker",
    description:
      "See how your resume performs against Applicant Tracking Systems. Get actionable tips to improve your score.",
    icon: BarChart3,
    features: [
      "Instant scoring",
      "Keyword analysis",
      "Format validation",
      "Improvement suggestions",
    ],
    path: "/tools/ats-score-checker",
  },
  {
    slug: "job-match-scorer",
    name: "Job Match Scorer",
    description:
      "Find out how well you match any job posting. AI analyzes your skills against requirements and suggests improvements.",
    icon: Target,
    features: [
      "Skill gap analysis",
      "Match percentage",
      "Keyword suggestions",
      "Role comparisons",
    ],
    path: "/tools/job-match-scorer",
  },
  {
    slug: "ai-job-assistant",
    name: "AI Job Assistant",
    description:
      "Get instant answers to all your job search questions. From salary negotiations to interview prep, your AI copilot is ready.",
    icon: Sparkles,
    features: [
      "24/7 availability",
      "Interview prep",
      "Salary guidance",
      "Career advice",
    ],
    path: "/tools/ai-job-assistant",
  },
];

export default function ToolsHub() {
  const title =
    "Free AI Job Search Tools | Resume Builder, ATS Checker & Cover Letter Gen";
  const description =
    "Free AI-powered job search tools: ATS-optimized resume builder, cover letter generator, job application tracker, and ATS score checker. No signup required for basic features.";

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900 font-sans text-slate-900 dark:text-slate-100">
      <SEO
        title={title}
        description={description}
        ogTitle="Free AI Job Search Tools | JobHuntin"
        ogImage="https://jobhuntin.com/og-image.png"
        canonicalUrl="https://jobhuntin.com/tools"
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "ItemList",
            name: "Free AI Job Search Tools",
            description: "Collection of free AI-powered tools for job seekers",
            numberOfItems: tools.length,
            itemListElement: tools.map((tool, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: tool.name,
              url: `https://jobhuntin.com${tool.path}`,
              description: tool.description,
            })),
          },
          {
            "@context": "https://schema.org",
            "@type": "WebPage",
            name: title,
            description: description,
            url: "https://jobhuntin.com/tools",
            provider: {
              "@type": "Organization",
              name: "JobHuntin",
              url: "https://jobhuntin.com",
            },
          },
        ]}
      />

      <main className="max-w-6xl mx-auto px-6 py-16">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-primary-100 text-primary-700 px-4 py-2 rounded-full text-sm font-semibold mb-6">
            <Zap className="w-4 h-4" />
            100% Free Tools
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-slate-900 mb-6 tracking-tight">
            AI-Powered Job Search Tools
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Everything you need to land your dream job. Build better resumes,
            write cover letters faster, and track your progress — all powered by
            AI.
          </p>
        </motion.div>

        {/* Trust badges */}
        <div className="flex flex-wrap justify-center gap-8 mb-16 text-sm text-slate-600">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-green-500" />
            No credit card required
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-500" />
            Privacy-first design
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-green-500" />
            Instant results
          </div>
        </div>

        {/* Tools Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tools.map((tool, index) => (
            <motion.div
              key={tool.slug}
              id={tool.slug}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Link
                to={`/tools#${tool.slug}`}
                className="block bg-white rounded-2xl p-6 shadow-sm border border-slate-100 hover:shadow-lg hover:border-primary-200 transition-all group h-full"
              >
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                    <tool.icon className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-lg font-bold text-slate-900 group-hover:text-primary-600 transition-colors">
                      {tool.name}
                    </h2>
                  </div>
                </div>
                <p className="text-slate-600 text-sm mb-4 leading-relaxed">
                  {tool.description}
                </p>
                <ul className="space-y-2">
                  {tool.features.map((feature, index_) => (
                    <li
                      key={index_}
                      className="flex items-center gap-2 text-sm text-slate-500"
                    >
                      <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-primary-600 font-semibold text-sm">
                  Try Free
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-20 bg-gradient-to-r from-primary-600 to-primary-700 rounded-3xl p-10 text-center text-white"
        >
          <h2 className="text-3xl font-bold mb-4">Want Complete Automation?</h2>
          <p className="text-primary-100 mb-8 max-w-xl mx-auto">
            Our tools are great, but JobHuntin Pro takes it further. Set your
            preferences once, and our AI agent applies to hundreds of jobs
            automatically.
          </p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 bg-white text-primary-700 px-8 py-4 rounded-xl font-bold hover:bg-primary-50 transition-colors"
          >
            Start Auto-Applying
            <ArrowRight className="w-5 h-5" />
          </Link>
        </motion.div>
      </main>
    </div>
  );
}
