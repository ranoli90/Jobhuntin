import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function authHeaders(): Promise<Record<string, string>> {
  const { supabase } = await import("../lib/supabase");
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

interface HealthSummary {
  status: string;
  uptime_seconds: number;
  total_requests: number;
  total_errors: number;
  error_rate_pct: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  active_alerts: number;
  circuit_breakers: Record<string, string>;
  database_status: string;
  redis_status: string;
}

interface AlertItem {
  id: string;
  rule_name: string;
  severity: string;
  status: string;
  message: string;
  metric_value: number;
  threshold: number;
  triggered_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
}

interface TenantActivity {
  tenant_id: string;
  tenant_name: string;
  plan: string;
  active_users: number;
  requests_last_hour: number;
  requests_last_day: number;
  error_count: number;
  last_activity: string | null;
}

interface PerformanceTrend {
  timestamp: string;
  requests_per_minute: number;
  avg_latency_ms: number;
  error_rate_pct: number;
  active_connections: number;
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    healthy: "bg-green-500/20 text-green-400",
    warning: "bg-yellow-500/20 text-yellow-400",
    degraded: "bg-orange-500/20 text-orange-400",
    unhealthy: "bg-red-500/20 text-red-400",
    ok: "bg-green-500/20 text-green-400",
    unavailable: "bg-gray-500/20 text-gray-400",
    unreachable: "bg-red-500/20 text-red-400",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${colors[status] || "bg-gray-500/20 text-gray-400"}`}>
      {status.toUpperCase()}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    info: "bg-blue-500/20 text-blue-400",
    warning: "bg-yellow-500/20 text-yellow-400",
    error: "bg-orange-500/20 text-orange-400",
    critical: "bg-red-500/20 text-red-400",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${colors[severity] || "bg-gray-500/20 text-gray-400"}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function StatCard({ label, value, unit, status }: { label: string; value: string | number; unit?: string; status?: string }) {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between">
        <p className="text-2xl font-bold text-foreground">{value}{unit && <span className="text-sm text-muted-foreground ml-1">{unit}</span>}</p>
        {status && <StatusBadge status={status} />}
      </div>
      <p className="text-sm text-muted-foreground mt-1">{label}</p>
    </div>
  );
}

function LatencyBar({ p50, p95, p99 }: { p50: number; p95: number; p99: number }) {
  const maxVal = Math.max(p99, 1000);
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground w-12">P50</span>
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-green-500 rounded-full" style={{ width: `${(p50 / maxVal) * 100}%` }} />
        </div>
        <span className="text-xs text-muted-foreground w-16 text-right">{p50.toFixed(0)}ms</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground w-12">P95</span>
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-yellow-500 rounded-full" style={{ width: `${(p95 / maxVal) * 100}%` }} />
        </div>
        <span className="text-xs text-muted-foreground w-16 text-right">{p95.toFixed(0)}ms</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground w-12">P99</span>
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-red-500 rounded-full" style={{ width: `${(p99 / maxVal) * 100}%` }} />
        </div>
        <span className="text-xs text-muted-foreground w-16 text-right">{p99.toFixed(0)}ms</span>
      </div>
    </div>
  );
}

function AlertsPanel({ alerts, onAcknowledge }: { alerts: AlertItem[]; onAcknowledge: (id: string) => void }) {
  const [acknowledging, setAcknowledging] = useState<string | null>(null);

  const handleAcknowledge = async (id: string) => {
    setAcknowledging(id);
    try {
      await onAcknowledge(id);
    } finally {
      setAcknowledging(null);
    }
  };

  if (alerts.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-3">Active Alerts</h2>
        <p className="text-muted-foreground text-sm">No active alerts</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h2 className="font-semibold mb-3">Active Alerts ({alerts.length})</h2>
      <div className="space-y-3">
        {alerts.map((alert) => (
          <div key={alert.id} className="border border-border rounded-lg p-3 space-y-2">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <SeverityBadge severity={alert.severity} />
                <span className="font-medium text-sm">{alert.rule_name}</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {new Date(alert.triggered_at).toLocaleTimeString()}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">{alert.message}</p>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">
                Value: {alert.metric_value.toFixed(2)} / Threshold: {alert.threshold.toFixed(2)}
              </span>
              {alert.status === "firing" && (
                <button
                  onClick={() => handleAcknowledge(alert.id)}
                  disabled={acknowledging === alert.id}
                  className="px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 disabled:opacity-50"
                >
                  {acknowledging === alert.id ? "Acknowledging..." : "Acknowledge"}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TenantsTable({ tenants }: { tenants: TenantActivity[] }) {
  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h2 className="font-semibold mb-3">Tenant Activity</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border">
              <th className="pb-2">Tenant</th>
              <th className="pb-2">Plan</th>
              <th className="pb-2 text-right">Users</th>
              <th className="pb-2 text-right">Last Hour</th>
              <th className="pb-2 text-right">Last Day</th>
              <th className="pb-2 text-right">Errors</th>
              <th className="pb-2 text-right">Last Activity</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((t) => (
              <tr key={t.tenant_id} className="border-b border-border/50">
                <td className="py-2 font-medium">{t.tenant_name}</td>
                <td className="py-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    t.plan === "ENTERPRISE" ? "bg-purple-500/20 text-purple-400" :
                    t.plan === "TEAM" ? "bg-blue-500/20 text-blue-400" :
                    t.plan === "PRO" ? "bg-green-500/20 text-green-400" :
                    "bg-gray-500/20 text-gray-400"
                  }`}>{t.plan}</span>
                </td>
                <td className="py-2 text-right">{t.active_users}</td>
                <td className="py-2 text-right">{t.requests_last_hour}</td>
                <td className="py-2 text-right">{t.requests_last_day}</td>
                <td className="py-2 text-right">
                  {t.error_count > 0 ? (
                    <span className="text-red-400">{t.error_count}</span>
                  ) : (
                    <span className="text-muted-foreground">0</span>
                  )}
                </td>
                <td className="py-2 text-right text-muted-foreground">
                  {t.last_activity ? new Date(t.last_activity).toLocaleString() : "N/A"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PerformanceChart({ trends }: { trends: PerformanceTrend[] }) {
  if (trends.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-3">Performance Trends</h2>
        <p className="text-muted-foreground text-sm">No data available</p>
      </div>
    );
  }

  const maxLatency = Math.max(...trends.map(t => t.avg_latency_ms), 100);
  const maxRpm = Math.max(...trends.map(t => t.requests_per_minute), 10);

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h2 className="font-semibold mb-3">Performance Trends (Last {trends.length} data points)</h2>
      <div className="space-y-4">
        <div>
          <h3 className="text-sm text-muted-foreground mb-2">Requests per Minute</h3>
          <div className="flex items-end gap-1 h-20">
            {trends.slice(-20).map((t, i) => (
              <div
                key={i}
                className="flex-1 bg-primary/50 rounded-t"
                style={{ height: `${(t.requests_per_minute / maxRpm) * 100}%` }}
                title={`${t.requests_per_minute.toFixed(1)} rpm`}
              />
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm text-muted-foreground mb-2">Avg Latency (ms)</h3>
          <div className="flex items-end gap-1 h-20">
            {trends.slice(-20).map((t, i) => (
              <div
                key={i}
                className={`flex-1 rounded-t ${t.avg_latency_ms > 500 ? 'bg-red-500/50' : t.avg_latency_ms > 200 ? 'bg-yellow-500/50' : 'bg-green-500/50'}`}
                style={{ height: `${(t.avg_latency_ms / maxLatency) * 100}%` }}
                title={`${t.avg_latency_ms.toFixed(0)}ms`}
              />
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm text-muted-foreground mb-2">Error Rate (%)</h3>
          <div className="flex items-end gap-1 h-20">
            {trends.slice(-20).map((t, i) => (
              <div
                key={i}
                className={`flex-1 rounded-t ${t.error_rate_pct > 5 ? 'bg-red-500/50' : t.error_rate_pct > 2 ? 'bg-yellow-500/50' : 'bg-green-500/50'}`}
                style={{ height: `${Math.min(t.error_rate_pct * 10, 100)}%` }}
                title={`${t.error_rate_pct.toFixed(2)}%`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function CircuitBreakersPanel({ circuitBreakers }: { circuitBreakers: Record<string, string> }) {
  const entries = Object.entries(circuitBreakers);
  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h2 className="font-semibold mb-3">Circuit Breakers</h2>
      <div className="flex flex-wrap gap-2">
        {entries.map(([name, state]) => (
          <div key={name} className="flex items-center gap-2 px-3 py-1 rounded-full border border-border">
            <span className="text-sm">{name}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              state === "closed" ? "bg-green-500/20 text-green-400" :
              state === "open" ? "bg-red-500/20 text-red-400" :
              "bg-yellow-500/20 text-yellow-400"
            }`}>
              {state.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const queryClient = useQueryClient();

  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ["dashboard", "overview"],
    queryFn: () => request<HealthSummary>("GET", "/admin/dashboard/overview"),
    refetchInterval: 30000,
  });

  const { data: alerts = [] } = useQuery({
    queryKey: ["dashboard", "alerts"],
    queryFn: () => request<AlertItem[]>("GET", "/admin/dashboard/alerts?status=firing"),
    refetchInterval: 10000,
  });

  const { data: tenants = [] } = useQuery({
    queryKey: ["dashboard", "tenants"],
    queryFn: () => request<TenantActivity[]>("GET", "/admin/dashboard/tenants"),
    refetchInterval: 60000,
  });

  const { data: trends = [] } = useQuery({
    queryKey: ["dashboard", "performance"],
    queryFn: () => request<PerformanceTrend[]>("GET", "/admin/dashboard/performance"),
    refetchInterval: 30000,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: string) => request<{ status: string }>("POST", `/admin/dashboard/alerts/${alertId}/acknowledge`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", "alerts"] });
    },
  });

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  if (loadingOverview) {
    return <div className="text-muted-foreground">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">System Dashboard</h1>
          <p className="text-sm text-muted-foreground">Real-time monitoring and alerting</p>
        </div>
        {overview && (
          <StatusBadge status={overview.status} />
        )}
      </div>

      {overview && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <StatCard label="Uptime" value={formatUptime(overview.uptime_seconds)} />
            <StatCard label="Total Requests" value={overview.total_requests.toLocaleString()} />
            <StatCard label="Total Errors" value={overview.total_errors.toLocaleString()} />
            <StatCard label="Error Rate" value={overview.error_rate_pct.toFixed(2)} unit="%" status={overview.error_rate_pct > 5 ? "unhealthy" : overview.error_rate_pct > 2 ? "warning" : "healthy"} />
            <StatCard label="Database" value="" status={overview.database_status} />
            <StatCard label="Redis" value="" status={overview.redis_status} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-card border border-border rounded-lg p-5">
              <h2 className="font-semibold mb-3">Latency Distribution</h2>
              <LatencyBar
                p50={overview.latency_p50_ms}
                p95={overview.latency_p95_ms}
                p99={overview.latency_p99_ms}
              />
            </div>
            <CircuitBreakersPanel circuitBreakers={overview.circuit_breakers} />
          </div>
        </>
      )}

      <AlertsPanel alerts={alerts} onAcknowledge={(id) => acknowledgeMutation.mutateAsync(id)} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceChart trends={trends} />
        <TenantsTable tenants={tenants} />
      </div>
    </div>
  );
}
