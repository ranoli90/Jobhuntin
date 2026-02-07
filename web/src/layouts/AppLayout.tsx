import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useBilling } from "../hooks/useBilling";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ToastShelf } from "../components/ui/ToastShelf";
import { cn } from "../lib/utils";
import { Menu, X } from "lucide-react";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/app/dashboard" },
  { label: "Jobs", to: "/app/jobs" },
  { label: "Applications", to: "/app/applications" },
  { label: "HOLDs", to: "/app/holds" },
  { label: "Team", to: "/app/team" },
  { label: "Billing", to: "/app/billing" },
  { label: "Settings", to: "/app/settings" },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const { plan } = useBilling();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const closeMobile = () => setMobileMenuOpen(false);
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center justify-between rounded-2xl px-4 py-2.5 text-sm font-semibold transition-all",
      isActive ? "bg-brand-shell text-brand-ink" : "text-brand-ink/70 hover:bg-brand-shell/70",
    );

  return (
    <div className="flex min-h-screen bg-brand-shell text-brand-ink">
      <aside className="hidden w-64 flex-col border-r border-white/70 bg-white/90 px-6 py-8 md:flex">
        <div>
          <p className="font-display text-2xl">Skedaddle</p>
          <p className="text-xs uppercase tracking-[0.4em] text-brand-ink/60">app</p>
        </div>
        <nav className="mt-8 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} className={navLinkClass}>
              {item.label}
              <span>→</span>
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto space-y-2 text-xs text-brand-ink/70">
          <Button variant="ghost" className="w-full justify-center" onClick={signOut}>
            Logout
          </Button>
          <p className="text-[11px]">support@skedaddle.com</p>
        </div>
      </aside>

      {/* Mobile menu overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={closeMobile}
          aria-hidden
        />
      )}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 flex-col border-r border-white/70 bg-white/90 px-6 py-8 shadow-xl transition-transform md:hidden",
          mobileMenuOpen ? "flex translate-x-0" : "flex -translate-x-full",
        )}
      >
        <div className="flex items-center justify-between">
          <p className="font-display text-2xl">Skedaddle</p>
          <Button variant="ghost" size="icon" onClick={closeMobile} aria-label="Close menu">
            <X className="h-5 w-5" />
          </Button>
        </div>
        <nav className="mt-8 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={navLinkClass}
              onClick={closeMobile}
            >
              {item.label}
              <span>→</span>
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto space-y-2 text-xs text-brand-ink/70">
          <Button variant="ghost" className="w-full justify-center" onClick={() => { signOut(); closeMobile(); }}>
            Logout
          </Button>
        </div>
      </div>
      <div className="flex flex-1 flex-col">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/70 bg-white/80 px-6 py-4 backdrop-blur">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMobileMenuOpen(true)} aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </Button>
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-brand-ink/70">Plan</p>
              <Badge variant="lagoon">{plan}</Badge>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-semibold">{user?.email ?? "hello@skedaddle.com"}</p>
              <p className="text-xs text-brand-ink/60">Account owner</p>
            </div>
            <div className="grid h-12 w-12 place-items-center rounded-full bg-brand-sunrise text-white font-semibold">
              {user?.email?.slice(0, 2).toUpperCase() ?? "SK"}
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto px-6 py-8">
          <Outlet />
        </main>
        <ToastShelf />
      </div>
    </div>
  );
}
