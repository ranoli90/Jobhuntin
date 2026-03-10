import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Rocket, User, MapPin, Briefcase, Sparkles, Trophy } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Card } from "../../../../components/ui/Card";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { Confetti } from "../../../../components/ui/Confetti";
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
    const [showConfetti, setShowConfetti] = React.useState(false);
    const [countdown, setCountdown] = React.useState<number | null>(null);
    const [isLaunching, setIsLaunching] = React.useState(false);
    const timersRef = React.useRef<ReturnType<typeof setTimeout>[]>([]);

    // Clean up all timers on unmount
    React.useEffect(() => {
        return () => {
            timersRef.current.forEach(clearTimeout);
        };
    }, []);

    // Trigger confetti on mount
    React.useEffect(() => {
        if (!shouldReduceMotion) {
            const timer = setTimeout(() => setShowConfetti(true), 500);
            return () => clearTimeout(timer);
        }
    }, [shouldReduceMotion]);

    const handleLaunch = () => {
        if (shouldReduceMotion) {
            onNext();
            return;
        }

        // Clear any previous timers
        timersRef.current.forEach(clearTimeout);
        timersRef.current = [];

        // Start countdown sequence
        setCountdown(3);
        timersRef.current.push(setTimeout(() => setCountdown(2), 700));
        timersRef.current.push(setTimeout(() => setCountdown(1), 1400));
        timersRef.current.push(setTimeout(() => {
            setCountdown(null);
            setIsLaunching(true);
            setShowConfetti(true);
        }, 2100));
        timersRef.current.push(setTimeout(() => {
            onNext();
        }, 3200));
    };

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

    const profilePoints = [
        contactInfo.first_name,
        contactInfo.email,
        preferences.location,
        preferences.role_type,
        (preferences.salary_min != null && preferences.salary_min !== ""),
        (profile?.resume_url || (resumeFile instanceof File))
    ].filter(Boolean).length;

    return (
        <div className="flex flex-col h-full" role="region" aria-labelledby="ready-step-title">
            <Confetti active={showConfetti} onComplete={() => setShowConfetti(false)} />

            {/* Countdown overlay */}
            <AnimatePresence>
                {countdown !== null && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm"
                        role="status"
                        aria-live="polite"
                    >
                        <motion.span
                            key={countdown}
                            initial={{ scale: 3, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.5, opacity: 0 }}
                            transition={{ duration: 0.4, ease: "easeOut" }}
                            className="text-8xl md:text-9xl font-black text-white"
                        >
                            {countdown}
                        </motion.span>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className={`flex-1 ${isLaunching ? "animate-lift-off" : ""}`}>
                <div className="text-center py-2 md:py-6">
                    <div className="mx-auto mb-3 md:mb-10 relative">
                        <motion.div
                            initial={shouldReduceMotion ? { scale: 1 } : { scale: 0 }}
                            animate={shouldReduceMotion ? undefined : { scale: [1, 1.2, 1] }}
                            transition={shouldReduceMotion ? undefined : { duration: 0.5, times: [0, 0.5, 1] }}
                            className="absolute inset-0 bg-emerald-500/20 rounded-full blur-2xl"
                        />
                        <motion.div
                            initial={shouldReduceMotion ? undefined : { scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={shouldReduceMotion ? undefined : { type: "spring", stiffness: 200, delay: 0.3 }}
                            className="relative mx-auto flex h-14 w-14 md:h-28 md:w-28 items-center justify-center rounded-[1.5rem] md:rounded-[3rem] bg-gradient-to-br from-emerald-500 to-teal-500 shadow-2xl shadow-emerald-200"
                        >
                            <CheckCircle2 className="h-7 w-7 md:h-12 md:w-16 text-white" aria-hidden />
                        </motion.div>
                    </div>

                    {/* Achievement badge */}
                    <motion.div
                        initial={shouldReduceMotion ? undefined : { opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-50 border border-amber-200 mb-3"
                    >
                        <Trophy className="w-3 h-3 text-amber-600" />
                        <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">
                            {t("onboarding.profileComplete", locale) || "Profile"} {completeness}% {t("onboarding.complete", locale) || "Complete"}
                        </span>
                    </motion.div>

                    <h1 id="ready-step-title" className="mb-1 md:mb-4 font-display text-2xl md:text-5xl font-black text-slate-900 tracking-tight">
                        {t("onboarding.launchTitle", locale) || "Launch"} <span className="text-primary-600 italic">{t("onboarding.launchReady", locale) || "Ready."}</span>
                    </h1>
                    <p className="mb-4 md:mb-12 text-slate-500 font-bold max-w-sm mx-auto text-sm md:text-lg leading-relaxed">
                        {t("onboarding.launchSubtitle", locale) || "Your AI job hunter is armed and ready to find your perfect match"}
                    </p>

                    {/* Summary Card */}
                    <div className="mb-4 md:mb-12 relative">
                        <div className="absolute -inset-4 bg-gradient-to-b from-slate-900/5 to-transparent rounded-[3rem] -z-10 hidden md:block" />
                        <Card className="bg-slate-900 text-white p-4 md:p-10 rounded-[1.5rem] md:rounded-[3rem] shadow-2xl shadow-primary-500/10 text-left relative overflow-hidden border-white/5 border-t-white/10">
                            <div className="absolute top-0 right-0 w-80 h-80 bg-primary-500/10 rounded-full blur-[100px]" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-6 md:mb-10 border-b border-white/5 pb-4 md:pb-6">
                                    <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-primary-500/20 flex items-center justify-center text-primary-400">
                                        <Rocket className="h-4 w-4 md:h-5 md:w-5" aria-hidden />
                                    </div>
                                    <h3 className="font-black text-white/40 text-[9px] md:text-[11px] uppercase tracking-[0.4em]">
                                        {t("onboarding.journeySoFar", locale) || "Your Journey So Far"}
                                    </h3>
                                </div>
                                <div className="space-y-4 md:space-y-6">
                                    {[
                                        { label: t("onboarding.yourDetails", locale) || "Your Details", value: `${contactInfo.first_name} ${contactInfo.last_name}`, sub: contactInfo.email, icon: User },
                                        { label: t("onboarding.yourLocation", locale) || "Your Location", value: preferences.location || (t("onboarding.globalPriority", locale) || "Global Priority"), icon: MapPin },
                                        { label: t("onboarding.targetRole", locale) || "Target Role", value: preferences.role_type || (t("onboarding.seniorImpactRole", locale) || "Senior Impact Role"), icon: Briefcase },
                                    ].map((item, i) => (
                                        <motion.div
                                            key={item.label}
                                            initial={shouldReduceMotion ? undefined : { opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.5 + i * 0.15 }}
                                            className="flex items-start justify-between group"
                                        >
                                            <div>
                                                <p className="text-[8px] md:text-[10px] font-black text-white/20 uppercase tracking-[0.2em] mb-1">
                                                    {item.label}
                                                </p>
                                                <p className="font-black text-sm md:text-xl text-white group-hover:text-primary-400 transition-colors uppercase">
                                                    {item.value}
                                                </p>
                                                {item.sub && (
                                                    <p className="text-[10px] md:text-xs text-white/30 font-medium mt-1 truncate">
                                                        {item.sub}
                                                    </p>
                                                )}
                                            </div>
                                            <item.icon className="h-4 w-4 md:h-6 md:w-6 text-white/5 group-hover:text-primary-500 transition-all" aria-hidden />
                                        </motion.div>
                                    ))}
                                </div>
                                <div className="mt-8 md:mt-12 pt-6 md:pt-10 border-t border-white/5 grid grid-cols-2 gap-4 md:gap-8">
                                    <div className="p-4 md:p-6 rounded-2xl bg-primary-500/10 border border-primary-500/20">
                                        <p className="text-[9px] md:text-[10px] uppercase font-black text-primary-500/70 mb-1 tracking-widest">
                                            {t("onboarding.strategyStrength", locale) || "Strategy Strength"}
                                        </p>
                                        <p className="text-2xl md:text-3xl font-black text-primary-400 italic">{completeness}%</p>
                                    </div>
                                    <div className="p-4 md:p-6 rounded-2xl bg-primary-500/10 border border-primary-500/20">
                                        <p className="text-[9px] md:text-[10px] uppercase font-black text-primary-500/70 mb-1 tracking-widest">
                                            {t("onboarding.profilePoints", locale) || "Profile Points"}
                                        </p>
                                        <p className="text-2xl md:text-3xl font-black text-primary-400 italic">
                                            {profilePoints}/6
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
                    onClick={handleLaunch}
                    className="w-full h-14 md:h-20 rounded-[1.5rem] md:rounded-[3rem] text-lg md:text-3xl font-black shadow-2xl shadow-primary-600/30 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-500 hover:to-purple-500 hover:scale-[1.02] active:scale-95 transition-all group overflow-hidden relative"
                    disabled={isCompleting || countdown !== null}
                    aria-label="Start My Hunt"
                    data-onboarding-next
                >
                    <span className="relative z-10 flex items-center justify-center gap-2 md:gap-4">
                        {isCompleting ? <LoadingSpinner size="sm" /> : (
                            <>
                                <Sparkles className="h-5 w-5 md:h-8 md:w-8" aria-hidden />
                                {t("onboarding.startMyHunt", locale) || "Start My Hunt"}
                                <Rocket className="h-6 w-6 md:h-10 md:w-10 group-hover:translate-x-2 group-hover:-translate-y-2 transition-transform" aria-hidden />
                            </>
                        )}
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
                </Button>

                {/* Scanning message during launch */}
                <AnimatePresence>
                    {isLaunching && (
                        <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-center text-sm font-bold text-primary-600 mt-4"
                        >
                            <Sparkles className="inline w-4 h-4 mr-1" />
                            {t("onboarding.scanningJobs", locale) || "Scanning 10,000+ jobs for your perfect match\u2026"}
                        </motion.p>
                    )}
                </AnimatePresence>

                <div className="mt-4 md:mt-10 flex justify-center">
                    <button
                        onClick={handleShareArchetype}
                        className="text-[10px] md:text-xs font-bold text-primary-600 hover:text-primary-700 underline decoration-dotted underline-offset-4 flex items-center gap-1 opacity-80 hover:opacity-100 transition-opacity"
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
