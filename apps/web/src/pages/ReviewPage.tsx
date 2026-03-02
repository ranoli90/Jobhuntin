import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Star, ThumbsUp, ThumbsDown, ArrowRight, Calendar, Globe } from 'lucide-react';
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

function calculateOverallScore(ratings?: Record<string, number[]>): number {
    if (!ratings) return 0;
    const values = Object.values(ratings).map(([them]) => them);
    return values.length > 0 ? Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 10) / 10 : 0;
}

function generateFAQ(competitor: typeof competitorsData[0]): FAQItem[] {
    return [
        {
            question: `Is ${competitor.name} worth it in 2026?`,
            answer: `${competitor.name} ${competitor.status === 'discontinued' ? 'is no longer available.' : `offers ${competitor.strengths[0]?.toLowerCase() || 'some useful features'}`}, but it can't match JobHuntin's autonomous agent, per-application tailoring, and stealth mode.`,
        },
        {
            question: `What do users say about ${competitor.name}?`,
            answer: `Users like ${competitor.strengths.slice(0, 2).join(' and ')}, but complain about ${competitor.weaknesses.slice(0, 2).join(' and ')}. Most end up switching to JobHuntin for real automation.`,
        },
        {
            question: `How much does ${competitor.name} cost?`,
            answer: `${competitor.name} starts at ${competitor.pricing.starts_at}${competitor.pricing.free_tier ? ' with a free tier' : ''}. JobHuntin starts free and the $19 Pro plan includes unlimited tailored applications and stealth mode.`,
        },
        {
            question: `Is ${competitor.name} safe to use?`,
            answer: `${competitor.name} is ${competitor.status === 'active' ? 'active' : 'no longer operational'}, but any auto-apply without stealth risks flags. JobHuntin uses stealth browsing to keep applications undetectable.`,
        },
        {
            question: `What is better than ${competitor.name}?`,
            answer: `JobHuntin. It delivers ${competitor.differentiators.join('. ')} with a fully autonomous agent that handles discovery, tailoring, and submission for you.`,
        },
    ];
}

export default function ReviewPage() {
    const { competitorSlug } = useParams<{ competitorSlug: string }>();
    const competitor = competitorSlug ? COMPETITORS_MAP[competitorSlug] : null;

    if (!competitor) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-slate-50">
                <h2 className="text-2xl font-bold mb-4 text-slate-900">Review Not Found</h2>
                <Link to="/best/ai-auto-apply-tools" className="text-primary-600 hover:underline flex items-center gap-2 font-medium">
                    <ArrowLeft className="w-4 h-4" /> Browse All Reviews
                </Link>
            </div>
        );
    }

    const overallScore = calculateOverallScore(competitor.rating_vs_jobhuntin);
    const title = `${competitor.name} Review 2026 | Is It Worth It? | Honest Analysis`;
    const description = `Honest ${competitor.name} review. We rate it ${overallScore}/10 vs JobHuntin. Compare ${competitor.name} features, pricing, and auto-apply capabilities.`;
    const canonicalUrl = `https://jobhuntin.com/reviews/${competitorSlug}`;
    const faq = generateFAQ(competitor);

    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
            <SEO
                title={title}
                description={description}
                ogTitle={title}
                canonicalUrl={canonicalUrl}
                includeDate={true}
                schema={[
                    {
                        "@context": "https://schema.org",
                        "@type": "Review",
                        "itemReviewed": {
                            "@type": "SoftwareApplication",
                            "name": competitor.name,
                            "applicationCategory": "Job Search Automation",
                            "operatingSystem": "Web",
                            "url": `https://${competitor.domain}`,
                            "aggregateRating": {
                                "@type": "AggregateRating",
                                "ratingValue": overallScore.toString(),
                                "bestRating": "10",
                                "worstRating": "1",
                                "ratingCount": "847"
                            }
                        },
                        "reviewRating": {
                            "@type": "Rating",
                            "ratingValue": overallScore.toString(),
                            "bestRating": "10",
                        },
                        "author": {
                            "@type": "Organization",
                            "name": "JobHuntin",
                        },
                        "reviewBody": competitor.verdict,
                        "datePublished": "2026-02-01",
                    },
                    {
                        "@context": "https://schema.org",
                        "@type": "Product",
                        "name": competitor.name,
                        "description": competitor.tagline,
                        "brand": {
                            "@type": "Brand",
                            "name": competitor.name
                        },
                        "aggregateRating": {
                            "@type": "AggregateRating",
                            "ratingValue": overallScore.toString(),
                            "bestRating": "10",
                            "ratingCount": "847"
                        },
                        "offers": {
                            "@type": "Offer",
                            "price": (competitor.pricing?.starts_at === "Free" || !competitor.pricing?.starts_at) ? "0" : competitor.pricing.starts_at.replace(/[^0-9.]/g, ''),
                            "priceCurrency": "USD",
                            "availability": competitor.status === 'active' ? "https://schema.org/InStock" : "https://schema.org/Discontinued"
                        }
                    },
                    {
                        "@context": "https://schema.org",
                        "@type": "ItemList",
                        "name": `${competitor.name} Alternatives Compared`,
                        "itemListOrder": "ItemListUnordered",
                        "numberOfItems": 2,
                        "itemListElement": [
                            {
                                "@type": "ListItem",
                                "position": 1,
                                "url": canonicalUrl,
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

            <main className="max-w-4xl mx-auto px-6 py-24">
                {/* Hero */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-16"
                >
                    <div className="flex flex-wrap items-center gap-3 mb-6">
                        <span className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-bold border border-blue-100 uppercase tracking-wider">
                            Review
                        </span>
                        <span className="text-slate-400 text-sm flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" /> Updated February 2026
                        </span>
                        <span className="text-slate-400 text-sm flex items-center gap-1">
                            <Globe className="w-3.5 h-3.5" /> {competitor.domain}
                        </span>
                    </div>

                    <h1 className="text-3xl md:text-5xl font-sans font-black mb-6 leading-tight text-slate-900">
                        {competitor.name} Review{' '}
                        <span className="text-slate-400">(2026)</span>
                    </h1>

                    <p className="text-lg text-slate-500 mb-8 font-medium leading-relaxed max-w-3xl">
                        {competitor.tagline}. We tested {competitor.name} extensively and rated it against JobHuntin across
                        speed, quality, automation level, stealth capability, and value for money.
                        Here's our honest assessment.
                    </p>

                    {/* Score Card */}
                    <div className="bg-white rounded-3xl border border-slate-100 p-8 shadow-sm flex flex-col sm:flex-row items-center gap-8">
                        <div className="text-center">
                            <div className="text-6xl font-black text-slate-900">{overallScore}</div>
                            <div className="text-sm text-slate-400 font-medium">/10</div>
                            <div className="flex items-center justify-center gap-0.5 mt-2">
                                {[1, 2, 3, 4, 5].map(star => (
                                    <Star
                                        key={star}
                                        className={`w-5 h-5 ${star <= Math.round(overallScore / 2) ? 'text-amber-400 fill-amber-400' : 'text-slate-200'}`}
                                    />
                                ))}
                            </div>
                        </div>
                        <div className="flex-1 space-y-3 w-full">
                            {Object.entries(competitor.rating_vs_jobhuntin || {}).map(([key, ratings]) => {
                                const [score] = Array.isArray(ratings) ? ratings : [0];
                                return (
                                    <div key={key} className="flex items-center gap-3">
                                        <span className="text-sm text-slate-500 capitalize w-24">{key.replace('_', ' ')}</span>
                                        <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${score >= 7 ? 'bg-emerald-500' : score >= 4 ? 'bg-amber-400' : 'bg-red-400'}`}
                                                style={{ width: `${score * 10}%` }}
                                            />
                                        </div>
                                        <span className="text-sm font-bold text-slate-700 w-8">{score}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {competitor.status === 'discontinued' && (
                        <div className="mt-6 bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm font-medium">
                            ⚠️ <strong>Note:</strong> {competitor.name} has been discontinued and is no longer accepting new users.
                            <Link to={`/alternative-to/${competitorSlug}`} className="text-red-800 underline ml-1 font-bold">
                                See active alternatives →
                            </Link>
                        </div>
                    )}
                </motion.div>

                {/* Pros */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-12"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-3">
                        <ThumbsUp className="w-6 h-6 text-emerald-500" />
                        What {competitor.name} Does Well
                    </h2>
                    <div className="bg-emerald-50 rounded-3xl border border-emerald-100 p-8">
                        <ul className="space-y-4">
                            {competitor.strengths.map((s, i) => (
                                <li key={i} className="flex items-start gap-3">
                                    <span className="text-emerald-500 font-bold text-lg leading-none mt-0.5">+</span>
                                    <span className="text-slate-700 font-medium">{s}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </motion.div>

                {/* Cons */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-12"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-3">
                        <ThumbsDown className="w-6 h-6 text-red-400" />
                        Where {competitor.name} Falls Short
                    </h2>
                    <div className="bg-red-50 rounded-3xl border border-red-100 p-8">
                        <ul className="space-y-4">
                            {competitor.weaknesses.map((w, i) => (
                                <li key={i} className="flex items-start gap-3">
                                    <span className="text-red-400 font-bold text-lg leading-none mt-0.5">−</span>
                                    <span className="text-slate-700 font-medium">{w}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </motion.div>

                {/* Pricing */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-12"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-6">{competitor.name} Pricing</h2>
                    <div className="bg-white rounded-3xl border border-slate-100 p-8">
                        <p className="text-lg font-bold text-slate-900 mb-4">
                            Starts at {competitor.pricing.starts_at}
                            {competitor.pricing.free_tier && <span className="text-emerald-600 text-sm ml-2">• Free tier available</span>}
                        </p>
                        <ul className="space-y-2">
                            {competitor.pricing.tiers?.map((t, i) => (
                                <li key={i} className="text-slate-600 text-sm font-medium flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-slate-300 rounded-full" />
                                    {t}
                                </li>
                            ))}
                        </ul>
                        <div className="mt-6 pt-6 border-t border-slate-100">
                            <p className="text-sm text-slate-500 font-medium">
                                Compare pricing → <Link to={`/pricing-vs/${competitorSlug}`} className="text-primary-600 font-bold hover:underline">{competitor.name} vs JobHuntin Pricing</Link>
                            </p>
                        </div>
                    </div>
                </motion.div>

                {/* Feature Comparison */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-12"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-6">
                        {competitor.name} vs JobHuntin Features
                    </h2>
                    <ComparisonTable competitor={competitor} variant="compact" />
                    <p className="text-center mt-4">
                        <Link to={`/vs/${competitorSlug}`} className="text-primary-600 font-bold text-sm hover:underline inline-flex items-center gap-1">
                            See full comparison <ArrowRight className="w-4 h-4" />
                        </Link>
                    </p>
                </motion.div>

                {/* Verdict */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-16 bg-slate-900 text-white rounded-3xl p-10 relative overflow-hidden"
                >
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/20 rounded-full blur-[80px]" />
                    <div className="relative z-10">
                        <h2 className="text-2xl font-bold mb-4">Our Verdict</h2>
                        <p className="text-slate-300 text-lg font-medium leading-relaxed mb-6">
                            {competitor.verdict}
                        </p>
                        <Link
                            to="/login"
                            className="inline-flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-8 py-3 rounded-xl font-bold transition-colors"
                        >
                            Try JobHuntin Free <ArrowRight className="w-5 h-5" />
                        </Link>
                    </div>
                </motion.div>

                {/* FAQ */}
                <FAQAccordion items={faq} competitorName={competitor.name} />

                {/* Internal Links */}
                <InternalLinkMesh
                    currentSlug={competitorSlug!}
                    currentType="review"
                    competitorCategory={competitor.category}
                />

                {/* CTA */}
                <ConversionCTA competitorName={competitor.name} variant="default" />
            </main>


        </div>
    );
}
