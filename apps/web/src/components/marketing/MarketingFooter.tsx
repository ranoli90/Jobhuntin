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
        { name: "Directory", path: "/jobs/software-engineer/remote" }, // Placeholder
      ]
    },
    {
      title: "Resources",
      links: [
        { name: "Job Search Guides", path: "/guides" },
        { name: "Compare Alternatives", path: "/vs/lazyapply" },
        { name: "Denver Jobs", path: "/jobs/all/denver" },
        { name: "Remote Roles", path: "/jobs/all/remote" },
      ]
    },
    {
      title: "Company",
      links: [
        { name: "About Us", path: "/about" }, // Assuming exists or 404
        { name: "Privacy Policy", path: "/privacy" },
        { name: "Terms of Service", path: "/terms" },
        { name: "Contact", path: "mailto:support@jobhuntin.com" },
      ]
    }
  ];

  return (
    <footer className="bg-white border-t border-slate-100 py-12">
      <div className="max-w-7xl mx-auto px-6 flex flex-col items-center text-center">
        <Link to="/" className="flex items-center gap-2 group mb-8">
          <div className="bg-primary-50 p-2 rounded-xl group-hover:bg-primary-100 transition-colors">
            <Bot className="text-primary-600 w-6 h-6" />
          </div>
          <span className="text-xl font-bold font-display text-slate-900 tracking-tight">JobHuntin</span>
        </Link>

        <nav className="flex flex-wrap justify-center gap-8 mb-8 text-sm font-medium text-slate-600">
          <Link to="/pricing" className="hover:text-primary-600 transition-colors">Pricing</Link>
          <Link to="/login" className="hover:text-primary-600 transition-colors">Sign In</Link>
          <Link to="/terms" className="hover:text-primary-600 transition-colors">Terms</Link>
          <Link to="/privacy" className="hover:text-primary-600 transition-colors">Privacy</Link>
          <a href="mailto:support@jobhuntin.com" className="hover:text-primary-600 transition-colors">Contact</a>
        </nav>

        <div className="flex flex-col gap-4 items-center">
          <p className="text-slate-400 text-sm">
            &copy; {new Date().getFullYear()} JobHuntin AI Inc. All rights reserved.
          </p>
          <p className="text-slate-400 text-xs flex items-center gap-1">
            Made with <Heart className="w-3 h-3 text-red-500 fill-current" /> in Denver, CO
          </p>
        </div>
      </div>
    </footer>
  );
}
