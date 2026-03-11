import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Progress } from "@/components/ui/Progress";
import {
  Users,
  Activity,
  Clock,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  BarChart3,
  RefreshCw,
  Eye,
  EyeOff,
} from "lucide-react";

interface ConcurrentSession {
  session_id: string;
  user_id: string;
  tenant_id: string;
  application_id?: string;
  status: "active" | "completed" | "failed" | "cancelled";
  steps_completed: number;
  total_steps: number;
  error_count: number;
  screenshots_captured: number;
  buttons_detected: number;
  forms_processed: number;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
}

interface ConcurrentStats {
  total_active: number;
  max_concurrent: number;
  current_concurrent: number;
  peak_concurrent: number;
  active_sessions: string[];
  tenant_stats: Record<string, Record<string, number>>;
}

const ConcurrentUsageMonitor: React.FC = () => {
  const [sessions, setSessions] = useState<ConcurrentSession[]>([]);
  const [stats, setStats] = useState<ConcurrentStats>({
    total_active: 0,
    max_concurrent: 10,
    current_concurrent: 0,
    peak_concurrent: 0,
    active_sessions: [],
    tenant_stats: {},
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchSessions();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchStats();
        fetchSessions();
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/concurrent-usage/stats", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch stats");
      const data = await response.json();
      setStats(data);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to fetch stats",
      );
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch("/api/concurrent-usage/sessions", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch sessions");
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to fetch sessions",
      );
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      active: "bg-green-100 text-green-800",
      completed: "bg-blue-100 text-blue-800",
      failed: "bg-red-100 text-red-800",
      cancelled: "bg-gray-100 text-gray-800",
    };
    return colors[status as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      active: <Activity className="h-4 w-4" />,
      completed: <CheckCircle className="h-4 w-4" />,
      failed: <AlertTriangle className="h-4 w-4" />,
      cancelled: <EyeOff className="h-4 w-4" />,
    };
    return icons[status as keyof typeof icons] || <Clock className="h-4 w-4" />;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return "N/A";
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);

    if (diffSeconds < 60) return "Just now";
    if (diffSeconds < 3600)
      return `${Math.floor(diffSeconds / 60)} minutes ago`;
    if (diffSeconds < 86_400)
      return `${Math.floor(diffSeconds / 3600)} hours ago`;
    return `${Math.floor(diffSeconds / 86_400)} days ago`;
  };

  const getProgressPercentage = (session: ConcurrentSession) => {
    if (session.total_steps === 0) return 0;
    return (session.steps_completed / session.total_steps) * 100;
  };

  const handleCompleteSession = async (sessionId: string) => {
    try {
      const response = await fetch("/api/concurrent-usage/complete-session", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          status: "completed",
        }),
      });

      if (!response.ok) throw new Error("Failed to complete session");

      await fetchSessions();
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to complete session",
      );
    }
  };

  const handleFailSession = async (sessionId: string) => {
    try {
      const response = await fetch("/api/concurrent-usage/fail-session", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          error_count: 1,
        }),
      });

      if (!response.ok) throw new Error("Failed to fail session");

      await fetchSessions();
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to fail session",
      );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Concurrent Usage Monitor</h1>
          <p className="text-gray-600">
            Real-time monitoring of concurrent application sessions
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${autoRefresh ? "animate-spin" : ""}`}
            />
            {autoRefresh ? "Auto-refresh" : "Manual refresh"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? (
              <EyeOff className="h-4 w-4 mr-2" />
            ) : (
              <Eye className="h-4 w-4 mr-2" />
            )}
            {showDetails ? "Hide Details" : "Show Details"}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchStats}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Active Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.total_active}
            </div>
            <div className="text-sm text-gray-500">
              {stats.current_concurrent}/{stats.max_concurrent} concurrent
            </div>
            <Progress
              value={(stats.current_concurrent / stats.max_concurrent) * 100}
              className="h-2 mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Peak Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {stats.peak_concurrent}
            </div>
            <div className="text-sm text-gray-500">
              Maximum concurrent sessions
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Total Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {sessions.length}
            </div>
            <div className="text-sm text-gray-500">All tracked sessions</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {sessions.length > 0
                ? Math.round(
                    (sessions.filter((s) => s.status === "completed").length /
                      sessions.length) *
                      100,
                  )
                : 0}
              %
            </div>
            <div className="text-sm text-gray-500">Completed successfully</div>
          </CardContent>
        </Card>
      </div>

      {/* Active Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sessions
              .filter((session) => session.status === "active")
              .map((session) => (
                <Card key={session.session_id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(session.status)}
                      <div className="flex-1">
                        <h4 className="font-medium">
                          Session: {session.session_id.slice(0, 8)}...
                        </h4>
                        <p className="text-sm text-gray-500">
                          Started: {formatTimeAgo(session.start_time)}
                        </p>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Badge className={getStatusColor(session.status)}>
                        {session.status.toUpperCase()}
                      </Badge>
                      <div className="flex space-x-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            handleCompleteSession(session.session_id)
                          }
                        >
                          <CheckCircle className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleFailSession(session.session_id)}
                        >
                          <AlertTriangle className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span>Progress</span>
                      <span>
                        {session.steps_completed}/{session.total_steps} steps
                      </span>
                    </div>
                    <Progress
                      value={getProgressPercentage(session)}
                      className="h-2"
                    />
                  </div>

                  {/* Metrics */}
                  {showDetails && (
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Screenshots:</span>
                        <span className="font-medium">
                          {session.screenshots_captured}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Buttons:</span>
                        <span className="font-medium">
                          {session.buttons_detected}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Forms:</span>
                        <span className="font-medium">
                          {session.forms_processed}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Errors:</span>
                        <span className="font-medium text-red-600">
                          {session.error_count}
                        </span>
                      </div>
                    </div>
                  )}
                </Card>
              ))}
          </div>

          {sessions.filter((session) => session.status === "active").length ===
            0 && (
            <div className="text-center py-8">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No active sessions</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Session History */}
      {showDetails && (
        <Card>
          <CardHeader>
            <CardTitle>Session History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sessions
                .filter((session) => session.status !== "active")
                .slice(0, 10)
                .map((session) => (
                  <Card key={session.session_id} className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(session.status)}
                        <div>
                          <h4 className="font-medium">
                            Session: {session.session_id.slice(0, 8)}...
                          </h4>
                          <p className="text-sm text-gray-500">
                            {session.end_time
                              ? `Ended: ${formatTimeAgo(session.end_time)}`
                              : `Started: ${formatTimeAgo(session.start_time)}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Badge className={getStatusColor(session.status)}>
                          {session.status.toUpperCase()}
                        </Badge>
                        <div className="text-sm text-gray-500">
                          {session.duration_seconds &&
                            formatDuration(session.duration_seconds)}
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ConcurrentUsageMonitor;
