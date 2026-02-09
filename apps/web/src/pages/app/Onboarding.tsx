import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Check, Upload, MapPin, Briefcase, DollarSign, Rocket, ArrowRight, ArrowLeft, FileText, CheckCircle2, Sparkles, User } from "lucide-react";
import { useOnboarding } from "../../hooks/useOnboarding";
import { useProfile } from "../../hooks/useProfile";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { pushToast } from "../../lib/toast";

export default function Onboarding() {
  const navigate = useNavigate();
  const { steps, currentStep, currentStepData, progress, isFirstStep, isLastStep, nextStep, prevStep, resetOnboarding } = useOnboarding();
  const { profile, loading, uploadResume, savePreferences, completeOnboarding } = useProfile();

  const [resumeFile, setResumeFile] = React.useState<File | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [resumeError, setResumeError] = React.useState<string | null>(null);
  const [preferences, setPreferences] = React.useState({
    location: "",
    role_type: "",
    salary_min: "",
    remote_only: false,
  });

  const [linkedinUrl, setLinkedinUrl] = React.useState("");
  const [parsedResume, setParsedResume] = React.useState<{title?: string; skills?: string[]; years?: number; summary?: string; headline?: string} | null>(null);
  const [showParsingPreview, setShowParsingPreview] = React.useState(false);
  const [isSavingPreferences, setIsSavingPreferences] = React.useState(false);
  const [isCompleting, setIsCompleting] = React.useState(false);

  React.useEffect(() => {
    if (profile?.preferences) {
      const p = profile.preferences;
      setPreferences({
        location: p.location ?? "",
        role_type: p.role_type ?? "",
        salary_min: p.salary_min ? String(p.salary_min) : "",
        remote_only: p.remote_only ?? false,
      });
    }
  }, [profile?.preferences]);

  React.useEffect(() => {
    if (profile?.has_completed_onboarding) {
      resetOnboarding();
      navigate("/app/jobs");
    }
  }, [profile, navigate, resetOnboarding]);

  const handleResumeUpload = async () => {
    if (!resumeFile) return;
    setIsUploading(true);
    setResumeError(null);
    try {
      const data = await uploadResume(resumeFile);
      pushToast({ title: "Resume uploaded!", tone: "success" });

      if (data.parsed_profile) {
        const p = data.parsed_profile;
        setParsedResume({
          title: p.headline || (p.experience?.[0]?.title),
          skills: p.skills?.technical?.slice(0, 5) || [],
          years: p.experience?.length || 0,
          summary: p.summary,
          headline: p.headline,
        });
        setShowParsingPreview(true);
      }
    } catch (err) {
      const message = (err as Error).message;
      setResumeError(message);
      pushToast({ title: "Upload failed", description: message, tone: "error" });
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirmParsing = () => {
    setShowParsingPreview(false);
    nextStep();
  };

  const calculateCompleteness = () => {
    let score = 0;
    if (profile?.resume_url || resumeFile) score += 40;
    if (preferences.location) score += 20;
    if (preferences.role_type) score += 20;
    if (preferences.salary_min) score += 20;
    return score;
  };

  const completeness = calculateCompleteness();

  const handleSavePreferences = async () => {
    try {
      setIsSavingPreferences(true);
      await savePreferences({
        location: preferences.location || undefined,
        role_type: preferences.role_type || undefined,
        salary_min: preferences.salary_min ? Number(preferences.salary_min) : undefined,
        remote_only: preferences.remote_only,
      });
      nextStep();
    } catch (err) {
      pushToast({ title: "Something went sideways", description: "Your data is safe. Please try again.", tone: "error" });
    } finally {
      setIsSavingPreferences(false);
    }
  };

  const handleComplete = async () => {
    try {
      setIsCompleting(true);
      await completeOnboarding();
      resetOnboarding();
      pushToast({ title: "You're all set! Let's job hunt! 🚀", tone: "success" });
      navigate("/app/jobs");
    } catch (err) {
      pushToast({ title: "Almost there!", description: "Please try again.", tone: "error" });
    } finally {
      setIsCompleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Loading your profile..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-shell px-6 py-12">
      <div className="mx-auto max-w-2xl">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-brand-ink">
              Step {currentStep + 1} of {steps.length}
            </span>
            <span className="text-sm text-brand-ink/60">{currentStepData.title}</span>
          </div>
          <div className="h-2 w-full rounded-full bg-white">
            <div
              className="h-full rounded-full bg-brand-sunrise transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <Card tone="shell" shadow="lift" className="p-8">
          {/* Profile completeness indicator */}
          <div className="mb-6 rounded-2xl bg-brand-lagoon/10 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-brand-lagoon" />
                <span className="text-sm font-medium text-brand-ink">Profile completeness</span>
              </div>
              <span className="text-sm font-bold text-brand-lagoon">{completeness}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-white">
              <div
                className="h-full rounded-full bg-brand-lagoon transition-all duration-500"
                style={{ width: `${completeness}%` }}
              />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {(profile?.resume_url || resumeFile) && (
                <Badge variant="lagoon" className="text-xs">
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                  Resume uploaded
                </Badge>
              )}
              {preferences.location && (
                <Badge variant="lagoon" className="text-xs">
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                  Location set
                </Badge>
              )}
              {preferences.role_type && (
                <Badge variant="lagoon" className="text-xs">
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                  Role type set
                </Badge>
              )}
              {preferences.salary_min && (
                <Badge variant="lagoon" className="text-xs">
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                  Salary set
                </Badge>
              )}
            </div>
          </div>

          {/* Step 1: Welcome */}
          {currentStep === 0 && (
            <div className="text-center">
              <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-brand-sunrise/20">
                <Rocket className="h-10 w-10 text-brand-sunrise" />
              </div>
              <h1 className="mb-4 font-display text-3xl text-brand-ink">
                Welcome to JobHuntin!
              </h1>
              <p className="mb-6 text-brand-ink/70">
                We're going to get you set up in just 2 minutes. Here's what we'll do:
              </p>
              <ul className="mb-8 space-y-3 text-left">
                {[
                  "Upload your resume (or paste your LinkedIn)",
                  "Set your job preferences",
                  "Start applying to perfect matches",
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-brand-ink">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-lagoon/20">
                      <Check className="h-4 w-4 text-brand-lagoon" />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
              <Button size="lg" wobble onClick={nextStep} className="w-full">
                Let's go!
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Step 2: Resume Upload */}
          {currentStep === 1 && (
            <div>
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-lagoon/20">
                  <Upload className="h-6 w-6 text-brand-lagoon" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-brand-ink">Upload your resume</h2>
                  <p className="text-sm text-brand-ink/60">PDF or Word doc — we'll extract your skills automatically</p>
                </div>
              </div>

              <div className="mb-6 rounded-2xl border-2 border-dashed border-brand-ink/20 bg-white/50 p-8 text-center">
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="resume-upload"
                />
                <label
                  htmlFor="resume-upload"
                  className="flex cursor-pointer flex-col items-center gap-3"
                >
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-shell">
                    <FileText className="h-8 w-8 text-brand-ink/60" />
                  </div>
                  <div>
                    <p className="font-medium text-brand-ink">
                      {resumeFile ? resumeFile.name : "Click to upload your resume"}
                    </p>
                    <p className="text-sm text-brand-ink/50">Or drag and drop here</p>
                  </div>
                </label>
              </div>

              <div className="mb-6">
                <p className="mb-2 text-sm text-brand-ink/60">Or paste your LinkedIn URL:</p>
                <input
                  type="url"
                  placeholder="https://linkedin.com/in/yourname"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                />
              </div>

              {resumeError && (
                <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                  {resumeError}
                </div>
              )}

              <div className="flex gap-3">
                <Button variant="ghost" onClick={prevStep} className="flex-1">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
                {resumeFile ? (
                  <Button
                    onClick={handleResumeUpload}
                    disabled={isUploading}
                    className="flex-1"
                  >
                    {isUploading ? "Uploading..." : showParsingPreview ? "Re-upload" : "Upload & Continue"}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    onClick={nextStep}
                    className="flex-1"
                  >
                    Skip for now
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                )}
              </div>

              {/* Resume Parsing Preview */}
              {showParsingPreview && parsedResume && (
                <Card tone="lagoon" className="mt-6 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Sparkles className="h-5 w-5 text-brand-lagoon" />
                    <h3 className="font-display text-lg">We found from your resume:</h3>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <User className="h-4 w-4 text-brand-lagoon mt-1" />
                      <div>
                        <p className="text-sm font-medium text-brand-ink">Title</p>
                        <p className="text-brand-ink/70">{parsedResume.title}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <Briefcase className="h-4 w-4 text-brand-lagoon mt-1" />
                      <div>
                        <p className="text-sm font-medium text-brand-ink">Experience</p>
                        <p className="text-brand-ink/70">{parsedResume.years} years</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="h-4 w-4 text-brand-lagoon mt-1" />
                      <div>
                        <p className="text-sm font-medium text-brand-ink">Top Skills</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {parsedResume.skills?.map((skill) => (
                            <Badge key={skill} variant="outline" className="text-xs">{skill}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    {parsedResume.summary && (
                      <div className="flex items-start gap-3">
                        <Sparkles className="h-4 w-4 text-brand-lagoon mt-1" />
                        <div>
                          <p className="text-sm font-medium text-brand-ink">Summary</p>
                          <p className="text-brand-ink/70">{parsedResume.summary}</p>
                        </div>
                      </div>
                    )}
                  </div>
                  <p className="mt-4 text-sm text-brand-ink/60">
                    Does this look right? We'll use these details to personalize your applications.
                  </p>
                  <Button 
                    variant="lagoon" 
                    className="w-full mt-4"
                    onClick={handleConfirmParsing}
                  >
                    Looks good, continue
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full mt-3"
                    onClick={() => {
                      setShowParsingPreview(false);
                      setResumeFile(null);
                      setParsedResume(null);
                    }}
                  >
                    Re-upload
                  </Button>
                </Card>
              )}
            </div>
          )}

          {/* Step 3: Preferences */}
          {currentStep === 2 && (
            <div>
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-plum/20">
                  <Briefcase className="h-6 w-6 text-brand-plum" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-brand-ink">Job preferences</h2>
                  <p className="text-sm text-brand-ink/60">Tell us what you're looking for</p>
                </div>
              </div>

              <div className="mb-6 space-y-4">
                <div>
                  <label className="mb-2 flex items-center gap-2 text-sm font-medium text-brand-ink">
                    <MapPin className="h-4 w-4" />
                    Preferred location
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., San Francisco, Remote, Europe"
                    value={preferences.location}
                    onChange={(e) => setPreferences((p) => ({ ...p, location: e.target.value }))}
                    className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                  />
                </div>

                <div>
                  <label className="mb-2 flex items-center gap-2 text-sm font-medium text-brand-ink">
                    <Briefcase className="h-4 w-4" />
                    Role type
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Product Designer, Software Engineer"
                    value={preferences.role_type}
                    onChange={(e) => setPreferences((p) => ({ ...p, role_type: e.target.value }))}
                    className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                  />
                </div>

                <div>
                  <label className="mb-2 flex items-center gap-2 text-sm font-medium text-brand-ink">
                    <DollarSign className="h-4 w-4" />
                    Minimum salary
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 100000"
                    value={preferences.salary_min}
                    onChange={(e) => setPreferences((p) => ({ ...p, salary_min: e.target.value }))}
                    className="w-full rounded-2xl border border-brand-ink/10 bg-white px-4 py-3 text-brand-ink"
                  />
                </div>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={preferences.remote_only}
                    onChange={(e) => setPreferences((p) => ({ ...p, remote_only: e.target.checked }))}
                    className="h-5 w-5 rounded border-brand-ink/20"
                  />
                  <span className="text-brand-ink">Remote only</span>
                </label>
              </div>

              <div className="flex gap-3">
                <Button variant="ghost" onClick={prevStep} className="flex-1">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
                <Button onClick={handleSavePreferences} className="flex-1" disabled={isSavingPreferences}>
                  Continue
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 4: Review & Ready! */}
          {currentStep === 3 && (
            <div className="text-center">
              <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-brand-lagoon/20">
                <Badge variant="lagoon" className="text-lg">🎉</Badge>
              </div>
              <h1 className="mb-4 font-display text-3xl text-brand-ink">
                You're ready to job hunt!
              </h1>
              <p className="mb-6 text-brand-ink/70">
                We've got your resume and preferences. Let's find you some perfect job matches.
              </p>

              {/* Preferences Summary */}
              <Card tone="shell" className="mb-6 p-5 text-left">
                <h3 className="mb-4 font-display text-lg text-brand-ink">Your preferences:</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-brand-ink/60">Location</span>
                    <span className="font-medium text-brand-ink">{preferences.location || "Not specified"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-brand-ink/60">Role type</span>
                    <span className="font-medium text-brand-ink">{preferences.role_type || "Not specified"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-brand-ink/60">Minimum salary</span>
                    <span className="font-medium text-brand-ink">
                      {preferences.salary_min ? `$${Number(preferences.salary_min).toLocaleString()}` : "Not specified"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-brand-ink/60">Remote only</span>
                    <span className="font-medium text-brand-ink">{preferences.remote_only ? "Yes" : "No"}</span>
                  </div>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="w-full mt-4"
                  onClick={() => prevStep()}
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Edit preferences
                </Button>
              </Card>

              <div className="mb-8 rounded-2xl bg-brand-shell/70 p-6">
                <h3 className="mb-4 font-display text-lg text-brand-ink">What happens next:</h3>
                <ul className="space-y-3 text-left">
                  {[
                    "We'll scan for jobs matching your profile",
                    "You swipe right on jobs you like",
                    "We apply for you with a personalized message",
                    "You get interview requests directly",
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-3 text-brand-ink">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-sunrise/20">
                        <span className="text-sm font-bold text-brand-sunrise">{i + 1}</span>
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <Button size="lg" variant="primary" wobble onClick={handleComplete} className="w-full" disabled={isCompleting}>
                {isCompleting ? "Finishing..." : "Let's find jobs!"}
                <Rocket className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
