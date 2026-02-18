import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, ArrowRight, LayoutDashboard } from 'lucide-react';
import { Button } from '../ui/Button';
import { Logo } from '../brand/Logo';
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

  const isLoggedIn = !loading && user;

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled || isMobileMenuOpen
        ? 'bg-stone-950/95 backdrop-blur-xl border-b border-stone-800/60 shadow-lg'
        : 'bg-transparent'
        }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo - always visible with gradient background */}
        <div className="relative">
          <div className="absolute inset-0" />
          <Logo to="/" onClick={closeMenu} variant="dark" />
        </div>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`text-sm font-medium transition-all hover:text-stone-100 active:scale-95 ${location.pathname === link.path ? 'text-stone-100' : 'text-stone-400'
                }`}
            >
              {link.name}
            </Link>
          ))}
        </div>

        {/* CTA Buttons */}
        <div className="hidden md:flex items-center gap-4">
          {isLoggedIn ? (
            <>
              <Link to="/app/dashboard" className="text-sm font-medium text-stone-400 hover:text-stone-100 transition-colors tracking-wide flex items-center gap-2">
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <Link to="/app/jobs">
                <Button variant="primary" size="sm" className="rounded-lg px-6 font-medium">
                  View Jobs <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </>
          ) : (
            <>
              <Link to="/login?mode=login" className="text-sm font-medium text-stone-400 hover:text-stone-100 transition-colors">
                Log in
              </Link>
              <Link to="/login">
                <Button variant="primary" size="sm" className="rounded-lg px-6 font-medium">
                  Get Started <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className="md:hidden p-3 -mr-2 text-stone-400 hover:text-white bg-stone-800/50 hover:bg-stone-800 rounded-lg transition-all active:scale-90"
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
                className={`text-lg font-medium block py-4 px-4 rounded-lg transition-all active:scale-[0.98] ${location.pathname === link.path
                  ? 'bg-stone-800 text-stone-100'
                  : 'text-stone-400 hover:bg-stone-800'
                  }`}
              >
                {link.name}
              </Link>
            ))}
            {isLoggedIn && (
              <Link
                to="/app/dashboard"
                onClick={closeMenu}
                className="text-lg font-medium block py-4 px-4 rounded-lg transition-all active:scale-[0.98] text-stone-400 hover:bg-stone-800 flex items-center gap-2"
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
                className="block w-full"
              >
                <Button variant="primary" size="lg" className="w-full justify-center text-base py-4 rounded-lg font-medium">
                  View Jobs
                </Button>
              </Link>
            ) : (
              <>
                <Link
                  to="/login?mode=login"
                  onClick={closeMenu}
                  className="block w-full"
                >
                  <Button variant="outline" size="lg" className="w-full justify-center text-base py-4 rounded-lg font-medium border-stone-700">Log in</Button>
                </Link>
                <Link
                  to="/login"
                  onClick={closeMenu}
                  className="block w-full"
                >
                  <Button variant="primary" size="lg" className="w-full justify-center text-base py-4 rounded-lg font-medium">
                    Get Started Free
                  </Button>
                </Link>
              </>
            )}
          </div>
        </MobileDrawerFooter>
      </MobileDrawer>
    </nav>
  );
}
