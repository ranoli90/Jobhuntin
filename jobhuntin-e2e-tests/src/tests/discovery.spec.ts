import { test, expect } from '@playwright/test';
import { crawlSite, saveDiscoveredUrls } from '../utils/crawler';

const baseUrl = process.env.BASE_URL || 'https://jobhuntin.com';

/**
 * Runs the crawler and persists discovered URLs to reports/discovered-urls.json
 * Useful standalone task to validate coverage and cap the crawl before heavy tests.
 */
test('discover public URLs', async () => {
  const discovered = await crawlSite({ baseUrl, maxDepth: 3, maxPages: 60 });
  await saveDiscoveredUrls(discovered);
  expect(discovered.length).toBeGreaterThan(0);
  console.log('Discovered URLs', discovered.map((d) => d.url));
});
