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
                <div className="mb-3 md:mb-8 flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6">
                    <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-primary-50 border border-primary-100 text-primary-600 shadow-inner">
                        <Upload className="h-4 w-4 md:h-8 md:w-8" />
                    </div>
                    <div className="min-w-0">
                        <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">Experience Input</h2>
                        <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">Feed the AI your career history for optimization.</p>
                    </div>
                </div>

                <div className="mb-3 md:mb-8 relative group">
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
                        className={`flex cursor-pointer flex-col items-center gap-2 md:gap-6 rounded-[1.25rem] md:rounded-[2.5rem] border-3 border-dashed p-3 md:p-10 text-center transition-all duration-300 ${resumeFile
                            ? "bg-primary-50/50 border-primary-300"
                            : "bg-slate-50/50 border-slate-200 hover:bg-slate-50 hover:border-primary-300"
                            }`}
                    >
                        <div className={`flex h-10 w-10 md:h-20 md:w-20 items-center justify-center rounded-[0.75rem] md:rounded-[2rem] bg-white shadow-xl transition-all ${isUploading ? 'animate-pulse scale-90' : 'group-hover:scale-110 group-hover:rotate-3'}`}>
                            {isUploading ? (
                                <div className="relative">
                                    <Sparkles className="h-5 w-5 md:h-10 md:w-10 text-primary-400" />
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="w-2.5 h-2.5 md:w-5 md:h-5 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
                                    </div>
                                </div>
                            ) : (
                                <FileText className={`h-5 w-5 md:h-10 md:w-10 ${resumeFile ? 'text-primary-600' : 'text-slate-300'}`} />
                            )}
                        </div>
                        <div className="space-y-0.5 md:space-y-2">
                            <p className={`text-xs md:text-xl font-black ${resumeFile ? 'text-primary-700' : 'text-slate-900'}`}>
                                {resumeFile ? resumeFile.name : "Tap to Upload Resume"}
                            </p>
                            <p className="text-[9px] md:text-xs text-slate-400 font-bold uppercase tracking-widest leading-tight">PDF, DOCX — AI Optimization Ready</p>
                        </div>
                    </label>
                    {/* Clear file button */}
                    {resumeFile && !isUploading && (
                        <button
                            onClick={(e) => { e.preventDefault(); setResumeFile(null); setResumeError(null); setShowParsingPreview(false); }}
                            className="absolute top-2 right-2 md:top-3 md:right-3 w-6 h-6 md:w-7 md:h-7 rounded-full bg-slate-200 hover:bg-red-100 flex items-center justify-center transition-colors z-20"
                            title="Remove file"
                            aria-label="Remove uploaded resume"
                        >
                            <X className="h-3 w-3 md:h-4 md:w-4 text-slate-500 hover:text-red-500" />
                        </button>
                    )}
                    {isUploading && (
                        <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] rounded-[1.25rem] md:rounded-[2.5rem] flex flex-col items-center justify-center gap-3 z-10">
                            <div className="w-40 md:w-64 h-1.5 bg-slate-200 rounded-full overflow-hidden border border-slate-100 shadow-inner">
                                <motion.div
                                    className="h-full bg-primary-500"
                                    initial={shouldReduceMotion ? { width: "100%" } : { width: "0%" }}
                                    animate={{ width: "100%" }}
                                    transition={shouldReduceMotion ? undefined : { duration: 4, repeat: Infinity }}
                                />
                            </div>
                            <p className="text-[9px] md:text-xs font-black text-primary-600 uppercase tracking-widest animate-pulse">Scanning Vector Space...</p>
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

                {/* Resume Parsing Preview */}
                <AnimatePresence>
                    {showParsingPreview && parsedResume && (
                        <motion.div
                            initial={{ opacity: 0, height: 0, y: 20 }}
                            animate={{ opacity: 1, height: 'auto', y: 0 }}
                            exit={{ opacity: 0, height: 0, y: 20 }}
                            className="overflow-hidden"
                        >
                            <Card className="mt-10 p-8 rounded-[2.5rem] border-primary-100 bg-primary-50/40 relative shadow-xl">
                                <div className="absolute top-4 right-4 bg-emerald-500 text-white text-[9px] font-black px-2 py-0.5 rounded uppercase tracking-widest">
                                    98% Accuracy
                                </div>
                                <div className="flex items-center gap-3 mb-8">
                                    <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center text-white shadow-lg shadow-primary-500/20">
                                        <Sparkles className="h-6 w-6" />
                                    </div>
                                    <h3 className="font-black text-slate-900 text-xl tracking-tight">System Extraction Result:</h3>
                                </div>
                                <div className="grid gap-6">
                                    <div className="flex items-start gap-4 p-4 rounded-2xl bg-white/80 border border-white shadow-sm">
                                        <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-primary-500 shadow-inner">
                                            <User className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Inferred Professional Title</p>
                                            <p className="font-black text-slate-900 text-lg">{parsedResume.title}</p>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="flex items-start gap-4 p-4 rounded-2xl bg-white/80 border border-white shadow-sm">
                                            <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-primary-500 shadow-inner">
                                                <Briefcase className="h-5 w-5" />
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Depth</p>
                                                <p className="font-black text-slate-900 text-lg">{parsedResume.years} Years</p>
                                            </div>
                                        </div>
                                        <div className="flex items-start gap-4 p-4 rounded-2xl bg-white/80 border border-white shadow-sm">
                                            <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-primary-500 shadow-inner">
                                                <Sparkles className="h-5 w-5" />
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Core Stack</p>
                                                <p className="font-black text-slate-900 text-lg">{parsedResume.skills?.length || 0} Skills</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="p-4 rounded-2xl bg-white/80 border border-white shadow-sm">
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Extracted Competencies</p>
                                        <div className="flex flex-wrap gap-2">
                                            {parsedResume.skills?.map((skill, i) => (
                                                <motion.div
                                                    initial={{ opacity: 0, scale: 0.8 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    transition={{ delay: i * 0.05 }}
                                                    key={skill}
                                                >
                                                    <Badge variant="outline" className="text-[10px] font-black bg-white border-slate-100 text-slate-700 px-3 py-1 uppercase tracking-wider">{skill}</Badge>
                                                </motion.div>
                                            ))}
                                            {(!parsedResume.skills || parsedResume.skills.length === 0) && (
                                                <span className="text-xs text-slate-400 font-medium">Automatic extraction pending manual review...</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <Button
                                    variant="primary"
                                    className="w-full mt-10 h-12 rounded-[1.25rem] font-black text-lg bg-emerald-600 hover:bg-emerald-500 shadow-xl shadow-emerald-500/20"
                                    onClick={onConfirmParsing}
                                    aria-label="Lock in extracted information and proceed"
                                >
                                    LOCK IN & PROCEED
                                </Button>
                            </Card>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <div className="flex gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button variant="ghost" onClick={onPrev} className="h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4" aria-label="Go to previous step">
                    <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                    PREV
                </Button>
                {resumeFile && !resumeError ? (
                    <Button
                        onClick={() => onUpload(resumeFile)}
                        disabled={isUploading}
                        className="flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black bg-primary-600 hover:bg-primary-500 shadow-2xl shadow-primary-500/30 text-xs md:text-lg group overflow-hidden relative"
                        aria-label={showParsingPreview ? "Sync new source" : "Extract experience from resume"}
                    >
                        <span className="relative z-10 flex items-center justify-center">
                            {isUploading ? <LoadingSpinner size="sm" /> : showParsingPreview ? "SYNC NEW SOURCE" : "EXTRACT EXPERIENCE"}
                            <ArrowRight className="ml-1.5 md:ml-3 h-4 w-4 md:h-6 md:w-6 group-hover:translate-x-1 transition-transform" />
                        </span>
                    </Button>
                ) : (
                    <Button
                        variant={resumeError ? "primary" : "outline"}
                        onClick={onNext}
                        className={`flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black transition-all text-xs md:text-lg truncate ${resumeError
                            ? "bg-primary-600 hover:bg-primary-500 shadow-xl shadow-primary-500/30 text-white"
                            : "text-slate-500 hover:border-slate-900 hover:text-slate-900 border-2 border-slate-200"
                            }`}
                        aria-label={resumeError ? "Continue anyway despite error" : "Skip resume upload and proceed manually"}
                    >
                        {resumeError ? "CONTINUE ANYWAY" : "SKIP TO MANUAL"}
                    </Button>
                )}
            </div>
        </div>
    );
}
