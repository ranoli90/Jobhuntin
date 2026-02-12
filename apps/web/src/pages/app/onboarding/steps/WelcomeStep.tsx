import * as React from "react";
import { motion } from "framer-motion";
import { Rocket, Sparkles, MapPin, ArrowRight } from "lucide-react";
import { Button } from "../../../../components/ui/Button";

interface WelcomeStepProps {
    onNext: () => void;
    shouldReduceMotion?: boolean;
}

export function WelcomeStep({ onNext, shouldReduceMotion }: WelcomeStepProps) {
    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                <div className="text-center py-1 md:py-4">
                    <div className="mx-auto mb-3 md:mb-6 relative">
                        <motion.div
                            animate={shouldReduceMotion ? undefined : { rotate: 360 }}
                            transition={shouldReduceMotion ? undefined : { duration: 20, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-0 rounded-[2rem] border-2 border-dashed border-primary-500/20 hidden md:block"
                        />
                        <div className="relative mx-auto flex h-12 w-12 md:h-20 md:w-20 items-center justify-center rounded-[1.5rem] md:rounded-[2rem] bg-slate-900 shadow-2xl shadow-primary-500/20 scale-100">
                            <Rocket className="h-6 w-6 md:h-10 md:w-10 text-primary-400" />
                        </div>
                    </div>
                    <h1 className="mb-1 md:mb-3 font-display text-xl md:text-3xl font-black text-slate-900 tracking-tight leading-tight">
                        Initiate <span className="text-primary-600 italic">Hyper-Hunt.</span>
                    </h1>
                    <p className="mb-3 md:mb-8 text-slate-500 font-medium leading-relaxed max-w-sm mx-auto text-xs md:text-base">
                        We're about to build your digital autonomous twin. Calibration takes 90 seconds.
                    </p>
                    <div className="grid gap-1.5 md:gap-3 mb-3 md:mb-8 text-left">
                        {[
                            { title: "Skill Mapping", desc: "AI-driven resume vectorization", icon: Sparkles },
                            { title: "Radar Tuning", desc: "Location & salary baseline profiling", icon: MapPin },
                            { title: "Autonomous Launch", desc: "1-Click application engine activation", icon: Rocket },
                        ].map((item, i) => (
                            <motion.div
                                key={i}
                                initial={shouldReduceMotion ? undefined : { opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={shouldReduceMotion ? undefined : { delay: 0.2 + i * 0.1 }}
                                className="flex items-center gap-2.5 md:gap-4 p-2 md:p-4 rounded-xl md:rounded-2xl bg-slate-50 border border-slate-100/50 hover:bg-white hover:shadow-md transition-all group"
                            >
                                <div className="flex h-7 w-7 md:h-10 md:w-10 shrink-0 items-center justify-center rounded-lg md:rounded-xl bg-primary-100 text-primary-600 group-hover:bg-primary-600 group-hover:text-white transition-colors">
                                    <item.icon className="h-3.5 w-3.5 md:h-5 md:w-5" />
                                </div>
                                <div className="text-left min-w-0">
                                    <p className="text-[11px] md:text-sm font-black text-slate-900 uppercase tracking-tight truncate">{item.title}</p>
                                    <p className="text-[9px] md:text-xs text-slate-500 font-medium truncate">{item.desc}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </div>
            <div className="sticky bottom-0 pt-2 md:pt-4 shrink-0 mt-auto bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button size="lg" onClick={onNext} className="w-full h-10 md:h-12 rounded-[1.25rem] text-base md:text-xl font-black shadow-xl md:shadow-2xl shadow-primary-500/30 bg-primary-600 hover:bg-primary-500 hover:scale-[1.02] transition-all group" aria-label="Begin Calibration">
                    BEGIN CALIBRATION
                    <ArrowRight className="ml-3 h-5 w-5 md:h-6 md:w-6 group-hover:translate-x-1 transition-transform" />
                </Button>
            </div>
        </div>
    );
}
