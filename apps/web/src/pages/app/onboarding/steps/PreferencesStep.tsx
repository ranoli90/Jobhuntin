import * as React from "react";
import {
  MapPin,
  Briefcase,
  DollarSign,
  Wifi,
  Shield,
  ArrowLeft,
  ArrowRight,
  Building2,
  Ban,
  Globe,
  AlertTriangle,
} from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { AutoCompleteInput } from "../../../../components/ui/AutoCompleteInput";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import {
  AISuggestionCard,
  SalarySuggestionCard,
} from "../../../../components/ui/AISuggestionCard";
import { CITIES } from "../../../../data/cities";
import { JOB_TITLES } from "../../../../data/jobTitles";
import type {
  RoleSuggestion,
  SalarySuggestion,
  LocationSuggestion,
} from "../../../../hooks/useAISuggestions";
import { t, getLocale } from "../../../../lib/i18n";

// Salary validation utilities
const validateSalary = (
  value: string,
  fieldName: string,
  locale: string,
): { isValid: boolean; error?: string } => {
  if (!value || value.trim() === "") {
    return {
      isValid: false,
      error:
        fieldName === "salary_min"
          ? t("onboarding.minSalaryRequired", locale) ||
            "Minimum salary is required"
          : t("onboarding.maxSalaryRequired", locale) ||
            "Maximum salary is required",
    };
  }

  const numberValue = Number.parseFloat(value);
  if (Number.isNaN(numberValue)) {
    return {
      isValid: false,
      error:
        t("onboarding.validNumber", locale) || "Please enter a valid number",
    };
  }

  if (numberValue < 0) {
    return {
      isValid: false,
      error:
        t("onboarding.salaryGreaterThanZero", locale) ||
        "Salary must be greater than 0",
    };
  }

  if (numberValue > 10_000_000) {
    return {
      isValid: false,
      error:
        t("onboarding.salaryExceeds", locale) ||
        "Salary cannot exceed $10,000,000",
    };
  }

  return { isValid: true };
};

const validateSalaryRange = (
  min: string,
  max: string,
  locale: string,
): { isValid: boolean; error?: string } => {
  if (!min || !max) return { isValid: true }; // Skip validation if either field is empty

  const minNumber = Number.parseFloat(min);
  const maxNumber = Number.parseFloat(max);

  if (
    !Number.isNaN(minNumber) &&
    !Number.isNaN(maxNumber) &&
    minNumber > maxNumber
  ) {
    return {
      isValid: false,
      error:
        t("onboarding.minGreaterThanMax", locale) ||
        "Minimum salary cannot be greater than maximum salary",
    };
  }

  return { isValid: true };
};

interface PreferencesStepProperties {
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
  setPreferences: React.Dispatch<
    React.SetStateAction<{
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
    }>
  >;
  isSavingPreferences: boolean;
  aiSuggestions: {
    roles: RoleSuggestion | null;
    salary: SalarySuggestion | null;
    locations: LocationSuggestion | null;
    rolesLoading?: boolean;
    salaryLoading?: boolean;
    locationsLoading?: boolean;
    rolesError?: string | null;
    salaryError?: string | null;
    locationsError?: string | null;
  };
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
}: PreferencesStepProperties) {
  const locale = getLocale();

  // M-3 fix: store raw text while editing to avoid flickering from split/join on each keystroke
  const [localExcludedKeywords, setLocalExcludedKeywords] = React.useState(
    preferences.excluded_keywords?.join(", ") || "",
  );
  const [localExcludedCompanies, setLocalExcludedCompanies] = React.useState(
    preferences.excluded_companies?.join(", ") || "",
  );

  // F4: Sync local state when preferences changes from profile (e.g. profile loads after mount)
  React.useEffect(() => {
    setLocalExcludedKeywords(preferences.excluded_keywords?.join(", ") || "");
    setLocalExcludedCompanies(preferences.excluded_companies?.join(", ") || "");
  }, [preferences.excluded_keywords, preferences.excluded_companies]);

  const handleLocationChange = (value: string) => {
    setPreferences((p) => ({ ...p, location: value }));
    if (onClearError && formErrors.location) {
      onClearError("location");
    }
  };

  const handleRoleTypeChange = (value: string) => {
    setPreferences((p) => ({ ...p, role_type: value }));
    if (onClearError && formErrors.role_type) {
      onClearError("role_type");
    }
  };

  const handleSalaryChange = (
    field: "salary_min" | "salary_max",
    value: string,
  ) => {
    // Only allow digits and one decimal point
    const cleaned = value.replaceAll(/[^\d.]/g, "");
    setPreferences((p) => ({ ...p, [field]: cleaned }));
    if (onClearError && (formErrors.salary_min || formErrors.salary_max)) {
      onClearError("salary_min");
      onClearError("salary_max");
    }
  };

  const formatSalaryPreview = (value: string): string => {
    const number_ = Number.parseFloat(value);
    if (isNaN(number_) || value === "") return "";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(number_);
  };

  const handleExcludedKeywordsChange = (value: string) => {
    setLocalExcludedKeywords(value);
    const keywords = value
      .split(",")
      .map((k) => k.trim())
      .filter((k) => k.length > 0);
    setPreferences((p) => ({ ...p, excluded_keywords: keywords }));
  };

  const handleExcludedCompaniesChange = (value: string) => {
    setLocalExcludedCompanies(value);
    const companies = value
      .split(",")
      .map((c) => c.trim())
      .filter((c) => c.length > 0);
    setPreferences((p) => ({ ...p, excluded_companies: companies }));
  };

  return (
    <div role="region" aria-labelledby="preferences-step-title">
      <div className="mb-4 md:mb-6 flex items-center gap-3 md:gap-4 border-b border-slate-100 pb-4 md:pb-6">
        <div className="flex h-10 w-12 md:h-12 md:w-14 shrink-0 items-center justify-center rounded-xl md:rounded-2xl bg-emerald-50 border border-emerald-100 text-emerald-600 shadow-sm">
          <MapPin className="h-5 w-5 md:h-6 md:w-6" />
        </div>
        <div className="min-w-0">
          <h2
            id="preferences-step-title"
            className="font-display text-lg md:text-2xl font-bold text-slate-900 tracking-tight"
          >
            {t("onboarding.preferencesTitle", locale)}
          </h2>
          <p className="text-xs md:text-sm text-slate-500 font-medium">
            {t("onboarding.preferencesSubtitle", locale)}
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:gap-6">
        {/* Location */}
        <div>
          <label
            htmlFor="onboarding-location"
            className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider"
          >
            <MapPin className="w-3 h-3" />
            {t("onboarding.location", locale)}
          </label>
          <AutoCompleteInput
            id="onboarding-location"
            value={preferences.location}
            onChange={handleLocationChange}
            suggestions={CITIES}
            placeholder={t("onboarding.locationPlaceholder", locale)}
            icon={<MapPin className="h-4 w-4 md:h-5 md:w-5" />}
            error={!!formErrors.location}
          />
          {formErrors.location && (
            <p className="mt-1 text-[10px] text-red-500 font-medium">
              {formErrors.location}
            </p>
          )}
        </div>

        {/* Role Type */}
        <div>
          <label
            htmlFor="onboarding-role-type"
            className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider"
          >
            <Briefcase className="w-3 h-3" />
            {t("onboarding.roleType", locale)}
          </label>
          <AutoCompleteInput
            id="onboarding-role-type"
            value={preferences.role_type}
            onChange={handleRoleTypeChange}
            suggestions={JOB_TITLES}
            placeholder={t("onboarding.rolePlaceholder", locale)}
            icon={<Briefcase className="h-4 w-4 md:h-5 md:w-5" />}
            error={!!formErrors.role_type}
          />
          {formErrors.role_type && (
            <p className="mt-1 text-[10px] text-red-500 font-medium">
              {formErrors.role_type}
            </p>
          )}
        </div>

        {/* Salary Range */}
        <div className="grid grid-cols-2 gap-3 md:gap-4">
          <div>
            <label
              htmlFor="onboarding-salary-min"
              className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider"
            >
              <DollarSign className="w-3 h-3" />
              {t("onboarding.minSalary", locale)}
            </label>
            <Input
              id="onboarding-salary-min"
              type="number"
              inputMode="numeric"
              placeholder="80000"
              value={preferences.salary_min}
              onChange={(e) => handleSalaryChange("salary_min", e.target.value)}
              icon={<DollarSign className="h-4 w-4 md:h-5 md:w-5" />}
              className="bg-white shadow-sm"
              error={!!formErrors.salary_min}
            />
            {formErrors.salary_min && (
              <p className="mt-1 text-[10px] text-red-500 font-medium">
                {formErrors.salary_min}
              </p>
            )}
            {preferences.salary_min && !formErrors.salary_min && (
              <p className="mt-1 text-[10px] text-emerald-600 font-medium">
                {formatSalaryPreview(preferences.salary_min)}
              </p>
            )}
          </div>
          <div>
            <label
              htmlFor="onboarding-salary-max"
              className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider"
            >
              <DollarSign className="w-3 h-3" />
              {t("onboarding.maxSalary", locale)}
            </label>
            <Input
              id="onboarding-salary-max"
              type="number"
              inputMode="numeric"
              placeholder="150000"
              value={preferences.salary_max || ""}
              onChange={(e) => handleSalaryChange("salary_max", e.target.value)}
              icon={<DollarSign className="h-4 w-4 md:h-5 md:w-5" />}
              className="bg-white shadow-sm"
              error={!!formErrors.salary_max}
            />
            {formErrors.salary_max && (
              <p className="mt-1 text-[10px] text-red-500 font-medium">
                {formErrors.salary_max}
              </p>
            )}
            {preferences.salary_max && !formErrors.salary_max && (
              <p className="mt-1 text-[10px] text-emerald-600 font-medium">
                {formatSalaryPreview(preferences.salary_max)}
              </p>
            )}
          </div>
        </div>
        <p className="text-[10px] text-slate-400 -mt-2">
          {t("onboarding.salaryHint", locale)}
        </p>

        {/* Work Arrangement */}
        <div className="p-3 md:p-4 rounded-xl bg-slate-50 border border-slate-100">
          <label className="mb-3 flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <Wifi className="w-3 h-3" />
            {t("onboarding.workArrangement", locale) || "Work Arrangement"}
          </label>
          <div className="flex flex-col gap-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.remote_only}
                onChange={(e) =>
                  setPreferences((p) => ({
                    ...p,
                    remote_only: e.target.checked,
                    // Mutually exclusive with onsite_only
                    onsite_only: e.target.checked ? false : p.onsite_only,
                  }))
                }
                className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-slate-700">
                {t("onboarding.remoteOnly", locale)}
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.onsite_only || false}
                onChange={(e) =>
                  setPreferences((p) => ({
                    ...p,
                    onsite_only: e.target.checked,
                    // Mutually exclusive with remote_only
                    remote_only: e.target.checked ? false : p.remote_only,
                  }))
                }
                className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-slate-700">
                {t("onboarding.onsiteOnly", locale)}
              </span>
            </label>
          </div>
        </div>

        {/* Work Authorization */}
        <div className="p-3 md:p-4 rounded-xl bg-slate-50 border border-slate-100">
          <label className="mb-3 flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <Shield className="w-3 h-3" />
            {t("onboarding.workAuthorization", locale) || "Work Authorization"}
          </label>
          <div className="flex flex-col gap-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.work_authorized !== false}
                onChange={(e) =>
                  setPreferences((p) => ({
                    ...p,
                    work_authorized: e.target.checked,
                  }))
                }
                className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-slate-700">
                {t("onboarding.workAuthorized", locale)}
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.visa_sponsorship || false}
                onChange={(e) =>
                  setPreferences((p) => ({
                    ...p,
                    visa_sponsorship: e.target.checked,
                  }))
                }
                className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-slate-700">
                {t("onboarding.visaSponsorship", locale)}
              </span>
            </label>
          </div>
          {preferences.visa_sponsorship && (
            <p className="mt-2 text-[10px] text-amber-600 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              {t("onboarding.visaSponsorshipDesc", locale)}
            </p>
          )}
        </div>

        {/* Excluded Companies */}
        <div>
          <label
            htmlFor="onboarding-excluded-companies"
            className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider"
          >
            <Building2 className="w-3 h-3" />
            {t("onboarding.excludedCompanies", locale)}
          </label>
          <Input
            id="onboarding-excluded-companies"
            type="text"
            placeholder={
              t("onboarding.excludedCompaniesPlaceholder", locale) ||
              "Company A, Company B, ..."
            }
            value={localExcludedCompanies}
            onChange={(e) => handleExcludedCompaniesChange(e.target.value)}
            icon={<Ban className="h-4 w-4 md:h-5 md:w-5" />}
            className="bg-white shadow-sm"
          />
          <p className="mt-1 text-[10px] text-slate-400">
            {t("onboarding.excludedCompaniesHint", locale) ||
              "Separate multiple companies with commas"}
          </p>
        </div>

        {/* Excluded Keywords */}
        <div>
          <label
            htmlFor="onboarding-excluded-keywords"
            className="mb-2 flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider"
          >
            <Ban className="w-3 h-3" />
            {t("onboarding.excludedKeywords", locale)}
          </label>
          <Input
            id="onboarding-excluded-keywords"
            type="text"
            placeholder={
              t("onboarding.excludedKeywordsPlaceholder", locale) ||
              "keyword1, keyword2, ..."
            }
            value={localExcludedKeywords}
            onChange={(e) => handleExcludedKeywordsChange(e.target.value)}
            icon={<Ban className="h-4 w-4 md:h-5 md:w-5" />}
            className="bg-white shadow-sm"
          />
          <p className="mt-1 text-[10px] text-slate-400">
            {t("onboarding.excludedKeywordsHint", locale) ||
              "Jobs containing these keywords will be filtered out"}
          </p>
        </div>

        {/* AI Suggestions */}
        {hasParsedProfile && (
          <div className="p-3 md:p-4 rounded-xl bg-blue-50 border border-blue-100">
            <div className="flex items-center gap-2 mb-3">
              <Globe className="w-4 h-4 text-blue-600" />
              <p className="text-[10px] font-bold text-blue-800 uppercase tracking-wider">
                {t("onboarding.aiSuggestions", locale) || "AI Suggestions"}
              </p>
            </div>

            {aiSuggestions.locationsLoading ? (
              <AISuggestionCard
                title={
                  t("onboarding.suggestedLocation", locale) ||
                  "Suggested Location"
                }
                suggestions={[]}
                loading
              />
            ) : aiSuggestions.locationsError && !aiSuggestions.locations ? (
              <AISuggestionCard
                title={
                  t("onboarding.suggestedLocation", locale) ||
                  "Suggested Location"
                }
                suggestions={[]}
                error={aiSuggestions.locationsError}
              />
            ) : aiSuggestions.locations &&
              aiSuggestions.locations.suggested_locations?.length > 0 ? (
              <AISuggestionCard
                title={
                  t("onboarding.suggestedLocation", locale) ||
                  "Suggested Location"
                }
                suggestions={[aiSuggestions.locations.suggested_locations[0]]}
                confidence={
                  aiSuggestions.locations.remote_friendly_score ?? 0.5
                }
                onAccept={(value) => handleLocationChange(value)}
              />
            ) : null}

            {aiSuggestions.rolesLoading ? (
              <AISuggestionCard
                title={
                  t("onboarding.suggestedRole", locale) || "Suggested Role"
                }
                suggestions={[]}
                loading
              />
            ) : aiSuggestions.rolesError && !aiSuggestions.roles ? (
              <AISuggestionCard
                title={
                  t("onboarding.suggestedRole", locale) || "Suggested Role"
                }
                suggestions={[]}
                error={aiSuggestions.rolesError}
              />
            ) : aiSuggestions.roles ? (
              <AISuggestionCard
                title={
                  t("onboarding.suggestedRole", locale) || "Suggested Role"
                }
                suggestions={[aiSuggestions.roles.primary_role]}
                confidence={aiSuggestions.roles.confidence}
                onAccept={(value) => handleRoleTypeChange(value)}
              />
            ) : null}

            {aiSuggestions.salaryLoading ? (
              <SalarySuggestionCard
                minSalary={0}
                maxSalary={0}
                marketMedian={0}
                confidence={0}
                loading
              />
            ) : aiSuggestions.salaryError && !aiSuggestions.salary ? (
              <SalarySuggestionCard
                minSalary={0}
                maxSalary={0}
                marketMedian={0}
                confidence={0}
                error={aiSuggestions.salaryError}
              />
            ) : aiSuggestions.salary ? (
              <SalarySuggestionCard
                minSalary={Number(aiSuggestions.salary.min_salary)}
                maxSalary={Number(aiSuggestions.salary.max_salary)}
                marketMedian={
                  (Number(aiSuggestions.salary.min_salary) +
                    Number(aiSuggestions.salary.max_salary)) /
                  2
                }
                confidence={aiSuggestions.salary.confidence}
                onAccept={(min, max) => {
                  handleSalaryChange("salary_min", min.toString());
                  handleSalaryChange("salary_max", max.toString());
                }}
              />
            ) : null}
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
          variant="outline"
          onClick={onNext}
          disabled={isSavingPreferences}
          className="h-12 sm:h-11 rounded-xl font-bold text-slate-500 hover:text-slate-700 border border-slate-200 hover:bg-slate-50 text-sm px-4 touch-manipulation"
          aria-label={t("onboarding.skipForNow", locale)}
        >
          {t("onboarding.skipForNow", locale) || "Skip for now"}
        </Button>
        <Button
          type="button"
          onClick={onNext}
          disabled={isSavingPreferences}
          className="flex-1 h-12 sm:h-11 rounded-xl font-bold bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 text-sm disabled:opacity-50 disabled:cursor-not-allowed group touch-manipulation"
          aria-label={t("onboarding.savePreferences", locale)}
          data-onboarding-next
        >
          {isSavingPreferences ? (
            <LoadingSpinner size="sm" />
          ) : (
            <>
              {t("onboarding.savePreferences", locale)}
              <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
