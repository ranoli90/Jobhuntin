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
  // Niche job pages
  { path: '/jobs/marketing-manager/denver', priority: 0.6, changefreq: 'daily' },
  { path: '/jobs/software-engineer/boulder', priority: 0.6, changefreq: 'daily' },
  { path: '/jobs/product-manager/denver', priority: 0.6, changefreq: 'daily' },
  { path: '/jobs/sales-representative/remote', priority: 0.6, changefreq: 'daily' },
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

const allRoutes = [...staticRoutes, ...competitorRoutes, ...categoryRoutes];

const generateSitemap = () => {
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allRoutes
      .map((route) => {
        return `  <url>
    <loc>${BASE_URL}${route.path}</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>${route.changefreq}</changefreq>
    <priority>${route.priority}</priority>
  </url>`;
      })
      .join('\n')}
</urlset>`;

  const publicPath = path.resolve(__dirname, '../public/sitemap.xml');
  fs.writeFileSync(publicPath, sitemap);
  console.log(`✅ Sitemap generated with ${allRoutes.length} URLs at: ${publicPath}`);
  console.log(`   - ${staticRoutes.length} static routes`);
  console.log(`   - ${competitorRoutes.length} competitor routes (${competitors.length} brands × 5 page types)`);
  console.log(`   - ${categoryRoutes.length} category hub routes`);
};

generateSitemap();
