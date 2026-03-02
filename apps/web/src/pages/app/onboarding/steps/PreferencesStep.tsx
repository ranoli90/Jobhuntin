import * as React from "react";
import { MapPin, Briefcase, DollarSign, Wifi, Shield, ArrowLeft, ArrowRight, Building2, Ban, Globe, AlertTriangle } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { AutoCompleteInput } from "../../../../components/ui/AutoCompleteInput";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { AISuggestionCard, SalarySuggestionCard } from "../../../../components/ui/AISuggestionCard";
import { CITIES } from "../../../../data/cities";
import { JOB_TITLES } from "../../../../data/jobTitles";

// Salary validation utilities
const validateSalary = (value: string, fieldName: string): { isValid: boolean; error?: string } => {
  if (!value || value.trim() === '') {
    return { isValid: false, error: `${fieldName === 'salary_min' ? 'Minimum' : 'Maximum'} salary is required` };
  }
  
  const numValue = Number.parseFloat(value);
  if (Number.isNaN(numValue)) {
    return { isValid: false, error: 'Please enter a valid number' };
  }
  
  if (numValue < 0) {
    return { isValid: false, error: 'Salary must be greater than 0' };
  }
  
  if (numValue > 10000000) {
    return { isValid: false, error: 'Salary cannot exceed $10,000,000' };
  }
  
  return { isValid: true };
};

const validateSalaryRange = (min: string, max: string): { isValid: boolean; error?: string } => {
  if (!min || !max) return { isValid: true }; // Skip validation if either field is empty
  
  const minNum = Number.parseFloat(min);
  const maxNum = Number.parseFloat(max);
  
  if (!Number.isNaN(minNum) && !Number.isNaN(maxNum) && minNum > maxNum) {
    return { isValid: false, error: 'Minimum salary cannot be greater than maximum salary' };
  }
  
  return { isValid: true };
};

interface PreferencesStepProps {
    onNext: () => void;
    onPrev: () => void;
    preferences: {
        location: string;
        role_type: string;
        salary_min: string;
        salary_max?: string;
        remote_only: boolean;
        onsite_only?: boolean;
        work_authorized?: boolean;
        visa_sponsorship?: boolean;
        excluded_companies?: string[];
        excluded_keywords?: string[];
    };
    setPreferences: React.Dispatch<React.SetStateAction<{
        location: string;
        role_type: string;
        salary_min: string;
        salary_max?: string;
        remote_only: boolean;
        onsite_only?: boolean;
        work_authorized?: boolean;
        visa_sponsorship?: boolean;
        excluded_companies?: string[];
        excluded_keywords?: string[];
    }>>;
    isSavingPreferences: boolean;
    aiSuggestions: any;
    formErrors: Record<string, string>;
    hasParsedProfile?: boolean;
    onClearError?: (field: string) => void;
}

export function PreferencesStep({
    onNext,
    onPrev,
    preferences,
    setPreferences,
    isSavingPreferences,
    aiSuggestions,
    formErrors,
    hasParsedProfile = false,
    onClearError,
}: PreferencesStepProps) {

    // M-3 fix: store raw text while editing to avoid flickering from split/join on each keystroke
    const [localExcludedKeywords, setLocalExcludedKeywords] = React.useState(
        preferences.excluded_keywords?.join(', ') || ''
    );
    
    // Local validation state for salary fields
    const [salaryErrors, setSalaryErrors] = React.useState<Record<string, string>>({});
    
    // Validate salary fields on change
    const validateSalaryFields = React.useCallback((minSalary: string, maxSalary: string) => {
        const errors: Record<string, string> = {};
        
        // Validate minimum salary
        const minValidation = validateSalary(minSalary, 'salary_min');
        if (!minValidation.isValid) {
            errors.salary_min = minValidation.error!;
        }
        
        // Validate maximum salary (only if provided)
        if (maxSalary && maxSalary.trim() !== '') {
            const maxValidation = validateSalary(maxSalary, 'salary_max');
            if (!maxValidation.isValid) {
                errors.salary_max = maxValidation.error!;
            }
        }
        
        // Validate salary range
        const rangeValidation = validateSalaryRange(minSalary, maxSalary);
        if (!rangeValidation.isValid) {
            errors.salary_min = rangeValidation.error!; // Show range error on min field
        }
        
        setSalaryErrors(errors);
        return Object.keys(errors).length === 0;
    }, []);
    
    // Check if form is valid for submission
    const isFormValid = React.useMemo(() => {
        const hasRequiredFields = preferences.location.trim() !== '' && 
                                preferences.role_type.trim() !== '' && 
                                preferences.salary_min.trim() !== '';
        
        const hasNoErrors = Object.keys(formErrors).length === 0 && 
                           Object.keys(salaryErrors).length === 0;
        
        return hasRequiredFields && hasNoErrors;
    }, [preferences, formErrors, salaryErrors]);
    
    // Validate on salary changes
    React.useEffect(() => {
        validateSalaryFields(preferences.salary_min, preferences.salary_max || '');
    }, [preferences.salary_min, preferences.salary_max, validateSalaryFields]);
    const [excludedKeywordsText, setExcludedKeywordsText] = React.useState(
        (preferences.excluded_keywords || []).join(", ")
    );

    const handleLocationChange = (value: string) => {
        setPreferences((p) => ({ ...p, location: value }));
        if (formErrors.location && onClearError) {
            onClearError('location');
        }
    };

    const handleRoleTypeChange = (value: string) => {
        setPreferences((p) => ({ ...p, role_type: value }));
        if (formErrors.role_type && onClearError) {
            onClearError('role_type');
        }
    };

    const showAISuggestions = hasParsedProfile && (
        aiSuggestions.roles.data ||
        aiSuggestions.roles.loading ||
        aiSuggestions.locations.data ||
        aiSuggestions.locations.loading ||
        aiSuggestions.salary.data ||
        aiSuggestions.salary.loading
    );
    return (
        <div>
            <div className="mb-4 md:mb-6 flex items-center gap-3 md:gap-4 border-b border-slate-100 pb-4 md:pb-6">
                <div className="flex h-10 w-12 md:h-12 md:w-14 shrink-0 items-center justify-center rounded-xl md:rounded-2xl bg-amber-50 border border-amber-100 text-amber-600 shadow-sm">
                    <MapPin className="h-5 w-5 md:h-6 md:w-6" />
                </div>
                <div className="min-w-0">
                    <h2 className="font-display text-lg md:text-2xl font-bold text-slate-900 tracking-tight">Job Settings</h2>
                    <p className="text-xs md:text-sm text-slate-500 font-medium">Set your location and salary goals.</p>
                </div>
            </div>

            {showAISuggestions && (
                <>
                    {(aiSuggestions.roles.data || aiSuggestions.roles.loading || aiSuggestions.locations.data || aiSuggestions.locations.loading) && (
                        <div className="grid md:grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6">
                            <AISuggestionCard
                                title="Suggested Roles"
                                subtitle="Based on your experience"
                                suggestions={aiSuggestions.roles.data?.suggested_roles || []}
                                confidence={aiSuggestions.roles.data?.confidence}
                                reasoning={aiSuggestions.roles.data?.reasoning}
                                loading={aiSuggestions.roles.loading}
                                error={aiSuggestions.roles.error}
                                onAccept={(role) => setPreferences(p => ({ ...p, role_type: role }))}
                                onReject={() => { console.debug('[AI] User dismissed role suggestion'); }}
                            />
                            <AISuggestionCard
                                title="Recommended Locations"
                                subtitle={aiSuggestions.locations.data?.remote_friendly_score
                                    ? `${Math.round(aiSuggestions.locations.data.remote_friendly_score * 100)}% remote`
                                    : "Based on your skills"
                                }
                                suggestions={aiSuggestions.locations.data?.suggested_locations || []}
                                confidence={aiSuggestions.locations.data?.remote_friendly_score}
                                reasoning={aiSuggestions.locations.data?.reasoning}
                                loading={aiSuggestions.locations.loading}
                                error={aiSuggestions.locations.error}
                                onAccept={(location) => setPreferences(p => ({ ...p, location }))}
                                onReject={() => { console.debug('[AI] User dismissed location suggestion'); }}
                            />
                        </div>
                    )}

                    {(aiSuggestions.salary.data || aiSuggestions.salary.loading) && (
                        <div className="mb-4 md:mb-6">
                            <SalarySuggestionCard
                                minSalary={aiSuggestions.salary.data?.min_salary || 0}
                                maxSalary={aiSuggestions.salary.data?.max_salary || 0}
                                marketMedian={aiSuggestions.salary.data?.market_median || 0}
                                currency={aiSuggestions.salary.data?.currency}
                                confidence={aiSuggestions.salary.data?.confidence}
                                factors={aiSuggestions.salary.data?.factors}
                                reasoning={aiSuggestions.salary.data?.reasoning}
                                loading={aiSuggestions.salary.loading}
                                error={aiSuggestions.salary.error}
                                onAccept={(min) => setPreferences(p => ({ ...p, salary_min: String(min) }))}
                                onReject={() => { console.debug('[AI] User dismissed salary suggestion'); }}
                            />
                        </div>
                    )}
                </>
            )}

            <div className="space-y-4 md:space-y-6">
                <div className="grid gap-4 md:gap-6">
                    <div>
                        <label className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            <div className="w-1 h-1 rounded-full bg-primary-500" />
                            Where do you want to work?
                        </label>
                        <AutoCompleteInput
                            icon={<MapPin className="h-4 w-4 md:h-5 md:w-5" />}
                            type="text"
                            placeholder="e.g., Remote, Austin TX, London"
                            value={preferences.location}
                            onChange={handleLocationChange}
                            onClear={() => setPreferences((p) => ({ ...p, location: "" }))}
                            suggestions={CITIES}
                            className="bg-white shadow-sm"
                            error={!!formErrors.location}
                        />
                    </div>

                    <div>
                        <label className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            <div className="w-1 h-1 rounded-full bg-primary-500" />
                            Desired Job Title
                        </label>
                        <AutoCompleteInput
                            icon={<Briefcase className="h-4 w-4 md:h-5 md:w-5" />}
                            type="text"
                            placeholder="e.g., Staff AI Engineer"
                            value={preferences.role_type}
                            onChange={handleRoleTypeChange}
                            onClear={() => setPreferences((p) => ({ ...p, role_type: "" }))}
                            suggestions={JOB_TITLES}
                            className="bg-white shadow-sm"
                            error={!!formErrors.role_type}
                        />
                    </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 md:gap-6">
                    <div>
                        <label className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            <div className="w-1 h-1 rounded-full bg-primary-500" />
                            Minimum Salary
                        </label>
                        <Input
                            icon={<DollarSign className="h-4 w-4 md:h-5 md:w-5" />}
                            type="number"
                            min="0"
                            max="10000000"
                            placeholder="150000"
                            value={preferences.salary_min}
                            onChange={(e) => {
                                setPreferences((p) => ({ ...p, salary_min: e.target.value || "" }));
                            }}
                            onClear={() => setPreferences((p) => ({ ...p, salary_min: "" }))}
                            className="bg-white shadow-sm"
                            error={!!salaryErrors.salary_min}
                            helperText={salaryErrors.salary_min}
                        />
                    </div>
                    <label className={`flex items-center gap-3 md:gap-4 p-3 md:p-4 rounded-xl cursor-pointer border transition-all ${preferences.remote_only ? 'bg-primary-50 border-primary-200' : 'bg-slate-50 border-slate-100'}`}>
                        <div className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center transition-all ${preferences.remote_only ? 'bg-primary-600 text-white' : 'bg-white text-slate-300'}`}>
                            <Wifi className="h-4 w-4 md:h-5 md:w-5" />
                        </div>
                        <div className="flex-1">
                            <p className="text-xs font-bold text-slate-900">Remote Work Only</p>
                            <p className="text-[10px] text-slate-500">Show only work-from-home jobs</p>
                        </div>
                        <input
                            type="checkbox"
                            checked={preferences.remote_only}
                            onChange={(e) => setPreferences((p) => ({ ...p, remote_only: e.target.checked, onsite_only: e.target.checked ? false : p.onsite_only }))}
                            className="h-5 w-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                        />
                    </label>
                </div>

                {/* Dealbreaker Filters */}
                <div className="pt-4 md:pt-6 border-t border-slate-100">
                    <div className="flex items-center gap-2 mb-3 md:mb-4">
                        <div className="w-1 h-1 rounded-full bg-red-500" />
                        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            Dealbreakers
                        </label>
                    </div>

                    <div className="space-y-3">
                        <label className={`flex items-center gap-3 md:gap-4 p-3 md:p-4 rounded-xl cursor-pointer border transition-all ${preferences.visa_sponsorship ? 'bg-blue-50 border-blue-200' : 'bg-slate-50 border-slate-100'}`}>
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${preferences.visa_sponsorship ? 'bg-blue-600 text-white' : 'bg-white text-slate-300'}`}>
                                <Globe className="h-4 w-4" />
                            </div>
                            <div className="flex-1">
                                <p className="text-xs font-bold text-slate-900">Need Visa Sponsorship?</p>
                                <p className="text-[10px] text-slate-500">I need a company to sponsor my work visa</p>
                            </div>
                            <input
                                type="checkbox"
                                checked={preferences.visa_sponsorship || false}
                                onChange={(e) => setPreferences((p) => ({ ...p, visa_sponsorship: e.target.checked }))}
                                className="h-5 w-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                            />
                        </label>

                        <label className={`flex items-center gap-3 md:gap-4 p-3 md:p-4 rounded-xl cursor-pointer border transition-all ${preferences.onsite_only ? 'bg-purple-50 border-purple-200' : 'bg-slate-50 border-slate-100'}`}>
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${preferences.onsite_only ? 'bg-purple-600 text-white' : 'bg-white text-slate-300'}`}>
                                <Building2 className="h-4 w-4" />
                            </div>
                            <div className="flex-1">
                                <p className="text-xs font-bold text-slate-900">On-site Only</p>
                                <p className="text-[10px] text-slate-500">I want to work at the office</p>
                            </div>
                            <input
                                type="checkbox"
                                checked={preferences.onsite_only || false}
                                onChange={(e) => setPreferences((p) => ({ ...p, onsite_only: e.target.checked, remote_only: e.target.checked ? false : p.remote_only }))}
                                className="h-5 w-5 rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                            />
                        </label>

                        <div className="p-3 md:p-4 rounded-xl border bg-slate-50 border-slate-100">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white text-slate-400">
                                    <DollarSign className="h-4 w-4" aria-hidden />
                                </div>
                                <div>
                                    <p className="text-xs font-bold text-slate-900">Salary Cap</p>
                                    <p className="text-[10px] text-slate-500">Your target upper range. Max $10M.</p>
                                </div>
                            </div>
                            <Input
                                type="number"
                                min="0"
                                max="10000000"
                                placeholder="e.g., 300000"
                                value={preferences.salary_max || ""}
                                onChange={(e) => {
                                  setPreferences((p) => ({ ...p, salary_max: e.target.value || "" }));
                                  if (formErrors.salary_max && onClearError) onClearError("salary_max");
                                }}
                                onClear={() => {
                                  setPreferences((p) => ({ ...p, salary_max: "" }));
                                  if (onClearError) onClearError("salary_max");
                                }}
                                className="bg-white"
                                error={!!salaryErrors.salary_max}
                                helperText={salaryErrors.salary_max}
                            />
                        </div>

                        <div className="p-3 md:p-4 rounded-xl border bg-slate-50 border-slate-100">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white text-slate-400">
                                    <Ban className="h-4 w-4" aria-hidden />
                                </div>
                                <div>
                                    <p className="text-xs font-bold text-slate-900">Exclude Companies</p>
                                    <p className="text-[10px] text-slate-500">Companies you don't want to apply to</p>
                                </div>
                            </div>
                            <Input
                                type="text"
                                placeholder="e.g., BadCorp, ToxicInc"
                                value={excludedCompaniesText}
                                onChange={(e) => setExcludedCompaniesText(e.target.value)}
                                onBlur={() => setPreferences((p) => ({
                                    ...p,
                                    excluded_companies: excludedCompaniesText.split(",").map(s => s.trim()).filter(Boolean)
                                }))}
                                onClear={() => { setExcludedCompaniesText(""); setPreferences((p) => ({ ...p, excluded_companies: [] })); }}
                                className="bg-white"
                            />
                        </div>

                        <div className="p-3 md:p-4 rounded-xl border bg-slate-50 border-slate-100">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white text-slate-400">
                                    <AlertTriangle className="h-4 w-4" />
                                </div>
                                <div>
                                    <p className="text-xs font-bold text-slate-900">Exclude Keywords</p>
                                    <p className="text-[10px] text-slate-500">Jobs with these words won't be shown</p>
                                </div>
                            </div>
                            <Input
                                type="text"
                                placeholder="e.g., senior, lead, manager"
                                value={excludedKeywordsText}
                                onChange={(e) => setExcludedKeywordsText(e.target.value)}
                                onBlur={() => setPreferences((p) => ({
                                    ...p,
                                    excluded_keywords: excludedKeywordsText.split(",").map(s => s.trim()).filter(Boolean)
                                }))}
                                onClear={() => { setExcludedKeywordsText(""); setPreferences((p) => ({ ...p, excluded_keywords: [] })); }}
                                className="bg-white"
                            />
                        </div>
                    </div>
                </div>

                {/* Work Authorization */}
                <div className="pt-4 md:pt-6 border-t border-slate-100">
                    <label className="mb-2 md:mb-3 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        <div className="w-1 h-1 rounded-full bg-emerald-500" />
                        Work Authorization
                    </label>
                    <label className={`flex items-center gap-3 md:gap-4 p-3 md:p-4 rounded-xl cursor-pointer border transition-all ${preferences.work_authorized ? 'bg-emerald-50 border-emerald-200' : 'bg-slate-50 border-slate-100'}`}>
                        <div className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center transition-all ${preferences.work_authorized ? 'bg-emerald-600 text-white' : 'bg-white text-slate-300'}`}>
                            <Shield className="h-4 w-4 md:h-5 md:w-5" />
                        </div>
                        <div className="flex-1">
                            <p className="text-xs font-bold text-slate-900">Can you work legally?</p>
                            <p className="text-[10px] text-slate-500">I don't need a visa sponsor</p>
                        </div>
                        <input
                            type="checkbox"
                            checked={preferences.work_authorized}
                            onChange={(e) => setPreferences((p) => ({ ...p, work_authorized: e.target.checked }))}
                            className="h-5 w-5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                        />
                    </label>
                </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-4 mt-4">
                <Button
                    type="button"
                    variant="ghost"
                    onClick={onPrev}
                    className="h-12 sm:h-11 rounded-xl font-bold text-slate-400 hover:text-slate-900 border border-slate-100 hover:bg-slate-50 text-sm px-4 touch-manipulation"
                    aria-label="Go back to previous step"
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back
                </Button>
                <Button
                    type="button"
                    onClick={onNext}
                    className="flex-1 h-12 sm:h-11 rounded-xl font-bold bg-primary-600 hover:bg-primary-500 shadow-lg shadow-primary-500/20 text-sm group touch-manipulation"
                    disabled={!isFormValid || isSavingPreferences}
                    aria-label="Save preferences and continue" data-onboarding-next
                >
                    {isSavingPreferences ? <LoadingSpinner size="sm" /> : "Save & Continue"}
                    {!isSavingPreferences && <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />}
                </Button>
            </div>
        </div>
    );
}
