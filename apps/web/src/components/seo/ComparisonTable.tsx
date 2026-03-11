import React from 'react';
import { Check, X, Minus } from 'lucide-react';

interface Competitor {
    name: string;
    features: Record<string, any>;
}

interface ComparisonTableProps {
    competitor: Competitor;
    variant?: 'full' | 'compact';
}

const FEATURE_LABELS: Record<string, string> = {
    auto_apply: 'Auto-Apply to Jobs',
    resume_tailoring: 'Resume Tailoring Per Application',
    cover_letter_gen: 'AI Cover Letter Generation',
    stealth_mode: 'Stealth Mode (Human-Like Browsing)',
    ai_agent: 'Autonomous AI Agent',
    browser_extension: 'Browser Extension',
    mobile_app: 'Mobile App',
    job_tracking: 'Job Application Tracking',
    ats_optimization: 'ATS Optimization',
};

const JOBHUNTIN_FEATURES: Record<string, boolean> = {
    auto_apply: true,
    resume_tailoring: true,
    cover_letter_gen: true,
    stealth_mode: true,
    ai_agent: true,
    browser_extension: true,
    mobile_app: true,
    job_tracking: true,
    ats_optimization: true,
};

function FeatureIcon({ value }: { value: boolean }) {
    if (value) {
        return (
            <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-emerald-50 text-emerald-600">
                <Check className="w-4 h-4" strokeWidth={3} />
            </span>
        );
    }
    return (
        <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-red-50 text-red-400">
            <X className="w-4 h-4" strokeWidth={3} />
        </span>
    );
}

export function ComparisonTable({ competitor, variant = 'full' }: ComparisonTableProps) {
    const features = variant === 'compact'
        ? Object.keys(FEATURE_LABELS).slice(0, 5)
        : Object.keys(FEATURE_LABELS);

    return (
        <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left" aria-label={`Feature comparison: JobHuntin vs ${competitor.name}`}>
                <thead>
                    <tr className="border-b border-slate-100 bg-slate-50/50">
                        <th scope="col" className="px-6 py-5 text-sm font-bold text-slate-500 uppercase tracking-wider">Feature</th>
                        <th scope="col" className="px-6 py-5 text-sm font-bold text-primary-600 uppercase tracking-wider text-center">
                            <span className="inline-flex items-center gap-2">
                                🦁 JobHuntin
                            </span>
                        </th>
                        <th scope="col" className="px-6 py-5 text-sm font-bold text-slate-400 uppercase tracking-wider text-center">
                            {competitor.name}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {features.map((featureKey, i) => (
                        <tr
                            key={featureKey}
                            className={`border-b border-slate-50 ${i % 2 === 0 ? 'bg-white' : 'bg-slate-50/30'} hover:bg-primary-50/30 transition-colors`}
                        >
                            <td className="px-6 py-4 text-sm font-medium text-slate-700">
                                {FEATURE_LABELS[featureKey]}
                            </td>
                            <td className="px-6 py-4 text-center">
                                <FeatureIcon value={JOBHUNTIN_FEATURES[featureKey]} />
                            </td>
                            <td className="px-6 py-4 text-center">
                                <FeatureIcon value={!!competitor.features[featureKey]} />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
