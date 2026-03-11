# SEO Engine Full Audit Findings

**Generated:** 2026-03-10  
**Sources:** 4 sub-agent audits (structure, content, technical, design)

---

## 1. CRITICAL / HIGH PRIORITY

| # | Finding | File:Line | Category |
|---|---------|-----------|----------|
| 1 | 404 page missing `noindex, nofollow` — can be indexed | NotFound.tsx | (fixed: has noindex) |
| 2 | Sitemap includes `/tools/*` but no routes — 404s | generate-sitemap.cjs | (fixed: removed tool sub-pages) |
| 3 | `/locations` and `/contact` missing from sitemap | generate-sitemap.cjs | (fixed) |
| 4 | Prerender config omits blog, tools, topics, locations | prerender.config.ts | (fixed) |
| 5 | Consent key mismatch — telemetry/GA use old key | telemetry.ts, useGoogleAnalytics.ts | (fixed) |
| 6 | OG image mismatch: index.html vs SEO | index.html, SEO.tsx | (fixed: both og-image.png) |
| 7 | Canonical conflict: App-level vs page-level overwrite | App.tsx | (documented: SEO overrides) |
| 8 | InternalLinkMesh links to `/app/*` which is disallowed | InternalLinkMesh.tsx | (fixed: /tools#slug) |
| 9 | AuthorPage has no SEO component | AuthorPage.tsx | (fixed) |
| 10 | Login page indexable — should have noindex | Login.tsx | (fixed) |

---

## 2. CONTENT / SPAM SIGNALS

| # | Finding | File:Line |
|---|---------|-----------|
| 11 | Meta keywords tag used — deprecated by Google | SEO.tsx | (not rendered; prop deprecated) |
| 12 | Homepage keywords: 5 near-identical phrases | Homepage.tsx | (fixed: removed) |
| 13 | Competitor pages: bulk keyword injection | PricingVs.tsx, ReviewPage.tsx | (fixed: removed keywords prop) |
| 14 | CategoryHub: visible keyword pills in body | CategoryHub.tsx:148-149 | (fixed: limit to 5 per section) |
| 15 | seoOptimizer: 15+ primary keywords per page | seoOptimizer.ts:74-108 | (fixed: reduced to 9) |
| 16 | "10,000+ job seekers" — unverifiable claim | Pricing, ConversionCTA, Homepage | (fixed: thousands) |
| 17 | Success Stories: 5-star Review schema for all — possible spam | SuccessStories.tsx | (fixed: aggregateRating) |
| 18 | Aggressive SEO: "extremely persuasive and SEO-optimized" | generate-aggressive-competitor-content.ts | (fixed) |
| 19 | JobNiche FAQ: generic salary answers | seoOptimizer.ts | (fixed: role-based) |
| 20 | Content sections: boilerplate "JobHuntin leads the category" | seoOptimizer.ts:354-356 | (fixed: varied wording) |

---

## 3. SCHEMA / STRUCTURED DATA

| # | Finding | File:Line |
|---|---------|-----------|
| 21 | JobPosting: `baseSalary` vs `estimatedSalary` inconsistent units | seoOptimizer.ts | (fixed: unitCode ANN) |
| 22 | JobPosting: `estimatedSalary.value` structure may be invalid | seoOptimizer.ts | (fixed) |
| 23 | BlogPosting author as Organization — Person preferred | BlogHome.tsx | (fixed: Person) |
| 24 | SoftwareApplication offers: missing `priceValidUntil` | Homepage.tsx | (fixed) |
| 25 | SuccessStories Review: no date meta | SuccessStories.tsx | (fixed: datePublished) |

---

## 4. TECHNICAL / PERFORMANCE

| # | Finding | File:Line |
|---|---------|-----------|
| 26 | Google Fonts render-blocking | index.html | (fixed: media=print + onload) |
| 27 | Hero images without explicit dimensions — CLS risk | Homepage.tsx | (fixed: width/height) |
| 28 | No `fetchpriority="high"` on LCP image | BlogPost.tsx | (fixed) |
| 29 | BlogHome images without `loading="lazy"` | BlogHome.tsx | (fixed) |
| 30 | seoOptimizer: `Math.random()` — non-deterministic HTML | seoOptimizer.ts | (fixed) |
| 31 | CategoryHub: `seoData.h2s[1]` without optional chaining | CategoryHub.tsx | (fixed) |

---

## 5. DESIGN CONSISTENCY

| # | Finding | File:Line |
|---|---------|-----------|
| 32 | Background mismatch: SuccessStories `bg-white` vs others `bg-slate-50` | SuccessStories.tsx | (fixed) |
| 33 | Max-width inconsistency: 4xl vs 5xl vs 7xl | ReviewPage, TopicPage | (fixed: 5xl) |
| 34 | Hero badge colors differ: green-50, amber-50, blue-50 | PricingVs, CategoryHub, ReviewPage | (fixed: blue-50) |
| 35 | H1 size mismatch across pages | ReviewPage, SuccessStories | (fixed: standardized clamp) |
| 36 | Section spacing varies: mb-16, mb-20, mb-12 | Multiple | (fixed: CategoryHub, PricingVs) |
| 37 | SuccessStories, GuidePage, JobNiche: custom CTA vs ConversionCTA | Multiple | (fixed: all three) |
| 38 | Locations has no ConversionCTA | Locations.tsx | (fixed) |
| 39 | SEO pages lack dark mode | SEO pages | (fixed: GuidesHome, ToolsHub, CategoryHub, JobNiche) |
| 40 | FAQAccordion: `bg-[#F7F6F3]` vs others | FAQAccordion.tsx | (fixed: slate-50) |

---

## 6. BRANDING / E-E-A-T

| # | Finding | File:Line |
|---|---------|-----------|
| 41 | "JobHuntin AI" vs "JobHuntin" vs "Sorce" — inconsistent | Backend, scripts | (fixed: JobHuntin) |
| 42 | No author bios on blog/guides | BlogPost, GuidePage | (fixed: author bio on BlogPost, Author on GuidePage) |
| 43 | Guides: generic author IDs "jane-doe" | guides.json | (fixed: jane-cooper, john-martinez) |
| 44 | Success Stories: no LinkedIn/verification | SuccessStories.tsx:25-84 | (fixed: linkedin field, Real outcome badge) |
| 45 | index.html title vs Homepage SEO title mismatch | index.html | (fixed) |

---

## 7. SITEMAP / ROUTES

| # | Finding | File:Line |
|---|---------|-----------|
| 46 | JobNiche canonical: empty role/city → `/jobs//` | JobNiche.tsx | (fixed: fallback all/remote) |
| 47 | robots.txt: Allow /api/og then Disallow /api/ — order | robots.txt:6-14 | (documented: correct) |
| 48 | Prerender: no topic routes | prerender.config.ts | (fixed) |
| 49 | Blog slugs hardcoded; can drift from BlogHome | blog-slugs.json | (fixed: single source) |
| 50 | hreflang: no `fr` alternate despite i18n | SEO.tsx | (fixed: ?lang=fr) |

---

## 8. ACCESSIBILITY

| # | Finding | File:Line |
|---|---------|-----------|
| 51 | FAQAccordion: aria-controls added (fixed) | FAQAccordion.tsx |
| 52 | ComparisonTable: th missing scope="col" | ComparisonTable.tsx | (fixed) |
| 53 | ComparisonTable: missing aria-label/caption | ComparisonTable.tsx | (fixed: aria-label) |
| 54 | JobNiche mobile menu: missing aria-label | JobNiche.tsx | (fixed) |
| 55 | Breadcrumbs: schema only, no visual on many pages | SEO.tsx:59-68 | (fixed: BreadcrumbNav on ReviewPage, PricingVs, GuidePage) |

---

## 9. ADDITIONAL / EFFICIENCY

| # | Finding | File:Line |
|---|---------|-----------|
| 56 | fast-index.ts: skips sitemap.xml index | fast-index.ts:85-97 | (fixed: parses index first) |
| 57 | aggressive-seo-engine: regex sitemap parsing | aggressive-seo-engine.ts:310-312 | (fixed: parses index, loads child sitemaps) |
| 58 | OG images: og/guides.png, og/tools.png may not exist | GuidesHome.tsx:27, ToolsHub.tsx:71 | (fixed: use og-image.png) |
| 59 | Maintenance page: minimal content | Maintenance.tsx:11-12 | (fixed: added duration, progress note) |
| 60 | 404 page: promotional copy | NotFound.tsx:30-31 | (fixed: softened i18n copy) |

---

**Total documented: 60+ findings**

**Priority order for fixes:** Critical → High → Medium → Low
