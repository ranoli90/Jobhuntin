import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, Twitter, Linkedin, Github, Heart } from 'lucide-react';

export function MarketingFooter() {
  const footerSections = [
    {
      title: "Platform",
      links: [
        { name: "Pricing", path: "/pricing" },
        { name: "Success Stories", path: "/success-stories" },
        { name: "Chrome Extension", path: "/chrome-extension" },
        { name: "For Recruiters", path: "/recruiters" },
        { name: "Job Search Guides", path: "/guides" },
      ]
    },
    {
      title: "Compare Tools",
      links: [
        { name: "vs LazyApply", path: "/vs/lazyapply" },
        { name: "vs Simplify", path: "/vs/simplify" },
        { name: "vs Teal", path: "/vs/teal" },
        { name: "vs Jobright AI", path: "/vs/jobright" },
        { name: "vs Jobscan", path: "/vs/jobscan" },
        { name: "vs LoopCV", path: "/vs/loopcv" },
        { name: "Sonara AI Alternative", path: "/alternative-to/sonara-ai" },
      ]
    },
    {
      title: "Best Of",
      links: [
        { name: "Best Auto-Apply Tools", path: "/best/ai-auto-apply-tools" },
        { name: "Best AI Resume Builders", path: "/best/ai-resume-builders" },
        { name: "Best ATS Optimizers", path: "/best/ats-optimization-tools" },
        { name: "Job Search Automation", path: "/best/job-search-automation" },
        { name: "Sonara AI Alternatives", path: "/best/sonara-ai-alternatives" },
      ]
    },
    {
      title: "Company",
      links: [
        { name: "About Us", path: "/about" },
        { name: "Privacy Policy", path: "/privacy" },
        { name: "Terms of Service", path: "/terms" },
        { name: "Locations Directory", path: "/locations" },
        { name: "Contact", path: "mailto:support@jobhuntin.com" },
      ]
    },
    {
      title: "Top Locations",
      links: [
        { name: "AI Jobs in NYC", path: "/jobs/software-engineer/new-york" },
        { name: "London AI Careers", path: "/jobs/marketing-manager/london" },
        { name: "SF Tech Jobs", path: "/jobs/ai-developer/san-francisco" },
        { name: "Austin Software", path: "/jobs/software-engineer/austin" },
        { name: "Berlin Startups", path: "/jobs/product-manager/berlin" },
        { name: "Toronto Fintech", path: "/jobs/data-scientist/toronto" },
      ]
    }
  ];

  return (
    <footer className="bg-slate-50 pt-20 pb-10 border-t border-slate-200">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid md:grid-cols-2 lg:grid-cols-6 gap-12 mb-16">
          <div className="lg:col-span-2">
            <Link to="/" className="flex items-center gap-2 group mb-6">
              <div className="bg-gradient-to-tr from-primary-500 to-primary-600 p-2 rounded-xl rotate-3 shadow-lg shadow-primary-500/20 group-hover:rotate-6 transition-transform duration-300">
                <Bot className="text-white w-6 h-6" />
              </div>
              <span className="text-xl font-bold font-display text-slate-900 tracking-tight">JobHuntin</span>
            </Link>
            <p className="text-slate-500 mb-8 max-w-sm leading-relaxed">
              The AI agent that applies to jobs while you sleep.
              Land more interviews, negotiate better offers, and get back your free time.
            </p>
            <div className="flex gap-4">
              <a href="#" className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-slate-400 hover:text-[#1DA1F2] hover:shadow-md transition-all">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-slate-400 hover:text-[#0077b5] hover:shadow-md transition-all">
                <Linkedin className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-slate-400 hover:text-slate-900 hover:shadow-md transition-all">
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>

          {footerSections.map((section) => (
            <div key={section.title}>
              <h3 className="font-bold text-slate-900 mb-6">{section.title}</h3>
              <ul className="space-y-4">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <Link
                      to={link.path}
                      className="text-slate-500 hover:text-primary-600 transition-colors text-sm font-medium"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 border-t border-slate-200 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-slate-400 text-sm">
            &copy; {new Date().getFullYear()} JobHuntin AI Inc. All rights reserved.
          </p>
          <p className="text-slate-400 text-sm flex items-center gap-1">
            Made with <Heart className="w-4 h-4 text-red-500 fill-current" /> in Denver, CO
          </p>
        </div>
      </div>
    </footer>
  );
}
