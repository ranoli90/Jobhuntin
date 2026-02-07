import { Link, Outlet } from "react-router-dom";
import { Button } from "../components/ui/Button";

const links = [
  { label: "How", href: "#how" },
  { label: "Proof", href: "#proof" },
  { label: "Pricing", href: "#pricing" },
  { label: "Login", href: "/app/dashboard" },
];

export default function MarketingLayout() {
  return (
    <div className="min-h-screen bg-brand-shell text-brand-ink">
      <header className="sticky top-0 z-20 backdrop-blur bg-brand-shell/90 border-b border-white/60">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <Link to="/" className="flex items-center gap-3 text-xl font-semibold">
            <div className="h-11 w-11 rounded-2xl bg-brand-sunrise text-white grid place-items-center shadow-pill">
              Sk
            </div>
            <div>
              <span className="font-display text-2xl leading-none">Skedaddle</span>
              <p className="text-xs uppercase tracking-[0.35em] text-brand-ink/70">chase the yes</p>
            </div>
          </Link>
          <div className="hidden items-center gap-6 text-sm font-medium md:flex">
            {links.map((link) =>
              link.href.startsWith("#") ? (
                <a key={link.label} href={link.href} className="text-brand-ink/70 hover:text-brand-ink">
                  {link.label}
                </a>
              ) : (
                <Link key={link.label} to={link.href} className="text-brand-ink/70 hover:text-brand-ink">
                  {link.label}
                </Link>
              ),
            )}
            <Button variant="primary" asChild>
              <Link to="/app/dashboard">Start free</Link>
            </Button>
          </div>
          <div className="md:hidden">
            <Button variant="ghost" size="sm">
              Menu
            </Button>
          </div>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="border-t border-white/70 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-8 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="font-display text-xl">Skedaddle</p>
            <p className="text-sm text-brand-ink/70">© {new Date().getFullYear()} Skedaddle. All rights reserved.</p>
          </div>
          <div className="flex gap-5 text-sm text-brand-ink/70">
            <a href="/" className="hover:text-brand-ink">
              Company
            </a>
            <a href="#" className="hover:text-brand-ink">
              Privacy
            </a>
            <a href="#" className="hover:text-brand-ink">
              Terms
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
