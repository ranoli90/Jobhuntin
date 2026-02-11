import type { Page } from '@playwright/test';

export type PerformanceMetrics = {
  lcp: number;
  cls: number;
  navigation: {
    domContentLoaded: number;
    load: number;
    firstByte: number;
    transferSize?: number;
  };
};

export async function registerPerformanceObservers(page: Page) {
  await page.addInitScript(() => {
    (window as any).__perfMetrics = { lcp: 0, cls: 0 };
    const lcpObserver = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const lastEntry = entries[entries.length - 1] as any;
      (window as any).__perfMetrics.lcp = lastEntry?.renderTime || lastEntry?.loadTime || 0;
    });
    try {
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
    } catch (e) {
      console.warn('LCP observer not supported', e);
    }

    const clsObserver = new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries() as any[]) {
        if (!entry.hadRecentInput) {
          (window as any).__perfMetrics.cls = ((window as any).__perfMetrics.cls || 0) + (entry.value || 0);
        }
      }
    });
    try {
      clsObserver.observe({ type: 'layout-shift', buffered: true });
    } catch (e) {
      console.warn('CLS observer not supported', e);
    }
  });
}

export async function collectPerformanceMetrics(page: Page): Promise<PerformanceMetrics> {
  const navigationTiming = await page.evaluate(() => {
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return nav
      ? {
          domContentLoaded: nav.domContentLoadedEventEnd,
          load: nav.loadEventEnd,
          firstByte: nav.responseStart,
          transferSize: (nav as any).transferSize,
        }
      : null;
  });

  const paintMetrics = await page.evaluate(() => (window as any).__perfMetrics || { lcp: 0, cls: 0 });

  return {
    lcp: paintMetrics.lcp || 0,
    cls: paintMetrics.cls || 0,
    navigation: navigationTiming || { domContentLoaded: 0, load: 0, firstByte: 0 },
  };
}

export function assertPerformanceThresholds(metrics: PerformanceMetrics) {
  const issues: string[] = [];
  if (metrics.lcp && metrics.lcp > 4000) issues.push(`LCP too high: ${metrics.lcp.toFixed(0)}ms`);
  if (metrics.cls && metrics.cls > 0.25) issues.push(`CLS too high: ${metrics.cls.toFixed(2)}`);
  if (metrics.navigation.domContentLoaded > 3000)
    issues.push(`DOMContentLoaded slow: ${metrics.navigation.domContentLoaded.toFixed(0)}ms`);
  if (metrics.navigation.load > 6000) issues.push(`Load event slow: ${metrics.navigation.load.toFixed(0)}ms`);

  if (issues.length) {
    throw new Error(`Performance thresholds exceeded:\n${issues.join('\n')}`);
  }
}
