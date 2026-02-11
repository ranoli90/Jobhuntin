import type { APIRequestContext, Page, Response } from '@playwright/test';

export async function assertNoFailedRequests(page: Page) {
  const failed: { url: string; status?: number; statusText?: string }[] = [];

  page.on('response', (resp: Response) => {
    const status = resp.status();
    if (status >= 400) {
      failed.push({ url: resp.url(), status, statusText: resp.statusText() });
    }
  });

  await page.waitForLoadState('networkidle');

  if (failed.length) {
    const msg = failed.map((f) => `${f.status} ${f.statusText} - ${f.url}`).join('\n');
    throw new Error(`Detected failed network requests:\n${msg}`);
  }
}

export async function checkAllLinks(request: APIRequestContext, links: string[], baseURL: string) {
  const badLinks: { url: string; status: number }[] = [];

  for (const link of links) {
    const absolute = link.startsWith('http') ? link : new URL(link, baseURL).toString();
    if (!absolute.startsWith(baseURL)) continue;
    let res = await request.head(absolute).catch(() => null);
    let status = res?.status();
    if (!status || status >= 400) {
      res = await request.get(absolute).catch(() => null);
      status = res?.status();
    }
    if (!status || status >= 400) {
      badLinks.push({ url: absolute, status: status ?? 0 });
    }
  }

  if (badLinks.length) {
    const msg = badLinks.map((b) => `${b.status} - ${b.url}`).join('\n');
    throw new Error(`Broken links detected:\n${msg}`);
  }
}
