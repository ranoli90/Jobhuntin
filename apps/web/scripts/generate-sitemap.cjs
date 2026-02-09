const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://jobhuntin.com';

const routes = [
  { path: '/', priority: 1.0, changefreq: 'daily' },
  { path: '/pricing', priority: 0.8, changefreq: 'weekly' },
  { path: '/success-stories', priority: 0.8, changefreq: 'weekly' },
  { path: '/chrome-extension', priority: 0.8, changefreq: 'weekly' },
  { path: '/recruiters', priority: 0.7, changefreq: 'monthly' },
  { path: '/privacy', priority: 0.3, changefreq: 'monthly' },
  { path: '/terms', priority: 0.3, changefreq: 'monthly' },
  // Programmatic Niche Routes
  { path: '/jobs/marketing-manager/denver', priority: 0.6, changefreq: 'daily' },
  { path: '/jobs/software-engineer/boulder', priority: 0.6, changefreq: 'daily' },
  { path: '/jobs/product-manager/denver', priority: 0.6, changefreq: 'daily' },
  { path: '/jobs/sales-representative/remote', priority: 0.6, changefreq: 'daily' },
  // Comparison Routes
  { path: '/vs/sorce', priority: 0.7, changefreq: 'weekly' },
  { path: '/vs/simplify', priority: 0.7, changefreq: 'weekly' },
  { path: '/vs/teal', priority: 0.7, changefreq: 'weekly' },
  // Guide Routes (Topical Authority Hub)
  { path: '/guides', priority: 0.9, changefreq: 'weekly' },
  { path: '/guides/how-to-beat-ats-with-ai', priority: 0.8, changefreq: 'monthly' },
  { path: '/guides/automated-job-search-ethics', priority: 0.8, changefreq: 'monthly' },
  { path: '/guides/scaling-your-applications-safely', priority: 0.8, changefreq: 'monthly' },
  { path: '/guides/ai-cover-letter-mastery', priority: 0.8, changefreq: 'monthly' },
];

const generateSitemap = () => {
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${routes
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
  console.log(`Sitemap generated at: ${publicPath}`);
};

generateSitemap();
