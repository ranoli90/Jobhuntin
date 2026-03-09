import * as React from "react";
import { ArrowLeft, ArrowRight, Brain, Check, Rocket, Users, Compass, Microscope, Zap, Building2, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../../../components/ui/Button";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { WorkStyleProfile } from "../../../../types/onboarding";
import { t, getLocale } from "../../../../lib/i18n";

// Raw API values as keys - options use value for state, label for display (i18n-safe)
const getBehavioralQuestions = (locale: string): Array<{ id: string; question: string; options: { value: string; label: string }[]; maps_to: string }> => [
    {
        id: "blocked_dependency",
        question: t("onboarding.workStyleQuestion1", locale),
        options: [
            { value: "high", label: t("onboarding.workStyleQ1Option1", locale) },
            { value: "medium", label: t("onboarding.workStyleQ1Option2", locale) },
            { value: "low", label: t("onboarding.workStyleQ1Option3", locale) },
            { value: "medium", label: t("onboarding.workStyleQ1Option4", locale) }
        ],
        maps_to: "autonomy_preference"
    },
    {
        id: "learning_new_tech",
        question: t("onboarding.workStyleQuestion2", locale),
        options: [
            { value: "docs", label: t("onboarding.workStyleQ2Option1", locale) },
            { value: "building", label: t("onboarding.workStyleQ2Option2", locale) },
            { value: "pairing", label: t("onboarding.workStyleQ2Option3", locale) },
            { value: "courses", label: t("onboarding.workStyleQ2Option4", locale) }
        ],
        maps_to: "learning_style"
    },
    {
        id: "company_stage",
        question: t("onboarding.workStyleQuestion3", locale),
        options: [
            { value: "early_startup", label: t("onboarding.workStyleQ3Option1", locale) },
            { value: "growth", label: t("onboarding.workStyleQ3Option2", locale) },
            { value: "enterprise", label: t("onboarding.workStyleQ3Option3", locale) },
            { value: "flexible", label: t("onboarding.workStyleQ3Option4", locale) }
        ],
        maps_to: "company_stage_preference"
    },
    {
        id: "communication_style",
        question: t("onboarding.workStyleQuestion4", locale),
        options: [
            { value: "async", label: t("onboarding.workStyleQ4Option1", locale) },
            { value: "sync", label: t("onboarding.workStyleQ4Option2", locale) },
            { value: "mixed", label: t("onboarding.workStyleQ4Option3", locale) },
            { value: "flexible", label: t("onboarding.workStyleQ4Option4", locale) }
        ],
        maps_to: "communication_style"
    },
    {
        id: "work_pace",
        question: t("onboarding.workStyleQuestion5", locale),
        options: [
            { value: "fast", label: t("onboarding.workStyleQ5Option1", locale) },
            { value: "steady", label: t("onboarding.workStyleQ5Option2", locale) },
            { value: "methodical", label: t("onboarding.workStyleQ5Option3", locale) },
            { value: "flexible", label: t("onboarding.workStyleQ5Option4", locale) }
        ],
        maps_to: "pace_preference"
    },
    {
        id: "ownership_style",
        question: t("onboarding.workStyleQuestion6", locale),
        options: [
            { value: "solo", label: t("onboarding.workStyleQ6Option1", locale) },
            { value: "team", label: t("onboarding.workStyleQ6Option2", locale) },
            { value: "lead", label: t("onboarding.workStyleQ6Option3", locale) },
            { value: "flexible", label: t("onboarding.workStyleQ6Option4", locale) }
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

// Work style archetype definitions
interface Archetype {
    name: string;
    icon: typeof Rocket;
    description: string;
    gradient: string;
}

function computeArchetype(answers: Record<string, string>): Archetype {
    const autonomy = answers.autonomy_preference;
    const pace = answers.pace_preference;
    const ownership = answers.ownership_preference;
    const stage = answers.company_stage_preference;
    const trajectory = answers.career_trajectory;

    if (autonomy === "high" && ownership === "solo" && pace === "fast") {
        return { name: "The Autonomous Builder", icon: Rocket, description: "You thrive when given ownership and freedom to ship fast.", gradient: "from-primary-600 to-violet-600" };
    }
    if (ownership === "team" && answers.communication_style === "sync") {
        return { name: "The Collaborative Leader", icon: Users, description: "You shine when working closely with a team in real-time.", gradient: "from-blue-600 to-cyan-600" };
    }
    if (ownership === "lead" || trajectory === "manager" || trajectory === "tech_lead") {
        return { name: "The Strategic Guide", icon: Compass, description: "You lead by example and guide others to deliver.", gradient: "from-amber-600 to-orange-600" };
    }
    if (pace === "methodical" && answers.learning_style === "docs") {
        return { name: "The Thoughtful Craftsman", icon: Microscope, description: "You value quality and thoroughness above speed.", gradient: "from-emerald-600 to-teal-600" };
    }
    if (stage === "early_startup" || trajectory === "founder") {
        return { name: "The Startup Maverick", icon: Zap, description: "You love the chaos and ownership of building from zero.", gradient: "from-rose-600 to-pink-600" };
    }
    if (stage === "enterprise" && pace === "steady") {
        return { name: "The Systems Architect", icon: Building2, description: "You excel at scaling and structuring large systems.", gradient: "from-slate-600 to-slate-800" };
    }
    return { name: "The Adaptive Pro", icon: Sparkles, description: "You're versatile and can thrive in any environment.", gradient: "from-primary-600 to-purple-600" };
}

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

    const handleAnswer = (questionId: string, optionValue: string, mapsTo: string) => {
        // optionValue is already the raw API value (from options[].value)
        setAnswers(prev => ({ ...prev, [mapsTo]: optionValue }));

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
                                (question.options as { value: string; label: string }[]).map((option) => {
                                    const isSelected = answers[question.maps_to] === option.value;
                                    return (
                                        <button
                                            key={option.value}
                                            onClick={() => handleAnswer(question.id, option.value, question.maps_to)}
                                            className={`w-full p-3 md:p-4 rounded-xl text-left transition-all border-2 ${isSelected
                                                ? "border-emerald-500 bg-emerald-50 scale-[1.02] shadow-md"
                                                : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50 active:scale-[0.98]"
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

                {/* Archetype Reveal */}
                <AnimatePresence>
                    {isComplete && (() => {
                        const archetype = computeArchetype(answers);
                        const ArchetypeIcon = archetype.icon;
                        return (
                            <motion.div
                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ type: "spring", stiffness: 200, damping: 20 }}
                                className="mt-6 p-5 md:p-6 rounded-2xl text-center relative overflow-hidden"
                            >
                                <div className={`absolute inset-0 bg-gradient-to-br ${archetype.gradient}`} />
                                <div className="relative z-10">
                                    <div className="mx-auto mb-3 w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center">
                                        <ArchetypeIcon className="w-6 h-6 text-white" />
                                    </div>
                                    <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/50 mb-1">{t("onboarding.yourWorkStyle", locale) || "Your Work Style"}</p>
                                    <h3 className="text-lg md:text-xl font-black text-white mb-1">{archetype.name}</h3>
                                    <p className="text-xs text-white/70 font-medium">{archetype.description}</p>
                                </div>
                            </motion.div>
                        );
                    })()}
                </AnimatePresence>
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
