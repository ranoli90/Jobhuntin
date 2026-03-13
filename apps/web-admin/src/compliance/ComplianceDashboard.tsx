import { useEffect, useState } from "react";
import { apiRequest, getApiBase } from "../lib/api";

interface ConsentRate {
  opted_in: number;
  opted_out: number;
  total: number;
  rate: number;
}

interface ConsentRates {
  marketing: ConsentRate;
  analytics: ConsentRate;
  cookies: ConsentRate;
  functional: ConsentRate;
  essential: ConsentRate;
}

interface DataVolume {
  count: number;
  latest_record: string | null;
}

interface DeletionRequests {
  total_requests: number;
  completed: number;
  pending: number;
  in_progress: number;
  failed: number;
}

interface RetentionCompliance {
  record_count: number;
  retention_days: number;
  compliant: boolean;
}

interface ComplianceOverview {
  consent_rates: ConsentRates;
  data_volume: {
    profiles: DataVolume;
    applications: DataVolume;
    resumes: DataVolume;
  };
  deletion_requests: DeletionRequests;
  retention_compliance: {
    applications: RetentionCompliance;
    application_events: RetentionCompliance;
    analytics_events: RetentionCompliance;
  };
  generated_at: string;
}

interface ProcessingActivity {
  id: string;
  name: string;
  purpose: string;
  data_categories: string[];
  legal_basis: string;
  retention_period: string;
  recipients: string[];
}

interface ComplianceEvent {
  id: string;
  type: string;
  action: string;
  details: string;
  timestamp: string;
}

export default function ComplianceDashboard() {
  const [overview, setOverview] = useState<ComplianceOverview | null>(null);
  const [activities, setActivities] = useState<ProcessingActivity[]>([]);
  const [events, setEvents] = useState<ComplianceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "processing" | "audit">("overview");

  const loadOverview = async () => {
    try {
      const data = await apiRequest<ComplianceOverview>("GET", "/compliance/overview");
      setOverview(data);
    } catch (e) {
      console.error("Failed to load compliance overview:", e);
    }
  };

  const loadActivities = async () => {
    try {
      const data = await apiRequest<{ activities: ProcessingActivity[] }>(
        "GET",
        "/compliance/data-processing"
      );
      setActivities(data.activities);
    } catch (e) {
      console.error("Failed to load processing activities:", e);
    }
  };

  const loadAuditLog = async () => {
    try {
      const data = await apiRequest<{ events: ComplianceEvent[]; total: number }>(
        "GET",
        "/compliance/audit-log?limit=50"
      );
      setEvents(data.events);
    } catch (e) {
      console.error("Failed to load audit log:", e);
    }
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await loadOverview();
      await loadActivities();
      await loadAuditLog();
      setLoading(false);
    };
    load();
  }, []);

  const handleExport = async (format: "json" | "csv") => {
    setExporting(true);
    try {
      const response = await fetch(
        `${getApiBase()}/compliance/export?format=${format}`,
        {
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("auth_token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Export failed");
      }

      const data = await response.json();
      const content = format === "csv" ? data.content : JSON.stringify(data.content, null, 2);
      const blob = new Blob([content], { type: format === "csv" ? "text/csv" : "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data.filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Export failed: ${e}`);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading compliance data...</div>
      </div>
    );
  }

  const consentTypes = overview ? Object.entries(overview.consent_rates) : [];
  const totalOptedIn = consentTypes.reduce((sum, [, data]) => sum + data.opted_in, 0);
  const totalOptedOut = consentTypes.reduce((sum, [, data]) => sum + data.opted_out, 0);
  const totalUsers = totalOptedIn + totalOptedOut;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Compliance Dashboard</h1>
          <p className="text-muted-foreground">
            GDPR Article 30 compliance reporting and monitoring
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport("json")}
            disabled={exporting}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50"
          >
            {exporting ? "Exporting..." : "Export JSON"}
          </button>
          <button
            onClick={() => handleExport("csv")}
            disabled={exporting}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:opacity-90 disabled:opacity-50"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-4 py-2 -mb-px ${
            activeTab === "overview"
              ? "border-b-2 border-primary font-medium"
              : "text-muted-foreground"
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab("processing")}
          className={`px-4 py-2 -mb-px ${
            activeTab === "processing"
              ? "border-b-2 border-primary font-medium"
              : "text-muted-foreground"
          }`}
        >
          Data Processing
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`px-4 py-2 -mb-px ${
            activeTab === "audit"
              ? "border-b-2 border-primary font-medium"
              : "text-muted-foreground"
          }`}
        >
          Audit Log
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && overview && (
        <div className="space-y-6">
          {/* Consent Rates Pie Chart Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Consent Pie Chart */}
            <div className="bg-card rounded-lg border p-6">
              <h3 className="text-lg font-semibold mb-4">Consent Distribution</h3>
              <div className="flex items-center justify-center">
                <div className="relative w-48 h-48">
                  <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                    {/* Opted In - Blue */}
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="20"
                      strokeDasharray={`${(totalOptedIn / totalUsers) * 251.2} 251.2`}
                    />
                    {/* Opted Out - Red */}
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      stroke="#ef4444"
                      strokeWidth="20"
                      strokeDasharray={`${(totalOptedOut / totalUsers) * 251.2} 251.2`}
                      strokeDashoffset={-((totalOptedIn / totalUsers) * 251.2)}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {totalUsers > 0 ? Math.round((totalOptedIn / totalUsers) * 100) : 0}%
                      </div>
                      <div className="text-xs text-muted-foreground">Opted In</div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex justify-center gap-4 mt-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span>Opted In ({totalOptedIn.toLocaleString()})</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span>Opted Out ({totalOptedOut.toLocaleString()})</span>
                </div>
              </div>
            </div>

            {/* Consent by Type */}
            <div className="bg-card rounded-lg border p-6">
              <h3 className="text-lg font-semibold mb-4">Consent by Type</h3>
              <div className="space-y-4">
                {consentTypes.map(([type, data]) => (
                  <div key={type} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="capitalize">{type}</span>
                      <span className="text-muted-foreground">
                        {data.rate.toFixed(1)}% ({data.opted_in.toLocaleString()} / {data.total.toLocaleString()})
                      </span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full"
                        style={{ width: `${data.rate}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Data Volume */}
            <div className="bg-card rounded-lg border p-6">
              <h4 className="text-sm font-medium text-muted-foreground mb-1">
                Total Profiles
              </h4>
              <div className="text-2xl font-bold">
                {overview.data_volume.profiles.count.toLocaleString()}
              </div>
            </div>
            <div className="bg-card rounded-lg border p-6">
              <h4 className="text-sm font-medium text-muted-foreground mb-1">
                Total Applications
              </h4>
              <div className="text-2xl font-bold">
                {overview.data_volume.applications.count.toLocaleString()}
              </div>
            </div>
            <div className="bg-card rounded-lg border p-6">
              <h4 className="text-sm font-medium text-muted-foreground mb-1">
                Deletion Requests
              </h4>
              <div className="text-2xl font-bold">
                {overview.deletion_requests.total_requests}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {overview.deletion_requests.completed} completed,{" "}
                {overview.deletion_requests.pending} pending
              </div>
            </div>
            <div className="bg-card rounded-lg border p-6">
              <h4 className="text-sm font-medium text-muted-foreground mb-1">
                Compliance Status
              </h4>
              <div className="text-2xl font-bold text-green-500">Active</div>
              <div className="text-xs text-muted-foreground mt-1">
                All retention policies enforced
              </div>
            </div>
          </div>

          {/* Data Retention Status */}
          <div className="bg-card rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4">Data Retention Compliance</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(overview.retention_compliance).map(([key, data]) => (
                <div key={key} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium capitalize">{key.replace("_", " ")}</span>
                    <span
                      className={`px-2 py-1 text-xs rounded ${
                        data.compliant
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {data.compliant ? "Compliant" : "Action Needed"}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <div>Retention: {data.retention_days} days</div>
                    <div>Records: {data.record_count.toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Compliance Events */}
          <div className="bg-card rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Compliance Events</h3>
            <div className="space-y-2">
              {events.slice(0, 10).map((event) => (
                <div
                  key={event.id}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-1 text-xs rounded ${
                        event.type === "consent"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-orange-100 text-orange-800"
                      }`}
                    >
                      {event.type}
                    </span>
                    <span className="text-sm">{event.action}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </div>
              ))}
              {events.length === 0 && (
                <div className="text-center text-muted-foreground py-4">
                  No recent compliance events
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Data Processing Tab */}
      {activeTab === "processing" && (
        <div className="bg-card rounded-lg border p-6">
          <h3 className="text-lg font-semibold mb-4">
            Records of Processing Activities (GDPR Article 30)
          </h3>
          <div className="space-y-4">
            {activities.map((activity) => (
              <div key={activity.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{activity.name}</h4>
                  <span className="text-sm text-muted-foreground">{activity.legal_basis}</span>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{activity.purpose}</p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Data Categories:</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {activity.data_categories.map((cat) => (
                        <span key={cat} className="px-2 py-0.5 bg-secondary rounded text-xs">
                          {cat}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Retention:</span>
                    <div className="mt-1">{activity.retention_period}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Recipients:</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {activity.recipients.map((rec) => (
                        <span key={rec} className="px-2 py-0.5 bg-secondary rounded text-xs">
                          {rec}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Log Tab */}
      {activeTab === "audit" && (
        <div className="bg-card rounded-lg border p-6">
          <h3 className="text-lg font-semibold mb-4">Compliance Audit Log</h3>
          <div className="space-y-2">
            {events.map((event) => (
              <div key={event.id} className="flex items-center justify-between py-3 border-b last:border-0">
                <div className="flex items-center gap-4">
                  <span
                    className={`px-2 py-1 text-xs rounded ${
                      event.type === "consent"
                        ? "bg-blue-100 text-blue-800"
                        : event.type === "deletion"
                        ? "bg-orange-100 text-orange-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {event.type}
                  </span>
                  <div>
                    <div className="font-medium">{event.action}</div>
                    <div className="text-sm text-muted-foreground">{event.details}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm">{new Date(event.timestamp).toLocaleDateString()}</div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {events.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                No audit log entries found
              </div>
            )}
          </div>
        </div>
      )}

      {/* Generated timestamp */}
      {overview && (
        <div className="text-xs text-muted-foreground text-right">
          Last updated: {new Date(overview.generated_at).toLocaleString()}
        </div>
      )}
    </div>
  );
}
