import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Textarea } from "@/components/ui/Textarea";
import {
  Clock,
  CheckCircle,
  Plus,
  Send,
  AlarmClock,
  AlertTriangle,
} from "lucide-react";

const REMINDER_TYPES = [
  "application_submitted",
  "one_week_follow_up",
  "two_week_follow_up",
  "interview_scheduled",
  "interview_preparation",
  "post_interview_thank_you",
  "offer_received",
  "offer_response",
  "rejection_follow_up",
  "custom",
] as const;

function formatReminderType(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return `${Math.abs(diffDays)} days ago`;
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Tomorrow";
  if (diffDays < 7) return `In ${diffDays} days`;
  if (diffDays < 30) return `In ${Math.floor(diffDays / 7)} weeks`;
  return date.toLocaleDateString();
}

interface FollowUpReminder {
  id: string;
  application_id: string;
  user_id: string;
  tenant_id: string;
  reminder_type: string;
  scheduled_for: string;
  message: string;
  status: string;
  sent_at?: string | null;
  completed_at?: string | null;
  metadata?: Record<string, unknown>;
}

interface Application {
  id: string;
  company?: string;
  job_title?: string;
  status?: string;
  [key: string]: unknown;
}

const FollowUpRemindersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState({
    application_id: "",
    reminder_type: "application_submitted",
    scheduled_for: "",
    message: "",
  });

  const { data: reminders = [], isLoading: remindersLoading } = useQuery({
    queryKey: ["ux-reminders"],
    queryFn: async () => apiGet<FollowUpReminder[]>("ux/reminders"),
    staleTime: 60 * 1000,
  });

  const { data: applicationsData } = useQuery({
    queryKey: ["applications"],
    queryFn: async () =>
      apiGet<{ applications?: Application[]; items?: Application[] }>(
        "me/applications",
      ),
    enabled: showCreateForm,
    staleTime: 60 * 1000,
  });

  const applications = applicationsData?.items ?? applicationsData?.applications ?? [];
  const appMap = Object.fromEntries(
    applications.map((a) => [a.id, { company: a.company ?? "Unknown", job_title: a.job_title ?? "Application" }]),
  );

  const createMutation = useMutation({
    mutationFn: async (body: {
      application_id: string;
      reminder_type: string;
      scheduled_for: string;
      message: string;
    }) => {
      const scheduledFor = body.scheduled_for
        ? new Date(body.scheduled_for).toISOString()
        : new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
      return apiPost<FollowUpReminder>("ux/reminders", {
        ...body,
        scheduled_for: scheduledFor,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ux-reminders"] });
      setShowCreateForm(false);
      setCreateForm({
        application_id: "",
        reminder_type: "application_submitted",
        scheduled_for: "",
        message: "",
      });
    },
  });

  const sendMutation = useMutation({
    mutationFn: (id: string) => apiPut<{ success: boolean }>(`ux/reminders/${id}/send`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ux-reminders"] }),
  });

  const completeMutation = useMutation({
    mutationFn: (id: string) =>
      apiPut<{ success: boolean }>(`ux/reminders/${id}/complete`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ux-reminders"] }),
  });

  const snoozeMutation = useMutation({
    mutationFn: ({ id, days }: { id: string; days: number }) =>
      apiPut<{ success: boolean }>(`ux/reminders/${id}/snooze?days=${days}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ux-reminders"] }),
  });

  const handleCreate = () => {
    if (!createForm.application_id || !createForm.message) return;
    createMutation.mutate({
      ...createForm,
      scheduled_for:
        createForm.scheduled_for ||
        new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
    });
  };

  const pendingCount = reminders.filter((r) => r.status === "pending").length;
  const completedCount = reminders.filter((r) => r.status === "completed").length;
  const sentCount = reminders.filter((r) => r.status === "sent").length;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Follow-up Reminders</h1>
          <p className="text-gray-600">
            Automated follow-up reminders for job applications
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Reminder
        </Button>
      </div>

      <Alert>
        <AlertDescription>
          Set up automated follow-up reminders to stay on top of your job
          applications and never miss an important deadline.
        </AlertDescription>
      </Alert>

      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create Reminder</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="create-application">Application</Label>
              {applications.length === 0 && (
                <p className="text-sm text-amber-600 mb-1">
                  Add job applications first to create reminders.
                </p>
              )}
              <Select
                value={createForm.application_id}
                onValueChange={(v) =>
                  setCreateForm((f) => ({ ...f, application_id: v }))
                }
              >
                <SelectTrigger id="create-application">
                  <SelectValue placeholder="Select application" />
                </SelectTrigger>
                <SelectContent>
                  {applications.map((app) => (
                    <SelectItem key={app.id} value={app.id}>
                      {app.company ?? "Unknown"} – {app.job_title ?? app.id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="create-type">Reminder Type</Label>
              <Select
                value={createForm.reminder_type}
                onValueChange={(v) =>
                  setCreateForm((f) => ({ ...f, reminder_type: v }))
                }
              >
                <SelectTrigger id="create-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {REMINDER_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {formatReminderType(t)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="create-date">Scheduled For</Label>
              <Input
                id="create-date"
                type="datetime-local"
                value={createForm.scheduled_for}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, scheduled_for: e.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="create-message">Message</Label>
              <Textarea
                id="create-message"
                value={createForm.message}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, message: e.target.value }))
                }
                placeholder="Reminder message..."
                rows={3}
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleCreate}
                disabled={
                  !createForm.application_id ||
                  !createForm.message ||
                  createMutation.isPending
                }
              >
                {createMutation.isPending ? "Creating..." : "Create"}
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowCreateForm(false)}
              >
                Cancel
              </Button>
            </div>
            {createMutation.isError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  {createMutation.error instanceof Error
                    ? createMutation.error.message
                    : "Failed to create reminder"}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Reminders</CardTitle>
        </CardHeader>
        <CardContent>
          {remindersLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            </div>
          ) : reminders.length === 0 ? (
            <EmptyState
              iconName="calendar"
              title="No reminders yet"
              description="Create a reminder to follow up on your job applications."
              actionLabel="Create Reminder"
              onAction={() => setShowCreateForm(true)}
            />
          ) : (
            <div className="space-y-4">
              {reminders.map((reminder) => {
                const app = appMap[reminder.application_id];
                const label = app
                  ? `${app.company} – ${app.job_title}`
                  : `Application ${reminder.application_id.slice(0, 8)}`;
                return (
                  <div
                    key={reminder.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <Clock
                        className={`h-5 w-5 ${
                          reminder.status === "completed"
                            ? "text-green-500"
                            : reminder.status === "sent"
                              ? "text-blue-500"
                              : "text-amber-500"
                        }`}
                      />
                      <div>
                        <div className="font-medium">{label}</div>
                        <div className="text-sm text-gray-500">
                          {formatReminderType(reminder.reminder_type)} •{" "}
                          {formatRelativeDate(reminder.scheduled_for)}
                        </div>
                        {reminder.message && (
                          <div className="text-sm text-gray-600 mt-1 line-clamp-2">
                            {reminder.message}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          reminder.status === "completed"
                            ? "default"
                            : reminder.status === "sent"
                              ? "secondary"
                              : "outline"
                        }
                      >
                        {reminder.status}
                      </Badge>
                      {reminder.status === "pending" && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              completeMutation.mutate(reminder.id)
                            }
                            disabled={completeMutation.isPending}
                            title="Mark complete"
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              snoozeMutation.mutate({
                                id: reminder.id,
                                days: 1,
                              })
                            }
                            disabled={snoozeMutation.isPending}
                            title="Snooze 1 day"
                          >
                            <AlarmClock className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => sendMutation.mutate(reminder.id)}
                            disabled={sendMutation.isPending}
                            title="Mark sent"
                          >
                            <Send className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {reminders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{pendingCount}</div>
                <p className="text-sm text-gray-500">Pending</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{
                  sentCount
                }</div>
                <p className="text-sm text-gray-500">Sent</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {completedCount}
                </div>
                <p className="text-sm text-gray-500">Completed</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{reminders.length}</div>
                <p className="text-sm text-gray-500">Total</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default FollowUpRemindersPage;
