import { useEffect, useState } from "react";
import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import { supabase } from "./lib/supabase";
import type { Session, User } from "@supabase/supabase-js";
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

// SECURITY: Admin role check - only allow users with admin privileges
interface AdminUser {
  id: string;
  email: string;
  is_admin: boolean;
  roles: string[];
}

async function checkAdminAccess(user: User): Promise<boolean> {
  try {
    // Check if user has admin role via the API
    const { data, error } = await supabase
      .from('profiles')
      .select('role, is_system_admin')
      .eq('user_id', user.id)
      .single();
    
    if (error) {
      console.error('Error checking admin status:', error);
      return false;
    }
    
    // Check for system admin flag or admin role
    const isAdmin = data?.is_system_admin === true || 
                    data?.role === 'admin' ||
                    data?.role === 'ADMIN';
    
    return isAdmin;
  } catch (err) {
    console.error('Failed to verify admin access:', err);
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

function Sidebar() {
  const loc = useLocation();
  let lastSection = "";

  return (
    <aside className="w-56 bg-card border-r border-border min-h-screen p-4 flex flex-col gap-0.5">
      <div className="text-xl font-bold text-primary mb-6 px-2">Sorce Admin</div>
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
              <span>{l.icon}</span> {l.label}
            </Link>
          </div>
        );
      })}
      <div className="flex-1" />
      <button
        onClick={() => supabase.auth.signOut()}
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
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_ev, s) => setSession(s));
    return () => listener.subscription.unsubscribe();
  }, []);

  // SECURITY: Check admin access when session changes
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

  if (loading || checkingAdmin) {
    return (
      <div className="flex items-center justify-center h-screen text-muted-foreground">
        Verifying access...
      </div>
    );
  }
  
  if (!session) return <LoginPage />;
  
  // SECURITY: Block non-admin users from accessing the admin dashboard
  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-destructive mb-4">Access Denied</h1>
          <p className="text-muted-foreground mb-4">
            You do not have admin privileges to access this dashboard.
          </p>
          <button
            onClick={() => supabase.auth.signOut()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
          >
            Sign Out
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
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
