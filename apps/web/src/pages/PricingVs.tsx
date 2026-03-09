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
            answer: `JobHuntin starts free while ${competitor.name} starts at ${competitor.pricing.starts_at}. The $19 Pro plan includes unlimited tailored applications and stealth mode — more value per dollar.`,
        },
        {
            question: `Does ${competitor.name} have a free plan?`,
            answer: `${competitor.pricing.free_tier ? `Yes, ${competitor.name} offers a free tier with limits.` : `No, ${competitor.name} starts at ${competitor.pricing.starts_at}.`} JobHuntin offers a free plan so you can see real results before upgrading.`,
        },
        {
            question: `What's the best value between ${competitor.name} and JobHuntin?`,
            answer: `JobHuntin. You get autonomous AI, per-application tailoring, stealth mode, and job tracking in one plan. ${competitor.name}'s top tier still ${competitor.features.stealth_mode ? 'can\'t match that scope' : 'misses stealth mode and full automation'}.`,
        },
        {
            question: `Are there hidden fees with ${competitor.name}?`,
            answer: `${competitor.name} starts at ${competitor.pricing.starts_at} with multiple tiers and gated features. JobHuntin's Pro plan includes everything — no hidden fees or per-application charges.`,
        },
        {
            question: `Can I try JobHuntin before paying?`,
            answer: `Yes — the free plan lets you run the AI agent with no credit card. Most users upgrade within a week after seeing interview volume.`,
        },
    ];
}

export default function PricingVs() {
    const { competitorSlug } = useParams<{ competitorSlug: string }>();
    const competitor = competitorSlug ? COMPETITORS_MAP[competitorSlug] : null;

    if (!competitor) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-slate-50">
                <h2 className="text-2xl font-bold mb-4 text-slate-900">Tool Not Found</h2>
                <Link to="/best/ai-auto-apply-tools" className="text-primary-600 hover:underline flex items-center gap-2 font-medium">
                    <ArrowLeft className="w-4 h-4" /> Browse All Tools
                </Link>
            </div>
        );
    }

    const title = `${competitor.name} vs JobHuntin Pricing 2026 | Compare Plans & Value`;
    const description = `Compare ${competitor.name} pricing (starts at ${competitor.pricing.starts_at}) vs JobHuntin (free tier, $19/mo Pro). See which offers better value for AI auto-apply and resume tailoring.`;
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
                breadcrumbs={[
                    { name: "Home", url: "https://jobhuntin.com" },
                    { name: "Compare Tools", url: "https://jobhuntin.com/best/ai-auto-apply-tools" },
                    { name: competitor.name + " vs JobHuntin Pricing", url: canonicalUrl },
                ]}
                keywords={competitor.seo_keywords?.join(", ")}
                schema={[
                    {
                        "@context": "https://schema.org",
                        "@type": "WebPage",
                        "name": title,
                        "description": description,
                        "url": canonicalUrl,
                    },
                    {
                        "@context": "https://schema.org",
                        "@type": "ItemList",
                        "name": `${competitor.name} vs JobHuntin Pricing Comparison`,
                        "itemListOrder": "ItemListUnordered",
                        "numberOfItems": 2,
                        "itemListElement": [
                            {
                                "@type": "ListItem",
                                "position": 1,
                                "url": `https://${competitor.domain}`,
                                "name": competitor.name,
                                "item": {
                                    "@type": "SoftwareApplication",
                                    "name": competitor.name,
                                    "applicationCategory": "Job Search Automation",
                                    "operatingSystem": "Web"
                                }
                            },
                            {
                                "@type": "ListItem",
                                "position": 2,
                                "url": "https://jobhuntin.com",
                                "name": "JobHuntin",
                                "item": {
                                    "@type": "SoftwareApplication",
                                    "name": "JobHuntin",
                                    "applicationCategory": "Job Search Automation",
                                    "operatingSystem": "Web"
                                }
                            }
                        ]
                    },
                    // FAQPage Schema
                    {
                        "@context": "https://schema.org",
                        "@type": "FAQPage",
                        "mainEntity": faq.map(f => ({
                            "@type": "Question",
                            "name": f.question,
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": f.answer
                            }
                        }))
                    }
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
                    <h1 className="text-4xl md:text-6xl font-sans font-black mb-6 leading-tight text-slate-900">
                        {competitor.name} Pricing vs{' '}
                        <span className="text-primary-600 font-black">
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
