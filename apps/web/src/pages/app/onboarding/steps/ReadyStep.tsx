import * as React from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Rocket, User, MapPin, Briefcase } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Card } from "../../../../components/ui/Card";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";

interface ReadyStepProps {
    onNext: () => void;
    isCompleting: boolean;
    contactInfo: any;
    preferences: any;
    completeness: number;
    profile: any;
    resumeFile: any;
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
    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                <div className="text-center py-2 md:py-6">
                    <div className="mx-auto mb-3 md:mb-10 relative">
                        <motion.div
                            initial={shouldReduceMotion ? { scale: 1 } : { scale: 0 }}
                            animate={shouldReduceMotion ? undefined : { scale: [1, 1.2, 1] }}
                            transition={shouldReduceMotion ? undefined : { duration: 0.5, times: [0, 0.5, 1] }}
                            className="absolute inset-0 bg-emerald-500/20 rounded-full blur-2xl"
                        />
                        <div className="relative mx-auto flex h-14 w-14 md:h-28 md:w-28 items-center justify-center rounded-[1.5rem] md:rounded-[3rem] bg-emerald-500 shadow-2xl shadow-emerald-200">
                            <CheckCircle2 className="h-7 w-7 md:h-12 md:w-16 text-white" />
                        </div>
                    </div>

                    <h1 className="mb-1 md:mb-4 font-display text-2xl md:text-5xl font-black text-slate-900 tracking-tight">
                        System <span className="text-emerald-500 italic">Online.</span>
                    </h1>
                    <p className="mb-4 md:mb-12 text-slate-500 font-medium max-w-sm mx-auto text-sm md:text-lg leading-relaxed">
                        Calibration successful. Your digital twin is initialized.
                    </p>

                    {/* Preferences Summary Table */}
                    <div className="mb-4 md:mb-12 relative">
                        <div className="absolute -inset-4 bg-gradient-to-b from-slate-900/5 to-transparent rounded-[3rem] -z-10 hidden md:block" />
                        <Card className="bg-slate-950 text-white p-3 md:p-8 rounded-[1.25rem] md:rounded-[2.5rem] shadow-2xl text-left relative overflow-hidden border-white/5 border-t-white/10">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 rounded-full blur-[80px]" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-4 md:mb-8 border-b border-white/5 pb-2 md:pb-4">
                                    <div className="w-6 h-6 md:w-8 md:h-8 rounded-lg bg-primary-500/20 flex items-center justify-center text-primary-400">
                                        <Rocket className="h-3 w-3 md:h-4 md:w-4" />
                                    </div>
                                    <h3 className="font-black text-white/50 text-[8px] md:text-[10px] uppercase tracking-[0.3em]">Operational Directives</h3>
                                </div>
                                <div className="space-y-4 md:space-y-6">
                                    <div className="flex items-start justify-between group">
                                        <div>
                                            <p className="text-[8px] md:text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">CONFIRMED IDENTITY</p>
                                            <p className="font-black text-sm md:text-lg text-white group-hover:text-emerald-400 transition-colors uppercase">{contactInfo.first_name} {contactInfo.last_name}</p>
                                            <p className="text-[10px] md:text-xs text-white/40 font-medium mt-0.5 max-w-[150px] truncate">{contactInfo.email}</p>
                                        </div>
                                        <User className="h-4 w-4 md:h-5 md:w-5 text-white/10 group-hover:text-emerald-500 transition-colors" />
                                    </div>
                                    <div className="flex items-start justify-between group">
                                        <div>
                                            <p className="text-[8px] md:text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">AOI GEOLOCATION</p>
                                            <p className="font-black text-sm md:text-lg text-white group-hover:text-primary-400 transition-colors uppercase">{preferences.location || "Global Priority"}</p>
                                        </div>
                                        <MapPin className="h-4 w-4 md:h-5 md:w-5 text-white/10 group-hover:text-primary-500 transition-colors" />
                                    </div>
                                    <div className="flex items-start justify-between group">
                                        <div>
                                            <p className="text-[8px] md:text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">TARGET CLASSIFICATION</p>
                                            <p className="font-black text-sm md:text-lg text-white group-hover:text-primary-400 transition-colors uppercase">{preferences.role_type || "Senior Impact Role"}</p>
                                        </div>
                                        <Briefcase className="h-4 w-4 md:h-5 md:w-5 text-white/10 group-hover:text-primary-500 transition-colors" />
                                    </div>
                                </div>
                                <div className="mt-6 md:mt-10 pt-4 md:pt-8 border-t border-white/5 grid grid-cols-2 gap-3 md:gap-6">
                                    <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-emerald-500/10 border border-emerald-500/20 group">
                                        <p className="text-[8px] md:text-[9px] uppercase font-black text-emerald-500/70 mb-1 tracking-widest">Match Strength</p>
                                        <p className="text-xl md:text-2xl font-black text-emerald-400 italic">{completeness}%</p>
                                    </div>
                                    <div className="p-3 md:p-4 rounded-xl md:rounded-2xl bg-primary-500/10 border border-primary-500/20 group">
                                        <p className="text-[8px] md:text-[9px] uppercase font-black text-primary-500/70 mb-1 tracking-widest">Data Points</p>
                                        <p className="text-xl md:text-2xl font-black text-primary-400 italic">{[contactInfo.first_name, contactInfo.email, preferences.location, preferences.role_type, preferences.salary_min, (profile?.resume_url || resumeFile)].filter(Boolean).length}/6</p>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </div>
                </div>
            </div>

            <div className="pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button size="lg" variant="primary" onClick={onNext} className="w-full h-10 md:h-16 rounded-[1.25rem] md:rounded-[2rem] text-base md:text-2xl font-black shadow-[0_20px_50px_-12px_rgba(59,130,246,0.5)] bg-primary-600 hover:bg-primary-500 hover:scale-[1.03] active:scale-95 transition-all group overflow-hidden relative" disabled={isCompleting} aria-label="Finalize setup and launch command center">
                    <span className="relative z-10 flex items-center justify-center gap-2 md:gap-4">
                        {isCompleting ? <LoadingSpinner size="sm" /> : "LAUNCH COMMAND CENTER"}
                        <Rocket className="h-5 w-5 md:h-8 md:w-8 group-hover:translate-x-2 group-hover:-translate-y-2 transition-transform" />
                    </span>
                    <motion.div
                        animate={shouldReduceMotion ? undefined : { x: ['-100%', '200%'] }}
                        transition={shouldReduceMotion ? undefined : { duration: 1.5, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-12"
                    />
                </Button>
                <p className="mt-2 md:mt-8 text-[8px] md:text-[10px] text-slate-400 font-black uppercase tracking-[0.4em] hidden md:block">Full system authority granted.</p>

                <div className="mt-4 md:mt-8 flex justify-center">
                    <button
                        onClick={() => {
                            const archetype = preferences.role_type || "Visionary";
                            const text = `I just calibrated my AI job hunter as a ${archetype}. Expected interview velocity: 300%. #JobHuntin`;
                            navigator.clipboard.writeText(text);
                            // Assuming pushToast is available or just alert, but ReadyStep doesn't seem to import pushToast.
                            // I'll leave it as a simple copy for now or simpler:
                            alert("Archetype link copied to clipboard!");
                        }}
                        className="text-[10px] md:text-xs font-bold text-primary-600 hover:text-primary-700 underline decoration-dotted underline-offset-4 flex items-center gap-1 opacity-80 hover:opacity-100 transition-opacity"
                    >
                        <User className="w-3 h-3" />
                        SHARE YOUR ARCHETYPE
                    </button>
                    <div className="w-[1px] h-3 bg-slate-300 mx-3 opacity-50"></div>
                    <button
                        onClick={() => {
                            // Mock referral
                            alert(" referral invite sent to your clipboard!");
                            navigator.clipboard.writeText("Join me on JobHuntin and let AI apply for you! https://jobhuntin.com/invite/friend");
                        }}
                        className="text-[10px] md:text-xs font-bold text-slate-400 hover:text-slate-600 underline decoration-dotted underline-offset-4 transition-colors"
                    >
                        REFER A FRIEND
                    </button>
                </div>
            </div>
        </div>
    );
}
