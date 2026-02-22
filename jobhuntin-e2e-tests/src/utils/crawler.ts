import { chromium, type BrowserContext, type Page, type Request } from 'playwright';
import { URL } from 'url';
import fs from 'fs-extra';
import path from 'path';

export type DiscoveredURL = {
  url: string;
  depth: number;
};

export type CrawlerOptions = {
  baseUrl: string;
  maxDepth: number;
  maxPages?: number;
  includePatterns?: RegExp[];
  excludePatterns?: RegExp[];
  blocklistPaths?: RegExp[];
  concurrency?: number;
  userAgent?: string;
  respectRobotsTxt?: boolean;
  waitForSelectors?: string[];
  delayMs?: number;
};

const DEFAULT_OPTIONS: Required<Omit<CrawlerOptions, 'includePatterns' | 'excludePatterns' | 'blocklistPaths' | 'maxPages'>> = {
  baseUrl: 'https://jobhuntin.com',
  maxDepth: 2,
  concurrency: 3,
  respectRobotsTxt: false,
  waitForSelectors: [],
  delayMs: 150,
};

const DEFAULT_INCLUDE = [/^https:\/\/jobhuntin\.com(\/.*)?$/];
const DEFAULT_EXCLUDE = [
  /login/,
  /auth/,
  /\.(pdf|jpg|jpeg|png|gif|svg|webp)$/i,
  /mailto:/,
  /tel:/,
  /\/jobs\//,
];
const DEFAULT_BLOCKLIST = [/\blogout\b/, /\/api\//, /\/app\//, /\/jobs\//];

function isInternal(url: string, base: string) {
  try {
    const parsed = new URL(url, base);
    const baseParsed = new URL(base);
    return parsed.hostname === baseParsed.hostname;
  } catch {
    return false;
  }
}

function shouldInclude(url: string, options: CrawlerOptions) {
  const includePatterns = options.includePatterns?.length ? options.includePatterns : DEFAULT_INCLUDE;
  const excludePatterns = options.excludePatterns ?? DEFAULT_EXCLUDE;
  const blocklistPaths = options.blocklistPaths ?? DEFAULT_BLOCKLIST;

  if (!isInternal(url, options.baseUrl)) return false;
  if (blocklistPaths.some((re) => re.test(url))) return false;
  if (excludePatterns.some((re) => re.test(url))) return false;
  return includePatterns.some((re) => re.test(url));
}

export async function crawlSite(options: Partial<CrawlerOptions> = {}): Promise<DiscoveredURL[]> {
  const opts: CrawlerOptions = { ...DEFAULT_OPTIONS, ...options } as CrawlerOptions;
  const seen = new Set<string>();
  const queue: DiscoveredURL[] = [{ url: opts.baseUrl, depth: 0 }];
  const results: DiscoveredURL[] = [];

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ userAgent: opts.userAgent });
  const page = await context.newPage();

  while (queue.length > 0) {
    const current = queue.shift()!;
    if (seen.has(current.url)) continue;
    if (opts.maxPages && results.length >= opts.maxPages) break;
    if (current.depth > opts.maxDepth) continue;

    seen.add(current.url);
    results.push(current);

    try {
      await page.goto(current.url, { waitUntil: 'domcontentloaded', timeout: 30_000 });

      // Respect optional wait selectors
      for (const selector of opts.waitForSelectors || []) {
        await page.waitForSelector(selector, { timeout: 5_000 }).catch(() => null);
      }

      // Collect links
      const links = await page.$$eval('a[href]', (anchors) => anchors.map((a) => (a as HTMLAnchorElement).href));

      for (const link of links) {
        if (!shouldInclude(link, opts)) continue;
        const normalized = link.split('#')[0];
        if (!seen.has(normalized)) {
          queue.push({ url: normalized, depth: current.depth + 1 });
        }
      }

      if (opts.delayMs) await page.waitForTimeout(opts.delayMs);
    } catch (err) {
      console.warn("Crawl error on", current.url, ":", err);
    }
  }

  await browser.close();
  return results;
}

export async function saveDiscoveredUrls(urls: DiscoveredURL[], outputFile = 'reports/discovered-urls.json') {
  await fs.ensureDir(path.dirname(outputFile));
  await fs.writeJson(outputFile, urls, { spaces: 2 });
}
