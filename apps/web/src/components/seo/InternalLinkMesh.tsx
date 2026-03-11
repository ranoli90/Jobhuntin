import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  Layers,
  BarChart3,
  MapPin,
  Wrench,
  Newspaper,
} from "lucide-react";
import competitorsData from "../../data/competitors.json";
import categoriesData from "../../data/categories.json";
import guidesData from "../../data/guides.json";
import topicsData from "../../data/topics.json";
import locationsData from "../../data/locations.json";

interface InternalLinkMeshProperties {
  currentSlug: string;
  currentType: "vs" | "alternative" | "review" | "switch" | "pricing" | "hub";
  competitorCategory?: string[];
  maxCrossLinks?: number;
  relatedRole?: string;
}

// Popular location IDs for Explore by Location (tech hubs + high-activity markets)
const POPULAR_LOCATION_IDS = [
  "new-york",
  "san-francisco",
  "seattle",
  "austin",
  "boston",
  "london",
];

export function InternalLinkMesh({
  currentSlug,
  currentType,
  competitorCategory = [],
  maxCrossLinks = 6,
  relatedRole,
}: InternalLinkMeshProperties) {
  const currentCompetitor = competitorsData.find((c) => c.slug === currentSlug);
  const competitorName = currentCompetitor?.name || currentSlug;

  // Get related competitors from same categories
  const relatedCompetitors = competitorsData
    .filter((c) => {
      if (c.slug === currentSlug) return false;
      return competitorCategory.some((cat) => c.category?.includes(cat));
    })
    .slice(0, maxCrossLinks);

  // Get related category hubs
  const relatedCategories = categoriesData
    .filter((cat) => cat.competitors.includes(currentSlug))
    .slice(0, 4);

  // Guides: object -> array, pick up to 3 relevant by keywords
  const guidesArray = Object.entries(
    guidesData as Record<string, { title: string; category?: string }>,
  ).map(([slug, data]) => ({ slug, ...data }));
  const keywords = [competitorName, ...competitorCategory]
    .map((k) => k.toLowerCase())
    .filter(Boolean);
  const relevantGuides = guidesArray
    .filter((g) =>
      keywords.some((kw) =>
        (g.title + " " + (g.category || "")).toLowerCase().includes(kw),
      ),
    )
    .slice(0, 3);
  const displayGuides =
    relevantGuides.length > 0 ? relevantGuides : guidesArray.slice(0, 3);

  // Topics: object -> array, pick up to 3 relevant by keywords
  const topicsArray = Object.entries(
    topicsData as Record<string, { title: string; description?: string }>,
  ).map(([slug, data]) => ({ slug, ...data }));
  const relevantTopics = topicsArray
    .filter((t) =>
      keywords.some((kw) =>
        (t.title + " " + (t.description || "")).toLowerCase().includes(kw),
      ),
    )
    .slice(0, 3);
  const displayTopics =
    relevantTopics.length > 0 ? relevantTopics : topicsArray.slice(0, 3);

  // Locations: 4-6 popular locations
  const popularLocations = (locationsData as { id: string; name: string }[])
    .filter((loc) => POPULAR_LOCATION_IDS.includes(loc.id))
    .sort(
      (a, b) =>
        POPULAR_LOCATION_IDS.indexOf(a.id) - POPULAR_LOCATION_IDS.indexOf(b.id),
    )
    .slice(0, 6);
  const locationRole = relatedRole || "software-engineer";

  const PAGE_TYPES = [
    {
      type: "vs",
      prefix: "/vs/",
      label: (name: string) => `JobHuntin vs ${name}`,
      icon: Layers,
    },
    {
      type: "alternative",
      prefix: "/alternative-to/",
      label: (name: string) => `Best ${name} Alternative`,
      icon: ArrowRight,
    },
    {
      type: "review",
      prefix: "/reviews/",
      label: (name: string) => `${name} Review 2026`,
      icon: BarChart3,
    },
    {
      type: "switch",
      prefix: "/switch-from/",
      label: (name: string) => `Switch from ${name}`,
      icon: ArrowRight,
    },
    {
      type: "pricing",
      prefix: "/pricing-vs/",
      label: (name: string) => `${name} Pricing Compared`,
      icon: BarChart3,
    },
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
          {PAGE_TYPES.filter((pt) => pt.type !== currentType).map((pt) => (
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
            {relatedCompetitors.map((c) => (
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
        <div className="mb-12">
          <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-emerald-500" />
            Browse by Category
          </h3>
          <div className="grid sm:grid-cols-2 gap-3">
            {relatedCategories.map((cat) => (
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

      {/* Related Guides */}
      <div className="mb-12">
        <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-amber-500" />
          Related Guides
        </h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {displayGuides.map((g) => (
            <Link
              key={g.slug}
              to={`/guides/${g.slug}`}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-50 hover:bg-amber-50 border border-slate-100 hover:border-amber-200 text-sm font-medium text-slate-700 hover:text-amber-700 transition-all group"
            >
              <BookOpen className="w-4 h-4 text-slate-400 group-hover:text-amber-500 transition-colors shrink-0" />
              <span className="truncate">{g.title}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Related Topics */}
      <div className="mb-12">
        <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <Newspaper className="w-5 h-5 text-indigo-500" />
          Related Topics
        </h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {displayTopics.map((t) => (
            <Link
              key={t.slug}
              to={`/topics/${t.slug}`}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-50 hover:bg-indigo-50 border border-slate-100 hover:border-indigo-200 text-sm font-medium text-slate-700 hover:text-indigo-700 transition-all group"
            >
              <Newspaper className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-colors shrink-0" />
              <span className="truncate">{t.title}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Explore by Location */}
      {popularLocations.length > 0 && (
        <div className="mb-12">
          <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-rose-500" />
            Explore by Location
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {popularLocations.map((loc) => (
              <Link
                key={loc.id}
                to={`/jobs/${locationRole}/${loc.id}`}
                className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-50 hover:bg-rose-50 border border-slate-100 hover:border-rose-200 text-sm font-medium text-slate-700 hover:text-rose-700 transition-all group"
              >
                <MapPin className="w-4 h-4 text-slate-400 group-hover:text-rose-500 transition-colors shrink-0" />
                <span>{loc.name} Jobs</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Free Tools */}
      <div>
        <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <Wrench className="w-5 h-5 text-slate-600" />
          Free Tools
        </h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <Link
            to="/tools"
            className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-100 hover:border-slate-200 text-sm font-medium text-slate-700 hover:text-slate-800 transition-all group"
          >
            <Wrench className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors shrink-0" />
            All Free Tools
          </Link>
          <Link
            to="/tools#ai-resume-builder"
            className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-100 hover:border-slate-200 text-sm font-medium text-slate-700 hover:text-slate-800 transition-all group"
          >
            <Wrench className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors shrink-0" />
            AI Resume Tailor
          </Link>
          <Link
            to="/tools#ats-score-checker"
            className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-100 hover:border-slate-200 text-sm font-medium text-slate-700 hover:text-slate-800 transition-all group"
          >
            <Wrench className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors shrink-0" />
            ATS Checker
          </Link>
        </div>
      </div>
    </section>
  );
}
