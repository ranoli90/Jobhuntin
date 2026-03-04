import * as React from "react";
import { motion } from "framer-motion";
import { Rocket, MapPin, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { t, getLocale } from "../../../../lib/i18n";
import { cn } from "../../../../lib/utils";

interface WelcomeStepProps {
    onNext: () => void;
    shouldReduceMotion?: boolean;
    firstName?: string;
}

export function WelcomeStep({ onNext, shouldReduceMotion, firstName }: WelcomeStepProps) {
    const locale = getLocale();

    const features = [
        { titleKey: "onboarding.feature1Title", descKey: "onboarding.feature1Desc", icon: Sparkles },
        { titleKey: "onboarding.feature2Title", descKey: "onboarding.feature2Desc", icon: MapPin },
        { titleKey: "onboarding.feature3Title", descKey: "onboarding.feature3Desc", icon: Rocket },
    ];

    const welcomeTitle = t("onboarding.welcomeTitle", locale);
    const titleWords = welcomeTitle.split(" ");
    const titleStart = titleWords.slice(0, -1).join(" ");
    const titleEnd = titleWords.pop()?.replace(".", "") || "";

    const personalGreeting = firstName ? `Hey ${firstName} 👋` : null;

    return (
        <div>
            <div className="text-center py-4">
                {/* Animated Icon */}
                <div className="mx-auto mb-6 relative font-display">
                    <motion.div
                        animate={shouldReduceMotion ? undefined : { rotate: 360 }}
                        transition={shouldReduceMotion ? undefined : { duration: 20, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 rounded-2xl border-2 border-dashed border-primary-500/20"
                    />
                    <div className={cn(
                        "relative mx-auto flex h-20 w-20 items-center justify-center",
                        "rounded-[2rem] bg-primary-600 shadow-2xl shadow-primary-500/40"
                    )}>
                        <Rocket className="h-10 w-10 text-white" />
                    </div>
                </div>

                {/* Personal Greeting */}
                {personalGreeting && (
                    <motion.p
                        initial={shouldReduceMotion ? undefined : { opacity: 0, y: -8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="mb-1 text-sm font-black text-primary-600 uppercase tracking-widest"
                    >
                        {personalGreeting}
                    </motion.p>
                )}

                {/* Title */}
                <h1 className="mb-3 font-display text-4xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight">
                    {titleStart}{" "}
                    <span className="text-primary-600 italic">{titleEnd}.</span>
                </h1>

                {/* Subtitle */}
                <p className={cn(
                    "mb-8 text-slate-500 font-bold leading-relaxed max-w-sm mx-auto",
                    "text-base md:text-lg"
                )}>
                    {t("onboarding.welcomeSubtitle", locale)}
                </p>

                {/* Feature Cards */}
                <div className="grid gap-3 mb-10 text-left">
                    {features.map((item, i) => (
                        <motion.div
                            key={i}
                            initial={shouldReduceMotion ? undefined : { opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={shouldReduceMotion ? undefined : { delay: 0.2 + i * 0.1 }}
                            className={cn(
                                "flex items-center gap-4 p-5 rounded-2xl",
                                "bg-white border border-slate-100",
                                "hover:border-primary-100 hover:shadow-xl hover:shadow-primary-500/5",
                                "transition-all group"
                            )}
                        >
                            <div className={cn(
                                "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl",
                                "bg-primary-50 text-primary-600",
                                "group-hover:bg-primary-600 group-hover:text-white",
                                "transition-all"
                            )}>
                                <item.icon className="h-6 w-6" />
                            </div>
                            <div className="text-left min-w-0">
                                <p className="text-sm font-black text-slate-900 uppercase tracking-wider">
                                    {t(item.titleKey, locale)}
                                </p>
                                <p className="text-xs text-slate-500 font-bold leading-snug mt-0.5">
                                    {t(item.descKey, locale)}
                                </p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Start Button */}
            <Button
                type="button"
                onClick={onNext}
                className={cn(
                    "w-full h-16 rounded-[2rem] font-black text-xl",
                    "shadow-xl shadow-primary-600/20",
                    "bg-primary-600 hover:bg-primary-500",
                    "group overflow-hidden relative"
                )}
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
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12"
                />
            </Button>
        </div>
    );
}
