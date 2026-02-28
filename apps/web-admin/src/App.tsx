import { useEffect, useState } from "react";
import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import Dashboard from "./pages/Dashboard";
import MembersPage from "./pages/MembersPage";
import UsagePage from "./pages/UsagePage";
import InvitesPage from "./pages/InvitesPage";
import LoginPage from "./pages/LoginPage";
import EnterpriseDashboard from "./enterprise/EnterpriseDashboard";
import SSOConfigPage from "./enterprise/SSOConfigPage";
import AuditLogPage from "./compliance/AuditLogPage";
import BulkCampaignsPage from "./bulk-ops/BulkCampaignsPage";
import MarketplaceBrowse from "./marketplace/MarketplaceBrowse";
import AuthorDashboard from "./marketplace/AuthorDashboard";
import SubmitBlueprint from "./marketplace/SubmitBlueprint";
import ApiKeysPage from "./developer-portal/ApiKeysPage";
import WebhooksPage from "./developer-portal/WebhooksPage";

const API_BASE = import.meta.env.VITE_API_URL || "";

interface User {
  id: string;
  email: string;
}

interface Session {
  user: User;
}

async function getSession(): Promise<Session | null> {
  const token = sessionStorage.getItem("auth_token");
  if (!token) return null;
  try {
    const resp = await fetch(`${API_BASE}/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resp.ok) {
      sessionStorage.removeItem("auth_token");
      return null;
    }
    const user = await resp.json();
    return { user };
  } catch {
    sessionStorage.removeItem("auth_token");
    return null;
  }
}

async function checkAdminAccess(user: User): Promise<boolean> {
  try {
    const token = sessionStorage.getItem("auth_token");
    if (!token) return false;
    const resp = await fetch(`${API_BASE}/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    return data?.is_system_admin === true || data?.role === "admin" || data?.role === "ADMIN";
  } catch (err) {
    console.error("Failed to verify admin access:", err);
    return false;
  }
}

interface NavLink { to: string; label: string; icon: string; section?: string }

const NAV_LINKS: NavLink[] = [
  { to: "/", label: "Dashboard", icon: "📊" },
  { to: "/monitoring", label: "Monitoring", icon: "📡", section: "Operations" },
  { to: "/members", label: "Members", icon: "👥" },
  { to: "/usage", label: "Usage & Billing", icon: "📈" },
  { to: "/invites", label: "Invites", icon: "✉️" },
  { to: "/enterprise", label: "Enterprise", icon: "🏢", section: "Enterprise" },
  { to: "/sso", label: "SSO Config", icon: "🔐", section: "Enterprise" },
  { to: "/audit-log", label: "Audit Log", icon: "📋", section: "Compliance" },
  { to: "/bulk-campaigns", label: "Bulk Campaigns", icon: "🚀", section: "Operations" },
  { to: "/marketplace", label: "Marketplace", icon: "🛒", section: "Marketplace" },
  { to: "/marketplace/submit", label: "Submit Blueprint", icon: "📤", section: "Marketplace" },
  { to: "/marketplace/author", label: "Author Dashboard", icon: "💰", section: "Marketplace" },
  { to: "/developer/api-keys", label: "API Keys", icon: "🔑", section: "Developer" },
  { to: "/developer/webhooks", label: "Webhooks", icon: "🔔", section: "Developer" },
];

function Sidebar({ open, onClose }: { open?: boolean; onClose?: () => void }) {
  const loc = useLocation();
  let lastSection = "";

  const handleSignOut = () => {
    sessionStorage.removeItem("auth_token");
    window.location.reload();
  };

  return (
    <aside role="navigation" aria-label="Admin navigation" className={`bg-card border-r border-border min-h-screen p-4 flex flex-col gap-0.5 ${open ? 'fixed inset-0 z-50 w-64' : 'hidden'} md:relative md:block md:w-56`}>
      <div className="flex items-center justify-between mb-6 px-2">
        <div className="text-xl font-bold text-primary">Sorce Admin</div>
        {onClose && (
          <button className="md:hidden p-1 text-muted-foreground hover:text-foreground" onClick={onClose} aria-label="Close menu">
            ✕
          </button>
        )}
      </div>
      {NAV_LINKS.map((l) => {
        const sectionHeader = l.section && l.section !== lastSection;
        if (l.section) lastSection = l.section;
        return (
          <div key={l.to}>
            {sectionHeader && (
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-semibold mt-4 mb-1 px-3">
                {l.section}
              </div>
            )}
            <Link
              to={l.to}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                loc.pathname === l.to
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <span aria-hidden="true">{l.icon}</span> {l.label}
            </Link>
          </div>
        );
      })}
      <div className="flex-1" />
      <button
        onClick={handleSignOut}
        className="px-3 py-2 text-sm text-muted-foreground hover:text-destructive transition-colors rounded-md"
      >
        Sign Out
      </button>
    </aside>
  );
}

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [checkingAdmin, setCheckingAdmin] = useState(true);

  useEffect(() => {
    getSession().then((s) => {
      setSession(s);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (session?.user) {
      setCheckingAdmin(true);
      checkAdminAccess(session.user).then((hasAccess) => {
        setIsAdmin(hasAccess);
        setCheckingAdmin(false);
      });
    } else {
      setIsAdmin(false);
      setCheckingAdmin(false);
    }
  }, [session]);

  const handleSignOut = () => {
    sessionStorage.removeItem("auth_token");
    window.location.reload();
  };

  if (loading || checkingAdmin) {
    return (
      <div className="flex items-center justify-center h-screen text-muted-foreground">
        Verifying access...
      </div>
    );
  }
  
  if (!session) return <LoginPage />;
  
  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-destructive mb-4">Access Denied</h1>
          <p className="text-muted-foreground mb-4">
            You do not have admin privileges to access this dashboard.
          </p>
          <button
            onClick={handleSignOut}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
          >
            Sign Out
          </button>
        </div>
      </div>
    );
  }

  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <button
        className="md:hidden fixed top-4 left-4 z-40 p-2 bg-card border border-border rounded-md shadow-sm"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar"
      >
        <span className="text-lg">☰</span>
      </button>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="flex-1 p-6 overflow-auto">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/monitoring" element={<Dashboard />} />
          <Route path="/members" element={<MembersPage />} />
          <Route path="/usage" element={<UsagePage />} />
          <Route path="/invites" element={<InvitesPage />} />
          <Route path="/enterprise" element={<EnterpriseDashboard />} />
          <Route path="/sso" element={<SSOConfigPage />} />
          <Route path="/audit-log" element={<AuditLogPage />} />
          <Route path="/bulk-campaigns" element={<BulkCampaignsPage />} />
          <Route path="/marketplace" element={<MarketplaceBrowse />} />
          <Route path="/marketplace/submit" element={<SubmitBlueprint />} />
          <Route path="/marketplace/author" element={<AuthorDashboard />} />
          <Route path="/developer/api-keys" element={<ApiKeysPage />} />
          <Route path="/developer/webhooks" element={<WebhooksPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}
