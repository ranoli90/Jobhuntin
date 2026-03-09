import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../lib/api";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ArrowLeft, Briefcase, Clock } from "lucide-react";
import { formatDate } from "../../lib/format";
import { getLocale } from "../../lib/i18n";
import { telemetry } from "../../lib/telemetry";

interface ApplicationDetail {
  application: {
    id: string;
    job_title?: string;
    company?: string;
    status?: string;
    hold_question?: string;
    last_activity?: string;
  };
  inputs: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
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
    </div>
  );
}
