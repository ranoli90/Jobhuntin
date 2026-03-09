/**
 * Notification Center Page - Centralize user notifications
 * Microsoft-level implementation with real-time updates and comprehensive notification management
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { 
  Bell, 
  BellOff, 
  Check, 
  X, 
  Filter,
  Search,
  Archive,
  Trash2,
  Eye,
  EyeOff,
  Clock,
  User,
  Briefcase,
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  Info,
  Star,
  Settings,
  RefreshCw
} from "lucide-react";

export default function NotificationCenterPage() {
  const { t } = useTranslation();
  const locale = localStorage.getItem("language") || "en";
  const queryClient = useQueryClient();

  // State
  const [selectedFilter, setSelectedFilter] = React.useState<"all" | "unread" | "read" | "archived">("all");
  const [selectedType, setSelectedType] = React.useState<string>("all");
  const [searchTerm, setSearchTerm] = React.useState("");
  const [selectedNotifications, setSelectedNotifications] = React.useState<Set<string>>(new Set());

  // Mock notification data (would come from API)
  const mockNotifications = [
    {
      id: "1",
      type: "application_status",
      title: "Application Status Update",
      message: "Your application for Senior Software Engineer at TechCorp has been viewed",
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
      read: false,
      archived: false,
      priority: "medium",
      action_url: "/applications/123",
      metadata: {
        company: "TechCorp",
        job_title: "Senior Software Engineer",
        application_id: "123"
      }
    },
    {
      id: "2",
      type: "interview_scheduled",
      title: "Interview Scheduled",
      message: "You have an interview scheduled for tomorrow at 2:00 PM with StartupXYZ",
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
      read: false,
      archived: false,
      priority: "high",
      action_url: "/interviews/456",
      metadata: {
        company: "StartupXYZ",
        time: "2:00 PM",
        date: "Tomorrow"
      }
    },
    {
      id: "3",
      type: "job_alert",
      title: "New Job Match",
      message: "5 new jobs match your saved search criteria for React Developer",
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
      read: true,
      archived: false,
      priority: "low",
      action_url: "/jobs?search=react",
      metadata: {
        job_count: 5,
        search_term: "React Developer"
      }
    },
    {
      id: "4",
      type: "career_insight",
      title: "Career Insight Available",
      message: "Your career path analysis is ready with personalized recommendations",
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
      read: true,
      archived: false,
      priority: "medium",
      action_url: "/career-path",
      metadata: {
        analysis_type: "career_path"
      }
    },
    {
      id: "5",
      type: "system_update",
      title: "System Update",
      message: "New features have been added to improve your job search experience",
      timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000), // 2 days ago
      read: true,
      archived: true,
      priority: "low",
      action_url: "/whats-new",
      metadata: {
        update_version: "2.1.0"
      }
    }
  ];

  // Fetch notifications (would be from API)
  const {
    data: notifications = mockNotifications,
    isLoading,
    error,
    refetch: refetchNotifications,
  } = useQuery({
    queryKey: ["notifications", selectedFilter, selectedType, searchTerm],
    queryFn: async () => {
      // return await apiGet(`notifications?filter=${selectedFilter}&type=${selectedType}&search=${searchTerm}`);
      return mockNotifications; // Mock for demo
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: async (notificationIds: string[]) => {
      // return await apiPatch("notifications/mark-read", { notification_ids: notificationIds });
      console.log("Marking notifications as read:", notificationIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      setSelectedNotifications(new Set());
    },
  });

  // Archive mutation
  const archiveMutation = useMutation({
    mutationFn: async (notificationIds: string[]) => {
      // return await apiPatch("notifications/archive", { notification_ids: notificationIds });
      console.log("Archiving notifications:", notificationIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      setSelectedNotifications(new Set());
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (notificationIds: string[]) => {
      // return await apiDelete("notifications", { notification_ids: notificationIds });
      console.log("Deleting notifications:", notificationIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      setSelectedNotifications(new Set());
    },
  });

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation({
    mutationFn: async () => {
      // return await apiPatch("notifications/mark-all-read");
      console.log("Marking all notifications as read");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  // Filter notifications
  const filteredNotifications = React.useMemo(() => {
    let filtered = notifications;

    // Apply status filter
    if (selectedFilter === "unread") {
      filtered = filtered.filter(n => !n.read);
    } else if (selectedFilter === "read") {
      filtered = filtered.filter(n => n.read);
    } else if (selectedFilter === "archived") {
      filtered = filtered.filter(n => n.archived);
    }

    // Apply type filter
    if (selectedType !== "all") {
      filtered = filtered.filter(n => n.type === selectedType);
    }

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(n => 
        n.title.toLowerCase().includes(searchLower) ||
        n.message.toLowerCase().includes(searchLower)
      );
    }

    return filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }, [notifications, selectedFilter, selectedType, searchTerm]);

  // Get notification type icon
  const getNotificationIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      application_status: <Briefcase className="w-5 h-5" />,
      interview_scheduled: <CheckCircle className="w-5 h-5" />,
      job_alert: <Star className="w-5 h-5" />,
      career_insight: <User className="w-5 h-5" />,
      system_update: <Info className="w-5 h-5" />,
    };
    return icons[type] || <Bell className="w-5 h-5" />;
  };

  // Get notification type color
  const getNotificationColor = (type: string) => {
    const colors: Record<string, string> = {
      application_status: "text-blue-600 bg-blue-100",
      interview_scheduled: "text-green-600 bg-green-100",
      job_alert: "text-yellow-600 bg-yellow-100",
      career_insight: "text-purple-600 bg-purple-100",
      system_update: "text-slate-600 bg-slate-100",
    };
    return colors[type] || "text-slate-600 bg-slate-100";
  };

  // Get priority color
  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      high: "text-red-600 bg-red-100",
      medium: "text-yellow-600 bg-yellow-100",
      low: "text-slate-600 bg-slate-100",
    };
    return colors[priority] || "text-slate-600 bg-slate-100";
  };

  // Format timestamp
  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) {
      return t("notificationCenter.minutesAgo", locale, { count: diffMins }) || `${diffMins} minutes ago`;
    } else if (diffHours < 24) {
      return t("notificationCenter.hoursAgo", locale, { count: diffHours }) || `${diffHours} hours ago`;
    } else {
      return t("notificationCenter.daysAgo", locale, { count: diffDays }) || `${diffDays} days ago`;
    }
  };

  // Handlers
  const handleSelectNotification = (id: string) => {
    setSelectedNotifications(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedNotifications.size === filteredNotifications.length) {
      setSelectedNotifications(new Set());
    } else {
      setSelectedNotifications(new Set(filteredNotifications.map(n => n.id)));
    }
  };

  const handleMarkAsRead = () => {
    if (selectedNotifications.size > 0) {
      markAsReadMutation.mutate(Array.from(selectedNotifications));
    }
  };

  const handleArchive = () => {
    if (selectedNotifications.size > 0) {
      archiveMutation.mutate(Array.from(selectedNotifications));
    }
  };

  const handleDelete = () => {
    if (selectedNotifications.size > 0) {
      if (window.confirm(t("notificationCenter.confirmDelete", locale) || "Are you sure you want to delete these notifications?")) {
        deleteMutation.mutate(Array.from(selectedNotifications));
      }
    }
  };

  const handleMarkAllAsRead = () => {
    markAllAsReadMutation.mutate();
  };

  const handleNotificationClick = (notification: any) => {
    if (!notification.read) {
      markAsReadMutation.mutate([notification.id]);
    }
    // Navigate to action URL if exists
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  const notificationTypes = [
    { value: "all", label: t("notificationCenter.allTypes", locale) || "All Types" },
    { value: "application_status", label: t("notificationCenter.applicationStatus", locale) || "Application Status" },
    { value: "interview_scheduled", label: t("notificationCenter.interviewScheduled", locale) || "Interview Scheduled" },
    { value: "job_alert", label: t("notificationCenter.jobAlert", locale) || "Job Alerts" },
    { value: "career_insight", label: t("notificationCenter.careerInsight", locale) || "Career Insights" },
    { value: "system_update", label: t("notificationCenter.systemUpdate", locale) || "System Updates" },
  ];

  const filterOptions = [
    { value: "all", label: t("notificationCenter.all", locale) || "All" },
    { value: "unread", label: t("notificationCenter.unread", locale) || "Unread" },
    { value: "read", label: t("notificationCenter.read", locale) || "Read" },
    { value: "archived", label: t("notificationCenter.archived", locale) || "Archived" },
  ];

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="p-6 text-center">
          <Bell className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-red-600 mb-2">
            {t("notificationCenter.errorLoading", locale) || "Error Loading Notifications"}
          </h2>
          <p className="text-slate-600">{error instanceof Error ? error.message : String(error)}</p>
          <Button onClick={() => refetchNotifications()}>
            {t("common.retry", locale) || "Retry"}
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">
            {t("notificationCenter.title", locale) || "Notification Center"}
          </h1>
          <p className="text-slate-500 font-medium">
            {t("notificationCenter.description", locale) || "Manage your notifications and stay updated on your job search progress"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleMarkAllAsRead}
            disabled={markAllAsReadMutation.isPending}
          >
            <Check className="w-4 h-4 mr-2" />
            {t("notificationCenter.markAllRead", locale) || "Mark All Read"}
          </Button>
          <Button variant="outline" onClick={() => refetchNotifications()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            {t("common.refresh", locale) || "Refresh"}
          </Button>
        </div>
      </div>

      {/* Filters and Search */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder={t("notificationCenter.searchPlaceholder", locale) || "Search notifications..."}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value as any)}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {filterOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {notificationTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Bulk Actions */}
      {selectedNotifications.size > 0 && (
        <Card className="p-4 bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-blue-900">
                {selectedNotifications.size} {t("notificationCenter.selected", locale) || "selected"}
              </span>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleMarkAsRead}
                disabled={markAsReadMutation.isPending}
              >
                <Check className="w-4 h-4 mr-2" />
                {t("notificationCenter.markRead", locale) || "Mark Read"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleArchive}
                disabled={archiveMutation.isPending}
              >
                <Archive className="w-4 h-4 mr-2" />
                {t("notificationCenter.archive", locale) || "Archive"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                {t("common.delete", locale) || "Delete"}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Notifications List */}
      <div className="space-y-2">
        {filteredNotifications.length === 0 ? (
          <Card className="p-8 text-center">
            <BellOff className="w-12 h-12 mx-auto text-slate-300 mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              {t("notificationCenter.noNotifications", locale) || "No Notifications"}
            </h3>
            <p className="text-slate-600">
              {t("notificationCenter.noNotificationsDescription", locale) || "You're all caught up! No notifications to display."}
            </p>
          </Card>
        ) : (
          <div className="space-y-2">
            {/* Select All Checkbox */}
            <div className="flex items-center p-3 bg-slate-50 rounded-lg">
              <input
                type="checkbox"
                checked={selectedNotifications.size === filteredNotifications.length}
                onChange={handleSelectAll}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
              />
              <span className="ml-2 text-sm font-medium text-slate-700">
                {t("notificationCenter.selectAll", locale) || "Select All"}
              </span>
            </div>

            {/* Notification Items */}
            {filteredNotifications.map((notification) => (
              <Card
                key={notification.id}
                className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                  !notification.read ? "bg-blue-50 border-blue-200" : ""
                } ${selectedNotifications.has(notification.id) ? "ring-2 ring-primary-500" : ""}`}
                onClick={() => handleNotificationClick(notification)}
              >
                <div className="flex items-start gap-4">
                  {/* Checkbox */}
                  <input
                    type="checkbox"
                    checked={selectedNotifications.has(notification.id)}
                    onChange={() => handleSelectNotification(notification.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded mt-1"
                  />

                  {/* Icon */}
                  <div className={`p-2 rounded-full ${getNotificationColor(notification.type)}`}>
                    {getNotificationIcon(notification.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900 mb-1">
                          {notification.title}
                        </h3>
                        <p className="text-slate-600">{notification.message}</p>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Badge variant="outline" className={getPriorityColor(notification.priority)}>
                          {notification.priority}
                        </Badge>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        )}
                      </div>
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center justify-between text-sm text-slate-500">
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {formatTimestamp(notification.timestamp)}
                        </span>
                        {notification.metadata?.company && (
                          <span className="flex items-center gap-1">
                            <Briefcase className="w-4 h-4" />
                            {notification.metadata.company}
                          </span>
                        )}
                      </div>
                      {notification.action_url && (
                        <span className="text-primary-600 hover:text-primary-700">
                          {t("notificationCenter.viewDetails", locale) || "View Details"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Notification Settings */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-900">
            {t("notificationCenter.settings", locale) || "Notification Settings"}
          </h2>
          <Button variant="outline">
            <Settings className="w-4 h-4 mr-2" />
            {t("notificationCenter.configure", locale) || "Configure"}
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
            <div>
              <h4 className="font-medium text-slate-900">
                {t("notificationCenter.emailNotifications", locale) || "Email Notifications"}
              </h4>
              <p className="text-sm text-slate-600">
                {t("notificationCenter.emailDescription", locale) || "Receive notifications via email"}
              </p>
            </div>
            <input
              type="checkbox"
              defaultChecked={true}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
            />
          </div>
          <div className="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
            <div>
              <h4 className="font-medium text-slate-900">
                {t("notificationCenter.pushNotifications", locale) || "Push Notifications"}
              </h4>
              <p className="text-sm text-slate-600">
                {t("notificationCenter.pushDescription", locale) || "Receive browser push notifications"}
              </p>
            </div>
            <input
              type="checkbox"
              defaultChecked={true}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
            />
          </div>
        </div>
      </Card>
    </div>
  );
}
