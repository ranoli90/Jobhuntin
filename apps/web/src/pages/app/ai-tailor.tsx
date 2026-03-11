import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Upload,
  FileText,
  Link,
  Loader2,
  Download,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { ErrorBoundary } from "../../components/ErrorBoundary";
import { useResumeTailor, useATSScore } from "../../hooks/useAIEndpoints";
import { useFeatureFlag } from "../../hooks/useFeatureFlags";
import { cn } from "../../lib/utils";
import { pushToast } from "../../lib/toast";
import { apiPostFormData } from "../../lib/api";

export default function AITailorPage() {
  const navigate = useNavigate();
  const tailor = useResumeTailor();
  const atsScore = useATSScore();
  const tailoringEnabled = useFeatureFlag("resume_tailoring");

  const MAX_FILE_SIZE_MB = 5;
  const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [inputMode, setInputMode] = useState<"url" | "paste">("url");
  const [beforeScore, setBeforeScore] = useState<number | null>(null);
  const [afterScore, setAfterScore] = useState<number | null>(null);
  const [parseError, setParseError] = useState<{ file: string; message: string } | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const fileInputReference = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      pushToast({
        title: "Invalid File Type",
        description: "Please upload a PDF file.",
        tone: "error",
      });
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      pushToast({
        title: "File Too Large",
        description: `Please upload a PDF under ${MAX_FILE_SIZE_MB}MB. Your file is ${(file.size / 1024 / 1024).toFixed(1)}MB.`,
        tone: "error",
      });
      return;
    }

    setResumeFile(file);
    setParseError(null);

    const formData = new FormData();
    formData.append("file", file);

    setIsParsing(true);
    try {
      const result = await apiPostFormData<{ text: string }>(
        "parse-resume",
        formData,
      );
      setResumeText(result.text);
      setParseError(null);
      pushToast({
        title: "Resume Uploaded",
        description: "Resume parsed successfully.",
        tone: "success",
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not parse resume.";
      setParseError({ file: file.name, message });
      pushToast({
        title: "Parse Failed",
        description: `${file.name}: ${message}. Click "Try again" below to retry.`,
        tone: "error",
      });
    } finally {
      setIsParsing(false);
    }
  };

  const handleRetryParse = async () => {
    if (!resumeFile) return;
    setParseError(null);
    setIsParsing(true);
    try {
      const formData = new FormData();
      formData.append("file", resumeFile);
      const result = await apiPostFormData<{ text: string }>(
        "parse-resume",
        formData,
      );
      setResumeText(result.text);
      pushToast({
        title: "Resume Uploaded",
        description: "Resume parsed successfully.",
        tone: "success",
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not parse resume.";
      setParseError({ file: resumeFile.name, message });
      pushToast({
        title: "Parse Failed",
        description: `${resumeFile.name}: ${message}. Click "Try again" below to retry.`,
        tone: "error",
      });
    } finally {
      setIsParsing(false);
    }
  };

  const handleTailor = async () => {
    if (!resumeText) {
      pushToast({
        title: "Missing Resume",
        description: "Please upload your resume first.",
        tone: "warning",
      });
      return;
    }

    if (inputMode === "url" && !jobUrl) {
      pushToast({
        title: "Missing Job URL",
        description: "Please enter a job URL.",
        tone: "warning",
      });
      return;
    }

    if (inputMode === "paste" && !jobDescription) {
      pushToast({
        title: "Missing Job Description",
        description: "Please paste the job description.",
        tone: "warning",
      });
      return;
    }

    if (beforeScore === null) {
      const beforeScoreResult = await atsScore.score({
        resume_text: resumeText,
        job_description: jobDescription,
      });
      if (beforeScoreResult) {
        setBeforeScore(beforeScoreResult.overall_score);
      }
    }

    const result = await tailor.tailor({
      profile: { resume_text: resumeText },
      job: { url: jobUrl, description: jobDescription },
    });

    if (result) {
      const afterScoreResult = await atsScore.score({
        resume_text: result.tailored_summary,
        job_description: jobDescription,
      });
      if (afterScoreResult) {
        setAfterScore(afterScoreResult.overall_score);
      }
    }
  };

  const handleDownload = () => {
    if (!tailor.data) return;

    const content = tailor.data.tailored_summary;
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tailored-resume.txt";
    a.click();
    URL.revokeObjectURL(url);

    pushToast({
      title: "Downloaded",
      description: "Tailored resume downloaded successfully.",
      tone: "success",
    });
  };

  const handleReset = () => {
    setResumeFile(null);
    setResumeText("");
    setJobUrl("");
    setJobDescription("");
    setBeforeScore(null);
    setAfterScore(null);
    setParseError(null);
    tailor.reset();
    atsScore.reset();
  };

  return (
    <ErrorBoundary>
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
                AI Tools
              </p>
              <h1 className="text-2xl font-bold text-slate-900">
                Resume Tailor
              </h1>
            </div>
          </div>
          {tailor.data && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Start Over
            </Button>
          )}
        </div>

        {!tailoringEnabled && (
          <Card className="p-4 border-amber-200 bg-amber-50">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <p className="text-sm text-amber-700">
                Resume tailoring is not enabled for your account.
              </p>
            </div>
          </Card>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          <Card className="p-6 space-y-4">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <Upload className="w-5 h-5 text-primary-500" />
              Upload Resume
            </h3>

            <input
              ref={fileInputReference}
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
            />

            <div
              onClick={() => !parseError && fileInputReference.current?.click()}
              className={cn(
                "border-2 border-dashed rounded-xl p-8 text-center transition-colors",
                parseError
                  ? "border-red-200 bg-red-50 cursor-default"
                  : "cursor-pointer",
                resumeFile && !parseError
                  ? "border-emerald-300 bg-emerald-50"
                  : !parseError && "border-slate-200 hover:border-slate-300 hover:bg-slate-50",
              )}
            >
              {parseError ? (
                <div className="space-y-3">
                  <AlertTriangle className="w-8 h-8 text-red-500 mx-auto" />
                  <p className="font-medium text-red-700">{parseError.file}</p>
                  <p className="text-sm text-red-600">{parseError.message}</p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRetryParse();
                    }}
                    disabled={isParsing}
                    className="gap-2"
                  >
                    {isParsing ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <RefreshCw className="w-4 h-4" />
                    )}
                    Try again
                  </Button>
                </div>
              ) : resumeFile ? (
                <div className="space-y-2">
                  {isParsing ? (
                    <Loader2 className="w-8 h-8 text-primary-500 mx-auto animate-spin" />
                  ) : (
                    <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto" />
                  )}
                  <p className="font-medium text-emerald-700">
                    {resumeFile.name}
                  </p>
                  <p className="text-xs text-emerald-600">Click to change</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <FileText className="w-8 h-8 text-slate-400 mx-auto" />
                  <p className="font-medium text-slate-600">
                    Drop your resume here or click to upload
                  </p>
                  <p className="text-xs text-slate-400">PDF only, max 5MB</p>
                </div>
              )}
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary-500" />
              Job Details
            </h3>

            <div className="flex gap-2 mb-4">
              <Button
                variant={inputMode === "url" ? "primary" : "outline"}
                size="sm"
                onClick={() => setInputMode("url")}
                className="flex-1 gap-2"
              >
                <Link className="w-4 h-4" />
                URL
              </Button>
              <Button
                variant={inputMode === "paste" ? "primary" : "outline"}
                size="sm"
                onClick={() => setInputMode("paste")}
                className="flex-1 gap-2"
              >
                <FileText className="w-4 h-4" />
                Paste
              </Button>
            </div>

            {inputMode === "url" ? (
              <input
                type="url"
                placeholder="https://example.com/jobs/..."
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none"
              />
            ) : (
              <textarea
                placeholder="Paste the job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={6}
                className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none resize-none"
              />
            )}
          </Card>
        </div>

        {tailor.progress > 0 && tailor.progress < 100 && (
          <Card className="p-4">
            <div className="flex items-center gap-4">
              <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-700">
                  Tailoring your resume...
                </p>
                <div className="h-2 bg-slate-100 rounded-full mt-2 overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full transition-all duration-300"
                    style={{ width: `${tailor.progress}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-bold text-primary-600">
                {tailor.progress}%
              </span>
            </div>
          </Card>
        )}

        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={handleTailor}
            disabled={tailor.loading || !tailoringEnabled}
            className="gap-2 px-8"
          >
            {tailor.loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Tailoring...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Tailor Resume
              </>
            )}
          </Button>
        </div>

        {tailor.data && (
          <div className="space-y-6">
            {beforeScore !== null && afterScore !== null && (
              <Card className="p-6">
                <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary-500" />
                  ATS Score Comparison
                </h3>
                <div className="grid grid-cols-2 gap-6">
                  <div className="text-center">
                    <p className="text-sm text-slate-500 mb-2">Before</p>
                    <p
                      className={cn(
                        "text-4xl font-bold",
                        beforeScore >= 0.7
                          ? "text-emerald-600"
                          : beforeScore >= 0.5
                            ? "text-amber-600"
                            : "text-red-600",
                      )}
                    >
                      {Math.round(beforeScore * 100)}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-slate-500 mb-2">After</p>
                    <p
                      className={cn(
                        "text-4xl font-bold",
                        afterScore >= 0.7
                          ? "text-emerald-600"
                          : afterScore >= 0.5
                            ? "text-amber-600"
                            : "text-red-600",
                      )}
                    >
                      {Math.round(afterScore * 100)}%
                    </p>
                    {afterScore > beforeScore && (
                      <Badge variant="success" className="mt-2">
                        +{Math.round((afterScore - beforeScore) * 100)}%
                        improved
                      </Badge>
                    )}
                  </div>
                </div>
              </Card>
            )}

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-900">
                  Tailored Summary
                </h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownload}
                  className="gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download
                </Button>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {tailor.data.tailored_summary}
                </p>
              </div>
            </Card>

            <div className="grid md:grid-cols-2 gap-4">
              <Card className="p-4">
                <h4 className="text-sm font-semibold text-slate-700 mb-2">
                  Highlighted Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {(tailor.data.highlighted_skills ?? []).map(
                    (skill, index) => (
                      <Badge key={index} variant="primary" size="sm">
                        {skill}
                      </Badge>
                    ),
                  )}
                </div>
              </Card>
              <Card className="p-4">
                <h4 className="text-sm font-semibold text-slate-700 mb-2">
                  Added Keywords
                </h4>
                <div className="flex flex-wrap gap-2">
                  {(tailor.data.added_keywords ?? []).map((keyword, index) => (
                    <Badge key={index} variant="lagoon" size="sm">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        {tailor.error && (
          <Card className="p-4 border-red-200 bg-red-50">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <div>
                <h4 className="font-semibold text-red-900">Tailoring Failed</h4>
                <p className="text-sm text-red-700">{tailor.error}</p>
              </div>
            </div>
          </Card>
        )}
      </div>
    </ErrorBoundary>
  );
}
