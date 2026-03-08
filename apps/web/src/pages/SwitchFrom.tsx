import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ArrowRight, CheckCircle2, Clock, Zap, UserCheck, Upload, Settings } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { FAQAccordion, type FAQItem } from '../components/seo/FAQAccordion';
import { InternalLinkMesh } from '../components/seo/InternalLinkMesh';
import { ConversionCTA } from '../components/seo/ConversionCTA';
import { motion } from 'framer-motion';
import competitorsData from '../data/competitors.json';

const COMPETITORS_MAP = Object.fromEntries(
    competitorsData.map(c => [c.slug, c])
);

const MIGRATION_STEPS = [
    {
        icon: UserCheck,
        title: 'Sign Up for JobHuntin',
        description: 'Create your free account in under 30 seconds. No credit card required.',
        time: '30 seconds',
    },
    {
        icon: Upload,
        title: 'Upload Your Resume',
        description: 'Upload your existing resume. Our AI will analyze it to understand your skills and experience.',
        time: '1 minute',
    },
    {
        icon: Settings,
        title: 'Set Your Preferences',
        description: 'Choose your target roles, locations, salary range, and job boards. The AI agent handles the rest.',
        time: '2 minutes',
    },
    {
        icon: Zap,
        title: 'Activate Your AI Agent',
        description: 'Turn on the autonomous agent. It will discover jobs, tailor your resume for each one, and auto-apply — all with stealth mode enabled.',
        time: '1 click',
    },
];

function generateFAQ(competitor: typeof competitorsData[0]): FAQItem[] {
    return [
        {
            question: `How do I cancel ${competitor.name}?`,
            answer: `Log into ${competitor.name}, go to billing, and cancel. ${competitor.status === 'discontinued' ? `${competitor.name} is already discontinued.` : 'Then set up JobHuntin in under 2 minutes.'}`,
        },
        {
            question: `Is it easy to switch from ${competitor.name} to JobHuntin?`,
            answer: `Yes — no data migration required. Create your account, upload your resume, set preferences, and the AI agent starts hunting immediately.`,
        },
        {
            question: `Will I lose my application history from ${competitor.name}?`,
            answer: `Your ${competitor.name} history stays in their system. JobHuntin starts tracking all new applications from day one with a cleaner dashboard and better insights.`,
        },
        {
            question: `How quickly can I start applying with JobHuntin after switching?`,
            answer: `Usually within 30 minutes. The agent starts discovering jobs, tailoring your resume, and submitting applications right away.`,
        },
        {
            question: `What if I'm currently in a ${competitor.name} contract?`,
            answer: `You can run both tools during the transition. Most users switch fully within a week once they see JobHuntin's results.`,
        },
    ];
}

export default function SwitchFrom() {
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

    const title = `Switch from ${competitor.name} to JobHuntin | 5-Minute Migration Guide 2026`;
    const description = `Migrate from ${competitor.name} to JobHuntin in 5 minutes. Get autonomous AI auto-apply, resume tailoring, and stealth mode. Step-by-step switching guide.`;
    const canonicalUrl = `https://jobhuntin.com/switch-from/${competitorSlug}`;
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
                        "@type": "HowTo",
                        "name": `How to Switch from ${competitor.name} to JobHuntin`,
                        "description": description,
                        "totalTime": "PT5M",
                        "step": MIGRATION_STEPS.map((step, i) => ({
                            "@type": "HowToStep",
                            "position": i + 1,
                            "name": step.title,
                            "text": step.description,
                        })),
                    },
                    {
                        "@context": "https://schema.org",
                        "@type": "ItemList",
                        "name": `${competitor.name} to JobHuntin Migration Tools`,
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

            <main className="max-w-4xl mx-auto px-6 py-24">
                {/* Hero */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-20"
                >
                    <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-600 px-4 py-1 rounded-lg text-sm font-bold mb-6 border border-amber-100">
                        <Clock className="w-4 h-4" />
                        5-Minute Migration
                    </div>
                    <h1 className="text-4xl md:text-6xl font-sans font-black mb-6 leading-tight text-slate-900">
                        Switch from{' '}
                        <span className="text-slate-400 line-through decoration-red-400">
                            {competitor.name}
                        </span>
                        {' '}to{' '}
                        <span className="text-primary-600 font-black">
                            JobHuntin
                        </span>
                    </h1>
                    <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
                        {competitor.status === 'discontinued'
                            ? `${competitor.name} is gone. Upgrade to JobHuntin's autonomous AI agent in under 5 minutes.`
                            : `Upgrade from ${competitor.name} to fully autonomous job hunting. No data migration needed.`
                        }
                    </p>
                </motion.div>

                {/* Migration Steps */}
                <div className="mb-20">
                    <h2 className="text-2xl font-bold text-slate-900 mb-10 text-center">
                        4 Steps to Switch — Under 5 Minutes
                    </h2>
                    <div className="space-y-6">
                        {MIGRATION_STEPS.map((step, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="flex gap-6 bg-white rounded-2xl border border-slate-100 p-8 shadow-sm hover:shadow-md transition-shadow"
                            >
                                <div className="flex-shrink-0">
                                    <div className="w-14 h-14 bg-primary-50 rounded-lg flex items-center justify-center text-primary-600 border border-primary-100">
                                        <step.icon className="w-7 h-7" />
                                    </div>
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="text-xs font-bold text-primary-600 bg-primary-50 px-2 py-0.5 rounded-lg">
                                            Step {i + 1}
                                        </span>
                                        <span className="text-xs text-slate-400 font-medium flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {step.time}
                                        </span>
                                    </div>
                                    <h3 className="text-lg font-bold text-slate-900 mb-1">{step.title}</h3>
                                    <p className="text-slate-500 text-sm font-medium leading-relaxed">{step.description}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* What You Gain */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-20 bg-white rounded-2xl border border-slate-100 p-10 shadow-sm"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-8">
                        What You Gain by Switching
                    </h2>
                    <div className="grid sm:grid-cols-2 gap-4">
                        {[
                            ...competitor.differentiators,
                            'Chrome extension for real-time job capture',
                            '24/7 autonomous operation — works while you sleep',
                            'Detailed application tracking dashboard',
                        ].map((item, i) => (
                            <div key={i} className="flex items-start gap-3 p-3 rounded-xl hover:bg-emerald-50 transition-colors">
                                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                                <span className="text-sm font-medium text-slate-700">{item}</span>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Quick CTA */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mb-20 text-center"
                >
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-3 bg-primary-600 hover:bg-primary-700 text-white px-10 py-5 rounded-lg font-bold text-xl shadow-xl shadow-primary-500/20 transition-colors"
                    >
                        Start Your Switch Now <ArrowRight className="w-6 h-6" />
                    </Link>
                    <p className="mt-3 text-sm text-slate-400 font-medium">
                        Free to start • No credit card • Setup in under 5 minutes
                    </p>
                </motion.div>

                {/* FAQ */}
                <FAQAccordion items={faq} competitorName={competitor.name} />

                {/* Internal Links */}
                <InternalLinkMesh
                    currentSlug={competitorSlug!}
                    currentType="switch"
                    competitorCategory={competitor.category}
                />

                {/* CTA */}
                <ConversionCTA competitorName={competitor.name} variant="switch" />
            </main>


        </div>
    );
}
