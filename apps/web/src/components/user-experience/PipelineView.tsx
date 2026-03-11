import React, { useState, useEffect } from "react";
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
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Progress } from "@/components/ui/Progress";
import {
  ArrowRight,
  ArrowLeft,
  Search,
  Filter,
  Download,
  Plus,
  MoreVertical,
  Calendar,
  Building2,
  MapPin,
  DollarSign,
  Clock,
} from "lucide-react";

interface Application {
  id: string;
  company: string;
  job_title: string;
  status: string;
  stage: string;
  priority: "low" | "medium" | "high";
  location: string;
  salary_min?: number;
  salary_max?: number;
  last_activity: string;
  created_at: string;
  notes_count: number;
  reminders_count: number;
}

interface PipelineStage {
  id: string;
  name: string;
  description: string;
  color: string;
  application_count: number;
  conversion_rate: number;
  avg_time_in_stage: number;
}

interface PipelineViewProperties {
  tenantId: string;
  userId: string;
}

export const PipelineView: React.FC<PipelineViewProperties> = ({
  tenantId,
  userId,
}) => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedPriority, setSelectedPriority] = useState("all");
  const [sortBy, setSortBy] = useState("last_activity");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    fetchPipelineData();
  }, [
    tenantId,
    userId,
    searchTerm,
    selectedStatus,
    selectedPriority,
    sortBy,
    sortOrder,
  ]);

  const fetchPipelineData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch pipeline view
      const pipelineResponse = await fetch("/api/ux/pipeline", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filters: {
            search: searchTerm,
            status: selectedStatus === "all" ? undefined : selectedStatus,
            priority: selectedPriority === "all" ? undefined : selectedPriority,
          },
          sort_by: sortBy,
          sort_order: sortOrder,
        }),
      });

      if (!pipelineResponse.ok)
        throw new Error("Failed to fetch pipeline data");
      const pipelineData = await pipelineResponse.json();

      setApplications(pipelineData.applications || []);
      setStages(pipelineData.stages || []);
    } catch (error_) {
      setError(error_ instanceof Error ? error_.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleStageChange = async (applicationId: string, newStage: string) => {
    try {
      const response = await fetch("/api/ux/pipeline/stage", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          application_id: applicationId,
          new_stage: newStage,
        }),
      });

      if (!response.ok) throw new Error("Failed to update stage");

      // Refresh data
      await fetchPipelineData();
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to update stage",
      );
    }
  };

  const handleBulkStageChange = async (
    applicationIds: string[],
    newStage: string,
  ) => {
    try {
      const response = await fetch("/api/ux/pipeline/stage/bulk", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          application_ids: applicationIds,
          new_stage: newStage,
        }),
      });

      if (!response.ok) throw new Error("Failed to bulk update stages");

      // Refresh data
      await fetchPipelineData();
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to bulk update stages",
      );
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      QUEUED: "bg-gray-100 text-gray-800",
      PROCESSING: "bg-blue-100 text-blue-800",
      REQUIRES_INPUT: "bg-yellow-100 text-yellow-800",
      APPLIED: "bg-green-100 text-green-800",
      SUBMITTED: "bg-green-100 text-green-800",
      COMPLETED: "bg-green-100 text-green-800",
      FAILED: "bg-red-100 text-red-800",
    };
    return colors[status as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      low: "bg-gray-100 text-gray-800",
      medium: "bg-yellow-100 text-yellow-800",
      high: "bg-red-100 text-red-800",
    };
    return (
      colors[priority as keyof typeof colors] || "bg-gray-100 text-gray-800"
    );
  };

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return "Not specified";
    if (min && max)
      return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    if (min) return `$${min.toLocaleString()}+`;
    return `Up to $${max?.toLocaleString()}`;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  const getApplicationsByStage = (stageId: string) => {
    return applications.filter((app) => app.stage === stageId);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map((index) => (
            <Card key={index} className="animate-pulse">
              <CardContent className="p-4">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters and Controls */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Application Pipeline</CardTitle>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="search"
                  placeholder="Search applications..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="QUEUED">Queued</SelectItem>
                  <SelectItem value="PROCESSING">Processing</SelectItem>
                  <SelectItem value="REQUIRES_INPUT">Requires Input</SelectItem>
                  <SelectItem value="APPLIED">Applied</SelectItem>
                  <SelectItem value="SUBMITTED">Submitted</SelectItem>
                  <SelectItem value="COMPLETED">Completed</SelectItem>
                  <SelectItem value="FAILED">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Select
                value={selectedPriority}
                onValueChange={setSelectedPriority}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All priorities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="sort">Sort By</Label>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger>
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="last_activity">Last Activity</SelectItem>
                  <SelectItem value="created_at">Created Date</SelectItem>
                  <SelectItem value="company">Company</SelectItem>
                  <SelectItem value="job_title">Job Title</SelectItem>
                  <SelectItem value="priority">Priority</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Pipeline Stages */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {stages.map((stage) => {
          const stageApplications = getApplicationsByStage(stage.id);

          return (
            <Card key={stage.id} className="min-h-96">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-sm">{stage.name}</CardTitle>
                    <p className="text-xs text-gray-500 mt-1">
                      {stage.description}
                    </p>
                  </div>
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: stage.color }}
                  />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Stage Stats */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Applications</span>
                    <span className="font-medium">
                      {stage.application_count}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Conversion Rate</span>
                    <span className="font-medium">
                      {stage.conversion_rate}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Avg. Time</span>
                    <span className="font-medium">
                      {stage.avg_time_in_stage}d
                    </span>
                  </div>
                  <Progress value={stage.conversion_rate} className="h-1" />
                </div>

                {/* Applications in Stage */}
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {stageApplications.map((application) => (
                    <Card
                      key={application.id}
                      className="p-3 cursor-pointer hover:shadow-md transition-shadow"
                    >
                      <div className="space-y-2">
                        <div className="flex justify-between items-start">
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium truncate">
                              {application.job_title}
                            </h4>
                            <p className="text-xs text-gray-500 truncate">
                              {application.company}
                            </p>
                          </div>
                          <div className="flex space-x-1">
                            <Badge
                              className={getPriorityColor(application.priority)}
                            >
                              {application.priority.toUpperCase()}
                            </Badge>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <Building2 className="h-3 w-3" />
                          <span>{application.company}</span>
                        </div>

                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <MapPin className="h-3 w-3" />
                          <span>{application.location}</span>
                        </div>

                        {application.salary_min && (
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <DollarSign className="h-3 w-3" />
                            <span>
                              {formatSalary(
                                application.salary_min,
                                application.salary_max,
                              )}
                            </span>
                          </div>
                        )}

                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <Clock className="h-3 w-3" />
                          <span>
                            {formatTimeAgo(application.last_activity)}
                          </span>
                        </div>

                        <div className="flex justify-between items-center pt-2">
                          <div className="flex space-x-1">
                            {application.notes_count > 0 && (
                              <Badge variant="outline" className="text-xs">
                                {application.notes_count} notes
                              </Badge>
                            )}
                            {application.reminders_count > 0 && (
                              <Badge variant="outline" className="text-xs">
                                {application.reminders_count} reminders
                              </Badge>
                            )}
                          </div>
                          <div className="flex space-x-1">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                handleStageChange(application.id, "next")
                              }
                            >
                              <ArrowRight className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}

                  {stageApplications.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <p className="text-sm">No applications in this stage</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Summary Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{applications.length}</div>
              <p className="text-sm text-gray-500">Total Applications</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {
                  applications.filter(
                    (app) =>
                      app.status === "APPLIED" || app.status === "SUBMITTED",
                  ).length
                }
              </div>
              <p className="text-sm text-gray-500">Successfully Applied</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {
                  applications.filter((app) => app.status === "REQUIRES_INPUT")
                    .length
                }
              </div>
              <p className="text-sm text-gray-500">Requires Input</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {applications.filter((app) => app.status === "FAILED").length}
              </div>
              <p className="text-sm text-gray-500">Failed</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
