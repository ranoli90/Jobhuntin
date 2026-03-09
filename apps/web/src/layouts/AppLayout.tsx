import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useBilling } from "../hooks/useBilling";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { PageTransition } from "../components/navigation/PageTransition";
import { MobileDrawer, MobileDrawerHeader, MobileDrawerBody, MobileDrawerFooter } from "../components/navigation/MobileDrawer";
import { AnimatePresence } from "framer-motion";
import { Logo } from "../components/brand/Logo";
import { cn } from "../lib/utils";
import {
  Menu,
  MoreHorizontal,
  LayoutDashboard,
  Briefcase,
  FileText,
  HelpCircle,
  Users,
  CreditCard,
  Settings,
  LogOut,
  Globe,
} from "lucide-react";
import { ThemeToggle } from "../components/ThemeToggle";
import { LanguageSelector } from "../components/LanguageSelector";

type NavItem = { label: string; to: string; icon: typeof LayoutDashboard; adminOnly?: boolean };

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/app/dashboard", icon: LayoutDashboard },
  { label: "Jobs", to: "/app/jobs", icon: Briefcase },
  { label: "Applications", to: "/app/applications", icon: FileText },
  { label: "Holds", to: "/app/holds", icon: HelpCircle },
  { label: "Team", to: "/app/team", icon: Users },
  { label: "Billing", to: "/app/billing", icon: CreditCard },
  { label: "Settings", to: "/app/settings", icon: Settings },
  // Admin only
  { label: "Sources", to: "/app/admin/sources", icon: Globe, adminOnly: true },
];

export default function AppLayout() {
  const { user, signOut } = useAuth();
  const { plan } = useBilling();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin';

  const closeMobile = () => setMobileMenuOpen(false);
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-bold transition-all active:scale-[0.98]",
      isActive
        ? "bg-primary-50 text-primary-700 shadow-sm ring-1 ring-primary-100"
        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
    );

  const visibleNavItems = NAV_ITEMS.filter(item => {
    if (item.adminOnly) return isAdmin;
    return true;
  });

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      {/* Skip to content link for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary-600 text-white px-4 py-2 rounded-lg font-medium z-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        aria-label="Skip to main content"
      >
        Skip to main content
      </a>
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 lg:flex">
        <div className="border-b border-slate-200 px-8 py-6">
          <Logo to="/app/dashboard" size="md" />
          <p className="text-[10px] text-slate-400 mt-2 font-black uppercase tracking-[0.2em] ml-1">Dashboard</p>
        </div>
        <nav className="flex-1 space-y-1 px-4 py-8">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-bold transition-all active:scale-[0.98]",
                  isActive
                    ? "bg-primary-50 text-primary-700 shadow-sm ring-1 ring-primary-100"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                )}>
                <Icon className="h-4 w-4" aria-hidden />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <div className="border-t border-slate-200 px-4 py-6">
          <div className="flex items-center gap-3 rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-200/50">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 text-white font-black grid place-items-center shadow-lg shadow-primary-500/20">
              {user?.email?.slice(0, 1).toUpperCase() ?? "J"}
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-bold truncate text-slate-900">{user?.email ?? "hello@user.com"}</p>
              <Badge variant="outline" size="sm" className="mt-0.5 text-[10px] uppercase font-black tracking-widest bg-white border-slate-200">
                {plan ?? "Free"}
              </Badge>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="mt-4 w-full justify-start text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl font-bold"
            onClick={signOut}
          >
            <LogOut className="mr-2 h-4 w-4" aria-hidden /> Sign out
          </Button>
        </div>
      </aside>

      {/* Universal Mobile Drawer */}
      <MobileDrawer isOpen={mobileMenuOpen} onClose={closeMobile} drawerId="app-mobile-drawer">
        <MobileDrawerHeader onClose={closeMobile}>
          <Logo to="/app/dashboard" size="sm" onClick={closeMobile} />
        </MobileDrawerHeader>

        <MobileDrawerBody>
          <nav className="space-y-1 mt-2">
            {visibleNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={navLinkClass}
                  onClick={closeMobile}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </MobileDrawerBody>

        <MobileDrawerFooter>
          <Button
            variant="ghost"
            className="w-full justify-start text-red-600 hover:bg-red-50 rounded-xl font-bold"
            onClick={() => {
              signOut();
              closeMobile();
            }}
          >
            <LogOut className="mr-2 h-4 w-4" aria-hidden /> Sign out
          </Button>
        </MobileDrawerFooter>
      </MobileDrawer>

      <div className="flex flex-1 flex-col h-screen h-[100svh] overflow-hidden lg:h-auto lg:overflow-visible">
        <header className="flex h-16 sm:h-20 items-center justify-between border-b border-slate-200 bg-white/80 dark:border-slate-800 dark:bg-slate-900/80 backdrop-blur-2xl px-4 sm:px-6 shrink-0 z-50 sticky top-0">
          <div className="flex items-center gap-3 sm:gap-4">
            <button
              className="lg:hidden p-2 text-slate-600 bg-slate-100 rounded-lg active:scale-95 transition-all outline-none focus:ring-2 focus:ring-primary-500"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open menu"
              aria-expanded={mobileMenuOpen}
              aria-controls="app-mobile-drawer"
            >
              <Menu className="h-5 w-5 sm:h-6 sm:w-6" />
            </button>
            <div className="flex items-center gap-2">
              <div className="hidden lg:block">
                <p className="text-[9px] uppercase tracking-[0.3em] text-slate-400 font-bold mb-0.5">Application</p>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-black text-slate-900 dark:text-slate-100">JobHuntin Agent</p>
                  <Badge variant="outline" size="sm" className="bg-slate-50 text-[10px] h-5 border-slate-200 px-1.5">v2.4.0</Badge>
                </div>
              </div>
              <div className="lg:hidden">
                <Logo iconOnly size="sm" />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            <LanguageSelector />
            <ThemeToggle className="text-slate-500 hover:text-slate-900 transition-colors" />
            <div className="hidden sm:flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-black text-slate-900 leading-tight">{user?.email?.split('@')[0] ?? "User"}</p>
                <p className="text-[9px] text-slate-400 uppercase font-black tracking-widest">Account Live</p>
              </div>
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200 text-primary-600 font-black shadow-sm group-hover:shadow-md transition-shadow">
                {user?.email?.slice(0, 1).toUpperCase() ?? "U"}
              </div>
            </div>
            <div className="sm:hidden grid h-9 w-9 place-items-center rounded-lg bg-slate-100 border border-slate-200 text-primary-600 font-black">
              {user?.email?.slice(0, 1).toUpperCase() ?? "U"}
            </div>
          </div>
        </header>
        <main id="main-content" className="flex-1 overflow-y-auto bg-slate-50/30 dark:bg-slate-950/30 pb-24 sm:pb-8 relative">
          <AnimatePresence mode="wait">
            <PageTransition key={location.pathname} className="h-full">
              <Outlet />
            </PageTransition>
          </AnimatePresence>
        </main>

        {/* Mobile bottom navigation: 4 main + More (opens full menu) */}
        <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl px-2 pb-safe-area shadow-[0_-8px_24px_rgba(15,23,42,0.06)]" aria-label="Mobile navigation">
          <div className="grid grid-cols-5 gap-1 pt-2 pb-5">
            {visibleNavItems.slice(0, 4).map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.to);
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={closeMobile}
                  className={({ isActive }) =>
                    cn(
                      "flex flex-col items-center justify-center rounded-xl px-2 py-2 transition-all min-h-[56px] active:scale-95 relative",
                      isActive ? "text-primary-700 font-bold" : "text-slate-500 hover:text-slate-900"
                    )
                  }
                  aria-label={item.label}
                >
                  <Icon className={cn("h-6 w-6 mb-1.5 transition-transform", isActive && "scale-110")} aria-hidden />
                  <span className="text-[11px] tracking-tight font-medium">{item.label}</span>
                  {isActive && <span className="absolute bottom-1.5 w-1 h-1 rounded-full bg-primary-600" />}
                </NavLink>
              );
            })}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              className={cn(
                "relative flex flex-col items-center justify-center rounded-xl px-2 py-2 transition-all min-h-[56px] active:scale-95",
                visibleNavItems.slice(4).some((i) => location.pathname.startsWith(i.to))
                  ? "text-primary-700 font-bold"
                  : "text-slate-500 hover:text-slate-900"
              )}
              aria-label="More menu"
              aria-expanded={mobileMenuOpen}
            >
              <MoreHorizontal className="h-6 w-6 mb-1.5" aria-hidden />
              <span className="text-[11px] tracking-tight font-medium">More</span>
              <span className="absolute top-1 right-2 flex h-5 min-w-[20px] items-center justify-center rounded-full bg-primary-600 text-[10px] font-black text-white px-1.5 border-2 border-white" aria-hidden>
                {visibleNavItems.slice(4).length}
              </span>
            </button>
          </div>
        </nav>
      </div>
    </div>
  );
}
