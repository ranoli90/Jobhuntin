import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight, LayoutDashboard } from 'lucide-react';
import { Button } from '../ui/Button';
import { Logo } from '../brand/Logo';
import { ThemeToggle } from '../ThemeToggle';
import { cn } from '../../lib/utils';
import { MobileDrawer, MobileDrawerHeader, MobileDrawerBody, MobileDrawerFooter } from '../navigation/MobileDrawer';
import { useAuth } from '../../hooks/useAuth';

export function MarketingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { user, loading } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu when the route changes (pathname, search, or hash)
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname, location.search, location.hash, location.key]);

  const navLinks = [
    { name: "How it Works", path: "/#how-it-works" },
    { name: "Features", path: "/#features" },
    { name: "Success Stories", path: "/success-stories" },
    { name: "Pricing", path: "/pricing" },
    { name: "Blog", path: "/blog" },
  ];

  const closeMenu = () => setIsMobileMenuOpen(false);

  const isLoggedIn = !loading && user;

  const isHomePage = location.pathname === '/';
  const shouldBeTransparent = isHomePage && !isScrolled && !isMobileMenuOpen;

  return (
    <nav
      aria-label="Main navigation"
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
        shouldBeTransparent
          ? "bg-white/80 backdrop-blur-xl border-b border-gray-100/60 py-2"
          : "bg-white/95 backdrop-blur-xl border-b border-gray-200/60 shadow-sm py-0"
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-[72px] flex items-center justify-between">
        {/* Logo */}
        <div className="relative">
          <Logo to="/" onClick={closeMenu} variant="light" />
        </div>

        {/* Desktop Nav */}
        <div className="hidden lg:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={cn(
                "text-[15px] font-semibold transition-all hover:opacity-100 active:scale-95 px-2 py-1 rounded-lg",
                shouldBeTransparent
                  ? "text-gray-500 hover:text-gray-900"
                  : location.pathname === link.path ? "text-gray-900" : "text-gray-500 hover:text-gray-900"
              )}
            >
              {link.name}
            </Link>
          ))}
        </div>

        {/* CTA Buttons */}
        <div className="hidden lg:flex items-center gap-5">
          <ThemeToggle className="text-slate-500 hover:text-slate-900 transition-colors" />
          {isLoggedIn ? (
            <>
              <Link
                to="/app/dashboard"
                className={cn(
                  "text-[15px] font-semibold transition-colors flex items-center gap-2",
                  shouldBeTransparent ? "text-gray-500 hover:text-gray-900" : "text-gray-500 hover:text-gray-900"
                )}
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <Link to="/app/jobs" className="h-10 px-6 rounded-full text-sm font-bold bg-primary-600 text-white hover:bg-primary-500 hover:shadow-lg hover:shadow-primary-600/25 hover:-translate-y-0.5 transition-all flex items-center gap-2">
                View Jobs <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/login?mode=login"
                className={cn(
                  "text-[15px] font-semibold transition-colors",
                  shouldBeTransparent ? "text-gray-500 hover:text-gray-900" : "text-gray-500 hover:text-gray-900"
                )}
              >
                Log in
              </Link>
              <Link to="/login" className={cn(
                "h-11 px-6 rounded-full text-[15px] font-bold transition-all flex items-center gap-2",
                shouldBeTransparent
                  ? "bg-primary-600 text-white hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-600/30"
                  : "bg-primary-600 text-white hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-600/30 hover:-translate-y-0.5"
              )}>
                Get 20 Free <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className={cn(
            "lg:hidden p-2.5 -mr-2 rounded-xl transition-all active:scale-90",
            "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
          )}
          onClick={() => setIsMobileMenuOpen((prev) => !prev)}
          aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={isMobileMenuOpen}
          aria-controls="marketing-mobile-drawer"
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
          <Logo to="/" onClick={closeMenu} size="md" variant="light" />
        </MobileDrawerHeader>

        <MobileDrawerBody>
          <div className="flex flex-col space-y-0.5 mt-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => {
                  closeMenu();
                  // If it's a hash link on the same page, manually scroll
                  if (link.path.startsWith('/#') && location.pathname === '/') {
                    const id = link.path.split('#')[1];
                    const el = document.getElementById(id);
                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                  }
                }}
                className={cn(
                  "text-[15px] font-bold block py-4 px-5 rounded-2xl transition-all active:scale-[0.98]",
                  location.pathname === link.path || (link.path.startsWith('/#') && location.pathname === '/')
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                )}
              >
                {link.name}
              </Link>
            ))}
            {isLoggedIn && (
              <Link
                to="/app/dashboard"
                onClick={closeMenu}
                className="text-[15px] font-semibold block py-3.5 px-4 rounded-xl transition-all active:scale-[0.98] text-gray-600 hover:bg-gray-50 hover:text-gray-900 flex items-center gap-2"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
            )}
          </div>
        </MobileDrawerBody>

        <MobileDrawerFooter>
          <div className="flex flex-col gap-3">
            {isLoggedIn ? (
              <Link
                to="/app/jobs"
                onClick={closeMenu}
                className="block w-full h-14 rounded-2xl text-[15px] font-bold bg-primary-600 text-white hover:bg-primary-700 transition-all flex items-center justify-center shadow-lg shadow-primary-600/20"
              >
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login?mode=login"
                  onClick={closeMenu}
                  className="block w-full h-14 rounded-2xl text-[15px] font-bold border-2 border-slate-200 text-slate-700 hover:bg-slate-50 transition-all flex items-center justify-center"
                >
                  Log in
                </Link>
                <Link
                  to="/login"
                  onClick={closeMenu}
                  className="block w-full h-14 rounded-2xl text-[15px] font-bold bg-primary-600 text-white hover:bg-primary-700 transition-all flex items-center justify-center shadow-lg shadow-primary-600/20"
                >
                  Start Applying Free
                </Link>
              </>
            )}
          </div>
        </MobileDrawerFooter>
      </MobileDrawer>
    </nav>
  );
}
