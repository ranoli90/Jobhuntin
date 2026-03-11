import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Textarea } from "@/components/ui/Textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { Progress } from "@/components/ui/Progress";
import { Switch } from "@/components/ui/Switch";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Settings,
  RefreshCw,
  Search,
  Filter,
  Trash2,
  Play,
  Pause,
  RotateCcw,
  Shield,
  Activity,
  Zap,
  AlertCircle,
} from "lucide-react";

interface Alert {
  id: string;
  type: string;
  priority: string;
  title: string;
  message: string;
  status: string;
  data: Record<string, any>;
  context: Record<string, any>;
  processed_at: string | null;
  created_at: string;
}

interface AlertRule {
  id: string;
  name: string;
  alert_type: string;
  conditions: Record<string, any>;
  actions: string[];
  priority: string;
  enabled: boolean;
  throttle_minutes: number;
  created_at: string;
  updated_at: string;
}

interface AlertStats {
  total_alerts: number;
  processed: number;
  failed: number;
  resolved: number;
  last_24h: number;
  last_7d: number;
}

const AlertProcessor: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [showCreateRule, setShowCreateRule] = useState(false);
  const [showCreateAlert, setShowCreateAlert] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Create alert form state
  const [alertForm, setAlertForm] = useState({
    type: "system_error",
    priority: "medium",
    title: "",
    message: "",
    data: {} as Record<string, any>,
    context: {} as Record<string, any>,
  });

  // Create rule form state
  const [ruleForm, setRuleForm] = useState({
    name: "",
    alert_type: "system_error",
    conditions: {} as Record<string, any>,
    actions: ["send_notification"],
    priority: "medium",
    enabled: true,
    throttle_minutes: 5,
  });

  useEffect(() => {
    fetchAlerts();
    fetchRules();
    fetchStats();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchAlerts();
        fetchStats();
      }, 20_000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedType, selectedStatus]);

  const fetchAlerts = async () => {
    try {
      const parameters = new URLSearchParams({
        limit: "50",
        alert_type: selectedType === "all" ? "" : selectedType,
        status: selectedStatus === "all" ? "" : selectedStatus,
      });

      const response = await fetch(
        `/api/communications/alerts/history?${parameters}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to fetch alerts");
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to fetch alerts",
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchRules = async () => {
    try {
      const response = await fetch("/api/communications/alerts/rules", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch rules");
      const data = await response.json();
      setRules(data.rules || []);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to fetch rules",
      );
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/communications/alerts/stats", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch stats");
      const data = await response.json();
      setStats(data.stats);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to fetch stats",
      );
    }
  };

  const handleCreateAlert = async () => {
    try {
      const response = await fetch("/api/communications/alerts/process", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(alertForm),
      });

      if (!response.ok) throw new Error("Failed to create alert");

      await fetchAlerts();
      await fetchStats();
      setShowCreateAlert(false);
      setAlertForm({
        type: "system_error",
        priority: "medium",
        title: "",
        message: "",
        data: {},
        context: {},
      });
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to create alert",
      );
    }
  };

  const handleCreateRule = async () => {
    try {
      const response = await fetch("/api/communications/alerts/rules", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(ruleForm),
      });

      if (!response.ok) throw new Error("Failed to create rule");

      await fetchRules();
      setShowCreateRule(false);
      setRuleForm({
        name: "",
        alert_type: "system_error",
        conditions: {},
        actions: ["send_notification"],
        priority: "medium",
        enabled: true,
        throttle_minutes: 5,
      });
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to create rule",
      );
    }
  };

  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      const response = await fetch(
        `/api/communications/alerts/rules/${ruleId}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ enabled }),
        },
      );

      if (!response.ok) throw new Error("Failed to update rule");

      await fetchRules();
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to update rule",
      );
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm("Are you sure you want to delete this alert rule?")) return;

    try {
      const response = await fetch(
        `/api/communications/alerts/rules/${ruleId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to delete rule");

      await fetchRules();
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to delete rule",
      );
    }
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      critical: "bg-red-100 text-red-800",
      high: "bg-orange-100 text-orange-800",
      medium: "bg-yellow-100 text-yellow-800",
      low: "bg-blue-100 text-blue-800",
    };
    return (
      colors[priority as keyof typeof colors] || "bg-gray-100 text-gray-800"
    );
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: "bg-yellow-100 text-yellow-800",
      processed: "bg-green-100 text-green-800",
      failed: "bg-red-100 text-red-800",
      resolved: "bg-blue-100 text-blue-800",
    };
    return colors[status as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      pending: <Clock className="h-4 w-4" />,
      processed: <CheckCircle className="h-4 w-4" />,
      failed: <AlertTriangle className="h-4 w-4" />,
      resolved: <CheckCircle className="h-4 w-4" />,
    };
    return icons[status as keyof typeof icons] || <Clock className="h-4 w-4" />;
  };

  const getTypeIcon = (type: string) => {
    const icons = {
      application_success: <CheckCircle className="h-4 w-4 text-green-600" />,
      application_failed: <AlertTriangle className="h-4 w-4 text-red-600" />,
      rate_limit_warning: <AlertCircle className="h-4 w-4 text-yellow-600" />,
      rate_limit_reached: <AlertTriangle className="h-4 w-4 text-orange-600" />,
      security_alert: <Shield className="h-4 w-4 text-red-600" />,
      system_error: <AlertTriangle className="h-4 w-4 text-red-600" />,
      maintenance: <Settings className="h-4 w-4 text-blue-600" />,
    };
    return (
      icons[type as keyof typeof icons] || <AlertTriangle className="h-4 w-4" />
    );
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

  const filteredAlerts = alerts.filter((alert) => {
    const typeMatch = selectedType === "all" || alert.type === selectedType;
    const statusMatch =
      selectedStatus === "all" || alert.status === selectedStatus;
    return typeMatch && statusMatch;
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Alert Processor</h1>
          <p className="text-gray-600">Manage alert rules and processing</p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setShowCreateAlert(true)}>
            <AlertTriangle className="h-4 w-4 mr-2" />
            Create Alert
          </Button>
          <Button variant="outline" onClick={() => setShowCreateRule(true)}>
            <Settings className="h-4 w-4 mr-2" />
            Create Rule
          </Button>
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
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Alert Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Total Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_alerts}</div>
              <div className="text-sm text-gray-500">All alerts</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Processed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {stats.processed}
              </div>
              <div className="text-sm text-gray-500">
                Successfully processed
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {stats.failed}
              </div>
              <div className="text-sm text-gray-500">Processing failed</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Last 24h</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {stats.last_24h}
              </div>
              <div className="text-sm text-gray-500">Recent activity</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Alert Modal */}
      {showCreateAlert && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Create Alert</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="alert-type">Alert Type</Label>
                  <Select
                    value={alertForm.type}
                    onValueChange={(value) =>
                      setAlertForm({ ...alertForm, type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="application_success">
                        Application Success
                      </SelectItem>
                      <SelectItem value="application_failed">
                        Application Failed
                      </SelectItem>
                      <SelectItem value="rate_limit_warning">
                        Rate Limit Warning
                      </SelectItem>
                      <SelectItem value="rate_limit_reached">
                        Rate Limit Reached
                      </SelectItem>
                      <SelectItem value="security_alert">
                        Security Alert
                      </SelectItem>
                      <SelectItem value="system_error">System Error</SelectItem>
                      <SelectItem value="maintenance">Maintenance</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priority">Priority</Label>
                  <Select
                    value={alertForm.priority}
                    onValueChange={(value) =>
                      setAlertForm({ ...alertForm, priority: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  placeholder="Alert title"
                  value={alertForm.title}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setAlertForm({ ...alertForm, title: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message</Label>
                <Textarea
                  id="message"
                  placeholder="Alert message"
                  rows={4}
                  value={alertForm.message}
                  onChange={(e) =>
                    setAlertForm({ ...alertForm, message: e.target.value })
                  }
                />
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={handleCreateAlert}
                  disabled={!alertForm.title || !alertForm.message}
                >
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Create Alert
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowCreateAlert(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create Rule Modal */}
      {showCreateRule && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Create Alert Rule</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="rule-name">Rule Name</Label>
                <Input
                  id="rule-name"
                  placeholder="Rule name"
                  value={ruleForm.name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setRuleForm({ ...ruleForm, name: e.target.value })
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="rule-alert-type">Alert Type</Label>
                  <Select
                    value={ruleForm.alert_type}
                    onValueChange={(value) =>
                      setRuleForm({ ...ruleForm, alert_type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="application_success">
                        Application Success
                      </SelectItem>
                      <SelectItem value="application_failed">
                        Application Failed
                      </SelectItem>
                      <SelectItem value="rate_limit_warning">
                        Rate Limit Warning
                      </SelectItem>
                      <SelectItem value="rate_limit_reached">
                        Rate Limit Reached
                      </SelectItem>
                      <SelectItem value="security_alert">
                        Security Alert
                      </SelectItem>
                      <SelectItem value="system_error">System Error</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="rule-priority">Priority</Label>
                  <Select
                    value={ruleForm.priority}
                    onValueChange={(value) =>
                      setRuleForm({ ...ruleForm, priority: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="rule-throttle">Throttle Minutes</Label>
                <Input
                  id="rule-throttle"
                  type="number"
                  min="1"
                  max="1440"
                  placeholder="Throttle in minutes"
                  value={ruleForm.throttle_minutes}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setRuleForm({
                      ...ruleForm,
                      throttle_minutes: Number.parseInt(e.target.value) || 5,
                    })
                  }
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="rule-enabled"
                  checked={ruleForm.enabled}
                  onCheckedChange={(checked: boolean) =>
                    setRuleForm({ ...ruleForm, enabled: checked })
                  }
                />
                <Label htmlFor="rule-enabled">Enable Rule</Label>
              </div>

              <div className="flex space-x-2">
                <Button onClick={handleCreateRule} disabled={!ruleForm.name}>
                  <Settings className="h-4 w-4 mr-2" />
                  Create Rule
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowCreateRule(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alert Rules */}
      <Card>
        <CardHeader>
          <CardTitle>Alert Rules</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {rules.map((rule) => (
              <Card key={rule.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="flex-1">
                      <h4 className="font-medium">{rule.name}</h4>
                      <p className="text-sm text-gray-500">
                        Type: {rule.alert_type.replace("_", " ")}
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge className={getPriorityColor(rule.priority)}>
                          {rule.priority}
                        </Badge>
                        <Badge variant={rule.enabled ? "default" : "outline"}>
                          {rule.enabled ? "Enabled" : "Disabled"}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleToggleRule(rule.id, !rule.enabled)}
                    >
                      {rule.enabled ? (
                        <Pause className="h-3 w-3" />
                      ) : (
                        <Play className="h-3 w-3" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDeleteRule(rule.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}

            {rules.length === 0 && (
              <div className="text-center py-8">
                <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No alert rules configured</p>
                <p className="text-sm text-gray-400 mt-2">
                  Click "Create Rule" to set up alert processing
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Alerts History */}
      <Card>
        <CardHeader>
          <CardTitle>Alert History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            <div className="flex items-center space-x-2">
              <Label>Type:</Label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="application_success">
                    Application Success
                  </SelectItem>
                  <SelectItem value="application_failed">
                    Application Failed
                  </SelectItem>
                  <SelectItem value="rate_limit_warning">
                    Rate Limit Warning
                  </SelectItem>
                  <SelectItem value="rate_limit_reached">
                    Rate Limit Reached
                  </SelectItem>
                  <SelectItem value="security_alert">Security Alert</SelectItem>
                  <SelectItem value="system_error">System Error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2">
              <Label>Status:</Label>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="processed">Processed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-4">
            {filteredAlerts.map((alert) => (
              <Card key={alert.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getTypeIcon(alert.type)}
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium">{alert.title}</h4>
                        <Badge className={getPriorityColor(alert.priority)}>
                          {alert.priority}
                        </Badge>
                        <Badge className={getStatusColor(alert.status)}>
                          {alert.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {alert.message}
                      </p>
                      <div className="text-xs text-gray-500 mt-2">
                        Created: {formatTimeAgo(alert.created_at)}
                        {alert.processed_at && (
                          <span className="ml-2">
                            Processed: {formatTimeAgo(alert.processed_at)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {filteredAlerts.length === 0 && (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No alerts found</p>
              <p className="text-sm text-gray-400 mt-2">
                Alerts will appear here when triggered
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AlertProcessor;
