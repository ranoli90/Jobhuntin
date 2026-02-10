/**
 * Prerender configuration — lists all routes that should get static HTML at build time.
 * Used by the generate-sitemap.cjs and can be consumed by any prerender plugin.
 */
import competitorsData from './src/data/competitors.json';
import categoriesData from './src/data/categories.json';
import rolesData from './src/data/roles.json';
import locationsData from './src/data/locations.json';

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

// Local Job Niche routes (Roles × Locations)
const localRoutes = rolesData.flatMap((role: { id: string }) =>
    locationsData.map((loc: { id: string }) => `/jobs/${role.id}/${loc.id}`)
);

export const prerenderRoutes = [
    ...staticRoutes,
    ...competitorRoutes,
    ...categoryRoutes,
    ...localRoutes,
];

export default prerenderRoutes;
