import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { pushToast } from "../../lib/toast";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "../../lib/api";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { Input } from "../../components/ui/Input";
import { Label } from "../../components/ui/Label";
import { Textarea } from "../../components/ui/Textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/Select";
import { Alert, AlertDescription } from "../../components/ui/Alert";
import { FocusTrap } from "focus-trap-react";
import {
  ArrowLeft,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  MessageSquare,
  FileText,
  History,
  Plus,
  Loader2,
} from "lucide-react";
import { formatDate } from "../../lib/format";
import { getLocale } from "../../lib/i18n";
import { telemetry } from "../../lib/telemetry";

interface ApplicationInput {
  id: string;
  selector?: string;
  question?: string;
  field_type?: string;
  answer?: string | null;
  resolved?: boolean;
  meta?: Record<string, unknown> | null;
}

interface ApplicationEvent {
  id?: string;
  event_type?: string;
  properties?: Record<string, unknown> | null;
  created_at?: string;
}

interface ApplicationDetail {
  application: {
    id: string;
    job_title?: string;
    company?: string;
    status?: string;
    hold_question?: string;
    last_activity?: string;
    created_at?: string;
    updated_at?: string;
  };
  inputs: ApplicationInput[];
  events: ApplicationEvent[];
}

interface ApplicationNote {
  id: string;
  application_id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

const NOTE_CATEGORIES = [
  "general",
  "contact_info",
  "interview_prep",
  "follow_up",
  "feedback",
  "questions",
  "research",
  "salary_info",
  "next_steps",
  "personal_notes",
];

function statusVariant(
  status: string,
): "success" | "warning" | "error" | "default" {
  switch (status) {
    case "APPLIED": {
      return "success";
    }
    case "HOLD": {
      return "warning";
    }
    case "FAILED":
    case "REJECTED": {
      return "error";
    }
    default: {
      return "default";
    }
  }
}

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const locale = getLocale();
  const queryClient = useQueryClient();
  const [showAddNoteModal, setShowAddNoteModal] = useState(false);
  const [noteForm, setNoteForm] = useState({
    title: "",
    content: "",
    category: "general",
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["application", id],
    queryFn: () => apiGet<ApplicationDetail>(`applications/${id}`),
    enabled: !!id,
  });

  const notesQuery = useQuery({
    queryKey: ["ux-notes", id],
    queryFn: () => apiGet<ApplicationNote[]>(`ux/notes/${id}`),
    enabled: !!id,
  });

  const createNoteMutation = useMutation({
    mutationFn: async (payload: {
      application_id: string;
      title: string;
      content: string;
      category: string;
      tags?: string[];
    }) => apiPost<ApplicationNote>("ux/notes", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ux-notes", id] });
      queryClient.invalidateQueries({ queryKey: ["ux-notes-statistics"] });
      setShowAddNoteModal(false);
      setNoteForm({ title: "", content: "", category: "general" });
      pushToast({ title: "Note added", tone: "success" });
    },
  });

  if (!id) {
    navigate("/app/applications", { replace: true });
    return null;
  }

  if (isLoading) {
    return (
      <div
        className="max-w-4xl mx-auto p-6"
        aria-busy="true"
        aria-label="Loading application"
      >
        <LoadingSpinner label="Loading application..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="p-8 text-center">
          <h2 className="text-xl font-bold text-slate-900 mb-2">
            Application not found
          </h2>
          <p className="text-slate-500 mb-4">
            This application may have been removed or you don&apos;t have access
            to it.
          </p>
          <Button
            onClick={() => navigate("/app/applications")}
            variant="outline"
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Applications
          </Button>
        </Card>
      </div>
    );
  }

  const app = data.application;
  React.useEffect(() => {
    if (app?.id)
      telemetry.track("application_viewed", {
        application_id: app.id,
        company: app.company,
        status: app.status,
      });
  }, [app?.id, app?.company, app?.status]);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate("/app/applications")}
        className="mb-4 -ml-2"
        aria-label="Back to applications"
      >
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Applications
      </Button>

      <Card className="p-6" shadow="sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-slate-900 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              {app.company?.charAt(0) ?? "?"}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {app.company ?? "Unknown"}
              </h1>
              <p className="text-slate-600 font-medium">
                {app.job_title ?? "Unknown"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              variant={statusVariant(app.status ?? "")}
              className="text-sm"
            >
              {app.status}
            </Badge>
            {app.last_activity && (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Clock className="w-4 h-4" />
                {formatDate(app.last_activity, locale)}
              </div>
            )}
          </div>
        </div>

        {app.hold_question && (
          <div className="mt-6 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
            <h3 className="text-sm font-bold text-amber-900 dark:text-amber-100 uppercase tracking-wider mb-2">
              Needs your input
            </h3>
            <p className="text-slate-700 dark:text-slate-300">
              {app.hold_question}
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => navigate("/app/holds")}
            >
              Answer in Holds
            </Button>
          </div>
        )}
      </Card>

      {/* HIGH: Display Application Inputs (Hold Questions) */}
      {data.inputs && data.inputs.length > 0 && (
        <Card className="p-6" shadow="sm">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-bold text-slate-900">
              Application Questions
            </h2>
            <Badge variant="default" className="ml-auto">
              {data.inputs.length}{" "}
              {data.inputs.length === 1 ? "question" : "questions"}
            </Badge>
          </div>
          <div className="space-y-4">
            {data.inputs.map((input, index) => (
              <div
                key={input.id || index}
                className={`p-4 rounded-lg border ${
                  input.resolved
                    ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                    : "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800"
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {input.resolved ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-amber-600" />
                      )}
                      <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {input.question || "Question"}
                      </span>
                      {input.resolved && (
                        <Badge variant="success" className="text-xs">
                          Resolved
                        </Badge>
                      )}
                    </div>
                    {input.answer && (
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 pl-6">
                        <span className="font-medium">Answer: </span>
                        {input.answer}
                      </p>
                    )}
                    {input.field_type && (
                      <span className="text-xs text-slate-500 dark:text-slate-500 mt-1 pl-6 block">
                        Type: {input.field_type}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* LOW: Display Application Events Timeline with visual timeline */}
      {/* TODO: No separate me/applications/{id}/events API exists. Events come from GET applications/{id} (included in response). */}
      {data.events && data.events.length > 0 && (
        <Card className="p-6" shadow="sm">
          <div className="flex items-center gap-2 mb-4">
            <History className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-bold text-slate-900">
              Application Timeline
            </h2>
            <Badge variant="default" className="ml-auto">
              {data.events.length}{" "}
              {data.events.length === 1 ? "event" : "events"}
            </Badge>
          </div>
          {/* Timeline visualization */}
          <div className="relative pl-8 border-l-2 border-slate-200 dark:border-slate-700">
            {data.events
              .sort((a, b) => {
                const aTime = a.created_at
                  ? new Date(a.created_at).getTime()
                  : 0;
                const bTime = b.created_at
                  ? new Date(b.created_at).getTime()
                  : 0;
                return bTime - aTime; // Most recent first
              })
              .map((event, index) => {
                const eventType = event.event_type || "UNKNOWN";
                const eventDate = event.created_at
                  ? formatDate(event.created_at, locale)
                  : "Unknown date";
                const getEventIcon = () => {
                  if (
                    eventType.includes("SUCCESS") ||
                    eventType.includes("APPLIED") ||
                    eventType.includes("COMPLETED")
                  ) {
                    return <CheckCircle className="w-5 h-5 text-green-600" />;
                  }
                  if (
                    eventType.includes("FAILED") ||
                    eventType.includes("ERROR") ||
                    eventType.includes("REJECTED")
                  ) {
                    return <XCircle className="w-5 h-5 text-red-600" />;
                  }
                  if (
                    eventType.includes("REQUIRES_INPUT") ||
                    eventType.includes("HOLD")
                  ) {
                    return <AlertCircle className="w-5 h-5 text-amber-600" />;
                  }
                  return <MessageSquare className="w-5 h-5 text-slate-600" />;
                };

                return (
                  <div
                    key={event.id || index}
                    className="relative flex items-start gap-4 pb-6 last:pb-0"
                  >
                    {/* Timeline dot */}
                    <div className="absolute -left-[21px] w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 bg-slate-400 dark:bg-slate-600 z-10" />
                    <div className="flex-shrink-0 mt-1">{getEventIcon()}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {eventType.replaceAll("_", " ")}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-500 whitespace-nowrap">
                          {eventDate}
                        </span>
                      </div>
                      {event.properties &&
                        Object.keys(event.properties).length > 0 && (
                          <div className="mt-2 p-2 rounded bg-slate-50 dark:bg-slate-800 text-xs">
                            <pre className="whitespace-pre-wrap text-slate-600 dark:text-slate-400">
                              {JSON.stringify(event.properties, null, 2)}
                            </pre>
                          </div>
                        )}
                    </div>
                  </div>
                );
              })}
          </div>
        </Card>
      )}

      {/* Notes Section */}
      <Card className="p-6" shadow="sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-bold text-slate-900">Notes</h2>
            {notesQuery.data && notesQuery.data.length > 0 && (
              <Badge variant="default" className="text-xs">
                {notesQuery.data.length}
              </Badge>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddNoteModal(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Note
          </Button>
        </div>

        {notesQuery.isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
          </div>
        ) : notesQuery.error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {notesQuery.error instanceof Error
                ? notesQuery.error.message
                : "Failed to load notes"}
            </AlertDescription>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => notesQuery.refetch()}
            >
              Retry
            </Button>
          </Alert>
        ) : notesQuery.data && notesQuery.data.length > 0 ? (
          <div className="space-y-3">
            {notesQuery.data
              .sort(
                (a, b) =>
                  new Date(b.updated_at).getTime() -
                  new Date(a.updated_at).getTime(),
              )
              .map((note) => (
                <div
                  key={note.id}
                  className="p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/30"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-medium text-slate-900 dark:text-slate-100">
                        {note.title}
                      </h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 whitespace-pre-wrap">
                        {note.content}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="secondary" className="text-xs">
                          {note.category.replace(/_/g, " ")}
                        </Badge>
                        <span className="text-xs text-slate-500">
                          {formatDate(note.updated_at, locale)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>
              No notes yet. Add notes to track your thoughts about this
              application.
            </p>
          </div>
        )}
      </Card>

      {/* Add Note Modal */}
      {showAddNoteModal && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-note-modal-title"
          onClick={(e) =>
            e.target === e.currentTarget && setShowAddNoteModal(false)
          }
        >
          <FocusTrap
            active={showAddNoteModal}
            focusTrapOptions={{
              escapeDeactivates: true,
              allowOutsideClick: true,
              onDeactivate: () => setShowAddNoteModal(false),
            }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-lg p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-xl">
              <div className="flex justify-between items-center mb-4">
                <h2
                  id="add-note-modal-title"
                  className="text-xl font-semibold text-slate-900 dark:text-slate-100"
                >
                  Add Note
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddNoteModal(false)}
                  aria-label="Close"
                >
                  ✕
                </Button>
              </div>

              {createNoteMutation.error && (
                <Alert variant="destructive" className="mb-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {createNoteMutation.error instanceof Error
                      ? createNoteMutation.error.message
                      : "Failed to add note"}
                  </AlertDescription>
                </Alert>
              )}

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="note-title">Title</Label>
                  <Input
                    id="note-title"
                    value={noteForm.title}
                    onChange={(e) =>
                      setNoteForm((p) => ({ ...p, title: e.target.value }))
                    }
                    placeholder="Note title"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="note-content">Content</Label>
                  <Textarea
                    id="note-content"
                    value={noteForm.content}
                    onChange={(e) =>
                      setNoteForm((p) => ({ ...p, content: e.target.value }))
                    }
                    placeholder="Note content..."
                    rows={4}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="note-category">Category</Label>
                  <Select
                    value={noteForm.category}
                    onValueChange={(v) =>
                      setNoteForm((p) => ({ ...p, category: v }))
                    }
                  >
                    <SelectTrigger id="note-category">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {NOTE_CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat}>
                          {cat.replace(/_/g, " ")}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => setShowAddNoteModal(false)}
                  disabled={createNoteMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    if (!noteForm.title.trim()) return;
                    createNoteMutation.mutate({
                      application_id: app.id,
                      title: noteForm.title.trim(),
                      content: noteForm.content.trim(),
                      category: noteForm.category,
                    });
                  }}
                  disabled={
                    !noteForm.title.trim() || createNoteMutation.isPending
                  }
                >
                  {createNoteMutation.isPending && (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  )}
                  Add Note
                </Button>
              </div>
            </div>
          </FocusTrap>
        </div>
      )}

      {/* Empty states for missing data */}
      {(!data.inputs || data.inputs.length === 0) &&
        (!data.events || data.events.length === 0) && (
          <Card className="p-8 text-center" shadow="sm">
            <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              No additional details
            </h3>
            <p className="text-slate-500 mb-4">
              This application doesn't have any questions or events yet.
            </p>
          </Card>
        )}
    </div>
  );
}
