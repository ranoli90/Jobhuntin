import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bot, Menu, X, ArrowRight } from 'lucide-react';
import { Button } from '../ui/Button';
import { MobileDrawer, MobileDrawerHeader, MobileDrawerBody, MobileDrawerFooter } from '../navigation/MobileDrawer';

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

  // Lock body scroll is handled by MobileDrawer now

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
        <Link to="/" className="flex items-center gap-2 group z-[70] relative">
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
          className="md:hidden p-2 text-slate-600 hover:text-slate-900 z-[70] relative"
          onClick={() => setIsMobileMenuOpen(true)}
          aria-label="Open menu"
        >
          <Menu className="w-6 h-6" />
        </button>
      </div>

      {/* Universal Mobile Drawer */}
      <MobileDrawer isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} side="right">
        <MobileDrawerHeader onClose={() => setIsMobileMenuOpen(false)}>
            <div className="flex items-center gap-2">
                <div className="bg-gradient-to-tr from-primary-500 to-primary-600 p-1.5 rounded-lg rotate-3 shadow-sm">
                    <Bot className="text-white w-5 h-5" />
                </div>
                <span className="text-lg font-bold font-display text-slate-900 tracking-tight">JobHuntin</span>
            </div>
        </MobileDrawerHeader>

        <MobileDrawerBody>
            <div className="flex flex-col space-y-2">
              {navLinks.map((link) => (
                <Link 
                  key={link.path}
                  to={link.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`text-lg font-bold block py-3 px-2 rounded-xl transition-colors ${
                    location.pathname === link.path ? 'bg-primary-50 text-primary-600' : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {link.name}
                </Link>
              ))}
            </div>
        </MobileDrawerBody>
        
        <MobileDrawerFooter>
            <div className="flex flex-col gap-3">
                <Link to="/login?mode=login" onClick={() => setIsMobileMenuOpen(false)} className="block w-full">
                  <Button variant="outline" size="lg" className="w-full justify-center text-base py-3 rounded-xl">Log in</Button>
                </Link>
                <Link to="/login" onClick={() => setIsMobileMenuOpen(false)} className="block w-full">
                  <Button variant="primary" size="lg" className="w-full justify-center text-base py-3 rounded-xl shadow-xl shadow-primary-500/20">
                    Get Started Free
                  </Button>
                </Link>
            </div>
        </MobileDrawerFooter>
      </MobileDrawer>
    </nav>
  );
}
