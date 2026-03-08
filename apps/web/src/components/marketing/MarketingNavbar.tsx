import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight, LayoutDashboard, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Logo } from '../brand/Logo';
import { ThemeToggle } from '../ThemeToggle';
import { LanguageSelector } from '../LanguageSelector';
import { cn } from '../../lib/utils';
import { MobileDrawer, MobileDrawerHeader, MobileDrawerBody, MobileDrawerFooter } from '../navigation/MobileDrawer';
import { useAuth } from '../../hooks/useAuth';

export function MarketingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { user, loading } = useAuth();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const closeMenu = useCallback(() => {
    setIsMobileMenuOpen(false);
  }, []);

  useEffect(() => {
    closeMenu();
  }, [location.pathname, location.search, location.hash, location.key, closeMenu]);

  const navLinks = [
    { name: "How it Works", path: "/#how-it-works" },
    { name: "Features", path: "/#features" },
    { name: "Success Stories", path: "/success-stories" },
    { name: "Pricing", path: "/pricing" },
    { name: "Blog", path: "/blog" },
  ];

  const isLoggedIn = !loading && user;
  const isHomePage = location.pathname === '/';
  const inHeroZone = isHomePage && !isScrolled && !isMobileMenuOpen;

  return (
    <nav
      aria-label="Main navigation"
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        inHeroZone
          ? "bg-transparent"
          : "bg-white/95 backdrop-blur-xl border-b border-[#E7E5E4]/60 shadow-sm"
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Logo
          to="/"
          onClick={closeMenu}
          variant={inHeroZone ? "dark" : "light"}
          size="md"
        />

        <div className="hidden lg:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={(e) => {
                if (link.path.startsWith('/#') && location.pathname === '/') {
                  e.preventDefault();
                  const id = link.path.split('#')[1];
                  const el = document.getElementById(id);
                  if (el) el.scrollIntoView({ behavior: 'smooth' });
                }
              }}
              className={cn(
                "text-[15px] font-medium px-4 py-2 rounded-lg transition-colors",
                inHeroZone
                  ? "text-white/90 hover:text-white"
                  : "text-[#57534E] hover:text-[#2D2A26]"
              )}
            >
              {link.name}
            </Link>
          ))}
        </div>

        <div className="hidden lg:flex items-center gap-2">
          <LanguageSelector />
          <ThemeToggle className={cn(inHeroZone ? "text-white/80" : "text-[#57534E]")} />
          {isLoggedIn ? (
            <>
              <Link
                to="/app/dashboard"
                className={cn(
                  "text-[15px] font-medium px-3 py-2 rounded-lg transition-colors flex items-center gap-2",
                  inHeroZone ? "text-white/90 hover:text-white" : "text-[#57534E] hover:bg-[#F5F5F4]"
                )}
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <Link
                to="/app/jobs"
                className="h-10 px-5 rounded-lg text-sm font-semibold bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-all flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                View Jobs
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/login?mode=login"
                className={cn(
                  "text-[15px] font-medium px-3 py-2 rounded-lg transition-colors",
                  inHeroZone ? "text-white/90 hover:text-white" : "text-[#57534E] hover:bg-[#F5F5F4]"
                )}
              >
                Log in
              </Link>
              <Link
                to="/login"
                className="h-10 px-5 rounded-lg text-sm font-semibold bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-all flex items-center gap-2"
              >
                Get 20 Free <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          )}
        </div>

        <button
          className={cn(
            "lg:hidden p-2 -mr-2 rounded-lg transition-colors touch-manipulation",
            inHeroZone ? "text-white hover:bg-white/10" : "text-[#57534E] hover:bg-[#F5F5F4]"
          )}
          onClick={() => setIsMobileMenuOpen((prev) => !prev)}
          aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={isMobileMenuOpen}
          aria-controls="marketing-mobile-drawer"
        >
          <AnimatePresence mode="wait">
            {isMobileMenuOpen ? (
              <motion.div key="close" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <X className="w-6 h-6" />
              </motion.div>
            ) : (
              <motion.div key="menu" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <Menu className="w-6 h-6" />
              </motion.div>
            )}
          </AnimatePresence>
        </button>
      </div>

      <MobileDrawer
        isOpen={isMobileMenuOpen}
        onClose={closeMenu}
        side="right"
        drawerId="marketing-mobile-drawer"
      >
        <MobileDrawerHeader onClose={closeMenu}>
          <Logo to="/" onClick={closeMenu} size="md" variant="light" />
        </MobileDrawerHeader>

        <MobileDrawerBody>
          <nav className="flex flex-col space-y-0.5 mt-1" aria-label="Mobile navigation">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={(e) => {
                  closeMenu();
                  if (link.path.startsWith('/#') && location.pathname === '/') {
                    e.preventDefault();
                    const id = link.path.split('#')[1];
                    const el = document.getElementById(id);
                    if (el) {
                      setTimeout(() => el.scrollIntoView({ behavior: 'smooth' }), 100);
                    }
                  }
                }}
                className={cn(
                  "text-[15px] font-semibold block py-3 px-4 rounded-xl transition-colors active:scale-[0.98]",
                  location.pathname === link.path || (link.path.startsWith('/#') && location.pathname === '/')
                    ? 'bg-[#F5F5F4] text-[#2D2A26]'
                    : 'text-[#57534E] hover:bg-[#FAFAF9] hover:text-[#2D2A26]'
                )}
              >
                {link.name}
              </Link>
            ))}
            {isLoggedIn && (
              <Link
                to="/app/dashboard"
                onClick={closeMenu}
                className="text-[15px] font-medium block py-3 px-4 rounded-xl transition-colors active:scale-[0.98] text-[#57534E] hover:bg-[#FAFAF9] hover:text-[#2D2A26] flex items-center gap-2"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
            )}
          </nav>
        </MobileDrawerBody>

        <MobileDrawerFooter>
          <div className="flex flex-col gap-3">
            {isLoggedIn ? (
              <Link
                to="/app/jobs"
                onClick={closeMenu}
                className="block w-full h-12 rounded-xl text-[15px] font-semibold bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-all flex items-center justify-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  onClick={closeMenu}
                  className="block w-full h-12 rounded-xl text-[15px] font-semibold bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-all flex items-center justify-center"
                >
                  Start Free
                </Link>
                <Link
                  to="/login?mode=login"
                  onClick={closeMenu}
                  className="block w-full h-12 rounded-xl text-[15px] font-medium border-2 border-[#E7E5E4] text-[#57534E] hover:border-[#D6D3D1] hover:bg-[#FAFAF9] transition-all flex items-center justify-center"
                >
                  Log in
                </Link>
              </>
            )}
          </div>
        </MobileDrawerFooter>
      </MobileDrawer>
    </nav>
  );
}
