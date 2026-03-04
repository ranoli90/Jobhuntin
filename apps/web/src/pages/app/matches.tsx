import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
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
import { ErrorBoundary } from "../../components/ErrorBoundary";
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
    if (s >= 80) return "from-emerald-400 to-emerald-600";
    if (s >= 60) return "from-amber-400 to-amber-600";
    return "from-red-400 to-red-600";
  };

  const getScoreTextColor = (s: number) => {
    if (s >= 80) return "text-emerald-600";
    if (s >= 60) return "text-amber-600";
    return "text-red-600";
  };

  const getScoreBgColor = (s: number) => {
    if (s >= 80) return "bg-emerald-50 border-emerald-200";
    if (s >= 60) return "bg-amber-50 border-amber-200";
    return "bg-red-50 border-red-200";
  };

  return (
    <motion.div
      className={`p-4 rounded-lg border ${getScoreBgColor(score)}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-600">{label}</span>
        <motion.div
          className={`text-2xl font-bold ${getScoreTextColor(score)}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.2 }}
        >
          {score}%
        </motion.div>
      </div>
      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
        <motion.div
          className={`h-full bg-gradient-to-r ${getScoreColor(score)} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ delay: 0.2, duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>
    </motion.div>
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
    <motion.div className="space-y-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>
      <motion.button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full text-left"
        whileHover={{ backgroundColor: "rgba(0,0,0,0.02)" }}
        transition={{ duration: 0.15 }}
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
        <motion.div
          className="w-4 h-4 text-slate-400"
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown />
        </motion.div>
      </motion.button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            className="flex flex-wrap gap-2 pl-6"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
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
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function DealbreakerWarnings({ reasons }: { reasons: string[] }) {
  if (reasons.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="p-4 border-red-200 bg-red-50">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-red-900 mb-2">Dealbreaker Issues Detected</h4>
            <ul className="space-y-1">
              {reasons.map((reason, i) => (
                <motion.li
                  key={i}
                  className="text-sm text-red-700 flex items-center gap-2"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.2 }}
                >
                  <XCircle className="w-3 h-3" />
                  {reason}
                </motion.li>
              ))}
            </ul>
          </div>
        </div>
      </Card>
    </motion.div>
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
          <Button variant="primary" onClick={() => navigate("/app/jobs")}>Browse Jobs</Button>
        </Card>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50">
        <div className="max-w-4xl mx-auto p-6 space-y-8">
          <div className="flex items-center justify-between bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/50">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(-1)}
                className="gap-2 hover:bg-slate-100 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  AI-Powered Match Analysis
                </p>
                <h1 className="text-3xl font-black text-slate-900 bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                  Job Match Results
                </h1>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={handleShare} className="gap-2 hover:bg-slate-50 transition-colors">
                <Share2 className="w-4 h-4" />
                Share
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport} className="gap-2 hover:bg-slate-50 transition-colors">
                <Download className="w-4 h-4" />
                Export
              </Button>
            </div>
          </div>

          {match.loading && (
            <Card className="p-12 bg-gradient-to-br from-white to-blue-50/50 border-0 shadow-xl" aria-busy="true" aria-label="Loading match analysis">
              <div className="text-center space-y-6">
                <div className="w-20 h-20 mx-auto">
                  <div className="w-full h-full rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center shadow-2xl animate-pulse">
                    <Brain className="w-10 h-10 text-white animate-bounce" />
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-slate-900">Analyzing Your Match</h3>
                  <p className="text-slate-600">AI is processing your resume against this job...</p>
                </div>
                <div className="w-64 h-2 bg-slate-200 rounded-full mx-auto overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-full animate-pulse" style={{ width: '60%' }} />
                </div>
              </div>
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
              <Card className="p-8 bg-gradient-to-br from-slate-50 via-white to-slate-50 border-0 shadow-xl">
                <div className="flex items-center gap-6 mb-8">
                  <div
                    className={cn(
                      "w-24 h-24 rounded-3xl flex items-center justify-center shadow-2xl transition-all duration-500 hover:scale-110",
                      match.data.score >= 0.8
                        ? "bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-emerald-500/30"
                        : match.data.score >= 0.6
                          ? "bg-gradient-to-br from-amber-400 to-amber-600 shadow-amber-500/30"
                          : "bg-gradient-to-br from-red-400 to-red-600 shadow-red-500/30"
                    )}
                  >
                    <Sparkles
                      className={cn(
                        "w-10 h-10 text-white drop-shadow-lg",
                        match.data.score >= 0.8
                          ? "animate-pulse"
                          : match.data.score >= 0.6
                            ? "animate-bounce"
                            : ""
                      )}
                    />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-baseline gap-3 mb-2">
                      <h2 className="text-5xl font-black text-slate-900 bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                        {Math.round(match.data.score * 100)}%
                      </h2>
                      <span className="text-lg font-semibold text-slate-600">Match</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge
                        variant={
                          match.data.confidence === "high"
                            ? "success"
                            : match.data.confidence === "medium"
                              ? "warning"
                              : "error"
                        }
                        className="px-3 py-1"
                      >
                        {match.data.confidence} confidence
                      </Badge>
                      {match.data.passed_dealbreakers ? (
                        <Badge variant="success" className="px-3 py-1">
                          ✓ Dealbreakers Passed
                        </Badge>
                      ) : (
                        <Badge variant="error" className="px-3 py-1">
                          ✗ Dealbreakers Failed
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-3 gap-4">
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

              <Card className="p-6 bg-gradient-to-br from-blue-50 via-white to-indigo-50 border-0 shadow-lg">
                <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  Skill Analysis
                </h3>

                <div className="space-y-5">
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

              <Card className="p-6 bg-gradient-to-br from-purple-50 via-white to-pink-50 border-0 shadow-lg">
                <button
                  onClick={() => setExpandedExplanation(!expandedExplanation)}
                  className="w-full text-left group"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-slate-900 flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-lg transition-transform group-hover:scale-110">
                        <TrendingUp className="w-5 h-5 text-white" />
                      </div>
                      AI Analysis
                    </h3>
                    {expandedExplanation ? (
                      <ChevronUp className="w-6 h-6 text-slate-400 transition-transform group-hover:text-slate-600" />
                    ) : (
                      <ChevronDown className="w-6 h-6 text-slate-400 transition-transform group-hover:text-slate-600" />
                    )}
                  </div>
                </button>
                <div className={cn(
                  "overflow-hidden transition-all duration-500 ease-in-out",
                  expandedExplanation ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
                )}>
                  <div className="p-4 bg-white/70 rounded-xl border border-white/50 shadow-sm">
                    <p className="text-slate-700 leading-relaxed text-sm">
                      {match.data.reasoning}
                    </p>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}
