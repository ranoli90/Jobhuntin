import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { pushToast } from "../../lib/toast";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../lib/api";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ArrowLeft, Briefcase, Clock, CheckCircle, XCircle, AlertCircle, MessageSquare, FileText, History, Plus } from "lucide-react";
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

function statusVariant(status: string): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'APPLIED': return 'success';
    case 'HOLD': return 'warning';
    case 'FAILED':
    case 'REJECTED': return 'error';
    default: return 'default';
  }
}

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const locale = getLocale();

  const { data, isLoading, error } = useQuery({
    queryKey: ["application", id],
    queryFn: () => apiGet<ApplicationDetail>(`applications/${id}`),
    enabled: !!id,
  });

  if (!id) {
    navigate("/app/applications", { replace: true });
    return null;
  }

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6" aria-busy="true" aria-label="Loading application">
        <LoadingSpinner label="Loading application..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="p-8 text-center">
          <h2 className="text-xl font-bold text-slate-900 mb-2">Application not found</h2>
          <p className="text-slate-500 mb-4">This application may have been removed or you don&apos;t have access to it.</p>
          <Button onClick={() => navigate("/app/applications")} variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Applications
          </Button>
        </Card>
      </div>
    );
  }

  const app = data.application;
  React.useEffect(() => {
    if (app?.id) telemetry.track("application_viewed", { application_id: app.id, company: app.company, status: app.status });
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
              <h1 className="text-2xl font-bold text-slate-900">{app.company}</h1>
              <p className="text-slate-600 font-medium">{app.job_title}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={statusVariant(app.status ?? "")} className="text-sm">
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
            <h3 className="text-sm font-bold text-amber-900 dark:text-amber-100 uppercase tracking-wider mb-2">Needs your input</h3>
            <p className="text-slate-700 dark:text-slate-300">{app.hold_question}</p>
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
            <h2 className="text-lg font-bold text-slate-900">Application Questions</h2>
            <Badge variant="default" className="ml-auto">
              {data.inputs.length} {data.inputs.length === 1 ? 'question' : 'questions'}
            </Badge>
          </div>
          <div className="space-y-4">
            {data.inputs.map((input, idx) => (
              <div
                key={input.id || idx}
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
                        <Badge variant="success" className="text-xs">Resolved</Badge>
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
      {data.events && data.events.length > 0 && (
        <Card className="p-6" shadow="sm">
          <div className="flex items-center gap-2 mb-4">
            <History className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-bold text-slate-900">Application Timeline</h2>
            <Badge variant="default" className="ml-auto">
              {data.events.length} {data.events.length === 1 ? 'event' : 'events'}
            </Badge>
          </div>
          {/* Timeline visualization */}
          <div className="relative pl-8 border-l-2 border-slate-200 dark:border-slate-700">
            {data.events
              .sort((a, b) => {
                const aTime = a.created_at ? new Date(a.created_at).getTime() : 0;
                const bTime = b.created_at ? new Date(b.created_at).getTime() : 0;
                return bTime - aTime; // Most recent first
              })
              .map((event, idx) => {
                const eventType = event.event_type || "UNKNOWN";
                const eventDate = event.created_at ? formatDate(event.created_at, locale) : "Unknown date";
                const getEventIcon = () => {
                  if (eventType.includes("SUCCESS") || eventType.includes("APPLIED") || eventType.includes("COMPLETED")) {
                    return <CheckCircle className="w-5 h-5 text-green-600" />;
                  }
                  if (eventType.includes("FAILED") || eventType.includes("ERROR") || eventType.includes("REJECTED")) {
                    return <XCircle className="w-5 h-5 text-red-600" />;
                  }
                  if (eventType.includes("REQUIRES_INPUT") || eventType.includes("HOLD")) {
                    return <AlertCircle className="w-5 h-5 text-amber-600" />;
                  }
                  return <MessageSquare className="w-5 h-5 text-slate-600" />;
                };
                
                return (
                  <div key={event.id || idx} className="relative flex items-start gap-4 pb-6 last:pb-0">
                    {/* Timeline dot */}
                    <div className="absolute -left-[21px] w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 bg-slate-400 dark:bg-slate-600 z-10" />
                    <div className="flex-shrink-0 mt-1">
                      {getEventIcon()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {eventType.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-500 whitespace-nowrap">
                          {eventDate}
                        </span>
                      </div>
                      {event.properties && Object.keys(event.properties).length > 0 && (
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

      {/* LOW: Notes/Annotations Section */}
      <Card className="p-6" shadow="sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-bold text-slate-900">Notes</h2>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // TODO: Implement notes creation
              pushToast({ title: "Notes feature coming soon", tone: "info" });
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Note
          </Button>
        </div>
        <div className="text-center py-8 text-slate-500">
          <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>No notes yet. Add notes to track your thoughts about this application.</p>
        </div>
      </Card>

      {/* Empty states for missing data */}
      {(!data.inputs || data.inputs.length === 0) && (!data.events || data.events.length === 0) && (
        <Card className="p-8 text-center" shadow="sm">
          <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No additional details</h3>
          <p className="text-slate-500 mb-4">
            This application doesn't have any questions or events yet.
          </p>
        </Card>
      )}
    </div>
  );
}
