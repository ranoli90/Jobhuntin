import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, ArrowRight, Moon } from 'lucide-react';
import { Button } from '../ui/Button';
import { Logo } from '../brand/Logo';
import { MobileDrawer, MobileDrawerHeader, MobileDrawerBody, MobileDrawerFooter } from '../navigation/MobileDrawer';

export function MarketingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu when the route changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  const navLinks = [
    { name: "Pricing", path: "/pricing" },
    { name: "Success Stories", path: "/success-stories" },
    { name: "About", path: "/about" },
    { name: "Extension", path: "/chrome-extension" },
  ];

  const closeMenu = () => setIsMobileMenuOpen(false);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled || isMobileMenuOpen
        ? 'bg-slate-900/90 backdrop-blur-xl border-b border-slate-700/60 shadow-lg'
        : 'bg-transparent'
        }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo */}
        <Logo to="/" onClick={closeMenu} variant="dark" />

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`text-sm font-bold transition-all hover:text-blue-400 active:scale-95 ${location.pathname === link.path ? 'text-blue-400' : 'text-slate-300'
                }`}
            >
              {link.name}
            </Link>
          ))}
        </div>

        {/* CTA Buttons */}
        <div className="hidden md:flex items-center gap-4">
          <Link to="/login?mode=login" className="text-sm font-black text-slate-300 hover:text-blue-400 transition-colors uppercase tracking-wider">
            Log in
          </Link>
          <Link to="/login">
            <Button variant="primary" size="sm" className="rounded-2xl px-6 shadow-xl shadow-blue-500/20 font-bold">
              Get Started <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className="md:hidden p-3 -mr-2 text-slate-300 hover:text-white bg-slate-800/50 hover:bg-slate-800 rounded-xl transition-all active:scale-90"
          onClick={() => setIsMobileMenuOpen((prev) => !prev)}
          aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={isMobileMenuOpen}
          aria-controls="mobile-marketing-drawer"
        >
          <Menu className="w-6 h-6" />
        </button>
      </div>

      {/* Universal Mobile Drawer */}
      <MobileDrawer
        isOpen={isMobileMenuOpen}
        onClose={closeMenu}
        side="right"
        drawerId="marketing-mobile-drawer"
      >
        <MobileDrawerHeader onClose={closeMenu}>
          <Logo to="/" onClick={closeMenu} size="sm" variant="dark" />
        </MobileDrawerHeader>

        <MobileDrawerBody>
          <div className="flex flex-col space-y-1 mt-2">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={closeMenu}
                className={`text-lg font-black block py-4 px-4 rounded-2xl transition-all active:scale-[0.98] ${location.pathname === link.path
                  ? 'bg-blue-900/20 text-blue-400 shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800'
                  }`}
              >
                {link.name}
              </Link>
            ))}
          </div>
        </MobileDrawerBody>

        <MobileDrawerFooter>
          <div className="flex flex-col gap-3">
            <Link
              to="/login?mode=login"
              onClick={closeMenu}
              className="block w-full"
            >
              <Button variant="outline" size="lg" className="w-full justify-center text-base py-4 rounded-2xl font-bold border-slate-700">Log in</Button>
            </Link>
            <Link
              to="/login"
              onClick={closeMenu}
              className="block w-full"
            >
              <Button variant="primary" size="lg" className="w-full justify-center text-base py-4 rounded-2xl shadow-2xl shadow-blue-500/30 font-black">
                Get Started Free
              </Button>
            </Link>
          </div>
        </MobileDrawerFooter>
      </MobileDrawer>
    </nav>
  );
}
