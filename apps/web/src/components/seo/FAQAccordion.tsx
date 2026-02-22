import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

export interface FAQItem {
    question: string;
    answer: string;
}

interface FAQAccordionProps {
    items: FAQItem[];
    competitorName?: string;
}

export function FAQAccordion({ items, competitorName }: FAQAccordionProps) {
    const [openIndex, setOpenIndex] = useState<number | null>(0);

    // Generate FAQPage schema
    const faqSchema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": items.map(item => ({
            "@type": "Question",
            "name": item.question,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item.answer,
            },
        })),
    };

    return (
        <section className="py-16">
            <h2 className="text-3xl font-bold font-display text-slate-900 mb-8 text-center">
                Frequently Asked Questions
                {competitorName && <span className="text-slate-400"> about {competitorName}</span>}
            </h2>

            <div className="max-w-3xl mx-auto space-y-3">
                {items.map((item, i) => (
                    <div
                        key={i}
                        className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden transition-all hover:shadow-md"
                    >
                        <button
                            onClick={() => setOpenIndex(openIndex === i ? null : i)}
                            className="w-full flex items-center justify-between px-6 py-5 text-left group"
                            aria-expanded={openIndex === i}
                        >
                            <span className="text-lg font-semibold text-slate-900 group-hover:text-primary-600 transition-colors pr-4">
                                {item.question}
                            </span>
                            {openIndex === i ? (
                                <ChevronUp className="w-5 h-5 text-primary-500 flex-shrink-0" />
                            ) : (
                                <ChevronDown className="w-5 h-5 text-slate-400 flex-shrink-0" />
                            )}
                        </button>
                        {openIndex === i && (
                            <div className="px-6 pb-5 text-slate-600 leading-relaxed animate-in fade-in">
                                <p>{item.answer}</p>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* nosemgrep: typescript.react.security.audit.react-dangerouslysetinnerhtml.react-dangerouslysetinnerhtml - JSON-LD schema; JSON.stringify+replace prevents XSS */}
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{
                    __html: JSON.stringify(faqSchema).replace(/</g, "\\u003c").replace(/>/g, "\\u003e"),
                }}
            />
        </section>
    );
}
