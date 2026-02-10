import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, BookOpen, Layers, BarChart3 } from 'lucide-react';
import competitorsData from '../../data/competitors.json';
import categoriesData from '../../data/categories.json';

interface InternalLinkMeshProps {
    currentSlug: string;
    currentType: 'vs' | 'alternative' | 'review' | 'switch' | 'pricing' | 'hub';
    competitorCategory?: string[];
    maxCrossLinks?: number;
}

export function InternalLinkMesh({
    currentSlug,
    currentType,
    competitorCategory = [],
    maxCrossLinks = 6,
}: InternalLinkMeshProps) {
    const currentCompetitor = competitorsData.find(c => c.slug === currentSlug);
    const competitorName = currentCompetitor?.name || currentSlug;

    // Get related competitors from same categories
    const relatedCompetitors = competitorsData
        .filter(c => {
            if (c.slug === currentSlug) return false;
            return competitorCategory.some(cat => c.category.includes(cat));
        })
        .slice(0, maxCrossLinks);

    // Get related category hubs
    const relatedCategories = categoriesData
        .filter(cat => cat.competitors.includes(currentSlug))
        .slice(0, 4);

    const PAGE_TYPES = [
        { type: 'vs', prefix: '/vs/', label: (name: string) => `JobHuntin vs ${name}`, icon: Layers },
        { type: 'alternative', prefix: '/alternative-to/', label: (name: string) => `Best ${name} Alternative`, icon: ArrowRight },
        { type: 'review', prefix: '/reviews/', label: (name: string) => `${name} Review 2026`, icon: BarChart3 },
        { type: 'switch', prefix: '/switch-from/', label: (name: string) => `Switch from ${name}`, icon: ArrowRight },
        { type: 'pricing', prefix: '/pricing-vs/', label: (name: string) => `${name} Pricing Compared`, icon: BarChart3 },
    ];

    return (
        <section className="border-t border-slate-200 pt-16 mt-16">
            {/* Same-brand cross-links */}
            <div className="mb-12">
                <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-primary-500" />
                    More about {competitorName}
                </h3>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {PAGE_TYPES.filter(pt => pt.type !== currentType).map(pt => (
                        <Link
                            key={pt.type}
                            to={`${pt.prefix}${currentSlug}`}
                            className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-50 hover:bg-primary-50 border border-slate-100 hover:border-primary-200 text-sm font-medium text-slate-700 hover:text-primary-700 transition-all group"
                        >
                            <pt.icon className="w-4 h-4 text-slate-400 group-hover:text-primary-500 transition-colors" />
                            {pt.label(competitorName)}
                        </Link>
                    ))}
                </div>
            </div>

            {/* Cross-competitor links */}
            {relatedCompetitors.length > 0 && (
                <div className="mb-12">
                    <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                        <Layers className="w-5 h-5 text-blue-500" />
                        Compare Other Tools
                    </h3>
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {relatedCompetitors.map(c => (
                            <Link
                                key={c.slug}
                                to={`/vs/${c.slug}`}
                                className="flex items-center justify-between px-4 py-3 rounded-xl bg-white hover:bg-blue-50 border border-slate-100 hover:border-blue-200 text-sm font-medium text-slate-700 hover:text-blue-700 transition-all group"
                            >
                                <span>JobHuntin vs {c.name}</span>
                                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* Category hub links */}
            {relatedCategories.length > 0 && (
                <div>
                    <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-emerald-500" />
                        Browse by Category
                    </h3>
                    <div className="grid sm:grid-cols-2 gap-3">
                        {relatedCategories.map(cat => (
                            <Link
                                key={cat.slug}
                                to={`/best/${cat.slug}`}
                                className="flex items-center justify-between px-4 py-3 rounded-xl bg-white hover:bg-emerald-50 border border-slate-100 hover:border-emerald-200 text-sm font-medium text-slate-700 hover:text-emerald-700 transition-all group"
                            >
                                <span>{cat.name}</span>
                                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-emerald-500 transition-colors" />
                            </Link>
                        ))}
                    </div>
                </div>
            )}
        </section>
    );
}
