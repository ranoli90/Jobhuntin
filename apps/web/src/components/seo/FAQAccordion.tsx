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
        <section className="py-16 sm:py-20 bg-[#F7F6F3]">
            <div className="max-w-[720px] mx-auto px-6">
                <h2 className="text-[clamp(1.75rem,3.5vw,28px)] font-bold text-[#2D2A26] mb-10 text-center" style={{ letterSpacing: '-0.5px' }}>
                    Frequently Asked Questions
                    {competitorName && <span className="text-[#9B9A97] font-normal"> about {competitorName}</span>}
                </h2>

                <div className="space-y-2">
                    {items.map((item, i) => (
                        <div
                            key={i}
                            className="rounded-xl border border-[#E9E9E7] bg-white overflow-hidden transition-all duration-200 hover:border-[#E3E2E0]"
                        >
                            <button
                                id={`faq-accordion-question-${i}`}
                                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                                className="w-full flex items-center justify-between gap-4 px-5 sm:px-6 py-4 sm:py-5 text-left group"
                                aria-expanded={openIndex === i}
                                aria-controls={`faq-accordion-answer-${i}`}
                            >
                                <span className="text-[15px] sm:text-[16px] font-semibold text-[#2D2A26] group-hover:text-[#455DD3] transition-colors pr-2">
                                    {item.question}
                                </span>
                                {openIndex === i ? (
                                    <ChevronUp className="w-5 h-5 text-[#455DD3] flex-shrink-0" />
                                ) : (
                                    <ChevronDown className="w-5 h-5 text-[#9B9A97] flex-shrink-0" />
                                )}
                            </button>
                            {openIndex === i && (
                                <div id={`faq-accordion-answer-${i}`} role="region" aria-labelledby={`faq-accordion-question-${i}`} className="px-5 sm:px-6 pb-5 pt-0 text-[15px] text-[#787774] leading-[1.6] border-t border-[#F1F1EF]">
                                    <p>{item.answer}</p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
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
