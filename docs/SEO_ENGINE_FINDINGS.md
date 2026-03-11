# SEO Engine Full Audit Findings

**Generated:** 2026-03-10  
**Sources:** 4 sub-agent audits (structure, content, technical, design)

---

## 1. CRITICAL / HIGH PRIORITY

| # | Finding | File:Line | Category |
|---|---------|-----------|----------|
| 1 | 404 page missing `noindex, nofollow` — can be indexed | NotFound.tsx:29-32 | Technical |
| 2 | Sitemap includes `/tools/*` but no routes — 404s | sitemap-core.xml, App.tsx | Structure |
| 3 | `/locations` and `/contact` missing from sitemap | generate-sitemap.cjs:26-60 | Structure |
| 4 | Prerender config omits blog, tools, topics, locations | prerender.config.ts:11-50 | Technical |
| 5 | Consent key mismatch — telemetry/GA use old key | telemetry.ts, useGoogleAnalytics.ts | (fixed) |
| 6 | OG image mismatch: index.html `og-image.png` vs SEO `og-default.png` | index.html:51, SEO.tsx:17 | Structure |
| 7 | Canonical conflict: App-level vs page-level overwrite | App.tsx:189, SEO.tsx:118 | Structure |
| 8 | InternalLinkMesh links to `/app/*` which is disallowed | InternalLinkMesh.tsx:230-244, robots.txt | Structure |
| 9 | AuthorPage has no SEO component | AuthorPage.tsx | Structure |
| 10 | Login page indexable — should have noindex | Login.tsx | Structure |

---

## 2. CONTENT / SPAM SIGNALS

| # | Finding | File:Line |
|---|---------|-----------|
| 11 | Meta keywords tag used — deprecated by Google | SEO.tsx:114 |
| 12 | Homepage keywords: 5 near-identical phrases | Homepage.tsx:301 |
| 13 | Competitor pages: bulk keyword injection | PricingVs.tsx:107, ReviewPage.tsx:81 |
| 14 | CategoryHub: visible keyword pills in body | CategoryHub.tsx:148-149 |
| 15 | seoOptimizer: 15+ primary keywords per page | seoOptimizer.ts:74-108 |
| 16 | "10,000+ job seekers" — unverifiable claim | Pricing.tsx:76, ConversionCTA.tsx:135 |
| 17 | Success Stories: 5-star Review schema for all — possible spam | SuccessStories.tsx:114-118 |
| 18 | Aggressive SEO: "extremely persuasive and SEO-optimized" | generate-aggressive-competitor-content.ts:242 |
| 19 | JobNiche FAQ: generic salary answers | seoOptimizer.ts:205-207 |
| 20 | Content sections: boilerplate "JobHuntin leads the category" | seoOptimizer.ts:354-356 |

---

## 3. SCHEMA / STRUCTURED DATA

| # | Finding | File:Line |
|---|---------|-----------|
| 21 | JobPosting: `baseSalary` vs `estimatedSalary` inconsistent units | seoOptimizer.ts:255-268 |
| 22 | JobPosting: `estimatedSalary.value` structure may be invalid | seoOptimizer.ts:259-268 |
| 23 | BlogPosting author as Organization — Person preferred | BlogHome.tsx:112-115 |
| 24 | SoftwareApplication offers: missing `priceValidUntil` | Homepage.tsx:301 |
| 25 | SuccessStories Review: no date meta | SuccessStories.tsx:111-112 |

---

## 4. TECHNICAL / PERFORMANCE

| # | Finding | File:Line |
|---|---------|-----------|
| 26 | Google Fonts render-blocking | index.html:39-42 |
| 27 | Hero images without explicit dimensions — CLS risk | Homepage.tsx:225-230 |
| 28 | No `fetchpriority="high"` on LCP image | BlogPost.tsx:269-274 |
| 29 | BlogHome images without `loading="lazy"` | BlogHome.tsx:185-190, 238 |
| 30 | seoOptimizer: `Math.random()` — non-deterministic HTML | seoOptimizer.ts:384, 416 |
| 31 | CategoryHub: `seoData.h2s[1]` without optional chaining | CategoryHub.tsx:213, 322 |

---

## 5. DESIGN CONSISTENCY

| # | Finding | File:Line |
|---|---------|-----------|
| 32 | Background mismatch: SuccessStories `bg-white` vs others `bg-slate-50` | SuccessStories.tsx:105 |
| 33 | Max-width inconsistency: 4xl vs 5xl vs 7xl | ReviewPage, Privacy, TopicPage |
| 34 | Hero badge colors differ: green-50, amber-50, blue-50 | PricingVs, CategoryHub, ReviewPage |
| 35 | H1 size mismatch across pages | ReviewPage, SuccessStories |
| 36 | Section spacing varies: mb-16, mb-20, mb-12 | Multiple |
| 37 | SuccessStories, GuidePage, JobNiche: custom CTA vs ConversionCTA | Multiple |
| 38 | Locations has no ConversionCTA | Locations.tsx |
| 39 | SEO pages lack dark mode | SEO pages |
| 40 | FAQAccordion: `bg-[#F7F6F3]` vs others |

---

## 6. BRANDING / E-E-A-T

| # | Finding | File:Line |
|---|---------|-----------|
| 41 | "JobHuntin AI" vs "JobHuntin" vs "Sorce" — inconsistent | Privacy, Terms, SEO |
| 42 | No author bios on blog/guides | BlogPost, GuidePage |
| 43 | Guides: generic author IDs "jane-doe" | guides.json |
| 44 | Success Stories: no LinkedIn/verification | SuccessStories.tsx:25-84 |
| 45 | index.html title vs Homepage SEO title mismatch | index.html:7, Homepage.tsx:301 |

---

## 7. SITEMAP / ROUTES

| # | Finding | File:Line |
|---|---------|-----------|
| 46 | JobNiche canonical: empty role/city → `/jobs//` | JobNiche.tsx:98 |
| 47 | robots.txt: Allow /api/og then Disallow /api/ — order | robots.txt:6-14 |
| 48 | Prerender: no topic routes | prerender.config.ts:46-51 |
| 49 | Blog slugs hardcoded; can drift from BlogHome | generate-sitemap.cjs:46-51 |
| 50 | hreflang: no `fr` alternate despite i18n | App.tsx:185-186 |

---

## 8. ACCESSIBILITY

| # | Finding | File:Line |
|---|---------|-----------|
| 51 | FAQAccordion: aria-controls added (fixed) | FAQAccordion.tsx |
| 52 | ComparisonTable: th missing scope="col" | ComparisonTable.tsx:62-71 |
| 53 | ComparisonTable: missing aria-label/caption | ComparisonTable.tsx:58 |
| 54 | JobNiche mobile menu: missing aria-label | JobNiche.tsx:148-154 |
| 55 | Breadcrumbs: schema only, no visual on many pages | SEO.tsx:59-68 |

---

## 9. ADDITIONAL / EFFICIENCY

| # | Finding | File:Line |
|---|---------|-----------|
| 56 | fast-index.ts: skips sitemap.xml index | fast-index.ts:85-97 |
| 57 | aggressive-seo-engine: regex sitemap parsing | aggressive-seo-engine.ts:310-312 |
| 58 | OG images: og/guides.png, og/tools.png may not exist | GuidesHome.tsx:27, ToolsHub.tsx:71 |
| 59 | Maintenance page: minimal content | Maintenance.tsx:11-12 |
| 60 | 404 page: promotional copy | NotFound.tsx:30-31 |

---

**Total documented: 60+ findings**

**Priority order for fixes:** Critical → High → Medium → Low
