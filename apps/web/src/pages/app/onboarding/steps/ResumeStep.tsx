import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, X, Sparkles, User, ArrowLeft, ArrowRight, Briefcase } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { Card } from "../../../../components/ui/Card";
import { Badge } from "../../../../components/ui/Badge";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { ParsedResume } from "../../../../types/onboarding";

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
}: ResumeStepProps) {
    const [isDragging, setIsDragging] = React.useState(false);

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
            setResumeFile(e.dataTransfer.files[0]);
        }
    };

    return (
        <div
            className="flex flex-col h-full overflow-hidden relative"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            {/* Full Screen Drag Overlay */}
            <AnimatePresence>
                {isDragging && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 z-50 bg-primary-500/90 backdrop-blur-sm flex flex-col items-center justify-center p-8 text-white text-center"
                    >
                        <motion.div
                            initial={{ scale: 0.8, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.8, y: 20 }}
                            className="bg-white/10 p-8 rounded-[2.5rem] border-4 border-white/20 shadow-2xl backdrop-blur-md"
                        >
                            <Upload className="w-20 h-20 mb-6 mx-auto animate-bounce" />
                            <h3 className="text-3xl font-black font-display tracking-tight mb-2">Drop to Analyze</h3>
                            <p className="text-lg font-medium text-white/80">Release to initialize vector scan</p>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                <div className="mb-3 md:mb-5 flex items-center gap-2.5 md:gap-4 border-b border-slate-100 pb-2.5 md:pb-5">
                    <div className="flex h-8 w-10 md:h-11 md:w-14 shrink-0 items-center justify-center rounded-xl md:rounded-2xl bg-primary-50 border border-primary-100 text-primary-600 shadow-sm">
                        <Upload className="h-4 w-4 md:h-6 md:w-6" />
                    </div>
                    <div className="min-w-0">
                        <h2 className="font-display text-base md:text-2xl font-bold text-slate-900 tracking-tight truncate">Upload Your Resume</h2>
                        <p className="text-[10px] md:text-sm text-slate-500 font-medium truncate">AI will extract your skills and experience</p>
                    </div>
                </div>

                <div className="mb-3 md:mb-6 relative group">
                    <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                        className="hidden"
                        id="resume-upload"
                        disabled={isUploading}
                    />
                    <label
                        htmlFor="resume-upload"
                        className={`flex cursor-pointer flex-col items-center gap-2 md:gap-4 rounded-2xl md:rounded-3xl border-2 border-dashed p-4 md:p-8 text-center transition-all duration-200 ${resumeFile
                            ? "bg-primary-50 border-primary-300"
                            : "bg-slate-50 border-slate-200 hover:bg-white hover:border-primary-300"
                            }`}
                    >
                        <div className={`flex h-12 w-12 md:h-16 md:w-16 items-center justify-center rounded-xl md:rounded-2xl bg-white shadow-sm border border-slate-100 transition-all ${isUploading ? 'animate-pulse' : 'group-hover:scale-105'}`}>
                            {isUploading ? (
                                <div className="relative">
                                    <Sparkles className="h-6 w-6 md:h-8 md:w-8 text-primary-400" />
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="w-3 h-3 md:w-4 md:h-4 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
                                    </div>
                                </div>
                            ) : (
                                <FileText className={`h-6 w-6 md:h-8 md:w-8 ${resumeFile ? 'text-primary-500' : 'text-slate-300'}`} />
                            )}
                        </div>
                        <div className="space-y-0.5 md:space-y-1">
                            <p className={`text-sm md:text-lg font-bold ${resumeFile ? 'text-primary-700' : 'text-slate-700'}`}>
                                {resumeFile ? resumeFile.name : "Tap to upload your resume"}
                            </p>
                            <p className="text-[10px] md:text-xs text-slate-400 font-medium">PDF format • Max 10MB</p>
                        </div>
                    </label>
                    {resumeFile && !isUploading && (
                        <button
                            onClick={(e) => { e.preventDefault(); setResumeFile(null); setResumeError(null); setShowParsingPreview(false); }}
                            className="absolute top-2 right-2 md:top-3 md:right-3 w-7 h-7 md:w-8 md:h-8 rounded-full bg-white border border-slate-200 hover:border-red-200 hover:bg-red-50 flex items-center justify-center transition-colors z-20 shadow-sm"
                            title="Remove file"
                            aria-label="Remove uploaded resume"
                        >
                            <X className="h-3.5 w-3.5 md:h-4 md:w-4 text-slate-400 hover:text-red-500" />
                        </button>
                    )}
                    {isUploading && (
                        <div className="absolute inset-0 bg-white/80 backdrop-blur-[1px] rounded-2xl md:rounded-3xl flex flex-col items-center justify-center gap-2 md:gap-3 z-10">
                            <div className="w-32 md:w-48 h-1 bg-slate-100 rounded-full overflow-hidden border border-slate-50">
                                <motion.div
                                    className="h-full bg-primary-500"
                                    initial={shouldReduceMotion ? { width: "100%" } : { width: "0%" }}
                                    animate={{ width: "100%" }}
                                    transition={shouldReduceMotion ? undefined : { duration: 3, repeat: Infinity }}
                                />
                            </div>
                            <p className="text-[10px] md:text-xs font-bold text-primary-600 uppercase tracking-wide">Parsing resume...</p>
                        </div>
                    )}
                </div>

                <div className="mb-3 md:mb-10">
                    <div className="flex items-center gap-2 mb-1.5 md:mb-4 px-1">
                        <div className="h-[1px] flex-1 bg-slate-100" />
                        <span className="text-[9px] md:text-[10px] font-black text-slate-300 uppercase tracking-widest">or social reference</span>
                        <div className="h-[1px] flex-1 bg-slate-100" />
                    </div>
                    <div className="relative">
                        <Input
                            icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                            type="url"
                            placeholder="LinkedIn URL (optional)"
                            value={linkedinUrl}
                            onChange={(e) => setLinkedinUrl(e.target.value)}
                            onClear={() => setLinkedinUrl("")}
                            className="bg-white shadow-sm text-sm"
                        />
                    </div>
                </div>

                {resumeError && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-3 md:mb-8 rounded-xl md:rounded-2xl border border-red-200 bg-red-50 p-3 md:p-5 text-xs md:text-sm text-red-600 font-bold flex items-center gap-2 md:gap-3"
                    >
                        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0" />
                        <span className="flex-1 min-w-0 truncate">{resumeError}</span>
                    </motion.div>
                )}

                {/* Resume Parsing Preview - Polished Professional Design */}
                <AnimatePresence>
                    {showParsingPreview && parsedResume && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                            className="mt-4 md:mt-6"
                        >
                            <div className="rounded-2xl md:rounded-3xl border border-slate-200 bg-white shadow-lg overflow-hidden">
                                <div className="bg-gradient-to-r from-emerald-600 to-emerald-500 px-4 py-3 md:px-6 md:py-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 md:gap-3">
                                            <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
                                                <Sparkles className="h-4 w-4 md:h-5 md:w-5 text-white" />
                                            </div>
                                            <div>
                                                <h3 className="font-bold text-white text-sm md:text-lg">Resume Parsed Successfully</h3>
                                                <p className="text-emerald-100 text-[10px] md:text-xs">AI extracted your professional profile</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-1.5 bg-white/20 backdrop-blur px-2 py-1 md:px-3 md:py-1.5 rounded-full">
                                            <div className="w-1.5 h-1.5 md:w-2 md:h-2 rounded-full bg-white animate-pulse" />
                                            <span className="text-[9px] md:text-xs font-bold text-white">98% Match</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-3 md:p-6 space-y-3 md:space-y-4">
                                    {parsedResume.title && (
                                        <div className="flex items-start gap-3 md:gap-4 p-3 md:p-4 rounded-xl md:rounded-2xl bg-slate-50 border border-slate-100">
                                            <div className="w-9 h-9 md:w-11 md:h-11 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0 shadow-sm">
                                                <User className="h-4 w-4 md:h-5 md:w-5 text-primary-500" />
                                            </div>
                                            <div className="min-w-0 flex-1">
                                                <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5 md:mb-1">Professional Title</p>
                                                <p className="font-bold text-slate-900 text-sm md:text-base leading-tight">{parsedResume.title}</p>
                                            </div>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-2 gap-2 md:gap-3">
                                        <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-slate-50 border border-slate-100">
                                            <div className="flex items-center gap-2 mb-1 md:mb-2">
                                                <Briefcase className="h-3.5 w-3.5 md:h-4 md:w-4 text-primary-500" />
                                                <span className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-wider">Experience</span>
                                            </div>
                                            <p className="font-bold text-slate-900 text-lg md:text-xl">{parsedResume.years || 0}<span className="text-sm md:text-base font-medium text-slate-500 ml-0.5">yrs</span></p>
                                        </div>
                                        <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-slate-50 border border-slate-100">
                                            <div className="flex items-center gap-2 mb-1 md:mb-2">
                                                <Sparkles className="h-3.5 w-3.5 md:h-4 md:w-4 text-primary-500" />
                                                <span className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-wider">Skills</span>
                                            </div>
                                            <p className="font-bold text-slate-900 text-lg md:text-xl">{parsedResume.skills?.length || 0}<span className="text-sm md:text-base font-medium text-slate-500 ml-0.5">found</span></p>
                                        </div>
                                    </div>

                                    {parsedResume.skills && parsedResume.skills.length > 0 && (
                                        <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-slate-50 border border-slate-100">
                                            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 md:mb-3">Detected Skills</p>
                                            <div className="flex flex-wrap gap-1.5 md:gap-2">
                                                {parsedResume.skills.slice(0, 12).map((skill, i) => (
                                                    <motion.span
                                                        key={skill}
                                                        initial={{ opacity: 0, scale: 0.9 }}
                                                        animate={{ opacity: 1, scale: 1 }}
                                                        transition={{ delay: i * 0.03 }}
                                                        className="inline-flex items-center px-2 py-0.5 md:px-2.5 md:py-1 rounded-full text-[9px] md:text-[10px] font-semibold bg-white border border-slate-200 text-slate-700 shadow-sm"
                                                    >
                                                        {skill}
                                                    </motion.span>
                                                ))}
                                                {parsedResume.skills.length > 12 && (
                                                    <span className="inline-flex items-center px-2 py-0.5 md:px-2.5 md:py-1 rounded-full text-[9px] md:text-[10px] font-semibold bg-primary-50 border border-primary-200 text-primary-700">
                                                        +{parsedResume.skills.length - 12} more
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {parsedResume.summary && (
                                        <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-slate-50 border border-slate-100">
                                            <p className="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 md:mb-2">Professional Summary</p>
                                            <p className="text-xs md:text-sm text-slate-600 leading-relaxed line-clamp-3">{parsedResume.summary}</p>
                                        </div>
                                    )}
                                </div>

                                <div className="px-3 pb-3 md:px-6 md:pb-6">
                                    <Button
                                        variant="primary"
                                        className="w-full h-11 md:h-12 rounded-xl md:rounded-2xl font-bold text-sm md:text-base bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-500/20"
                                        onClick={onConfirmParsing}
                                        aria-label="Confirm extracted information and continue"
                                    >
                                        Looks Good, Continue
                                    </Button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <div className="flex gap-2 md:gap-3 pt-2 md:pt-3 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button variant="ghost" onClick={onPrev} className="h-9 md:h-11 rounded-xl md:rounded-2xl font-bold text-slate-400 hover:text-slate-900 border border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-sm px-3 md:px-4" aria-label="Go to previous step">
                    <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-4 md:w-4" />
                    Back
                </Button>
                {resumeFile && !resumeError ? (
                    <Button
                        onClick={() => onUpload(resumeFile)}
                        disabled={isUploading}
                        className="flex-[2] h-9 md:h-11 rounded-xl md:rounded-2xl font-bold bg-primary-600 hover:bg-primary-500 shadow-lg shadow-primary-500/20 text-xs md:text-sm group overflow-hidden relative"
                        aria-label={showParsingPreview ? "Upload new resume" : "Extract experience from resume"}
                    >
                        <span className="relative z-10 flex items-center justify-center">
                            {isUploading ? <LoadingSpinner size="sm" /> : showParsingPreview ? "Upload New" : "Parse Resume"}
                            <ArrowRight className="ml-1.5 md:ml-2 h-3.5 w-3.5 md:h-4 md:w-4 group-hover:translate-x-0.5 transition-transform" />
                        </span>
                    </Button>
                ) : (
                    <Button
                        variant={resumeError ? "primary" : "outline"}
                        onClick={onNext}
                        className={`flex-[2] h-9 md:h-11 rounded-xl md:rounded-2xl font-bold transition-all text-xs md:text-sm truncate ${resumeError
                            ? "bg-primary-600 hover:bg-primary-500 shadow-lg shadow-primary-500/20 text-white"
                            : "text-slate-500 hover:border-slate-300 hover:text-slate-700 border border-slate-200"
                            }`}
                        aria-label={resumeError ? "Continue anyway despite error" : "Skip resume upload and proceed manually"}
                    >
                        {resumeError ? "Continue Anyway" : "Skip for Now"}
                    </Button>
                )}
            </div>
        </div>
    );
}
