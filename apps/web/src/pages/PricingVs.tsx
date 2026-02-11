import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, DollarSign, ArrowRight, Check, X, Star, Minus } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { FAQAccordion, type FAQItem } from '../components/seo/FAQAccordion';
import { InternalLinkMesh } from '../components/seo/InternalLinkMesh';
import { ConversionCTA } from '../components/seo/ConversionCTA';
import { motion } from 'framer-motion';
import competitorsData from '../data/competitors.json';

const COMPETITORS_MAP: Record<string, typeof competitorsData[0]> = Object.fromEntries(
    competitorsData.map(c => [c.slug, c])
);

function generateFAQ(competitor: typeof competitorsData[0]): FAQItem[] {
    return [
        {
            question: `Is JobHuntin cheaper than ${competitor.name}?`,
            answer: `JobHuntin offers a free tier to get started, while ${competitor.name} starts at ${competitor.pricing.starts_at}. ${competitor.pricing.free_tier ? `Both offer free tiers, but` : `Unlike ${competitor.name},`} JobHuntin's free plan includes access to the autonomous AI agent. Pro plans deliver significantly more value per dollar with unlimited AI-tailored applications and stealth mode.`,
        },
        {
            question: `Does ${competitor.name} have a free plan?`,
            answer: `${competitor.pricing.free_tier ? `Yes, ${competitor.name} offers a free tier with limited features.` : `No, ${competitor.name} does not have a free plan — it starts at ${competitor.pricing.starts_at}.`} JobHuntin offers a free plan that lets you experience the autonomous AI agent before committing to a paid tier.`,
        },
        {
            question: `What's the best value between ${competitor.name} and JobHuntin?`,
            answer: `When comparing total value, JobHuntin provides more features per dollar: autonomous AI operation, per-application resume tailoring, stealth mode, cover letter generation, and job tracking — all included in the Pro plan. ${competitor.name}'s ${competitor.pricing.tiers?.[competitor.pricing.tiers.length - 1] ?? 'top tier'} still ${competitor.features.stealth_mode ? 'doesn\'t match' : 'lacks key features like stealth mode and full automation that'} JobHuntin includes.`,
        },
        {
            question: `Are there hidden fees with ${competitor.name}?`,
            answer: `${competitor.name} charges ${competitor.pricing.starts_at} with ${competitor.pricing.tiers?.length ?? 0} pricing tiers. Some features may only be available on higher tiers. JobHuntin's pricing is transparent — the Pro plan includes all features with no hidden fees, per-application charges, or surprise upgrades.`,
        },
        {
            question: `Can I try JobHuntin before paying?`,
            answer: `Yes! JobHuntin offers a generous free tier that gives you access to the AI agent so you can see real results before upgrading. No credit card required to start. Most users upgrade to Pro within the first week after seeing the quality and volume of applications.`,
        },
    ];
}

export default function PricingVs() {
    const { competitorSlug } = useParams<{ competitorSlug: string }>();
    const competitor = competitorSlug ? COMPETITORS_MAP[competitorSlug] : null;

    if (!competitor) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-slate-50">
                <h1 className="text-2xl font-bold mb-4 text-slate-900">Tool Not Found</h1>
                <Link to="/best/ai-auto-apply-tools" className="text-primary-600 hover:underline flex items-center gap-2 font-medium">
                    <ArrowLeft className="w-4 h-4" /> Browse All Tools
                </Link>
            </div>
        );
    }

    const title = `${competitor.name} Pricing vs JobHuntin (2026) — Which is Better Value?`;
    const description = `Compare ${competitor.name} pricing (starts at ${competitor.pricing.starts_at}) with JobHuntin (free to start). See which AI job tool offers better value for your money.`;
    const canonicalUrl = `https://jobhuntin.com/pricing-vs/${competitorSlug}`;
    const faq = generateFAQ(competitor);

    const JOBHUNTIN_TIERS = [
        {
            name: 'Free',
            price: '$0/mo',
            features: [
                'AI Job Agent (limited)',
                'Resume upload & analysis',
                'Basic job tracking',
                'Community support',
            ],
            missing: [
                'Unlimited applications',
                'Stealth Mode',
                'Resume tailoring',
                'Priority support',
            ],
        },
        {
            name: 'Pro',
            price: '$19/mo',
            popular: true,
            features: [
                'Unlimited AI applications',
                'Per-application resume tailoring',
                'AI cover letter generation',
                'Stealth Mode (human-like browsing)',
                'Full autonomous operation',
                'Chrome extension',
                'Advanced job tracking',
                'Priority support',
            ],
            missing: [],
        },
    ];

    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
            <SEO
                title={title}
                description={description}
                ogTitle={title}
                canonicalUrl={canonicalUrl}
                schema={[
                    {
                        "@context": "https://schema.org",
                        "@type": "WebPage",
                        "name": title,
                        "description": description,
                        "url": canonicalUrl,
                    },
                ]}
            />

            <main className="max-w-5xl mx-auto px-6 py-24">
                {/* Hero */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-20"
                >
                    <div className="inline-flex items-center gap-2 bg-green-50 text-green-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-green-100">
                        <DollarSign className="w-4 h-4" />
                        Pricing Breakdown
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black font-display mb-6 leading-tight text-slate-900">
                        {competitor.name} Pricing vs{' '}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-emerald-400">
                            JobHuntin
                        </span>
                    </h1>
                    <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
                        {competitor.name} starts at {competitor.pricing.starts_at}.
                        JobHuntin is free to start with Pro at $19/mo. See what you get for your money.
                    </p>
                </motion.div>

                {/* Side-by-Side Pricing */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-20 grid md:grid-cols-2 gap-8"
                >
                    {/* Competitor Pricing */}
                    <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
                        <h2 className="text-xl font-bold text-slate-500 mb-2">{competitor.name}</h2>
                        <p className="text-3xl font-black text-slate-900 mb-6">
                            {competitor.pricing.starts_at}
                            <span className="text-sm text-slate-400 font-medium ml-1">starting</span>
                        </p>
                        <div className="space-y-3 mb-6">
                            {(competitor.pricing.tiers ?? []).map((tier, i) => (
                                <div key={i} className="flex items-center gap-3 text-sm">
                                    <Minus className="w-4 h-4 text-slate-300" />
                                    <span className="text-slate-600 font-medium">{tier}</span>
                                </div>
                            ))}
                        </div>
                        <div className="border-t border-slate-100 pt-6">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">What's missing</h3>
                            <ul className="space-y-2">
                                {!competitor.features.stealth_mode && (
                                    <li className="flex items-center gap-2 text-sm text-red-500"><X className="w-4 h-4" /> Stealth Mode</li>
                                )}
                                {!competitor.features.resume_tailoring && (
                                    <li className="flex items-center gap-2 text-sm text-red-500"><X className="w-4 h-4" /> Per-app resume tailoring</li>
                                )}
                                {!competitor.features.ai_agent && (
                                    <li className="flex items-center gap-2 text-sm text-red-500"><X className="w-4 h-4" /> Autonomous AI agent</li>
                                )}
                                {!competitor.features.auto_apply && (
                                    <li className="flex items-center gap-2 text-sm text-red-500"><X className="w-4 h-4" /> Auto-apply</li>
                                )}
                            </ul>
                        </div>
                    </div>

                    {/* JobHuntin Pricing */}
                    <div className="bg-primary-50 rounded-3xl border-2 border-primary-200 p-8 shadow-sm relative">
                        <div className="absolute -top-3 right-6 bg-primary-600 text-white text-xs font-bold px-4 py-1 rounded-full flex items-center gap-1">
                            <Star className="w-3 h-3 fill-white" /> BEST VALUE
                        </div>
                        <h2 className="text-xl font-bold text-primary-700 mb-2">JobHuntin</h2>
                        <p className="text-3xl font-black text-slate-900 mb-6">
                            Free
                            <span className="text-sm text-slate-400 font-medium ml-1">to start</span>
                        </p>
                        <div className="space-y-4">
                            {JOBHUNTIN_TIERS.map((tier, i) => (
                                <div key={i} className="bg-white rounded-2xl p-5 border border-primary-100">
                                    <div className="flex items-center justify-between mb-3">
                                        <span className="font-bold text-slate-900">{tier.name}</span>
                                        <span className="text-primary-600 font-bold">{tier.price}</span>
                                    </div>
                                    <ul className="space-y-1.5">
                                        {tier.features.map((f, j) => (
                                            <li key={j} className="flex items-center gap-2 text-sm text-slate-600">
                                                <Check className="w-4 h-4 text-emerald-500" />
                                                <span className="font-medium">{f}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>
                        <Link
                            to="/pricing"
                            className="block text-center mt-6 text-primary-600 font-bold text-sm hover:underline"
                        >
                            See full pricing details →
                        </Link>
                    </div>
                </motion.div>

                {/* Value Comparison Table */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-20"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-6">What You Get for Your Money</h2>
                    <div className="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-slate-100 bg-slate-50/50">
                                    <th className="px-6 py-4 text-left text-sm font-bold text-slate-500">Included Feature</th>
                                    <th className="px-6 py-4 text-center text-sm font-bold text-primary-600">JobHuntin Pro</th>
                                    <th className="px-6 py-4 text-center text-sm font-bold text-slate-400">{competitor.name}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[
                                    ['Autonomous AI Agent', true, competitor.features.ai_agent],
                                    ['Per-Application Resume Tailoring', true, competitor.features.resume_tailoring],
                                    ['Stealth Mode', true, competitor.features.stealth_mode],
                                    ['Auto-Apply', true, competitor.features.auto_apply],
                                    ['Cover Letter Generation', true, competitor.features.cover_letter_gen],
                                    ['ATS Optimization', true, competitor.features.ats_optimization],
                                    ['Job Tracking Dashboard', true, competitor.features.job_tracking],
                                    ['Chrome Extension', true, competitor.features.browser_extension],
                                    ['Mobile App', true, competitor.features.mobile_app],
                                ].map(([feature, jh, comp], i) => (
                                    <tr key={i} className={`border-b border-slate-50 ${i % 2 === 0 ? '' : 'bg-slate-50/30'}`}>
                                        <td className="px-6 py-3 text-sm font-medium text-slate-700">{feature as string}</td>
                                        <td className="px-6 py-3 text-center">
                                            {jh ? (
                                                <Check className="w-5 h-5 text-emerald-500 mx-auto" />
                                            ) : (
                                                <X className="w-5 h-5 text-red-400 mx-auto" />
                                            )}
                                        </td>
                                        <td className="px-6 py-3 text-center">
                                            {comp ? (
                                                <Check className="w-5 h-5 text-emerald-500 mx-auto" />
                                            ) : (
                                                <X className="w-5 h-5 text-red-400 mx-auto" />
                                            )}
                                        </td>
                                    </tr>
                                ))}
                                <tr className="bg-primary-50 border-t-2 border-primary-200">
                                    <td className="px-6 py-4 text-sm font-bold text-slate-900">Monthly Price</td>
                                    <td className="px-6 py-4 text-center text-lg font-black text-primary-600">$19/mo</td>
                                    <td className="px-6 py-4 text-center text-lg font-bold text-slate-500">{competitor.pricing.starts_at}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </motion.div>

                {/* FAQ */}
                <FAQAccordion items={faq} competitorName={competitor.name} />

                {/* Internal Links */}
                <InternalLinkMesh
                    currentSlug={competitorSlug!}
                    currentType="pricing"
                    competitorCategory={competitor.category}
                />

                {/* CTA */}
                <ConversionCTA competitorName={competitor.name} variant="compare" />
            </main>


        </div>
    );
}
