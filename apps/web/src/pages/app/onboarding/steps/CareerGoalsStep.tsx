import * as React from "react";
import { ArrowLeft, ArrowRight, Target, Flame, Eye, Sprout, Clock, Briefcase, TrendingUp, Heart, DollarSign, Scale, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../../../components/ui/Button";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { t, getLocale } from "../../../../lib/i18n";

interface CareerGoalsStepProps {
    onNext: () => void;
    onPrev: () => void;
    careerGoals: {
        experience_level: string;
        urgency: string;
        primary_goal: string;
        why_leaving: string;
    };
    setCareerGoals: React.Dispatch<React.SetStateAction<{
        experience_level: string;
        urgency: string;
        primary_goal: string;
        why_leaving: string;
    }>>;
    isSaving: boolean;
}

const EXPERIENCE_LEVELS = [
    { value: "0-1", labelKey: "onboarding.expLevelEntry", subKey: "onboarding.expLevelEntrySub", gradient: "from-sky-400 to-blue-500" },
    { value: "1-3", labelKey: "onboarding.expLevelJunior", subKey: "onboarding.expLevelJuniorSub", gradient: "from-teal-400 to-emerald-500" },
    { value: "3-5", labelKey: "onboarding.expLevelMid", subKey: "onboarding.expLevelMidSub", gradient: "from-amber-400 to-orange-500" },
    { value: "5-10", labelKey: "onboarding.expLevelSenior", subKey: "onboarding.expLevelSeniorSub", gradient: "from-violet-400 to-purple-600" },
    { value: "10+", labelKey: "onboarding.expLevelStaff", subKey: "onboarding.expLevelStaffSub", gradient: "from-rose-400 to-pink-600" },
];

const URGENCY_OPTIONS = [
    { value: "active", icon: Flame, labelKey: "onboarding.urgencyActive", descKey: "onboarding.urgencyActiveDesc", color: "border-red-200 bg-red-50/50 hover:border-red-300", iconColor: "text-red-500" },
    { value: "open", icon: Eye, labelKey: "onboarding.urgencyOpen", descKey: "onboarding.urgencyOpenDesc", color: "border-amber-200 bg-amber-50/50 hover:border-amber-300", iconColor: "text-amber-500" },
    { value: "exploring", icon: Sprout, labelKey: "onboarding.urgencyExploring", descKey: "onboarding.urgencyExploringDesc", color: "border-emerald-200 bg-emerald-50/50 hover:border-emerald-300", iconColor: "text-emerald-500" },
];

const GOALS = [
    { value: "senior_ic", labelKey: "onboarding.goalSeniorIc", icon: TrendingUp },
    { value: "management", labelKey: "onboarding.goalManagement", icon: Briefcase },
    { value: "career_change", labelKey: "onboarding.goalCareerChange", icon: Target },
    { value: "higher_comp", labelKey: "onboarding.goalHigherComp", icon: DollarSign },
    { value: "work_life", labelKey: "onboarding.goalWorkLife", icon: Scale },
    { value: "startup", labelKey: "onboarding.goalStartup", icon: Flame },
];

const REASONS = [
    { value: "growth", labelKey: "onboarding.reasonGrowth" },
    { value: "compensation", labelKey: "onboarding.reasonCompensation" },
    { value: "culture", labelKey: "onboarding.reasonCulture" },
    { value: "layoff", labelKey: "onboarding.reasonLayoff" },
    { value: "relocation", labelKey: "onboarding.reasonRelocation" },
    { value: "contract_ending", labelKey: "onboarding.reasonContract" },
    { value: "not_employed", labelKey: "onboarding.reasonNotEmployed" },
];

export function CareerGoalsStep({
    onNext,
    onPrev,
    careerGoals,
    setCareerGoals,
    isSaving,
}: CareerGoalsStepProps) {
    const locale = getLocale();

    return (
        <div className="flex flex-col h-full" role="region" aria-labelledby="career-goals-step-title">
            <div className="flex-1">
                {/* Header */}
                <div className="mb-4 md:mb-6 flex items-center gap-3 md:gap-4 border-b border-slate-100 pb-4 md:pb-6">
                    <div className="flex h-10 w-12 md:h-12 md:w-14 shrink-0 items-center justify-center rounded-xl md:rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/20">
                        <Target className="h-5 w-5 md:h-6 md:w-6" />
                    </div>
                    <div className="min-w-0">
                        <h2 id="career-goals-step-title" className="font-display text-lg md:text-2xl font-bold text-slate-900 tracking-tight">
                            {t("onboarding.careerGoalsTitle", locale) || "Career Goals"}
                        </h2>
                        <p className="text-xs md:text-sm text-slate-500 font-medium">
                            {t("onboarding.careerGoalsSubtitle", locale) || "Help us understand where you're headed"}
                        </p>
                    </div>
                </div>

                {/* Experience Level */}
                <div className="mb-6">
                    <label className="mb-3 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        <Clock className="w-3 h-3" />
                        {t("onboarding.experienceLevel", locale) || "Experience Level"} <span className="text-red-400">*</span>
                    </label>
                    <div className="grid grid-cols-3 md:grid-cols-5 gap-2" role="radiogroup" aria-label="Experience level">
                        {EXPERIENCE_LEVELS.map((level) => {
                            const isSelected = careerGoals.experience_level === level.value;
                            return (
                                <button
                                    key={level.value}
                                    role="radio"
                                    aria-checked={isSelected}
                                    onClick={() => setCareerGoals(prev => ({ ...prev, experience_level: level.value }))}
                                    className={`relative min-h-[44px] p-3 rounded-xl text-center transition-all border-2 ${isSelected
                                        ? "border-primary-500 shadow-md scale-[1.02]"
                                        : "border-slate-100 hover:border-slate-200 active:scale-[0.98]"
                                        }`}
                                >
                                    <div className={`mx-auto w-8 h-8 rounded-lg bg-gradient-to-br ${level.gradient} mb-2 flex items-center justify-center ${isSelected ? "shadow-lg" : ""}`}>
                                        <span className="text-white text-xs font-black">{level.value.replace("+", "")}</span>
                                    </div>
                                    <p className="text-[10px] md:text-xs font-bold text-slate-900">{t(level.labelKey, locale) || level.labelKey}</p>
                                    <p className="text-[8px] md:text-[10px] text-slate-400">{t(level.subKey, locale) || level.subKey}</p>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Job Search Urgency */}
                <div className="mb-6">
                    <label className="mb-3 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        <Flame className="w-3 h-3" />
                        {t("onboarding.searchUrgency", locale) || "How urgently are you looking?"} <span className="text-red-400">*</span>
                    </label>
                    <div className="grid gap-2" role="radiogroup" aria-label="Job search urgency">
                        {URGENCY_OPTIONS.map((option) => {
                            const isSelected = careerGoals.urgency === option.value;
                            const UrgencyIcon = option.icon;
                            return (
                                <button
                                    key={option.value}
                                    role="radio"
                                    aria-checked={isSelected}
                                    onClick={() => setCareerGoals(prev => ({ ...prev, urgency: option.value }))}
                                    className={`flex items-center gap-3 min-h-[44px] p-3 md:p-4 rounded-xl text-left transition-all border-2 ${isSelected
                                        ? "border-primary-500 bg-primary-50 shadow-md scale-[1.01]"
                                        : `${option.color} active:scale-[0.99]`
                                        }`}
                                >
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${isSelected ? 'bg-primary-100' : 'bg-white'}`}>
                                        <UrgencyIcon className={`w-5 h-5 ${isSelected ? 'text-primary-600' : option.iconColor}`} />
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-slate-900">{t(option.labelKey, locale) || option.labelKey}</p>
                                        <p className="text-xs text-slate-500">{t(option.descKey, locale) || option.descKey}</p>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Primary Career Goal */}
                <div className="mb-6">
                    <label className="mb-3 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        <Target className="w-3 h-3" />
                        {t("onboarding.primaryGoal", locale) || "Primary career goal"}
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2" role="radiogroup" aria-label="Primary career goal">
                        {GOALS.map((goal) => {
                            const isSelected = careerGoals.primary_goal === goal.value;
                            const Icon = goal.icon;
                            return (
                                <button
                                    key={goal.value}
                                    role="radio"
                                    aria-checked={isSelected}
                                    onClick={() => setCareerGoals(prev => ({
                                        ...prev,
                                        primary_goal: prev.primary_goal === goal.value ? "" : goal.value
                                    }))}
                                    className={`flex items-center gap-2 min-h-[44px] p-3 rounded-xl text-left transition-all border-2 ${isSelected
                                        ? "border-primary-500 bg-primary-50 shadow-sm"
                                        : "border-slate-100 hover:border-slate-200 active:scale-[0.98]"
                                        }`}
                                >
                                    <Icon className={`w-4 h-4 shrink-0 ${isSelected ? "text-primary-600" : "text-slate-400"}`} />
                                    <span className="text-xs font-bold text-slate-700">{t(goal.labelKey, locale) || goal.labelKey}</span>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Why Leaving (Optional) */}
                <div className="mb-4">
                    <label className="mb-3 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        <Heart className="w-3 h-3" />
                        {t("onboarding.whyLeaving", locale) || "Why are you looking?"} <span className="text-slate-300 font-normal normal-case tracking-normal">(optional)</span>
                    </label>
                    <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Why are you looking">
                        {REASONS.map((reason) => {
                            const isSelected = careerGoals.why_leaving === reason.value;
                            return (
                                <button
                                    key={reason.value}
                                    role="radio"
                                    aria-checked={isSelected}
                                    onClick={() => setCareerGoals(prev => ({
                                        ...prev,
                                        why_leaving: prev.why_leaving === reason.value ? "" : reason.value
                                    }))}
                                    className={`min-h-[44px] px-4 py-2 rounded-full text-xs font-bold transition-all border flex items-center ${isSelected
                                        ? "border-primary-500 bg-primary-50 text-primary-700"
                                        : "border-slate-200 text-slate-600 hover:border-slate-300 active:scale-[0.97]"
                                        }`}
                                >
                                    {t(reason.labelKey, locale) || reason.labelKey}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4 mt-4 shrink-0">
                <Button
                    type="button"
                    variant="ghost"
                    onClick={onPrev}
                    className="h-12 sm:h-11 rounded-xl font-bold text-slate-400 hover:text-slate-900 border border-slate-100 hover:bg-slate-50 text-sm px-4 touch-manipulation"
                    aria-label={t("onboarding.back", locale)}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    {t("onboarding.back", locale)}
                </Button>
                <Button
                    type="button"
                    onClick={onNext}
                    disabled={isSaving || !careerGoals.experience_level || !careerGoals.urgency}
                    className="flex-1 h-12 sm:h-11 rounded-xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-500 hover:to-purple-500 shadow-lg shadow-primary-500/20 text-sm disabled:opacity-50 disabled:cursor-not-allowed group touch-manipulation"
                    aria-label={t("onboarding.saveContinue", locale) || "Save & Continue"}
                    data-onboarding-next
                >
                    {isSaving ? <LoadingSpinner size="sm" /> : (
                        <>
                            {t("onboarding.saveContinue", locale) || "Save & Continue"}
                            <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}
