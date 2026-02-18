import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { MarketingNavbar } from "../components/marketing/MarketingNavbar";
import { MarketingFooter } from "../components/marketing/MarketingFooter";
import { PageTransition } from "../components/navigation/PageTransition";

export default function MarketingLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-white font-sans text-gray-900 selection:bg-purple-600/10 selection:text-gray-900 flex flex-col">
      <MarketingNavbar />
      <main className="flex-1 pt-[72px]">
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
