import * as React from "react";
import { MapPin, Briefcase, DollarSign, Zap, Shield, ArrowLeft, ArrowRight, HelpCircle } from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { AISuggestionCard, SalarySuggestionCard } from "../../../../components/ui/AISuggestionCard";

interface PreferencesStepProps {
    onNext: () => void;
    onPrev: () => void;
    preferences: {
        location: string;
        role_type: string;
        salary_min: string;
        remote_only: boolean;
        work_authorized: boolean;
    };
    setPreferences: React.Dispatch<React.SetStateAction<{
        location: string;
        role_type: string;
        salary_min: string;
        remote_only: boolean;
        work_authorized: boolean;
    }>>;
    isSavingPreferences: boolean;
    aiSuggestions: any;
    formErrors: Record<string, string>;
}

export function PreferencesStep({
    onNext,
    onPrev,
    preferences,
    setPreferences,
    isSavingPreferences,
    aiSuggestions,
    formErrors,
}: PreferencesStepProps) {
    const [plainLanguage, setPlainLanguage] = React.useState(false);

    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                <div className="flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6 mb-3 md:mb-8">
                    <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-amber-50 border border-amber-100 text-amber-600 shadow-inner">
                        <MapPin className="h-4 w-4 md:h-8 md:w-8" />
                    </div>
                    <div className="min-w-0">
                        <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">{plainLanguage ? "Job Settings" : "Active Parameters"}</h2>
                        <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">{plainLanguage ? "Set your location and salary goals." : "Define the geospatial and fiscal bounds."}</p>
                    </div>
                </div>

                {/* AI Suggestions Section */}
                {(aiSuggestions.roles.data || aiSuggestions.roles.loading || aiSuggestions.locations.data || aiSuggestions.locations.loading) && (
                    <div className="grid md:grid-cols-2 gap-2.5 md:gap-6 mb-3 md:mb-8">
                        {/* Role Suggestions */}
                        <AISuggestionCard
                            title="Suggested Roles"
                            subtitle="Based on your experience"
                            suggestions={aiSuggestions.roles.data?.suggested_roles || []}
                            confidence={aiSuggestions.roles.data?.confidence}
                            reasoning={aiSuggestions.roles.data?.reasoning}
                            loading={aiSuggestions.roles.loading}
                            error={aiSuggestions.roles.error}
                            onAccept={(role) => setPreferences(p => ({ ...p, role_type: role }))}
                            onReject={() => { }}
                        />

                        {/* Location Suggestions */}
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
                            onReject={() => { }}
                        />
                    </div>
                )}

                {/* Salary Suggestion */}
                {(aiSuggestions.salary.data || aiSuggestions.salary.loading) && (
                    <div className="mb-3 md:mb-8">
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
                            onReject={() => { }}
                        />
                    </div>
                )}

                <div className="flex justify-end mb-4">
                    <button
                        onClick={() => setPlainLanguage(!plainLanguage)}
                        className="text-[10px] uppercase font-bold text-slate-400 hover:text-slate-600 flex items-center gap-1 bg-slate-100 px-2 py-1 rounded-full transition-colors"
                    >
                        <span className={plainLanguage ? "text-primary-600" : ""}>Simple</span>
                        <span className="text-slate-300">/</span>
                        <span className={!plainLanguage ? "text-primary-600" : ""}>Technical</span>
                    </button>
                </div>

                <div className="space-y-3 md:space-y-8">
                    <div className="grid gap-3 md:gap-8">
                        <div>
                            <label className="mb-2 md:mb-4 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] group relative w-fit">
                                <div className="w-1 h-1 rounded-full bg-primary-500" />
                                {plainLanguage ? "Where do you want to work?" : "Primary Operation Hub"}
                                <HelpCircle className="w-3 h-3 text-slate-300 cursor-help" />
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-slate-800 text-white text-[10px] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 font-medium normal-case tracking-normal">
                                    Determines legal jurisdiction and timezones.
                                </div>
                            </label>
                            <div className="relative">
                                <Input
                                    icon={<MapPin className="h-4 w-4 md:h-5 md:w-5" />}
                                    type="text"
                                    placeholder="e.g., Remote, Austin TX, London"
                                    value={preferences.location}
                                    onChange={(e) => setPreferences((p) => ({ ...p, location: e.target.value }))}
                                    onClear={() => setPreferences((p) => ({ ...p, location: "" }))}
                                    className="bg-white shadow-sm text-sm"
                                    error={!!formErrors.location}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="mb-2 md:mb-4 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                                <div className="w-1 h-1 rounded-full bg-primary-500" />
                                {plainLanguage ? "Desired Job Title" : "Target Role Classification"}
                            </label>
                            <div className="relative">
                                <Input
                                    icon={<Briefcase className="h-4 w-4 md:h-5 md:w-5" />}
                                    type="text"
                                    placeholder="e.g., Staff AI Engineer"
                                    value={preferences.role_type}
                                    onChange={(e) => setPreferences((p) => ({ ...p, role_type: e.target.value }))}
                                    onClear={() => setPreferences((p) => ({ ...p, role_type: "" }))}
                                    className="bg-white shadow-sm text-sm"
                                    error={!!formErrors.role_type}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-3 md:gap-8">
                        <div>
                            <label className="mb-2 md:mb-4 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] group relative w-fit">
                                <div className="w-1 h-1 rounded-full bg-primary-500" />
                                {plainLanguage ? "Minimum Salary" : "Min Multiplier (Salary)"}
                                <HelpCircle className="w-3 h-3 text-slate-300 cursor-help" />
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-slate-800 text-white text-[10px] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 font-medium normal-case tracking-normal">
                                    We filter out roles below this threshold.
                                </div>
                            </label>
                            <div className="relative">
                                <Input
                                    icon={<DollarSign className="h-4 w-4 md:h-5 md:w-5" />}
                                    type="number"
                                    placeholder="150000"
                                    value={preferences.salary_min}
                                    onChange={(e) => setPreferences((p) => ({ ...p, salary_min: e.target.value }))}
                                    onClear={() => setPreferences((p) => ({ ...p, salary_min: "" }))}
                                    className="bg-white shadow-sm text-sm"
                                />
                            </div>
                        </div>
                        <div className="flex flex-col justify-end">
                            <label className={`flex items-center gap-3 md:gap-4 p-3 md:p-5 rounded-2xl cursor-pointer border-2 transition-all ${preferences.remote_only ? 'bg-primary-50 border-primary-200 shadow-sm' : 'bg-slate-50 border-slate-100'}`}>
                                <div className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center transition-all ${preferences.remote_only ? 'bg-primary-600 text-white' : 'bg-white text-slate-300 shadow-sm'}`}>
                                    <Zap className="h-4 w-4 md:h-5 md:w-5" />
                                </div>
                                <div className="flex-1">
                                    <p className="text-xs font-black text-slate-900 uppercase tracking-tight">{plainLanguage ? "Onne-Online (Remote)" : "Geo-Agnostic Only"}</p>
                                    <p className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-widest">{plainLanguage ? "Show only work-from-home jobs" : "100% Remote Filter"}</p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={preferences.remote_only}
                                    onChange={(e) => setPreferences((p) => ({ ...p, remote_only: e.target.checked }))}
                                    className="h-5 w-5 md:h-6 md:w-6 rounded-lg border-slate-300 text-primary-600 focus:ring-primary-500"
                                />
                            </label>
                        </div>
                    </div>
                </div>

                {/* Work Authorization */}
                <div className="pt-3 md:pt-6 border-t border-slate-100 mt-3 md:mt-8">
                    <label className="mb-2 md:mb-4 flex items-center gap-2 md:gap-3 text-[8px] md:text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                        <div className="w-1 h-1 rounded-full bg-emerald-500" />
                        Work Authorization
                    </label>
                    <label className={`flex items-center gap-3 md:gap-4 p-3 md:p-5 rounded-2xl cursor-pointer border-2 transition-all ${preferences.work_authorized ? 'bg-emerald-50 border-emerald-200 shadow-sm' : 'bg-slate-50 border-slate-100'}`}>
                        <div className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center transition-all ${preferences.work_authorized ? 'bg-emerald-600 text-white' : 'bg-white text-slate-300 shadow-sm'}`}>
                            <Shield className="h-4 w-4 md:h-5 md:w-5" />
                        </div>
                        <div className="flex-1">
                            <p className="text-xs font-black text-slate-900 uppercase tracking-tight">{plainLanguage ? "Can you work legally?" : "Authorized to Work"}</p>
                            <p className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-widest">{plainLanguage ? "I don't need a visa sponsor" : "No visa sponsorship needed"}</p>
                        </div>
                        <input
                            type="checkbox"
                            checked={preferences.work_authorized}
                            onChange={(e) => setPreferences((p) => ({ ...p, work_authorized: e.target.checked }))}
                            className="h-5 w-5 md:h-6 md:w-6 rounded-lg border-slate-300 text-emerald-600 focus:ring-emerald-500"
                        />
                    </label>
                </div>
            </div>

            <div className="flex gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button variant="ghost" onClick={onPrev} className="h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4" aria-label="Go to previous step">
                    <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                    PREV
                </Button>
                <Button onClick={onNext} className="flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black bg-primary-600 hover:bg-primary-500 shadow-2xl shadow-primary-500/30 text-xs md:text-xl group" disabled={isSavingPreferences} aria-label="Save preferences and deploy hunter engine">
                    {isSavingPreferences ? <LoadingSpinner size="sm" /> : "DEPLOY HUNTER ENGINE"}
                    <ArrowRight className="ml-1.5 md:ml-3 h-4 w-4 md:h-6 md:w-6 group-hover:translate-x-1 transition-transform" />
                </Button>
            </div>
        </div>
    );
}
