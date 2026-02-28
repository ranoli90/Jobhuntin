/**
 * AISuggestionCard - Displays AI-generated suggestions with accept/reject actions
 * 
 * Used during onboarding to show role suggestions, salary estimates, and location
 * recommendations with confidence scores and explanations.
 */

import * as React from "react";
import { cn } from "../../lib/utils";

// Sparkles icon for AI branding
const SparklesIcon = () => (
    <svg
        className="w-4 h-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <path d="M12 3L13.4 8.6L19 10L13.4 11.4L12 17L10.6 11.4L5 10L10.6 8.6L12 3Z" />
        <path d="M19 15L19.94 17.06L22 18L19.94 18.94L19 21L18.06 18.94L16 18L18.06 17.06L19 15Z" />
        <path d="M5 15L5.94 17.06L8 18L5.94 18.94L5 21L4.06 18.94L2 18L4.06 17.06L5 15Z" />
    </svg>
);

// Confidence indicator bar
const ConfidenceBar = ({ confidence }: { confidence: number }) => {
    const percentage = Math.round(confidence * 100);
    const color = confidence >= 0.7 ? "bg-emerald-500" : confidence >= 0.4 ? "bg-amber-500" : "bg-slate-400";

    return (
        <div className="flex items-center gap-2 text-xs text-slate-500">
            <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                    className={cn("h-full rounded-full transition-all duration-500", color)}
                    style={{ width: `${percentage}%` }}
                />
            </div>
            <span className="tabular-nums">{percentage}%</span>
        </div>
    );
};

export interface AISuggestionCardProps {
    /** Title of the suggestion card */
    title: string;
    /** Subtitle or description */
    subtitle?: string;
    /** List of suggestions to display */
    suggestions: string[];
    /** AI confidence score 0-1 */
    confidence?: number;
    /** Explanation of the suggestions */
    reasoning?: string;
    /** Called when user accepts a suggestion */
    onAccept?: (suggestion: string) => void;
    /** Called when user rejects all suggestions */
    onReject?: () => void;
    /** Loading state */
    loading?: boolean;
    /** Error message */
    error?: string | null;
    /** Additional className */
    className?: string;
    /** Allow selecting multiple suggestions */
    multiSelect?: boolean;
    /** Currently selected suggestions (for controlled mode) */
    selected?: string[];
    /** Callback when selection changes */
    onSelectionChange?: (selected: string[]) => void;
}

export function AISuggestionCard({
    title,
    subtitle,
    suggestions,
    confidence,
    reasoning,
    onAccept,
    onReject,
    loading = false,
    error = null,
    className,
    multiSelect = false,
    selected: controlledSelected,
    onSelectionChange,
}: AISuggestionCardProps) {
    const [internalSelected, setInternalSelected] = React.useState<string[]>([]);
    const selected = controlledSelected ?? internalSelected;

    const handleSelect = (suggestion: string) => {
        let newSelected: string[];

        if (multiSelect) {
            if (selected.includes(suggestion)) {
                newSelected = selected.filter(s => s !== suggestion);
            } else {
                newSelected = [...selected, suggestion];
            }
        } else {
            newSelected = [suggestion];
            // For single select, immediately call onAccept
            onAccept?.(suggestion);
        }

        if (controlledSelected === undefined) {
            setInternalSelected(newSelected);
        }
        onSelectionChange?.(newSelected);
    };

    if (loading) {
        return (
            <div className={cn(
                "rounded-xl border border-violet-100 bg-gradient-to-br from-violet-50 to-white p-5",
                "animate-pulse",
                className
            )}>
                <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-full bg-violet-200" />
                    <div className="h-5 w-32 bg-violet-200 rounded" />
                </div>
                <div className="space-y-2">
                    <div className="h-10 bg-violet-100 rounded-lg" />
                    <div className="h-10 bg-violet-100/60 rounded-lg" />
                    <div className="h-10 bg-violet-100/30 rounded-lg" />
                </div>
                <div className="mt-4 text-xs text-violet-500 text-center">
                    ✨ AI is analyzing your profile...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={cn(
                "rounded-xl border border-red-200 bg-red-50 p-5",
                className
            )}>
                <div className="flex items-center gap-2 text-red-600 mb-2">
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    <span className="font-medium text-sm">Couldn't get suggestions</span>
                </div>
                <p className="text-xs text-red-500">{error}</p>
                {onReject && (
                    <button
                        onClick={onReject}
                        className="mt-3 text-xs text-red-600 hover:underline"
                    >
                        Continue without AI suggestions
                    </button>
                )}
            </div>
        );
    }

    if (suggestions.length === 0) {
        return null;
    }

    return (
        <div className={cn(
            "rounded-xl border border-violet-200 bg-gradient-to-br from-violet-50/80 to-white p-5",
            "shadow-sm shadow-violet-100/50",
            className
        )}>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white">
                        <SparklesIcon />
                    </div>
                    <div>
                        <h4 className="font-semibold text-slate-800 text-sm">{title}</h4>
                        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
                    </div>
                </div>
                <span className="text-[10px] font-medium text-violet-600 bg-violet-100 px-2 py-0.5 rounded-full">
                    AI Suggestion
                </span>
            </div>

            {/* Confidence indicator */}
            {confidence !== undefined && (
                <div className="mb-3">
                    <ConfidenceBar confidence={confidence} />
                </div>
            )}

            {/* Suggestions list */}
            <div className="space-y-2">
                {suggestions.map((suggestion, index) => {
                    const isSelected = selected.includes(suggestion);
                    return (
                        <button
                            key={suggestion}
                            onClick={() => handleSelect(suggestion)}
                            className={cn(
                                "w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200",
                                "border flex items-center justify-between group",
                                isSelected
                                    ? "bg-violet-100 border-violet-300 text-violet-900"
                                    : "bg-white border-slate-200 hover:border-violet-300 hover:bg-violet-50/50 text-slate-700",
                                index === 0 && !isSelected && "ring-1 ring-violet-200 ring-offset-2"
                            )}
                        >
                            <span className="font-medium">{suggestion}</span>
                            {isSelected ? (
                                <svg className="w-4 h-4 text-violet-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                            ) : (
                                <svg className="w-4 h-4 text-slate-300 group-hover:text-violet-400 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                </svg>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Reasoning */}
            {reasoning && (
                <p className="mt-3 text-xs text-slate-500 leading-relaxed">
                    💡 {reasoning}
                </p>
            )}

            {/* Actions */}
            {onReject && (
                <div className="mt-4 pt-3 border-t border-violet-100">
                    <button
                        onClick={onReject}
                        className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
                    >
                        Skip AI suggestions
                    </button>
                </div>
            )}
        </div>
    );
}

// Specialized card for salary suggestions
export interface SalarySuggestionCardProps {
    minSalary: number;
    maxSalary: number;
    marketMedian: number;
    currency?: string;
    confidence?: number;
    factors?: string[];
    reasoning?: string;
    loading?: boolean;
    error?: string | null;
    onAccept?: (min: number, max: number) => void;
    onReject?: () => void;
    className?: string;
}

export function SalarySuggestionCard({
    minSalary,
    maxSalary,
    marketMedian,
    currency = "USD",
    confidence,
    factors = [],
    reasoning,
    loading = false,
    error = null,
    onAccept,
    onReject,
    className,
}: SalarySuggestionCardProps) {
    const formatSalary = (amount: number) => {
        return new Intl.NumberFormat(navigator.language || "en-US", {
            style: "currency",
            currency,
            maximumFractionDigits: 0,
        }).format(amount);
    };

    if (loading) {
        return (
            <div className={cn(
                "rounded-xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white p-5",
                "animate-pulse",
                className
            )}>
                <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-full bg-emerald-200" />
                    <div className="h-5 w-40 bg-emerald-200 rounded" />
                </div>
                <div className="h-16 bg-emerald-100 rounded-lg" />
                <div className="mt-4 text-xs text-emerald-500 text-center">
                    💰 Calculating market rates...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={cn(
                "rounded-xl border border-red-200 bg-red-50 p-5",
                className
            )}>
                <p className="text-sm text-red-600">{error}</p>
            </div>
        );
    }

    return (
        <div className={cn(
            "rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50/80 to-white p-5",
            "shadow-sm shadow-emerald-100/50",
            className
        )}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white text-xs">
                        💵
                    </div>
                    <h4 className="font-semibold text-slate-800 text-sm">Salary Estimate</h4>
                </div>
                <span className="text-[10px] font-medium text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full">
                    AI Estimate
                </span>
            </div>

            {/* Salary range */}
            <div
                className="bg-white rounded-lg border border-emerald-200 p-4 cursor-pointer hover:border-emerald-400 transition-colors"
                onClick={() => onAccept?.(minSalary, maxSalary)}
            >
                <div className="flex items-baseline justify-center gap-2">
                    <span className="text-2xl font-bold text-emerald-600">{formatSalary(minSalary)}</span>
                    <span className="text-slate-400">—</span>
                    <span className="text-2xl font-bold text-emerald-600">{formatSalary(maxSalary)}</span>
                </div>
                <p className="text-center text-xs text-slate-500 mt-1">
                    Market median: {formatSalary(marketMedian)}
                </p>
            </div>

            {/* Confidence */}
            {confidence !== undefined && (
                <div className="mt-3">
                    <ConfidenceBar confidence={confidence} />
                </div>
            )}

            {/* Factors */}
            {factors.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                    {factors.slice(0, 4).map((factor) => (
                        <span
                            key={factor}
                            className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full"
                        >
                            {factor}
                        </span>
                    ))}
                </div>
            )}

            {/* Reasoning */}
            {reasoning && (
                <p className="mt-3 text-xs text-slate-500 leading-relaxed">
                    💡 {reasoning}
                </p>
            )}

            {/* Skip button */}
            {onReject && (
                <div className="mt-4 pt-3 border-t border-emerald-100">
                    <button
                        onClick={onReject}
                        className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
                    >
                        Set manually
                    </button>
                </div>
            )}
        </div>
    );
}
