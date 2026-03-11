import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
import { apiGet, apiPost } from "../../lib/api";
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

/** Map API AlertResponse to our Alert shape. Dashboard API: /admin/dashboard/alerts */
function mapApiAlertToAlert(raw: {
  id: string;
  rule_name: string;
  severity: string;
  status: string;
  message: string;
  triggered_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
}): Alert {
  const type =
    raw.severity === "critical" || raw.severity === "error"
      ? "critical"
      : raw.severity === "warning"
        ? "warning"
        : "info";
  const status =
    raw.status === "firing"
      ? "active"
      : (raw.status as "acknowledged" | "resolved");
  return {
    id: raw.id,
    type,
    title: raw.rule_name,
    message: raw.message,
    tenant_id: "system",
    tenant_name: "System",
    status,
    created_at: raw.triggered_at,
    acknowledged_at: raw.acknowledged_at,
    acknowledged_by: raw.acknowledged_by,
  };
}

function AlertIcon({ type }: { type: Alert["type"] }) {
  switch (type) {
    case "critical": {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
    case "warning": {
      return <AlertTriangle className="w-5 h-5 text-amber-500" />;
    }
    case "info": {
      return <Info className="w-5 h-5 text-blue-500" />;
    }
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
        alert.type === "critical" &&
          alert.status === "active" &&
          "border-red-200 bg-red-50/50",
        alert.type === "warning" &&
          alert.status === "active" &&
          "border-amber-200 bg-amber-50/50",
        isHistorical && "opacity-75",
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
          <Button
            size="sm"
            variant="outline"
            onClick={() => onAcknowledge(alert.id)}
          >
            Acknowledge
          </Button>
        )}
      </div>
    </Card>
  );
}

const ALERTS_QUERY_KEY = ["admin", "dashboard", "alerts"] as const;

export default function AdminAlertsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [tab, setTab] = useState<"active" | "historical">("active");

  const { data: rawAlerts = [], isLoading, error, refetch } = useQuery({
    queryKey: [...ALERTS_QUERY_KEY, severityFilter, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (severityFilter) params.set("severity", severityFilter);
      if (statusFilter) params.set("status", statusFilter);
      return apiGet<Array<{
        id: string;
        rule_name: string;
        severity: string;
        status: string;
        message: string;
        triggered_at: string;
        acknowledged_at: string | null;
        acknowledged_by: string | null;
      }>>(`admin/dashboard/alerts?${params}`);
    },
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: string) =>
      apiPost(`admin/dashboard/alerts/${alertId}/acknowledge`, {}),
    onSuccess: () => {
      pushToast({
        title: "Alert Acknowledged",
        description: "The alert has been acknowledged.",
        tone: "success",
      });
      queryClient.invalidateQueries({ queryKey: ALERTS_QUERY_KEY });
    },
    onError: () => {
      pushToast({
        title: "Acknowledgement Failed",
        description: "Could not acknowledge alert.",
        tone: "error",
      });
    },
  });

  const alertsData: AlertsData = {
    active: rawAlerts
      .filter((a) => a.status === "firing")
      .map(mapApiAlertToAlert),
    historical: rawAlerts
      .filter((a) => a.status !== "firing")
      .map(mapApiAlertToAlert),
  };

  const handleAcknowledge = (alertId: string) => {
    acknowledgeMutation.mutate(alertId);
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

  if (isLoading) {
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
          <h2 className="text-lg font-semibold text-slate-900">
            Failed to load alerts
          </h2>
          <p className="text-sm text-slate-600">
            {error instanceof Error ? error.message : "Failed to load alerts"}
          </p>
          <Button onClick={() => refetch()}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Admin
            </p>
            <h1 className="text-2xl font-bold text-slate-900">
              Real-time Alerts
            </h1>
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
                : "bg-white text-slate-600 hover:bg-slate-50",
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
                : "bg-white text-slate-600 hover:bg-slate-50",
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
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
            />
          ))
        )}
      </div>
    </div>
  );
}
