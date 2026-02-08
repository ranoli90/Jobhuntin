import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bot, Menu, X, ArrowRight } from 'lucide-react';
import { Button } from '../ui/Button';
import { motion, AnimatePresence } from 'framer-motion';

export function MarketingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: "Pricing", path: "/pricing" },
    { name: "Success Stories", path: "/success-stories" },
    { name: "Extension", path: "/chrome-extension" },
    { name: "Recruiters", path: "/recruiters" },
  ];

  return (
    <nav 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled || isMobileMenuOpen ? 'bg-white/80 backdrop-blur-xl border-b border-slate-200/50 shadow-sm' : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="bg-gradient-to-tr from-primary-500 to-primary-600 p-2 rounded-xl rotate-3 shadow-lg shadow-primary-500/20 group-hover:rotate-6 transition-transform duration-300">
            <Bot className="text-white w-6 h-6" />
          </div>
          <span className="text-xl font-bold font-display text-slate-900 tracking-tight">JobHuntin</span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link 
              key={link.path}
              to={link.path} 
              className={`text-sm font-medium transition-colors hover:text-primary-600 ${
                location.pathname === link.path ? 'text-primary-600' : 'text-slate-600'
              }`}
            >
              {link.name}
            </Link>
          ))}
        </div>

        {/* CTA Buttons */}
        <div className="hidden md:flex items-center gap-4">
          <Link to="/login?mode=login" className="text-sm font-bold text-slate-700 hover:text-slate-900 transition-colors">
            Log in
          </Link>
          <Link to="/login">
            <Button variant="primary" size="sm" className="rounded-full px-6 shadow-lg shadow-primary-500/20">
              Get Started <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </div>

        {/* Mobile Menu Toggle */}
        <button 
          className="md:hidden p-2 text-slate-600 hover:text-slate-900"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] bg-white md:hidden flex flex-col"
          >
            <div className="px-6 h-20 flex items-center justify-between border-b border-slate-100">
               <Link to="/" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center gap-2">
                  <div className="bg-gradient-to-tr from-primary-500 to-primary-600 p-2 rounded-xl">
                    <Bot className="text-white w-6 h-6" />
                  </div>
                  <span className="text-xl font-bold font-display text-slate-900 tracking-tight">JobHuntin</span>
               </Link>
               <button 
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-2 text-slate-500 hover:text-slate-900 bg-slate-50 rounded-full"
               >
                  <X className="w-6 h-6" />
               </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 flex flex-col justify-center space-y-8">
              <div className="flex flex-col gap-6 text-center">
                {navLinks.map((link) => (
                  <Link 
                    key={link.path}
                    to={link.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="text-2xl font-bold text-slate-800 hover:text-primary-600 transition-colors"
                  >
                    {link.name}
                  </Link>
                ))}
              </div>
              
              <div className="flex flex-col gap-4 max-w-xs mx-auto w-full pt-8 border-t border-slate-100">
                <Link to="/login" onClick={() => setIsMobileMenuOpen(false)}>
                  <Button variant="outline" size="lg" className="w-full justify-center text-lg py-6 rounded-2xl">Log in</Button>
                </Link>
                <Link to="/login" onClick={() => setIsMobileMenuOpen(false)}>
                  <Button variant="primary" size="lg" className="w-full justify-center text-lg py-6 rounded-2xl shadow-xl shadow-primary-500/20">
                    Get Started Free
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
