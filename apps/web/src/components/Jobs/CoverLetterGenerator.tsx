import * as React from "react";
import { useState, useEffect } from "react";
import { X, Copy, RefreshCw, Wand2, Check, AlertCircle } from "lucide-react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { useCoverLetter } from "../../hooks/useCoverLetter";
import { useProfile } from "../../hooks/useProfile";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import type { JobPosting } from "../../hooks/useJobs";

interface CoverLetterGeneratorProps {
    job: JobPosting;
    isOpen: boolean;
    onClose: () => void;
}

export function CoverLetterGenerator({ job, isOpen, onClose }: CoverLetterGeneratorProps) {
    const { profile } = useProfile();
    const { generate, reset, loading, error, result } = useCoverLetter();
    const [tone, setTone] = useState("professional");
    const [copied, setCopied] = useState(false);

    // Reset when opened
    useEffect(() => {
        if (isOpen) {
            setCopied(false);
            reset();
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const handleGenerate = async () => {
        if (!profile) return;
        await generate(profile, job, tone);
    };

    const handleCopy = () => {
        if (result) {
            navigator.clipboard.writeText(result.content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4 animate-in fade-in duration-200">
            <div
                className="absolute inset-0"
                onClick={onClose}
            />

            <Card tone="glass" className="relative w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl animate-in zoom-in-95 duration-200 bg-white">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-100">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center">
                            <Wand2 className="h-5 w-5" />
                        </div>
                        <div>
                            <h2 className="font-display text-xl font-bold text-slate-900">AI Cover Letter</h2>
                            <p className="text-sm text-slate-500 font-medium">Drafting for {job.company}</p>
                        </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {!result && !loading ? (
                        <div className="space-y-6">
                            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-sm text-slate-600 leading-relaxed">
                                <p>
                                    This tool uses your profile and the job description to generate a tailored cover letter.
                                    Choose a tone and let AI do the heavy lifting.
                                </p>
                            </div>

                            <div className="space-y-3">
                                <label className="text-xs font-black text-slate-400 uppercase tracking-widest block">Tone</label>
                                <div className="grid grid-cols-3 gap-3">
                                    {["Professional", "Enthusiastic", "Confident"].map((t) => (
                                        <button
                                            key={t}
                                            onClick={() => setTone(t.toLowerCase())}
                                            className={`
                        py-3 px-4 rounded-xl text-sm font-bold transition-all border
                        ${tone === t.toLowerCase()
                                                    ? "bg-primary-50 border-primary-500 text-primary-700 ring-1 ring-primary-500"
                                                    : "bg-white border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50"
                                                }
                      `}
                                        >
                                            {t}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {error && (
                                <div className="p-4 rounded-xl bg-red-50 text-red-600 text-sm flex items-start gap-2">
                                    <AlertCircle className="h-5 w-5 shrink-0" />
                                    <p>{error}</p>
                                </div>
                            )}
                        </div>
                    ) : null}

                    {loading && (
                        <div className="py-20 flex flex-col items-center justify-center text-center space-y-4">
                            <LoadingSpinner size="lg" />
                            <p className="text-sm font-bold text-slate-400 animate-pulse">Analyzing job requirements...</p>
                        </div>
                    )}

                    {result && !loading && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="space-y-1">
                                <label className="text-xs font-black text-slate-400 uppercase tracking-widest">Subject Line</label>
                                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-sm font-medium text-slate-800 select-all">
                                    {result.subject_line}
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-black text-slate-400 uppercase tracking-widest">Content</label>
                                <div className="p-4 bg-white rounded-xl border border-slate-200 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap font-serif min-h-[300px]">
                                    {result.content}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between gap-4">
                    {!result ? (
                        <Button
                            variant="lagoon"
                            size="lg"
                            wobble
                            className="w-full gap-2"
                            onClick={handleGenerate}
                            disabled={loading || !profile}
                        >
                            {loading ? "Generating..." : "Generate Draft"}
                            {!loading && <Wand2 className="h-4 w-4" />}
                        </Button>
                    ) : (
                        <>
                            <Button variant="ghost" onClick={reset} disabled={loading}>
                                Discard
                            </Button>
                            <div className="flex gap-3">
                                <Button variant="outline" onClick={handleGenerate} disabled={loading}>
                                    <RefreshCw className="h-4 w-4 mr-2" />
                                    Regenerate
                                </Button>
                                <Button variant="lagoon" wobble onClick={handleCopy}>
                                    {copied ? (
                                        <>
                                            <Check className="h-4 w-4 mr-2" />
                                            Copied!
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="h-4 w-4 mr-2" />
                                            Copy to Clipboard
                                        </>
                                    )}
                                </Button>
                            </div>
                        </>
                    )}
                </div>
            </Card>
        </div>
    );
}
