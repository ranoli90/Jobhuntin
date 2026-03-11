import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api";
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
import {
  FileText,
  Plus,
  Search,
  Tag,
  Calendar,
  AlertCircle,
  Pencil,
  Trash2,
  Loader2,
} from "lucide-react";
import { FocusTrap } from "focus-trap-react";

interface ApplicationNote {
  id: string;
  application_id: string;
  user_id: string;
  tenant_id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  is_private: boolean;
  is_pinned: boolean;
  reminder_date: string | null;
  created_at: string;
  updated_at: string;
  author_id: string;
}

interface NoteSearchResult {
  note: ApplicationNote;
  relevance_score: number;
  matched_terms: string[];
}

interface NoteTemplate {
  id: string;
  name: string;
  category: string;
  title_template: string;
  content_template: string;
  suggested_tags: string[];
  is_default: boolean;
}

interface ApplicationRecord {
  id: string;
  job_title: string;
  company: string;
  status: string;
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

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3600_000);
  const diffDays = Math.floor(diffMs / 86400_000);

  if (diffMins < 60) return `${diffMins} minutes ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}

const ApplicationNotesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"recent" | "reminders">("recent");
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [editingNote, setEditingNote] = useState<ApplicationNote | null>(null);
  const [formData, setFormData] = useState({
    application_id: "",
    title: "",
    content: "",
    category: "general",
    tags: [] as string[],
  });

  // Fetch applications for Add Note form
  const { data: applications = [] } = useQuery({
    queryKey: ["applications"],
    queryFn: async () => {
      const json = await apiGet<
        | { items?: ApplicationRecord[]; applications?: ApplicationRecord[] }
        | ApplicationRecord[]
      >("me/applications");
      if (Array.isArray(json)) return json;
      return json.items ?? json.applications ?? [];
    },
  });

  // Fetch notes: search (empty = recent) or reminders
  const notesQuery = useQuery({
    queryKey: ["ux-notes", viewMode, searchQuery],
    queryFn: async () => {
      if (viewMode === "reminders") {
        const data = await apiGet<ApplicationNote[]>(
          "ux/notes/reminders?days_ahead=7",
        );
        return data;
      }
      const params = new URLSearchParams({
        query: searchQuery.trim(),
        limit: "50",
      });
      const data = await apiGet<NoteSearchResult[]>(
        `ux/notes/search?${params}`,
      );
      return Array.isArray(data)
        ? data.map((r) => (typeof r.note === "object" ? r.note : r as unknown as ApplicationNote))
        : [];
    },
  });

  // Fetch templates
  const templatesQuery = useQuery({
    queryKey: ["ux-notes-templates"],
    queryFn: async () => {
      const data = await apiGet<NoteTemplate[] | { templates?: NoteTemplate[] }>(
        "ux/notes/templates",
      );
      return Array.isArray(data) ? data : data.templates ?? [];
    },
  });

  // Fetch statistics
  const statsQuery = useQuery({
    queryKey: ["ux-notes-statistics"],
    queryFn: async () =>
      apiGet<{
        total_notes?: number;
        pinned_notes?: number;
        reminder_notes?: number;
        category_breakdown?: Record<string, number>;
        period_days?: number;
      }>("ux/notes/statistics?days_back=30"),
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
      queryClient.invalidateQueries({ queryKey: ["ux-notes"] });
      queryClient.invalidateQueries({ queryKey: ["ux-notes-statistics"] });
      setShowNoteModal(false);
      setFormData({
        application_id: "",
        title: "",
        content: "",
        category: "general",
        tags: [],
      });
    },
  });

  const updateNoteMutation = useMutation({
    mutationFn: async ({
      noteId,
      ...payload
    }: {
      noteId: string;
      title?: string;
      content?: string;
      category?: string;
      tags?: string[];
    }) => apiPut(`ux/notes/${noteId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ux-notes"] });
      queryClient.invalidateQueries({ queryKey: ["ux-notes-statistics"] });
      setShowNoteModal(false);
      setEditingNote(null);
    },
  });

  const deleteNoteMutation = useMutation({
    mutationFn: async (noteId: string) => apiDelete(`ux/notes/${noteId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ux-notes"] });
      queryClient.invalidateQueries({ queryKey: ["ux-notes-statistics"] });
      setEditingNote(null);
    },
  });

  const notes: ApplicationNote[] = (() => {
    const raw = notesQuery.data;
    if (!raw) return [];
    if (Array.isArray(raw)) {
      return raw.every(
        (r) => r && typeof r === "object" && "id" in r && "title" in r,
      )
        ? (raw as ApplicationNote[])
        : raw.map((r: NoteSearchResult) => r.note);
    }
    return [];
  })();

  const templates = templatesQuery.data ?? [];
  const stats = statsQuery.data ?? {};
  const isLoading =
    notesQuery.isLoading || templatesQuery.isLoading || statsQuery.isLoading;
  const error =
    notesQuery.error ?? templatesQuery.error ?? statsQuery.error;
  const mutateError =
    createNoteMutation.error ??
    updateNoteMutation.error ??
    deleteNoteMutation.error;

  const handleAddNote = () => {
    setEditingNote(null);
    setFormData({
      application_id: applications[0]?.id ?? "",
      title: "",
      content: "",
      category: "general",
      tags: [],
    });
    setShowNoteModal(true);
  };

  const handleEditNote = (note: ApplicationNote) => {
    setEditingNote(note);
    setFormData({
      application_id: note.application_id,
      title: note.title,
      content: note.content,
      category: note.category,
      tags: note.tags ?? [],
    });
    setShowNoteModal(true);
  };

  const handleDeleteNote = (note: ApplicationNote) => {
    if (!window.confirm("Are you sure you want to delete this note?")) return;
    deleteNoteMutation.mutate(note.id);
  };

  const handleSubmitNote = () => {
    if (editingNote) {
      updateNoteMutation.mutate({
        noteId: editingNote.id,
        title: formData.title,
        content: formData.content,
        category: formData.category,
        tags: formData.tags,
      });
    } else {
      if (!formData.application_id) {
        return;
      }
      createNoteMutation.mutate({
        application_id: formData.application_id,
        title: formData.title,
        content: formData.content,
        category: formData.category,
        tags: formData.tags,
      });
    }
  };

  const getApplicationLabel = (appId: string) => {
    const app = applications.find((a) => a.id === appId);
    return app ? `${app.company} • ${app.job_title}` : appId;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Application Notes</h1>
          <p className="text-gray-600">
            Rich note-taking system with templates and search capabilities
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={handleAddNote}>
            <Plus className="h-4 w-4 mr-2" />
            Add Note
          </Button>
        </div>
      </div>

      <Alert>
        <AlertDescription>
          Keep detailed notes for each application with templates, search
          functionality, and reminder integration.
        </AlertDescription>
      </Alert>

      {/* Search and view toggle */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            disabled={viewMode === "reminders"}
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={viewMode === "recent" ? "default" : "outline"}
            onClick={() => setViewMode("recent")}
          >
            Recent
          </Button>
          <Button
            variant={viewMode === "reminders" ? "default" : "outline"}
            onClick={() => setViewMode("reminders")}
          >
            <Calendar className="h-4 w-4 mr-2" />
            Reminders
          </Button>
        </div>
      </div>

      {mutateError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {mutateError instanceof Error
              ? mutateError.message
              : String(mutateError)}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>
              {viewMode === "reminders" ? "Upcoming Reminders" : "Recent Notes"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : error ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {error instanceof Error ? error.message : String(error)}
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
            ) : notes.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>
                  {viewMode === "reminders"
                    ? "No notes with upcoming reminders"
                    : "No notes yet. Add your first note to get started."}
                </p>
                {viewMode === "recent" && (
                  <Button
                    variant="outline"
                    className="mt-3"
                    onClick={handleAddNote}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Note
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {notes.map((note) => (
                  <div
                    key={note.id}
                    className="flex items-center justify-between p-4 border rounded-lg group"
                  >
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <FileText className="h-5 w-5 text-blue-500 shrink-0" />
                      <div className="min-w-0">
                        <div className="font-medium truncate">{note.title}</div>
                        <div className="text-sm text-gray-500 truncate">
                          {getApplicationLabel(note.application_id)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="text-right">
                        <div className="text-sm text-gray-500">
                          {formatRelativeTime(note.updated_at)}
                        </div>
                        <Badge variant="secondary">{note.category}</Badge>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditNote(note)}
                          aria-label="Edit note"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteNote(note)}
                          aria-label="Delete note"
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Note Templates</CardTitle>
          </CardHeader>
          <CardContent>
            {templatesQuery.isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : templates.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Tag className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No templates available</p>
              </div>
            ) : (
              <div className="space-y-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="p-4 border rounded-lg"
                  >
                    <div className="font-medium">{template.name}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      {template.content_template?.slice(0, 80)}...
                    </div>
                    <Badge
                      variant="outline"
                      className="mt-2"
                    >
                      {template.is_default ? "Popular" : template.category}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Note Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          {statsQuery.isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {stats.total_notes ?? 0}
                </div>
                <p className="text-sm text-gray-500">Total Notes</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.period_days ?? 30}
                </div>
                <p className="text-sm text-gray-500">Days Tracked</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {stats.reminder_notes ?? 0}
                </div>
                <p className="text-sm text-gray-500">With Reminders</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.pinned_notes ?? 0}
                </div>
                <p className="text-sm text-gray-500">Pinned</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Note Modal */}
      {showNoteModal && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="note-modal-title"
          onClick={(e) =>
            e.target === e.currentTarget &&
            (setShowNoteModal(false), setEditingNote(null))
          }
        >
          <FocusTrap
            active={showNoteModal}
            focusTrapOptions={{
              escapeDeactivates: true,
              allowOutsideClick: true,
              onDeactivate: () => {
                setShowNoteModal(false);
                setEditingNote(null);
              },
            }}
          >
            <div className="bg-white rounded-lg p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h2 id="note-modal-title" className="text-xl font-semibold">
                  {editingNote ? "Edit Note" : "Add Note"}
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowNoteModal(false);
                    setEditingNote(null);
                  }}
                >
                  ✕
                </Button>
              </div>

              <div className="space-y-4">
                {!editingNote && (
                  <div className="space-y-2">
                    <Label htmlFor="note-application">Application</Label>
                    {applications.length === 0 ? (
                      <p className="text-sm text-gray-500">
                        No applications yet. Create an application first to add
                        notes.
                      </p>
                    ) : (
                      <Select
                        value={formData.application_id}
                        onValueChange={(v) =>
                          setFormData((p) => ({ ...p, application_id: v }))
                        }
                      >
                        <SelectTrigger id="note-application">
                          <SelectValue placeholder="Select application" />
                        </SelectTrigger>
                        <SelectContent>
                          {applications.map((app) => (
                            <SelectItem key={app.id} value={app.id}>
                              {app.company} • {app.job_title}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="note-title">Title</Label>
                  <Input
                    id="note-title"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData((p) => ({ ...p, title: e.target.value }))
                    }
                    placeholder="Note title"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="note-content">Content</Label>
                  <Textarea
                    id="note-content"
                    value={formData.content}
                    onChange={(e) =>
                      setFormData((p) => ({ ...p, content: e.target.value }))
                    }
                    placeholder="Note content..."
                    rows={4}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="note-category">Category</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(v) =>
                      setFormData((p) => ({ ...p, category: v }))
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
                  onClick={() => {
                    setShowNoteModal(false);
                    setEditingNote(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmitNote}
                  disabled={
                    !formData.title ||
                    (!editingNote && !formData.application_id) ||
                    createNoteMutation.isPending ||
                    updateNoteMutation.isPending
                  }
                >
                  {(createNoteMutation.isPending ||
                    updateNoteMutation.isPending) && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  {editingNote ? "Save" : "Create"}
                </Button>
              </div>
            </div>
          </FocusTrap>
        </div>
      )}
    </div>
  );
};

export default ApplicationNotesPage;
