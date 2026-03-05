import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight, LayoutDashboard, Sparkles, Briefcase, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { Logo } from '../brand/Logo';
import { ThemeToggle } from '../ThemeToggle';
import { LanguageSelector } from '../LanguageSelector';
import { cn } from '../../lib/utils';
import { MobileDrawer, MobileDrawerHeader, MobileDrawerBody, MobileDrawerFooter } from '../navigation/MobileDrawer';
import { useAuth } from '../../hooks/useAuth';

export function MarketingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [windowWidth, setWindowWidth] = useState(1920); // Default for SSR
  const [isClient, setIsClient] = useState(false);
  const location = useLocation();
  const { user, loading } = useAuth();

  useEffect(() => {
    setIsClient(true);
    setWindowWidth(window.innerWidth);
    
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleResize, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleResize);
    };
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

  // Animated connection lines suggesting job matching flow
  const connectionLines = [
    { id: 1, delay: 0, duration: 4 },
    { id: 2, delay: 1.5, duration: 5 },
    { id: 3, delay: 3, duration: 4.5 },
  ];

  return (
    <>
      {/* Purposeful animated background - connection flow visualization */}
      {isClient && isHomePage && !isScrolled && (
        <div className="fixed inset-0 overflow-hidden pointer-events-none z-40">
          <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
            <defs>
              <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#F59E0B" stopOpacity="0" />
                <stop offset="50%" stopColor="#F59E0B" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#2DD4BF" stopOpacity="0" />
              </linearGradient>
            </defs>
            {connectionLines.map((line) => (
              <motion.path
                key={line.id}
                d={`M -100,${60 + line.id * 25} Q ${windowWidth * 0.3},${40 + line.id * 15} ${windowWidth * 0.6},${70 + line.id * 20} T ${windowWidth + 100},${50 + line.id * 25}`}
                stroke="url(#lineGradient)"
                strokeWidth="1.5"
                fill="none"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{
                  pathLength: [0, 1, 1, 0],
                  opacity: [0, 0.6, 0.6, 0],
                  x: [0, 50, 100]
                }}
                transition={{
                  duration: line.duration,
                  delay: line.delay,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            ))}
          </svg>
          
          {/* Subtle floating icons representing job matching */}
          <motion.div
            className="absolute top-6 left-[15%]"
            animate={{
              y: [0, -8, 0],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            <Briefcase className="w-4 h-4 text-[#F59E0B]" />
          </motion.div>
          <motion.div
            className="absolute top-8 right-[20%]"
            animate={{
              y: [0, -6, 0],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          >
            <Search className="w-4 h-4 text-[#2DD4BF]" />
          </motion.div>
          <motion.div
            className="absolute bottom-4 left-[40%]"
            animate={{
              y: [0, -10, 0],
              opacity: [0.2, 0.4, 0.2]
            }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          >
            <Sparkles className="w-3 h-3 text-[#F87171]" />
          </motion.div>
        </div>
      )}
      
      <nav
      aria-label="Main navigation"
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
        shouldBeTransparent
          ? "bg-white/70 backdrop-blur-2xl border-b border-[#E7E5E4]/50 py-3"
          : "bg-white/95 backdrop-blur-2xl border-b border-[#E7E5E4]/60 shadow-sm shadow-[#F59E0B]/5 py-2"
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[64px] flex items-center justify-between">
      {/* Logo */}
      <div className="relative">
        <Logo to="/" onClick={closeMenu} variant="light" />
      </div>

      {/* Desktop Nav */}
      <div className="hidden lg:flex items-center gap-1">
        {navLinks.map((link, index) => (
          <motion.div
            key={link.path}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.05 }}
          >
            <Link
              to={link.path}
              className={cn(
                "text-[15px] font-medium transition-colors px-4 py-2 rounded-lg relative group",
                shouldBeTransparent
                  ? "text-[#57534E] hover:text-[#2D2A26]"
                  : location.pathname === link.path ? "text-[#2D2A26] font-semibold" : "text-[#57534E] hover:text-[#2D2A26]"
              )}
            >
              {link.name}
              {/* Subtle background on hover */}
              <span className="absolute inset-0 bg-[#F5F5F4] rounded-lg scale-95 opacity-0 group-hover:opacity-100 transition-all -z-10" />
              {/* Active indicator line */}
              <span className={cn(
                "absolute bottom-1 left-1/2 -translate-x-1/2 h-0.5 bg-[#F59E0B] rounded-full transition-all",
                location.pathname === link.path || (link.path.startsWith('/#') && location.pathname === '/')
                  ? "w-4 opacity-100"
                  : "w-0 group-hover:w-4 opacity-0 group-hover:opacity-100"
              )} />
            </Link>
          </motion.div>
        ))}
      </div>

        {/* CTA Buttons */}
        <div className="hidden lg:flex items-center gap-2">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="flex items-center gap-2"
          >
            <LanguageSelector />
            <ThemeToggle className="text-[#57534E] hover:text-[#2D2A26] transition-colors" />
            {isLoggedIn ? (
              <>
                <Link
                  to="/app/dashboard"
                  className={cn(
                    "text-[15px] font-medium transition-colors flex items-center gap-2 px-3 py-2 rounded-lg group hover:bg-[#F5F5F4]",
                    shouldBeTransparent ? "text-[#57534E]" : "text-[#57534E]"
                  )}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span>Dashboard</span>
                </Link>
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Link
                    to="/app/jobs"
                    className="h-10 px-5 rounded-lg text-sm font-semibold bg-[#2D2A26] text-white hover:bg-[#3D3A36] transition-all flex items-center gap-2 shadow-sm hover:shadow-md"
                  >
                    <Sparkles className="w-4 h-4" />
                    View Jobs
                  </Link>
                </motion.div>
              </>
            ) : (
              <>
                <Link
                  to="/login?mode=login"
                  className={cn(
                    "text-[15px] font-medium transition-colors px-3 py-2 rounded-lg hover:bg-[#F5F5F4]",
                    shouldBeTransparent ? "text-[#57534E]" : "text-[#57534E]"
                  )}
                >
                  Log in
                </Link>
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Link
                    to="/login"
                    className="h-10 px-5 rounded-lg text-sm font-semibold bg-[#2D2A26] text-white hover:bg-[#3D3A36] transition-all flex items-center gap-2 shadow-sm hover:shadow-md"
                  >
                    Get 20 Free <ArrowRight className="w-4 h-4" />
                  </Link>
                </motion.div>
              </>
            )}
          </motion.div>
        </div>

        {/* Mobile Menu Toggle */}
        <motion.button
          className={cn(
            "lg:hidden p-2 -mr-2 rounded-lg transition-all",
            "text-[#57534E] hover:text-[#2D2A26] hover:bg-[#F5F5F4]"
          )}
          onClick={() => setIsMobileMenuOpen((prev) => !prev)}
          aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={isMobileMenuOpen}
          aria-controls="marketing-mobile-drawer"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <AnimatePresence mode="wait">
            {isMobileMenuOpen ? (
              <motion.div
                key="close"
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: 90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <X className="w-6 h-6" />
              </motion.div>
            ) : (
              <motion.div
                key="menu"
                initial={{ rotate: 90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: -90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Menu className="w-6 h-6" />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
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
                "text-[15px] font-semibold block py-3 px-4 rounded-xl transition-all active:scale-[0.98]",
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
                className="text-[15px] font-medium block py-3 px-4 rounded-xl transition-all active:scale-[0.98] text-[#57534E] hover:bg-[#FAFAF9] hover:text-[#2D2A26] flex items-center gap-2"
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
              <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                <Link
                  to="/app/jobs"
                  onClick={closeMenu}
                  className="block w-full h-12 rounded-xl text-[15px] font-semibold bg-[#2D2A26] text-white hover:bg-[#3D3A36] transition-all flex items-center justify-center shadow-sm"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Go to Dashboard
                </Link>
              </motion.div>
            ) : (
              <>
                <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                  <Link
                    to="/login"
                    onClick={closeMenu}
                    className="block w-full h-12 rounded-xl text-[15px] font-semibold bg-[#2D2A26] text-white hover:bg-[#3D3A36] transition-all flex items-center justify-center shadow-sm"
                  >
                    Start Free
                  </Link>
                </motion.div>
                <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                  <Link
                    to="/login?mode=login"
                    onClick={closeMenu}
                    className="block w-full h-12 rounded-xl text-[15px] font-medium border-2 border-[#E7E5E4] text-[#57534E] hover:border-[#D6D3D1] hover:bg-[#FAFAF9] transition-all flex items-center justify-center"
                  >
                    Log in
                  </Link>
                </motion.div>
              </>
            )}
          </div>
        </MobileDrawerFooter>
      </MobileDrawer>
    </nav>
    </>
  );
}
