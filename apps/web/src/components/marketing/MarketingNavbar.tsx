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

  return (
    <nav
      aria-label="Main navigation"
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled || isMobileMenuOpen
        ? 'bg-white/95 backdrop-blur-xl border-b border-gray-200/60 shadow-sm'
        : 'bg-white/80 backdrop-blur-sm'
        }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-[72px] flex items-center justify-between">
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
              className={`text-[15px] font-medium transition-all hover:text-gray-900 active:scale-95 ${location.pathname === link.path ? 'text-gray-900' : 'text-gray-500'
                }`}
            >
              {link.name}
            </Link>
          ))}
        </div>

        {/* CTA Buttons */}
        <div className="hidden lg:flex items-center gap-5">
          <ThemeToggle />
          {isLoggedIn ? (
            <>
              <Link to="/app/dashboard" className="text-[15px] font-medium text-gray-500 hover:text-gray-900 transition-colors flex items-center gap-2">
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <Link to="/app/jobs" className="h-10 px-6 rounded-full text-sm font-semibold bg-purple-600 text-white hover:bg-purple-700 hover:shadow-lg hover:shadow-purple-600/25 hover:-translate-y-0.5 transition-all flex items-center gap-2">
                  View Jobs <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          ) : (
            <>
              <Link to="/login?mode=login" className="text-[15px] font-medium text-gray-500 hover:text-gray-900 transition-colors">
                Log in
              </Link>
              <Link to="/login" className="h-10 px-6 rounded-full text-sm font-semibold bg-purple-600 text-white hover:bg-purple-700 hover:shadow-lg hover:shadow-purple-600/25 hover:-translate-y-0.5 transition-all flex items-center gap-2">
                  Get Started Free <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className="lg:hidden p-2.5 -mr-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all active:scale-90"
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
                className={`text-lg font-medium block py-4 px-4 rounded-xl transition-all active:scale-[0.98] ${location.pathname === link.path
                  ? 'bg-purple-50 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-50'
                  }`}
              >
                {link.name}
              </Link>
            ))}
            {isLoggedIn && (
              <Link
                to="/app/dashboard"
                onClick={closeMenu}
                className="text-lg font-medium block py-4 px-4 rounded-xl transition-all active:scale-[0.98] text-gray-600 hover:bg-gray-50 flex items-center gap-2"
              >
                <LayoutDashboard className="w-5 h-5" />
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
                className="block w-full h-12 rounded-full text-base font-semibold bg-purple-600 text-white hover:bg-purple-700 transition-all flex items-center justify-center"
              >
                  View Jobs
              </Link>
            ) : (
              <>
                <Link
                  to="/login?mode=login"
                  onClick={closeMenu}
                  className="block w-full h-12 rounded-full text-base font-semibold border-2 border-gray-200 text-gray-700 hover:bg-gray-50 transition-all flex items-center justify-center"
                >
                    Log in
                </Link>
                <Link
                  to="/login"
                  onClick={closeMenu}
                  className="block w-full h-12 rounded-full text-base font-semibold bg-purple-600 text-white hover:bg-purple-700 transition-all flex items-center justify-center"
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
