
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    RefreshCw,
    Globe,
    CheckCircle,
    XCircle,
    AlertTriangle,
    Clock,
    Database,
    Search,
    Activity
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { apiGet, apiPost } from "../../lib/api";
import { pushToast } from "../../lib/toast";

interface JobSource {
    source: string;
    total_jobs_fetched: number;
    last_sync_at: string | null;
    last_error_at: string | null;
    last_error_message: string | null;
    consecutive_failures: number;
    average_duration_ms: number;
}

interface SyncRun {
    source: string;
    status: "running" | "completed" | "failed";
    jobs_new: number;
    jobs_updated: number;
    duration_ms: number;
    started_at: string;
}

interface SyncStatus {
    sources: JobSource[];
    recent_runs: SyncRun[];
    job_stats: any[];
    circuit_breakers: Record<string, "closed" | "open" | "half-open">;
}

export default function AdminSourcesPage() {
    const queryClient = useQueryClient();
    const [isSyncing, setIsSyncing] = useState(false);

    const { data, isLoading, error, refetch } = useQuery<SyncStatus>({
        queryKey: ["admin", "jobs", "sync-status"],
        queryFn: async () => apiGet("admin/jobs/sync-status"),
        refetchInterval: 5000, // Poll every 5s to see progress
    });

    const triggerSync = useMutation({
        mutationFn: async () => apiPost("admin/jobs/sync", {}),
        onMutate: () => setIsSyncing(true),
        onSuccess: () => {
            pushToast({
                title: "Sync Started",
                description: "Job sync has been triggered in the background.",
                tone: "success",
            });
            // Invalidate query to refresh status immediately
            queryClient.invalidateQueries({ queryKey: ["admin", "jobs", "sync-status"] });
        },
        onError: (err: any) => {
            pushToast({
                title: "Sync Failed",
                description: err.message || "Could not trigger sync.",
                tone: "error",
            });
            setIsSyncing(false);
        },
        onSettled: () => {
            // Reset local loading state after a delay or let the polling handle status updates
            setTimeout(() => setIsSyncing(false), 2000);
        }
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12">
                <LoadingSpinner label="Loading sources..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6">
                <Card className="bg-red-50 border-red-200">
                    <div className="flex items-center gap-3 text-red-800">
                        <AlertTriangle className="h-5 w-5" />
                        <h3 className="font-bold">Error Loading Status</h3>
                    </div>
                    <p className="mt-2 text-red-600">{String(error)}</p>
                    <Button onClick={() => refetch()} className="mt-4" variant="outline">
                        Retry
                    </Button>
                </Card>
            </div>
        );
    }

    const sources = data?.sources || [];
    const recentRuns = data?.recent_runs || [];

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                        <Globe className="h-6 w-6 text-primary-600" />
                        Job Sources
                    </h1>
                    <p className="text-slate-500">Monitor and manage job scraping integrations</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        onClick={() => refetch()}
                        className="gap-2"
                    >
                        <RefreshCw className="h-4 w-4" />
                        Refresh
                    </Button>
                    <Button
                        onClick={() => triggerSync.mutate()}
                        disabled={triggerSync.isPending || isSyncing}
                        className="gap-2 bg-primary-600 hover:bg-primary-700 text-white"
                    >
                        {triggerSync.isPending || isSyncing ? (
                            <LoadingSpinner size="sm" />
                        ) : (
                            <Activity className="h-4 w-4" />
                        )}
                        Trigger Sync
                    </Button>
                </div>
            </div>

            {/* Status Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="p-6 border-slate-200 bg-white">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-slate-500">Active Sources</p>
                            <h3 className="text-3xl font-bold text-slate-900 mt-1">{sources.length}</h3>
                        </div>
                        <div className="p-2 bg-blue-50 rounded-lg">
                            <Database className="h-5 w-5 text-blue-600" />
                        </div>
                    </div>
                </Card>

                <Card className="p-6 border-slate-200 bg-white">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-slate-500">Total Jobs Fetched</p>
                            <h3 className="text-3xl font-bold text-slate-900 mt-1">
                                {sources.reduce((sum, s) => sum + s.total_jobs_fetched, 0).toLocaleString()}
                            </h3>
                        </div>
                        <div className="p-2 bg-emerald-50 rounded-lg">
                            <Search className="h-5 w-5 text-emerald-600" />
                        </div>
                    </div>
                </Card>

                <Card className="p-6 border-slate-200 bg-white">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-slate-500">Health Status</p>
                            <div className="flex items-center gap-2 mt-1">
                                {sources.every(s => s.consecutive_failures === 0) ? (
                                    <Badge variant="success">All Systems Operational</Badge>
                                ) : (
                                    <Badge variant="warning">{sources.filter(s => s.consecutive_failures > 0).length} Degradations</Badge>
                                )}
                            </div>
                        </div>
                        <div className="p-2 bg-purple-50 rounded-lg">
                            <Activity className="h-5 w-5 text-purple-600" />
                        </div>
                    </div>
                </Card>
            </div>

            {/* Sources Table */}
            <Card className="overflow-hidden border-slate-200 bg-white">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50">
                    <h3 className="font-semibold text-slate-900">Integration Status</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100">
                            <tr>
                                <th className="px-6 py-3 font-medium">Source</th>
                                <th className="px-6 py-3 font-medium">Status</th>
                                <th className="px-6 py-3 font-medium">Last Sync</th>
                                <th className="px-6 py-3 font-medium">Jobs Fetched</th>
                                <th className="px-6 py-3 font-medium">Failures</th>
                                <th className="px-6 py-3 font-medium">Circuit Breaker</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {sources.map((source) => (
                                <tr key={source.source} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-slate-900 capitalize flex items-center gap-2">
                                        <span className={`w-2 h-2 rounded-full ${source.consecutive_failures === 0 ? 'bg-emerald-500' : 'bg-red-500'}`} />
                                        {source.source}
                                    </td>
                                    <td className="px-6 py-4">
                                        {source.last_error_at ? (
                                            <div className="flex flex-col">
                                                <span className="text-red-600 font-medium">Error</span>
                                                <span className="text-xs text-red-500 truncate max-w-[200px]" title={source.last_error_message || ''}>
                                                    {source.last_error_message}
                                                </span>
                                            </div>
                                        ) : (
                                            <span className="text-emerald-600 font-medium">Healthy</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-slate-500">
                                        {source.last_sync_at ? (
                                            <div className="flex items-center gap-1">
                                                <Clock className="w-3 h-3" />
                                                {formatDistanceToNow(new Date(source.last_sync_at), { addSuffix: true })}
                                            </div>
                                        ) : (
                                            "Never"
                                        )}
                                    </td>
                                    <td className="px-6 py-4 font-mono text-slate-600">
                                        {source.total_jobs_fetched.toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        {source.consecutive_failures > 0 ? (
                                            <Badge variant="error">{source.consecutive_failures}</Badge>
                                        ) : (
                                            <span className="text-slate-400">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4">
                                        {data?.circuit_breakers[source.source] === 'open' ? (
                                            <Badge variant="error" className="animate-pulse">OPEN</Badge>
                                        ) : data?.circuit_breakers[source.source] === 'half-open' ? (
                                            <Badge variant="warning">HALF-OPEN</Badge>
                                        ) : (
                                            <Badge variant="success" className="bg-emerald-100 text-emerald-800 border-none">CLOSED</Badge>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {sources.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                                        No sources configured.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* Recent Activity Log */}
            <h3 className="font-bold text-slate-900 text-lg mt-8">Recent Sync Activity</h3>
            <Card className="overflow-hidden border-slate-200 bg-white">
                <div className="divide-y divide-slate-100">
                    {recentRuns.length > 0 ? recentRuns.map((run, i) => (
                        <div key={i} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                            <div className="flex items-center gap-4">
                                <div className={`p-2 rounded-full ${run.status === 'completed' ? 'bg-emerald-100 text-emerald-600' :
                                        run.status === 'failed' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600 animate-spin-slow'
                                    }`}>
                                    {run.status === 'completed' ? <CheckCircle className="w-5 h-5" /> :
                                        run.status === 'failed' ? <XCircle className="w-5 h-5" /> : <RefreshCw className="w-5 h-5" />}
                                </div>
                                <div>
                                    <p className="font-medium text-slate-900 capitalize">
                                        {run.source} Sync
                                    </p>
                                    <p className="text-xs text-slate-500">
                                        {formatDistanceToNow(new Date(run.started_at), { addSuffix: true })} • {run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : 'Ongoing'}
                                    </p>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-medium text-slate-900">
                                    +{run.jobs_new} New
                                </div>
                                <div className="text-xs text-slate-500">
                                    {run.jobs_updated} Updated
                                </div>
                            </div>
                        </div>
                    )) : (
                        <div className="p-8 text-center text-slate-400">No recent activity logs.</div>
                    )}
                </div>
            </Card>
        </div>
    );
}
