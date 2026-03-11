import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Clock,
  Filter,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { cn } from "../../lib/utils";
import { apiGet, apiPatch } from "../../lib/api";
import { pushToast } from "../../lib/toast";

interface Alert {
  id: string;
  type: "critical" | "warning" | "info";
  title: string;
  message: string;
  tenant_id: string;
  tenant_name: string;
  status: "active" | "acknowledged" | "resolved";
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
}

interface AlertsData {
  active: Alert[];
  historical: Alert[];
}

const mockAlertsData: AlertsData = {
  active: [
    {
      id: "a1",
      type: "critical",
      title: "API Rate Limit Exceeded",
      message: "Tenant 'Enterprise Solutions' has exceeded their API rate limit. Requests are being throttled.",
      tenant_id: "t5",
      tenant_name: "Enterprise Solutions",
      status: "active",
      created_at: "2026-02-12T10:30:00Z",
      acknowledged_at: null,
      acknowledged_by: null,
    },
    {
      id: "a2",
      type: "warning",
      title: "High Error Rate Detected",
      message: "Match API error rate has exceeded 5% in the last hour. Current rate: 7.2%.",
      tenant_id: "system",
      tenant_name: "System",
      status: "active",
      created_at: "2026-02-12T09:45:00Z",
      acknowledged_at: null,
      acknowledged_by: null,
    },
    {
      id: "a3",
      type: "warning",
      title: "Quota Near Limit",
      message: "Tenant 'Global Systems' is at 89% of their monthly match quota.",
      tenant_id: "t3",
      tenant_name: "Global Systems",
      status: "active",
      created_at: "2026-02-12T08:00:00Z",
      acknowledged_at: null,
      acknowledged_by: null,
    },
    {
      id: "a4",
      type: "info",
      title: "Scheduled Maintenance",
      message: "Planned maintenance window scheduled for Feb 14, 2026 at 2:00 AM UTC. Expected downtime: 30 minutes.",
      tenant_id: "system",
      tenant_name: "System",
      status: "active",
      created_at: "2026-02-11T15:00:00Z",
      acknowledged_at: null,
      acknowledged_by: null,
    },
  ],
  historical: [
    {
      id: "h1",
      type: "critical",
      title: "Database Connection Pool Exhausted",
      message: "Connection pool reached 100% capacity. Automatic scaling triggered.",
      tenant_id: "system",
      tenant_name: "System",
      status: "resolved",
      created_at: "2026-02-10T14:20:00Z",
      acknowledged_at: "2026-02-10T14:25:00Z",
      acknowledged_by: "admin@example.com",
    },
    {
      id: "h2",
      type: "warning",
      title: "Memory Usage High",
      message: "Server memory usage exceeded 85%. Monitoring closely.",
      tenant_id: "system",
      tenant_name: "System",
      status: "acknowledged",
      created_at: "2026-02-10T10:00:00Z",
      acknowledged_at: "2026-02-10T10:05:00Z",
      acknowledged_by: "admin@example.com",
    },
  ],
};

function AlertIcon({ type }: { type: Alert["type"] }) {
  switch (type) {
    case "critical":
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    case "warning":
      return <AlertTriangle className="w-5 h-5 text-amber-500" />;
    case "info":
      return <Info className="w-5 h-5 text-blue-500" />;
  }
}

function AlertCard({
  alert,
  onAcknowledge,
}: {
  alert: Alert;
  onAcknowledge: (id: string) => void;
}) {
  const isHistorical = alert.status !== "active";

  return (
    <Card
      className={cn(
        "p-4",
        alert.type === "critical" && alert.status === "active" && "border-red-200 bg-red-50/50",
        alert.type === "warning" && alert.status === "active" && "border-amber-200 bg-amber-50/50",
        isHistorical && "opacity-75"
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <AlertIcon type={alert.type} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-semibold text-slate-900">{alert.title}</h4>
            <Badge
              variant={
                alert.status === "active"
                  ? alert.type === "critical"
                    ? "error"
                    : "warning"
                  : alert.status === "acknowledged"
                    ? "warning"
                    : "success"
              }
              size="sm"
            >
              {alert.status}
            </Badge>
          </div>
          <p className="text-sm text-slate-600 mb-2">{alert.message}</p>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(alert.created_at).toLocaleString()}
            </span>
            <span>Tenant: {alert.tenant_name}</span>
            {alert.acknowledged_at && (
              <span className="flex items-center gap-1">
                <CheckCircle className="w-3 h-3" />
                Acknowledged by {alert.acknowledged_by}
              </span>
            )}
          </div>
        </div>
        {alert.status === "active" && (
          <Button size="sm" variant="outline" onClick={() => onAcknowledge(alert.id)}>
            Acknowledge
          </Button>
        )}
      </div>
    </Card>
  );
}

export default function AdminAlertsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [alertsData, setAlertsData] = useState<AlertsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [tab, setTab] = useState<"active" | "historical">("active");

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (severityFilter) params.append("severity", severityFilter);
      if (statusFilter) params.append("status", statusFilter);
      const data = await apiGet<AlertsData>(`admin/alerts?${params}`);
      setAlertsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load alerts");
      setAlertsData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [severityFilter, statusFilter]);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await apiPatch(`admin/alerts/${alertId}/acknowledge`, {});
      pushToast({
        title: "Alert Acknowledged",
        description: "The alert has been acknowledged.",
        tone: "success",
      });
      setAlertsData((prev) => {
        if (!prev) return prev;
        const alert = prev.active.find((a) => a.id === alertId);
        if (alert) {
          alert.status = "acknowledged";
          alert.acknowledged_at = new Date().toISOString();
          alert.acknowledged_by = "current-user@example.com";
          return {
            active: prev.active.filter((a) => a.id !== alertId),
            historical: [alert, ...prev.historical],
          };
        }
        return prev;
      });
    } catch {
      pushToast({
        title: "Acknowledgement Failed",
        description: "Could not acknowledge alert.",
        tone: "error",
      });
    }
  };

  const filteredAlerts =
    tab === "active"
      ? alertsData?.active.filter((a) => {
          if (severityFilter && a.type !== severityFilter) return false;
          if (statusFilter && a.status !== statusFilter) return false;
          return true;
        })
      : alertsData?.historical.filter((a) => {
          if (severityFilter && a.type !== severityFilter) return false;
          if (statusFilter && a.status !== statusFilter) return false;
          return true;
        });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner label="Loading alerts..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4 text-center">
          <AlertTriangle className="w-12 h-12 text-red-500" />
          <h2 className="text-lg font-semibold text-slate-900">Failed to load alerts</h2>
          <p className="text-sm text-slate-600">{error}</p>
          <Button onClick={() => fetchAlerts()}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Admin</p>
            <h1 className="text-2xl font-bold text-slate-900">Real-time Alerts</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-slate-400" />
          <Badge variant={alertsData?.active.length ? "error" : "success"}>
            {alertsData?.active.length ?? 0} active
          </Badge>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex rounded-lg border border-slate-200 overflow-hidden">
          <button
            onClick={() => setTab("active")}
            className={cn(
              "px-4 py-2 text-sm font-medium transition-colors",
              tab === "active"
                ? "bg-primary-500 text-white"
                : "bg-white text-slate-600 hover:bg-slate-50"
            )}
          >
            Active ({alertsData?.active.length ?? 0})
          </button>
          <button
            onClick={() => setTab("historical")}
            className={cn(
              "px-4 py-2 text-sm font-medium transition-colors",
              tab === "historical"
                ? "bg-primary-500 text-white"
                : "bg-white text-slate-600 hover:bg-slate-50"
            )}
          >
            Historical ({alertsData?.historical.length ?? 0})
          </button>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      <div className="space-y-4">
        {filteredAlerts?.length === 0 ? (
          <Card className="p-8 text-center">
            <Bell className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-700 mb-2">
              {tab === "active" ? "No Active Alerts" : "No Historical Alerts"}
            </h3>
            <p className="text-slate-500">
              {tab === "active"
                ? "All systems operating normally."
                : "No alerts match your filters."}
            </p>
          </Card>
        ) : (
          filteredAlerts?.map((alert) => (
            <AlertCard key={alert.id} alert={alert} onAcknowledge={handleAcknowledge} />
          ))
        )}
      </div>
    </div>
  );
}
