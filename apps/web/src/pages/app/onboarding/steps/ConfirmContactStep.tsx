import * as React from "react";
import { User, Mail, Phone, Sparkles, ArrowLeft, HelpCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { formatPhoneNumber } from "../../../../lib/phoneUtils";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { ParsedResume } from "../../../../types/onboarding";

interface ConfirmContactStepProps {
    onNext: () => void;
    onPrev: () => void;
    contactInfo: {
        first_name: string;
        last_name: string;
        email: string;
        phone: string;
    };
    setContactInfo: React.Dispatch<React.SetStateAction<{
        first_name: string;
        last_name: string;
        email: string;
        phone: string;
    }>>;
    isSavingContact: boolean;
    parsedResume: ParsedResume | null;
    formErrors: Record<string, string>;
    emailTypoSuggestion?: string | null;
    onApplyEmailSuggestion?: (suggestion: string) => void;
}

export function ConfirmContactStep({
    onNext,
    onPrev,
    contactInfo,
    setContactInfo,
    isSavingContact,
    parsedResume,
    formErrors,
    emailTypoSuggestion,
    onApplyEmailSuggestion,
}: ConfirmContactStepProps) {
    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                <div className="mb-3 md:mb-8 flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6">
                    <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-emerald-50 border border-emerald-100 text-emerald-600 shadow-inner">
                        <User className="h-4 w-4 md:h-8 md:w-8" />
                    </div>
                    <div className="min-w-0">
                        <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">Verify Identity</h2>
                        <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">Confirm the details we extracted.</p>
                    </div>
                </div>

                <div className="grid gap-3 md:gap-6">
                    <div className="grid grid-cols-2 gap-2.5 md:gap-6">
                        <div>
                            <label className="mb-2 md:mb-3 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                                <div className="w-1 h-1 rounded-full bg-emerald-500" />
                                First Name <span className="text-red-400">*</span>
                            </label>
                            <div className="relative">
                                <Input
                                    icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                                    type="text"
                                    placeholder="John"
                                    value={contactInfo.first_name}
                                    onChange={(e) => setContactInfo(c => ({ ...c, first_name: e.target.value }))}
                                    onClear={() => setContactInfo(c => ({ ...c, first_name: "" }))}
                                    className="bg-white shadow-sm text-sm"
                                    error={!!formErrors.first_name}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="mb-2 md:mb-3 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                                <div className="w-1 h-1 rounded-full bg-emerald-500" />
                                Last Name <span className="text-red-400">*</span>
                            </label>
                            <div className="relative">
                                <Input
                                    icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                                    type="text"
                                    placeholder="Doe"
                                    value={contactInfo.last_name}
                                    onChange={(e) => setContactInfo(c => ({ ...c, last_name: e.target.value }))}
                                    onClear={() => setContactInfo(c => ({ ...c, last_name: "" }))}
                                    className="bg-white shadow-sm text-sm"
                                    error={!!formErrors.last_name}
                                />
                            </div>
                        </div>
                    </div>

                    <div>
                        <label className="mb-2 md:mb-3 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                            <div className="w-1 h-1 rounded-full bg-emerald-500" />
                            Email Address <span className="text-red-400">*</span>
                        </label>
                        <div className="relative">
                            <Input
                                icon={<Mail className="h-4 w-4 md:h-5 md:w-5" />}
                                type="email"
                                placeholder="john@example.com"
                                value={contactInfo.email}
                                onChange={(e) => setContactInfo(c => ({ ...c, email: e.target.value }))}
                                onClear={() => setContactInfo(c => ({ ...c, email: "" }))}
                                className="bg-white shadow-sm text-sm"
                                error={!!formErrors.email}
                            />
                        </div>
                        <p className="mt-1 text-[9px] text-slate-400 font-medium">We hate spam. You can unsubscribe anytime.</p>
                        <AnimatePresence>
                            {emailTypoSuggestion && onApplyEmailSuggestion && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="mt-2"
                                >
                                    <button
                                        type="button"
                                        onClick={() => onApplyEmailSuggestion(emailTypoSuggestion)}
                                        className="text-[10px] md:text-xs font-bold text-primary-600 hover:text-primary-700 underline decoration-dotted underline-offset-4"
                                    >
                                        Did you mean <span className="italic">{contactInfo.email.split('@')[0]}@{emailTypoSuggestion}</span>?
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    <div>
                        <label className="mb-2 md:mb-3 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] group relative w-fit">
                            <div className="w-1 h-1 rounded-full bg-emerald-500" />
                            Phone Number
                            <HelpCircle className="w-3 h-3 text-slate-300 cursor-help" />
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-slate-800 text-white text-[10px] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 font-medium normal-case tracking-normal">
                                Used for 2FA and recruiter contact only.
                            </div>
                        </label>
                        <div className="relative">
                            <Input
                                icon={<Phone className="h-4 w-4 md:h-5 md:w-5" />}
                                type="tel"
                                placeholder="+1 (555) 123-4567"
                                value={contactInfo.phone}
                                onChange={(e) => {
                                    const formatted = formatPhoneNumber(e.target.value);
                                    setContactInfo(c => ({ ...c, phone: formatted }));
                                }}
                                onClear={() => setContactInfo(c => ({ ...c, phone: "" }))}
                                className="bg-white shadow-sm text-sm"
                            />
                        </div>
                    </div>
                </div>

                {parsedResume && (
                    <div className="mt-3 md:mt-8 p-2.5 md:p-5 rounded-xl md:rounded-2xl bg-emerald-50 border border-emerald-100">
                        <div className="flex items-center gap-2 mb-1 md:mb-2">
                            <Sparkles className="h-3 w-3 md:h-4 md:w-4 text-emerald-600" />
                            <p className="text-[7px] md:text-[10px] font-black text-emerald-700 uppercase tracking-widest">AI-Extracted From Resume</p>
                        </div>
                        <p className="text-[10px] md:text-sm text-emerald-800 font-medium">We pre-filled these from your resume. Please verify details.</p>
                    </div>
                )}
            </div>

            <div className="flex gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button variant="ghost" onClick={onPrev} className="h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4" aria-label="Go to previous step">
                    <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                    PREV
                </Button>
                <Button
                    onClick={onNext}
                    disabled={!contactInfo.first_name || !contactInfo.email || isSavingContact}
                    className="flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black bg-emerald-600 hover:bg-emerald-500 shadow-2xl shadow-emerald-500/30 text-xs md:text-lg disabled:opacity-50 disabled:cursor-not-allowed group"
                    aria-label="Confirm identity and proceed"
                >
                    {isSavingContact ? <LoadingSpinner size="sm" /> : "CONFIRM IDENTITY"}
                </Button>
            </div>
        </div>
    );
}
