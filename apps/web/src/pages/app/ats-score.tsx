import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Upload,
  FileText,
  AlertTriangle,
  TrendingUp,
  Download,
  CheckCircle,
  XCircle,
  Target,
  Globe,
  Sparkles,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ErrorBoundaryAI } from "../../components/ui/ErrorBoundaryAI";
import { useATSScore } from "../../hooks/useAIEndpoints";
import { useFeatureFlag } from "../../hooks/useFeatureFlags";
import { cn } from "../../lib/utils";
import { pushToast } from "../../lib/toast";

const ATS_PLATFORMS = [
  "Greenhouse",
  "Lever",
  "Workday",
  "iCIMS",
  "Taleo",
  "BrassRing",
  "Jobvite",
  "SmartRecruiters",
  "Recruitee",
  "BambooHR",
  "Ashby",
  "Hired",
];

const ATS_METRICS: { key: string; label: string; description: string }[] = [
  { key: "keyword_match", label: "Keyword Match", description: "How well your resume matches job keywords" },
  { key: "skills_relevance", label: "Skills Relevance", description: "Relevance of skills to the job" },
  { key: "experience_alignment", label: "Experience Alignment", description: "Alignment of experience with job requirements" },
  { key: "quantifiable_achievements", label: "Quantifiable Achievements", description: "Presence of metrics and achievements" },
  { key: "action_verbs", label: "Action Verbs", description: "Use of strong action verbs" },
  { key: "format_score", label: "Format Score", description: "Resume formatting compatibility" },
  { key: "section_completeness", label: "Section Completeness", description: "All required sections present" },
  { key: "contact_info", label: "Contact Info", description: "Complete contact information" },
  { key: "summary_quality", label: "Summary Quality", description: "Professional summary effectiveness" },
  { key: "education_relevance", label: "Education Relevance", description: "Education section relevance" },
  { key: "certification_match", label: "Certifications", description: "Relevant certifications included" },
  { key: "readability_score", label: "Readability", description: "Overall readability and clarity" },
  { key: "length_score", label: "Length Score", description: "Appropriate resume length" },
  { key: "ats_compatibility", label: "ATS Compatibility", description: "General ATS system compatibility" },
  { key: "spelling_grammar", label: "Spelling & Grammar", description: "Error-free writing" },
  { key: "consistency", label: "Consistency", description: "Consistent formatting throughout" },
  { key: "dates_format", label: "Date Format", description: "Proper date formatting" },
  { key: "bullet_points", label: "Bullet Points", description: "Effective bullet point usage" },
  { key: "file_format", label: "File Format", description: "Compatible file format" },
  { key: "personalization", label: "Personalization", description: "Tailored to the job" },
  { key: "industry_keywords", label: "Industry Keywords", description: "Industry-specific terminology" },
  { key: "soft_skills", label: "Soft Skills", description: "Relevant soft skills mentioned" },
  { key: "technical_skills", label: "Technical Skills", description: "Technical skills visibility" },
];

function MetricBar({ label, value, description }: { label: string; value: number; description: string }) {
  const getColor = (v: number) => {
    if (v >= 0.7) return "bg-emerald-500";
    if (v >= 0.5) return "bg-amber-500";
    return "bg-red-500";
  };

  const getTextColor = (v: number) => {
    if (v >= 0.7) return "text-emerald-600";
    if (v >= 0.5) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-1" title={description}>
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">{label}</span>
        <span className={cn("text-sm font-semibold", getTextColor(value))}>
          {Math.round(value * 100)}%
        </span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", getColor(value))}
          style={{ width: `${Math.min(100, value * 100)}%` }}
        />
      </div>
    </div>
  );
}

export default function ATSScorePage() {
  const navigate = useNavigate();
  const atsScore = useATSScore();
  const atsScoringEnabled = useFeatureFlag("ats_scoring");

  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [detectedPlatform, setDetectedPlatform] = useState<string | null>(null);

  const handleScore = async () => {
    if (!resumeText) {
      pushToast({
        title: "Missing Resume",
        description: "Please enter your resume text.",
        tone: "warning",
      });
      return;
    }

    if (!jobDescription) {
      pushToast({
        title: "Missing Job Description",
        description: "Please enter the job description.",
        tone: "warning",
      });
      return;
    }

    const platform = detectPlatform(jobDescription);
    setDetectedPlatform(platform);

    await atsScore.score({
      resume_text: resumeText,
      job_description: jobDescription,
    });
  };

  const detectPlatform = (text: string): string | null => {
    const lower = text.toLowerCase();
    for (const platform of ATS_PLATFORMS) {
      if (lower.includes(platform.toLowerCase())) {
        return platform;
      }
    }
    return null;
  };

  const handleExport = () => {
    if (!atsScore.data) return;

    const exportData = {
      overall_score: atsScore.data.overall_score,
      metrics: atsScore.data.metrics,
      recommendations: atsScore.data.recommendations,
      detected_platform: detectedPlatform,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ats-score-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    pushToast({
      title: "Report Exported",
      description: "ATS score report downloaded successfully.",
      tone: "success",
    });
  };

  return (
    <ErrorBoundaryAI onRetry={handleScore}>
      <div className="max-w-5xl mx-auto p-6 space-y-6">
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
                AI Tools
              </p>
              <h1 className="text-2xl font-bold text-slate-900">ATS Score Dashboard</h1>
            </div>
          </div>
          {atsScore.data && (
            <Button variant="outline" size="sm" onClick={handleExport} className="gap-2">
              <Download className="w-4 h-4" />
              Export Report
            </Button>
          )}
        </div>

        {!atsScoringEnabled && (
          <Card className="p-4 border-amber-200 bg-amber-50">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <p className="text-sm text-amber-700">
                ATS scoring is not enabled for your account.
              </p>
            </div>
          </Card>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          <Card className="p-6 space-y-4">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary-500" />
              Your Resume
            </h3>
            <textarea
              placeholder="Paste your resume text here..."
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={12}
              className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none resize-none font-mono"
            />
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <Target className="w-5 h-5 text-primary-500" />
              Job Description
            </h3>
            <textarea
              placeholder="Paste the job description here..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={12}
              className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none resize-none font-mono"
            />
          </Card>
        </div>

        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={handleScore}
            disabled={atsScore.loading || !atsScoringEnabled}
            className="gap-2 px-8"
          >
            <Sparkles className="w-5 h-5" />
            Calculate ATS Score
          </Button>
        </div>

        {atsScore.loading && (
          <Card className="p-12">
            <LoadingSpinner label="Analyzing resume against job description..." />
          </Card>
        )}

        {atsScore.error && (
          <Card className="p-4 border-red-200 bg-red-50">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <div>
                <h4 className="font-semibold text-red-900">Scoring Failed</h4>
                <p className="text-sm text-red-700">{atsScore.error}</p>
              </div>
            </div>
          </Card>
        )}

        {atsScore.data && (
          <div className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div
                    className={cn(
                      "w-16 h-16 rounded-2xl flex items-center justify-center",
                      atsScore.data.overall_score >= 0.7
                        ? "bg-emerald-100"
                        : atsScore.data.overall_score >= 0.5
                          ? "bg-amber-100"
                          : "bg-red-100"
                    )}
                  >
                    <TrendingUp
                      className={cn(
                        "w-7 h-7",
                        atsScore.data.overall_score >= 0.7
                          ? "text-emerald-600"
                          : atsScore.data.overall_score >= 0.5
                            ? "text-amber-600"
                            : "text-red-600"
                      )}
                    />
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold text-slate-900">
                      {Math.round(atsScore.data.overall_score * 100)}%
                    </h2>
                    <p className="text-sm text-slate-500">Overall ATS Score</p>
                  </div>
                </div>
                {detectedPlatform && (
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-slate-400" />
                    <Badge variant="outline">{detectedPlatform}</Badge>
                  </div>
                )}
              </div>

              <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-700",
                    atsScore.data.overall_score >= 0.7
                      ? "bg-emerald-500"
                      : atsScore.data.overall_score >= 0.5
                        ? "bg-amber-500"
                        : "bg-red-500"
                  )}
                  style={{ width: `${Math.min(100, atsScore.data.overall_score * 100)}%` }}
                />
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold text-slate-900 mb-4">23 Metrics Analysis</h3>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {ATS_METRICS.map((metric) => (
                  <MetricBar
                    key={metric.key}
                    label={metric.label}
                    value={atsScore.data!.metrics[metric.key] ?? 0}
                    description={metric.description}
                  />
                ))}
              </div>
            </Card>

            {atsScore.data.recommendations.length > 0 && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-500" />
                  Optimization Recommendations
                </h3>
                <ul className="space-y-3">
                  {atsScore.data.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-xs font-bold text-amber-600">{i + 1}</span>
                      </div>
                      <p className="text-sm text-slate-700">{rec}</p>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
        )}
      </div>
    </ErrorBoundaryAI>
  );
}
