import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { MarketingNavbar } from "../components/marketing/MarketingNavbar";
import { MarketingFooter } from "../components/marketing/MarketingFooter";
import { PageTransition } from "../components/navigation/PageTransition";

export default function MarketingLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-white font-sans text-gray-900 selection:bg-purple-600/10 selection:text-gray-900 flex flex-col">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-white focus:text-brand-ink focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-brand-accent">
        Skip to content
      </a>
      <MarketingNavbar />
      <main id="main-content" className="flex-1 pt-[72px]">
        <AnimatePresence mode="wait">
          <PageTransition key={location.pathname} className="h-full">
            <Outlet />
          </PageTransition>
        </AnimatePresence>
      </main>
      <MarketingFooter />
    </div>
  );
}
