import { test as base, type ConsoleMessage, type Page, type Response } from '@playwright/test';

type NetworkError = { url: string; status?: number; statusText?: string };

export const test = base.extend<{ page: Page; consoleErrors: ConsoleMessage[]; networkErrors: NetworkError[] }>({
  consoleErrors: async ({}, use) => {
    await use([]);
  },
  networkErrors: async ({}, use) => {
    await use([]);
  },
  page: async ({ page }, use, testInfo) => {
    const consoleErrors: ConsoleMessage[] = [];
    const networkErrors: NetworkError[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg);
      }
    });

    page.on('response', (resp: Response) => {
      if (resp.request().resourceType() === 'xhr') return; // skip analytics noise
      const status = resp.status();
      if (status >= 400) {
        networkErrors.push({ url: resp.url(), status, statusText: resp.statusText() });
      }
    });

    await use(page);

    if (consoleErrors.length) {
      const details = consoleErrors.map((c) => `${c.text()} [${c.location().url}:${c.location().lineNumber}]`).join('\n');
      testInfo.attachments.push({ name: 'console-errors', contentType: 'text/plain', body: details });
    }

    if (networkErrors.length) {
      const details = networkErrors.map((n) => `${n.status} ${n.statusText} - ${n.url}`).join('\n');
      testInfo.attachments.push({ name: 'network-errors', contentType: 'text/plain', body: details });
    }
  },
});

export const expect = test.expect;
