import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { MarketingNavbar } from "../components/marketing/MarketingNavbar";
import { MarketingFooter } from "../components/marketing/MarketingFooter";
import { PageTransition } from "../components/navigation/PageTransition";
import { HelpButton } from "../components/HelpButton";
import { cn } from "../lib/utils";

export default function MarketingLayout() {
  const location = useLocation();
  const isLoginPage = location.pathname === "/login";
  const [, forceLocaleUpdate] = useState(0);

  useEffect(() => {
    const handler = () => forceLocaleUpdate((n) => n + 1);
    window.addEventListener("localechange", handler);
    return () => window.removeEventListener("localechange", handler);
  }, []);

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 font-sans text-gray-900 dark:text-slate-100 flex flex-col antialiased">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-white focus:text-black focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-black dark:focus:bg-slate-900 dark:focus:text-slate-100 dark:focus:ring-white"
      >
        Skip to content
      </a>
      <MarketingNavbar />
      <main
        id="main-content"
        className={cn(
          "flex-1",
          (location.pathname !== "/" || isLoginPage) && "pt-16 sm:pt-20",
        )}
      >
        <AnimatePresence mode="wait">
          <PageTransition key={location.pathname} className="h-full">
            <Outlet />
          </PageTransition>
        </AnimatePresence>
      </main>
      <MarketingFooter />
      <HelpButton />
    </div>
  );
}
