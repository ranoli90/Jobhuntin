import React from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, Twitter, Linkedin, Github, Heart } from 'lucide-react';

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
    <footer className="bg-[#F7F6F3] dark:bg-slate-900 pt-16 sm:pt-20 pb-10 border-t border-[#E9E9E7] dark:border-slate-800 antialiased">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-x-8 gap-y-12 mb-16">
          <div className="col-span-2 md:col-span-3 lg:col-span-1">
            <Link to="/" className="flex items-center gap-2.5 group mb-5">
              <div className="bg-[#2D2A26] p-2 rounded-xl shadow-lg shadow-[#2D2A26]/10 group-hover:bg-[#3D3A36] transition-colors duration-300">
                <Briefcase className="text-white w-5 h-5" aria-hidden />
              </div>
              <span className="text-lg font-black text-[#2D2A26] dark:text-slate-100 tracking-tight">JobHuntin</span>
            </Link>
            <p className="text-[#787774] dark:text-slate-400 text-sm mb-6 max-w-xs leading-relaxed font-medium">
              The automation platform for job seekers.
            </p>
            <div className="flex gap-2.5">
              <a 
                href="https://twitter.com/jobhuntin" 
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Follow us on Twitter (opens in new tab)" 
                className="w-11 h-11 bg-white dark:bg-slate-800 border border-[#E9E9E7] dark:border-slate-700 rounded-full flex items-center justify-center text-[#787774] hover:text-[#455DD3] hover:border-[#455DD3]/30 hover:bg-[#455DD3]/5 transition-all focus:outline-none focus:ring-2 focus:ring-[#455DD3] focus:ring-offset-2"
              >
                <Twitter className="w-4 h-4" aria-hidden />
              </a>
              <a 
                href="https://linkedin.com/company/jobhuntin" 
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Follow us on LinkedIn (opens in new tab)" 
                className="w-11 h-11 bg-white dark:bg-slate-800 border border-[#E9E9E7] dark:border-slate-700 rounded-full flex items-center justify-center text-[#787774] hover:text-[#455DD3] hover:border-[#455DD3]/30 hover:bg-[#455DD3]/5 transition-all focus:outline-none focus:ring-2 focus:ring-[#455DD3] focus:ring-offset-2"
              >
                <Linkedin className="w-4 h-4" aria-hidden />
              </a>
              <a 
                href="https://github.com/jobhuntin" 
                target="_blank"
                rel="noopener noreferrer"
                aria-label="View our GitHub (opens in new tab)" 
                className="w-11 h-11 bg-white dark:bg-slate-800 border border-[#E9E9E7] dark:border-slate-700 rounded-full flex items-center justify-center text-[#787774] hover:text-[#455DD3] hover:border-[#455DD3]/30 hover:bg-[#455DD3]/5 transition-all focus:outline-none focus:ring-2 focus:ring-[#455DD3] focus:ring-offset-2"
              >
                <Github className="w-4 h-4" aria-hidden />
              </a>
            </div>
          </div>

          {footerSections.map((section) => (
            <div key={section.title}>
              <h3 className="font-bold text-[#2D2A26] dark:text-slate-100 mb-4 text-xs uppercase tracking-wider">{section.title}</h3>
              <ul className="space-y-2.5">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <Link
                      to={link.path}
                      className="text-[#787774] dark:text-slate-400 hover:text-[#2D2A26] dark:hover:text-slate-100 transition-colors text-sm font-medium"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-6 border-t border-[#E9E9E7] dark:border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-[#787774] dark:text-slate-500 text-xs font-semibold uppercase tracking-wider">
            &copy; {new Date().getFullYear()} JobHuntin Inc.
          </p>
          <p className="text-[#9B9A97] dark:text-slate-500 text-xs font-semibold uppercase tracking-wider flex items-center gap-1">
            Made with <Heart className="w-3.5 h-3.5 text-[#0D9488] fill-current" aria-hidden /> in Denver
          </p>
        </div>
      </div>
    </footer>
  );
}
