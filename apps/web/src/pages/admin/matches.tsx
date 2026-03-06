import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Edit2,
  Eye,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { cn } from "../../lib/utils";
import { apiGet, apiPatch } from "../../lib/api";
import { pushToast } from "../../lib/toast";

interface MatchRecord {
  id: string;
  job_id: string;
  job_title: string;
  company: string;
  tenant_id: string;
  tenant_name: string;
  user_id: string;
  score: number;
  passed_dealbreakers: boolean;
  status: "completed" | "failed" | "pending";
  created_at: string;
}

interface MatchesData {
  matches: MatchRecord[];
  total: number;
  page: number;
  per_page: number;
  success_rate: number;
}

const mockMatchesData: MatchesData = {
  matches: [
    { id: "1", job_id: "j1", job_title: "Retail Associate", company: "Walmart", tenant_id: "t1", tenant_name: "Walmart", user_id: "u1", score: 92, passed_dealbreakers: true, status: "completed", created_at: "2026-02-12T10:30:00Z" },
    { id: "2", job_id: "j2", job_title: "Cashier", company: "Target", tenant_id: "t2", tenant_name: "Target Inc", user_id: "u2", score: 78, passed_dealbreakers: true, status: "completed", created_at: "2026-02-12T09:45:00Z" },
    { id: "3", job_id: "j3", job_title: "Sales Associate", company: "Best Buy", tenant_id: "t3", tenant_name: "Best Buy", user_id: "u3", score: 45, passed_dealbreakers: false, status: "completed", created_at: "2026-02-12T09:30:00Z" },
    { id: "4", job_id: "j4", job_title: "Customer Service", company: "Amazon", tenant_id: "t4", tenant_name: "Amazon", user_id: "u4", score: 0, passed_dealbreakers: false, status: "failed", created_at: "2026-02-12T09:15:00Z" },
    { id: "5", job_id: "j5", job_title: "Warehouse Worker", company: "Costco", tenant_id: "t1", tenant_name: "Costco", user_id: "u1", score: 85, passed_dealbreakers: true, status: "completed", created_at: "2026-02-12T08:00:00Z" },
  ],
  total: 1250,
  page: 1,
  per_page: 20,
  success_rate: 94.5,
};

export default function AdminMatchesPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [matchesData, setMatchesData] = useState<MatchesData | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [tenantFilter, setTenantFilter] = useState("");
  const [scoreMin, setScoreMin] = useState("");
  const [scoreMax, setScoreMax] = useState("");
  const [editingMatch, setEditingMatch] = useState<string | null>(null);
  const [overrideScore, setOverrideScore] = useState<number>(0);

  const page = Number.parseInt(searchParams.get("page") || "1", 10);

  useEffect(() => {
    async function fetchMatches() {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          page: page.toString(),
          ...(tenantFilter && { tenant: tenantFilter }),
          ...(scoreMin && { score_min: scoreMin }),
          ...(scoreMax && { score_max: scoreMax }),
        });
        const data = await apiGet<MatchesData>(`admin/matches?${params}`);
        setMatchesData(data);
      } catch {
        setMatchesData(mockMatchesData);
      } finally {
        setLoading(false);
      }
    }

    fetchMatches();
  }, [page, tenantFilter, scoreMin, scoreMax]);

  const handleOverride = async (matchId: string) => {
    try {
      await apiPatch(`admin/matches/${matchId}/override`, { score: overrideScore });
      pushToast({
        title: "Score Overridden",
        description: `Match ${matchId} score updated to ${overrideScore}`,
        tone: "success",
      });
      setEditingMatch(null);
    } catch {
      pushToast({
        title: "Override Failed",
        description: "Could not update match score.",
        tone: "error",
      });
    }
  };

  const handlePageChange = (newPage: number) => {
    setSearchParams({ page: newPage.toString() });
  };

  const getScoreBadge = (score: number) => {
    if (score >= 80) return <Badge variant="success">{score}%</Badge>;
    if (score >= 60) return <Badge variant="warning">{score}%</Badge>;
    return <Badge variant="error">{score}%</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner label="Loading matches..." />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Admin</p>
            <h1 className="text-2xl font-bold text-slate-900">Match Monitoring</h1>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Total Matches</p>
              <p className="text-2xl font-bold text-slate-900">{matchesData?.total.toLocaleString()}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-emerald-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Success Rate</p>
              <p className="text-2xl font-bold text-slate-900">{matchesData?.success_rate}%</p>
            </div>
            <CheckCircle className="w-8 h-8 text-primary-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Failed Matches</p>
              <p className="text-2xl font-bold text-slate-900">
                {Math.round((matchesData?.total ?? 0) * (1 - (matchesData?.success_rate ?? 100) / 100))}
              </p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </Card>
      </div>

      <Card className="p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by job title or company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none"
              />
            </div>
          </div>
          <select
            value={tenantFilter}
            onChange={(e) => setTenantFilter(e.target.value)}
            className="px-4 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none"
          >
            <option value="">All Tenants</option>
            <option value="t1">Acme Corp</option>
            <option value="t2">TechStart Inc</option>
            <option value="t3">Global Systems</option>
          </select>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <input
              type="number"
              placeholder="Min score"
              value={scoreMin}
              onChange={(e) => setScoreMin(e.target.value)}
              className="w-24 px-3 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none"
            />
            <span className="text-slate-400">-</span>
            <input
              type="number"
              placeholder="Max score"
              value={scoreMax}
              onChange={(e) => setScoreMax(e.target.value)}
              className="w-24 px-3 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none"
            />
          </div>
        </div>
      </Card>

      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Job
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Tenant
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Score
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Dealbreakers
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {matchesData?.matches.map((match) => (
                <tr key={match.id} className="hover:bg-slate-50">
                  <td className="py-4 px-4">
                    <p className="font-medium text-slate-900">{match.job_title}</p>
                    <p className="text-xs text-slate-500">{match.company}</p>
                  </td>
                  <td className="py-4 px-4">
                    <p className="text-sm text-slate-700">{match.tenant_name}</p>
                  </td>
                  <td className="py-4 px-4">
                    {editingMatch === match.id ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          value={overrideScore}
                          onChange={(e) => setOverrideScore(Number.parseInt(e.target.value, 10))}
                          className="w-16 px-2 py-1 rounded border border-slate-200 text-sm"
                        />
                        <Button size="sm" onClick={() => handleOverride(match.id)}>
                          Save
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setEditingMatch(null)}>
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      getScoreBadge(match.score)
                    )}
                  </td>
                  <td className="py-4 px-4">
                    {match.passed_dealbreakers ? (
                      <CheckCircle className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-amber-500" />
                    )}
                  </td>
                  <td className="py-4 px-4">
                    <Badge
                      variant={
                        match.status === "completed"
                          ? "success"
                          : match.status === "failed"
                            ? "error"
                            : "warning"
                      }
                    >
                      {match.status}
                    </Badge>
                  </td>
                  <td className="py-4 px-4 text-sm text-slate-500">
                    {new Date(match.created_at).toLocaleString()}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditingMatch(match.id);
                          setOverrideScore(match.score);
                        }}
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/app/matches?jobId=${match.job_id}`)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {matchesData && matchesData.total > matchesData.per_page && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">
            Showing {(page - 1) * matchesData.per_page + 1} -{" "}
            {Math.min(page * matchesData.per_page, matchesData.total)} of {matchesData.total}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => handlePageChange(page - 1)}
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page * matchesData.per_page >= matchesData.total}
              onClick={() => handlePageChange(page + 1)}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
