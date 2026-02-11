import { APIRequestContext, expect, request, test } from '@playwright/test';
import { crawlSite } from '../utils/crawler';
import { runAxeAudit } from '../utils/accessibility';
import { assertPerformanceThresholds, collectPerformanceMetrics, registerPerformanceObservers } from '../utils/performance';
import { checkAllLinks } from '../utils/network';

const baseUrl = process.env.BASE_URL || 'https://jobhuntin.com';
const maxDepth = Number(process.env.CRAWL_DEPTH || 3);
const maxPages = Number(process.env.CRAWL_MAX_PAGES || 60);

// Top-level crawl so tests are generated per discovered URL
const discovered = await crawlSite({ baseUrl, maxDepth, maxPages });
const urls = Array.from(new Set(discovered.map((d) => d.url.split('#')[0])));
if (!urls.length) {
  throw new Error('Crawler found no URLs. Check connectivity or adjust BASE_URL/CRAWL_* envs.');
}

test.describe('Public site coverage', () => {
  let api: APIRequestContext;

  test.beforeAll(async () => {
    api = await request.newContext({ baseURL: baseUrl });
  });

  test.afterAll(async () => {
    await api.dispose();
  });

  test.describe.configure({ mode: 'parallel' });

  for (const url of urls) {
    test(url, async ({ page }) => {
      await registerPerformanceObservers(page);

      const consoleErrors: string[] = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error') consoleErrors.push(msg.text());
      });

      const failedResponses: { url: string; status: number }[] = [];
      page.on('response', (resp) => {
        if (resp.status() >= 400) failedResponses.push({ url: resp.url(), status: resp.status() });
      });

      const response = await page.goto(url, { waitUntil: 'networkidle' });
      expect(response?.status(), 'page load status').toBeLessThan(400);

      // Broken link detection
      const links = await page.$$eval('a[href]', (anchors) => anchors.map((a) => (a as HTMLAnchorElement).href));
      await checkAllLinks(api, links, baseUrl);

      // Accessibility audit
      await runAxeAudit(page, url);

      // Non-destructive interaction smoke
      const clickable = page.locator('[role="button"], summary, button');
      const count = await clickable.count();
      if (count > 0) {
        await clickable.first().click({ trial: true }).catch(() => {});
      }

      // Performance
      const perf = await collectPerformanceMetrics(page);
      assertPerformanceThresholds(perf);

      // Visual snapshot (baseline stored in baselines/)
      await expect(page).toHaveScreenshot({ fullPage: true, maxDiffPixels: 1500 });

      if (consoleErrors.length) {
        throw new Error(`Console errors on ${url}:\n${consoleErrors.join('\n')}`);
      }
      if (failedResponses.length) {
        const msg = failedResponses.map((f) => `${f.status} - ${f.url}`).join('\n');
        throw new Error(`Failed network responses on ${url}:\n${msg}`);
      }
    });
  }
});
