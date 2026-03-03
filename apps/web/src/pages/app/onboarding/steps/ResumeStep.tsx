import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FocusTrap } from "focus-trap-react";
import { Upload, FileText, X, Sparkles, User, ArrowLeft, ArrowRight, Briefcase } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { ParsedResume } from "../../../../types/onboarding";
import { t, getLocale } from "../../../../lib/i18n";

function SkipConfirmModal({ onStay, onSkip }: { onStay: () => void; onSkip: () => void }) {
    const containerRef = React.useRef<HTMLDivElement>(null);
    const locale = getLocale();
    
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="skip-confirm-title" onClick={(e) => e.target === e.currentTarget && onStay()}>
            <FocusTrap
                focusTrapOptions={{
                    initialFocus: () => containerRef.current?.querySelector<HTMLElement>('button') ?? false,
                    allowOutsideClick: true,
                    escapeDeactivates: true,
                }}
            >
                <div ref={containerRef} className="bg-white dark:bg-slate-900 rounded-2xl p-6 max-w-sm shadow-xl border border-slate-200 dark:border-slate-700 relative" onClick={(e) => e.stopPropagation()}>
                    <button
                        type="button"
                        onClick={onStay}
                        aria-label={t("onboarding.cancel", locale)}
                        className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    >
                        <X className="h-5 w-5" aria-hidden />
                    </button>
                    <h3 id="skip-confirm-title" className="font-bold text-slate-900 dark:text-slate-100 mb-2 pr-8">
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

interface ResumeStepProps {
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
}: ResumeStepProps) {
    const locale = getLocale();
    const [isDragging, setIsDragging] = React.useState(false);
    const [linkedinError, setLinkedinError] = React.useState<string | null>(null);
    const [showSkipConfirm, setShowSkipConfirm] = React.useState(false);
    
    // Reset parsing state when a new file is selected
    const handleFileChange = (file: File | null) => {
        setResumeFile(file);
        setResumeError(null);
        setShowParsingPreview(false);
        if (onResetParsingState) {
            onResetParsingState();
        }
    };

    const validateLinkedInUrl = (url: string): boolean => {
        if (!url) return true;
        // More permissive pattern: accepts various LinkedIn URL formats
        // - linkedin.com/in/username
        // - www.linkedin.com/in/username
        // - https://linkedin.com/in/username
        // - https://www.linkedin.com/in/username
        // - http:// variants
        // - with or without trailing slash
        // - with additional path segments like /details/experience
        const linkedinPattern = /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+(\/[a-zA-Z0-9_-]*)*\/?$/i;
        return linkedinPattern.test(url.trim());
    };

    const handleLinkedinChange = (value: string) => {
        setLinkedinUrl(value);
        if (value && !validateLinkedInUrl(value)) {
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

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileChange(e.dataTransfer.files[0]);
        }
    };

    return (
        <div
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
                        className="fixed inset-0 z-50 bg-primary-500/90 backdrop-blur-sm flex flex-col items-center justify-center p-8 text-white text-center"
                    >
                        <motion.div
                            initial={{ scale: 0.8, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.8, y: 20 }}
                            className="bg-white/10 p-8 rounded-3xl border-4 border-white/20 shadow-2xl backdrop-blur-md"
                        >
                            <Upload className="w-16 h-16 mb-4 mx-auto animate-bounce" />
                            <h3 className="text-2xl font-bold tracking-tight mb-2">{t("onboarding.dragAndDrop", locale)}</h3>
                            <p className="text-base text-white/80">{t("onboarding.uploadResume", locale)}</p>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="mb-4 md:mb-6 flex items-center gap-3 md:gap-4 border-b border-slate-100 pb-4 md:pb-6">
                <div className="flex h-10 w-12 md:h-12 md:w-14 shrink-0 items-center justify-center rounded-xl md:rounded-2xl bg-primary-50 border border-primary-100 text-primary-600 shadow-sm">
                    <Upload className="h-5 w-5 md:h-6 md:w-6" />
                </div>
                <div className="min-w-0">
                    <h2 className="font-display text-lg md:text-2xl font-bold text-slate-900 tracking-tight">
                        {t("onboarding.resumeTitle", locale)}
                    </h2>
                    <p className="text-xs md:text-sm text-slate-500 font-medium">
                        {t("onboarding.resumeSubtitle", locale)}
                    </p>
                </div>
            </div>

            <div className="mb-4 md:mb-6 relative group">
                <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file && file.size > 15 * 1024 * 1024) {
                        setResumeError("File must be under 15MB");
                        e.target.value = "";
                        return;
                      }
                      // Validate file type - PDF only to match backend
                      const allowedTypes = ['application/pdf'];
                      if (file && !allowedTypes.includes(file.type)) {
                        setResumeError("Please upload a PDF file");
                        e.target.value = "";
                        return;
                      }
                      handleFileChange(file || null);
                    }}
                    className="hidden"
                    id="resume-upload"
                    disabled={isUploading}
                />
                <label
                    htmlFor="resume-upload"
                    className={`flex cursor-pointer flex-col items-center gap-3 md:gap-4 rounded-2xl border-2 border-dashed p-6 md:p-8 text-center transition-all duration-200 ${resumeFile
                        ? "bg-primary-50 border-primary-300"
                        : "bg-slate-50 border-slate-200 hover:bg-white hover:border-primary-300"
                        }`}
                >
                    <div className={`flex h-14 w-14 md:h-16 md:w-16 items-center justify-center rounded-xl md:rounded-2xl bg-white shadow-sm border border-slate-100 transition-all ${isUploading ? 'animate-pulse' : 'group-hover:scale-105'}`}>
                        {isUploading ? (
                            <div className="relative">
                                <Sparkles className="h-7 w-7 md:h-8 md:w-8 text-primary-400" />
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="w-3.5 h-3.5 md:w-4 md:h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                                </div>
                            </div>
                        ) : (
                            <FileText className={`h-7 w-7 md:h-8 md:w-8 ${resumeFile ? 'text-primary-500' : 'text-slate-300'}`} />
                        )}
                    </div>
                    <div className="space-y-1">
                        <p className={`text-base md:text-lg font-bold ${resumeFile ? 'text-primary-700' : 'text-slate-700'}`}>
                            {resumeFile ? resumeFile.name : t("onboarding.clickToUpload", locale)}
                        </p>
                        <p className="text-xs text-slate-400 font-medium">{t("onboarding.fileTypes", locale)}</p>
                    </div>
                </label>
                {resumeFile && !isUploading && (
                    <button
                        onClick={(e) => { e.preventDefault(); setResumeFile(null); setResumeError(null); setShowParsingPreview(false); }}
                        className="absolute top-2 right-2 md:top-3 md:right-3 w-7 h-7 md:w-8 md:h-8 rounded-full bg-white border border-slate-200 hover:border-red-200 hover:bg-red-50 flex items-center justify-center transition-colors z-20 shadow-sm"
                        title={t("app.delete", locale)}
                        aria-label={t("app.delete", locale)}
                    >
                        <X className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-400 hover:text-red-500" />
                    </button>
                )}
                {isUploading && (
                    <div className="absolute inset-0 bg-white/80 backdrop-blur-[1px] rounded-2xl flex flex-col items-center justify-center gap-2 md:gap-3 z-10">
                        <div className="w-32 md:w-48 h-1 bg-slate-100 rounded-full overflow-hidden">
                            <motion.div
                                className="h-full bg-primary-500"
                                initial={shouldReduceMotion ? { width: "100%" } : { width: "0%" }}
                                animate={{ width: "100%" }}
                                transition={shouldReduceMotion ? undefined : { duration: 3, repeat: Infinity }}
                            />
                        </div>
                        <p className="text-xs font-bold text-primary-600 uppercase tracking-wide">{t("app.loading", locale)}</p>
                    </div>
                )}
            </div>

            <div className="mb-4 md:mb-6">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-px flex-1 bg-slate-200" />
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{t("app.or", locale) || "or"}</span>
                    <div className="h-px flex-1 bg-slate-200" />
                </div>
                <Input
                    icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                    type="url"
                    placeholder={t("onboarding.linkedinPlaceholder", locale)}
                    value={linkedinUrl}
                    onChange={(e) => handleLinkedinChange(e.target.value)}
                    onClear={() => { setLinkedinUrl(""); setLinkedinError(null); }}
                    className="bg-white shadow-sm"
                    error={!!linkedinError}
                />
                {linkedinError && (
                    <p className="mt-1 text-[10px] text-red-500 font-medium">{linkedinError}</p>
                )}
            </div>

            {resumeError && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600 font-bold flex items-center gap-2"
                >
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0" />
                    <span className="flex-1 min-w-0">{resumeError}</span>
                </motion.div>
            )}

            <AnimatePresence>
                {showParsingPreview && parsedResume && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                        className="mb-4"
                    >
                        <div className="rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden">
                            <div className="bg-gradient-to-r from-emerald-600 to-emerald-500 px-4 py-3">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                                            <Sparkles className="h-4 w-4 text-white" />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-white text-sm">{t("onboarding.parsingSuccess", locale) || "Resume Parsed Successfully"}</h3>
                                            <p className="text-emerald-100 text-xs">{t("onboarding.aiExtracted", locale) || "AI extracted your professional profile"}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-1 bg-white/20 px-2 py-1 rounded-full">
                                        <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                                        <span className="text-xs font-bold text-white">98%</span>
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 space-y-3">
                                {parsedResume.title && (
                                    <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                                        <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center shrink-0">
                                            <User className="h-5 w-5 text-primary-500" />
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">
                                                {t("onboarding.professionalTitle", locale) || "Professional Title"}
                                            </p>
                                            <p className="font-bold text-slate-900 text-sm">{parsedResume.title}</p>
                                        </div>
                                    </div>
                                )}

                                <div className="grid grid-cols-2 gap-3">
                                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
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
                                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                                        <div className="flex items-center gap-2 mb-1">
                                            <Sparkles className="h-4 w-4 text-primary-500" />
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

                                {parsedResume.skills && parsedResume.skills.length > 0 && (
                                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                                            {t("onboarding.detectedSkills", locale) || "Detected Skills"}
                                        </p>
                                        <div className="flex flex-wrap gap-1.5">
                                            {parsedResume.skills.slice(0, 12).map((skill, i) => (
                                                <motion.span
                                                    key={skill}
                                                    initial={{ opacity: 0, scale: 0.9 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    transition={{ delay: i * 0.03 }}
                                                    className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-white border border-slate-200 text-slate-700"
                                                >
                                                    {skill}
                                                </motion.span>
                                            ))}
                                            {parsedResume.skills.length > 12 && (
                                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-primary-50 border border-primary-200 text-primary-700">
                                                    +{parsedResume.skills.length - 12} {t("onboarding.more", locale) || "more"}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="px-4 pb-4">
                                <Button
                                    variant="primary"
                                    className="w-full h-12 sm:h-11 rounded-xl font-bold text-sm bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 touch-manipulation"
                                    onClick={onConfirmParsing}
                                    aria-label={t("onboarding.looksGoodContinue", locale)} data-onboarding-next
                                >
                                    {t("onboarding.looksGoodContinue", locale)}
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <Button 
                    variant="ghost" 
                    onClick={onPrev} 
                    className="h-12 sm:h-11 rounded-xl font-bold text-slate-400 hover:text-slate-900 border border-slate-100 hover:bg-slate-50 text-sm px-4 touch-manipulation"
                    aria-label={t("onboarding.back", locale)}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    {t("onboarding.back", locale)}
                </Button>
                {resumeFile && !resumeError ? (
                    <Button
                        onClick={() => onUpload(resumeFile)}
                        disabled={isUploading}
                        className="flex-1 h-12 sm:h-11 rounded-xl font-bold bg-primary-600 hover:bg-primary-500 shadow-lg shadow-primary-500/20 text-sm group touch-manipulation"
                        aria-label={t("onboarding.uploadResume", locale)} data-onboarding-next
                    >
                        {isUploading ? <LoadingSpinner size="sm" /> : showParsingPreview ? t("onboarding.reupload", locale) : t("onboarding.uploadResume", locale)}
                        {!isUploading && <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />}
                    </Button>
                ) : (
                    <Button
                        variant="ghost"
                        onClick={() => (resumeFile || parsedResume) ? setShowSkipConfirm(true) : onNext()}
                        className="flex-1 h-12 sm:h-11 rounded-xl font-bold text-slate-500 hover:text-slate-700 border border-slate-200 hover:bg-slate-50 text-sm touch-manipulation"
                        aria-label={t("onboarding.skipForNow", locale)} data-onboarding-next
                    >
                        {resumeError ? t("onboarding.skipUpload", locale) || "Skip Upload" : t("onboarding.skipForNow", locale)}
                        <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                )}
            </div>

            {showSkipConfirm && (
                <SkipConfirmModal
                    onStay={() => setShowSkipConfirm(false)}
                    onSkip={() => { setShowSkipConfirm(false); onNext(); }}
                />
            )}
        </div>
    );
}
