import React, { useState, useEffect } from "react";
import { apiGet, apiFetch, handleApiError } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { Checkbox } from "@/components/ui/Checkbox";
import { Textarea } from "@/components/ui/Textarea";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Progress } from "@/components/ui/Progress";
import {
  Download,
  FileText,
  Table,
  FileSpreadsheet,
  FileImage,
  Calendar,
  Filter,
  Search,
  CheckCircle,
  AlertCircle,
  Clock,
} from "lucide-react";

interface Application {
  id: string;
  company: string;
  job_title: string;
  status: string;
  location: string;
  salary_min?: number;
  salary_max?: number;
  created_at: string;
  last_activity: string;
  notes_count: number;
  reminders_count: number;
}

interface ExportTemplate {
  id: string;
  name: string;
  description: string;
  format: string;
  fields: string[];
  is_default: boolean;
}

interface ExportConfig {
  format: "csv" | "xlsx" | "pdf" | "json";
  fields: string[];
  filters: {
    status?: string;
    date_from?: string;
    date_to?: string;
    company?: string;
    location?: string;
  };
  include_notes: boolean;
  include_reminders: boolean;
}

const ApplicationExportPage: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [templates, setTemplates] = useState<ExportTemplate[]>([]);
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    format: "csv",
    fields: ["company", "job_title", "status", "location", "created_at"],
    filters: {},
    include_notes: false,
    include_reminders: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [exportProgress, setExportProgress] = useState(0);
  const [isExporting, setIsExporting] = useState(false);

  const availableFields = [
    { id: "id", label: "Application ID", description: "Unique identifier" },
    { id: "company", label: "Company", description: "Company name" },
    { id: "job_title", label: "Job Title", description: "Position title" },
    { id: "status", label: "Status", description: "Application status" },
    { id: "location", label: "Location", description: "Job location" },
    { id: "salary_min", label: "Min Salary", description: "Minimum salary" },
    { id: "salary_max", label: "Max Salary", description: "Maximum salary" },
    {
      id: "created_at",
      label: "Created Date",
      description: "Application creation date",
    },
    {
      id: "last_activity",
      label: "Last Activity",
      description: "Last activity date",
    },
    { id: "notes_count", label: "Notes Count", description: "Number of notes" },
    {
      id: "reminders_count",
      label: "Reminders Count",
      description: "Number of reminders",
    },
  ];

  useEffect(() => {
    fetchApplications();
    fetchTemplates();
  }, []);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const all: Application[] = [];
      const limit = 100;
      let offset = 0;
      let hasMore = true;

      while (hasMore) {
        const data = await apiGet<{
          items?: Application[];
          applications?: Application[];
          pagination?: { has_more: boolean };
        }>(`me/applications?limit=${limit}&offset=${offset}`);
        const items = data.items ?? data.applications ?? [];
        all.push(...items);
        hasMore = data.pagination?.has_more ?? items.length >= limit;
        offset += limit;
      }

      setApplications(all);
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to fetch applications",
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const data = await apiGet<
        { templates?: ExportTemplate[] } | ExportTemplate[]
      >("ux/export/templates");
      const templates = Array.isArray(data)
        ? data
        : (data as { templates?: ExportTemplate[] }).templates || [];
      setTemplates(templates);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to fetch templates",
      );
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      setError(null);
      setSuccess(null);
      setExportProgress(0);

      const response = await apiFetch("ux/export/applications", {
        method: "POST",
        body: JSON.stringify({
          format: exportConfig.format,
          fields: exportConfig.fields,
          filters: exportConfig.filters,
          include_headers: true,
          filename_prefix: "applications",
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        handleApiError(response, text);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `applications-export-${new Date().toISOString().split("T")[0]}.${exportConfig.format}`;
      document.body.append(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

      setSuccess("Export completed successfully!");
      setExportProgress(100);
    } catch (error_) {
      setError(error_ instanceof Error ? error_.message : "Export failed");
    } finally {
      setIsExporting(false);
    }
  };

  const handleTemplateSelect = (template: ExportTemplate) => {
    setExportConfig({
      ...exportConfig,
      format: template.format as any,
      fields: template.fields,
    });
  };

  const handleFieldToggle = (fieldId: string, checked: boolean) => {
    if (checked) {
      setExportConfig({
        ...exportConfig,
        fields: [...exportConfig.fields, fieldId],
      });
    } else {
      setExportConfig({
        ...exportConfig,
        fields: exportConfig.fields.filter((field) => field !== fieldId),
      });
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case "csv": {
        return <FileText className="h-4 w-4" />;
      }
      case "xlsx": {
        return <FileSpreadsheet className="h-4 w-4" />;
      }
      case "pdf": {
        return <FileImage className="h-4 w-4" />;
      }
      case "json": {
        return <FileText className="h-4 w-4" />;
      }
      default: {
        return <FileText className="h-4 w-4" />;
      }
    }
  };

  const getFilteredApplications = () => {
    return applications.filter((app) => {
      if (
        exportConfig.filters.status &&
        app.status !== exportConfig.filters.status
      ) {
        return false;
      }
      if (
        exportConfig.filters.company &&
        !(app.company ?? "")
          .toLowerCase()
          .includes(exportConfig.filters.company.toLowerCase())
      ) {
        return false;
      }
      if (
        exportConfig.filters.location &&
        !app.location
          .toLowerCase()
          .includes(exportConfig.filters.location.toLowerCase())
      ) {
        return false;
      }
      if (
        exportConfig.filters.date_from &&
        new Date(app.created_at) < new Date(exportConfig.filters.date_from)
      ) {
        return false;
      }
      if (
        exportConfig.filters.date_to &&
        new Date(app.created_at) > new Date(exportConfig.filters.date_to)
      ) {
        return false;
      }
      return true;
    });
  };

  const filteredApplications = getFilteredApplications();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Application Export</h1>
          <p className="text-gray-600">
            Export your applications data in multiple formats
          </p>
        </div>
      </div>

      {/* Export Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Export Applications</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Templates */}
          <div className="space-y-4">
            <Label>Quick Templates</Label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {templates.map((template) => (
                <Card
                  key={template.id}
                  className={`cursor-pointer transition-all ${
                    exportConfig.fields.length === template.fields.length &&
                    exportConfig.format === template.format
                      ? "ring-2 ring-blue-500"
                      : "hover:shadow-md"
                  }`}
                  onClick={() => handleTemplateSelect(template)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      {getFormatIcon(template.format)}
                      <span className="font-medium">{template.name}</span>
                      {template.is_default && (
                        <Badge variant="secondary" className="text-xs">
                          Default
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">
                      {template.description}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {template.fields.length} fields •{" "}
                      {template.format.toUpperCase()}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Export Format */}
          <div className="space-y-2">
            <Label>Export Format</Label>
            <Select
              value={exportConfig.format}
              onValueChange={(value: any) =>
                setExportConfig({ ...exportConfig, format: value })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4" />
                    <span>CSV</span>
                  </div>
                </SelectItem>
                <SelectItem value="xlsx">
                  <div className="flex items-center space-x-2">
                    <FileSpreadsheet className="h-4 w-4" />
                    <span>Excel (XLSX)</span>
                  </div>
                </SelectItem>
                <SelectItem value="pdf">
                  <div className="flex items-center space-x-2">
                    <FileImage className="h-4 w-4" />
                    <span>PDF</span>
                  </div>
                </SelectItem>
                <SelectItem value="json">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4" />
                    <span>JSON</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Field Selection */}
          <div className="space-y-4">
            <Label>
              Fields to Export ({exportConfig.fields.length} selected)
            </Label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {availableFields.map((field) => (
                <div key={field.id} className="flex items-start space-x-2">
                  <Checkbox
                    id={field.id}
                    checked={exportConfig.fields.includes(field.id)}
                    onCheckedChange={(checked) =>
                      handleFieldToggle(field.id, checked)
                    }
                  />
                  <div className="flex-1">
                    <Label htmlFor={field.id} className="text-sm font-medium">
                      {field.label}
                    </Label>
                    <p className="text-xs text-gray-500">{field.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Filters */}
          <div className="space-y-4">
            <Label>Filters</Label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="status-filter">Status</Label>
                <Select
                  value={exportConfig.filters.status || ""}
                  onValueChange={(value) =>
                    setExportConfig({
                      ...exportConfig,
                      filters: {
                        ...exportConfig.filters,
                        status: value || undefined,
                      },
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All statuses</SelectItem>
                    <SelectItem value="QUEUED">Queued</SelectItem>
                    <SelectItem value="PROCESSING">Processing</SelectItem>
                    <SelectItem value="REQUIRES_INPUT">
                      Requires Input
                    </SelectItem>
                    <SelectItem value="APPLIED">Applied</SelectItem>
                    <SelectItem value="SUBMITTED">Submitted</SelectItem>
                    <SelectItem value="COMPLETED">Completed</SelectItem>
                    <SelectItem value="FAILED">Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="page-company-filter">Company</Label>
                <Input
                  id="page-company-filter"
                  placeholder="Filter by company..."
                  value={exportConfig.filters.company || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setExportConfig({
                      ...exportConfig,
                      filters: {
                        ...exportConfig.filters,
                        company: e.target.value || undefined,
                      },
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="page-location-filter">Location</Label>
                <Input
                  id="page-location-filter"
                  placeholder="Filter by location..."
                  value={exportConfig.filters.location || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setExportConfig({
                      ...exportConfig,
                      filters: {
                        ...exportConfig.filters,
                        location: e.target.value || undefined,
                      },
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="page-date-from">Date From</Label>
                <Input
                  id="page-date-from"
                  type="date"
                  value={exportConfig.filters.date_from || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setExportConfig({
                      ...exportConfig,
                      filters: {
                        ...exportConfig.filters,
                        date_from: e.target.value || undefined,
                      },
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="page-date-to">Date To</Label>
                <Input
                  id="page-date-to"
                  type="date"
                  value={exportConfig.filters.date_to || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setExportConfig({
                      ...exportConfig,
                      filters: {
                        ...exportConfig.filters,
                        date_to: e.target.value || undefined,
                      },
                    })
                  }
                />
              </div>
            </div>
          </div>

          {/* Additional Options */}
          <div className="space-y-4">
            <Label>Additional Options</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="page-include-notes"
                  checked={exportConfig.include_notes}
                  onCheckedChange={(checked) =>
                    setExportConfig({
                      ...exportConfig,
                      include_notes: checked,
                    })
                  }
                />
                <Label htmlFor="page-include-notes">Include application notes</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="page-include-reminders"
                  checked={exportConfig.include_reminders}
                  onCheckedChange={(checked) =>
                    setExportConfig({
                      ...exportConfig,
                      include_reminders: checked,
                    })
                  }
                />
                <Label htmlFor="page-include-reminders">Include reminders</Label>
              </div>
            </div>
          </div>

          {/* Export Status */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>{success}</AlertDescription>
            </Alert>
          )}

          {isExporting && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Exporting...</span>
                <span>{exportProgress}%</span>
              </div>
              <Progress value={exportProgress} className="h-2" />
            </div>
          )}

          {/* Export Button */}
          <Button
            onClick={handleExport}
            disabled={isExporting || exportConfig.fields.length === 0}
            className="w-full"
            size="lg"
          >
            <Download className="h-4 w-4 mr-2" />
            {isExporting
              ? "Exporting..."
              : `Export ${filteredApplications.length} Applications`}
          </Button>
        </CardContent>
      </Card>

      {/* Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Export Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">
                {filteredApplications.length} applications will be exported
              </span>
              <div className="flex space-x-2">
                <Badge variant="outline">
                  {exportConfig.format.toUpperCase()}
                </Badge>
                <Badge variant="outline">
                  {exportConfig.fields.length} fields
                </Badge>
              </div>
            </div>

            {filteredApplications.length > 0 && (
              <div className="border rounded-lg overflow-hidden overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {exportConfig.fields.map((field) => (
                        <th
                          key={field}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {availableFields.find((f) => f.id === field)?.label ||
                            field}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredApplications.slice(0, 5).map((app) => (
                      <tr key={app.id}>
                        {exportConfig.fields.map((field) => (
                          <td
                            key={field}
                            className="px-4 py-2 whitespace-nowrap text-sm text-gray-900"
                          >
                            {field === "salary_min" && app.salary_min
                              ? `$${app.salary_min.toLocaleString()}`
                              : field === "salary_max" && app.salary_max
                                ? `$${app.salary_max.toLocaleString()}`
                                : field === "created_at" ||
                                    field === "last_activity"
                                  ? new Date(
                                      (app[
                                        field as keyof Application
                                      ] as string) || "",
                                    ).toLocaleDateString()
                                  : String(
                                      (
                                        app as unknown as Record<
                                          string,
                                          unknown
                                        >
                                      )[field] ?? "-",
                                    )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredApplications.length > 5 && (
                  <div className="px-4 py-2 text-center text-sm text-gray-500">
                    ... and {filteredApplications.length - 5} more applications
                  </div>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicationExportPage;
