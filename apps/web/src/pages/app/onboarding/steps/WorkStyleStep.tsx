import * as React from "react";
import { ArrowLeft, ArrowRight, Brain, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../../../components/ui/Button";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { BehavioralQuestion, WorkStyleProfile } from "../../../../types/onboarding";
import { t, getLocale } from "../../../../lib/i18n";

const getBehavioralQuestions = (locale: string): BehavioralQuestion[] => [
    {
        id: "blocked_dependency",
        question: t("onboarding.workStyleQuestion1", locale),
        options: [
            t("onboarding.workStyleQ1Option1", locale),
            t("onboarding.workStyleQ1Option2", locale),
            t("onboarding.workStyleQ1Option3", locale),
            t("onboarding.workStyleQ1Option4", locale)
        ],
        maps_to: "autonomy_preference"
    },
    {
        id: "learning_new_tech",
        question: t("onboarding.workStyleQuestion2", locale),
        options: [
            t("onboarding.workStyleQ2Option1", locale),
            t("onboarding.workStyleQ2Option2", locale),
            t("onboarding.workStyleQ2Option3", locale),
            t("onboarding.workStyleQ2Option4", locale)
        ],
        maps_to: "learning_style"
    },
    {
        id: "company_stage",
        question: t("onboarding.workStyleQuestion3", locale),
        options: [
            t("onboarding.workStyleQ3Option1", locale),
            t("onboarding.workStyleQ3Option2", locale),
            t("onboarding.workStyleQ3Option3", locale),
            t("onboarding.workStyleQ3Option4", locale)
        ],
        maps_to: "company_stage_preference"
    },
    {
        id: "communication_style",
        question: t("onboarding.workStyleQuestion4", locale),
        options: [
            t("onboarding.workStyleQ4Option1", locale),
            t("onboarding.workStyleQ4Option2", locale),
            t("onboarding.workStyleQ4Option3", locale),
            t("onboarding.workStyleQ4Option4", locale)
        ],
        maps_to: "communication_style"
    },
    {
        id: "work_pace",
        question: t("onboarding.workStyleQuestion5", locale),
        options: [
            t("onboarding.workStyleQ5Option1", locale),
            t("onboarding.workStyleQ5Option2", locale),
            t("onboarding.workStyleQ5Option3", locale),
            t("onboarding.workStyleQ5Option4", locale)
        ],
        maps_to: "pace_preference"
    },
    {
        id: "ownership_style",
        question: t("onboarding.workStyleQuestion6", locale),
        options: [
            t("onboarding.workStyleQ6Option1", locale),
            t("onboarding.workStyleQ6Option2", locale),
            t("onboarding.workStyleQ6Option3", locale),
            t("onboarding.workStyleQ6Option4", locale)
        ],
        maps_to: "ownership_preference"
    }
];

const getTrajectoryQuestion = (locale: string) => ({
    id: "career_trajectory",
    question: t("onboarding.workStyleQuestion7", locale),
    options: [
        { value: "ic", label: t("onboarding.workStyleQ7Option1", locale) },
        { value: "tech_lead", label: t("onboarding.workStyleQ7Option2", locale) },
        { value: "manager", label: t("onboarding.workStyleQ7Option3", locale) },
        { value: "founder", label: t("onboarding.workStyleQ7Option4", locale) },
        { value: "open", label: t("onboarding.workStyleQ7Option5", locale) }
    ]
});

const VALUE_MAPS: Record<string, Record<string, string>> = {
    autonomy_preference: {
        "Build a workaround and move forward": "high",
        "Escalate to get unblocked": "medium",
        "Document the blocker and wait": "low",
        "Pick up other work while waiting": "medium"
    },
    learning_style: {
        "Read docs thoroughly first": "docs",
        "Build something small immediately": "building",
        "Pair with someone experienced": "pairing",
        "Take a structured course": "courses"
    },
    company_stage_preference: {
        "Early-stage startup (chaos, ownership)": "early_startup",
        "Growth-stage company (scaling, process)": "growth",
        "Enterprise (stability, specialization)": "enterprise",
        "No strong preference": "flexible"
    },
    communication_style: {
        "Async (Slack, docs, PRs)": "async",
        "Real-time (meetings, pairing)": "sync",
        "Mixed depending on urgency": "mixed",
        "Whatever the team prefers": "flexible"
    },
    pace_preference: {
        "Fast (ship fast, iterate)": "fast",
        "Steady (predictable sprints)": "steady",
        "Methodical (thorough before shipping)": "methodical",
        "Varies by project": "flexible"
    },
    ownership_preference: {
        "Solo (end-to-end ownership)": "solo",
        "Team (collaborative ownership)": "team",
        "Lead (guide others, delegate)": "lead",
        "Mix depending on scope": "flexible"
    }
};

interface WorkStyleStepProps {
    onNext: () => void;
    onPrev: () => void;
    answers: Record<string, string>;
    setAnswers: React.Dispatch<React.SetStateAction<Record<string, string>>>;
    isSaving: boolean;
}

export function WorkStyleStep({
    onNext,
    onPrev,
    answers,
    setAnswers,
    isSaving,
}: WorkStyleStepProps) {
    const locale = getLocale();
    const BEHAVIORAL_QUESTIONS = getBehavioralQuestions(locale);
    const TRAJECTORY_QUESTION = getTrajectoryQuestion(locale);
    
    const [currentQuestion, setCurrentQuestion] = React.useState(0);
    const allQuestions = [...BEHAVIORAL_QUESTIONS, { ...TRAJECTORY_QUESTION, maps_to: "career_trajectory" }];
    const totalQuestions = allQuestions.length;

    const answeredCount = allQuestions.filter(q => answers[q.maps_to]).length;
    const progress = (answeredCount / totalQuestions) * 100;
    const isComplete = answeredCount >= 4;

    const handleAnswer = (questionId: string, option: string, mapsTo: string) => {
        let value = option;

        // For trajectory, use the value directly
        if (questionId === "career_trajectory") {
            value = option;
        } else {
            // For behavioral questions, map to the profile value
            const valueMap = VALUE_MAPS[mapsTo];
            if (valueMap && valueMap[option]) {
                value = valueMap[option];
            }
        }

        setAnswers(prev => ({ ...prev, [mapsTo]: value }));

        if (currentQuestion < totalQuestions - 1) {
            // Skip to next unanswered question instead of blindly incrementing
            setTimeout(() => {
                setCurrentQuestion(curr => {
                    // Look for the next unanswered question starting from curr + 1
                    for (let i = curr + 1; i < totalQuestions; i++) {
                        if (!answers[allQuestions[i].maps_to] && allQuestions[i].maps_to !== mapsTo) {
                            return i;
                        }
                    }
                    // If all remaining are answered, just go to next
                    return Math.min(curr + 1, totalQuestions - 1);
                });
            }, 600);
        }
    };

    const question = allQuestions[currentQuestion];

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1">
                <div className="mb-3 md:mb-6 flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6">
                    <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-emerald-50 border border-emerald-100 text-emerald-600 shadow-inner">
                        <Brain className="h-4 w-4 md:h-8 md:w-8" />
                    </div>
                    <div className="min-w-0">
                        <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">
                            {t("onboarding.workStyleTitle", locale)}
                        </h2>
                        <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">
                            {t("onboarding.workStyleSubtitle", locale)}
                        </p>
                    </div>
                </div>

                {/* Progress dots */}
                <div className="flex gap-1.5 mb-4 md:mb-6 justify-center">
                    {allQuestions.map((q, idx) => (
                        <button
                            key={q.id}
                            onClick={() => setCurrentQuestion(idx)}
                            className={`w-2 h-2 md:w-2.5 md:h-2.5 rounded-full transition-all ${answers[q.maps_to]
                                    ? "bg-emerald-500"
                                    : idx === currentQuestion
                                        ? "bg-slate-400 scale-125"
                                        : "bg-slate-200"
                                }`}
                            aria-label={`${t("onboarding.question", locale) || "Question"} ${idx + 1}`}
                        />
                    ))}
                </div>

                {/* Question card */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={question.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.2 }}
                        className="space-y-4"
                    >
                        <h3 className="text-base md:text-xl font-bold text-slate-900 text-center">
                            {question.question}
                        </h3>

                        <div className="space-y-2 md:space-y-3">
                            {"options" in question && question.options.length > 0 && (
                                typeof question.options[0] === "string"
                                    ? (question.options as string[]).map((option) => {
                                        const isSelected = answers[question.maps_to] === VALUE_MAPS[question.maps_to]?.[option];
                                        return (
                                            <button
                                                key={option}
                                                onClick={() => handleAnswer(question.id, option, question.maps_to)}
                                                className={`w-full p-3 md:p-4 rounded-xl text-left transition-all border-2 ${isSelected
                                                        ? "border-emerald-500 bg-emerald-50"
                                                        : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
                                                    }`}
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm md:text-base font-medium text-slate-700">{option}</span>
                                                    {isSelected && (
                                                        <Check className="w-4 h-4 md:w-5 md:h-5 text-emerald-600" />
                                                    )}
                                                </div>
                                            </button>
                                        );
                                    })
                                    : (question.options as { value: string; label: string }[]).map((option) => {
                                        const isSelected = answers[question.maps_to] === option.value;
                                        return (
                                            <button
                                                key={option.value}
                                                onClick={() => handleAnswer(question.id, option.value, question.maps_to)}
                                                className={`w-full p-3 md:p-4 rounded-xl text-left transition-all border-2 ${isSelected
                                                        ? "border-emerald-500 bg-emerald-50"
                                                        : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
                                                    }`}
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm md:text-base font-medium text-slate-700">{option.label}</span>
                                                    {isSelected && (
                                                        <Check className="w-4 h-4 md:w-5 md:h-5 text-emerald-600" />
                                                    )}
                                                </div>
                                            </button>
                                        );
                                    })
                            )}
                        </div>
                    </motion.div>
                </AnimatePresence>

                {/* Question counter */}
                <p className="mt-4 md:mt-6 text-center text-[10px] md:text-xs text-slate-400">
                    {t("onboarding.questionCounter", locale).replace("{current}", String(currentQuestion + 1)).replace("{total}", String(totalQuestions))}
                </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button
                    variant="ghost"
                    onClick={onPrev}
                    className="h-12 sm:h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4 touch-manipulation"
                    aria-label={t("onboarding.back", locale)}
                >
                    <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                    {t("onboarding.prev", locale)}
                </Button>
                {!isComplete && (
                    <Button
                        variant="outline"
                        onClick={onNext}
                        disabled={isSaving}
                        className="h-12 sm:h-9 md:h-12 rounded-[1.25rem] font-black border-2 border-slate-200 text-slate-600 hover:bg-slate-50 transition-all text-[10px] md:text-sm px-4 touch-manipulation"
                        aria-label={t("onboarding.skip", locale)}
                    >
                        {t("onboarding.skip", locale)}
                    </Button>
                )}
                <Button
                    onClick={onNext}
                    disabled={!isComplete || isSaving}
                    className="flex-[2] h-12 sm:h-9 md:h-12 rounded-[1.25rem] font-black bg-emerald-600 hover:bg-emerald-500 shadow-2xl shadow-emerald-500/30 text-xs md:text-lg disabled:opacity-50 disabled:cursor-not-allowed group touch-manipulation"
                    aria-label={t("onboarding.saveWorkStyle", locale)} data-onboarding-next
                >
                    {isSaving ? <LoadingSpinner size="sm" /> : (
                        <>
                            {t("onboarding.saveWorkStyle", locale)}
                            <ArrowRight className="ml-1 md:ml-2 h-3.5 w-3.5 md:h-5 md:w-5 group-hover:translate-x-1 transition-transform" />
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}
