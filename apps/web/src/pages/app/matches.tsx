import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  Share2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  Target,
  Brain,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ErrorBoundaryAI } from "../../components/ui/ErrorBoundaryAI";
import { useSemanticMatch } from "../../hooks/useAIEndpoints";
import { useFeatureFlag } from "../../hooks/useFeatureFlags";
import { cn } from "../../lib/utils";
import { pushToast } from "../../lib/toast";

interface SkillGap {
  skill: string;
  importance: "critical" | "important" | "nice_to_have";
  present: boolean;
}

function ScoreVisualization({ score, label }: { score: number; label: string }) {
  const getScoreColor = (s: number) => {
    if (s >= 80) return "bg-emerald-500";
    if (s >= 60) return "bg-amber-500";
    return "bg-red-500";
  };

  const getScoreTextColor = (s: number) => {
    if (s >= 80) return "text-emerald-600";
    if (s >= 60) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-slate-600">{label}</span>
        <span className={cn("text-lg font-bold", getScoreTextColor(score))}>
          {Math.round(score)}%
        </span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", getScoreColor(score))}
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
    </div>
  );
}

function SkillList({
  skills,
  title,
  variant,
}: {
  skills: string[];
  title: string;
  variant: "matched" | "missing";
}) {
  const [expanded, setExpanded] = useState(true);

  if (skills.length === 0) return null;

  return (
    <div className="space-y-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          {variant === "matched" ? (
            <CheckCircle className="w-4 h-4 text-emerald-500" />
          ) : (
            <XCircle className="w-4 h-4 text-red-500" />
          )}
          {title}
          <Badge variant={variant === "matched" ? "success" : "error"} size="sm">
            {skills.length}
          </Badge>
        </h4>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>
      {expanded && (
        <div className="flex flex-wrap gap-2 pl-6">
          {skills.map((skill, i) => (
            <Badge
              key={i}
              variant={variant === "matched" ? "success" : "error"}
              size="sm"
              className="text-xs"
            >
              {skill}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function DealbreakerWarnings({ reasons }: { reasons: string[] }) {
  if (reasons.length === 0) return null;

  return (
    <Card className="p-4 border-red-200 bg-red-50">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-red-900 mb-2">Dealbreaker Issues Detected</h4>
          <ul className="space-y-1">
            {reasons.map((reason, i) => (
              <li key={i} className="text-sm text-red-700 flex items-center gap-2">
                <XCircle className="w-3 h-3" />
                {reason}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
}

export default function MatchesPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const match = useSemanticMatch();
  const semanticMatchingEnabled = useFeatureFlag("semantic_matching");

  const jobId = searchParams.get("jobId");
  const [expandedExplanation, setExpandedExplanation] = useState(false);

  useEffect(() => {
    if (!semanticMatchingEnabled) {
      pushToast({
        title: "Feature Disabled",
        description: "Semantic matching is not enabled for your account.",
        tone: "warning",
      });
      navigate("/app/jobs");
    }
  }, [semanticMatchingEnabled, navigate]);

  const handleExport = () => {
    if (!match.data) return;

    const exportData = {
      job_id: match.data.job_id,
      score: match.data.score,
      matched_skills: match.data.matched_skills,
      missing_skills: match.data.missing_skills,
      reasoning: match.data.reasoning,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `match-report-${match.data.job_id}.json`;
    a.click();
    URL.revokeObjectURL(url);

    pushToast({
      title: "Export Complete",
      description: "Match report downloaded successfully.",
      tone: "success",
    });
  };

  const handleShare = async () => {
    if (!match.data) return;

    const shareData = {
      title: `Job Match Report`,
      text: `Match Score: ${Math.round(match.data.score * 100)}% - ${match.data.reasoning.slice(0, 100)}...`,
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch {
        pushToast({
          title: "Share Cancelled",
          description: "Share operation was cancelled.",
          tone: "neutral",
        });
      }
    } else {
      await navigator.clipboard.writeText(window.location.href);
      pushToast({
        title: "Link Copied",
        description: "Match report link copied to clipboard.",
        tone: "success",
      });
    }
  };

  if (!jobId) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="p-8 text-center">
          <Target className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-900 mb-2">No Job Selected</h2>
          <p className="text-slate-500 mb-6">
            Select a job from the job feed to view match details.
          </p>
          <Button onClick={() => navigate("/app/jobs")}>Browse Jobs</Button>
        </Card>
      </div>
    );
  }

  return (
    <ErrorBoundaryAI>
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
              className="gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Semantic Match Analysis
              </p>
              <h1 className="text-2xl font-bold text-slate-900">Match Results</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleShare} className="gap-2">
              <Share2 className="w-4 h-4" />
              Share
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport} className="gap-2">
              <Download className="w-4 h-4" />
              Export
            </Button>
          </div>
        </div>

        {match.loading && (
          <Card className="p-12">
            <LoadingSpinner label="Analyzing job match..." />
          </Card>
        )}

        {match.error && (
          <Card className="p-6 border-red-200 bg-red-50">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <div>
                <h3 className="font-semibold text-red-900">Analysis Failed</h3>
                <p className="text-sm text-red-700">{match.error}</p>
              </div>
            </div>
          </Card>
        )}

        {match.data && (
          <>
            <Card className="p-6">
              <div className="flex items-center gap-4 mb-6">
                <div
                  className={cn(
                    "w-20 h-20 rounded-2xl flex items-center justify-center",
                    match.data.score >= 0.8
                      ? "bg-emerald-100"
                      : match.data.score >= 0.6
                        ? "bg-amber-100"
                        : "bg-red-100"
                  )}
                >
                  <Sparkles
                    className={cn(
                      "w-8 h-8",
                      match.data.score >= 0.8
                        ? "text-emerald-600"
                        : match.data.score >= 0.6
                          ? "text-amber-600"
                          : "text-red-600"
                    )}
                  />
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-slate-900">
                    {Math.round(match.data.score * 100)}% Match
                  </h2>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge
                      variant={
                        match.data.confidence === "high"
                          ? "success"
                          : match.data.confidence === "medium"
                            ? "warning"
                            : "error"
                      }
                    >
                      {match.data.confidence} confidence
                    </Badge>
                    {match.data.passed_dealbreakers ? (
                      <Badge variant="success">Passed Dealbreakers</Badge>
                    ) : (
                      <Badge variant="error">Failed Dealbreakers</Badge>
                    )}
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <ScoreVisualization
                  score={match.data.semantic_similarity * 100}
                  label="Semantic Similarity"
                />
                <ScoreVisualization
                  score={match.data.skill_match_ratio * 100}
                  label="Skill Match"
                />
                <ScoreVisualization
                  score={match.data.experience_alignment * 100}
                  label="Experience Alignment"
                />
              </div>
            </Card>

            <DealbreakerWarnings reasons={match.data.dealbreaker_reasons} />

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5 text-primary-500" />
                Skill Gap Analysis
              </h3>

              <div className="space-y-4">
                <SkillList
                  skills={match.data.matched_skills}
                  title="Matched Skills"
                  variant="matched"
                />
                <SkillList
                  skills={match.data.missing_skills}
                  title="Missing Skills"
                  variant="missing"
                />
              </div>
            </Card>

            <Card className="p-6">
              <button
                onClick={() => setExpandedExplanation(!expandedExplanation)}
                className="flex items-center justify-between w-full text-left"
              >
                <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary-500" />
                  Match Explanation
                </h3>
                {expandedExplanation ? (
                  <ChevronUp className="w-5 h-5 text-slate-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                )}
              </button>
              {expandedExplanation && (
                <div className="mt-4 p-4 bg-slate-50 rounded-lg">
                  <p className="text-slate-700 leading-relaxed">
                    {match.data.reasoning}
                  </p>
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </ErrorBoundaryAI>
  );
}
