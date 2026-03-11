import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  Calendar,
  BarChart3,
  TrendingUp,
  Users,
  Zap,
  AlertTriangle,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { cn } from "../../lib/utils";
import { apiGet } from "../../lib/api";
import { pushToast } from "../../lib/toast";

interface TenantUsage {
  tenant_id: string;
  tenant_name: string;
  matches_used: number;
  matches_limit: number;
  api_calls: number;
  api_limit: number;
  quota_percentage: number;
}

interface UsageData {
  total_matches: number;
  total_api_calls: number;
  period_start: string;
  period_end: string;
  tenants: TenantUsage[];
}

const mockUsageData: UsageData = {
  total_matches: 15420,
  total_api_calls: 89340,
  period_start: "2026-01-01",
  period_end: "2026-01-31",
  tenants: [
    { tenant_id: "1", tenant_name: "Acme Corp", matches_used: 4500, matches_limit: 10000, api_calls: 25000, api_limit: 50000, quota_percentage: 45 },
    { tenant_id: "2", tenant_name: "TechStart Inc", matches_used: 3200, matches_limit: 5000, api_calls: 18000, api_limit: 30000, quota_percentage: 64 },
    { tenant_id: "3", tenant_name: "Global Systems", matches_used: 8920, matches_limit: 10000, api_calls: 42000, api_limit: 50000, quota_percentage: 89 },
    { tenant_id: "4", tenant_name: "StartupXYZ", matches_used: 1500, matches_limit: 5000, api_calls: 8000, api_limit: 25000, quota_percentage: 30 },
    { tenant_id: "5", tenant_name: "Enterprise Solutions", matches_used: 4800, matches_limit: 5000, api_calls: 22000, api_limit: 25000, quota_percentage: 96 },
  ],
};

function QuotaBar({ used, limit, label }: { used: number; limit: number; label: string }) {
  const percentage = (used / limit) * 100;
  const isWarning = percentage >= 80;
  const isDanger = percentage >= 95;

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">{label}</span>
        <span className="text-sm font-medium text-slate-700">
          {used.toLocaleString()} / {limit.toLocaleString()}
        </span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            isDanger ? "bg-red-500" : isWarning ? "bg-amber-500" : "bg-emerald-500"
          )}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
      {isDanger && (
        <p className="text-xs text-red-600 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          Near limit - consider upgrading
        </p>
      )}
    </div>
  );
}

export default function AdminUsagePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().setDate(1)).toISOString().split("T")[0],
    end: new Date().toISOString().split("T")[0],
  });

  const fetchUsage = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<UsageData>(
        `admin/usage?start=${dateRange.start}&end=${dateRange.end}`
      );
      setUsageData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load usage");
      setUsageData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsage();
  }, [dateRange]);

  const handleExport = () => {
    if (!usageData) return;

    const csvContent = [
      ["Tenant", "Matches Used", "Matches Limit", "API Calls", "API Limit", "Quota %"].join(","),
      ...usageData.tenants.map((t) =>
        [t.tenant_name, t.matches_used, t.matches_limit, t.api_calls, t.api_limit, t.quota_percentage].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `usage-report-${dateRange.start}-${dateRange.end}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    pushToast({
      title: "Export Complete",
      description: "Usage report downloaded successfully.",
      tone: "success",
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner label="Loading usage data..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4 text-center">
          <AlertTriangle className="w-12 h-12 text-red-500" />
          <h2 className="text-lg font-semibold text-slate-900">Failed to load usage</h2>
          <p className="text-sm text-slate-600">{error}</p>
          <Button onClick={() => fetchUsage()}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Admin</p>
            <h1 className="text-2xl font-bold text-slate-900">Tenant Usage Analytics</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg p-1">
            <Calendar className="w-4 h-4 text-slate-400" />
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange((d) => ({ ...d, start: e.target.value }))}
              className="text-sm border-none outline-none bg-transparent"
            />
            <span className="text-slate-400">to</span>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange((d) => ({ ...d, end: e.target.value }))}
              className="text-sm border-none outline-none bg-transparent"
            />
          </div>
          <Button variant="outline" size="sm" onClick={handleExport} className="gap-2">
            <Download className="w-4 h-4" />
            Export
          </Button>
        </div>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Total Matches</p>
              <p className="text-xl font-bold text-slate-900">
                {usageData?.total_matches.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-100 flex items-center justify-center">
              <Zap className="w-5 h-5 text-cyan-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">API Calls</p>
              <p className="text-xl font-bold text-slate-900">
                {usageData?.total_api_calls.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Users className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Active Tenants</p>
              <p className="text-xl font-bold text-slate-900">{usageData?.tenants.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Avg Quota Used</p>
              <p className="text-xl font-bold text-slate-900">
                {Math.round(
                  (usageData?.tenants.reduce((acc, t) => acc + t.quota_percentage, 0) ?? 0) /
                    (usageData?.tenants.length ?? 1)
                )}
                %
              </p>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Match Volume (Last 30 Days)</h3>
        <div className="h-48 flex items-end gap-1">
          {Array.from({ length: 30 }).map((_, i) => {
            const height = Math.random() * 80 + 20;
            return (
              <div
                key={i}
                className="flex-1 bg-primary-500 rounded-t hover:bg-primary-600 transition-colors cursor-pointer"
                style={{ height: `${height}%` }}
                title={`Day ${i + 1}: ${Math.round(height * 15)} matches`}
              />
            );
          })}
        </div>
        <div className="flex justify-between mt-2 text-xs text-slate-400">
          <span>30 days ago</span>
          <span>Today</span>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Tenant Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Tenant
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Match Quota
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  API Quota
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {usageData?.tenants.map((tenant) => (
                <tr key={tenant.tenant_id} className="hover:bg-slate-50">
                  <td className="py-4 px-4">
                    <p className="font-medium text-slate-900">{tenant.tenant_name}</p>
                    <p className="text-xs text-slate-400">{tenant.tenant_id}</p>
                  </td>
                  <td className="py-4 px-4 w-64">
                    <QuotaBar
                      used={tenant.matches_used}
                      limit={tenant.matches_limit}
                      label=""
                    />
                  </td>
                  <td className="py-4 px-4 w-64">
                    <QuotaBar
                      used={tenant.api_calls}
                      limit={tenant.api_limit}
                      label=""
                    />
                  </td>
                  <td className="py-4 px-4">
                    {tenant.quota_percentage >= 95 ? (
                      <Badge variant="error">Critical</Badge>
                    ) : tenant.quota_percentage >= 80 ? (
                      <Badge variant="warning">Warning</Badge>
                    ) : (
                      <Badge variant="success">Healthy</Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
