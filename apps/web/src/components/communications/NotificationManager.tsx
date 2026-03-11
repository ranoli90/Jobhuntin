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
import { Switch } from "@/components/ui/Switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { Progress } from "@/components/ui/Progress";
import {
  Bell,
  Send,
  Clock,
  CheckCircle,
  AlertTriangle,
  Settings,
  RefreshCw,
  Eye,
  EyeOff,
  Filter,
  Search,
  Trash2,
  Volume2,
  VolumeX,
  Smartphone,
  Mail,
  MessageSquare,
} from "lucide-react";

interface Notification {
  id: string;
  title: string;
  message: string;
  category: string;
  priority: string;
  channels: string[];
  is_read: boolean;
  data: Record<string, any>;
  expires_at: string | null;
  created_at: string;
}

interface NotificationPreferences {
  user_id: string;
  tenant_id: string;
  in_app_enabled: boolean;
  email_enabled: boolean;
  push_enabled: boolean;
  sms_enabled: boolean;
  categories: Record<string, Record<string, boolean>>;
  do_not_disturb_enabled: boolean;
  do_not_disturb_start: string | null;
  do_not_disturb_end: string | null;
  updated_at: string;
}

interface NotificationStats {
  total: number;
  unread: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  last_24h: number;
  last_7d: number;
}

const NotificationManager: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [preferences, setPreferences] =
    useState<NotificationPreferences | null>(null);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [showCompose, setShowCompose] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Compose form state
  const [composeForm, setComposeForm] = useState({
    title: "",
    message: "",
    category: "general",
    priority: "medium",
    channels: ["in_app"],
    data: {} as Record<string, any>,
  });

  // Preferences form state
  const [preferencesForm, setPreferencesForm] = useState({
    in_app_enabled: true,
    email_enabled: true,
    push_enabled: true,
    sms_enabled: false,
    categories: {} as Record<string, Record<string, boolean>>,
    do_not_disturb_enabled: false,
    do_not_disturb_start: "",
    do_not_disturb_end: "",
  });

  useEffect(() => {
    fetchNotifications();
    fetchPreferences();
    fetchStats();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchNotifications();
        fetchStats();
      }, 15_000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedCategory, unreadOnly]);

  const fetchNotifications = async () => {
    try {
      const parameters = new URLSearchParams({
        limit: "50",
        category: selectedCategory === "all" ? "" : selectedCategory,
        unread_only: unreadOnly.toString(),
      });

      const response = await fetch(
        `/api/communications/notifications?${parameters}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to fetch notifications");
      const data = await response.json();
      setNotifications(data.notifications || []);
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to fetch notifications",
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchPreferences = async () => {
    try {
      const response = await fetch("/api/communications/preferences", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch preferences");
      const data = await response.json();
      setPreferences(data);
      setPreferencesForm({
        in_app_enabled: data.in_app_enabled,
        email_enabled: data.email_enabled,
        push_enabled: data.push_enabled,
        sms_enabled: data.sms_enabled,
        categories: data.categories,
        do_not_disturb_enabled: data.do_not_disturb_enabled,
        do_not_disturb_start: data.do_not_disturb_start || "",
        do_not_disturb_end: data.do_not_disturb_end || "",
      });
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to fetch preferences",
      );
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/communications/notifications/stats", {
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

  const handleSendNotification = async () => {
    try {
      const response = await fetch("/api/communications/notifications/send", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(composeForm),
      });

      if (!response.ok) throw new Error("Failed to send notification");

      await fetchNotifications();
      await fetchStats();
      setShowCompose(false);
      setComposeForm({
        title: "",
        message: "",
        category: "general",
        priority: "medium",
        channels: ["in_app"],
        data: {},
      });
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to send notification",
      );
    }
  };

  const handleUpdatePreferences = async () => {
    try {
      const response = await fetch("/api/communications/preferences", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(preferencesForm),
      });

      if (!response.ok) throw new Error("Failed to update preferences");

      await fetchPreferences();
      setShowPreferences(false);
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to update preferences",
      );
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      const response = await fetch(
        `/api/communications/notifications/${notificationId}/read`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to mark as read");

      await fetchNotifications();
      await fetchStats();
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to mark as read",
      );
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      const parameters = new URLSearchParams({
        category: selectedCategory === "all" ? "" : selectedCategory,
      });

      const response = await fetch(
        `/api/communications/notifications/read-all?${parameters}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to mark all as read");

      await fetchNotifications();
      await fetchStats();
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to mark all as read",
      );
    }
  };

  const handleDeleteNotification = async (notificationId: string) => {
    if (!confirm("Are you sure you want to delete this notification?")) return;

    try {
      const response = await fetch(
        `/api/communications/notifications/${notificationId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to delete notification");

      await fetchNotifications();
      await fetchStats();
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to delete notification",
      );
    }
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      critical: "bg-red-100 text-red-800",
      high: "bg-orange-100 text-orange-800",
      medium: "bg-blue-100 text-blue-800",
      low: "bg-gray-100 text-gray-800",
    };
    return (
      colors[priority as keyof typeof colors] || "bg-gray-100 text-gray-800"
    );
  };

  const getChannelIcon = (channel: string) => {
    const icons = {
      in_app: <Bell className="h-4 w-4" />,
      email: <Mail className="h-4 w-4" />,
      push: <Smartphone className="h-4 w-4" />,
      sms: <MessageSquare className="h-4 w-4" />,
    };
    return icons[channel as keyof typeof icons] || <Bell className="h-4 w-4" />;
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

  const filteredNotifications =
    selectedCategory === "all"
      ? notifications
      : notifications.filter(
          (notification) => notification.category === selectedCategory,
        );

  const displayNotifications = unreadOnly
    ? filteredNotifications.filter((n) => !n.is_read)
    : filteredNotifications;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Notification Manager</h1>
          <p className="text-gray-600">Manage notifications and preferences</p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setShowCompose(true)}>
            <Bell className="h-4 w-4 mr-2" />
            Send Notification
          </Button>
          <Button variant="outline" onClick={() => setShowPreferences(true)}>
            <Settings className="h-4 w-4 mr-2" />
            Preferences
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

      {/* Notification Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Total Notifications
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-sm text-gray-500">All notifications</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Unread</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {stats.unread}
              </div>
              <div className="text-sm text-gray-500">Pending attention</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Critical</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {stats.critical}
              </div>
              <div className="text-sm text-gray-500">High priority</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Last 24h</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {stats.last_24h}
              </div>
              <div className="text-sm text-gray-500">Recent activity</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Notification Compose Modal */}
      {showCompose && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Send Notification</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  placeholder="Notification title"
                  value={composeForm.title}
                  onChange={(e) =>
                    setComposeForm({ ...composeForm, title: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message</Label>
                <Textarea
                  id="message"
                  placeholder="Notification message"
                  rows={4}
                  value={composeForm.message}
                  onChange={(e) =>
                    setComposeForm({ ...composeForm, message: e.target.value })
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={composeForm.category}
                    onValueChange={(value) =>
                      setComposeForm({ ...composeForm, category: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="application_status">
                        Application Status
                      </SelectItem>
                      <SelectItem value="job_matches">Job Matches</SelectItem>
                      <SelectItem value="security">Security</SelectItem>
                      <SelectItem value="marketing">Marketing</SelectItem>
                      <SelectItem value="usage_limits">Usage Limits</SelectItem>
                      <SelectItem value="reminders">Reminders</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priority">Priority</Label>
                  <Select
                    value={composeForm.priority}
                    onValueChange={(value) =>
                      setComposeForm({ ...composeForm, priority: value })
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
                <Label>Channels</Label>
                <div className="flex flex-wrap gap-2">
                  {["in_app", "email", "push", "sms"].map((channel) => (
                    <div key={channel} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={`channel-${channel}`}
                        checked={composeForm.channels.includes(channel)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setComposeForm({
                              ...composeForm,
                              channels: [...composeForm.channels, channel],
                            });
                          } else {
                            setComposeForm({
                              ...composeForm,
                              channels: composeForm.channels.filter(
                                (c) => c !== channel,
                              ),
                            });
                          }
                        }}
                      />
                      <Label
                        htmlFor={`channel-${channel}`}
                        className="flex items-center space-x-1"
                      >
                        {getChannelIcon(channel)}
                        <span className="capitalize">{channel}</span>
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={handleSendNotification}
                  disabled={!composeForm.title || !composeForm.message}
                >
                  <Send className="h-4 w-4 mr-2" />
                  Send Notification
                </Button>
                <Button variant="outline" onClick={() => setShowCompose(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notification Preferences Modal */}
      {showPreferences && preferences && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Notification Preferences</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium">Channel Preferences</h4>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Bell className="h-4 w-4" />
                    <Switch
                      id="in-app-enabled"
                      checked={preferencesForm.in_app_enabled}
                      onCheckedChange={(checked) =>
                        setPreferencesForm({
                          ...preferencesForm,
                          in_app_enabled: checked,
                        })
                      }
                    />
                    <Label htmlFor="in-app-enabled">In-App Notifications</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Mail className="h-4 w-4" />
                    <Switch
                      id="email-enabled"
                      checked={preferencesForm.email_enabled}
                      onCheckedChange={(checked) =>
                        setPreferencesForm({
                          ...preferencesForm,
                          email_enabled: checked,
                        })
                      }
                    />
                    <Label htmlFor="email-enabled">Email Notifications</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Smartphone className="h-4 w-4" />
                    <Switch
                      id="push-enabled"
                      checked={preferencesForm.push_enabled}
                      onCheckedChange={(checked) =>
                        setPreferencesForm({
                          ...preferencesForm,
                          push_enabled: checked,
                        })
                      }
                    />
                    <Label htmlFor="push-enabled">Push Notifications</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <MessageSquare className="h-4 w-4" />
                    <Switch
                      id="sms-enabled"
                      checked={preferencesForm.sms_enabled}
                      onCheckedChange={(checked) =>
                        setPreferencesForm({
                          ...preferencesForm,
                          sms_enabled: checked,
                        })
                      }
                    />
                    <Label htmlFor="sms-enabled">SMS Notifications</Label>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Category Preferences</h4>
                <div className="space-y-2">
                  {Object.entries(preferencesForm.categories).map(
                    ([category, channels]) => (
                      <div key={category} className="border rounded-lg p-3">
                        <div className="font-medium capitalize mb-2">
                          {category.replace("_", " ")}
                        </div>
                        <div className="space-y-1">
                          {Object.entries(channels).map(
                            ([channel, enabled]) => (
                              <div
                                key={channel}
                                className="flex items-center space-x-2"
                              >
                                <Switch
                                  id={`category-${category}-${channel}`}
                                  checked={enabled}
                                  onCheckedChange={(checked) => {
                                    setPreferencesForm({
                                      ...preferencesForm,
                                      categories: {
                                        ...preferencesForm.categories,
                                        [category]: {
                                          ...preferencesForm.categories[
                                            category
                                          ],
                                          [channel]: checked,
                                        },
                                      },
                                    });
                                  }}
                                />
                                <Label
                                  htmlFor={`category-${category}-${channel}`}
                                  className="flex items-center space-x-1"
                                >
                                  {getChannelIcon(channel)}
                                  <span className="capitalize">{channel}</span>
                                </Label>
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    ),
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Do Not Disturb</h4>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="dnd-enabled"
                    checked={preferencesForm.do_not_disturb_enabled}
                    onCheckedChange={(checked) =>
                      setPreferencesForm({
                        ...preferencesForm,
                        do_not_disturb_enabled: checked,
                      })
                    }
                  />
                  <Label htmlFor="dnd-enabled">Enable Do Not Disturb</Label>
                </div>

                {preferencesForm.do_not_disturb_enabled && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="dnd-start">Start Time</Label>
                      <Input
                        id="dnd-start"
                        type="time"
                        value={preferencesForm.do_not_disturb_start}
                        onChange={(e) =>
                          setPreferencesForm({
                            ...preferencesForm,
                            do_not_disturb_start: e.target.value,
                          })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="dnd-end">End Time</Label>
                      <Input
                        id="dnd-end"
                        type="time"
                        value={preferencesForm.do_not_disturb_end}
                        onChange={(e) =>
                          setPreferencesForm({
                            ...preferencesForm,
                            do_not_disturb_end: e.target.value,
                          })
                        }
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="flex space-x-2">
                <Button onClick={handleUpdatePreferences}>
                  <Settings className="h-4 w-4 mr-2" />
                  Update Preferences
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowPreferences(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            <Button
              variant={selectedCategory === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory("all")}
            >
              All Categories
            </Button>
            {[
              "application_status",
              "job_matches",
              "security",
              "marketing",
              "usage_limits",
              "reminders",
            ].map((category) => (
              <Button
                key={category}
                variant={selectedCategory === category ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category)}
              >
                {category.replace("_", " ")}
              </Button>
            ))}
            <Button
              variant={unreadOnly ? "default" : "outline"}
              size="sm"
              onClick={() => setUnreadOnly(!unreadOnly)}
            >
              {unreadOnly ? (
                <EyeOff className="h-4 w-4 mr-1" />
              ) : (
                <Eye className="h-4 w-4 mr-1" />
              )}
              {unreadOnly ? "All" : "Unread"}
            </Button>
            {displayNotifications.some((n) => !n.is_read) && (
              <Button variant="outline" size="sm" onClick={handleMarkAllAsRead}>
                Mark All Read
              </Button>
            )}
          </div>

          <div className="space-y-4">
            {displayNotifications.map((notification) => (
              <Card
                key={notification.id}
                className={`p-4 ${notification.is_read ? "opacity-60" : ""}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium">{notification.title}</h4>
                        <Badge
                          className={getPriorityColor(notification.priority)}
                        >
                          {notification.priority}
                        </Badge>
                        {notification.is_read && (
                          <Badge variant="outline">Read</Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {notification.message}
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge variant="outline" className="text-xs">
                          {notification.category}
                        </Badge>
                        {notification.channels.map((channel) => (
                          <div
                            key={channel}
                            className="flex items-center space-x-1"
                          >
                            {getChannelIcon(channel)}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="text-sm text-gray-500">
                      {formatTimeAgo(notification.created_at)}
                    </div>
                    <div className="flex space-x-1">
                      {!notification.is_read && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMarkAsRead(notification.id)}
                        >
                          <CheckCircle className="h-3 w-3" />
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          handleDeleteNotification(notification.id)
                        }
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {displayNotifications.length === 0 && (
            <div className="text-center py-8">
              <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {unreadOnly
                  ? "No unread notifications"
                  : "No notifications yet"}
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Click "Send Notification" to create your first notification
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default NotificationManager;
