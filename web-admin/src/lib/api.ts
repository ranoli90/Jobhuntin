import { supabase } from "./supabase";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers = await authHeaders();
  const opts: RequestInit = { method, headers };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(`${API_BASE}${path}`, opts);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API ${resp.status}: ${text}`);
  }
  return resp.json() as Promise<T>;
}

// ── Billing / Team ──────────────────────────────────────────
export const getTeamOverview = () => request<TeamOverview>("GET", "/billing/team");
export const getTeamMembers = () => request<TeamMember[]>("GET", "/billing/team/members");
export const getTeamInvites = () => request<TeamInvite[]>("GET", "/billing/team/invites");
export const getBillingStatus = () => request<BillingStatus>("GET", "/billing/status");
export const getBillingUsage = () => request<BillingUsage>("GET", "/billing/usage");
export const inviteMember = (email: string, role = "MEMBER") =>
  request<{ status: string; invite: TeamInvite }>("POST", "/billing/invite", { email, role });
export const removeMember = (userId: string) =>
  request<{ status: string }>("DELETE", `/billing/team/members/${userId}`);
export const addSeats = (newTotalSeats: number) =>
  request<{ status: string }>("POST", "/billing/add-seats", { new_total_seats: newTotalSeats });
export const createTeamCheckout = (seats: number, teamName: string) =>
  request<{ checkout_url: string }>("POST", "/billing/team-checkout", {
    seats, team_name: teamName,
    success_url: `${window.location.origin}/billing/success`,
    cancel_url: `${window.location.origin}/billing/cancel`,
  });
export const createPortal = () =>
  request<{ portal_url: string }>("POST", "/billing/portal");

// ── Enterprise Billing ──────────────────────────────────────
export const createEnterpriseCheckout = (seats: number, teamName: string, slaTier = "standard") =>
  request<{ checkout_url: string; session_id: string }>("POST", "/billing/enterprise-checkout", {
    seats, team_name: teamName, sla_tier: slaTier,
    success_url: `${window.location.origin}/billing/success`,
    cancel_url: `${window.location.origin}/billing/cancel`,
  });
export const getAuditLog = (limit = 50, offset = 0, action?: string) => {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (action) params.set("action", action);
  return request<AuditLogResponse>("GET", `/billing/audit-log?${params}`);
};

// ── Annual Billing ──────────────────────────────────────────
export const createAnnualCheckout = (plan: string, seats = 1, teamName = "") =>
  request<{ checkout_url: string; session_id: string }>("POST", "/billing/annual-checkout", {
    plan, seats, team_name: teamName,
    success_url: `${window.location.origin}/billing/success`,
    cancel_url: `${window.location.origin}/billing/cancel`,
  });
export const startEnterpriseSelfServe = (companyName: string, seats = 10, billingInterval = "monthly", customDomain = "") =>
  request<{ checkout_url: string; onboarding: any }>("POST", "/billing/enterprise-self-serve", {
    company_name: companyName, seats, billing_interval: billingInterval, custom_domain: customDomain,
  });
export const getOnboarding = () => request<any>("GET", "/billing/onboarding");

// ── Marketplace ─────────────────────────────────────────────
export const browseBlueprints = (params?: { category?: string; search?: string; sort?: string; limit?: number }) => {
  const p = new URLSearchParams();
  if (params?.category) p.set("category", params.category);
  if (params?.search) p.set("search", params.search);
  if (params?.sort) p.set("sort", params.sort);
  if (params?.limit) p.set("limit", String(params.limit));
  return request<{ blueprints: MarketplaceBlueprint[]; total: number }>("GET", `/marketplace/blueprints?${p}`);
};
export const getMarketplaceCategories = () => request<Array<{ category: string; count: number }>>("GET", "/marketplace/categories");
export const installBlueprint = (id: string, config = {}) =>
  request<{ status: string; installation: any }>("POST", `/marketplace/blueprints/${id}/install`, { config });
export const submitBlueprint = (data: SubmitBlueprintData) =>
  request<{ status: string; blueprint: any }>("POST", "/marketplace/blueprints/submit", data);
export const getAuthorBlueprints = () => request<AuthorBlueprint[]>("GET", "/marketplace/author/blueprints");
export const getAuthorEarnings = () => request<AuthorEarnings>("GET", "/marketplace/author/earnings");

// ── Dashboards ──────────────────────────────────────────────
export const getM3Dashboard = () => request<M3Dashboard>("GET", "/admin/m3-dashboard");
export const getM4Dashboard = () => request<M4Dashboard>("GET", "/admin/m4-dashboard");
export const refreshM4Views = () => request<{ status: string }>("POST", "/admin/m4-dashboard/refresh");
export const getAlerts = () => request<AlertsResponse>("GET", "/admin/alerts");
export const getM5Dashboard = () => request<any>("GET", "/admin/m5-dashboard");
export const refreshM5Views = () => request<{ status: string }>("POST", "/admin/m5-dashboard/refresh");
export const getInvestorMetrics = () => request<InvestorMetrics>("GET", "/investors/metrics");
export const runAlertingCycle = () => request<AlertingCycleResult>("POST", "/admin/alerting-cycle");

// ── Types ───────────────────────────────────────────────────
export interface TeamMember {
  user_id: string;
  role: string;
  email: string;
  name: string | null;
  apps_this_month: number;
  apps_total: number;
}

export interface TeamInvite {
  id: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
  expires_at: string;
  accepted_at: string | null;
}

export interface TeamOverview {
  tenant: {
    id: string;
    name: string;
    team_name: string | null;
    plan: string;
    seat_count: number;
    max_seats: number;
  };
  members: TeamMember[];
  member_count: number;
  pending_invites: number;
  total_apps_this_month: number;
  total_apps_all_time: number;
}

export interface BillingStatus {
  tenant_id: string;
  plan: string;
  provider: string | null;
  subscription_status: string;
  current_period_end: string | null;
}

export interface BillingUsage {
  tenant_id: string;
  plan: string;
  monthly_limit: number;
  monthly_used: number;
  monthly_remaining: number;
  concurrent_limit: number;
  concurrent_used: number;
  percentage_used: number;
}

export interface M3Dashboard {
  active_users: { mau: number; wau: number; dau: number };
  m1_targets: { pro_subscribers: number; mrr: number };
  total_applications: number;
  total_mrr: number;
  mrr_by_plan: Array<{ plan: string; tenant_count: number; plan_mrr: number }>;
  team_metrics: {
    total_teams: number;
    total_team_seats: number;
    team_mrr: number;
    teams_with_3_plus: number;
  };
  blueprint_performance: Array<{
    blueprint_key: string;
    total: number;
    succeeded: number;
    success_rate: number;
  }>;
  plan_distribution: Array<{ plan: string; tenant_count: number; user_count: number }>;
  churn_risk: Array<{ tenant_id: string; name: string; days_inactive: number }>;
}

export interface M4Dashboard extends M3Dashboard {
  mrr_cohorts: Array<{ cohort_month: string; tenants: number; paying: number; cohort_mrr: number }>;
  expansion_revenue: Array<{ month: string; upgrades: number; downgrades: number; seat_expansions: number }>;
  churn_prediction: Array<{
    tenant_id: string; name: string; plan: string;
    mrr_at_risk: number; days_since_last_activity: number;
    churn_risk_level: string;
  }>;
  churn_summary: { high_risk: number; medium_risk: number; low_risk: number; total_mrr_at_risk: number };
  nrr_monthly: Array<{ month: string; ending_mrr: number; starting_mrr: number | null; nrr_pct: number | null }>;
  enterprise_pipeline: Array<{
    tenant_id: string; name: string; plan: string;
    seat_count: number; sla_tier: string | null;
    pipeline_stage: string; contract_mrr: number;
  }>;
  ltv_cac: {
    arpu: number; paying_tenants: number; total_mrr: number;
    monthly_churn_rate: number; estimated_ltv: number;
    estimated_cac: number; ltv_cac_ratio: number;
  };
  m4_targets: {
    mau_target: number; mau_current: number;
    mrr_target: number; mrr_current: number;
    subscribers_target: number; subscribers_current: number;
    team_accounts_target: number; team_accounts_current: number;
    enterprise_pilots_target: number; enterprise_pilots_current: number;
    nrr_target: number; nrr_current: number;
  };
}

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource: string;
  resource_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogResponse {
  logs: AuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface AlertItem {
  name: string;
  level: string;
  message: string;
  value: unknown;
}

export interface AlertsResponse {
  alerts: AlertItem[];
  total: number;
}

// ── M5 Types ────────────────────────────────────────────────

export interface MarketplaceBlueprint {
  id: string; slug: string; name: string; description: string;
  category: string; author_name: string; version: string;
  install_count: number; rating_avg: number; rating_count: number;
  price_cents: number; is_featured: boolean; icon_url: string | null;
  published_at: string | null;
}

export interface SubmitBlueprintData {
  name: string; slug: string; description: string;
  long_description?: string; category?: string;
  version?: string; price_cents?: number;
  source_code?: Record<string, unknown>;
  config_schema?: Record<string, unknown>;
}

export interface AuthorBlueprint {
  id: string; slug: string; name: string; version: string;
  approval_status: string; install_count: number;
  rating_avg: number; price_cents: number; created_at: string;
}

export interface AuthorEarnings {
  total_earned_cents: number; pending_cents: number;
  paid_out_cents: number; total_payouts: number;
  total_installs: number;
}

export interface InvestorMetrics {
  company: string;
  period: string;
  generated_at: string;
  financials: {
    mrr: number; arr: number; mrr_growth_mom_pct: number;
    gross_margin_pct: number; estimated_cogs: number;
    net_revenue_retention_pct: number | null;
  };
  customers: {
    total_tenants: number; paying_subscribers: number;
    pro: number; team: number; enterprise: number;
  };
  unit_economics: {
    arpu: number; ltv: number; cac: number;
    ltv_cac_ratio: number; monthly_churn_pct: number;
    payback_months: number;
  };
  product: {
    agent_success_rate_pct: number;
    total_applications_processed: number;
    marketplace_blueprints: number;
    marketplace_platform_revenue: number;
  };
  mrr_history: Array<{ month: string; mrr: number }>;
}

export interface AlertingCycleResult {
  alerts: AlertItem[];
  rollback: { action: string; reason: string } | null;
  graduated_experiments: Array<{
    experiment: string; winner: string;
    winner_rate: number; delta: number;
  }>;
  dispatched: number;
}

// ── M6 Methods ──────────────────────────────────────────────

export const getM6Dashboard = () => request<any>("GET", "/admin/m6-platform");
export const refreshM6Views = () => request<{ status: string }>("POST", "/admin/m6-platform/refresh");
export const getFullInvestorMetrics = () => request<FullInvestorMetrics>("GET", "/investors/full-metrics");
export const runRenewalCycle = () => request<RenewalCycleResult>("POST", "/admin/renewal-cycle");

// Developer Portal
export const listApiKeys = () => request<ApiKeyItem[]>("GET", "/developer/api-keys");
export const createApiKey = (name: string, tier = "free") =>
  request<ApiKeyItem & { raw_key: string }>("POST", "/developer/api-keys", { name, tier });
export const revokeApiKey = (id: string) => request<{ status: string }>("DELETE", `/developer/api-keys/${id}`);
export const listWebhooks = () => request<WebhookItem[]>("GET", "/developer/webhooks");
export const createWebhook = (url: string, events: string[]) =>
  request<WebhookItem & { secret: string }>("POST", "/developer/webhooks", { url, events });
export const deleteWebhook = (id: string) => request<{ status: string }>("DELETE", `/developer/webhooks/${id}`);
export const getDevUsage = () => request<DevUsageDashboard>("GET", "/developer/usage");

// University Partners
export const createUniversityPartner = (data: { name: string; domain: string; bundle_id?: string; revenue_share_pct?: number }) =>
  request<any>("POST", "/partners/university/partners", data);
export const listUniversityPartners = () => request<any[]>("GET", "/partners/university/partners");
export const getUniversityRoi = (partnerId: string) =>
  request<UniversityRoiReport>("GET", `/partners/university/roi-report?partner_id=${partnerId}`);

// ── M6 Types ────────────────────────────────────────────────

export interface ApiKeyItem {
  id: string; name: string; key_prefix: string; tier: string;
  rate_limit_rpm: number; monthly_quota: number; calls_this_month: number;
  is_active: boolean; last_used_at: string | null; created_at: string;
}

export interface WebhookItem {
  id: string; url: string; events: string[]; is_active: boolean;
  failure_count: number; last_success_at: string | null; created_at: string;
}

export interface DevUsageDashboard {
  keys: ApiKeyItem[];
  daily_usage: Array<{ day: string; calls: number; avg_latency: number }>;
  by_endpoint: Array<{ endpoint: string; method: string; calls: number; avg_latency: number }>;
}

export interface RenewalCycleResult {
  new_renewals_tracked: number;
  notifications_sent: number;
  notifications: Array<{
    tenant: string; plan: string; days_until: number;
    status: string; value: number;
  }>;
}

export interface UniversityRoiReport {
  partner: { name: string; domain: string; total_students: number };
  metrics: {
    active_students: number; total_applications: number;
    successful_applications: number; success_rate_pct: number;
    pro_upgrades: number;
  };
  revenue: {
    monthly_student_revenue: number;
    partner_share_monthly: number;
    revenue_share_pct: number;
  };
}

export interface FullInvestorMetrics extends InvestorMetrics {
  platform: {
    active_api_keys: number; api_active_tenants_30d: number;
    marketplace_blueprints: number; active_installations: number;
    active_webhooks: number; integrators: number;
  };
  verticals: Array<{
    vertical: string; tenant_count: number;
    mrr: number; arr: number; enterprise_count: number;
  }>;
  staffing_vertical: {
    total_batches: number; total_candidates_submitted: number;
    success_rate_pct: number; revenue: number; unique_agencies: number;
  };
  university_partnerships: {
    partner_count: number; total_students: number;
    partners: Array<{ name: string; students: number; pro_upgrades: number }>;
  };
  marketplace_economics: {
    total_paid_blueprints: number; gross_revenue: number;
    platform_revenue: number; author_revenue: number;
    top_blueprints: Array<{ name: string; installs: number; revenue: number }>;
  };
}
