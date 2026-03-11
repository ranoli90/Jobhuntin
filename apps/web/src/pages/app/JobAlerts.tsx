/**
 * Job Alerts Page - User-facing job alert management
 * Microsoft-level implementation with real-time updates and comprehensive alert management
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPatch, apiDelete } from "../../lib/api";
import { formatCurrency } from "../../lib/format";
import { Button } from "../../components/ui/Button";

interface JobAlert {
  id: string;
  name: string;
  keywords: string[];
  locations: string[];
  salary_min?: number;
  salary_max?: number;
  is_active: boolean;
  frequency: string;
  remote_only?: boolean;
  last_sent_at?: string | number | Date;
  [key: string]: unknown;
}
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { FocusTrap } from "focus-trap-react";
import {
  Bell,
  BellOff,
  Plus,
  Trash2,
  Search,
  Filter,
  Edit,
  Check,
  Clock,
  MapPin,
  DollarSign,
  Building,
  AlertTriangle,
} from "lucide-react";

export default function JobAlertsPage() {
  const { t } = useTranslation();
  const locale = localStorage.getItem("language") || "en";
  const queryClient = useQueryClient();

  // State
  const [searchTerm, setSearchTerm] = React.useState("");
  const [showCreateForm, setShowCreateForm] = React.useState(false);
  const [editingAlert, setEditingAlert] = React.useState<string | null>(null);
  const [formData, setFormData] = React.useState({
    name: "",
    keywords: [] as string[],
    locations: [] as string[],
    salary_min: "",
    salary_max: "",
    companies_include: [] as string[],
    companies_exclude: [] as string[],
    job_types: [] as string[],
    remote_only: false,
    frequency: "daily",
  });

  // Fetch alerts
  const {
    data: alerts = [],
    isLoading,
    error,
    refetch: refetchAlerts,
  } = useQuery({
    queryKey: ["job-alerts"],
    queryFn: async () => {
      return await apiGet<JobAlert[]>("v1/alerts");
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Create alert mutation
  const createAlertMutation = useMutation({
    mutationFn: async (alertData: typeof formData) => {
      return await apiPost("v1/alerts", alertData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-alerts"] });
      setShowCreateForm(false);
      setFormData({
        name: "",
        keywords: [],
        locations: [],
        salary_min: "",
        salary_max: "",
        companies_include: [],
        companies_exclude: [],
        job_types: [],
        remote_only: false,
        frequency: "daily",
      });
    },
  });

  // Update alert mutation
  const updateAlertMutation = useMutation({
    mutationFn: async ({ id, ...data }: { id: string } & typeof formData) => {
      return await apiPatch(`v1/alerts/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-alerts"] });
      setEditingAlert(null);
    },
  });

  // Delete alert mutation
  const deleteAlertMutation = useMutation({
    mutationFn: async (alertId: string) => {
      return await apiDelete(`v1/alerts/${alertId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-alerts"] });
    },
  });

  // Toggle alert status mutation
  const toggleAlertMutation = useMutation({
    mutationFn: async ({ id, isActive }: { id: string; isActive: boolean }) => {
      return await apiPatch(`v1/alerts/${id}`, { is_active: isActive });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-alerts"] });
    },
  });

  // Filter alerts
  const filteredAlerts = React.useMemo(() => {
    if (!searchTerm) return alerts;

    const searchLower = searchTerm.toLowerCase();
    return alerts.filter(
      (alert) =>
        alert.name.toLowerCase().includes(searchLower) ||
        alert.keywords.some((keyword) =>
          keyword.toLowerCase().includes(searchLower),
        ) ||
        alert.locations.some((location) =>
          location.toLowerCase().includes(searchLower),
        ),
    );
  }, [alerts, searchTerm]);

  // Handlers
  const handleCreateAlert = () => {
    createAlertMutation.mutate(formData);
  };

  const handleEditAlert = (alert: any) => {
    setEditingAlert(alert.id);
    setShowCreateForm(true);
    setFormData({
      name: alert.name,
      keywords: alert.keywords,
      locations: alert.locations,
      salary_min: alert.salary_min || "",
      salary_max: alert.salary_max || "",
      companies_include: alert.companies_include || [],
      companies_exclude: alert.companies_exclude || [],
      job_types: alert.job_types || [],
      remote_only: alert.remote_only || false,
      frequency: alert.frequency,
    });
  };

  const handleUpdateAlert = () => {
    if (editingAlert) {
      updateAlertMutation.mutate({ id: editingAlert, ...formData });
    }
  };

  const handleDeleteAlert = (alertId: string) => {
    if (
      window.confirm(
        t("jobAlerts.confirmDelete", locale) ||
          "Are you sure you want to delete this alert?",
      )
    ) {
      deleteAlertMutation.mutate(alertId);
    }
  };

  const handleToggleAlert = (alertId: string, isActive: boolean) => {
    toggleAlertMutation.mutate({ id: alertId, isActive });
  };

  const addKeyword = (keyword: string) => {
    if (keyword && !formData.keywords.includes(keyword)) {
      setFormData((previous) => ({
        ...previous,
        keywords: [...previous.keywords, keyword],
      }));
    }
  };

  const removeKeyword = (index: number) => {
    setFormData((previous) => ({
      ...previous,
      keywords: previous.keywords.filter((_, index_) => index_ !== index),
    }));
  };

  const addLocation = (location: string) => {
    if (location && !formData.locations.includes(location)) {
      setFormData((previous) => ({
        ...previous,
        locations: [...previous.locations, location],
      }));
    }
  };

  const removeLocation = (index: number) => {
    setFormData((previous) => ({
      ...previous,
      locations: previous.locations.filter((_, index_) => index_ !== index),
    }));
  };

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
          <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-red-600 mb-2">
            {t("jobAlerts.errorLoading", locale) || "Error Loading Alerts"}
          </h2>
          <p className="text-slate-600">
            {error instanceof Error ? error.message : String(error)}
          </p>
          <Button onClick={() => refetchAlerts()}>
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
            {t("jobAlerts.title", locale) || "Job Alerts"}
          </h1>
          <p className="text-slate-500 font-medium">
            {t("jobAlerts.description", locale) ||
              "Manage your job search alerts and get notified when matching jobs are posted"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            {t("jobAlerts.createAlert", locale) || "Create Alert"}
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <Card className="p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder={
              t("jobAlerts.searchPlaceholder", locale) || "Search alerts..."
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label={
              t("jobAlerts.searchPlaceholder", locale) ||
              "Search alerts by name, keywords, or locations"
            }
          />
        </div>
      </Card>

      {/* Create/Edit Form Modal */}
      {showCreateForm && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="job-alerts-modal-title"
          onClick={(e) =>
            e.target === e.currentTarget &&
            (setShowCreateForm(false), setEditingAlert(null))
          }
        >
          <FocusTrap
            active={showCreateForm}
            focusTrapOptions={{
              escapeDeactivates: true,
              allowOutsideClick: true,
              onDeactivate: () => {
                setShowCreateForm(false);
                setEditingAlert(null);
              },
            }}
          >
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h2
                  id="job-alerts-modal-title"
                  className="text-xl font-semibold text-slate-900"
                >
                  {editingAlert
                    ? t("jobAlerts.editAlert", locale) || "Edit Alert"
                    : t("jobAlerts.createAlert", locale) || "Create New Alert"}
                </h2>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setShowCreateForm(false);
                    setEditingAlert(null);
                    setFormData({
                      name: "",
                      keywords: [],
                      locations: [],
                      salary_min: "",
                      salary_max: "",
                      companies_include: [],
                      companies_exclude: [],
                      job_types: [],
                      remote_only: false,
                      frequency: "daily",
                    });
                  }}
                >
                  ✕
                </Button>
              </div>

              <div className="space-y-4">
                {/* Alert Name */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    {t("jobAlerts.alertName", locale) || "Alert Name"}
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData((previous) => ({
                        ...previous,
                        name: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder={
                      t("jobAlerts.alertNamePlaceholder", locale) ||
                      "e.g., Software Engineer Jobs"
                    }
                  />
                </div>

                {/* Keywords */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    {t("jobAlerts.keywords", locale) || "Keywords"}
                  </label>
                  <div className="space-y-2">
                    {formData.keywords.map((keyword, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={keyword}
                          onChange={(e) => {
                            const newKeywords = [...formData.keywords];
                            newKeywords[index] = e.target.value;
                            setFormData((previous) => ({
                              ...previous,
                              keywords: newKeywords,
                            }));
                          }}
                          className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          placeholder={
                            t("jobAlerts.keywordPlaceholder", locale) ||
                            "e.g., React, TypeScript"
                          }
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeKeyword(index)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setFormData((previous) => ({
                          ...previous,
                          keywords: [...previous.keywords, ""],
                        }))
                      }
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Locations */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    {t("jobAlerts.locations", locale) || "Locations"}
                  </label>
                  <div className="space-y-2">
                    {formData.locations.map((location, index) => (
                      <div key={index} className="flex gap-2">
                        <div className="relative flex-1">
                          <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                          <input
                            type="text"
                            value={location}
                            onChange={(e) => {
                              const newLocations = [...formData.locations];
                              newLocations[index] = e.target.value;
                              setFormData((previous) => ({
                                ...previous,
                                locations: newLocations,
                              }));
                            }}
                            className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                            placeholder={
                              t("jobAlerts.locationPlaceholder", locale) ||
                              "e.g., San Francisco, CA"
                            }
                          />
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeLocation(index)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setFormData((previous) => ({
                          ...previous,
                          locations: [...previous.locations, ""],
                        }))
                      }
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Salary Range */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      {t("jobAlerts.minSalary", locale) || "Minimum Salary"}
                    </label>
                    <input
                      type="number"
                      value={formData.salary_min}
                      onChange={(e) =>
                        setFormData((previous) => ({
                          ...previous,
                          salary_min: e.target.value,
                        }))
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder={
                        t("jobAlerts.salaryPlaceholder", locale) || "50000"
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      {t("jobAlerts.maxSalary", locale) || "Maximum Salary"}
                    </label>
                    <input
                      type="number"
                      value={formData.salary_max}
                      onChange={(e) =>
                        setFormData((previous) => ({
                          ...previous,
                          salary_max: e.target.value,
                        }))
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder={
                        t("jobAlerts.salaryPlaceholder", locale) || "150000"
                      }
                    />
                  </div>
                </div>

                {/* Frequency */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    {t("jobAlerts.frequency", locale) || "Alert Frequency"}
                  </label>
                  <select
                    value={formData.frequency}
                    onChange={(e) =>
                      setFormData((previous) => ({
                        ...previous,
                        frequency: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="daily">
                      {t("jobAlerts.daily", locale) || "Daily"}
                    </option>
                    <option value="weekly">
                      {t("jobAlerts.weekly", locale) || "Weekly"}
                    </option>
                    <option value="monthly">
                      {t("jobAlerts.monthly", locale) || "Monthly"}
                    </option>
                  </select>
                </div>

                {/* Remote Only */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="remote_only"
                    checked={formData.remote_only}
                    onChange={(e) =>
                      setFormData((previous) => ({
                        ...previous,
                        remote_only: e.target.checked,
                      }))
                    }
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
                  />
                  <label
                    htmlFor="remote_only"
                    className="ml-2 text-sm text-slate-700"
                  >
                    {t("jobAlerts.remoteOnly", locale) || "Remote jobs only"}
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => setShowCreateForm(false)}
                >
                  {t("common.cancel", locale) || "Cancel"}
                </Button>
                <Button
                  onClick={editingAlert ? handleUpdateAlert : handleCreateAlert}
                  disabled={
                    (editingAlert
                      ? updateAlertMutation.isPending
                      : createAlertMutation.isPending) || !formData.name.trim()
                  }
                >
                  {(
                    editingAlert
                      ? updateAlertMutation.isPending
                      : createAlertMutation.isPending
                  ) ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                  ) : (editingAlert ? (
                    <Check className="w-4 h-4 mr-2" />
                  ) : (
                    <Plus className="w-4 h-4 mr-2" />
                  ))}
                  {editingAlert
                    ? t("jobAlerts.updateAlert", locale) || "Update Alert"
                    : t("jobAlerts.createAlert", locale) || "Create Alert"}
                </Button>
              </div>
            </div>
          </FocusTrap>
        </div>
      )}

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <Card className="p-8 text-center">
            <BellOff className="w-12 h-12 mx-auto text-slate-300 mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              {searchTerm
                ? t("jobAlerts.noSearchResults", locale) ||
                  "No alerts match your search"
                : t("jobAlerts.noAlerts", locale) || "No job alerts yet"}
            </h3>
            <p className="text-slate-600 mb-4">
              {t("jobAlerts.noAlertsDescription", locale) ||
                "Create your first job alert to get notified when matching jobs are posted"}
            </p>
            {!searchTerm && (
              <Button onClick={() => setShowCreateForm(true)}>
                <Plus className="w-4 h-4 mr-2" />
                {t("jobAlerts.createFirstAlert", locale) ||
                  "Create Your First Alert"}
              </Button>
            )}
          </Card>
        ) : (
          filteredAlerts.map((alert) => (
            <Card
              key={alert.id}
              className="p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                {/* Alert Details */}
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-1 flex items-center gap-2">
                        {alert.is_active ? (
                          <Bell className="w-5 h-5 text-green-500" />
                        ) : (
                          <BellOff className="w-5 h-5 text-slate-400" />
                        )}
                        {alert.name}
                      </h3>
                      <div className="flex items-center gap-2">
                        <Badge variant={alert.is_active ? "lagoon" : "outline"}>
                          {alert.is_active
                            ? t("jobAlerts.active", locale) || "Active"
                            : t("jobAlerts.inactive", locale) || "Inactive"}
                        </Badge>
                        <Badge variant="outline" className="ml-2">
                          {alert.frequency}
                        </Badge>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleEditAlert(alert)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        {t("common.edit", locale) || "Edit"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          handleToggleAlert(alert.id, !alert.is_active)
                        }
                      >
                        {alert.is_active ? (
                          <BellOff className="w-4 h-4 mr-1" />
                        ) : (
                          <Bell className="w-4 h-4 mr-1" />
                        )}
                        {t("jobAlerts.toggle", locale) || "Toggle"}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteAlert(alert.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        {t("common.delete", locale) || "Delete"}
                      </Button>
                    </div>
                  </div>

                  {/* Alert Criteria */}
                  <div className="space-y-3 text-sm text-slate-600">
                    {alert.keywords.length > 0 && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {t("jobAlerts.keywords", locale) || "Keywords"}:
                        </span>
                        <span>{alert.keywords.join(", ")}</span>
                      </div>
                    )}

                    {alert.locations.length > 0 && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {t("jobAlerts.locations", locale) || "Locations"}:
                        </span>
                        <span>{alert.locations.join(", ")}</span>
                      </div>
                    )}

                    {(alert.salary_min || alert.salary_max) && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {t("jobAlerts.salaryRange", locale) || "Salary"}:
                        </span>
                        <span>
                          {alert.salary_min != undefined &&
                            formatCurrency(Number(alert.salary_min))}
                          {alert.salary_min != undefined &&
                            alert.salary_max != undefined &&
                            " - "}
                          {alert.salary_max != undefined &&
                            formatCurrency(Number(alert.salary_max))}
                        </span>
                      </div>
                    )}

                    {alert.remote_only && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {t("jobAlerts.remoteOnly", locale) || "Remote"}:
                        </span>
                        <span>Yes</span>
                      </div>
                    )}

                    {alert.last_sent_at && (
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>
                          {t("jobAlerts.lastSent", locale) || "Last sent"}:{" "}
                          {alert.last_sent_at
                            ? new Date(alert.last_sent_at).toLocaleDateString(
                                locale,
                              )
                            : "-"}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
