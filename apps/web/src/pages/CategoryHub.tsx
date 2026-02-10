import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Trophy, Star, Sparkles, Check, X } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { FAQAccordion, type FAQItem } from '../components/seo/FAQAccordion';
import { ConversionCTA } from '../components/seo/ConversionCTA';
import { motion } from 'framer-motion';
import competitorsData from '../data/competitors.json';
import categoriesData from '../data/categories.json';

const CATEGORIES_MAP = Object.fromEntries(
    categoriesData.map(c => [c.slug, c])
);

const COMPETITORS_MAP = Object.fromEntries(
    competitorsData.map(c => [c.slug, c])
);

function generateFAQ(category: typeof categoriesData[0]): FAQItem[] {
    const toolNames = category.competitors
        .map(slug => COMPETITORS_MAP[slug]?.name)
        .filter(Boolean)
        .slice(0, 5);

    return [
        {
            question: `What is the best ${category.name.toLowerCase()} in 2026?`,
            answer: `JobHuntin is the best ${category.name.toLowerCase()} in 2026 for job seekers who want fully autonomous AI-powered applications. Other notable tools include ${toolNames.join(', ')}. JobHuntin stands out with its stealth mode, per-application resume tailoring, and background autonomous operation.`,
        },
        {
            question: `Are ${category.name.toLowerCase()} worth it?`,
            answer: `Yes, ${category.name.toLowerCase()} can dramatically increase your interview rate by automating the most time-consuming part of job searching — the application itself. Users of tools like JobHuntin report landing 3x more interviews within 14 days of starting. The key is choosing a tool with quality-focused automation, not just volume.`,
        },
        {
            question: `Which ${category.name.toLowerCase()} are free?`,
            answer: `Several ${category.name.toLowerCase()} offer free tiers: ${category.competitors.filter(slug => COMPETITORS_MAP[slug]?.pricing.free_tier).map(slug => COMPETITORS_MAP[slug]?.name).filter(Boolean).join(', ') || 'limited options available'}. JobHuntin also offers a free tier that includes access to the AI agent. For unlimited applications with stealth mode, Pro plans start at $19/month.`,
        },
        {
            question: `Can ${category.name.toLowerCase()} get me banned from job boards?`,
            answer: `Some ${category.name.toLowerCase()} that lack stealth capabilities can trigger bot detection on job boards. JobHuntin solves this with Stealth Mode — simulating human-like browsing patterns, random delays, and natural cursor movements. This makes your automated applications indistinguishable from manual ones.`,
        },
        {
            question: `How do I choose the right ${category.name.toLowerCase().replace(' in 2026', '')}?`,
            answer: `Look for: 1) Autonomous operation (works without your active involvement), 2) Per-application customization (tailored resumes and cover letters), 3) Stealth capabilities (avoids bot detection), 4) Broad platform coverage (works across multiple job boards), and 5) Transparent pricing. JobHuntin checks all five boxes.`,
        },
    ];
}

export default function CategoryHub() {
    const { categorySlug } = useParams<{ categorySlug: string }>();
    const category = categorySlug ? CATEGORIES_MAP[categorySlug] : null;

    if (!category) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-slate-50">
                <h1 className="text-2xl font-bold mb-4 text-slate-900">Category Not Found</h1>
                <Link to="/" className="text-primary-600 hover:underline flex items-center gap-2 font-medium">
                    <ArrowLeft className="w-4 h-4" /> Back to Home
                </Link>
            </div>
        );
    }

    const competitors = category.competitors
        .map(slug => COMPETITORS_MAP[slug])
        .filter(Boolean);

    const title = `${category.h1} — Compared & Ranked`;
    const description = `${category.description}. Compare ${competitors.length}+ tools including ${competitors.slice(0, 3).map(c => c.name).join(', ')} and see why JobHuntin tops the list.`;
    const canonicalUrl = `https://jobhuntin.com/best/${categorySlug}`;
    const faq = generateFAQ(category);

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
                        "@type": "CollectionPage",
                        "name": title,
                        "description": description,
                        "url": canonicalUrl,
                    },
                    {
                        "@context": "https://schema.org",
                        "@type": "ItemList",
                        "name": category.h1,
                        "numberOfItems": competitors.length + 1,
                        "itemListElement": [
                            {
                                "@type": "ListItem",
                                "position": 1,
                                "name": "JobHuntin",
                                "url": "https://jobhuntin.com",
                                "description": "Autonomous AI job hunt automation with stealth mode and resume tailoring",
                            },
                            ...competitors.map((c, i) => ({
                                "@type": "ListItem",
                                "position": i + 2,
                                "name": c.name,
                                "url": `https://jobhuntin.com/vs/${c.slug}`,
                                "description": c.tagline,
                            })),
                        ],
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
                    <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-amber-100">
                        <Trophy className="w-4 h-4" />
                        Updated February 2026
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black font-display mb-6 leading-tight text-slate-900">
                        {category.h1}
                    </h1>
                    <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
                        {category.description}. We tested {competitors.length}+ tools and ranked them by
                        automation level, quality, stealth capability, and value.
                    </p>
                </motion.div>

                {/* #1 Pick — JobHuntin */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-12"
                >
                    <div className="bg-primary-50 rounded-3xl border-2 border-primary-200 p-8 md:p-10 relative overflow-hidden">
                        <div className="absolute top-4 right-4 bg-primary-600 text-white text-xs font-bold px-4 py-1.5 rounded-full flex items-center gap-1">
                            <Trophy className="w-3.5 h-3.5" /> #1 PICK
                        </div>
                        <div className="flex flex-col md:flex-row gap-8 items-start">
                            <div className="flex-1">
                                <h2 className="text-2xl font-black text-slate-900 mb-2">JobHuntin</h2>
                                <p className="text-slate-500 font-medium mb-4">
                                    Autonomous AI job search automation with stealth mode, per-application resume tailoring,
                                    and 24/7 background operation. The most comprehensive tool in this category.
                                </p>
                                <div className="flex items-center gap-1 mb-4">
                                    {[1, 2, 3, 4, 5].map(s => (
                                        <Star key={s} className="w-5 h-5 text-amber-400 fill-amber-400" />
                                    ))}
                                    <span className="text-sm text-slate-500 font-bold ml-2">10/10</span>
                                </div>
                                <div className="flex flex-wrap gap-2 mb-6">
                                    {['Auto-Apply', 'Resume Tailoring', 'Stealth Mode', 'AI Agent', 'Chrome Extension'].map(tag => (
                                        <span key={tag} className="bg-white text-primary-600 text-xs font-bold px-3 py-1 rounded-full border border-primary-100">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                                <div className="flex items-center gap-2 text-sm font-bold text-primary-600">
                                    <span>Free to start</span>
                                    <span className="text-slate-300">|</span>
                                    <span>Pro $19/mo</span>
                                </div>
                            </div>
                            <div className="flex-shrink-0">
                                <Link
                                    to="/login"
                                    className="inline-flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-8 py-4 rounded-2xl font-bold text-lg shadow-lg shadow-primary-500/20 transition-colors"
                                >
                                    Try Free <ArrowRight className="w-5 h-5" />
                                </Link>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Competitor List */}
                <div className="space-y-6 mb-20">
                    {competitors.map((comp, i) => {
                        const score = Math.round(
                            Object.values(comp.rating_vs_jobhuntin).reduce(
                                (sum, [them]) => sum + them, 0
                            ) / Object.keys(comp.rating_vs_jobhuntin).length * 10
                        ) / 10;

                        return (
                            <motion.div
                                key={comp.slug}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.05 }}
                                className="bg-white rounded-3xl border border-slate-100 p-8 shadow-sm hover:shadow-md transition-shadow"
                            >
                                <div className="flex flex-col md:flex-row gap-6 items-start">
                                    <div className="flex-shrink-0 w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center text-slate-500 font-black text-lg">
                                        #{i + 2}
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h2 className="text-xl font-bold text-slate-900">{comp.name}</h2>
                                            {comp.status === 'discontinued' && (
                                                <span className="text-xs font-bold text-red-500 bg-red-50 px-2 py-0.5 rounded-full border border-red-100">
                                                    Discontinued
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-slate-500 font-medium mb-3">{comp.tagline}</p>
                                        <div className="flex items-center gap-1 mb-3">
                                            {[1, 2, 3, 4, 5].map(s => (
                                                <Star
                                                    key={s}
                                                    className={`w-4 h-4 ${s <= Math.round(score / 2) ? 'text-amber-400 fill-amber-400' : 'text-slate-200'}`}
                                                />
                                            ))}
                                            <span className="text-sm text-slate-500 font-bold ml-1">{score}/10</span>
                                        </div>
                                        <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                                            <span className="flex items-center gap-1">
                                                {comp.features.auto_apply ? <Check className="w-4 h-4 text-emerald-500" /> : <X className="w-4 h-4 text-red-400" />}
                                                Auto-Apply
                                            </span>
                                            <span className="flex items-center gap-1">
                                                {comp.features.resume_tailoring ? <Check className="w-4 h-4 text-emerald-500" /> : <X className="w-4 h-4 text-red-400" />}
                                                Resume Tailoring
                                            </span>
                                            <span className="flex items-center gap-1">
                                                {comp.features.stealth_mode ? <Check className="w-4 h-4 text-emerald-500" /> : <X className="w-4 h-4 text-red-400" />}
                                                Stealth Mode
                                            </span>
                                            <span className="flex items-center gap-1">
                                                {comp.features.ai_agent ? <Check className="w-4 h-4 text-emerald-500" /> : <X className="w-4 h-4 text-red-400" />}
                                                AI Agent
                                            </span>
                                        </div>
                                        <p className="mt-3 text-sm text-slate-500 font-medium">
                                            Starting at {comp.pricing.starts_at}
                                            {comp.pricing.free_tier && ' • Free tier available'}
                                        </p>
                                    </div>
                                    <div className="flex flex-col gap-2 flex-shrink-0">
                                        <Link
                                            to={`/vs/${comp.slug}`}
                                            className="text-sm font-bold text-primary-600 hover:text-primary-700 flex items-center gap-1"
                                        >
                                            Full Comparison <ArrowRight className="w-4 h-4" />
                                        </Link>
                                        <Link
                                            to={`/reviews/${comp.slug}`}
                                            className="text-sm font-bold text-slate-500 hover:text-slate-700 flex items-center gap-1"
                                        >
                                            Read Review <ArrowRight className="w-4 h-4" />
                                        </Link>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Cross-link to other categories */}
                <div className="mb-16">
                    <h2 className="text-2xl font-bold text-slate-900 mb-6">Browse Other Categories</h2>
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {categoriesData
                            .filter(cat => cat.slug !== categorySlug)
                            .map(cat => (
                                <Link
                                    key={cat.slug}
                                    to={`/best/${cat.slug}`}
                                    className="flex items-center justify-between px-5 py-4 rounded-2xl bg-white hover:bg-slate-50 border border-slate-100 hover:border-slate-200 text-sm font-medium text-slate-700 transition-all group"
                                >
                                    <span>{cat.name}</span>
                                    <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-primary-500 transition-colors" />
                                </Link>
                            ))}
                    </div>
                </div>

                {/* FAQ */}
                <FAQAccordion items={faq} />

                {/* CTA */}
                <ConversionCTA variant="default" />
            </main>

            <footer className="bg-white border-t border-slate-200 py-12 mt-20">
                <div className="max-w-7xl mx-auto px-6 text-center text-slate-400 text-sm font-medium">
                    &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
                </div>
            </footer>
        </div>
    );
}
