import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useBilling } from "../hooks/useBilling";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ToastShelf } from "../components/ui/ToastShelf";
import { cn } from "../lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/app/dashboard" },
  { label: "Jobs", to: "/app/jobs" },
  { label: "Applications", to: "/app/applications" },
  { label: "HOLDs", to: "/app/holds" },
  { label: "Team", to: "/app/team" },
  { label: "Billing", to: "/app/billing" },
];

export default function AppLayout() {
  const { user, signOut } = useAuth();
  const { plan } = useBilling();

  return (
    <div className="flex min-h-screen bg-brand-shell text-brand-ink">
      <aside className="hidden w-64 flex-col border-r border-white/70 bg-white/90 px-6 py-8 md:flex">
        <div>
          <p className="font-display text-2xl">Skedaddle</p>
          <p className="text-xs uppercase tracking-[0.4em] text-brand-ink/60">app</p>
        </div>
        <nav className="mt-8 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center justify-between rounded-2xl px-4 py-2.5 text-sm font-semibold transition-all",
                  isActive ? "bg-brand-shell text-brand-ink" : "text-brand-ink/70 hover:bg-brand-shell/70",
                )
              }
            >
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
      <div className="flex flex-1 flex-col">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/70 bg-white/80 px-6 py-4 backdrop-blur">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-brand-ink/70">Plan</p>
            <Badge variant="lagoon">{plan}</Badge>
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
