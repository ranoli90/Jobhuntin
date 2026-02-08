import { Link, Outlet } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { ToastShelf } from "../components/ui/ToastShelf";
import { Menu, X } from "lucide-react";
import { useState } from "react";

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how" },
  { label: "Testimonials", href: "#testimonials" },
  { label: "FAQ", href: "#faq" },
];

export default function MarketingLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white text-slate-900">
      {/* Professional Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200">
        <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center text-white font-bold text-lg shadow-sm">
                JH
              </div>
              <span className="font-semibold text-xl tracking-tight">JobHuntin</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </div>

            {/* Desktop CTA */}
            <div className="hidden md:flex items-center gap-4">
              <Link
                to="/login"
                className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                Sign in
              </Link>
              <Button size="sm" asChild>
                <Link to="/login">Get started</Link>
              </Button>
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-slate-200 py-4">
              <div className="flex flex-col gap-2">
                {navLinks.map((link) => (
                  <a
                    key={link.label}
                    href={link.href}
                    className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {link.label}
                  </a>
                ))}
                <hr className="my-2 border-slate-200" />
                <Link
                  to="/login"
                  className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Sign in
                </Link>
                <Button size="sm" className="mx-3" asChild>
                  <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                    Get started
                  </Link>
                </Button>
              </div>
            </div>
          )}
        </nav>
      </header>

      {/* Main Content */}
      <main>
        <Outlet />
      </main>

      {/* Professional Footer */}
      <footer className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid gap-8 md:grid-cols-4">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center text-white font-bold text-sm">
                  JH
                </div>
                <span className="font-semibold text-lg">JobHuntin</span>
              </div>
              <p className="text-sm text-slate-600 max-w-sm">
                AI-powered job application automation. Land your dream job faster with intelligent matching and automated applications.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="font-semibold text-sm mb-4">Product</h4>
              <ul className="space-y-2">
                <li><a href="#features" className="text-sm text-slate-600 hover:text-slate-900">Features</a></li>
                <li><a href="#how" className="text-sm text-slate-600 hover:text-slate-900">How it works</a></li>
                <li><a href="#" className="text-sm text-slate-600 hover:text-slate-900">Pricing</a></li>
                <li><a href="#" className="text-sm text-slate-600 hover:text-slate-900">API</a></li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="font-semibold text-sm mb-4">Company</h4>
              <ul className="space-y-2">
                <li><a href="#" className="text-sm text-slate-600 hover:text-slate-900">About</a></li>
                <li><a href="#" className="text-sm text-slate-600 hover:text-slate-900">Blog</a></li>
                <li><a href="#" className="text-sm text-slate-600 hover:text-slate-900">Careers</a></li>
                <li><a href="#" className="text-sm text-slate-600 hover:text-slate-900">Contact</a></li>
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="mt-12 pt-8 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-sm text-slate-500">
              © {new Date().getFullYear()} JobHuntin. All rights reserved.
            </p>
            <div className="flex gap-6">
              <Link to="/privacy" className="text-sm text-slate-500 hover:text-slate-700">Privacy Policy</Link>
              <Link to="/terms" className="text-sm text-slate-500 hover:text-slate-700">Terms of Service</Link>
            </div>
          </div>
        </div>
      </footer>
      <ToastShelf />
    </div>
  );
}
