import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, ArrowRight, Star, CheckCircle2, XCircle } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { ComparisonTable } from '../components/seo/ComparisonTable';
import { FAQAccordion, type FAQItem } from '../components/seo/FAQAccordion';
import { InternalLinkMesh } from '../components/seo/InternalLinkMesh';
import { ConversionCTA } from '../components/seo/ConversionCTA';
import { motion } from 'framer-motion';
import competitorsData from '../data/competitors.json';

const COMPETITORS_MAP = Object.fromEntries(
    competitorsData.map(c => [c.slug, c])
);

function generateFAQ(competitor: typeof competitorsData[0]): FAQItem[] {
    return [
        {
            question: `What is the best ${competitor.name} alternative in 2026?`,
            answer: `JobHuntin. It's a fully autonomous AI agent that discovers jobs, tailors your resume per application, and submits with stealth browsing — all in the background while you sleep.`,
        },
        {
            question: `Why are people switching from ${competitor.name}?`,
            answer: `${competitor.weaknesses.slice(0, 2).join('. ')}. JobHuntin fixes all of that with autonomous operation and per-application resume tailoring.`,
        },
        {
            question: `Is JobHuntin free like ${competitor.name}?`,
            answer: `${competitor.pricing.free_tier ? `Both offer free tiers, but JobHuntin's free plan includes AI resume tailoring.` : `JobHuntin offers a free tier — ${competitor.name} starts at ${competitor.pricing.starts_at}.`} Upgrade to Pro ($19/mo) for unlimited applications with full stealth mode.`,
        },
        {
            question: `How does JobHuntin compare to ${competitor.name} for volume?`,
            answer: `${competitor.features.auto_apply ? `${competitor.name} auto-applies but sends generic apps.` : `${competitor.name} doesn't even auto-apply.`} JobHuntin tailors every resume, cover letter, and form response — at higher volume than any competitor.`,
        },
        {
            question: `Can I use JobHuntin and ${competitor.name} together?`,
            answer: `You can, but most users drop ${competitor.name} within a week. JobHuntin handles the entire pipeline from discovery to tailored submission — there's nothing left for another tool to do.`,
        },
    ];
}

export default function AlternativeTo() {
    const { competitorSlug } = useParams<{ competitorSlug: string }>();
    const competitor = competitorSlug ? COMPETITORS_MAP[competitorSlug] : null;

    if (!competitor) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-slate-50">
                <h2 className="text-2xl font-bold mb-4 text-slate-900">Tool Not Found</h2>
                <Link to="/best/ai-auto-apply-tools" className="text-primary-600 hover:underline flex items-center gap-2 font-medium">
                    <ArrowLeft className="w-4 h-4" /> Browse All Alternatives
                </Link>
            </div>
        );
    }

    const title = `Best ${competitor.name} Alternative 2026 | JobHuntin Auto-Apply & Resume Tailoring`;
    const description = `Looking for a ${competitor.name} alternative? JobHuntin offers autonomous AI auto-apply, per-application resume tailoring, and stealth mode. Compare features and pricing.`;
    const canonicalUrl = `https://jobhuntin.com/alternative-to/${competitorSlug}`;
    const faq = generateFAQ(competitor);

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
                    {
                        "@context": "https://schema.org",
                        "@type": "ItemList",
                        "name": `Best ${competitor.name} Alternatives`,
                        "numberOfItems": 1,
                        "itemListElement": [
                            {
                                "@type": "ListItem",
                                "position": 1,
                                "name": "JobHuntin",
                                "url": "https://jobhuntin.com",
                                "description": "Autonomous AI job search automation with stealth mode and resume tailoring",
                            },
                        ],
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
                    },
                    // Product Schema
                    {
                        "@context": "https://schema.org",
                        "@type": "Product",
                        "name": "JobHuntin",
                        "description": "AI-powered job search automation with auto-apply, resume tailoring, and stealth mode",
                        "brand": { "@type": "Brand", "name": "JobHuntin" },
                        "offers": {
                            "@type": "Offer",
                            "price": "19",
                            "priceCurrency": "USD",
                            "availability": "https://schema.org/InStock"
                        }
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
                    <div className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-emerald-100">
                        <Sparkles className="w-4 h-4" />
                        #1 Alternative
                    </div>
                    <h1 className="text-4xl md:text-6xl font-sans font-black mb-6 leading-tight text-slate-900">
                        The Best{' '}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-emerald-400">
                            {competitor.name}
                        </span>
                        {' '}Alternative
                    </h1>
                    <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
                        {competitor.status === 'discontinued'
                            ? `${competitor.name} is no longer available. JobHuntin is the top alternative with autonomous AI-powered job hunting.`
                            : `Stop settling for ${competitor.name}'s limitations. Upgrade to fully autonomous job hunting with JobHuntin.`
                        }
                    </p>
                </motion.div>

                {/* Why Switch Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-20"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-8">
                        Why Switch from {competitor.name} to JobHuntin?
                    </h2>

                    <div className="grid md:grid-cols-2 gap-6">
                        {/* What you lose */}
                        <div className="bg-white rounded-3xl border border-slate-100 p-8">
                            <h3 className="text-lg font-bold text-slate-400 mb-6 flex items-center gap-2">
                                <XCircle className="w-5 h-5 text-red-400" />
                                What {competitor.name} lacks
                            </h3>
                            <ul className="space-y-4">
                                {competitor.weaknesses.map((w, i) => (
                                    <li key={i} className="flex items-start gap-3 text-sm text-slate-600">
                                        <span className="text-red-400 mt-0.5 flex-shrink-0">✕</span>
                                        <span className="font-medium">{w}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* What you gain */}
                        <div className="bg-primary-50 rounded-3xl border border-primary-200 p-8">
                            <h3 className="text-lg font-bold text-primary-700 mb-6 flex items-center gap-2">
                                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                                What JobHuntin delivers
                            </h3>
                            <ul className="space-y-4">
                                {competitor.differentiators.map((d, i) => (
                                    <li key={i} className="flex items-start gap-3 text-sm text-slate-700">
                                        <span className="text-emerald-500 mt-0.5 flex-shrink-0">✓</span>
                                        <span className="font-medium">{d}</span>
                                    </li>
                                ))}
                                <li className="flex items-start gap-3 text-sm text-slate-700">
                                    <span className="text-emerald-500 mt-0.5 flex-shrink-0">✓</span>
                                    <span className="font-medium">Chrome extension for real-time job capture from any site</span>
                                </li>
                                <li className="flex items-start gap-3 text-sm text-slate-700">
                                    <span className="text-emerald-500 mt-0.5 flex-shrink-0">✓</span>
                                    <span className="font-medium">AI cover letters crafted for each specific job description</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </motion.div>

                {/* Feature Table */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-20"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-6">
                        Feature-by-Feature Comparison
                    </h2>
                    <ComparisonTable competitor={competitor} />
                </motion.div>

                {/* Verdict */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-20 bg-white rounded-3xl border border-slate-100 p-10 shadow-sm text-center"
                >
                    <div className="flex items-center justify-center gap-1 mb-4">
                        {[1, 2, 3, 4, 5].map(star => (
                            <Star key={star} className="w-6 h-6 text-amber-400 fill-amber-400" />
                        ))}
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-4">Our Verdict</h2>
                    <p className="text-lg text-slate-600 max-w-2xl mx-auto font-medium leading-relaxed">
                        {competitor.verdict}
                    </p>
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-2 mt-8 bg-primary-600 hover:bg-primary-700 text-white px-8 py-4 rounded-2xl font-bold text-lg shadow-lg shadow-primary-500/20 transition-colors"
                    >
                        Try JobHuntin Free <ArrowRight className="w-5 h-5" />
                    </Link>
                </motion.div>

                {/* FAQ */}
                <FAQAccordion items={faq} competitorName={competitor.name} />

                {/* Internal Links */}
                <InternalLinkMesh
                    currentSlug={competitorSlug!}
                    currentType="alternative"
                    competitorCategory={competitor.category}
                />

                {/* CTA */}
                <ConversionCTA competitorName={competitor.name} variant="switch" />
            </main>


        </div>
    );
}
