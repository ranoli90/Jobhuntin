import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, Twitter, Linkedin, Github, Heart } from 'lucide-react';

export function MarketingFooter() {
  const footerSections = [
    {
      title: "Platform",
      links: [
        { name: "How it Works", path: "/#how-it-works" },
        { name: "Features", path: "/#features" },
        { name: "Pricing", path: "/pricing" },
        { name: "Success Stories", path: "/success-stories" },
        { name: "Chrome Extension", path: "/chrome-extension" },
        { name: "For Recruiters", path: "/recruiters" },
      ]
    },
    {
      title: "Features",
      links: [
        { name: "AI Resume Tailoring", path: "/#features" },
        { name: "Auto-Apply Engine", path: "/#features" },
        { name: "ATS Optimization", path: "/#features" },
        { name: "Application Tracking", path: "/#dashboard" },
        { name: "Interview Prep", path: "/#features" },
        { name: "Job Search Guides", path: "/guides" },
      ]
    },
    {
      title: "Resources",
      links: [
        { name: "Blog", path: "/blog" },
        { name: "Job Search Guides", path: "/guides" },
        { name: "Best Auto-Apply Tools", path: "/best/ai-auto-apply-tools" },
        { name: "Best AI Resume Builders", path: "/best/ai-resume-builders" },
        { name: "Best ATS Optimizers", path: "/best/ats-optimization-tools" },
      ]
    },
    {
      title: "Company",
      links: [
        { name: "About Us", path: "/about" },
        { name: "Privacy Policy", path: "/privacy" },
        { name: "Terms of Service", path: "/terms" },
        { name: "Do Not Sell My Info", path: "/privacy#ccpa" },
        { name: "Contact", path: "mailto:support@jobhuntin.com" },
      ]
    },
    {
      title: "Compare",
      links: [
        { name: "vs LazyApply", path: "/vs/lazyapply" },
        { name: "vs Simplify", path: "/vs/simplify" },
        { name: "vs Teal", path: "/vs/teal" },
        { name: "vs Jobright AI", path: "/vs/jobright" },
        { name: "vs Jobscan", path: "/vs/jobscan" },
      ]
    }
  ];

  return (
    <footer className="bg-gray-50 pt-20 pb-10 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-10 mb-16">
          <div className="col-span-2 md:col-span-3 lg:col-span-1">
            <Link to="/" className="flex items-center gap-2.5 group mb-5">
              <div className="bg-purple-600 p-2 rounded-xl shadow-lg shadow-purple-600/20 group-hover:bg-purple-700 transition-colors duration-300">
                <Bot className="text-white w-5 h-5" />
              </div>
              <span className="text-lg font-bold text-gray-900 tracking-tight">JobHuntin</span>
            </Link>
            <p className="text-gray-500 text-sm mb-6 max-w-xs leading-relaxed">
              The AI agent that applies to jobs while you sleep.
            </p>
            <div className="flex gap-2.5">
              <a href="#" aria-label="Follow us on Twitter" className="w-11 h-11 bg-white border border-gray-200 rounded-full flex items-center justify-center text-gray-400 hover:text-purple-600 hover:border-purple-200 hover:bg-purple-50 transition-all">
                <Twitter className="w-4 h-4" />
              </a>
              <a href="#" aria-label="Follow us on LinkedIn" className="w-11 h-11 bg-white border border-gray-200 rounded-full flex items-center justify-center text-gray-400 hover:text-purple-600 hover:border-purple-200 hover:bg-purple-50 transition-all">
                <Linkedin className="w-4 h-4" />
              </a>
              <a href="#" aria-label="View our GitHub" className="w-11 h-11 bg-white border border-gray-200 rounded-full flex items-center justify-center text-gray-400 hover:text-purple-600 hover:border-purple-200 hover:bg-purple-50 transition-all">
                <Github className="w-4 h-4" />
              </a>
            </div>
          </div>

          {footerSections.map((section) => (
            <div key={section.title}>
              <h3 className="font-semibold text-gray-900 mb-4 text-sm">{section.title}</h3>
              <ul className="space-y-2.5">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <Link
                      to={link.path}
                      className="text-gray-500 hover:text-purple-600 transition-colors text-sm"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-6 border-t border-gray-200 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-gray-400 text-sm">
            &copy; {new Date().getFullYear()} JobHuntin AI Inc. All rights reserved.
          </p>
          <p className="text-gray-400 text-sm flex items-center gap-1">
            Made with <Heart className="w-3.5 h-3.5 text-purple-400 fill-current" /> in Denver, CO
          </p>
        </div>
      </div>
    </footer>
  );
}
