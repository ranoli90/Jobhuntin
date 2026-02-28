import * as React from "react";
import { motion } from "framer-motion";
import { Rocket, Sparkles, MapPin, ArrowRight } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { t, getLocale } from "../../../../lib/i18n";

interface WelcomeStepProps {
    onNext: () => void;
    shouldReduceMotion?: boolean;
}

export function WelcomeStep({ onNext, shouldReduceMotion }: WelcomeStepProps) {
    return (
        <div>
            <div className="text-center py-2 md:py-4">
                <div className="mx-auto mb-4 md:mb-6 relative">
                    <motion.div
                        animate={shouldReduceMotion ? undefined : { rotate: 360 }}
                        transition={shouldReduceMotion ? undefined : { duration: 20, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 rounded-2xl border-2 border-dashed border-primary-500/20 hidden md:block"
                    />
                    <div className="relative mx-auto flex h-14 w-14 md:h-20 md:w-20 items-center justify-center rounded-2xl md:rounded-3xl bg-slate-900 shadow-2xl shadow-primary-500/20">
                        <Rocket className="h-7 w-7 md:h-10 md:w-10 text-primary-400" />
                    </div>
                </div>
                <h1 className="mb-2 md:mb-3 font-display text-xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
                    Find Your <span className="text-primary-600 italic">Dream Job.</span>
                </h1>
                <p className="mb-4 md:mb-8 text-slate-500 font-medium leading-relaxed max-w-sm mx-auto text-sm md:text-base">
                    {t("onboarding.welcomeSubtitle", getLocale())}
                </p>
                <div className="grid gap-2 md:gap-3 mb-6 md:mb-8 text-left">
                    {[
                        { title: "Upload Resume", desc: "We'll analyze your skills and experience", icon: Sparkles },
                        { title: "Set Preferences", desc: "Tell us where and what you want to work", icon: MapPin },
                        { title: "Auto-Apply", desc: "We'll apply to jobs for you automatically", icon: Rocket },
                    ].map((item, i) => (
                        <motion.div
                            key={i}
                            initial={shouldReduceMotion ? undefined : { opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={shouldReduceMotion ? undefined : { delay: 0.2 + i * 0.1 }}
                            className="flex items-center gap-3 md:gap-4 p-3 md:p-4 rounded-xl bg-slate-50 border border-slate-100 hover:bg-white hover:shadow-sm transition-all group"
                        >
                            <div className="flex h-9 w-9 md:h-10 md:w-10 shrink-0 items-center justify-center rounded-xl bg-primary-100 text-primary-600 group-hover:bg-primary-600 group-hover:text-white transition-colors">
                                <item.icon className="h-4 w-4 md:h-5 md:w-5" />
                            </div>
                            <div className="text-left min-w-0">
                                <p className="text-xs md:text-sm font-bold text-slate-900 uppercase tracking-tight">{item.title}</p>
                                <p className="text-[10px] md:text-xs text-slate-500 font-medium">{item.desc}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            <Button type="button" onClick={onNext} className="w-full h-11 md:h-12 rounded-xl font-bold text-base md:text-lg shadow-lg shadow-primary-500/20 bg-primary-600 hover:bg-primary-500 group" aria-label={t("onboarding.startSetup", getLocale())} data-onboarding-next>
                {t("onboarding.startSetup", getLocale())}
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Button>
        </div>
    );
}
