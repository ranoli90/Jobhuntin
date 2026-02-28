import { useState } from "react";
import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useBilling } from "../hooks/useBilling";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ToastShelf } from "../components/ui/ToastShelf";
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

const NAV_ITEMS = [
  { label: "Dashboard", to: "/app/dashboard", icon: LayoutDashboard },
  { label: "Jobs", to: "/app/jobs", icon: Briefcase },
  { label: "Applications", to: "/app/applications", icon: FileText },
  { label: "HOLDs", to: "/app/holds", icon: HelpCircle },
  { label: "Team", to: "/app/team", icon: Users },
  { label: "Billing", to: "/app/billing", icon: CreditCard },
  { label: "Sources", to: "/app/admin/sources", icon: Globe },
  { label: "Settings", to: "/app/settings", icon: Settings },
];

export default function AppLayout() {
  const { user, signOut } = useAuth();
  const { plan } = useBilling();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const closeMobile = () => setMobileMenuOpen(false);
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-bold transition-all active:scale-[0.98]",
      isActive
        ? "bg-primary-50 text-primary-700 shadow-sm ring-1 ring-primary-100"
        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
    );

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-white focus:text-brand-ink focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-brand-accent">
        Skip to content
      </a>
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
        <div className="border-b border-slate-200 px-8 py-6">
          <Logo to="/app/dashboard" size="md" />
          <p className="text-[10px] text-slate-400 mt-2 font-black uppercase tracking-[0.2em] ml-1">Application Console</p>
        </div>
        <nav className="flex-1 space-y-1 px-4 py-8">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={navLinkClass}>
                <Icon className="h-4 w-4" />
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
            <LogOut className="mr-2 h-4 w-4" /> Sign out
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
            {NAV_ITEMS.map((item) => {
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
            <LogOut className="mr-2 h-4 w-4" /> Sign out
          </Button>
        </MobileDrawerFooter>
      </MobileDrawer>

      <div className="flex flex-1 flex-col h-screen overflow-hidden">
        <header className="flex h-20 items-center justify-between border-b border-slate-200 bg-white/90 backdrop-blur-xl px-6 shrink-0 z-50 sticky top-0">
          <div className="flex items-center gap-4">
            <button
              className="lg:hidden p-2.5 -ml-2 text-slate-600 bg-slate-100 rounded-xl active:scale-90 transition-all"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open menu"
              aria-expanded={mobileMenuOpen}
              aria-controls="app-mobile-drawer"
            >
              <Menu className="h-6 w-6" />
            </button>
            <div className="flex items-center gap-2">
              <div className="hidden lg:block">
                <p className="text-[10px] uppercase tracking-[0.35em] text-slate-400 font-black">Dashboard</p>
                <p className="text-sm font-black text-slate-900">Application Console</p>
              </div>
              <div className="lg:hidden">
                <Logo iconOnly size="sm" />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant="primary" size="sm" className="font-black px-3">
              {plan ?? "Free"}
            </Badge>
            <div className="flex items-center gap-3">
              <div className="hidden text-right md:block">
                <p className="text-sm font-black text-slate-900">{user?.email?.split('@')[0] ?? "User"}</p>
                <p className="text-[10px] text-slate-400 uppercase font-black tracking-widest">Account Active</p>
              </div>
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-slate-50 border border-slate-200 text-primary-600 font-black shadow-sm">
                {user?.email?.slice(0, 1).toUpperCase() ?? "U"}
              </div>
            </div>
          </div>
        </header>
        <main id="main-content" className="flex-1 overflow-y-auto bg-slate-50/50 pb-20">
          <AnimatePresence mode="wait">
            <PageTransition key={location.pathname} className="h-full">
              <Outlet />
            </PageTransition>
          </AnimatePresence>
        </main>

        {/* Mobile bottom navigation: 4 main + More (opens full menu) */}
        <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-white/95 backdrop-blur-xl px-2 py-2 shadow-[0_-8px_24px_rgba(15,23,42,0.08)]" aria-label="Main navigation">
          <div className="grid grid-cols-5 gap-1">
            {NAV_ITEMS.slice(0, 4).map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.to);
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={closeMobile}
                  className={cn(
                    "flex flex-col items-center justify-center rounded-xl px-1 py-3 text-[10px] font-bold transition-all min-h-[44px]",
                    isActive ? "bg-primary-50 text-primary-700 ring-1 ring-primary-100" : "text-slate-500 hover:text-slate-900"
                  )}
                  aria-label={item.label}
                >
                  <Icon className="h-5 w-5" aria-hidden />
                  <span className="mt-1 leading-none">{item.label}</span>
                </NavLink>
              );
            })}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              className={cn(
                "flex flex-col items-center justify-center rounded-xl px-1 py-3 text-[10px] font-bold transition-all min-h-[44px]",
                NAV_ITEMS.slice(4).some((i) => location.pathname.startsWith(i.to))
                  ? "bg-primary-50 text-primary-700 ring-1 ring-primary-100"
                  : "text-slate-500 hover:text-slate-900"
              )}
              aria-label="More menu (Team, Billing, Sources, Settings)"
            >
              <MoreHorizontal className="h-5 w-5" aria-hidden />
              <span className="mt-1 leading-none">More</span>
            </button>
          </div>
        </nav>
        <ToastShelf />
      </div>
    </div>
  );
}
