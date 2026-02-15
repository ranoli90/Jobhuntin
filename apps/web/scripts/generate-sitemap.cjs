const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://jobhuntin.com';

// Load competitor and category data dynamically
const competitors = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, '../src/data/competitors.json'), 'utf-8')
);
const categories = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, '../src/data/categories.json'), 'utf-8')
);
const roles = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, '../src/data/roles.json'), 'utf-8')
);
const locations = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, '../src/data/locations.json'), 'utf-8')
);

// Static routes
const staticRoutes = [
  { path: '/', priority: 1.0, changefreq: 'daily' },
  { path: '/pricing', priority: 0.8, changefreq: 'weekly' },
  { path: '/success-stories', priority: 0.8, changefreq: 'weekly' },
  { path: '/chrome-extension', priority: 0.8, changefreq: 'weekly' },
  { path: '/recruiters', priority: 0.7, changefreq: 'monthly' },
  { path: '/privacy', priority: 0.3, changefreq: 'monthly' },
  { path: '/terms', priority: 0.3, changefreq: 'monthly' },
  { path: '/about', priority: 0.5, changefreq: 'monthly' },
  // New SEO pages
  { path: '/blog', priority: 0.9, changefreq: 'daily' },
  { path: '/tools', priority: 0.9, changefreq: 'weekly' },
  { path: '/tools/ai-resume-builder', priority: 0.8, changefreq: 'monthly' },
  { path: '/tools/cover-letter-generator', priority: 0.8, changefreq: 'monthly' },
  { path: '/tools/job-tracker', priority: 0.8, changefreq: 'monthly' },
  { path: '/tools/ats-score-checker', priority: 0.8, changefreq: 'monthly' },
  { path: '/tools/job-match-scorer', priority: 0.8, changefreq: 'monthly' },
  { path: '/tools/ai-job-assistant', priority: 0.8, changefreq: 'monthly' },
  // Blog posts
  { path: '/blog/is-jobright-legit', priority: 0.9, changefreq: 'weekly' },
  { path: '/blog/ai-job-application-tools-compared', priority: 0.9, changefreq: 'weekly' },
  { path: '/blog/how-to-auto-apply-jobs', priority: 0.8, changefreq: 'monthly' },
  { path: '/blog/ats-resume-optimization', priority: 0.8, changefreq: 'monthly' },
  { path: '/blog/job-search-statistics-2026', priority: 0.8, changefreq: 'monthly' },
  { path: '/blog/interview-success-stories', priority: 0.8, changefreq: 'monthly' },
  // Dedicated outranking page
  { path: '/vs/jobright', priority: 1.0, changefreq: 'daily' },
  // Guides
  { path: '/guides', priority: 0.9, changefreq: 'weekly' },
  { path: '/guides/how-to-beat-ats-with-ai', priority: 0.8, changefreq: 'monthly' },
  { path: '/guides/automated-job-search-ethics', priority: 0.8, changefreq: 'monthly' },
  { path: '/guides/scaling-your-applications-safely', priority: 0.8, changefreq: 'monthly' },
  { path: '/guides/ai-cover-letter-mastery', priority: 0.8, changefreq: 'monthly' },
];

// Programmatic competitor routes — 5 page types per competitor
const competitorRoutes = competitors.flatMap((c) => [
  { path: `/vs/${c.slug}`, priority: 0.8, changefreq: 'weekly' },
  { path: `/alternative-to/${c.slug}`, priority: 0.8, changefreq: 'weekly' },
  { path: `/reviews/${c.slug}`, priority: 0.7, changefreq: 'weekly' },
  { path: `/switch-from/${c.slug}`, priority: 0.6, changefreq: 'monthly' },
  { path: `/pricing-vs/${c.slug}`, priority: 0.6, changefreq: 'monthly' },
]);

// Category hub routes
const categoryRoutes = categories.map((cat) => ({
  path: `/best/${cat.slug}`,
  priority: 0.9,
  changefreq: 'weekly',
}));

// Local Job Niche routes (Roles × Locations)
// Filter out roles without valid id field to prevent undefined URLs
const localRoutes = roles
  .filter((role) => role.id && typeof role.id === 'string' && role.id.trim() !== '')
  .flatMap((role) =>
    locations
      .filter((loc) => loc.id && typeof loc.id === 'string' && loc.id.trim() !== '')
      .map((loc) => ({
        path: `/jobs/${role.id}/${loc.id}`,
        priority: 0.7,
        changefreq: 'daily',
      }))
  );

const today = new Date().toISOString().split('T')[0];

function writeSitemap(filename, routes) {
  const body = routes
    .map((route) => `  <url>
    <loc>${BASE_URL}${route.path}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${route.changefreq}</changefreq>
    <priority>${route.priority}</priority>
  </url>`)
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${body}
</urlset>`;

  const publicPath = path.resolve(__dirname, `../public/${filename}`);
  fs.writeFileSync(publicPath, xml);
  return publicPath;
}

const sections = [
  { name: 'core', routes: staticRoutes },
  { name: 'competitors', routes: competitorRoutes },
  { name: 'categories', routes: categoryRoutes },
  { name: 'jobs', routes: localRoutes },
];

function generateSitemaps() {
  const indexEntries = sections.map(({ name, routes }) => {
    const filename = `sitemap-${name}.xml`;
    const filepath = writeSitemap(filename, routes);
    console.log(`✅ ${filename} written (${routes.length} URLs) -> ${filepath}`);
    return { filename, count: routes.length };
  });

  const indexXml = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${indexEntries
      .map(
        ({ filename }) => `  <sitemap>
    <loc>${BASE_URL}/${filename}</loc>
    <lastmod>${today}</lastmod>
  </sitemap>`
      )
      .join('\n')}
</sitemapindex>`;

  const indexPath = path.resolve(__dirname, '../public/sitemap.xml');
  fs.writeFileSync(indexPath, indexXml);
  console.log('📄 Sitemap index written ->', indexPath);
  console.log(`   - ${staticRoutes.length} static routes`);
  console.log(`   - ${competitorRoutes.length} competitor routes (${competitors.length} brands × 5 page types)`);
  console.log(`   - ${categoryRoutes.length} category hub routes`);
  console.log(`   - ${localRoutes.length} job routes`);
}

generateSitemaps();
