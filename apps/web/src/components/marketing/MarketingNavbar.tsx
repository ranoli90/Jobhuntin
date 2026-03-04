import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight, LayoutDashboard } from 'lucide-react';
import { Button } from '../ui/Button';
import { Logo } from '../brand/Logo';
import { ThemeToggle } from '../ThemeToggle';
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
          ? "bg-transparent py-2"
          : "bg-white/95 backdrop-blur-xl border-b border-gray-200/60 shadow-sm py-0"
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-[72px] flex items-center justify-between">
        {/* Logo */}
        <div className="relative">
          <Logo to="/" onClick={closeMenu} variant={shouldBeTransparent ? "dark" : "light"} />
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
                  ? "text-white/80 hover:text-white"
                  : location.pathname === link.path ? "text-gray-900" : "text-gray-500 hover:text-gray-900"
              )}
            >
              {link.name}
            </Link>
          ))}
        </div>

        {/* CTA Buttons */}
        <div className="hidden lg:flex items-center gap-5">
          <ThemeToggle className={shouldBeTransparent ? "text-white/80 hover:text-white" : ""} />
          {isLoggedIn ? (
            <>
              <Link
                to="/app/dashboard"
                className={cn(
                  "text-[15px] font-semibold transition-colors flex items-center gap-2",
                  shouldBeTransparent ? "text-white/80 hover:text-white" : "text-gray-500 hover:text-gray-900"
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
                  shouldBeTransparent ? "text-white/80 hover:text-white" : "text-gray-500 hover:text-gray-900"
                )}
              >
                Log in
              </Link>
              <Link to="/login" className={cn(
                "h-10 px-6 rounded-full text-sm font-bold transition-all flex items-center gap-2",
                shouldBeTransparent
                  ? "bg-white text-gray-900 hover:bg-gray-100"
                  : "bg-primary-600 text-white hover:bg-primary-500 hover:shadow-lg hover:shadow-primary-600/25 hover:-translate-y-0.5"
              )}>
                Get Started Free <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className={cn(
            "lg:hidden p-2.5 -mr-2 rounded-xl transition-all active:scale-90",
            shouldBeTransparent
              ? "text-white hover:bg-white/10"
              : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
          )}
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
          <Logo to="/" onClick={closeMenu} size="sm" variant="light" />
        </MobileDrawerHeader>

        <MobileDrawerBody>
          <div className="flex flex-col space-y-1 mt-2">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={closeMenu}
                className={`text-lg font-black tracking-tight block py-4 px-4 rounded-xl transition-all active:scale-[0.98] ${location.pathname === link.path
                  ? 'bg-primary-50 text-primary-900'
                  : 'text-gray-950 hover:bg-gray-50'
                  }`}
              >
                {link.name}
              </Link>
            ))}
            {isLoggedIn && (
              <Link
                to="/app/dashboard"
                onClick={closeMenu}
                className="text-lg font-black tracking-tight block py-4 px-4 rounded-xl transition-all active:scale-[0.98] text-gray-950 hover:bg-gray-50 flex items-center gap-2"
              >
                <LayoutDashboard className="w-5 h-5" />
                Dashboard
              </Link>
            )}
          </div>
        </MobileDrawerBody>

        <MobileDrawerFooter>
          <div className="flex flex-col gap-3 text-center">
            {isLoggedIn ? (
              <Link
                to="/app/jobs"
                onClick={closeMenu}
                className="block w-full h-14 rounded-2xl text-base font-bold bg-primary-600 text-white hover:bg-primary-500 transition-all flex items-center justify-center"
              >
                View Jobs
              </Link>
            ) : (
              <>
                <Link
                  to="/login?mode=login"
                  onClick={closeMenu}
                  className="block w-full h-14 rounded-2xl text-base font-bold border-2 border-gray-100 text-gray-950 hover:bg-gray-50 transition-all flex items-center justify-center"
                >
                  Log in
                </Link>
                <Link
                  to="/login"
                  onClick={closeMenu}
                  className="block w-full h-14 rounded-2xl text-base font-bold bg-primary-600 text-white hover:bg-primary-500 transition-all flex items-center justify-center shadow-xl shadow-primary-600/20"
                >
                  Get Started Free
                </Link>
              </>
            )}
          </div>
        </MobileDrawerFooter>
      </MobileDrawer>
    </nav>
  );
}
