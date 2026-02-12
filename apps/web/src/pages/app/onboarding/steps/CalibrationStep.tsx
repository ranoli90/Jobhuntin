import * as React from "react";
import { Rocket, ArrowLeft, ArrowRight } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";

interface CalibrationStepProps {
    onNext: () => void;
    onPrev: () => void;
    calibrationQuestions: any[];
    calibrationAnswers: Record<string, any>;
    updateFormData: (updates: any) => void;
    isFetchingQuestions: boolean;
    isSavingCalibration: boolean;
}

export function CalibrationStep({
    onNext,
    onPrev,
    calibrationQuestions,
    calibrationAnswers,
    updateFormData,
    isFetchingQuestions,
    isSavingCalibration,
}: CalibrationStepProps) {
    // Smart Skip Logic
    const [currentQuestionIndex, setCurrentQuestionIndex] = React.useState(0);

    React.useEffect(() => {
        if (calibrationQuestions.length > 0 && currentQuestionIndex < calibrationQuestions.length) {
            const currentQ = calibrationQuestions[currentQuestionIndex];
            // Frontend-side Smart Skip: If we detect the answer is already in `calibrationAnswers` and marked 'verified', skip.
            // For this demo, let's implement a "Auto-Advance on 100% Confidence" mock.
            if (currentQ.confidence && currentQ.confidence > 0.95) {
                // Auto-fill and skip
                updateFormData({
                    calibrationAnswers: {
                        ...calibrationAnswers,
                        [currentQ.id]: currentQ.suggested_answer
                    }
                });
                if (currentQuestionIndex < calibrationQuestions.length - 1) {
                    setCurrentQuestionIndex(prev => prev + 1);
                }
            }
        }
    }, [currentQuestionIndex, calibrationQuestions, calibrationAnswers, updateFormData]);

    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                <div className="flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6 mb-3 md:mb-8">
                    <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-indigo-50 border border-indigo-100 text-indigo-600 shadow-inner">
                        <Rocket className="h-4 w-4 md:h-8 md:w-8" />
                    </div>
                    <div className="min-w-0">
                        <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">Final Calibration</h2>
                        <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">Fine-tuning AI parameters for launch.</p>
                    </div>
                </div>

                {isFetchingQuestions ? (
                    <div className="flex flex-col items-center justify-center h-48 space-y-4">
                        <LoadingSpinner size="lg" />
                        <p className="text-slate-500 font-medium">Generating strategic questions...</p>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {calibrationQuestions.map((q: any) => (
                            <div key={q.id} className="p-4 rounded-2xl bg-white border border-slate-100 shadow-sm">
                                <label className="block text-sm md:text-base font-bold text-slate-900 mb-3">{q.text}</label>
                                {q.type === 'yes_no' && (
                                    <div className="flex gap-4" role="radiogroup" aria-label={q.text}>
                                        {['Yes', 'No'].map(opt => (
                                            <label
                                                key={opt}
                                                className={`flex-1 p-3 rounded-xl border-2 cursor-pointer transition-all ${calibrationAnswers[q.id] === opt ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-slate-100 hover:border-slate-200'}`}
                                            >
                                                <input
                                                    type="radio"
                                                    name={q.id}
                                                    value={opt}
                                                    checked={calibrationAnswers[q.id] === opt}
                                                    onChange={(e) => updateFormData({ calibrationAnswers: { ...calibrationAnswers, [q.id]: e.target.value } })}
                                                    className="sr-only"
                                                />
                                                <span className="block text-center font-bold" aria-hidden="true">{opt}</span>
                                                <span className="sr-only">{opt === 'Yes' ? 'Agree' : 'Disagree'}</span>
                                            </label>
                                        ))}
                                    </div>
                                )}
                                {q.type === 'select' && (
                                    <div className="relative">
                                        <select
                                            value={calibrationAnswers[q.id] || ""}
                                            onChange={(e) => updateFormData({ calibrationAnswers: { ...calibrationAnswers, [q.id]: e.target.value } })}
                                            className="w-full h-12 rounded-xl border-slate-200 pl-4 pr-10 text-sm font-medium focus:ring-primary-500 appearance-none bg-white"
                                        >
                                            <option value="">Select an option...</option>
                                            {(q.options || []).map((opt: string) => (
                                                <option key={opt} value={opt}>{opt}</option>
                                            ))}
                                        </select>
                                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6" /></svg>
                                        </div>
                                    </div>
                                )}
                                {q.type === 'text' && (
                                    <Input
                                        value={calibrationAnswers[q.id] || ""}
                                        onChange={(e) => updateFormData({ calibrationAnswers: { ...calibrationAnswers, [q.id]: e.target.value } })}
                                        placeholder="Your answer..."
                                        className="h-12"
                                    />
                                )}
                            </div>
                        ))}
                        {calibrationQuestions.length === 0 && (
                            <div className="text-center text-slate-500 py-10">
                                <p>No calibration needed. You're good to go!</p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div className="flex gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button variant="ghost" onClick={onPrev} className="h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4" aria-label="Go to previous step">
                    <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                    PREV
                </Button>
                <Button onClick={onNext} className="flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black bg-primary-600 hover:bg-primary-500 shadow-2xl shadow-primary-500/30 text-xs md:text-xl group" disabled={isSavingCalibration || isFetchingQuestions} aria-label="Complete calibration and prepare for launch">
                    {isSavingCalibration ? <LoadingSpinner size="sm" /> : "COMPLETE CALIBRATION"}
                    <ArrowRight className="ml-1.5 md:ml-3 h-4 w-4 md:h-6 md:w-6 group-hover:translate-x-1 transition-transform" />
                </Button>
            </div>
        </div>
    );
}
