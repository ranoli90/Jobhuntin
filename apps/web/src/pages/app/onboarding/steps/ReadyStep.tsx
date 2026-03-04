import * as React from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Rocket, User, MapPin, Briefcase } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Card } from "../../../../components/ui/Card";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { pushToast } from "../../../../lib/toast";
import { t, getLocale } from "../../../../lib/i18n";

interface ContactInfo {
    first_name?: string;
    last_name?: string;
    email?: string;
}

interface PreferencesInfo {
    location?: string;
    role_type?: string;
    salary_min?: number | string;
}

interface ReadyStepProps {
    onNext: () => void;
    isCompleting: boolean;
    contactInfo: ContactInfo;
    preferences: PreferencesInfo;
    completeness: number;
    profile: { resume_url?: string | null } | null;
    resumeFile: File | null;
    shouldReduceMotion?: boolean;
}

export function ReadyStep({
    onNext,
    isCompleting,
    contactInfo,
    preferences,
    completeness,
    profile,
    resumeFile,
    shouldReduceMotion,
}: ReadyStepProps) {
    const locale = getLocale();

    const handleShareArchetype = async () => {
        const role = preferences.role_type || t("onboarding.techProfessional", locale) || "tech professional";
        const text = t("onboarding.shareArchetypeText", locale)?.replace("{role}", role) ||
            `I just set up my AI job hunter on JobHuntin as a ${role}. Check it out! #JobHuntin`;
        try {
            await navigator.clipboard.writeText(text);
            pushToast({
                title: t("onboarding.copiedClipboard", locale),
                description: t("onboarding.shareOnSocial", locale),
                tone: "success"
            });
        } catch {
            pushToast({
                title: t("onboarding.copyFailed", locale),
                description: t("onboarding.browserBlocked", locale),
                tone: "error"
            });
        }
    };

    const handleReferFriend = async () => {
        const text = t("onboarding.referFriendText", locale) || "Join me on JobHuntin and let AI apply for you! https://jobhuntin.com";
        try {
            await navigator.clipboard.writeText(text);
            pushToast({
                title: t("onboarding.linkCopied", locale),
                description: t("onboarding.shareWithFriends", locale),
                tone: "success"
            });
        } catch {
            pushToast({
                title: t("onboarding.copyFailed", locale),
                description: t("onboarding.browserBlocked", locale),
                tone: "error"
            });
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1">
                <div className="text-center py-2 md:py-6">
                    <div className="mx-auto mb-3 md:mb-10 relative">
                        <motion.div
                            initial={shouldReduceMotion ? { scale: 1 } : { scale: 0 }}
                            animate={shouldReduceMotion ? undefined : { scale: [1, 1.2, 1] }}
                            transition={shouldReduceMotion ? undefined : { duration: 0.5, times: [0, 0.5, 1] }}
                            className="absolute inset-0 bg-emerald-500/20 rounded-full blur-2xl"
                        />
                        <div className="relative mx-auto flex h-14 w-14 md:h-28 md:w-28 items-center justify-center rounded-[1.5rem] md:rounded-[3rem] bg-emerald-500 shadow-2xl shadow-emerald-200">
                            <CheckCircle2 className="h-7 w-7 md:h-12 md:w-16 text-white" aria-hidden />
                        </div>
                    </div>

                    <h1 className="mb-1 md:mb-4 font-display text-2xl md:text-5xl font-black text-slate-900 tracking-tight">
                        Launch <span className="text-indigo-600 italic">Ready.</span>
                    </h1>
                    <p className="mb-4 md:mb-12 text-slate-500 font-bold max-w-sm mx-auto text-sm md:text-lg leading-relaxed uppercase tracking-widest">
                        You're all set!
                    </p>

                    {/* Preferences Summary Table */}
                    <div className="mb-4 md:mb-12 relative">
                        <div className="absolute -inset-4 bg-gradient-to-b from-slate-900/5 to-transparent rounded-[3rem] -z-10 hidden md:block" />
                        <Card className="bg-slate-900 text-white p-4 md:p-10 rounded-[1.5rem] md:rounded-[3rem] shadow-2xl shadow-indigo-500/10 text-left relative overflow-hidden border-white/5 border-t-white/10">
                            <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-[100px]" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-6 md:mb-10 border-b border-white/5 pb-4 md:pb-6">
                                    <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                                        <Rocket className="h-4 w-4 md:h-5 md:w-5" aria-hidden />
                                    </div>
                                    <h3 className="font-black text-white/40 text-[9px] md:text-[11px] uppercase tracking-[0.4em]">
                                        Your Journey So Far
                                    </h3>
                                </div>
                                <div className="space-y-4 md:space-y-6">
                                    <div className="flex items-start justify-between group">
                                        <div>
                                            <p className="text-[8px] md:text-[10px] font-black text-white/20 uppercase tracking-[0.2em] mb-1">
                                                Your Details
                                            </p>
                                            <p className="font-black text-sm md:text-xl text-white group-hover:text-indigo-400 transition-colors uppercase">
                                                {contactInfo.first_name} {contactInfo.last_name}
                                            </p>
                                            <p className="text-[10px] md:text-xs text-white/30 font-medium mt-1 truncate">
                                                {contactInfo.email}
                                            </p>
                                        </div>
                                        <User className="h-4 w-4 md:h-6 md:w-6 text-white/5 group-hover:text-indigo-500 transition-all" aria-hidden />
                                    </div>
                                    <div className="flex items-start justify-between group">
                                        <div>
                                            <p className="text-[8px] md:text-[10px] font-black text-white/20 uppercase tracking-[0.2em] mb-1">
                                                Your Location
                                            </p>
                                            <p className="font-black text-sm md:text-xl text-white group-hover:text-indigo-400 transition-colors uppercase">
                                                {preferences.location || "Global Priority"}
                                            </p>
                                        </div>
                                        <MapPin className="h-4 w-4 md:h-6 md:w-6 text-white/5 group-hover:text-indigo-500 transition-all" aria-hidden />
                                    </div>
                                    <div className="flex items-start justify-between group">
                                        <div>
                                            <p className="text-[8px] md:text-[10px] font-black text-white/20 uppercase tracking-[0.2em] mb-1">
                                                Target Role
                                            </p>
                                            <p className="font-black text-sm md:text-xl text-white group-hover:text-indigo-400 transition-colors uppercase">
                                                {preferences.role_type || "Senior Impact Role"}
                                            </p>
                                        </div>
                                        <Briefcase className="h-4 w-4 md:h-6 md:w-6 text-white/5 group-hover:text-indigo-500 transition-all" aria-hidden />
                                    </div>
                                </div>
                                <div className="mt-8 md:mt-12 pt-6 md:pt-10 border-t border-white/5 grid grid-cols-2 gap-4 md:gap-8">
                                    <div className="p-4 md:p-6 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 group">
                                        <p className="text-[9px] md:text-[10px] uppercase font-black text-indigo-500/70 mb-1 tracking-widest">
                                            Strategy Strength
                                        </p>
                                        <p className="text-2xl md:text-3xl font-black text-indigo-400 italic">{completeness}%</p>
                                    </div>
                                    <div className="p-4 md:p-6 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 group">
                                        <p className="text-[9px] md:text-[10px] uppercase font-black text-indigo-500/70 mb-1 tracking-widest">
                                            Profile Points
                                        </p>
                                        <p className="text-2xl md:text-3xl font-black text-indigo-400 italic">
                                            {[contactInfo.first_name, contactInfo.email, preferences.location, preferences.role_type, (preferences.salary_min != null && preferences.salary_min !== ""), (profile?.resume_url || (resumeFile instanceof File))].filter(Boolean).length}/6
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </div>
                </div>
            </div>

            <div className="pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent dark:from-slate-950 dark:via-slate-950/95 backdrop-blur">
                <Button
                    size="lg"
                    variant="primary"
                    onClick={onNext}
                    className="w-full h-14 md:h-20 rounded-[1.5rem] md:rounded-[3rem] text-lg md:text-3xl font-black shadow-2xl shadow-indigo-600/30 bg-indigo-600 hover:bg-indigo-500 hover:scale-[1.02] active:scale-95 transition-all group overflow-hidden relative"
                    disabled={isCompleting}
                    aria-label="Start My Hunt"
                    data-onboarding-next
                >
                    <span className="relative z-10 flex items-center justify-center gap-2 md:gap-4">
                        {isCompleting ? <LoadingSpinner size="sm" /> : "Start My Hunt"}
                        <Rocket className="h-6 w-6 md:h-10 md:w-10 group-hover:translate-x-2 group-hover:-translate-y-2 transition-transform" aria-hidden />
                    </span>
                    <motion.div
                        animate={shouldReduceMotion ? undefined : { x: ['-100%', '200%'] }}
                        transition={shouldReduceMotion ? undefined : { duration: 1.5, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12"
                    />
                </Button>
                <div className="mt-4 md:mt-10 flex justify-center">
                    <button
                        onClick={handleShareArchetype}
                        className="text-[10px] md:text-xs font-bold text-indigo-600 hover:text-indigo-700 underline decoration-dotted underline-offset-4 flex items-center gap-1 opacity-80 hover:opacity-100 transition-opacity"
                    >
                        <User className="w-3 h-3" aria-hidden />
                        {t("onboarding.shareArchetype", locale)}
                    </button>
                    <div className="w-[1px] h-3 bg-slate-300 mx-3 opacity-50"></div>
                    <button
                        onClick={handleReferFriend}
                        className="text-[10px] md:text-xs font-bold text-slate-400 hover:text-slate-600 underline decoration-dotted underline-offset-4 transition-colors"
                    >
                        {t("onboarding.referFriend", locale)}
                    </button>
                </div>
            </div>
        </div>
    );
}
