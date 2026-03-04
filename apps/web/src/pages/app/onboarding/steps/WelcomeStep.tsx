import * as React from "react";
import { motion } from "framer-motion";
import { Rocket, MapPin, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { t, getLocale } from "../../../../lib/i18n";

interface WelcomeStepProps {
    onNext: () => void;
    shouldReduceMotion?: boolean;
    firstName?: string;
}

export function WelcomeStep({ onNext, shouldReduceMotion, firstName }: WelcomeStepProps) {
    const locale = getLocale();

    const features = [
        {
            titleKey: "onboarding.feature1Title",
            descKey: "onboarding.feature1Desc",
            icon: Sparkles
        },
        {
            titleKey: "onboarding.feature2Title",
            descKey: "onboarding.feature2Desc",
            icon: MapPin
        },
        {
            titleKey: "onboarding.feature3Title",
            descKey: "onboarding.feature3Desc",
            icon: Rocket
        },
    ];

    const welcomeTitle = t("onboarding.welcomeTitle", locale);
    const titleWords = welcomeTitle.split(" ");
    const titleStart = titleWords.slice(0, -1).join(" ");
    const titleEnd = titleWords.pop()?.replace(".", "") || "";

    const personalGreeting = firstName
        ? `Hey ${firstName} 👋`
        : null;

    return (
        <div>
            <div className="text-center py-2 md:py-4">
                <div className="mx-auto mb-4 md:mb-6 relative font-display">
                    <motion.div
                        animate={shouldReduceMotion ? undefined : { rotate: 360 }}
                        transition={shouldReduceMotion ? undefined : { duration: 20, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 rounded-2xl border-2 border-dashed border-indigo-500/20 hidden md:block"
                    />
                    <div className="relative mx-auto flex h-14 w-14 md:h-20 md:w-20 items-center justify-center rounded-[1.25rem] md:rounded-[2rem] bg-indigo-600 shadow-2xl shadow-indigo-500/40">
                        <Rocket className="h-7 w-7 md:h-10 md:w-10 text-white" />
                    </div>
                </div>

                {personalGreeting && (
                    <motion.p
                        initial={shouldReduceMotion ? undefined : { opacity: 0, y: -8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="mb-1 text-sm font-black text-indigo-600 uppercase tracking-widest"
                    >
                        {personalGreeting}
                    </motion.p>
                )}

                <h1 className="mb-2 md:mb-3 font-display text-2xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight">
                    {titleStart}{" "}
                    <span className="text-indigo-600 italic">
                        {titleEnd}.
                    </span>
                </h1>
                <p className="mb-4 md:mb-8 text-slate-500 font-bold leading-relaxed max-w-sm mx-auto text-sm md:text-lg">
                    {t("onboarding.welcomeSubtitle", locale)}
                </p>
                <div className="grid gap-2 md:gap-3 mb-6 md:mb-10 text-left">
                    {features.map((item, i) => (
                        <motion.div
                            key={i}
                            initial={shouldReduceMotion ? undefined : { opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={shouldReduceMotion ? undefined : { delay: 0.2 + i * 0.1 }}
                            className="flex items-center gap-3 md:gap-4 p-4 md:p-5 rounded-2xl bg-white border border-slate-100 hover:border-indigo-100 hover:shadow-xl hover:shadow-indigo-500/5 transition-all group"
                        >
                            <div className="flex h-10 w-10 md:h-12 md:w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                                <item.icon className="h-5 w-5 md:h-6 md:w-6" />
                            </div>
                            <div className="text-left min-w-0">
                                <p className="text-xs md:text-sm font-black text-slate-900 uppercase tracking-wider">
                                    {t(item.titleKey, locale)}
                                </p>
                                <p className="text-[10px] md:text-xs text-slate-500 font-bold leading-snug mt-0.5">
                                    {t(item.descKey, locale)}
                                </p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            <Button
                type="button"
                onClick={onNext}
                className="w-full h-14 md:h-16 rounded-[1.25rem] md:rounded-[2rem] font-black text-lg md:text-xl shadow-xl shadow-indigo-600/20 bg-indigo-600 hover:bg-indigo-500 group overflow-hidden relative"
                aria-label={t("onboarding.startSetup", locale)}
                data-onboarding-next
            >
                <span className="relative z-10 flex items-center gap-2">
                    {t("onboarding.startSetup", locale)}
                    <ArrowRight className="ml-2 h-6 w-6 group-hover:translate-x-2 transition-transform" />
                </span>
                <motion.div
                    animate={shouldReduceMotion ? undefined : { x: ['-100%', '200%'] }}
                    transition={shouldReduceMotion ? undefined : { duration: 2, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-20"
                />
            </Button>
        </div>
    );
}
