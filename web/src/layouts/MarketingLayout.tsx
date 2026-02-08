import { Outlet } from "react-router-dom";
import { MarketingNavbar } from "../components/marketing/MarketingNavbar";
import { MarketingFooter } from "../components/marketing/MarketingFooter";

export default function MarketingLayout() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <MarketingNavbar />
      <main>
        <Outlet />
      </main>
      <MarketingFooter />
    </div>
  );
}
