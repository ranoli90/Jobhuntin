import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FocusTrap } from "focus-trap-react";
import {
  Upload,
  FileText,
  X,
  User,
  ArrowLeft,
  ArrowRight,
  Briefcase,
} from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { ParsedResume } from "../../../../types/onboarding";
import { t, getLocale } from "../../../../lib/i18n";
import { cn } from "../../../../lib/utils";
import { isValidLinkedInUrl } from "../../../../lib/linkedinValidation";
import { isValidResumeFile } from "../../../../lib/fileValidation";

function SkipConfirmModal({
  onStay,
  onSkip,
}: {
  onStay: () => void;
  onSkip: () => void;
}) {
  const containerReference = React.useRef<HTMLDivElement>(null);
  const locale = getLocale();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="skip-confirm-title"
      onClick={(e) => e.target === e.currentTarget && onStay()}
    >
      <FocusTrap
        focusTrapOptions={{
          initialFocus: () =>
            containerReference.current?.querySelector<HTMLElement>("button") ??
            false,
          allowOutsideClick: true,
          escapeDeactivates: true,
        }}
      >
        <div
          ref={containerReference}
          className={cn(
            "bg-white dark:bg-slate-900 rounded-2xl p-6 max-w-sm shadow-xl",
            "border border-slate-200 dark:border-slate-700 relative",
          )}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            type="button"
            onClick={onStay}
            aria-label={t("onboarding.cancel", locale)}
            className={cn(
              "absolute top-4 right-4 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg",
              "text-slate-400 hover:text-slate-600 hover:bg-slate-100",
              "dark:hover:bg-slate-800 transition-colors",
            )}
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
          <h3
            id="skip-confirm-title"
            className="font-bold text-slate-900 dark:text-slate-100 mb-2 pr-8"
          >
            {t("onboarding.skipResumeTitle", locale)}
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            {t("onboarding.skipResumeDesc", locale)}
          </p>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onStay} className="flex-1">
              {t("onboarding.goBack", locale)}
            </Button>
            <Button variant="primary" onClick={onSkip} className="flex-1">
              {t("onboarding.skipForNow", locale)}
            </Button>
          </div>
        </div>
      </FocusTrap>
    </div>
  );
}

interface ResumeStepProperties {
  onNext: () => void;
  onPrev: () => void;
  onUpload: (file: File) => Promise<void>;
  resumeFile: File | null;
  setResumeFile: (file: File | null) => void;
  isUploading: boolean;
  resumeError: string | null;
  setResumeError: (error: string | null) => void;
  linkedinUrl: string;
  setLinkedinUrl: (url: string) => void;
  showParsingPreview: boolean;
  setShowParsingPreview: (show: boolean) => void;
  parsedResume: ParsedResume | null;
  onConfirmParsing: () => void;
  shouldReduceMotion?: boolean;
  onResetParsingState?: () => void;
}

export function ResumeStep({
  onNext,
  onPrev,
  onUpload,
  resumeFile,
  setResumeFile,
  isUploading,
  resumeError,
  setResumeError,
  linkedinUrl,
  setLinkedinUrl,
  showParsingPreview,
  setShowParsingPreview,
  parsedResume,
  onConfirmParsing,
  shouldReduceMotion,
  onResetParsingState,
}: ResumeStepProperties) {
  const locale = getLocale();
  const [isDragging, setIsDragging] = React.useState(false);
  const [linkedinError, setLinkedinError] = React.useState<string | null>(null);
  const [showSkipConfirm, setShowSkipConfirm] = React.useState(false);

  const handleFileChange = (file: File | null) => {
    setResumeFile(file);
    setResumeError(null);
    setShowParsingPreview(false);
    if (onResetParsingState) {
      onResetParsingState();
    }
  };

  const handleLinkedinChange = (value: string) => {
    setLinkedinUrl(value);
    // D5: Clear error on change when user fixes it; validate on blur to avoid showing error while typing
    if (linkedinError && (!value || isValidLinkedInUrl(value)))
      setLinkedinError(null);
  };
  const handleLinkedinBlur = () => {
    if (linkedinUrl.trim() && !isValidLinkedInUrl(linkedinUrl)) {
      setLinkedinError(t("onboarding.linkedinError", locale));
    } else {
      setLinkedinError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    if (file.size > 15 * 1024 * 1024) {
      setResumeError("File must be under 15MB");
      return;
    }
    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    if (!allowedTypes.includes(file.type)) {
      setResumeError("Please upload a PDF or Word document");
      return;
    }
    const { valid, reason } = await isValidResumeFile(file);
    if (!valid) {
      setResumeError(reason || "Please upload a PDF or Word document");
      return;
    }
    handleFileChange(file);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      handleFileChange(null);
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setResumeError("File must be under 15MB");
      e.target.value = "";
      return;
    }
    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    if (!allowedTypes.includes(file.type)) {
      setResumeError("Please upload a PDF or Word document");
      e.target.value = "";
      return;
    }
    const { valid, reason } = await isValidResumeFile(file);
    if (!valid) {
      setResumeError(reason || "Please upload a PDF or Word document");
      e.target.value = "";
      return;
    }
    handleFileChange(file);
  };

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.preventDefault();
    setResumeFile(null);
    setResumeError(null);
    setShowParsingPreview(false);
  };

  return (
    <div
      role="region"
      aria-labelledby="resume-step-title"
      className="relative"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={cn(
              "fixed inset-0 z-50 flex flex-col items-center justify-center p-8 text-white text-center",
              "bg-primary-600/90 backdrop-blur-sm",
            )}
          >
            <motion.div
              initial={{ scale: 0.8, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 20 }}
              className={cn(
                "bg-white/10 p-8 rounded-3xl border-4 border-white/20",
                "shadow-2xl backdrop-blur-md",
              )}
            >
              <Upload className="w-16 h-16 mb-4 mx-auto animate-bounce" />
              <h3 className="text-2xl font-bold tracking-tight mb-2">
                {t("onboarding.dragAndDrop", locale)}
              </h3>
              <p className="text-base text-white/80">
                {t("onboarding.uploadResume", locale)}
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div
        className={cn(
          "mb-6 flex items-center gap-4",
          "border-b border-slate-100 pb-6",
        )}
      >
        <div
          className={cn(
            "flex h-12 w-14 shrink-0 items-center justify-center",
            "rounded-2xl bg-primary-50 border border-primary-100",
            "text-primary-600 shadow-sm",
          )}
        >
          <Upload className="h-6 w-6" />
        </div>
        <div className="min-w-0">
          <h2
            id="resume-step-title"
            className="font-display text-2xl font-bold text-slate-900 tracking-tight"
          >
            {t("onboarding.resumeTitle", locale)}
          </h2>
          <p className="text-sm text-slate-500 font-medium">
            {t("onboarding.resumeSubtitle", locale)}
          </p>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="mb-6 relative group">
        <input
          type="file"
          accept=".pdf,.docx,.doc,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleFileSelect}
          className="hidden"
          id="resume-upload"
          disabled={isUploading}
        />
        <label
          htmlFor="resume-upload"
          aria-disabled={isUploading}
          className={cn(
            "flex flex-col items-center gap-4 rounded-2xl border-2 border-dashed",
            "p-8 text-center transition-all duration-200",
            isUploading
              ? "cursor-not-allowed pointer-events-none opacity-80"
              : "cursor-pointer",
            resumeFile
              ? "bg-primary-50 border-primary-300"
              : "bg-slate-50 border-slate-200 hover:bg-white hover:border-primary-300",
          )}
        >
          <div
            className={cn(
              "flex h-16 w-16 items-center justify-center rounded-2xl",
              "bg-white shadow-sm border border-slate-100 transition-all",
              isUploading ? "animate-pulse" : "group-hover:scale-105",
            )}
          >
            {isUploading ? (
              <div className="relative">
                <FileText className="h-8 w-8 text-primary-400" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                </div>
              </div>
            ) : (
              <FileText
                className={cn(
                  "h-8 w-8",
                  resumeFile ? "text-primary-500" : "text-slate-300",
                )}
              />
            )}
          </div>
          <div className="space-y-1">
            <p
              className={cn(
                "text-lg font-bold",
                resumeFile ? "text-primary-700" : "text-slate-700",
              )}
            >
              {resumeFile
                ? resumeFile.name
                : t("onboarding.clickToUpload", locale)}
            </p>
            <p className="text-xs text-slate-400 font-medium">
              {t("onboarding.fileTypes", locale)}
            </p>
          </div>
        </label>

        {/* Remove Button */}
        {resumeFile && !isUploading && (
          <button
            onClick={handleRemoveFile}
            className={cn(
              "absolute top-3 right-3 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-full",
              "bg-white border border-slate-200",
              "hover:border-red-200 hover:bg-red-50",
              "flex items-center justify-center transition-colors z-20 shadow-sm",
            )}
            title={t("app.delete", locale)}
            aria-label={t("app.delete", locale)}
          >
            <X className="h-4 w-4 text-slate-400 hover:text-red-500" />
          </button>
        )}

        {/* Upload Progress Overlay */}
        {isUploading && (
          <div
            className={cn(
              "absolute inset-0 rounded-2xl flex flex-col items-center justify-center gap-3 z-10",
              "bg-white/80 backdrop-blur-[1px]",
            )}
          >
            <div className="w-48 h-1 bg-slate-100 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary-500"
                initial={
                  shouldReduceMotion ? { width: "100%" } : { width: "0%" }
                }
                animate={{ width: "100%" }}
                transition={
                  shouldReduceMotion
                    ? undefined
                    : { duration: 3, repeat: Infinity }
                }
              />
            </div>
            <p className="text-xs font-bold text-primary-600 uppercase tracking-wide">
              {t("app.loading", locale)}
            </p>
          </div>
        )}
      </div>

      {/* LinkedIn Input */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <div className="h-px flex-1 bg-slate-200" />
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            {t("app.or", locale) || "or"}
          </span>
          <div className="h-px flex-1 bg-slate-200" />
        </div>
        <label htmlFor="resume-linkedin-url" className="sr-only">
          {t("onboarding.linkedinPlaceholder", locale) ||
            "LinkedIn profile URL"}
        </label>
        <Input
          id="resume-linkedin-url"
          aria-label={
            t("onboarding.linkedinPlaceholder", locale) ||
            "LinkedIn profile URL"
          }
          icon={<User className="h-5 w-5" />}
          type="url"
          placeholder={t("onboarding.linkedinPlaceholder", locale)}
          value={linkedinUrl}
          onChange={(e) => handleLinkedinChange(e.target.value)}
          onBlur={handleLinkedinBlur}
          onClear={() => {
            setLinkedinUrl("");
            setLinkedinError(null);
          }}
          className="bg-white shadow-sm"
          error={!!linkedinError}
        />
        {linkedinError && (
          <p className="mt-1 text-[10px] text-red-500 font-medium">
            {linkedinError}
          </p>
        )}
      </div>

      {/* Error Message */}
      {resumeError && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn(
            "mb-4 rounded-xl border border-red-200 bg-red-50 p-4",
            "text-sm text-red-600",
          )}
          role="alert"
        >
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0 mt-1.5" />
            <div className="flex-1 min-w-0">
              <p className="font-bold">{resumeError}</p>
              {(resumeError.toLowerCase().includes("parse") ||
                resumeError.toLowerCase().includes("extract") ||
                resumeError.toLowerCase().includes("read")) && (
                <p className="text-xs text-red-600/90 mt-1 font-normal">
                  {t("onboarding.parsingErrorHint", locale) ||
                    "You can try a different file, or skip and add your details manually in the next steps."}
                </p>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* AI Parsing Preview */}
      <AnimatePresence>
        {showParsingPreview && parsedResume && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="mb-4"
          >
            <div
              className={cn(
                "rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden",
              )}
            >
              {/* Success Header */}
              <div className="bg-gradient-to-r from-emerald-600 to-emerald-500 px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                      <FileText className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-sm">
                        {t("onboarding.parsingSuccess", locale) ||
                          "Resume Parsed Successfully"}
                      </h3>
                      <p className="text-emerald-100 text-xs">
                        {t("onboarding.aiExtracted", locale) ||
                          "AI extracted your professional profile"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 bg-white/20 px-2 py-1 rounded-full">
                    <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                    <span className="text-xs font-bold text-white">98%</span>
                  </div>
                </div>
              </div>

              {/* Parsed Data */}
              <div className="p-4 space-y-3">
                {parsedResume.title && (
                  <div
                    className={cn(
                      "flex items-start gap-3 p-3 rounded-xl",
                      "bg-primary-50/30 border border-primary-100",
                    )}
                  >
                    <div
                      className={cn(
                        "w-10 h-10 rounded-lg bg-white border border-slate-200",
                        "flex items-center justify-center shrink-0",
                      )}
                    >
                      <User className="h-5 w-5 text-primary-500" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">
                        {t("onboarding.professionalTitle", locale) ||
                          "Professional Title"}
                      </p>
                      <p className="font-bold text-slate-900 text-sm">
                        {parsedResume.title}
                      </p>
                    </div>
                  </div>
                )}

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div
                    className={cn(
                      "p-3 rounded-xl bg-slate-50 border border-slate-100",
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Briefcase className="h-4 w-4 text-primary-500" />
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        {t("onboarding.experience", locale) || "Experience"}
                      </span>
                    </div>
                    <p className="font-bold text-slate-900 text-lg">
                      {parsedResume.years || 0}
                      <span className="text-sm font-medium text-slate-500 ml-0.5">
                        {t("onboarding.years", locale) || "yrs"}
                      </span>
                    </p>
                  </div>
                  <div
                    className={cn(
                      "p-3 rounded-xl bg-slate-50 border border-slate-100",
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <FileText className="h-4 w-4 text-primary-500" />
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        {t("onboarding.skillsDetected", locale) || "Skills"}
                      </span>
                    </div>
                    <p className="font-bold text-slate-900 text-lg">
                      {parsedResume.skills?.length || 0}
                      <span className="text-sm font-medium text-slate-500 ml-0.5">
                        {t("onboarding.found", locale) || "found"}
                      </span>
                    </p>
                  </div>
                </div>

                {/* Skills Tags */}
                {parsedResume.skills && parsedResume.skills.length > 0 && (
                  <div
                    className={cn(
                      "p-3 rounded-xl bg-slate-50 border border-slate-100",
                    )}
                  >
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      {t("onboarding.detectedSkills", locale) ||
                        "Detected Skills"}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {(parsedResume.skills ?? [])
                        .slice(0, 12)
                        .map((skill, index) => {
                          const skillLabel =
                            typeof skill === "string"
                              ? skill
                              : ((skill as { name?: string; skill?: string })
                                  ?.name ??
                                (skill as { name?: string; skill?: string })
                                  ?.skill ??
                                String(skill));
                          return (
                            <motion.span
                              key={`${skillLabel}-${index}`}
                              initial={{ opacity: 0, scale: 0.9 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: index * 0.03 }}
                              className={cn(
                                "inline-flex items-center px-2 py-0.5 rounded-full",
                                "text-[10px] font-semibold bg-white border border-slate-200 text-slate-700",
                              )}
                            >
                              {skillLabel}
                            </motion.span>
                          );
                        })}
                      {(parsedResume.skills ?? []).length > 12 && (
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 rounded-full",
                            "text-[10px] font-black bg-primary-50 border border-primary-200 text-primary-700",
                          )}
                        >
                          +{(parsedResume.skills ?? []).length - 12}{" "}
                          {t("onboarding.more", locale) || "more"}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Button */}
              <div className="px-4 pb-4">
                <Button
                  variant="primary"
                  className={cn(
                    "w-full h-11 rounded-xl font-bold text-sm",
                    "bg-emerald-600 hover:bg-emerald-500",
                    "shadow-lg shadow-emerald-500/20",
                  )}
                  onClick={onConfirmParsing}
                  aria-label={t("onboarding.looksGoodContinue", locale)}
                  data-onboarding-next
                >
                  {t("onboarding.looksGoodContinue", locale)}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 pt-2">
        <Button
          variant="ghost"
          onClick={onPrev}
          className={cn(
            "h-11 rounded-xl font-bold text-slate-400 hover:text-slate-900",
            "border border-slate-100 hover:bg-slate-50 text-sm px-4",
          )}
          aria-label={t("onboarding.back", locale)}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t("onboarding.back", locale)}
        </Button>
        {resumeFile && !resumeError ? (
          <Button
            onClick={() => onUpload(resumeFile)}
            disabled={isUploading}
            className={cn(
              "flex-1 h-11 rounded-xl font-bold",
              "bg-primary-600 hover:bg-primary-500",
              "shadow-lg shadow-primary-500/20 text-sm group",
            )}
            aria-label={t("onboarding.uploadResume", locale)}
            data-onboarding-next
          >
            {isUploading ? (
              <LoadingSpinner size="sm" />
            ) : (showParsingPreview ? (
              t("onboarding.reupload", locale)
            ) : (
              t("onboarding.uploadResume", locale)
            ))}
            {!isUploading && (
              <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
            )}
          </Button>
        ) : (
          <Button
            variant="ghost"
            onClick={() =>
              resumeFile || parsedResume ? setShowSkipConfirm(true) : onNext()
            }
            className={cn(
              "flex-1 h-11 rounded-xl font-bold text-slate-500 hover:text-slate-700",
              "border border-slate-200 hover:bg-slate-50 text-sm",
            )}
            aria-label={t("onboarding.skipForNow", locale)}
            data-onboarding-next
          >
            {resumeError
              ? t("onboarding.skipUpload", locale) || "Skip Upload"
              : t("onboarding.skipForNow", locale)}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Skip Confirmation Modal */}
      {showSkipConfirm && (
        <SkipConfirmModal
          onStay={() => setShowSkipConfirm(false)}
          onSkip={() => {
            setLinkedinError(null);
            setShowSkipConfirm(false);
            onNext();
          }}
        />
      )}
    </div>
  );
}
