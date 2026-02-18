import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { MarketingNavbar } from "../components/marketing/MarketingNavbar";
import { MarketingFooter } from "../components/marketing/MarketingFooter";
import { PageTransition } from "../components/navigation/PageTransition";

export default function MarketingLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-stone-50 font-sans text-stone-900 selection:bg-stone-900/10 selection:text-stone-900 flex flex-col">
      <MarketingNavbar />
      <main className="flex-1 pt-20 md:pt-24">
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
