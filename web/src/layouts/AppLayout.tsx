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
import { cn } from "../lib/utils";
import {
  Menu,
  LayoutDashboard,
  Briefcase,
  FileText,
  HelpCircle,
  Users,
  CreditCard,
  Settings,
  LogOut,
} from "lucide-react";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/app/dashboard", icon: LayoutDashboard },
  { label: "Jobs", to: "/app/jobs", icon: Briefcase },
  { label: "Applications", to: "/app/applications", icon: FileText },
  { label: "HOLDs", to: "/app/holds", icon: HelpCircle },
  { label: "Team", to: "/app/team", icon: Users },
  { label: "Billing", to: "/app/billing", icon: CreditCard },
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
      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition-colors",
      isActive
        ? "bg-primary-50 text-primary-700"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
    );

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white md:flex">
        <div className="border-b border-slate-200 px-6 py-5">
          <Link to="/app/dashboard" className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 text-white font-semibold grid place-items-center">
              JH
            </div>
            <div>
              <p className="text-lg font-semibold">JobHuntin</p>
              <p className="text-xs text-slate-500">Intelligence console</p>
            </div>
          </Link>
        </div>
        <nav className="flex-1 space-y-1 px-4 py-6">
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
        <div className="border-t border-slate-200 px-4 py-5">
          <div className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 text-white font-semibold grid place-items-center">
              {user?.email?.slice(0, 2).toUpperCase() ?? "JH"}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium truncate">{user?.email ?? "hello@jobhuntin.com"}</p>
              <Badge variant="outline" size="sm" className="mt-1">
                {plan ?? "Free"}
              </Badge>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="mt-3 w-full justify-start text-slate-600"
            onClick={signOut}
          >
            <LogOut className="mr-2 h-4 w-4" /> Sign out
          </Button>
        </div>
      </aside>

      {/* Universal Mobile Drawer */}
      <MobileDrawer isOpen={mobileMenuOpen} onClose={closeMobile}>
        <MobileDrawerHeader onClose={closeMobile}>
          <Link to="/app/dashboard" className="flex items-center gap-3" onClick={closeMobile}>
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 text-white font-semibold grid place-items-center">
              JH
            </div>
            <span className="text-lg font-semibold">JobHuntin</span>
          </Link>
        </MobileDrawerHeader>
        
        <MobileDrawerBody>
          <nav className="space-y-1">
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
            className="w-full justify-start"
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
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white px-4 py-3 shrink-0">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Workspace</p>
              <p className="text-sm font-semibold text-slate-900">Command Center</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="primary" size="sm">
              {plan ?? "Free"}
            </Badge>
            <div className="hidden items-center gap-3 md:flex">
              <div className="text-right">
                <p className="text-sm font-semibold">{user?.email ?? "hello@jobhuntin.com"}</p>
                <p className="text-xs text-slate-500">Account owner</p>
              </div>
              <div className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-primary-500 to-primary-600 text-white font-semibold">
                {user?.email?.slice(0, 2).toUpperCase() ?? "JH"}
              </div>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto px-4 py-6 lg:px-8 lg:py-8 bg-slate-50">
          <AnimatePresence mode="wait">
             <PageTransition key={location.pathname} className="h-full">
                <Outlet />
             </PageTransition>
          </AnimatePresence>
        </main>
        <ToastShelf />
      </div>
    </div>
  );
}
