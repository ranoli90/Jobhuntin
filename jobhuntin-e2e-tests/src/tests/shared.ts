import { crawlSite } from '../utils/crawler';

const baseUrl = process.env.BASE_URL || 'https://jobhuntin.com';
const maxDepth = Number(process.env.CRAWL_DEPTH || 3);
const maxPages = Number(process.env.CRAWL_MAX_PAGES || 60);

export async function getDiscoveredUrls() {
  const discovered = await crawlSite({ baseUrl, maxDepth, maxPages });
  const unique = Array.from(new Set(discovered.map((d) => d.url.split('#')[0])));
  return unique;
}

export { baseUrl };
