/**
 * Prerender configuration — lists all routes that should get static HTML at build time.
 * Used by the generate-sitemap.cjs and can be consumed by any prerender plugin.
 */
import competitorsData from './src/data/competitors.json';
import categoriesData from './src/data/categories.json';

// Static marketing routes
const staticRoutes = [
    '/',
    '/pricing',
    '/success-stories',
    '/chrome-extension',
    '/recruiters',
    '/privacy',
    '/terms',
    '/about',
    '/login',
    '/guides',
    '/guides/how-to-beat-ats-with-ai',
    '/guides/automated-job-search-ethics',
    '/guides/scaling-your-applications-safely',
    '/guides/ai-cover-letter-mastery',
    // Niche job pages
    '/jobs/marketing-manager/denver',
    '/jobs/software-engineer/boulder',
    '/jobs/product-manager/denver',
    '/jobs/sales-representative/remote',
];

// Programmatic competitor routes (5 page types × N competitors)
const competitorRoutes = competitorsData.flatMap((c: { slug: string }) => [
    `/vs/${c.slug}`,
    `/alternative-to/${c.slug}`,
    `/reviews/${c.slug}`,
    `/switch-from/${c.slug}`,
    `/pricing-vs/${c.slug}`,
]);

// Category hub routes
const categoryRoutes = categoriesData.map((cat: { slug: string }) => `/best/${cat.slug}`);

export const prerenderRoutes = [
    ...staticRoutes,
    ...competitorRoutes,
    ...categoryRoutes,
];

export default prerenderRoutes;
