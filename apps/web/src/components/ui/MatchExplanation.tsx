/**
 * MatchExplanation - Displays detailed breakdown of AI match scoring
 *
 * Shows why a job matched or didn't match, including:
 * - Semantic similarity score
 * - Skill match breakdown
 * - Experience alignment
 * - Dealbreaker status
 * - Recommendations
 */

import * as React from "react";
import { cn } from "../../lib/utils";
import { CheckCircle2, XCircle, AlertCircle, TrendingUp, Target, Briefcase, MapPin, DollarSign, Sparkles } from "lucide-react";

export interface MatchExplanationData {
    score: number;
    semantic_similarity: number;
    skill_match_ratio: number;
    experience_alignment: number;
    location_compatible: boolean;
    salary_in_range: boolean;
    matched_skills: string[];
    missing_skills: string[];
    reasoning: string;
    confidence: "low" | "medium" | "high";
}

export interface DealbreakerInfo {
    passed: boolean;
    reasons: string[];
}

export interface MatchExplanationProps {
    explanation: MatchExplanationData;
    dealbreakers?: DealbreakerInfo;
    className?: string;
    compact?: boolean;
}

function ScoreBar({ label, value, icon: Icon }: { label: string; value: number; icon?: React.ElementType }) {
    const percentage = Math.round(value * 100);
    const colorClass = percentage >= 80
        ? "bg-emerald-500"
        : percentage >= 60
            ? "bg-amber-500"
            : "bg-slate-400";

    return (
        <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 text-slate-600 font-medium">
                    {Icon && <Icon className="w-3.5 h-3.5" />}
                    {label}
                </span>
                <span className={cn(
                    "font-bold tabular-nums",
                    percentage >= 80 ? "text-emerald-600" : percentage >= 60 ? "text-amber-600" : "text-slate-500"
                )}>
                    {percentage}%
                </span>
            </div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                    className={cn("h-full rounded-full transition-all duration-500", colorClass)}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}

function SkillTag({ skill, matched }: { skill: string; matched: boolean }) {
    return (
        <span
            className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
                matched
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-slate-100 text-slate-500 border border-slate-200"
            )}
        >
            {matched ? (
                <CheckCircle2 className="w-3 h-3" />
            ) : (
                <AlertCircle className="w-3 h-3" />
            )}
            {skill}
        </span>
    );
}

export function MatchExplanation({
    explanation,
    dealbreakers,
    className,
    compact = false,
}: MatchExplanationProps) {
    const overallScore = Math.round(explanation.score * 100);
    const confidenceColor = explanation.confidence === "high"
        ? "text-emerald-600"
        : explanation.confidence === "medium"
            ? "text-amber-600"
            : "text-slate-500";

    if (compact) {
        return (
            <div className={cn("flex items-center gap-2", className)}>
                <div className={cn(
                    "flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold",
                    overallScore >= 80
                        ? "bg-emerald-50 text-emerald-700"
                        : overallScore >= 60
                            ? "bg-amber-50 text-amber-700"
                            : "bg-slate-100 text-slate-600"
                )}>
                    <Sparkles className="w-3 h-3" />
                    {overallScore}% Match
                </div>
                {dealbreakers && !dealbreakers.passed && (
                    <span className="text-xs text-red-500 font-medium">
                        {dealbreakers.reasons.length} dealbreaker(s)
                    </span>
                )}
            </div>
        );
    }

    return (
        <div className={cn("bg-white rounded-xl border border-slate-200 p-4 space-y-4", className)}>
            {/* Header with overall score */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className={cn(
                        "flex items-center justify-center w-10 h-10 rounded-xl",
                        overallScore >= 80
                            ? "bg-emerald-100"
                            : overallScore >= 60
                                ? "bg-amber-100"
                                : "bg-slate-100"
                    )}>
                        <Sparkles className={cn(
                            "w-5 h-5",
                            overallScore >= 80
                                ? "text-emerald-600"
                                : overallScore >= 60
                                    ? "text-amber-600"
                                    : "text-slate-500"
                        )} />
                    </div>
                    <div>
                        <div className="font-bold text-lg text-slate-900">{overallScore}% Match</div>
                        <div className={cn("text-xs font-medium uppercase tracking-wider", confidenceColor)}>
                            {explanation.confidence} confidence
                        </div>
                    </div>
                </div>
                {dealbreakers && (
                    <div className={cn(
                        "flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-bold",
                        dealbreakers.passed
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-red-50 text-red-700"
                    )}>
                        {dealbreakers.passed ? (
                            <>
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                Passes filters
                            </>
                        ) : (
                            <>
                                <XCircle className="w-3.5 h-3.5" />
                                {dealbreakers.reasons.length} dealbreaker(s)
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Score breakdown */}
            <div className="space-y-2">
                <ScoreBar
                    label="Semantic Match"
                    value={explanation.semantic_similarity}
                    icon={Target}
                />
                <ScoreBar
                    label="Skills Alignment"
                    value={explanation.skill_match_ratio}
                    icon={Briefcase}
                />
                <ScoreBar
                    label="Experience Fit"
                    value={explanation.experience_alignment}
                    icon={TrendingUp}
                />
            </div>

            {/* Skills breakdown */}
            {(explanation.matched_skills.length > 0 || explanation.missing_skills.length > 0) && (
                <div className="space-y-2">
                    <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                        Skills Analysis
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                        {explanation.matched_skills.map((skill) => (
                            <SkillTag key={skill} skill={skill} matched={true} />
                        ))}
                        {explanation.missing_skills.slice(0, 3).map((skill) => (
                            <SkillTag key={skill} skill={skill} matched={false} />
                        ))}
                    </div>
                </div>
            )}

            {/* Location & Salary indicators */}
            <div className="flex gap-3">
                <div className={cn(
                    "flex items-center gap-1.5 text-xs font-medium",
                    explanation.location_compatible ? "text-emerald-600" : "text-slate-400"
                )}>
                    <MapPin className="w-3.5 h-3.5" />
                    {explanation.location_compatible ? "Location OK" : "Location mismatch"}
                </div>
                <div className={cn(
                    "flex items-center gap-1.5 text-xs font-medium",
                    explanation.salary_in_range ? "text-emerald-600" : "text-slate-400"
                )}>
                    <DollarSign className="w-3.5 h-3.5" />
                    {explanation.salary_in_range ? "Salary in range" : "Salary unclear"}
                </div>
            </div>

            {/* AI Reasoning */}
            {explanation.reasoning && (
                <div className="pt-2 border-t border-slate-100">
                    <p className="text-sm text-slate-600 leading-relaxed">
                        {explanation.reasoning}
                    </p>
                </div>
            )}

            {/* Dealbreaker reasons */}
            {dealbreakers && !dealbreakers.passed && dealbreakers.reasons.length > 0 && (
                <div className="bg-red-50 rounded-lg p-3 space-y-1">
                    <div className="text-xs font-bold text-red-700 uppercase tracking-wider">
                        Why this job was filtered
                    </div>
                    <ul className="text-sm text-red-600 space-y-1">
                        {dealbreakers.reasons.map((reason, i) => (
                            <li key={i} className="flex items-start gap-2">
                                <XCircle className="w-4 h-4 mt-0.5 shrink-0" />
                                {reason}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

/**
 * Compact inline version for job cards and lists
 */
export function MatchScoreInline({
    score,
    confidence,
    passed,
    className,
}: {
    score: number;
    confidence: "low" | "medium" | "high";
    passed?: boolean;
    className?: string;
}) {
    const percentage = Math.round(score * 100);

    return (
        <div className={cn("flex items-center gap-2", className)}>
            <div className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold",
                percentage >= 80
                    ? "bg-emerald-50 text-emerald-700"
                    : percentage >= 60
                        ? "bg-amber-50 text-amber-700"
                        : "bg-slate-100 text-slate-600"
            )}>
                <Sparkles className="w-3 h-3" />
                {percentage}%
            </div>
            {passed === false && (
                <XCircle className="w-4 h-4 text-red-500" />
            )}
        </div>
    );
}
