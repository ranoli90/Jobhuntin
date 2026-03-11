import * as React from "react";
import { User, Mail, Phone, UserCheck, ArrowLeft } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { formatPhoneNumber, isValidPhoneNumber } from "../../../../lib/phoneUtils";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { ParsedResume } from "../../../../types/onboarding";
import { t, getLocale } from "../../../../lib/i18n";
import { isValidEmail } from "../../../../lib/emailUtils";

interface ConfirmContactStepProps {
    /** E3: May be sync or async; caller should await if async. Advances to next step when contact is saved. */
    onNext: () => void | Promise<void>;
    /** E3: Sync; navigates to previous step. */
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
    onClearError?: (field: string) => void;
    onSetFormError?: (field: string, error: string) => void;
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
    onClearError,
    onSetFormError,
}: ConfirmContactStepProps) {
    const locale = getLocale();

    const handleFieldChange = (field: string, value: string) => {
        setContactInfo(c => ({ ...c, [field]: value }));
        // Clear error when user starts typing
        if (formErrors[field] && onClearError) {
            onClearError(field);
        }
    };

    const handlePhoneChange = (value: string) => {
        const formatted = formatPhoneNumber(value);
        setContactInfo(c => ({ ...c, phone: formatted }));

        // Clear error when user starts typing
        if (formErrors.phone && onClearError) {
            onClearError('phone');
        }

        // Validate phone number if provided
        if (formatted && !isValidPhoneNumber(formatted) && onSetFormError) {
            onSetFormError('phone', t("onboarding.phoneInvalid", locale) || 'Please enter a valid phone number');
        } else if (onClearError) {
            onClearError('phone');
        }
    };

    return (
        <div role="region" aria-labelledby="confirm-contact-step-title">
            {/* Screen reader error announcement */}
            {Object.keys(formErrors).length > 0 && (
                <div role="alert" aria-live="polite" className="sr-only">
                    {t("onboarding.formErrors", locale) || "Form has"} {Object.keys(formErrors).length} {Object.keys(formErrors).length > 1 ? t("onboarding.errorsPlural", locale) || 'errors' : t("onboarding.errorsSingular", locale) || 'error'}:
                    {Object.entries(formErrors).map(([field, msg]) => `${field}: ${msg}`).join(', ')}
                </div>
            )}

            <div className="mb-4 md:mb-6 flex items-center gap-3 md:gap-4 border-b border-[#E9E9E7] pb-4 md:pb-6">
                <div className="flex h-10 w-12 md:h-12 md:w-14 shrink-0 items-center justify-center rounded-xl md:rounded-2xl bg-[#17BEBB]/10 border border-[#17BEBB]/20 text-[#17BEBB] shadow-sm">
                    <User className="h-5 w-5 md:h-6 md:w-6" />
                </div>
                <div className="min-w-0">
                    <h2 id="confirm-contact-step-title" className="font-display text-lg md:text-2xl font-bold text-[#2D2A26] tracking-tight">
                        {t("onboarding.contactTitle", locale)}
                    </h2>
                    <p className="text-xs md:text-sm text-[#787774] font-medium">
                        {t("onboarding.contactSubtitle", locale)}
                    </p>
                </div>
            </div>

            <div className="grid gap-4 md:gap-6">
                <div className="grid grid-cols-2 gap-3 md:gap-4">
                    <div>
                        <label htmlFor="onboarding-first-name" className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            <div className="w-1 h-1 rounded-full bg-[#17BEBB]" />
                            {t("onboarding.firstName", locale)} <span className="text-red-400">*</span>
                        </label>
                        <Input
                            id="onboarding-first-name"
                            icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                            type="text"
                            placeholder={t("onboarding.firstNamePlaceholder", locale) || "John"}
                            value={contactInfo.first_name}
                            onChange={(e) => handleFieldChange('first_name', e.target.value)}
                            onClear={() => setContactInfo(c => ({ ...c, first_name: "" }))}
                            className="bg-white shadow-sm"
                            error={!!formErrors.first_name}
                        />
                    </div>
                    <div>
                        <label htmlFor="onboarding-last-name" className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            <div className="w-1 h-1 rounded-full bg-[#17BEBB]" />
                            {t("onboarding.lastName", locale)} <span className="text-red-400">*</span>
                        </label>
                        <Input
                            id="onboarding-last-name"
                            icon={<User className="h-4 w-4 md:h-5 md:w-5" />}
                            type="text"
                            placeholder={t("onboarding.lastNamePlaceholder", locale) || "Doe"}
                            value={contactInfo.last_name}
                            onChange={(e) => handleFieldChange('last_name', e.target.value)}
                            onClear={() => setContactInfo(c => ({ ...c, last_name: "" }))}
                            className="bg-white shadow-sm"
                            error={!!formErrors.last_name}
                        />
                    </div>
                </div>

                <div>
                    <label htmlFor="onboarding-email" className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        <div className="w-1 h-1 rounded-full bg-emerald-500" />
                        {t("onboarding.email", locale)} <span className="text-red-400">*</span>
                    </label>
                    <Input
                        id="onboarding-email"
                        icon={<Mail className="h-4 w-4 md:h-5 md:w-5" />}
                        type="email"
                        inputMode="email"
                        autoComplete="email"
                        placeholder={t("onboarding.emailPlaceholder", locale) || "john@example.com"}
                        value={contactInfo.email}
                        onChange={(e) => handleFieldChange('email', e.target.value)}
                        onClear={() => setContactInfo(c => ({ ...c, email: "" }))}
                        className="bg-white shadow-sm"
                        error={!!formErrors.email}
                    />
                    <p className="mt-1 text-[10px] text-slate-400">{t("onboarding.emailPrivacy", locale) || "We hate spam. You can unsubscribe anytime."}</p>
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
                                    className="text-xs font-bold text-primary-600 hover:text-primary-700 underline"
                                >
                                    {t("onboarding.didYouMean", locale)} <span className="italic">{(contactInfo.email ?? "").split('@')[0]}@{emailTypoSuggestion}</span>?
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                <div>
                    <label htmlFor="onboarding-phone" className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        <div className="w-1 h-1 rounded-full bg-emerald-500" />
                        {t("onboarding.phone", locale)}
                    </label>
                    <Input
                        id="onboarding-phone"
                        icon={<Phone className="h-4 w-4 md:h-5 md:w-5" />}
                        type="tel"
                        inputMode="tel"
                        autoComplete="tel"
                        placeholder={t("onboarding.phonePlaceholder", locale) || "+1 (555) 123-4567"}
                        value={contactInfo.phone}
                        onChange={(e) => handlePhoneChange(e.target.value)}
                        onClear={() => setContactInfo(c => ({ ...c, phone: "" }))}
                        className="bg-white shadow-sm"
                        error={!!formErrors.phone}
                    />
                    <p className="mt-1 text-[10px] text-slate-400">{t("onboarding.phoneHint", locale) || "Optional. Include country code (e.g. +1 for US)."}</p>
                    {formErrors.phone && (
                        <p className="mt-1 text-[10px] text-red-500 font-medium">{formErrors.phone}</p>
                    )}
                </div>

                {parsedResume && (
                    <div className="p-3 md:p-4 rounded-xl bg-emerald-50 border border-emerald-100">
                        <div className="flex items-center gap-2 mb-1">
                            <UserCheck className="h-4 w-4 text-emerald-600" />
                            <p className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">{t("onboarding.aiExtracted", locale) || "AI-Extracted From Resume"}</p>
                        </div>
                        <p className="text-xs text-emerald-800 font-medium">{t("onboarding.verifyDetails", locale) || "We pre-filled these from your resume. Please verify details."}</p>
                    </div>
                )}
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-4 mt-4">
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
                    disabled={!contactInfo.first_name || !contactInfo.last_name || !contactInfo.email || !isValidEmail(contactInfo.email) || isSavingContact}
                    className="flex-1 h-12 sm:h-11 rounded-xl font-bold bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 text-sm disabled:opacity-50 disabled:cursor-not-allowed group touch-manipulation"
                    aria-label={t("onboarding.confirmIdentity", locale) || "Confirm identity and continue"} data-onboarding-next
                >
                    {isSavingContact ? <LoadingSpinner size="sm" /> : t("onboarding.continue", locale)}
                </Button>
            </div>
        </div>
    );
}
